"""
JARVIS — Scene Manager

Manages the execution of multi-device smart home scenes.
Supports delays, sequential actions, and Spotify control integration.
"""

import asyncio
from typing import Dict, List, Optional, Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.events import EventBus, JarvisEvent
from app.db.database import DatabaseManager
from app.db.models import Scene, SceneAction

import structlog

logger = structlog.get_logger("jarvis.scenes")


class SceneManager:
    """Manages scene loading and sequential action execution."""

    def __init__(self, db: DatabaseManager, event_bus: EventBus, device_manager):
        self.db = db
        self.event_bus = event_bus
        self.device_manager = device_manager

        # Subscribe to SCENE_ACTIVATE events (triggered via voice, automations, etc.)
        self.event_bus.subscribe("SCENE_ACTIVATE", self._on_scene_activate_event)

    async def execute_scene(self, scene_id: int) -> bool:
        """Execute a scene by ID sequentially."""
        async with self.db.get_session() as session:
            result = await session.execute(
                select(Scene)
                .options(selectinload(Scene.actions))
                .where(Scene.id == scene_id)
            )
            scene = result.scalar_one_or_none()
            if not scene:
                logger.warning("scenes.not_found", scene_id=scene_id)
                return False

            logger.info("scenes.executing", scene_id=scene_id, name=scene.name)

            # Sort actions by execution order
            actions = sorted(scene.actions, key=lambda x: x.order)

            # Run in background to prevent blocking HTTP endpoints
            asyncio.create_task(self._run_actions(actions, scene.name))
            return True

    async def execute_scene_by_name(self, scene_name: str) -> bool:
        """Fuzzy match scene by name and execute."""
        async with self.db.get_session() as session:
            result = await session.execute(
                select(Scene)
                .options(selectinload(Scene.actions))
                .where(Scene.name.ilike(scene_name))
            )
            scene = result.scalar_one_or_none()
            if not scene:
                # Try partial match
                result = await session.execute(
                    select(Scene)
                    .options(selectinload(Scene.actions))
                    .where(Scene.name.ilike(f"%{scene_name}%"))
                )
                scene = result.scalar_one_or_none()

            if not scene:
                logger.warning("scenes.match_failed", name=scene_name)
                return False

            return await self.execute_scene(scene.id)

    async def _run_actions(self, actions: List[SceneAction], scene_name: str) -> None:
        """Worker loop to process scene actions sequentially."""
        try:
            for idx, action in enumerate(actions):
                logger.info(
                    "scenes.action_start",
                    scene=scene_name,
                    step=idx + 1,
                    type=action.action_type
                )
                
                if action.action_type == "device_control":
                    device_id = action.target
                    if device_id:
                        await self.device_manager.execute_command(
                            device_id=device_id,
                            action=action.action,
                            source=f"scene_{scene_name}"
                        )
                
                elif action.action_type == "music_control":
                    # Emit Spotify command to event bus
                    await self.event_bus.publish(JarvisEvent(
                        type="MUSIC_COMMAND",
                        source=f"scene_{scene_name}",
                        data={
                            "action": action.action,
                            "query": action.parameters.get("query"),
                            "value": action.parameters.get("value")
                        }
                    ))
                
                elif action.action_type == "delay":
                    delay_secs = float(action.parameters.get("seconds", 1.0))
                    await asyncio.sleep(delay_secs)

            logger.info("scenes.execution_completed", scene=scene_name)
            
            await self.event_bus.publish(JarvisEvent(
                type="NOTIFICATION",
                source="scenes",
                data={
                    "level": "info",
                    "title": "Scene Activated",
                    "message": f"Successfully activated scene: {scene_name}"
                }
            ))

        except Exception as e:
            logger.error("scenes.execution_failed", scene=scene_name, error=str(e))
            await self.event_bus.publish(JarvisEvent(
                type="NOTIFICATION",
                source="scenes",
                data={
                    "level": "error",
                    "title": "Scene Failed",
                    "message": f"Failed executing scene {scene_name}: {e}"
                }
            ))

    async def _on_scene_activate_event(self, event: JarvisEvent) -> None:
        """Handle incoming activation request event."""
        scene_name = event.data.get("scene_name")
        if scene_name:
            await self.execute_scene_by_name(scene_name)

