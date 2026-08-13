"""
JARVIS — Voice Pipeline

Orchestrates: Audio → VAD → STT → Intent → Execute → TTS
All processing happens on the server. ESP32 only streams raw PCM audio.
"""

import asyncio
import uuid
import base64
import io
from typing import Optional

from app.core.events import EventBus, JarvisEvent
from app.core.config import settings
from app.voice.vad import VoiceActivityDetector
from app.voice.stt.provider import STTProvider
from app.voice.stt.whisper_provider import WhisperSTTProvider
from app.assistant.engine import IntentEngine
from app.tts.manager import TTSManager

import structlog

logger = structlog.get_logger("jarvis.voice")


class VoiceSession:
    """Represents an active voice recording session."""

    def __init__(self, message_id: str):
        self.message_id = message_id
        self.audio_chunks: list[bytes] = []
        self.total_bytes = 0
        self.started = False
        self.finished = False


class VoicePipeline:
    """Full voice processing pipeline.
    
    Flow: INMP441 → ESP32 → WebSocket → VAD → STT → Intent → Execute → TTS → ESP32 → Speaker
    """

    def __init__(self, event_bus: EventBus, device_manager, music_manager=None):
        self.event_bus = event_bus
        self.device_manager = device_manager
        self.music_manager = music_manager
        self.stt: Optional[STTProvider] = None
        self.intent_engine: Optional[IntentEngine] = None
        self.tts: Optional[TTSManager] = None
        self.vad = VoiceActivityDetector(aggressiveness=settings.vad_aggressiveness)
        self._active_session: Optional[VoiceSession] = None
        self._lock = asyncio.Lock()
        self._status = "not_initialized"

    async def initialize(self) -> None:
        """Initialize all voice components."""
        try:
            # Initialize STT
            logger.info("voice.stt.loading", provider=settings.stt_provider, model=settings.stt_model)
            self.stt = WhisperSTTProvider(
                model_size=settings.stt_model,
                device=settings.stt_device,
                language=settings.stt_language,
            )
            await self.stt.initialize()
            logger.info("voice.stt.ready")

            # Initialize Intent Engine (Ollama)
            self.intent_engine = IntentEngine(
                device_manager=self.device_manager,
                event_bus=self.event_bus,
                music_manager=self.music_manager,
            )
            await self.intent_engine.initialize()

            # Initialize TTS
            self.tts = TTSManager(event_bus=self.event_bus)
            await self.tts.initialize()

            # Subscribe to voice events from WebSocket
            self.event_bus.subscribe("VOICE_START", self._on_voice_start)
            self.event_bus.subscribe("VOICE_AUDIO", self._on_voice_audio)
            self.event_bus.subscribe("VOICE_END", self._on_voice_end)
            self.event_bus.subscribe("VOICE_CANCEL", self._on_voice_cancel)

            self._status = "ready"
            logger.info("voice.pipeline.ready")

        except Exception as e:
            self._status = f"error: {e}"
            logger.error("voice.pipeline.init_failed", error=str(e))

    async def stop(self) -> None:
        """Stop the voice pipeline."""
        if self.tts:
            await self.tts.stop()
        self._status = "stopped"
        logger.info("voice.pipeline.stopped")

    @property
    def status(self) -> str:
        return self._status

    @property
    def stt_status(self) -> str:
        return "ready" if self.stt and self.stt.is_ready else "unavailable"

    @property
    def tts_status(self) -> str:
        return "ready" if self.tts and self.tts.is_ready else "unavailable"

    @property
    def ai_status(self) -> str:
        return "ready" if self.intent_engine and self.intent_engine.is_ready else "unavailable"

    # ---- Event Handlers ----

    async def _on_voice_start(self, event: JarvisEvent) -> None:
        """Handle voice recording start."""
        async with self._lock:
            msg_id = event.message_id or str(uuid.uuid4())
            self._active_session = VoiceSession(msg_id)
            self._active_session.started = True

            logger.info("voice.session.started", message_id=msg_id)

            await self.event_bus.publish(JarvisEvent(
                type="VOICE_LISTENING",
                source="voice",
                message_id=msg_id,
            ))

    async def _on_voice_audio(self, event: JarvisEvent) -> None:
        """Handle incoming audio chunk."""
        if not self._active_session or self._active_session.finished:
            return

        audio_b64 = event.data.get("audio", "")
        if not audio_b64:
            return

        try:
            audio_bytes = base64.b64decode(audio_b64)
            self._active_session.audio_chunks.append(audio_bytes)
            self._active_session.total_bytes += len(audio_bytes)

            # Safety limit: max recording size (~15s at 16kHz 16-bit = ~480KB)
            max_bytes = settings.max_recording_seconds * 16000 * 2
            if self._active_session.total_bytes > max_bytes:
                logger.warning("voice.session.max_size", message_id=self._active_session.message_id)
                await self._process_session()

        except Exception as e:
            logger.error("voice.audio_error", error=str(e))

    async def _on_voice_end(self, event: JarvisEvent) -> None:
        """Handle voice recording end — process the audio."""
        await self._process_session()

    async def _on_voice_cancel(self, event: JarvisEvent) -> None:
        """Handle voice recording cancellation."""
        async with self._lock:
            if self._active_session:
                logger.info("voice.session.cancelled", message_id=self._active_session.message_id)
                self._active_session = None

    async def _process_session(self) -> None:
        """Process the recorded audio through the full pipeline."""
        async with self._lock:
            session = self._active_session
            if not session or session.finished:
                return
            session.finished = True
            self._active_session = None

        msg_id = session.message_id

        if not session.audio_chunks:
            logger.warning("voice.session.empty", message_id=msg_id)
            return

        # Combine audio chunks
        audio_data = b"".join(session.audio_chunks)
        logger.info("voice.processing", message_id=msg_id, audio_bytes=len(audio_data))

        # Publish thinking state
        await self.event_bus.publish(JarvisEvent(
            type="VOICE_THINKING",
            source="voice",
            message_id=msg_id,
        ))

        # --- STT ---
        if not self.stt or not self.stt.is_ready:
            await self._publish_error(msg_id, "STT_UNAVAILABLE", "Speech recognition is not available")
            return

        try:
            transcription = await self.stt.transcribe(audio_data)
        except Exception as e:
            logger.error("voice.stt_error", error=str(e), message_id=msg_id)
            await self._publish_error(msg_id, "STT_ERROR", f"Transcription failed: {e}")
            return

        if not transcription or not transcription.strip():
            logger.info("voice.empty_transcription", message_id=msg_id)
            return

        logger.info("voice.transcribed", text=transcription, message_id=msg_id)

        await self.event_bus.publish(JarvisEvent(
            type="VOICE_TRANSCRIBED",
            source="voice",
            message_id=msg_id,
            data={"text": transcription},
        ))

        # --- Intent Processing ---
        if not self.intent_engine or not self.intent_engine.is_ready:
            await self._publish_error(msg_id, "AI_UNAVAILABLE", "AI assistant is not available")
            return

        try:
            result = await self.intent_engine.process(transcription, msg_id)
        except Exception as e:
            logger.error("voice.intent_error", error=str(e), message_id=msg_id)
            await self._publish_error(msg_id, "AI_ERROR", f"Intent processing failed: {e}")
            return

        # --- TTS Response ---
        response_text = result.get("response_text", "")
        if response_text and self.tts and self.tts.is_ready:
            try:
                await self.tts.speak(response_text, msg_id)
            except Exception as e:
                logger.error("voice.tts_error", error=str(e), message_id=msg_id)
                # TTS failure should not prevent command execution

        # Publish final response
        await self.event_bus.publish(JarvisEvent(
            type="ASSISTANT_RESPONSE",
            source="voice",
            message_id=msg_id,
            data={
                "text": response_text,
                "success": result.get("success", False),
                "intent": result.get("intent"),
            },
        ))

    async def _publish_error(self, message_id: str, code: str, message: str) -> None:
        """Publish an error event."""
        await self.event_bus.publish(JarvisEvent(
            type="ASSISTANT_ERROR",
            source="voice",
            message_id=message_id,
            data={"error": message, "code": code},
        ))
