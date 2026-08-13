"""
JARVIS — Scene Schemas

Schemas for scene creation, updates, and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SceneActionCreate(BaseModel):
    order: int = Field(default=0, ge=0)
    action_type: str = Field(..., pattern=r"^(device_control|music_control|delay)$")
    target: Optional[str] = None
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SceneActionResponse(BaseModel):
    id: int
    order: int
    action_type: str
    target: Optional[str] = None
    action: str
    parameters: Dict[str, Any]


class SceneCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = ""
    icon: Optional[str] = "layers"
    actions: List[SceneActionCreate] = Field(default_factory=list)


class SceneUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    icon: Optional[str] = None
    actions: Optional[List[SceneActionCreate]] = None


class SceneResponse(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    actions: List[SceneActionResponse]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
