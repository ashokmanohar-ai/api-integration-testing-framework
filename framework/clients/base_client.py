"""Observable HTTPX client that preserves the underlying response."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any, Protocol, cast
from uuid import uuid4

import httpx

from framework.utils.logger import sanitise

LOGGER = logging.getLogger(__name__)


class RequestTransport(Protocol):
    """Small protocol implemented by HTTPX and Starlette test clients."""

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response: ...

    def close(self) -> None: ...


class BaseApiClient:
    """Thin HTTP client with auth, correlation, timing, logging and optional retries."""

    def __init__(
        self,
        base_url: str,
        *,
        token: str | None = None,
        timeout: float = 5.0,
        transport: RequestTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._owns_transport = transport is None
        self.transport = cast(
            RequestTransport,
            transport or httpx.Client(base_url=self.base_url, timeout=timeout, trust_env=False),
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: Mapping[str, str] | None = None,
        retry_statuses: frozenset[int] = frozenset(),
        max_attempts: int = 1,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send a request; retry only explicitly selected safe scenarios."""

        request_headers = dict(headers or {})
        request_headers.setdefault("X-Correlation-ID", str(uuid4()))
        if self._token:
            request_headers.setdefault("Authorization", f"Bearer {self._token}")
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"

        response: httpx.Response | None = None
        for attempt in range(1, max_attempts + 1):
            started = time.perf_counter()
            response = self.transport.request(method, url, headers=request_headers, **kwargs)
            duration_ms = (time.perf_counter() - started) * 1000
            LOGGER.info(
                "api_request method=%s url=%s status=%s duration_ms=%.2f correlation_id=%s "
                "attempt=%s body=%s",
                method.upper(),
                url,
                response.status_code,
                duration_ms,
                request_headers["X-Correlation-ID"],
                attempt,
                sanitise(kwargs.get("json")),
            )
            if response.status_code not in retry_statuses or attempt == max_attempts:
                return response
        raise RuntimeError("unreachable")

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)

    def close(self) -> None:
        if self._owns_transport:
            self.transport.close()

    def __enter__(self) -> BaseApiClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
