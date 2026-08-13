"""
JARVIS — System Status and Diagnostics API Router
"""

import time
import psutil
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.security import get_current_user

router = APIRouter(prefix="/system", tags=["system"])


class SystemStatusResponse(BaseModel):
    server_uptime: int
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    db_size_mb: float
    ws_connections: int
    stt_status: str
    tts_status: str
    ai_status: str
    spotify_status: str


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    request: Request,
    _user=Depends(get_current_user)
):
    """Retrieve server resource usage diagnostics and subsystem statuses."""
    # Subsystem instances from app state
    ws_manager = request.app.state.ws_manager
    voice_pipeline = request.app.state.voice_pipeline
    music_manager = request.app.state.music_manager
    db = request.app.state.db

    # Resource metrics
    process = psutil.Process()
    uptime = int(time.time() - process.create_time())
    
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    # DB stats
    db_size = 0.0
    try:
        db_stats = await db.get_stats()
        db_size = db_stats.get("size_mb", 0.0)
    except Exception:
        pass

    return SystemStatusResponse(
        server_uptime=uptime,
        cpu_percent=cpu,
        ram_percent=ram,
        disk_percent=disk,
        db_size_mb=db_size,
        ws_connections=ws_manager.connection_count,
        stt_status=voice_pipeline.stt_status,
        tts_status=voice_pipeline.tts_status,
        ai_status=voice_pipeline.ai_status,
        spotify_status="connected" if music_manager.is_connected else "disconnected"
    )
