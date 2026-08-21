"""Order contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(ge=1, le=100)


class CreateOrderRequest(BaseModel):
    customer_id: UUID
    items: list[OrderItemRequest] = Field(min_length=1, max_length=20)


class OrderItemResponse(BaseModel):
    product_id: UUID
    quantity: int
    unit_price: float


class OrderResponse(BaseModel):
    id: UUID
    customer_id: UUID
    status: Literal["PENDING", "CONFIRMED", "PAYMENT_FAILED", "CANCELLED"]
    total: float
    correlation_id: UUID
    items: list[OrderItemResponse]
    created_at: datetime


class PaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    status: Literal["APPROVED", "DECLINED", "ERROR"]
    attempts: int
    idempotency_key: str
