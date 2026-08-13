"""
JARVIS — TTS Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional


class TTSProvider(ABC):
    """Abstract base class for Text-to-Speech providers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the TTS engine."""
        ...

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to raw PCM audio.
        
        Args:
            text: Text to speak.
            
        Returns:
            Raw PCM bytes (16-bit signed, mono, at provider's sample rate).
        """
        ...

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """Output sample rate in Hz."""
        ...

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """Whether the provider is ready."""
        ...
