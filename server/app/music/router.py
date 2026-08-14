"""
JARVIS — Music API Router

REST endpoints for music playback state, commands, and resized album art fetching.
"""

import io
import urllib.request
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user
from app.music.schemas import MusicStateResponse, MusicControlCommand

router = APIRouter(prefix="/music", tags=["music"])

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


def _get_music_manager(request: Request):
    return request.app.state.music_manager


@router.get("/state", response_model=MusicStateResponse)
async def get_state(
    music_manager=Depends(_get_music_manager),
    _user=Depends(get_current_user)
):
    """Get current Spotify playback status."""
    return await music_manager.get_state()


@router.post("/control")
async def control_music(
    command: MusicControlCommand,
    music_manager=Depends(_get_music_manager),
    _user=Depends(get_current_user)
):
    """Execute music playback command."""
    success = await music_manager.bridge.execute_command(
        action=command.action,
        query=command.query,
        value=command.value
    )
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to execute command. Verify Spotify is active."
        )
    return {"success": True}


@router.get("/album-art")
async def get_album_art(
    music_manager=Depends(_get_music_manager)
):
    """Get currently playing album art resized for ESP32 (64x64)."""
    state = await music_manager.get_state()
    track = state.get("track")
    
    if not track or not track.get("album_art_url"):
        raise HTTPException(status_code=404, detail="No track playing or album art unavailable")

    art_url = track["album_art_url"]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(art_url, timeout=5.0)
            if resp.status_code != 200:
                raise HTTPException(status_code=404, detail="Failed to fetch album art from Spotify")
            
            image_data = resp.content

            if PILLOW_AVAILABLE:
                # Resize to 64x64 for ESP32 memory safety (no PSRAM)
                img = Image.open(io.BytesIO(image_data))
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                
                # Output as raw RGB565 bytes (TFT native format) or simple JPEG
                # Let's support JPEG for easiest ESP32 decoding without custom byte parsing, 
                # but heavily compressed.
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=60)
                output.seek(0)
                return StreamingResponse(output, media_type="image/jpeg")
            
            # Fallback if PIL not installed
            return Response(content=image_data, media_type="image/jpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resizing album art: {e}")

@router.get("/album-art-rgb565")
async def get_album_art_rgb565(
    music_manager=Depends(_get_music_manager)
):
    """Get currently playing album art as raw RGB565 big-endian bytes (64x64)."""
    state = await music_manager.get_state()
    track = state.get("track")
    
    if not track or not track.get("album_art_url"):
        raise HTTPException(status_code=404, detail="No track playing or album art unavailable")

    art_url = track["album_art_url"]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(art_url, timeout=5.0)
            if resp.status_code != 200:
                raise HTTPException(status_code=404, detail="Failed to fetch album art")
            
            if PILLOW_AVAILABLE:
                img = Image.open(io.BytesIO(resp.content))
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                img = img.convert("RGB")
                
                rgb565_data = bytearray()
                for y in range(64):
                    for x in range(64):
                        r, g, b = img.getpixel((x, y))
                        r5 = (r >> 3) & 0x1F
                        g6 = (g >> 2) & 0x3F
                        b5 = (b >> 3) & 0x1F
                        val = (r5 << 11) | (g6 << 5) | b5
                        # Big endian bytes
                        rgb565_data.append((val >> 8) & 0xFF)
                        rgb565_data.append(val & 0xFF)
                return Response(content=bytes(rgb565_data), media_type="application/octet-stream")
            else:
                raise HTTPException(status_code=500, detail="PIL not available for RGB565 conversion")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_music(
    q: str,
    music_manager=Depends(_get_music_manager),
    _user=Depends(get_current_user)
):
    """Search for tracks on Spotify."""
    if not music_manager.is_connected:
        raise HTTPException(
            status_code=400,
            detail="Spotify is not connected. Verify credentials and active device."
        )
    return await music_manager.bridge.search_tracks(q)

from fastapi.responses import HTMLResponse
from pydantic import BaseModel

class BluetoothSpeakerUpdate(BaseModel):
    name: str

@router.get("/auth-url")
async def get_spotify_auth_url(
    music_manager=Depends(_get_music_manager),
    _user=Depends(get_current_user)
):
    """Retrieve Spotify authorization URL for OAuth flow."""
    url = music_manager.bridge.get_auth_url()
    if not url:
        raise HTTPException(
            status_code=400,
            detail="Spotify Client ID or Client Secret not configured on server."
        )
    return {"url": url}

@router.get("/callback", response_class=HTMLResponse)
async def spotify_callback(
    code: str,
    music_manager=Depends(_get_music_manager)
):
    """Callback for Spotify authorization code flow."""
    try:
        # Exchange authorization code for refresh token
        refresh_token = music_manager.bridge.exchange_code_for_token(code)
        if not refresh_token:
            raise Exception("No refresh token returned from Spotify")

        # Save refresh token in database settings
        db = music_manager.db
        if db:
            async with db.get_session() as session:
                from app.db.models import Setting
                from sqlalchemy import select
                result = await session.execute(select(Setting).where(Setting.key == "spotify_refresh_token"))
                setting = result.scalar_one_or_none()
                if not setting:
                    setting = Setting(key="spotify_refresh_token", value=refresh_token, type="string")
                    session.add(setting)
                else:
                    setting.value = refresh_token
                await session.commit()

        # Initialize Spotify client immediately
        initialized = await music_manager.bridge.initialize_with_token(refresh_token)
        if not initialized:
            raise Exception("Failed to initialize Spotify client after exchange")

        # Return callback landing page
        return """
        <html>
        <head>
            <title>Spotify Authorized</title>
            <style>
                body {
                    font-family: 'Inter', sans-serif;
                    background-color: #121212;
                    color: #ffffff;
                    text-align: center;
                    padding-top: 100px;
                }
                .container {
                    border: 4px solid #000000;
                    background-color: #1e1e1e;
                    display: inline-block;
                    padding: 40px;
                    box-shadow: 8px 8px 0px 0px #10b981;
                }
                h1 { color: #10b981; margin-top: 0; }
                p { font-size: 16px; font-weight: bold; }
                button {
                    background-color: #ffe600;
                    color: #000000;
                    border: 2px solid #000000;
                    padding: 10px 20px;
                    font-weight: bold;
                    cursor: pointer;
                    box-shadow: 3px 3px 0px 0px #000000;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Spotify Connected!</h1>
                <p>JARVIS OS has authorized your Spotify account successfully.</p>
                <p>This window will close automatically.</p>
                <button onclick="window.close()">Close Window</button>
            </div>
            <script>
                // Notify parent window (dashboard) if open
                if (window.opener) {
                    window.opener.postMessage("spotify_connected", "*");
                }
                setTimeout(function() {
                    window.close();
                }, 3000);
            </script>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <html>
        <head><title>Spotify Authorization Failed</title></head>
        <body style="background-color: #121212; color: #ff5555; font-family: sans-serif; text-align: center; padding-top: 100px;">
            <h2>Authorization Failed</h2>
            <p>Error: {str(e)}</p>
        </body>
        </html>
        """

@router.post("/disconnect")
async def disconnect_spotify(
    music_manager=Depends(_get_music_manager),
    _user=Depends(get_current_user)
):
    """Disconnect Spotify integration and delete credentials."""
    # Delete refresh token from DB
    db = music_manager.db
    if db:
        async with db.get_session() as session:
            from app.db.models import Setting
            from sqlalchemy import select
            result = await session.execute(select(Setting).where(Setting.key == "spotify_refresh_token"))
            setting = result.scalar_one_or_none()
            if setting:
                await session.delete(setting)
                await session.commit()
                
    music_manager.bridge.disconnect()
    return {"success": True}

@router.get("/audio-devices")
async def get_audio_output_devices(
    _user=Depends(get_current_user)
):
    """Get list of active audio output devices on the server host."""
    from app.system.audio import get_windows_audio_devices
    return get_windows_audio_devices()

@router.post("/bluetooth-speaker")
async def update_bluetooth_speaker(
    payload: BluetoothSpeakerUpdate,
    music_manager=Depends(_get_music_manager),
    _user=Depends(get_current_user)
):
    """Update configured Bluetooth speaker target name."""
    db = music_manager.db
    if db:
        async with db.get_session() as session:
            from app.db.models import Setting
            from sqlalchemy import select
            result = await session.execute(select(Setting).where(Setting.key == "bluetooth_speaker_name"))
            setting = result.scalar_one_or_none()
            if not setting:
                setting = Setting(key="bluetooth_speaker_name", value=payload.name, type="string")
                session.add(setting)
            else:
                setting.value = payload.name
            await session.commit()
            
    return {"success": True, "name": payload.name}
