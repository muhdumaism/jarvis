"""
JARVIS — API Master Router

Combines all modular routers (auth, rooms, devices, nodes, music, automations, scenes, firmware, settings, system, events).
"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.rooms import router as rooms_router
from app.api.settings import router as settings_router
from app.api.system import router as system_router
from app.api.events import router as events_router
from app.devices.router import router as devices_router
from app.nodes.router import router as nodes_router
from app.music.router import router as music_router
from app.automation.router import router as automation_router
from app.scenes.router import router as scenes_router
from app.firmware.router import router as firmware_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(rooms_router)
api_router.include_router(devices_router)
api_router.include_router(nodes_router)
api_router.include_router(music_router)
api_router.include_router(automation_router)
api_router.include_router(scenes_router)
api_router.include_router(firmware_router)
api_router.include_router(settings_router)
api_router.include_router(system_router)
api_router.include_router(events_router)
