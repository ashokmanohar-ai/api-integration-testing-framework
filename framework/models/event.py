"""Event contracts used for outbox and broker validation."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class DomainEvent(BaseModel):
    event_id: UUID
    aggregate_id: UUID
    event_type: str
    correlation_id: UUID
    timestamp: datetime
    sequence: int
    payload: dict[str, Any]


class OrderCreatedEvent(DomainEvent):
    event_type: Literal["OrderCreated"] = "OrderCreated"


class OrderConfirmedEvent(DomainEvent):
    event_type: Literal["OrderConfirmed"] = "OrderConfirmed"


class PaymentFailedEvent(DomainEvent):
    event_type: Literal["PaymentFailed"] = "PaymentFailed"
