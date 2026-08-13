"""
JARVIS — STT Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional


class STTProvider(ABC):
    """Abstract base class for Speech-to-Text providers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the STT engine (load model, etc.)."""
        ...

    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> Optional[str]:
        """Transcribe PCM audio to text.
        
        Args:
            audio_data: Raw PCM bytes (16-bit signed, mono, 16kHz)
            
        Returns:
            Transcribed text or None if nothing detected.
        """
        ...

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """Whether the provider is ready to transcribe."""
        ...
