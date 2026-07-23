"""
Structured logging configuration for Adaptive SOC CoPilot.

Sets up Python's standard logging with a JSON-like format suitable for
log aggregators (e.g., Datadog, Logtail, AWS CloudWatch).

Usage:
    from app.core.logging_config import setup_logging, get_logger

    # Call once at application startup (in main.py)
    setup_logging()

    # In any module
    logger = get_logger(__name__)
    logger.info("Event ingested", extra={"event_id": str(event.id)})
"""

import logging
import sys
from typing import Optional

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """
    Custom log formatter that outputs a structured, human-readable format
    in development and a compact format in production.

    Development format:
        2026-07-23 21:00:00 | INFO     | app.api.v1.endpoints.auth | User logged in

    Production format:
        level=INFO logger=app.api.v1.endpoints.auth msg="User logged in"
    """

    DEV_FORMAT = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    PROD_FORMAT = (
        'level=%(levelname)s logger=%(name)s msg="%(message)s"'
    )

    def format(self, record: logging.LogRecord) -> str:
        if settings.is_development:
            self._style._fmt = self.DEV_FORMAT  # type: ignore[attr-defined]
        else:
            self._style._fmt = self.PROD_FORMAT  # type: ignore[attr-defined]
        return super().format(record)


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure the root logger and silence noisy third-party loggers.

    Should be called exactly once during application startup.

    Args:
        level: Override the log level (e.g., 'DEBUG'). Defaults to DEBUG in
               development, INFO in production.
    """
    log_level_str = level or ("DEBUG" if settings.is_development else "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Root logger configuration
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    logging.basicConfig(
        level=log_level,
        handlers=[handler],
        force=True,  # Override any pre-existing configuration
    )

    # Silence noisy third-party libraries in production
    for noisy_logger in ("uvicorn.access", "sqlalchemy.engine", "passlib"):
        logging.getLogger(noisy_logger).setLevel(
            logging.DEBUG if settings.is_development else logging.WARNING
        )

    logger = get_logger(__name__)
    logger.info(
        "Logging initialized | level=%s | environment=%s",
        log_level_str,
        settings.ENVIRONMENT,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger instance.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A configured Logger instance.
    """
    return logging.getLogger(name)
