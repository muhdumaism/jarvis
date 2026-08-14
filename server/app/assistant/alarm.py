"""
JARVIS — Alarm Manager

Manages timer-based and time-of-day alarms.
Triggers looping warnings on the PC speaker and broadcasts events.
"""

import asyncio
import datetime
import winsound
import time
import uuid
from typing import Dict, Any, Tuple
import structlog
from app.core.events import EventBus, JarvisEvent

logger = structlog.get_logger("jarvis.alarm")


class AlarmManager:
    """Manages scheduling and triggering of alarms."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.active_alarms: Dict[str, Tuple[datetime.datetime, asyncio.Task]] = {}
        self.is_alarm_ringing = False

    async def set_alarm(self, time_str: str, am_pm: str = None) -> str:
        """Set an alarm for a specific time today/tomorrow.
        
        Args:
            time_str: Time in "HH:MM" format.
            am_pm: Optional "AM" or "PM" modifier.
            
        Returns:
            A formatted string of the set time (e.g. "07:30 PM").
        """
        try:
            now = datetime.datetime.now()
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])

            if am_pm:
                am_pm = am_pm.upper()
                if am_pm == "PM" and hour < 12:
                    hour += 12
                elif am_pm == "AM" and hour == 12:
                    hour = 0

            alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if alarm_time <= now:
                # If the time is in the past, schedule it for tomorrow
                alarm_time += datetime.timedelta(days=1)

            delay = (alarm_time - now).total_seconds()
            alarm_id = str(uuid.uuid4())[:8]

            # Cancel existing alarm at the exact same minute to prevent duplicate beeping
            for existing_id, (existing_time, existing_task) in list(self.active_alarms.items()):
                if existing_time == alarm_time:
                    existing_task.cancel()
                    del self.active_alarms[existing_id]

            # Schedule the task
            task = asyncio.create_task(self._run_alarm_timer(alarm_id, delay))
            self.active_alarms[alarm_id] = (alarm_time, task)

            logger.info("alarm.scheduled", alarm_id=alarm_id, time=alarm_time.isoformat(), delay=delay)
            return alarm_time.strftime("%I:%M %p")
        except Exception as e:
            logger.error("alarm.set_failed", error=str(e))
            raise ValueError(f"Failed to set alarm: {e}")

    async def set_alarm_delay(self, minutes: float) -> str:
        """Set an alarm to trigger after a certain number of minutes.
        
        Returns:
            A formatted string of the trigger time (e.g. "06:15 PM").
        """
        now = datetime.datetime.now()
        alarm_time = now + datetime.timedelta(minutes=minutes)
        delay = minutes * 60.0
        alarm_id = str(uuid.uuid4())[:8]

        task = asyncio.create_task(self._run_alarm_timer(alarm_id, delay))
        self.active_alarms[alarm_id] = (alarm_time, task)

        logger.info("alarm.scheduled_delay", alarm_id=alarm_id, time=alarm_time.isoformat(), delay=delay)
        return alarm_time.strftime("%I:%M %p")

    async def stop_ringing(self) -> bool:
        """Stop any currently ringing alarm and cancel any immediate active beepers."""
        if self.is_alarm_ringing:
            self.is_alarm_ringing = False
            # Stop Windows sound playback
            try:
                winsound.PlaySound(None, 0)
            except Exception:
                pass
            logger.info("alarm.ringing_stopped")
            await self.event_bus.publish(JarvisEvent(
                type="ALARM_STOPPED",
                source="alarm_manager",
                data={}
            ))
            return True
        return False

    async def _run_alarm_timer(self, alarm_id: str, delay: float):
        """Timer task that sleeps until target time, then triggers ringing."""
        try:
            await asyncio.sleep(delay)
            self.is_alarm_ringing = True
            logger.info("alarm.triggered", alarm_id=alarm_id)

            # Clean up task reference
            if alarm_id in self.active_alarms:
                del self.active_alarms[alarm_id]

            # Broadcast event to WebSockets/ESP32 (flashes screen, etc.)
            await self.event_bus.publish(JarvisEvent(
                type="ALARM_TRIGGERED",
                source="alarm_manager",
                data={"alarm_id": alarm_id}
            ))

            # Loop system alert sound on default Windows PC output
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._play_alarm_loop)

        except asyncio.CancelledError:
            logger.info("alarm.cancelled", alarm_id=alarm_id)

    def _play_alarm_loop(self):
        """Synchronous loop to play native system beeps on the Windows thread."""
        try:
            # Play a looping System warning sound asynchronously
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_LOOP)
            # Stay inside this thread block until is_alarm_ringing is cancelled
            while self.is_alarm_ringing:
                time.sleep(0.5)
            winsound.PlaySound(None, 0)
        except Exception as e:
            logger.error("alarm.playback_error", error=str(e))
