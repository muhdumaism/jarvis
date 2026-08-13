"""
JARVIS — Automation Schemas

Schemas for CRUD and test operations on automations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AutomationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = ""
    enabled: bool = True
    trigger_type: str = Field(..., pattern=r"^(time|temperature|device_state|sensor)$")
    trigger_config: Dict[str, Any]
    # Examples:
    # time: {"cron": "0 23 * * *"} or {"time": "23:00"}
    # temperature: {"sensor_id": "...", "operator": ">", "value": 28}
    # device_state: {"device_id": "...", "state": "on"}
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]]
    # Example: [{"device_id": "room_fan", "action": "turn_on"}]
    cooldown_seconds: int = Field(default=30, ge=0)


class AutomationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    enabled: Optional[bool] = None
    trigger_type: Optional[str] = Field(None, pattern=r"^(time|temperature|device_state|sensor)$")
    trigger_config: Optional[Dict[str, Any]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    cooldown_seconds: Optional[int] = Field(None, ge=0)


class AutomationResponse(BaseModel):
    id: int
    name: str
    description: str
    enabled: bool
    trigger_type: str
    trigger_config: Dict[str, Any]
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    cooldown_seconds: int
    last_triggered: Optional[datetime] = None
    trigger_count: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
