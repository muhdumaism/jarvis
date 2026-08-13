"""
JARVIS — Ollama AI Provider

Local LLM inference via Ollama for intent extraction.
No cloud APIs. Everything runs on the user's machine.
"""

import asyncio
import json
from typing import Optional, Dict, Any

import httpx

from app.core.config import settings

import structlog

logger = structlog.get_logger("jarvis.ai.ollama")


class OllamaProvider:
    """Ollama-based local LLM provider for intent extraction."""

    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._ready = False

    async def initialize(self) -> None:
        """Check Ollama is running and model is available."""
        self._client = httpx.AsyncClient(timeout=self.timeout)

        try:
            # Check Ollama is running
            resp = await self._client.get(f"{self.base_url}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in models]

                if any(self.model in name for name in model_names):
                    self._ready = True
                    logger.info("ollama.ready", model=self.model)
                else:
                    logger.warning(
                        "ollama.model_not_found",
                        model=self.model,
                        available=model_names,
                        help=f"Run: ollama pull {self.model}",
                    )
                    # Try to pull the model
                    self._ready = True  # Allow trying anyway
            else:
                logger.error("ollama.not_responding", status=resp.status_code)

        except httpx.ConnectError:
            logger.error(
                "ollama.not_running",
                url=self.base_url,
                help="Start Ollama with: ollama serve",
            )
        except Exception as e:
            logger.error("ollama.init_error", error=str(e))

    async def generate(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Generate a response from Ollama."""
        if not self._client:
            return None

        try:
            resp = await self._client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent intents
                        "num_predict": 256,  # Short responses
                    },
                },
                timeout=self.timeout,
            )

            if resp.status_code == 200:
                result = resp.json()
                return result.get("response", "").strip()
            else:
                logger.error("ollama.generate_error", status=resp.status_code)
                return None

        except httpx.ConnectError:
            logger.error("ollama.connection_lost")
            self._ready = False
            return None
        except httpx.TimeoutException:
            logger.error("ollama.timeout", model=self.model)
            return None
        except Exception as e:
            logger.error("ollama.error", error=str(e))
            return None

    @property
    def is_ready(self) -> bool:
        return self._ready

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
