"""
JARVIS — Node Schemas

Pydantic models for node validation and API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NodeCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    name: str = Field(..., min_length=1, max_length=128)
    room_id: str = Field(..., min_length=1, max_length=64)
    mac_address: Optional[str] = Field(None, pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
    chip_type: str = Field(default="esp32s3")
    config: dict = Field(default_factory=dict)


class NodeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    room_id: Optional[str] = None
    mac_address: Optional[str] = None
    chip_type: Optional[str] = None
    config: Optional[dict] = None


class NodeResponse(BaseModel):
    id: str
    name: str
    room_id: str
    mac_address: Optional[str]
    chip_type: str
    firmware_version: str
    status: str
    last_seen: Optional[datetime]
    uptime: int
    free_heap: int
    device_count: int = 0
    config: dict
    created_at: Optional[datetime]
