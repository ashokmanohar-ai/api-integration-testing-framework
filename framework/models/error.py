"""Stable API error contract."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
    field: str | None = None
    correlation_id: UUID
    timestamp: datetime
