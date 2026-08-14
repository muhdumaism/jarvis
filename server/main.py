"""
JARVIS server — Main Entry Point

Starts the FastAPI server with all services initialized during lifespan.
"""

import os
import sys
import asyncio
import time
import psutil
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.events import EventBus, JarvisEvent
from app.db.database import DatabaseManager
from app.devices.manager import DeviceManager
from app.nodes.manager import NodeManager
from app.websocket.manager import WebSocketManager
from app.voice.pipeline import VoicePipeline
from app.automation.engine import AutomationEngine
from app.scenes.manager import SceneManager
from app.music.manager import MusicManager
from app.firmware.manager import FirmwareManager

import structlog

# Setup logging before anything else
setup_logging()
logger = structlog.get_logger("jarvis.main")


async def periodic_system_status_broadcast(app: FastAPI):
    """Periodically collect system resource stats and publish them to the EventBus."""
    await asyncio.sleep(2) # Let the app initialize fully
    event_bus = app.state.event_bus
    
    while True:
        try:
            ws_manager = app.state.ws_manager
            # Only poll/publish if we have at least one active dashboard client connected
            if ws_manager.connection_count > 0:
                process = psutil.Process()
                uptime = int(time.time() - process.create_time())
                
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                disk = psutil.disk_usage("/").percent

                db_size = 0.0
                try:
                    db_stats = await app.state.db.get_stats()
                    db_size = db_stats.get("size_mb", 0.0)
                except Exception:
                    pass

                data = {
                    "server_uptime": uptime,
                    "cpu_percent": cpu,
                    "ram_percent": ram,
                    "disk_percent": disk,
                    "db_size_mb": db_size,
                    "ws_connections": ws_manager.connection_count,
                    "stt_status": app.state.voice_pipeline.stt_status,
                    "tts_status": app.state.voice_pipeline.tts_status,
                    "ai_status": app.state.voice_pipeline.ai_status,
                    "spotify_status": "connected" if app.state.music_manager.is_connected else "disconnected",
                }
                
                await event_bus.publish(JarvisEvent(
                    type="SYSTEM_STATUS",
                    source="system",
                    data=data
                ))
        except Exception:
            pass
            
        await asyncio.sleep(5) # Broadcast status every 5 seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize and teardown all services."""
    logger.info("jarvis.starting", version="1.0.0")

    # 1. Event bus
    event_bus = EventBus()
    await event_bus.start()
    app.state.event_bus = event_bus

    # 2. Database
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    app.state.db = db

    # 3. Device manager
    device_manager = DeviceManager(db, event_bus)
    await device_manager.initialize()
    app.state.device_manager = device_manager

    # 4. Node manager
    node_manager = NodeManager(db, event_bus)
    await node_manager.initialize()
    app.state.node_manager = node_manager

    # 5. WebSocket manager
    ws_manager = WebSocketManager(event_bus, device_manager, node_manager)
    app.state.ws_manager = ws_manager

    # 6. Music manager (Spotify bridge)
    music_manager = MusicManager(event_bus, db)
    await music_manager.initialize()
    app.state.music_manager = music_manager

    # 7. Voice pipeline (STT + AI + TTS)
    voice_pipeline = VoicePipeline(
        event_bus=event_bus,
        device_manager=device_manager,
        music_manager=music_manager,
    )
    await voice_pipeline.initialize()
    app.state.voice_pipeline = voice_pipeline

    # 8. Automation engine
    automation_engine = AutomationEngine(db, event_bus, device_manager)
    await automation_engine.start()
    app.state.automation_engine = automation_engine

    # 9. Scene manager
    scene_manager = SceneManager(db, event_bus, device_manager)
    app.state.scene_manager = scene_manager

    # 10. Firmware manager
    firmware_manager = FirmwareManager(db, settings.firmware_dir)
    await firmware_manager.initialize()
    app.state.firmware_manager = firmware_manager

    # 11. Start periodic system status broadcaster task
    status_broadcast_task = asyncio.create_task(periodic_system_status_broadcast(app))

    logger.info("jarvis.started", host=settings.server_host, port=settings.server_port)

    yield

    # Shutdown
    logger.info("jarvis.shutting_down")
    status_broadcast_task.cancel()
    try:
        await status_broadcast_task
    except asyncio.CancelledError:
        pass
    await automation_engine.stop()
    await music_manager.stop()
    await voice_pipeline.stop()
    await event_bus.stop()
    await db.close()
    logger.info("jarvis.stopped")


# Create FastAPI application
app = FastAPI(
    title="JARVIS — Local AI Room Assistant",
    description="Production-quality local-first smart-room assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://.*\.localtunnel\.me|https://.*\.ngrok-free\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Import and include routers ---
from app.api.router import api_router
from app.websocket.manager import websocket_endpoint

app.include_router(api_router, prefix="/api")
app.add_api_websocket_route("/ws", websocket_endpoint)

# --- Serve firmware files if directory exists ---
firmware_dir = settings.firmware_dir
if os.path.exists(firmware_dir):
    app.mount("/firmware", StaticFiles(directory=firmware_dir), name="firmware")


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "jarvis", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
