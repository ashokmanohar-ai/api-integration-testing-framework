"""Explicit retry policy for dependency behaviour, not blanket test retries."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class RetryResult[T]:
    value: T
    attempts: int


def retry_call[T](
    operation: Callable[[], T],
    *,
    should_retry: Callable[[T], bool],
    max_attempts: int = 3,
    backoff_seconds: float = 0,
) -> RetryResult[T]:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    value: T
    for attempt in range(1, max_attempts + 1):
        value = operation()
        if not should_retry(value) or attempt == max_attempts:
            return RetryResult(value=value, attempts=attempt)
        if backoff_seconds:
            time.sleep(backoff_seconds * attempt)
    raise RuntimeError("unreachable")
