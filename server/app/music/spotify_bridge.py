"""
JARVIS — Spotify Bridge

Interfaces with the Spotify Web API using credentials from settings.
Allows control of the user's existing Spotify playback (on phone, computer, etc.).
"""

import asyncio
from typing import Any, Dict, Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

from app.core.config import settings
import structlog

logger = structlog.get_logger("jarvis.music.spotify")


class SpotifyBridge:
    """Bridges control commands to the Spotify API for the user's current playback session."""

    def __init__(self):
        self.sp: Optional[spotipy.Spotify] = None
        self._auth_manager: Optional[SpotifyOAuth] = None
        self._initialized = False

    async def initialize(self, db_refresh_token: Optional[str] = None) -> None:
        """Initialize the Spotify client with refresh token credentials."""
        token_to_use = db_refresh_token or settings.spotify_refresh_token
        if not settings.spotify_client_id or not settings.spotify_client_secret or not token_to_use:
            logger.warning("spotify.missing_credentials", message="Spotify integration will run in mock/disabled state.")
            self.sp = None
            self._initialized = False
            return

        try:
            # Setup OAuth manager specifically for token refreshing
            self._auth_manager = SpotifyOAuth(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret,
                redirect_uri=settings.spotify_redirect_uri,
                scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
                open_browser=False
            )
            
            # Manually seed refresh token cache/state
            token_info = self._auth_manager.refresh_access_token(token_to_use)
            if token_info:
                self.sp = spotipy.Spotify(auth=token_info['access_token'])
                self._initialized = True
                logger.info("spotify.authenticated_successfully")
            else:
                logger.error("spotify.failed_to_refresh_token")
                self.sp = None
                self._initialized = False
        except Exception as e:
            logger.error("spotify.auth_error", error=str(e))
            self.sp = None
            self._initialized = False

    def get_auth_url(self) -> str:
        """Get the Spotify authorization URL."""
        if not settings.spotify_client_id or not settings.spotify_client_secret:
            return ""
        auth_manager = SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
            open_browser=False
        )
        return auth_manager.get_authorize_url()

    def exchange_code_for_token(self, code: str) -> str:
        """Exchange authorization code for access and refresh tokens, and return refresh token."""
        auth_manager = SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
            open_browser=False
        )
        token_info = auth_manager.get_access_token(code, as_dict=True)
        return token_info.get("refresh_token")

    async def initialize_with_token(self, refresh_token: str) -> bool:
        """Initialize the Spotify client dynamically with a new refresh token."""
        await self.initialize(db_refresh_token=refresh_token)
        return self._initialized

    def disconnect(self) -> None:
        """Disconnect Spotify client and clear initialization state."""
        self.sp = None
        self._auth_manager = None
        self._initialized = False
        logger.info("spotify.disconnected_successfully")

    @property
    def is_connected(self) -> bool:
        return self._initialized and self.sp is not None

    def _refresh_client_if_needed(self) -> None:
        """Ensure token is valid, refresh if needed."""
        if not self._initialized or not self._auth_manager or not self.sp:
            return
        
        try:
            # spotipy's auth manager can auto refresh if cached token exists
            cached_token = self._auth_manager.get_cached_token()
            if cached_token and self._auth_manager.is_token_expired(cached_token):
                token_info = self._auth_manager.refresh_access_token(settings.spotify_refresh_token)
                self.sp = spotipy.Spotify(auth=token_info['access_token'])
        except Exception as e:
            logger.error("spotify.token_refresh_error", error=str(e))

    async def get_playback_state(self) -> Optional[Dict[str, Any]]:
        """Fetch the current playback state from Spotify."""
        if not self.is_connected:
            return None

        # Run spotipy call in executor to not block async loop
        loop = asyncio.get_event_loop()
        try:
            self._refresh_client_if_needed()
            state = await loop.run_in_executor(None, self.sp.current_playback)
            if not state:
                return None
            
            # Normalize state representation
            item = state.get("item")
            track_info = None
            if item:
                images = item.get("album", {}).get("images", [])
                album_art = images[0].get("url") if images else None
                
                track_info = {
                    "title": item.get("name", "Unknown Track"),
                    "artist": ", ".join(a.get("name", "Unknown Artist") for a in item.get("artists", [])),
                    "album": item.get("album", {}).get("name", "Unknown Album"),
                    "album_art_url": album_art,
                    "duration_ms": item.get("duration_ms", 0),
                    "position_ms": state.get("progress_ms", 0),
                }

            return {
                "is_playing": state.get("is_playing", False),
                "track": track_info
            }
        except Exception as e:
            logger.debug("spotify.playback_state_error", error=str(e))
            return None

    def launch_local_spotify(self) -> None:
        """Launch the official Spotify client on Windows if closed."""
        import sys
        import subprocess
        if sys.platform == "win32":
            try:
                logger.info("spotify.auto_launching_client")
                subprocess.Popen("start spotify:", shell=True)
            except Exception as e:
                logger.error("spotify.failed_to_launch_client", error=str(e))

    def _get_device_id(self, auto_launch: bool = True) -> Optional[str]:
        """Get the ID of the preferred device, or fallback to any active device."""
        if not self.sp:
            return None
        import time
        try:
            devices = self.sp.devices().get("devices", [])
            logger.info("spotify.devices_list", devices=[{"name": d.get("name"), "id": d.get("id"), "is_active": d.get("is_active")} for d in devices])
            
            # 1. Look for settings preferred device
            pref_name = settings.spotify_preferred_device.lower() if settings.spotify_preferred_device else ""
            if pref_name:
                for d in devices:
                    if pref_name in d.get("name", "").lower():
                        return d.get("id")
            
            # 2. Fallback to any active device
            for d in devices:
                if d.get("is_active"):
                    return d.get("id")
            
            # 3. Fallback to the first available device
            if devices:
                return devices[0].get("id")

            # 4. Last resort: auto launch official client
            if auto_launch:
                self.launch_local_spotify()
                time.sleep(4)
                devices = self.sp.devices().get("devices", [])
                logger.info("spotify.devices_list_retry", devices=[{"name": d.get("name"), "id": d.get("id"), "is_active": d.get("is_active")} for d in devices])
                if devices:
                    return devices[0].get("id")
                
            return None
        except Exception as e:
            logger.error("spotify.failed_to_get_device", error=str(e))
            return None

    async def execute_command(self, action: str, query: Optional[str] = None, value: Optional[int] = None) -> bool:
        """Execute a playback command on Spotify."""
        if not self.is_connected:
            logger.warning("spotify.command_ignored", reason="not_connected")
            return False

        loop = asyncio.get_event_loop()
        self._refresh_client_if_needed()
        device_id = self._get_device_id()

        try:
            if action == "play":
                if query:
                    if str(query).startswith("spotify:"):
                        await loop.run_in_executor(None, lambda: self.sp.start_playback(uris=[query], device_id=device_id))
                    else:
                        # Search and play track
                        await loop.run_in_executor(None, self._search_and_play, query, device_id)
                else:
                    await loop.run_in_executor(None, lambda: self.sp.start_playback(device_id=device_id))
            elif action == "pause":
                await loop.run_in_executor(None, lambda: self.sp.pause_playback(device_id=device_id))
            elif action == "resume":
                await loop.run_in_executor(None, lambda: self.sp.start_playback(device_id=device_id))
            elif action == "next":
                await loop.run_in_executor(None, lambda: self.sp.next_track(device_id=device_id))
            elif action == "previous":
                await loop.run_in_executor(None, lambda: self.sp.previous_track(device_id=device_id))
            elif action == "seek":
                if value is not None:
                    await loop.run_in_executor(None, lambda: self.sp.seek_track(value, device_id=device_id))
            elif action == "volume":
                if value is not None:
                    # Normalize value to 0-100 range
                    vol = max(0, min(100, value))
                    await loop.run_in_executor(None, lambda: self.sp.volume(vol, device_id=device_id))
            elif action == "search_play":
                if query:
                    await loop.run_in_executor(None, self._search_and_play, query, device_id)
            else:
                logger.warning("spotify.invalid_action", action=action)
                return False
            
            logger.info("spotify.command_executed", action=action, query=query, value=value, device_id=device_id)
            return True
        except Exception as e:
            logger.error("spotify.command_failed", action=action, error=str(e))
            return False

    def _search_and_play(self, query: str, device_id: Optional[str] = None) -> None:
        """Helper to search for a track and start playing it on active/preferred device."""
        results = self.sp.search(q=query, limit=1, type="track")
        tracks = results.get("tracks", {}).get("items", [])
        if not tracks:
            logger.warning("spotify.search_no_results", query=query)
            return
        
        track_uri = tracks[0]["uri"]
        self.sp.start_playback(uris=[track_uri], device_id=device_id)
        logger.info("spotify.started_track_uri", uri=track_uri, query=query, device_id=device_id)

    async def search_tracks(self, query: str, limit: int = 5) -> list:
        """Search for tracks matching query."""
        if not self.is_connected:
            return []
        loop = asyncio.get_event_loop()
        self._refresh_client_if_needed()
        
        def sync_search():
            results = self.sp.search(q=query, limit=limit, type="track")
            tracks = results.get("tracks", {}).get("items", [])
            output = []
            for t in tracks:
                album_art = t.get("album", {}).get("images", [])
                art_url = album_art[0].get("url") if album_art else ""
                output.append({
                    "uri": t.get("uri"),
                    "title": t.get("name"),
                    "artist": ", ".join([a.get("name") for a in t.get("artists", [])]),
                    "album": t.get("album", {}).get("name"),
                    "album_art_url": art_url,
                    "duration_ms": t.get("duration_ms")
                })
            return output

        try:
            return await loop.run_in_executor(None, sync_search)
        except Exception as e:
            logger.error("spotify.search_failed", query=query, error=str(e))
            return []
