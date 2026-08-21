"""Correlation identifier helpers."""

from uuid import UUID, uuid4

HEADER = "X-Correlation-ID"


def new_correlation_id() -> UUID:
    return uuid4()
