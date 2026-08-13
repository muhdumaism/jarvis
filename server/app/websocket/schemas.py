"""
JARVIS — WebSocket Schemas

All WebSocket message types as defined in PROTOCOL.md.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class WSMessage(BaseModel):
    """Base WebSocket message."""
    type: str
    message_id: Optional[str] = None
    timestamp: Optional[str] = None


class WSAuthMessage(WSMessage):
    type: str = "AUTH"
    token: str
    client_type: str  # "esp32_main", "esp32_node", "dashboard"
    client_id: str
    firmware_version: Optional[str] = None


class WSAuthResponse(WSMessage):
    type: str = "AUTH_RESPONSE"
    success: bool
    server_time: str
    error: Optional[str] = None


class WSHeartbeat(WSMessage):
    type: str = "HEARTBEAT"
    client_id: str
    uptime: int = 0
    free_heap: int = 0
    wifi_rssi: int = 0


class WSHeartbeatAck(WSMessage):
    type: str = "HEARTBEAT_ACK"
    server_time: str


class WSVoiceStart(WSMessage):
    type: str = "VOICE_START"


class WSVoiceAudio(WSMessage):
    type: str = "VOICE_AUDIO"
    audio: str  # Base64 PCM
    seq: int = 0


class WSVoiceEnd(WSMessage):
    type: str = "VOICE_END"


class WSDeviceCommand(WSMessage):
    type: str = "DEVICE_COMMAND"
    device_id: str
    node_id: str
    action: str
    source: str = "server"
    channel: int = 0
    target_state: Optional[str] = None


class WSDeviceStateChanged(WSMessage):
    type: str = "DEVICE_STATE_CHANGED"
    device_id: str
    state: str
    confirmed: bool
    changed_at: Optional[str] = None


class WSDeviceStatePending(WSMessage):
    type: str = "DEVICE_STATE_PENDING"
    device_id: str
    requested_state: str


class WSDeviceStateFailed(WSMessage):
    type: str = "DEVICE_STATE_FAILED"
    device_id: str
    error: str
    code: str = "COMMAND_TIMEOUT"


class WSMusicState(WSMessage):
    type: str = "MUSIC_STATE"
    is_playing: bool = False
    track: Optional[Dict[str, Any]] = None


class WSSystemStatus(WSMessage):
    type: str = "SYSTEM_STATUS"
    server_uptime: int = 0
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    disk_percent: float = 0.0
    db_size_mb: float = 0.0
    ws_connections: int = 0
    stt_status: str = "unknown"
    tts_status: str = "unknown"
    ai_status: str = "unknown"
    spotify_status: str = "unknown"


class WSNotification(WSMessage):
    type: str = "NOTIFICATION"
    level: str = "info"  # info, warning, error
    title: str = ""
    message: str = ""


class WSError(WSMessage):
    type: str = "ERROR"
    code: str
    message: str
    component: str = "server"
