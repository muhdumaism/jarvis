"""
JARVIS — Intent Definitions

All valid intents and their structures.
The AI must only output these specific intent types.
"""

from typing import Optional, List
from pydantic import BaseModel


class DeviceControlIntent(BaseModel):
    """Intent to control a device."""
    intent: str = "device_control"
    target: str  # device_id
    action: str  # turn_on, turn_off, toggle


class MusicControlIntent(BaseModel):
    """Intent to control music."""
    intent: str = "music_control"
    action: str  # play, pause, next, previous, volume
    query: Optional[str] = None  # Search query for play
    value: Optional[int] = None  # Volume value


class RoomQueryIntent(BaseModel):
    """Intent to query room information."""
    intent: str = "room_query"
    query: str  # temperature, humidity, device_status


class SceneActivateIntent(BaseModel):
    """Intent to activate a scene."""
    intent: str = "scene_activate"
    scene_name: str


class AutomationControlIntent(BaseModel):
    """Intent to control automations."""
    intent: str = "automation_control"
    action: str  # enable, disable, list
    automation_name: Optional[str] = None


class ConversationIntent(BaseModel):
    """Intent for general conversation (no device action)."""
    intent: str = "conversation"
    response: str


class UnknownIntent(BaseModel):
    """When the AI cannot determine an intent."""
    intent: str = "unknown"
    raw_text: str


# Valid intent types
VALID_INTENTS = {
    "device_control",
    "music_control",
    "room_query",
    "scene_activate",
    "automation_control",
    "conversation",
    "unknown",
}

# Valid device actions
VALID_DEVICE_ACTIONS = {"turn_on", "turn_off", "toggle"}

# Valid music actions
VALID_MUSIC_ACTIONS = {"play", "pause", "resume", "next", "previous", "volume", "search_play"}
