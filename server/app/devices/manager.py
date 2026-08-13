"""
JARVIS — Device Manager

Manages the device registry, state tracking, and command execution.
Implements the confirmed-state pattern: state only updates on node ACK.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import DatabaseManager
from app.db.models import Device, DeviceStateLog, Node
from app.core.events import EventBus, JarvisEvent

import structlog

logger = structlog.get_logger("jarvis.devices")


class DeviceManager:
    """Manages device registry, state, and commands."""

    def __init__(self, db: DatabaseManager, event_bus: EventBus):
        self.db = db
        self.event_bus = event_bus
        self._devices: Dict[str, dict] = {}  # In-memory cache

    async def initialize(self) -> None:
        """Load all devices from database into memory cache."""
        async with self.db.get_session() as session:
            result = await session.execute(select(Device))
            devices = result.scalars().all()
            for device in devices:
                self._devices[device.id] = self._device_to_dict(device)

        # Subscribe to node state changes
        self.event_bus.subscribe("NODE_STATE_CHANGED", self._on_node_state_changed)
        logger.info("device_manager.initialized", device_count=len(self._devices))

    def _device_to_dict(self, device: Device) -> dict:
        return {
            "id": device.id,
            "name": device.name,
            "room_id": device.room_id,
            "node_id": device.node_id,
            "type": device.type,
            "channel": device.channel,
            "capabilities": device.capabilities or ["on", "off", "toggle"],
            "state": device.state,
            "confirmed": device.confirmed,
            "last_changed": device.last_changed.isoformat() if device.last_changed else None,
            "metadata": device.metadata_ or {},
            "created_at": device.created_at.isoformat() if device.created_at else None,
        }

    # ---- CRUD ----

    async def get_all(self) -> List[dict]:
        """Get all devices."""
        return list(self._devices.values())

    async def get(self, device_id: str) -> Optional[dict]:
        """Get a single device by ID."""
        return self._devices.get(device_id)

    async def create(self, data: dict) -> dict:
        """Create a new device."""
        async with self.db.get_session() as session:
            device = Device(
                id=data["id"],
                name=data["name"],
                room_id=data["room_id"],
                node_id=data["node_id"],
                type=data.get("type", "relay"),
                channel=data.get("channel", 0),
                capabilities=data.get("capabilities", ["on", "off", "toggle"]),
                state="unknown",
                confirmed=False,
                metadata_=data.get("metadata", {}),
            )
            session.add(device)
            await session.commit()
            await session.refresh(device)

            device_dict = self._device_to_dict(device)
            self._devices[device.id] = device_dict
            logger.info("device.created", device_id=device.id, name=device.name)
            return device_dict

    async def update(self, device_id: str, data: dict) -> Optional[dict]:
        """Update a device."""
        if device_id not in self._devices:
            return None

        async with self.db.get_session() as session:
            result = await session.execute(
                select(Device).where(Device.id == device_id)
            )
            device = result.scalar_one_or_none()
            if not device:
                return None

            for key, value in data.items():
                if value is not None and hasattr(device, key):
                    if key == "metadata":
                        device.metadata_ = value
                    else:
                        setattr(device, key, value)

            await session.commit()
            await session.refresh(device)

            device_dict = self._device_to_dict(device)
            self._devices[device_id] = device_dict
            logger.info("device.updated", device_id=device_id)
            return device_dict

    async def delete(self, device_id: str) -> bool:
        """Delete a device."""
        if device_id not in self._devices:
            return False

        async with self.db.get_session() as session:
            result = await session.execute(
                select(Device).where(Device.id == device_id)
            )
            device = result.scalar_one_or_none()
            if device:
                await session.delete(device)
                await session.commit()

        del self._devices[device_id]
        logger.info("device.deleted", device_id=device_id)
        return True

    # ---- Device Control ----

    async def execute_command(
        self,
        device_id: str,
        action: str,
        source: str = "dashboard",
        message_id: Optional[str] = None,
    ) -> dict:
        """Execute a device command. Returns immediately with pending state.
        
        Actual state confirmation comes later via confirm_state().
        """
        device = self._devices.get(device_id)
        if not device:
            raise ValueError(f"Device not found: {device_id}")

        if action not in ("turn_on", "turn_off", "toggle"):
            raise ValueError(f"Invalid action: {action}")

        msg_id = message_id or str(uuid.uuid4())

        # Determine target state
        if action == "toggle":
            target_state = "off" if device["state"] == "on" else "on"
        elif action == "turn_on":
            target_state = "on"
        else:
            target_state = "off"

        # Publish command event — WebSocket manager will route to ESP32
        await self.event_bus.publish(JarvisEvent(
            type="DEVICE_COMMAND",
            source=source,
            message_id=msg_id,
            data={
                "device_id": device_id,
                "node_id": device["node_id"],
                "channel": device["channel"],
                "action": action,
                "target_state": target_state,
            },
        ))

        # Log pending state
        async with self.db.get_session() as session:
            state_log = DeviceStateLog(
                device_id=device_id,
                state=f"pending_{target_state}",
                confirmed=False,
                source=source,
                message_id=msg_id,
            )
            session.add(state_log)
            await session.commit()

        logger.info(
            "device.command",
            device_id=device_id,
            action=action,
            target_state=target_state,
            message_id=msg_id,
            source=source,
        )

        return {
            "message_id": msg_id,
            "device_id": device_id,
            "action": action,
            "state": "pending",
            "message": f"Command sent — waiting for {device['name']}",
        }

    async def confirm_state(
        self,
        device_id: str,
        state: str,
        message_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Confirm device state from node ACK. Only this method sets confirmed=True."""
        device = self._devices.get(device_id)
        if not device:
            logger.warning("device.confirm_unknown", device_id=device_id)
            return None

        now = datetime.now(timezone.utc)

        # Update in-memory cache
        device["state"] = state
        device["confirmed"] = True
        device["last_changed"] = now.isoformat()

        # Update database
        async with self.db.get_session() as session:
            result = await session.execute(
                select(Device).where(Device.id == device_id)
            )
            db_device = result.scalar_one_or_none()
            if db_device:
                db_device.state = state
                db_device.confirmed = True
                db_device.last_changed = now

                # Log confirmed state
                state_log = DeviceStateLog(
                    device_id=device_id,
                    state=state,
                    confirmed=True,
                    source="node_ack",
                    message_id=message_id,
                )
                session.add(state_log)
                await session.commit()

        # Publish state change event
        await self.event_bus.publish(JarvisEvent(
            type="DEVICE_STATE_CHANGED",
            source="node",
            message_id=message_id,
            data={
                "device_id": device_id,
                "state": state,
                "confirmed": True,
            },
        ))

        logger.info(
            "device.state_confirmed",
            device_id=device_id,
            state=state,
            message_id=message_id,
        )
        return device

    async def mark_state_failed(
        self,
        device_id: str,
        error: str,
        message_id: Optional[str] = None,
    ) -> None:
        """Mark a device command as failed (no ACK received)."""
        device = self._devices.get(device_id)
        if device:
            device["confirmed"] = False

        await self.event_bus.publish(JarvisEvent(
            type="DEVICE_STATE_FAILED",
            source="system",
            message_id=message_id,
            data={
                "device_id": device_id,
                "error": error,
            },
        ))

        logger.warning(
            "device.state_failed",
            device_id=device_id,
            error=error,
            message_id=message_id,
        )

    # ---- Queries ----

    async def get_devices_by_node(self, node_id: str) -> List[dict]:
        """Get all devices belonging to a node."""
        return [d for d in self._devices.values() if d["node_id"] == node_id]

    async def get_devices_by_room(self, room_id: str) -> List[dict]:
        """Get all devices in a room."""
        return [d for d in self._devices.values() if d["room_id"] == room_id]

    def device_exists(self, device_id: str) -> bool:
        """Check if a device exists."""
        return device_id in self._devices

    def get_device_sync(self, device_id: str) -> Optional[dict]:
        """Synchronous device lookup for use in validation."""
        return self._devices.get(device_id)

    async def get_state_history(
        self, device_id: str, limit: int = 50
    ) -> List[dict]:
        """Get recent state change history for a device."""
        async with self.db.get_session() as session:
            result = await session.execute(
                select(DeviceStateLog)
                .where(DeviceStateLog.device_id == device_id)
                .order_by(DeviceStateLog.changed_at.desc())
                .limit(limit)
            )
            return [
                {
                    "state": log.state,
                    "confirmed": log.confirmed,
                    "source": log.source,
                    "message_id": log.message_id,
                    "changed_at": log.changed_at.isoformat() if log.changed_at else None,
                }
                for log in result.scalars().all()
            ]

    # ---- Event Handlers ----

    async def _on_node_state_changed(self, event: JarvisEvent) -> None:
        """Handle node online/offline changes — update device availability."""
        node_id = event.data.get("node_id")
        status = event.data.get("status")

        if status == "offline":
            # Mark all devices on this node as unconfirmed
            for device in self._devices.values():
                if device["node_id"] == node_id:
                    device["confirmed"] = False
            logger.info("device.node_offline", node_id=node_id)
