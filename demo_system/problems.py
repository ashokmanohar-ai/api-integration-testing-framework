"""Consistent error contract and exception handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ProblemError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        field: str | None = None,
    ) -> None:
        self.status = status
        self.code = code
        self.message = message
        self.field = field


def correlation_id(request: Request) -> UUID:
    value = getattr(request.state, "correlation_id", None)
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return uuid4()


def problem_response(
    request: Request,
    *,
    status: int,
    code: str,
    message: str,
    field: str | None = None,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status,
        content={
            "code": code,
            "message": message,
            "field": field,
            "correlation_id": str(correlation_id(request)),
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )
    response.headers["X-Correlation-ID"] = str(correlation_id(request))
    return response


async def problem_handler(request: Request, exc: ProblemError) -> JSONResponse:
    return problem_response(
        request,
        status=exc.status,
        code=exc.code,
        message=exc.message,
        field=exc.field,
    )


async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0]
    location = first.get("loc", [])
    field = str(location[-1]) if location else None
    return problem_response(
        request,
        status=400,
        code="VALIDATION_ERROR",
        message=str(first.get("msg", "Request validation failed")),
        field=field,
    )
