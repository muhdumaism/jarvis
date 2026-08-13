"""
JARVIS — faster-whisper STT Provider

Local CPU-only speech-to-text using faster-whisper.
Default model: tiny (fast, ~400MB RAM)
Alternative: base (more accurate, ~500MB RAM)
"""

import asyncio
import io
import tempfile
import os
from typing import Optional

import numpy as np

from app.voice.stt.provider import STTProvider

import structlog

logger = structlog.get_logger("jarvis.stt.whisper")


class WhisperSTTProvider(STTProvider):
    """faster-whisper based STT. Runs entirely on CPU."""

    def __init__(
        self,
        model_size: str = "tiny",
        device: str = "cpu",
        language: str = "en",
        compute_type: str = "int8",
    ):
        self.model_size = model_size
        self.device = device
        self.language = language
        self.compute_type = compute_type
        self._model = None
        self._ready = False

    async def initialize(self) -> None:
        """Load the Whisper model. This may take a few seconds on first run."""
        try:
            # Import here to fail gracefully if not installed
            from faster_whisper import WhisperModel

            logger.info(
                "stt.whisper.loading",
                model=self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )

            # Load model in a thread to not block the event loop
            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(
                None,
                lambda: WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                ),
            )

            self._ready = True
            logger.info("stt.whisper.ready", model=self.model_size)

        except ImportError:
            logger.error(
                "stt.whisper.not_installed",
                help="Install with: pip install faster-whisper",
            )
            self._ready = False
        except Exception as e:
            logger.error("stt.whisper.load_failed", error=str(e))
            self._ready = False

    async def transcribe(self, audio_data: bytes) -> Optional[str]:
        """Transcribe raw PCM audio (16-bit, mono, 16kHz) to text."""
        if not self._ready or not self._model:
            raise RuntimeError("Whisper model not loaded")

        # Convert raw PCM bytes to float32 numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

        if len(audio_array) == 0:
            return None

        # Whisper expects float32 array at 16kHz
        loop = asyncio.get_event_loop()

        try:
            segments, info = await loop.run_in_executor(
                None,
                lambda: self._model.transcribe(
                    audio_array,
                    language=self.language,
                    beam_size=1,  # Faster for CPU
                    best_of=1,
                    temperature=0.0,
                    vad_filter=True,  # Built-in VAD filtering
                    vad_parameters=dict(
                        min_silence_duration_ms=500,
                        speech_pad_ms=200,
                    ),
                ),
            )

            # Collect all segments
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())

            transcription = " ".join(text_parts).strip()

            if transcription:
                logger.info(
                    "stt.transcribed",
                    text=transcription,
                    language=info.language,
                    probability=round(info.language_probability, 2),
                )

            return transcription if transcription else None

        except Exception as e:
            logger.error("stt.transcribe_error", error=str(e))
            raise

    @property
    def is_ready(self) -> bool:
        return self._ready
