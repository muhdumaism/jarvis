"""
JARVIS server — Configuration

All settings loaded from environment variables / .env file.
Single source of truth for server configuration.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

_config_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.abspath(os.path.join(_config_dir, "..", "..", ".env"))


class Settings(BaseSettings):
    """JARVIS server configuration. All values come from .env or environment variables."""

    # --- Server ---
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    # --- Security ---
    secret_key: str = "CHANGE_ME_GENERATE_A_REAL_KEY"
    api_key: str = "CHANGE_ME_GENERATE_A_REAL_KEY"
    default_admin_username: str = "admin"
    default_admin_password: str = "CHANGE_ME"
    access_token_expire_minutes: int = 1440  # 24 hours

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./jarvis.db"

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # --- STT ---
    stt_provider: str = "faster_whisper"
    stt_model: str = "tiny"
    stt_language: str = "en"
    stt_device: str = "cpu"

    # --- AI / Intent ---
    ai_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"
    default_weather_location: str = "Nilambur"

    # --- TTS ---
    tts_provider: str = "piper"
    piper_model_path: str = "./models/piper/en_US-lessac-medium.onnx"
    piper_config_path: str = "./models/piper/en_US-lessac-medium.onnx.json"
    tts_sample_rate: int = 22050
    play_tts_on_pc: bool = False
    piper_bin_path: str = "piper"

    # --- Spotify ---
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_refresh_token: str = ""
    spotify_preferred_device: str = "Nothing Phone 3a Pro"
    spotify_redirect_uri: str = "http://127.0.0.1:8000/api/music/callback"
    spotify_poll_interval: int = 5

    # --- Bluetooth Speaker ---
    bluetooth_speaker_name: str = "default"

    # --- ESP32 ---
    esp32_api_key: str = "CHANGE_ME_GENERATE_A_REAL_KEY"
    main_esp32_id: str = "main_esp32_01"

    # --- Voice ---
    vad_aggressiveness: int = 2  # 0-3, higher = more aggressive filtering
    silence_timeout_ms: int = 1500
    max_recording_seconds: int = 15
    audio_privacy_mode: bool = True  # Don't store audio by default

    # --- Automation ---
    automation_cooldown_seconds: int = 30
    max_automation_chain_depth: int = 3

    # --- Firmware ---
    firmware_dir: str = "./firmware-build"

    model_config = {
        "env_file": _env_path,
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Global settings instance — initialized once at startup
settings = Settings()
