"""Structured logging configuration."""

import logging
import sys
from typing import Any

import structlog
from structlog.typing import FilteringBoundLogger

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add timestamp
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.dev.ConsoleRenderer(colors=settings.is_development)
            if settings.is_development
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )
    
    # Suppress noisy loggers in production
    if not settings.is_development:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> FilteringBoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def redact_sensitive_data(data: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive information from log data."""
    sensitive_fields = {
        "password",
        "token",
        "authorization",
        "jwt",
        "secret",
        "api_key",
        "access_token",
        "refresh_token",
    }
    
    redacted_data = {}
    for key, value in data.items():
        if key.lower() in sensitive_fields:
            redacted_data[key] = "***REDACTED***"
        elif isinstance(value, dict):
            redacted_data[key] = redact_sensitive_data(value)
        elif isinstance(value, list):
            redacted_data[key] = [
                redact_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            redacted_data[key] = value
    
    return redacted_data
