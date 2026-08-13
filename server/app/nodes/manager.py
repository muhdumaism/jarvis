"""
JARVIS — Node Manager

Manages node registry, online/offline tracking, and heartbeat monitoring.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select

from app.db.database import DatabaseManager
from app.db.models import Node, Device, Room
from app.core.events import EventBus, JarvisEvent

import structlog

logger = structlog.get_logger("jarvis.nodes")

# Timeout: if no heartbeat for this many seconds, mark offline
HEARTBEAT_TIMEOUT_SECONDS = 45


class NodeManager:
    """Manages node registry and online/offline tracking."""

    def __init__(self, db: DatabaseManager, event_bus: EventBus):
        self.db = db
        self.event_bus = event_bus
        self._nodes: Dict[str, dict] = {}
        self._monitor_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Load all nodes from database."""
        async with self.db.get_session() as session:
            result = await session.execute(select(Node))
            nodes = result.scalars().all()
            for node in nodes:
                # Count devices for this node
                dev_result = await session.execute(
                    select(Device).where(Device.node_id == node.id)
                )
                device_count = len(dev_result.scalars().all())

                self._nodes[node.id] = {
                    "id": node.id,
                    "name": node.name,
                    "room_id": node.room_id,
                    "mac_address": node.mac_address,
                    "chip_type": node.chip_type,
                    "firmware_version": node.firmware_version,
                    "status": node.status,
                    "last_seen": node.last_seen.isoformat() if node.last_seen else None,
                    "uptime": node.uptime,
                    "free_heap": node.free_heap,
                    "device_count": device_count,
                    "config": node.config or {},
                    "created_at": node.created_at.isoformat() if node.created_at else None,
                }

        # Start heartbeat monitor
        self._monitor_task = asyncio.create_task(self._heartbeat_monitor())
        logger.info("node_manager.initialized", node_count=len(self._nodes))

    async def stop(self) -> None:
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    # ---- CRUD ----

    async def get_all(self) -> List[dict]:
        return list(self._nodes.values())

    async def get(self, node_id: str) -> Optional[dict]:
        return self._nodes.get(node_id)

    async def create(self, data: dict) -> dict:
        async with self.db.get_session() as session:
            mac_address = data.get("mac_address")
            if not mac_address or str(mac_address).strip() == "":
                mac_address = None

            node = Node(
                id=data["id"],
                name=data["name"],
                room_id=data.get("room_id"),
                mac_address=mac_address,
                chip_type=data.get("chip_type", "esp32s3"),
                config=data.get("config", {}),
            )
            session.add(node)
            await session.commit()
            await session.refresh(node)

            node_dict = {
                "id": node.id,
                "name": node.name,
                "room_id": node.room_id,
                "mac_address": node.mac_address,
                "chip_type": node.chip_type,
                "firmware_version": node.firmware_version,
                "status": node.status,
                "last_seen": None,
                "uptime": 0,
                "free_heap": 0,
                "device_count": 0,
                "config": node.config or {},
                "created_at": node.created_at.isoformat() if node.created_at else None,
            }
            self._nodes[node.id] = node_dict
            logger.info("node.created", node_id=node.id, name=node.name)
            return node_dict

    async def update(self, node_id: str, data: dict) -> Optional[dict]:
        if node_id not in self._nodes:
            return None

        async with self.db.get_session() as session:
            result = await session.execute(select(Node).where(Node.id == node_id))
            node = result.scalar_one_or_none()
            if not node:
                return None

            for key, value in data.items():
                if value is not None and hasattr(node, key):
                    setattr(node, key, value)

            await session.commit()
            await session.refresh(node)

            self._nodes[node_id].update({
                k: v for k, v in data.items() if v is not None
            })
            logger.info("node.updated", node_id=node_id)
            return self._nodes[node_id]

    async def delete(self, node_id: str) -> bool:
        if node_id not in self._nodes:
            return False

        async with self.db.get_session() as session:
            result = await session.execute(select(Node).where(Node.id == node_id))
            node = result.scalar_one_or_none()
            if node:
                await session.delete(node)
                await session.commit()

        del self._nodes[node_id]
        logger.info("node.deleted", node_id=node_id)
        return True

    # ---- Heartbeat ----

    async def process_heartbeat(self, node_id: str, data: dict) -> None:
        """Process a heartbeat from a node."""
        now = datetime.now(timezone.utc)

        if node_id not in self._nodes:
            logger.info("node.heartbeat_discovered", node_id=node_id)
            
            # Ensure a default 'unassigned' room exists in the DB to satisfy nullable=False FK constraint
            async with self.db.get_session() as session:
                result = await session.execute(select(Room).where(Room.id == "unassigned"))
                room = result.scalar_one_or_none()
                if not room:
                    logger.info("node.creating_unassigned_room")
                    room = Room(id="unassigned", name="Unassigned")
                    session.add(room)
                    await session.commit()

            await self.create({
                "id": node_id,
                "name": f"Discovered {node_id.replace('_', ' ').title()}",
                "room_id": "unassigned",
                "mac_address": data.get("mac_address"),
                "chip_type": data.get("chip_type", "esp32s3"),
                "config": {}
            })

        was_offline = self._nodes[node_id]["status"] == "offline"

        self._nodes[node_id].update({
            "status": "online",
            "last_seen": now.isoformat(),
            "uptime": data.get("uptime", 0),
            "free_heap": data.get("free_heap", 0),
            "firmware_version": data.get("firmware_version", self._nodes[node_id]["firmware_version"]),
        })

        # Update database
        async with self.db.get_session() as session:
            result = await session.execute(select(Node).where(Node.id == node_id))
            node = result.scalar_one_or_none()
            if node:
                node.status = "online"
                node.last_seen = now
                node.uptime = data.get("uptime", 0)
                node.free_heap = data.get("free_heap", 0)
                if data.get("firmware_version"):
                    node.firmware_version = data["firmware_version"]
                await session.commit()

        if was_offline:
            await self.event_bus.publish(JarvisEvent(
                type="NODE_ONLINE",
                source="node",
                data={"node_id": node_id},
            ))
            await self.event_bus.publish(JarvisEvent(
                type="NODE_STATE_CHANGED",
                source="node",
                data={"node_id": node_id, "status": "online"},
            ))
            logger.info("node.online", node_id=node_id)

    async def _mark_offline(self, node_id: str) -> None:
        """Mark a node as offline."""
        if node_id in self._nodes and self._nodes[node_id]["status"] != "offline":
            self._nodes[node_id]["status"] = "offline"

            async with self.db.get_session() as session:
                result = await session.execute(select(Node).where(Node.id == node_id))
                node = result.scalar_one_or_none()
                if node:
                    node.status = "offline"
                    await session.commit()

            await self.event_bus.publish(JarvisEvent(
                type="NODE_OFFLINE",
                source="system",
                data={"node_id": node_id, "last_seen": self._nodes[node_id]["last_seen"]},
            ))
            await self.event_bus.publish(JarvisEvent(
                type="NODE_STATE_CHANGED",
                source="system",
                data={"node_id": node_id, "status": "offline"},
            ))
            logger.warning("node.offline", node_id=node_id)

    async def _heartbeat_monitor(self) -> None:
        """Periodically check for nodes that have missed heartbeats."""
        while True:
            try:
                await asyncio.sleep(15)
                now = datetime.now(timezone.utc)
                timeout = timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)

                for node_id, node in self._nodes.items():
                    if node["status"] == "online" and node["last_seen"]:
                        last_seen = datetime.fromisoformat(node["last_seen"])
                        if last_seen.tzinfo is None:
                            last_seen = last_seen.replace(tzinfo=timezone.utc)
                        if now - last_seen > timeout:
                            await self._mark_offline(node_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("node.monitor_error", error=str(e))

    def is_online(self, node_id: str) -> bool:
        """Check if a node is online."""
        node = self._nodes.get(node_id)
        return node is not None and node["status"] == "online"
