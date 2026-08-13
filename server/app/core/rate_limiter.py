"""
JARVIS server — Rate Limiter

Simple in-memory rate limiter for API endpoints and WebSocket messages.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import HTTPException, Request, status

import structlog

logger = structlog.get_logger("jarvis.rate_limiter")


class RateLimiter:
    """Token bucket rate limiter.
    
    Tracks request counts per client IP with a sliding window.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self._buckets: Dict[str, Tuple[float, int]] = defaultdict(
            lambda: (time.time(), burst_size)
        )

    def _get_tokens(self, key: str) -> Tuple[float, int]:
        """Get the current token count for a key, refilling as needed."""
        last_time, tokens = self._buckets[key]
        now = time.time()
        elapsed = now - last_time

        # Refill tokens based on elapsed time
        refill = elapsed * (self.requests_per_minute / 60.0)
        tokens = min(self.burst_size, tokens + refill)

        self._buckets[key] = (now, tokens)
        return now, tokens

    def check(self, key: str) -> bool:
        """Check if a request is allowed. Returns True if allowed."""
        _, tokens = self._get_tokens(key)
        if tokens >= 1:
            self._buckets[key] = (time.time(), tokens - 1)
            return True
        return False

    def cleanup(self, max_age_seconds: int = 300) -> None:
        """Remove stale entries older than max_age_seconds."""
        now = time.time()
        stale_keys = [
            k for k, (t, _) in self._buckets.items()
            if now - t > max_age_seconds
        ]
        for key in stale_keys:
            del self._buckets[key]


# Global rate limiters for different purposes
api_limiter = RateLimiter(requests_per_minute=120, burst_size=20)
ws_limiter = RateLimiter(requests_per_minute=300, burst_size=50)
voice_limiter = RateLimiter(requests_per_minute=10, burst_size=3)
device_limiter = RateLimiter(requests_per_minute=30, burst_size=5)


async def rate_limit_middleware(request: Request) -> None:
    """Check rate limit for incoming API requests."""
    client_ip = request.client.host if request.client else "unknown"
    if not api_limiter.check(client_ip):
        logger.warning("rate_limit.exceeded", client=client_ip, path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )
