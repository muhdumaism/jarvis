"""
JARVIS — Device Schemas

Pydantic models for device validation, API requests/responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class DeviceCreate(BaseModel):
    """Schema for creating a new device."""
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    name: str = Field(..., min_length=1, max_length=128)
    room_id: str = Field(..., min_length=1, max_length=64)
    node_id: str = Field(..., min_length=1, max_length=64)
    type: str = Field(default="relay")
    channel: int = Field(default=0, ge=0, le=7)
    capabilities: List[str] = Field(default=["on", "off", "toggle"])
    metadata: dict = Field(default_factory=dict)


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    room_id: Optional[str] = None
    node_id: Optional[str] = None
    channel: Optional[int] = Field(None, ge=0, le=7)
    capabilities: Optional[List[str]] = None
    metadata: Optional[dict] = None


class DeviceResponse(BaseModel):
    """Schema for device API response."""
    id: str
    name: str
    room_id: str
    node_id: str
    type: str
    channel: int
    capabilities: List[str]
    state: str
    confirmed: bool
    last_changed: Optional[datetime]
    metadata: dict
    online: bool = False  # Computed from node status
    created_at: Optional[datetime]


class DeviceControlRequest(BaseModel):
    """Schema for device control action."""
    action: str = Field(..., pattern=r"^(turn_on|turn_off|toggle)$")
    source: str = Field(default="dashboard")


class DeviceControlResponse(BaseModel):
    """Response after issuing a device command."""
    message_id: str
    device_id: str
    action: str
    state: str  # "pending", "confirmed", "failed"
    message: str


class DeviceStateResponse(BaseModel):
    """Schema for device state."""
    device_id: str
    state: str
    confirmed: bool
    source: str
    message_id: Optional[str]
    changed_at: Optional[datetime]
