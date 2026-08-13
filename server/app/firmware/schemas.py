"""
JARVIS — Firmware Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FirmwareUploadResponse(BaseModel):
    id: int
    version: str
    chip_type: str
    target: str
    filename: str
    file_size: int
    sha256: str
    description: str
    uploaded_at: datetime


class FirmwareVersionResponse(BaseModel):
    id: int
    version: str
    chip_type: str
    target: str
    filename: str
    file_size: int
    sha256: str
    description: str
    uploaded_at: datetime
