"""
JARVIS — Automation Engine

Listens to device state changes, sensor updates, and time events to trigger user-defined automations.
Implements cooldown checks and automation loop protection.
"""

import asyncio
from datetime import datetime, timezone
import json
from typing import Dict, List, Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.events import EventBus, JarvisEvent
from app.db.database import DatabaseManager
from app.db.models import Automation, AutomationRun

import structlog

logger = structlog.get_logger("jarvis.automation")


class AutomationEngine:
    """Evaluates time, sensor, and state triggers to run automations."""

    def __init__(self, db: DatabaseManager, event_bus: EventBus, device_manager):
        self.db = db
        self.event_bus = event_bus
        self.device_manager = device_manager
        self._automations: Dict[int, dict] = {}
        self._running = False
        self._time_trigger_task: Optional[asyncio.Task] = None
        self._loop_tracker: Dict[int, List[float]] = {}  # Track runs per automation to prevent loops

    async def start(self) -> None:
        """Start the automation engine and load rules."""
        self._running = True
        await self.load_automations()

        # Subscribe to device state changes and sensor data events
        self.event_bus.subscribe("DEVICE_STATE_CHANGED", self._on_device_state_changed)
        self.event_bus.subscribe("SENSOR_DATA", self._on_sensor_data)

        # Start periodic time trigger evaluation task
        self._time_trigger_task = asyncio.create_task(self._time_checker_loop())
        logger.info("automation.engine.started", count=len(self._automations))

    async def stop(self) -> None:
        """Stop automation tasks."""
        self._running = False
        if self._time_trigger_task:
            self._time_trigger_task.cancel()
            try:
                await self._time_trigger_task
            except asyncio.CancelledError:
                pass
        logger.info("automation.engine.stopped")

    async def load_automations(self) -> None:
        """Load all enabled automations from the database."""
        async with self.db.get_session() as session:
            result = await session.execute(
                select(Automation).where(Automation.enabled == True)
            )
            autos = result.scalars().all()
            
            self._automations.clear()
            for auto in autos:
                self._automations[auto.id] = {
                    "id": auto.id,
                    "name": auto.name,
                    "trigger_type": auto.trigger_type,
                    "trigger_config": auto.trigger_config,
                    "conditions": auto.conditions or [],
                    "actions": auto.actions,
                    "cooldown_seconds": auto.cooldown_seconds,
                    "last_triggered": auto.last_triggered,
                }

    # ---- Event Subscriptions ----

    async def _on_device_state_changed(self, event: JarvisEvent) -> None:
        """Triggered when a device changes state."""
        device_id = event.data.get("device_id")
        state = event.data.get("state")
        
        if not device_id or not state:
            return

        for auto_id, auto in list(self._automations.items()):
            if auto["trigger_type"] == "device_state":
                cfg = auto["trigger_config"]
                if cfg.get("device_id") == device_id and cfg.get("state") == state:
                    await self.trigger_automation(auto_id, trigger_data=event.data)

    async def _on_sensor_data(self, event: JarvisEvent) -> None:
        """Triggered when sensor data arrives."""
        sensor_id = event.data.get("sensor_id")
        sensor_type = event.data.get("sensor_type")
        value = event.data.get("value")

        if not sensor_id or value is None:
            return

        for auto_id, auto in list(self._automations.items()):
            if auto["trigger_type"] in ("temperature", "sensor"):
                cfg = auto["trigger_config"]
                if cfg.get("sensor_id") == sensor_id:
                    operator = cfg.get("operator", "==")
                    target_val = cfg.get("value")
                    
                    if self._evaluate_condition(value, operator, target_val):
                        await self.trigger_automation(auto_id, trigger_data=event.data)

    # ---- Time Checker Loop ----

    async def _time_checker_loop(self) -> None:
        """Runs once a minute to check time-based triggers."""
        while self._running:
            try:
                # Wait until the start of the next minute
                now = datetime.now()
                sleep_seconds = 60 - now.second - (now.microsecond / 1000000.0)
                await asyncio.sleep(sleep_seconds)

                if not self._running:
                    break

                now_time = datetime.now().strftime("%H:%M")
                
                for auto_id, auto in list(self._automations.items()):
                    if auto["trigger_type"] == "time":
                        cfg = auto["trigger_config"]
                        if cfg.get("time") == now_time:
                            await self.trigger_automation(auto_id, trigger_data={"time": now_time})

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("automation.time_loop_failed", error=str(e))

    # ---- Execution & Validation ----

    def _evaluate_condition(self, val: Any, operator: str, target: Any) -> bool:
        """Evaluate logical condition operator."""
        try:
            val = float(val)
            target = float(target)
        except (ValueError, TypeError):
            pass

        try:
            if operator == "==" or operator == "equals":
                return val == target
            elif operator == "!=":
                return val != target
            elif operator == ">":
                return val > target
            elif operator == "<":
                return val < target
            elif operator == ">=":
                return val >= target
            elif operator == "<=":
                return val <= target
        except Exception:
            return False
        return False

    async def trigger_automation(self, auto_id: int, trigger_data: Optional[dict] = None) -> bool:
        """Trigger an automation by ID. Verifies cooldown and loop limits."""
        auto = self._automations.get(auto_id)
        if not auto:
            return False

        now = datetime.now(timezone.utc)

        # 1. Cooldown verification
        if auto["last_triggered"]:
            last_trig = auto["last_triggered"]
            if last_trig.tzinfo is None:
                last_trig = last_trig.replace(tzinfo=timezone.utc)
            
            elapsed = (now - last_trig).total_seconds()
            if elapsed < auto["cooldown_seconds"]:
                logger.debug("automation.cooldown_active", auto_id=auto_id, elapsed=elapsed)
                return False

        # 2. Loop detection check (prevent spamming multiple runs in short timeframe)
        if self._detect_loop(auto_id):
            logger.warning("automation.loop_detected", auto_id=auto_id, message="Disabling to prevent loop.")
            await self.disable_automation(auto_id)
            await self.event_bus.publish(JarvisEvent(
                type="NOTIFICATION",
                source="automation",
                data={
                    "level": "error",
                    "title": f"Loop Blocked: {auto['name']}",
                    "message": "Automation disabled automatically to prevent infinite loops."
                }
            ))
            return False

        logger.info("automation.triggered", auto_id=auto_id, name=auto["name"])

        # Update last triggered locally
        auto["last_triggered"] = now

        # Execute actions
        actions_executed = []
        success = True
        error_msg = None

        try:
            for action in auto["actions"]:
                device_id = action.get("device_id")
                act_name = action.get("action")
                if device_id and act_name:
                    await self.device_manager.execute_command(
                        device_id=device_id,
                        action=act_name,
                        source=f"automation_{auto_id}"
                    )
                    actions_executed.append(action)
        except Exception as e:
            success = False
            error_msg = str(e)
            logger.error("automation.execution_error", auto_id=auto_id, error=error_msg)

        # Log run to database
        async with self.db.get_session() as session:
            run = AutomationRun(
                automation_id=auto_id,
                triggered_at=now,
                trigger_data=trigger_data,
                actions_executed=actions_executed,
                success=success,
                error=error_msg
            )
            session.add(run)

            # Update stats on automation model
            result = await session.execute(
                select(Automation).where(Automation.id == auto_id)
            )
            db_auto = result.scalar_one_or_none()
            if db_auto:
                db_auto.last_triggered = now
                db_auto.trigger_count += 1
                
            await session.commit()

        await self.event_bus.publish(JarvisEvent(
            type="NOTIFICATION",
            source="automation",
            data={
                "level": "info" if success else "error",
                "title": f"Automation Run: {auto['name']}",
                "message": f"Successfully ran {len(actions_executed)} actions." if success else f"Run failed: {error_msg}"
            }
        ))

        return success

    def _detect_loop(self, auto_id: int) -> bool:
        """Return True if automation ran > 3 times in 10 seconds."""
        now = datetime.now().timestamp()
        if auto_id not in self._loop_tracker:
            self._loop_tracker[auto_id] = []

        # Prune runs older than 10 seconds
        self._loop_tracker[auto_id] = [t for t in self._loop_tracker[auto_id] if now - t < 10.0]
        self._loop_tracker[auto_id].append(now)

        return len(self._loop_tracker[auto_id]) > 3

    async def disable_automation(self, auto_id: int) -> None:
        """Helper to disable an automation after loops or manually."""
        if auto_id in self._automations:
            del self._automations[auto_id]

        async with self.db.get_session() as session:
            result = await session.execute(
                select(Automation).where(Automation.id == auto_id)
            )
            db_auto = result.scalar_one_or_none()
            if db_auto:
                db_auto.enabled = False
                await session.commit()
            logger.info("automation.disabled", auto_id=auto_id)
