"""
JARVIS — WebSocket Manager

Manages all WebSocket connections (ESP32 + Dashboard clients).
Handles authentication, heartbeat, message routing, and broadcasting.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from app.core.security import authenticate_websocket
from app.core.events import EventBus, JarvisEvent
from app.core.rate_limiter import ws_limiter

import structlog

logger = structlog.get_logger("jarvis.websocket")


class ConnectedClient:
    """Represents a connected WebSocket client."""

    def __init__(self, websocket: WebSocket, client_id: str, client_type: str):
        self.websocket = websocket
        self.client_id = client_id
        self.client_type = client_type  # "esp32_main", "dashboard"
        self.connected_at = datetime.now(timezone.utc)
        self.last_heartbeat = datetime.now(timezone.utc)
        self.authenticated = False
        self.auth_info: dict = {}


class WebSocketManager:
    """Manages WebSocket connections and message routing."""

    def __init__(self, event_bus: EventBus, device_manager, node_manager):
        self.event_bus = event_bus
        self.device_manager = device_manager
        self.node_manager = node_manager
        self._clients: Dict[str, ConnectedClient] = {}
        self._esp32_client: Optional[ConnectedClient] = None

        # Subscribe to events that need broadcasting
        self.event_bus.subscribe("DEVICE_STATE_CHANGED", self._broadcast_event)
        self.event_bus.subscribe("DEVICE_STATE_PENDING", self._broadcast_event)
        self.event_bus.subscribe("DEVICE_STATE_FAILED", self._broadcast_event)
        self.event_bus.subscribe("NODE_ONLINE", self._broadcast_event)
        self.event_bus.subscribe("NODE_OFFLINE", self._broadcast_event)
        self.event_bus.subscribe("MUSIC_STATE", self._broadcast_event)
        self.event_bus.subscribe("VOICE_LISTENING", self._broadcast_event)
        self.event_bus.subscribe("VOICE_THINKING", self._broadcast_event)
        self.event_bus.subscribe("VOICE_TRANSCRIBED", self._broadcast_event)
        self.event_bus.subscribe("ASSISTANT_INTENT", self._broadcast_event)
        self.event_bus.subscribe("ASSISTANT_EXECUTING", self._broadcast_event)
        self.event_bus.subscribe("ASSISTANT_RESPONSE", self._broadcast_event)
        self.event_bus.subscribe("ASSISTANT_ERROR", self._broadcast_event)
        self.event_bus.subscribe("NOTIFICATION", self._broadcast_event)
        self.event_bus.subscribe("SYSTEM_STATUS", self._broadcast_event)

        # Subscribe to device commands that need routing to ESP32
        self.event_bus.subscribe("DEVICE_COMMAND", self._route_device_command)
        # Subscribe to TTS events that go to ESP32
        self.event_bus.subscribe("TTS_START", self._send_to_esp32)
        self.event_bus.subscribe("TTS_AUDIO", self._send_to_esp32)
        self.event_bus.subscribe("TTS_END", self._send_to_esp32)

    @property
    def connection_count(self) -> int:
        return len(self._clients)

    @property
    def esp32_connected(self) -> bool:
        return self._esp32_client is not None

    async def connect(self, client: ConnectedClient) -> None:
        """Register a new client."""
        self._clients[client.client_id] = client
        if client.client_type == "esp32_main":
            self._esp32_client = client
        logger.info(
            "ws.connected",
            client_id=client.client_id,
            client_type=client.client_type,
        )

    async def disconnect(self, client_id: str) -> None:
        """Remove a client."""
        client = self._clients.pop(client_id, None)
        if client and client.client_type == "esp32_main":
            self._esp32_client = None
            logger.warning("ws.esp32_disconnected")
        if client:
            logger.info("ws.disconnected", client_id=client_id)

    async def send_to_client(self, client_id: str, message: dict) -> bool:
        """Send a message to a specific client."""
        client = self._clients.get(client_id)
        if not client:
            return False
        try:
            await client.websocket.send_json(message)
            return True
        except Exception as e:
            logger.error("ws.send_error", client_id=client_id, error=str(e))
            await self.disconnect(client_id)
            return False

    async def send_to_esp32(self, message: dict) -> bool:
        """Send a message to the main ESP32."""
        if not self._esp32_client:
            logger.warning("ws.esp32_not_connected")
            return False
        return await self.send_to_client(self._esp32_client.client_id, message)

    async def broadcast(self, message: dict, exclude: Optional[Set[str]] = None) -> None:
        """Broadcast a message to all connected clients."""
        exclude = exclude or set()
        disconnected = []
        for client_id, client in self._clients.items():
            if client_id in exclude:
                continue
            try:
                await client.websocket.send_json(message)
            except Exception:
                disconnected.append(client_id)

        for client_id in disconnected:
            await self.disconnect(client_id)

    async def broadcast_to_dashboards(self, message: dict) -> None:
        """Broadcast a message to all dashboard clients only."""
        disconnected = []
        for client_id, client in self._clients.items():
            if client.client_type != "dashboard":
                continue
            try:
                await client.websocket.send_json(message)
            except Exception:
                disconnected.append(client_id)
        for cid in disconnected:
            await self.disconnect(cid)

    # ---- Event Handlers ----

    async def _broadcast_event(self, event: JarvisEvent) -> None:
        """Broadcast an event to all clients."""
        message = {
            "type": event.type,
            "message_id": event.message_id,
            "timestamp": event.timestamp,
            **event.data,
        }
        await self.broadcast(message)

    async def _route_device_command(self, event: JarvisEvent) -> None:
        """Route a device command to the main ESP32."""
        message = {
            "type": "DEVICE_COMMAND",
            "message_id": event.message_id,
            "device_id": event.data.get("device_id"),
            "node_id": event.data.get("node_id"),
            "channel": event.data.get("channel", 0),
            "action": event.data.get("action"),
            "target_state": event.data.get("target_state"),
        }
        sent = await self.send_to_esp32(message)
        if not sent:
            # ESP32 not connected — mark command as failed
            await self.device_manager.mark_state_failed(
                device_id=event.data.get("device_id"),
                error="Main ESP32 not connected",
                message_id=event.message_id,
            )

    async def _send_to_esp32(self, event: JarvisEvent) -> None:
        """Send TTS/audio events directly to ESP32."""
        message = {
            "type": event.type,
            "message_id": event.message_id,
            **event.data,
        }
        await self.send_to_esp32(message)

    # ---- Message Processing ----

    async def process_message(self, client: ConnectedClient, data: dict) -> None:
        """Process an incoming WebSocket message from a client."""
        msg_type = data.get("type", "")

        # Rate limiting
        if not ws_limiter.check(client.client_id):
            await self.send_to_client(client.client_id, {
                "type": "ERROR",
                "code": "RATE_LIMITED",
                "message": "Too many messages",
            })
            return

        if msg_type == "HEARTBEAT":
            await self._handle_heartbeat(client, data)
        elif msg_type == "VOICE_START":
            await self._handle_voice_event(client, data)
        elif msg_type == "VOICE_AUDIO":
            await self._handle_voice_event(client, data)
        elif msg_type == "VOICE_END":
            await self._handle_voice_event(client, data)
        elif msg_type == "VOICE_CANCEL":
            await self._handle_voice_event(client, data)
        elif msg_type == "DEVICE_STATE_CHANGED":
            await self._handle_device_state(client, data)
        elif msg_type == "NODE_HEARTBEAT":
            await self._handle_node_heartbeat(client, data)
        elif msg_type == "MUSIC_COMMAND":
            await self._handle_music_command(data)
        elif msg_type == "DEVICE_COMMAND":
            await self._handle_dashboard_device_command(data)
        else:
            logger.debug("ws.unknown_message", type=msg_type, client=client.client_id)

    async def _handle_heartbeat(self, client: ConnectedClient, data: dict) -> None:
        """Handle heartbeat from ESP32 or dashboard."""
        client.last_heartbeat = datetime.now(timezone.utc)
        await self.send_to_client(client.client_id, {
            "type": "HEARTBEAT_ACK",
            "server_time": datetime.now(timezone.utc).isoformat(),
        })

    async def _handle_voice_event(self, client: ConnectedClient, data: dict) -> None:
        """Forward voice events to the voice pipeline via event bus."""
        await self.event_bus.publish(JarvisEvent(
            type=data["type"],
            source="esp32",
            message_id=data.get("message_id"),
            data=data,
        ))

    async def _handle_device_state(self, client: ConnectedClient, data: dict) -> None:
        """Handle device state confirmation from ESP32 (via node ACK)."""
        device_id = data.get("device_id")
        state = data.get("state")
        if device_id and state:
            await self.device_manager.confirm_state(
                device_id=device_id,
                state=state,
                message_id=data.get("message_id"),
            )

    async def _handle_node_heartbeat(self, client: ConnectedClient, data: dict) -> None:
        """Handle node heartbeat forwarded by ESP32."""
        node_id = data.get("node_id")
        if node_id:
            await self.node_manager.process_heartbeat(node_id, data)

    async def _handle_music_command(self, data: dict) -> None:
        """Forward music commands to music manager via event bus."""
        await self.event_bus.publish(JarvisEvent(
            type="MUSIC_COMMAND",
            source="dashboard",
            data=data,
        ))

    async def _handle_dashboard_device_command(self, data: dict) -> None:
        """Handle device control from dashboard via WebSocket."""
        device_id = data.get("device_id")
        action = data.get("action")
        if device_id and action:
            await self.device_manager.execute_command(
                device_id=device_id,
                action=action,
                source="dashboard",
            )


# ---- WebSocket Endpoint ----

async def websocket_endpoint(websocket: WebSocket):
    """FastAPI WebSocket endpoint handler."""
    await websocket.accept()

    # Get app state
    ws_manager: WebSocketManager = websocket.app.state.ws_manager

    client: Optional[ConnectedClient] = None

    try:
        # First message must be AUTH
        auth_data = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)

        if auth_data.get("type") != "AUTH":
            await websocket.send_json({
                "type": "AUTH_RESPONSE",
                "success": False,
                "error": "First message must be AUTH",
            })
            await websocket.close()
            return

        # Authenticate
        auth_result = await authenticate_websocket(
            websocket, auth_data.get("token", "")
        )

        if not auth_result:
            await websocket.send_json({
                "type": "AUTH_RESPONSE",
                "success": False,
                "error": "Authentication failed",
                "server_time": datetime.now(timezone.utc).isoformat(),
            })
            await websocket.close()
            return

        # Create client
        client_id = auth_data.get("client_id", f"client_{id(websocket)}")
        client_type = auth_data.get("client_type", "dashboard")
        client = ConnectedClient(websocket, client_id, client_type)
        client.authenticated = True
        client.auth_info = auth_result

        await ws_manager.connect(client)

        # Log operating Wi-Fi channel for gateway devices
        wifi_channel = auth_data.get("wifi_channel")
        if wifi_channel is not None:
            logger.info("ws.gateway_wifi_channel", client_id=client_id, wifi_channel=wifi_channel)

        # Send auth success
        await websocket.send_json({
            "type": "AUTH_RESPONSE",
            "success": True,
            "server_time": datetime.now(timezone.utc).isoformat(),
        })

        # Message loop
        while True:
            data = await websocket.receive_json()
            await ws_manager.process_message(client, data)

    except WebSocketDisconnect:
        pass
    except asyncio.TimeoutError:
        logger.warning("ws.auth_timeout")
    except Exception as e:
        logger.error("ws.error", error=str(e))
    finally:
        if client:
            await ws_manager.disconnect(client.client_id)
