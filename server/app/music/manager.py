"""
JARVIS — Music Manager

Orchestrates polling Spotify playback state, broadcasting changes, and handling commands.
"""

import asyncio
import time
from typing import Optional, Any, Dict

from app.core.config import settings
from app.core.events import EventBus, JarvisEvent
from app.music.spotify_bridge import SpotifyBridge
from app.system.audio import is_bluetooth_speaker_connected, get_current_audio_output

import structlog

logger = structlog.get_logger("jarvis.music.manager")


class MusicManager:
    """Manages active Spotify bridge polling and music event handling."""

    def __init__(self, event_bus: EventBus, db=None):
        self.event_bus = event_bus
        self.db = db
        self.bridge = SpotifyBridge()
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None
        self._last_state: Optional[dict] = None
        self._speaker_connected: Optional[bool] = None
        self._last_alert_time: float = 0

    async def initialize(self) -> None:
        """Initialize Spotify bridge and start periodic polling task."""
        # Query db for refresh token if db is available
        db_refresh_token = None
        if self.db:
            try:
                db_refresh_token = await self._get_db_setting("spotify_refresh_token")
            except Exception as e:
                logger.error("music.failed_to_load_db_refresh_token", error=str(e))
        
        await self.bridge.initialize(db_refresh_token=db_refresh_token)
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_spotify_state())

        # Subscribe to internal music command events
        self.event_bus.subscribe("MUSIC_COMMAND", self._on_music_command)
        logger.info("music.manager.initialized")

    async def stop(self) -> None:
        """Stop polling task."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
                
        logger.info("music.manager.stopped")

    @property
    def is_connected(self) -> bool:
        return self.bridge.is_connected

    async def get_state(self) -> dict:
        """Return cached or current Spotify playback state along with speaker status."""
        speaker_name = await self._get_db_setting("bluetooth_speaker_name", settings.bluetooth_speaker_name)
        spk_conn = is_bluetooth_speaker_connected(speaker_name)
        curr_output = get_current_audio_output()

        if not self.bridge.is_connected:
            return {
                "is_playing": False,
                "track": None,
                "speaker_connected": spk_conn,
                "current_output_device": curr_output
            }
        
        state = await self.bridge.get_playback_state()
        state_data = state or {"is_playing": False, "track": None}
        state_data["speaker_connected"] = spk_conn
        state_data["current_output_device"] = curr_output
        return state_data

    async def _get_db_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        if not self.db:
            return default
        try:
            async with self.db.get_session() as session:
                from sqlalchemy import select
                from app.db.models import Setting
                result = await session.execute(select(Setting).where(Setting.key == key))
                setting = result.scalar_one_or_none()
                if setting and setting.value is not None:
                    return setting.value
        except Exception as e:
            logger.debug("music.db_setting_error", key=key, error=str(e))
        return default

    async def _poll_spotify_state(self) -> None:
        """Periodically check Spotify playback state and notify subscribers if changed."""
        await asyncio.sleep(2) # Let the server startup settle
        
        while self._running:
            try:
                # 1. Poll Bluetooth Speaker connection status
                speaker_name = await self._get_db_setting("bluetooth_speaker_name", settings.bluetooth_speaker_name)
                spk_conn = is_bluetooth_speaker_connected(speaker_name)
                
                if spk_conn != self._speaker_connected:
                    self._speaker_connected = spk_conn
                    # Broadcast speaker connection state changes to WebSocket clients/dashboard
                    await self.event_bus.publish(JarvisEvent(
                        type="speaker_state",
                        source="system",
                        data={"connected": spk_conn}
                    ))
                    logger.info("music.speaker_state_changed", connected=spk_conn, speaker_name=speaker_name)

                # 2. Poll Spotify playback state
                if self.bridge.is_connected:
                    state = await self.bridge.get_playback_state()
                    
                    if state:
                        # Append Bluetooth speaker status to state payload
                        state["speaker_connected"] = spk_conn
                        state["current_output_device"] = get_current_audio_output()
                        
                        # Handle case where Spotify is active but Bluetooth speaker is offline
                        if state.get("is_playing") and not spk_conn:
                            now = time.time()
                            if now - self._last_alert_time > 60: # Rate-limit voice warnings to 1 min
                                self._last_alert_time = now
                                await self.event_bus.publish(JarvisEvent(
                                    type="TTS_SPEAK",
                                    source="music_manager",
                                    data={"text": "The Bluetooth speaker is disconnected."}
                                ))
                        
                        if state != self._last_state:
                            self._last_state = state
                            # Broadcast state change to clients
                            await self.event_bus.publish(JarvisEvent(
                                type="MUSIC_STATE",
                                source="spotify",
                                data=state
                            ))
                else:
                    # Retry database refresh token lookup and initialization occasionally if not connected
                    db_refresh_token = await self._get_db_setting("spotify_refresh_token")
                    await self.bridge.initialize(db_refresh_token=db_refresh_token)

            except Exception as e:
                logger.error("music.polling_failed", error=str(e))

            await asyncio.sleep(settings.spotify_poll_interval)

    async def _on_music_command(self, event: JarvisEvent) -> None:
        """Process command event received from Event Bus."""
        action = event.data.get("action")
        query = event.data.get("query")
        value = event.data.get("value")

        if not action:
            return

        # Double check speaker connection before attempting playback commands
        if action in ["play", "resume", "search_play"]:
            speaker_name = await self._get_db_setting("bluetooth_speaker_name", settings.bluetooth_speaker_name)
            if not is_bluetooth_speaker_connected(speaker_name):
                # Alert user speaker is disconnected and prevent false success reports
                await self.event_bus.publish(JarvisEvent(
                    type="TTS_SPEAK",
                    source="music_manager",
                    data={"text": "Cannot play music. The Bluetooth speaker is disconnected."}
                ))
                await self.event_bus.publish(JarvisEvent(
                    type="speaker_state",
                    source="system",
                    data={"connected": False}
                ))
                return

        logger.info("music.processing_command", action=action, query=query, value=value)
        success = await self.bridge.execute_command(action, query, value)

        if success:
            # Force status poll immediately to update UI quickly
            state = await self.get_state()
            if state:
                self._last_state = state
                await self.event_bus.publish(JarvisEvent(
                    type="MUSIC_STATE",
                    source="spotify",
                    data=state
                ))
        else:
            await self.event_bus.publish(JarvisEvent(
                type="ERROR",
                source="music",
                data={
                    "code": "SPOTIFY_UNAVAILABLE",
                    "message": "Failed to execute command. Is Spotify running on the PC?"
                }
            ))
            logger.warning("music.command_execution_failed", action=action)
