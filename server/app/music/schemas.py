"""
JARVIS — Music Schemas

Schemas for Spotify Bridge commands and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TrackInfo(BaseModel):
    title: str
    artist: str
    album: str
    album_art_url: Optional[str] = None
    duration_ms: int
    position_ms: int


class MusicStateResponse(BaseModel):
    is_playing: bool
    track: Optional[TrackInfo] = None
    speaker_connected: Optional[bool] = None
    current_output_device: Optional[str] = None


class MusicControlCommand(BaseModel):
    action: str = Field(..., pattern=r"^(play|pause|resume|next|previous|seek|volume|search_play)$")
    query: Optional[str] = None
    value: Optional[int] = None  # position_ms for seek, volume_percent for volume
