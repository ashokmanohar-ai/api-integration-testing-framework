"""Structured logging and recursive secret/PII redaction."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = frozenset(
    {"authorization", "password", "token", "access_token", "client_secret", "email"}
)


def sanitise(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): "***REDACTED***" if str(key).lower() in SENSITIVE_KEYS else sanitise(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitise(item) for item in value]
    return value


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
