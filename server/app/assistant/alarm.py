"""
JARVIS — Alarm & Timer Manager

Manages timer-based and time-of-day alarms/timers.
Triggers looping warnings on the PC speaker and broadcasts events.
"""

import asyncio
import datetime
import winsound
import time
import uuid
import re
from typing import Dict, Any, Tuple
import structlog
from app.core.events import EventBus, JarvisEvent

logger = structlog.get_logger("jarvis.alarm")


class AlarmManager:
    """Manages scheduling and triggering of alarms and timers."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.active_alarms: Dict[str, Tuple[datetime.datetime, asyncio.Task, str]] = {} # id -> (time, task, label)
        self.is_alarm_ringing = False

    async def set_alarm(self, time_str: str, am_pm: str = None) -> str:
        """Set an alarm for a specific time today/tomorrow.
        
        Args:
            time_str: Time in "HH:MM" or "HH" format.
            am_pm: Optional "AM" or "PM" modifier.
            
        Returns:
            A formatted string of the set time (e.g. "07:30 PM").
        """
        try:
            now = datetime.datetime.now()
            
            # Clean up input string
            clean_time = time_str.lower().strip()
            
            # Extract numbers
            numbers = re.findall(r'\d+', clean_time)
            if not numbers:
                raise ValueError("No numbers found in time string")
                
            hour = int(numbers[0])
            minute = int(numbers[1]) if len(numbers) > 1 else 0

            # Detect AM/PM from either argument or time string
            is_pm = False
            is_am = False
            
            if am_pm:
                is_pm = am_pm.upper() == "PM"
                is_am = am_pm.upper() == "AM"
            elif "pm" in clean_time:
                is_pm = True
            elif "am" in clean_time:
                is_am = True

            if is_pm and hour < 12:
                hour += 12
            elif is_am and hour == 12:
                hour = 0

            # Safeguard hour and minute bounds
            hour = max(0, min(23, hour))
            minute = max(0, min(59, minute))

            alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if alarm_time <= now:
                # If the time is in the past, schedule it for tomorrow
                alarm_time += datetime.timedelta(days=1)

            delay = (alarm_time - now).total_seconds()
            alarm_id = str(uuid.uuid4())[:8]

            # Cancel existing alarm at the exact same minute to prevent duplicates
            for existing_id, (existing_time, existing_task, label) in list(self.active_alarms.items()):
                if existing_time == alarm_time:
                    existing_task.cancel()
                    del self.active_alarms[existing_id]

            # Schedule the task
            task = asyncio.create_task(self._run_alarm_timer(alarm_id, delay, "alarm"))
            self.active_alarms[alarm_id] = (alarm_time, task, "alarm")

            logger.info("alarm.scheduled", alarm_id=alarm_id, time=alarm_time.isoformat(), delay=delay)
            return alarm_time.strftime("%I:%M %p")
        except Exception as e:
            logger.error("alarm.set_failed", error=str(e), time_str=time_str, am_pm=am_pm)
            raise ValueError(f"Failed to parse time '{time_str}': {e}")

    async def set_alarm_delay(self, minutes: float, label: str = "alarm") -> str:
        """Set a relative alarm or timer to trigger after a certain number of minutes.
        
        Returns:
            A formatted string of the trigger time (e.g. "06:15 PM").
        """
        now = datetime.datetime.now()
        alarm_time = now + datetime.timedelta(minutes=minutes)
        delay = minutes * 60.0
        alarm_id = str(uuid.uuid4())[:8]

        task = asyncio.create_task(self._run_alarm_timer(alarm_id, delay, label))
        self.active_alarms[alarm_id] = (alarm_time, task, label)

        logger.info("alarm.scheduled_delay", alarm_id=alarm_id, label=label, time=alarm_time.isoformat(), delay=delay)
        return alarm_time.strftime("%I:%M %p")

    async def stop_ringing(self) -> bool:
        """Stop any currently ringing alarm and cancel any active beepers."""
        if self.is_alarm_ringing:
            self.is_alarm_ringing = False
            # Stop Windows sound loops
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

    async def _run_alarm_timer(self, alarm_id: str, delay: float, label: str):
        """Timer task that sleeps until target time, then triggers ringing."""
        try:
            await asyncio.sleep(delay)
            self.is_alarm_ringing = True
            logger.info("alarm.triggered", alarm_id=alarm_id, label=label)

            # Clean up task reference
            if alarm_id in self.active_alarms:
                del self.active_alarms[alarm_id]

            # Broadcast event to WebSockets/ESP32 (flashes screen, etc.)
            await self.event_bus.publish(JarvisEvent(
                type="ALARM_TRIGGERED",
                source="alarm_manager",
                data={"alarm_id": alarm_id, "label": label}
            ))

            # Start background auto-silence safety task (5 minutes = 300 seconds)
            asyncio.create_task(self._auto_silence_timer(300.0))

            # Loop alternating beeps on default Windows output
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._play_alarm_loop)

        except asyncio.CancelledError:
            logger.info("alarm.cancelled", alarm_id=alarm_id)

    async def _auto_silence_timer(self, timeout: float):
        """Automatically silence the alarm after the timeout period if still ringing."""
        await asyncio.sleep(timeout)
        if self.is_alarm_ringing:
            logger.info("alarm.auto_silenced", timeout_seconds=timeout)
            await self.stop_ringing()

    def _play_alarm_loop(self):
        """Synchronous loop to play alternating frequency warning tones on the Windows speaker."""
        try:
            # Play a background system sound loop as backup
            try:
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_LOOP)
            except Exception:
                pass

            # Alternating high-reliability tone beeps
            while self.is_alarm_ringing:
                winsound.Beep(1800, 350)
                
                # Check is_alarm_ringing state in short 50ms intervals
                for _ in range(3):
                    if not self.is_alarm_ringing:
                        break
                    time.sleep(0.05)
                if not self.is_alarm_ringing:
                    break

                winsound.Beep(1400, 350)
                for _ in range(7):
                    if not self.is_alarm_ringing:
                        break
                    time.sleep(0.05)

            winsound.PlaySound(None, 0)
        except Exception as e:
            logger.error("alarm.playback_error", error=str(e))
