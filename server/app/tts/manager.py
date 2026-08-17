"""
JARVIS — TTS Manager

Manages the TTS queue, handles cancellation, processes speech synthesis requests,
and chunks raw PCM audio to send to the Main ESP32 via the Event Bus.
"""

import asyncio
import base64
import uuid
from typing import Optional

from app.core.config import settings
from app.core.events import EventBus, JarvisEvent
from app.tts.piper_provider import PiperTTSProvider

try:
    import winsound
except ImportError:
    winsound = None

import structlog

logger = structlog.get_logger("jarvis.tts.manager")


class TTSManager:
    """Manages Text-To-Speech requests, queue, and chunking for the ESP32."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.provider = PiperTTSProvider()
        self._queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()  # (text, message_id)
        self._running = False
        self._process_task: Optional[asyncio.Task] = None
        self._current_message_id: Optional[str] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the TTS provider and start the worker loop."""
        await self.provider.initialize()
        self._running = True
        self._process_task = asyncio.create_task(self._process_queue())
        # Subscribe to TTS speak requests
        self.event_bus.subscribe("TTS_SPEAK", self._on_tts_speak)
        logger.info("tts.manager.initialized")

    async def stop(self) -> None:
        """Stop the worker loop."""
        self._running = False
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        logger.info("tts.manager.stopped")

    @property
    def is_ready(self) -> bool:
        return self.provider.is_ready

    @property
    def is_speaking(self) -> bool:
        return self._current_message_id is not None or not self._queue.empty()

    async def speak(self, text: str, message_id: Optional[str] = None) -> str:
        """Add a text-to-speech request to the queue. Returns the message_id."""
        msg_id = message_id or str(uuid.uuid4())
        await self._queue.put((text, msg_id))
        logger.info("tts.queued", text=text[:50], message_id=msg_id)
        return msg_id

    async def cancel_current(self) -> None:
        """Cancel current speaking playback."""
        async with self._lock:
            if self._current_message_id:
                logger.info("tts.cancelled", message_id=self._current_message_id)
                # Send TTS_END / Cancel event to main ESP32 to stop current audio play
                await self.event_bus.publish(JarvisEvent(
                    type="TTS_END",
                    source="tts_manager",
                    message_id=self._current_message_id,
                ))
                self._current_message_id = None

    async def _on_tts_speak(self, event: JarvisEvent) -> None:
        """Process speak requests published on the Event Bus."""
        text = event.data.get("text")
        if text:
            await self.speak(text, event.message_id)

    async def _process_queue(self) -> None:
        """Background loop to process TTS requests sequentially."""
        while self._running:
            try:
                text, msg_id = await self._queue.get()
            except asyncio.CancelledError:
                break

            try:
                async with self._lock:
                    self._current_message_id = msg_id

                logger.info("tts.speaking", text=text, message_id=msg_id)
                pcm_data = await self.provider.synthesize(text)

                if not pcm_data:
                    logger.warning("tts.no_audio_generated", message_id=msg_id)
                    continue

                if settings.play_tts_on_pc:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self._play_audio_locally, pcm_data)

                # Publish TTS_START event
                # Sample rate defaults to Piper (usually 22050), channels=1, 16bit signed
                total_len = len(pcm_data)
                chunk_size = 4096  # Chunk size defined in PROTOCOL.md
                total_chunks = (total_len + chunk_size - 1) // chunk_size

                await self.event_bus.publish(JarvisEvent(
                    type="TTS_START",
                    source="tts_manager",
                    message_id=msg_id,
                    data={
                        "sample_rate": self.provider.sample_rate,
                        "channels": 1,
                        "bit_depth": 16,
                        "total_chunks": total_chunks
                    }
                ))

                # Stream audio chunks to ESP32 (only if not playing locally on PC)
                if not settings.play_tts_on_pc:
                    for i in range(total_chunks):
                        # Check if cancelled mid-stream
                        if self._current_message_id != msg_id:
                            logger.info("tts.interrupted", message_id=msg_id)
                            break

                        start_idx = i * chunk_size
                        end_idx = min(start_idx + chunk_size, total_len)
                        chunk_bytes = pcm_data[start_idx:end_idx]

                        # Base64 encode for WebSocket JSON transfer
                        b64_chunk = base64.b64encode(chunk_bytes).decode("utf-8")

                        await self.event_bus.publish(JarvisEvent(
                            type="TTS_AUDIO",
                            source="tts_manager",
                            message_id=msg_id,
                            data={
                                "chunk": i,
                                "audio": b64_chunk
                            }
                        ))
                        # Sleep slightly to avoid flooding the websocket and buffer on ESP32
                        # 4096 bytes of 16-bit 22050Hz mono audio is:
                        # 4096 / 2 bytes_per_sample = 2048 samples
                        # 2048 / 22050 samples_per_sec = ~0.092 seconds (92ms) of audio
                        # We can sleep slightly less than that to keep buffer filled, e.g., 60-70ms
                        await asyncio.sleep(0.06)

                # Send TTS_END if successfully completed without being cancelled
                if self._current_message_id == msg_id:
                    await self.event_bus.publish(JarvisEvent(
                        type="TTS_END",
                        source="tts_manager",
                        message_id=msg_id
                    ))
                    async with self._lock:
                        self._current_message_id = None

            except Exception as e:
                logger.error("tts.processing_error", error=str(e), message_id=msg_id)
            finally:
                self._queue.task_done()

    def _play_audio_locally(self, pcm_data: bytes) -> None:
        """Play raw PCM audio on the local Windows PC using winsound."""
        if not winsound:
            logger.warning("tts.local_playback.failed", reason="winsound module not available (non-Windows platform)")
            return
            
        import wave
        import io
        import tempfile
        import os
        
        try:
            # Create in-memory WAV file from raw PCM bytes
            wav_buf = io.BytesIO()
            with wave.open(wav_buf, "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.provider.sample_rate)
                wav_file.writeframes(pcm_data)
            
            # Write to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(wav_buf.getvalue())
                temp_path = f.name
            
            # Play synchronously inside the executor thread
            winsound.PlaySound(temp_path, winsound.SND_FILENAME)
            
            # Clean up temp file
            os.remove(temp_path)
            logger.info("tts.local_playback.success")
            
        except Exception as e:
            logger.error("tts.local_playback.error", error=str(e))
