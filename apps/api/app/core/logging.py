"""Structured JSON logging — observability baseline (system_architecture.md).

Emits one JSON object per log line so logs are machine-parseable by aggregators.
A ``request_id`` is attached per request via contextvars (see middleware).
"""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from typing import Any

# Correlation id for the active request; set by RequestContextMiddleware.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON with request correlation."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = request_id_ctx.get()
        if request_id is not None:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Allow structured extras passed via logger.info(..., extra={"extra": {...}}).
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Install the JSON formatter on the root logger (idempotent)."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
