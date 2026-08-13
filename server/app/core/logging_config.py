"""
JARVIS server — Structured Logging Configuration

Uses structlog for JSON-formatted structured logging.
Never logs secrets.
"""

import logging
import sys

import structlog
from app.core.config import settings


def safe_add_logger_name(logger, name, event_dict):
    if logger is not None and hasattr(logger, "name") and logger.name:
        event_dict["logger"] = logger.name
    elif name:
        event_dict["logger"] = name
    else:
        event_dict["logger"] = "root"
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the JARVIS server."""

    # Set up structlog processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        safe_add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.debug:
        # Development: colored console output
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # Production: JSON output
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *shared_processors,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# List of sensitive keys that must never be logged
SENSITIVE_KEYS = {
    "password", "token", "secret", "api_key", "refresh_token",
    "client_secret", "spotify_client_id", "spotify_client_secret",
    "spotify_refresh_token", "secret_key",
}


def sanitize_log_data(data: dict) -> dict:
    """Remove sensitive values from log data."""
    sanitized = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        else:
            sanitized[key] = value
    return sanitized
