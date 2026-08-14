"""
JARVIS — Piper TTS Provider

Local text-to-speech using Piper. Fast, offline, natural-sounding.
Output: raw PCM 16-bit mono at 22050Hz (default).
"""

import asyncio
import io
import wave
import subprocess
import os
from typing import Optional

from app.tts.provider import TTSProvider
from app.core.config import settings

import structlog

logger = structlog.get_logger("jarvis.tts.piper")


class PiperTTSProvider(TTSProvider):
    """Piper TTS provider. Runs entirely locally on CPU."""

    def __init__(
        self,
        model_path: str = None,
        config_path: str = None,
        output_sample_rate: int = None,
    ):
        self.model_path = model_path or settings.piper_model_path
        self.config_path = config_path or settings.piper_config_path
        self._sample_rate = output_sample_rate or settings.tts_sample_rate
        self.piper_bin_path = settings.piper_bin_path
        self._ready = False
        self._piper_available = False

    async def initialize(self) -> None:
        """Check if Piper is available and model exists."""
        # Try importing piper
        try:
            # Check if piper CLI is available
            result = await asyncio.create_subprocess_exec(
                self.piper_bin_path, "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.communicate()
            self._piper_available = True
            logger.info("tts.piper.cli_available", bin=self.piper_bin_path)
        except FileNotFoundError:
            logger.warning(
                "tts.piper.cli_not_found",
                bin=self.piper_bin_path,
                help="Configure PIPER_BIN_PATH in .env to point to standalone piper.exe",
            )

        # Check model file
        if os.path.exists(self.model_path):
            self._ready = True
            logger.info("tts.piper.ready", model=self.model_path)
        else:
            logger.warning(
                "tts.piper.model_not_found",
                path=self.model_path,
                help=(
                    "Download a Piper model from https://github.com/rhasspy/piper/releases "
                    "and place it at the configured path. "
                    "Example: wget https://huggingface.co/rhasspy/piper-voices/resolve/main/"
                    "en/en_US/lessac/medium/en_US-lessac-medium.onnx"
                ),
            )
            # Still mark as ready if CLI is available — model can be downloaded later
            if self._piper_available:
                self._ready = False

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to raw PCM audio using Piper CLI."""
        if not self._ready:
            raise RuntimeError("Piper TTS not ready — model not found")

        try:
            # Use piper CLI to synthesize
            process = await asyncio.create_subprocess_exec(
                self.piper_bin_path,
                "--model", self.model_path,
                "--output-raw",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=text.encode("utf-8")),
                timeout=15.0,
            )

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace")
                logger.error("tts.piper.synthesis_error", error=error_msg)
                raise RuntimeError(f"Piper TTS failed: {error_msg}")

            logger.info("tts.piper.synthesized", text=text[:50], bytes=len(stdout))
            return stdout

        except asyncio.TimeoutError:
            logger.error("tts.piper.timeout", text=text[:50])
            raise RuntimeError("TTS synthesis timed out")
        except FileNotFoundError:
            logger.error("tts.piper.not_found")
            raise RuntimeError("Piper CLI not found")

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def is_ready(self) -> bool:
        return self._ready
