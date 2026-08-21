"""API assertions with actionable failure diagnostics."""

from __future__ import annotations

import json
from collections.abc import Iterable

import httpx

from framework.models.error import ErrorResponse
from framework.utils.logger import sanitise


def assert_status(response: httpx.Response, expected: int | Iterable[int]) -> None:
    expected_set = {expected} if isinstance(expected, int) else set(expected)
    if response.status_code not in expected_set:
        request = response.request
        correlation_id = response.headers.get(
            "X-Correlation-ID", request.headers.get("X-Correlation-ID", "missing")
        )
        try:
            body = sanitise(response.json())
        except json.JSONDecodeError:
            body = response.text[:1000]
        raise AssertionError(
            "API assertion failed\n"
            f"Method: {request.method}\n"
            f"Endpoint: {request.url}\n"
            f"Expected Status: {sorted(expected_set)}\n"
            f"Actual Status: {response.status_code}\n"
            f"Correlation ID: {correlation_id}\n"
            f"Response: {body}"
        )


def assert_error(
    response: httpx.Response,
    *,
    status: int,
    code: str,
    field: str | None = None,
) -> ErrorResponse:
    assert_status(response, status)
    problem = ErrorResponse.model_validate(response.json())
    assert problem.code == code
    if field is not None:
        assert problem.field == field
    return problem


def assert_response_time(response: httpx.Response, maximum_seconds: float) -> None:
    assert response.elapsed.total_seconds() < maximum_seconds, (
        f"Response took {response.elapsed.total_seconds():.3f}s; "
        f"threshold is {maximum_seconds:.3f}s"
    )
