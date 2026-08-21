"""Diagnostic polling instead of arbitrary sleeps."""

from __future__ import annotations

import time
from collections.abc import Callable


class PollTimeoutError(TimeoutError):
    pass


def await_until[T](
    condition: Callable[[], T | None],
    *,
    timeout: float = 10,
    poll_interval: float = 0.25,
    description: str = "condition",
) -> T:
    deadline = time.monotonic() + timeout
    attempts = 0
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        attempts += 1
        try:
            value = condition()
            if value:
                return value
        except Exception as exc:  # diagnostic retention; re-raised as timeout context
            last_error = exc
        time.sleep(poll_interval)
    suffix = f"; last error: {last_error!r}" if last_error else ""
    raise PollTimeoutError(
        f"Timed out after {timeout:.2f}s and {attempts} attempts waiting for {description}{suffix}"
    )
