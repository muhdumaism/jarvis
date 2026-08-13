"""
JARVIS — Voice Activity Detection

Detects speech boundaries in PCM audio.
Uses webrtcvad for robust speech detection.
"""

import struct
from typing import Optional

import structlog

logger = structlog.get_logger("jarvis.vad")

try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    logger.warning("vad.webrtcvad_not_available", fallback="energy_based")


class VoiceActivityDetector:
    """Detects voice activity in PCM audio.
    
    Uses webrtcvad if available, falls back to energy-based detection.
    
    Input: 16-bit mono PCM at 16kHz
    """

    def __init__(self, aggressiveness: int = 2, energy_threshold: float = 500.0):
        self.aggressiveness = aggressiveness
        self.energy_threshold = energy_threshold
        self._vad = None

        if VAD_AVAILABLE:
            self._vad = webrtcvad.Vad(aggressiveness)
            logger.info("vad.initialized", engine="webrtcvad", aggressiveness=aggressiveness)
        else:
            logger.info("vad.initialized", engine="energy_based", threshold=energy_threshold)

    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        """Check if an audio chunk contains speech.
        
        Args:
            audio_chunk: Raw PCM bytes (16-bit signed, mono)
            sample_rate: Sample rate in Hz (must be 8000, 16000, or 32000 for webrtcvad)
        
        Returns:
            True if speech is detected.
        """
        if self._vad:
            return self._is_speech_webrtcvad(audio_chunk, sample_rate)
        return self._is_speech_energy(audio_chunk)

    def _is_speech_webrtcvad(self, audio_chunk: bytes, sample_rate: int) -> bool:
        """Use webrtcvad for speech detection.
        
        webrtcvad requires frames of exactly 10, 20, or 30ms.
        """
        try:
            # webrtcvad needs frames of specific sizes
            frame_duration_ms = 30  # 30ms frames
            frame_size = int(sample_rate * frame_duration_ms / 1000) * 2  # 2 bytes per sample

            if len(audio_chunk) < frame_size:
                return self._is_speech_energy(audio_chunk)

            # Check frames within the chunk
            speech_frames = 0
            total_frames = 0
            for i in range(0, len(audio_chunk) - frame_size + 1, frame_size):
                frame = audio_chunk[i:i + frame_size]
                if len(frame) == frame_size:
                    total_frames += 1
                    if self._vad.is_speech(frame, sample_rate):
                        speech_frames += 1

            # Consider speech if > 30% of frames contain speech
            if total_frames == 0:
                return False
            return (speech_frames / total_frames) > 0.3

        except Exception as e:
            logger.debug("vad.webrtcvad_error", error=str(e))
            return self._is_speech_energy(audio_chunk)

    def _is_speech_energy(self, audio_chunk: bytes) -> bool:
        """Fallback: simple energy-based speech detection."""
        if len(audio_chunk) < 2:
            return False

        # Calculate RMS energy
        num_samples = len(audio_chunk) // 2
        if num_samples == 0:
            return False

        total = 0
        for i in range(num_samples):
            sample = struct.unpack_from("<h", audio_chunk, i * 2)[0]
            total += sample * sample

        rms = (total / num_samples) ** 0.5
        return rms > self.energy_threshold
