"""Business services shared by REST and GraphQL boundaries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from demo_system.database import (
    CustomerRecord,
    EventRecord,
    OrderItemRecord,
    OrderRecord,
    PaymentRecord,
    ProductRecord,
)
from demo_system.payment import PaymentGateway
from demo_system.problems import ProblemError
from framework.models.order import CreateOrderRequest
from framework.utils.retry import retry_call


def now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """SQLite drops timezone metadata; keep the public contract consistently UTC-aware."""

    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def customer_payload(record: CustomerRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "first_name": record.first_name,
        "last_name": record.last_name,
        "email": record.email,
        "status": record.status,
        "created_at": as_utc(record.created_at),
    }


def product_payload(record: ProductRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "sku": record.sku,
        "name": record.name,
        "price": record.price,
        "inventory": record.inventory,
        "created_at": as_utc(record.created_at),
    }


def order_payload(record: OrderRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "customer_id": record.customer_id,
        "status": record.status,
        "total": round(record.total, 2),
        "correlation_id": record.correlation_id,
        "items": [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in record.items
        ],
        "created_at": as_utc(record.created_at),
    }


def event_payload(record: EventRecord) -> dict[str, Any]:
    return {
        "event_id": record.event_id,
        "aggregate_id": record.aggregate_id,
        "event_type": record.event_type,
        "correlation_id": record.correlation_id,
        "timestamp": as_utc(record.timestamp),
        "sequence": record.sequence,
        "payload": record.payload,
    }


def emit_event(
    session: Session,
    *,
    event_type: str,
    aggregate_id: str,
    correlation_id: str,
    sequence: int,
    payload: dict[str, Any],
) -> EventRecord:
    event = EventRecord(
        event_id=str(uuid4()),
        aggregate_id=aggregate_id,
        event_type=event_type,
        correlation_id=correlation_id,
        timestamp=now(),
        sequence=sequence,
        payload=payload,
        processed=False,
    )
    session.add(event)
    return event


def create_order_record(
    session: Session,
    request: CreateOrderRequest,
    correlation_id: str,
) -> OrderRecord:
    customer = session.get(CustomerRecord, str(request.customer_id))
    if customer is None:
        raise ProblemError(404, "CUSTOMER_NOT_FOUND", "The customer does not exist")
    if customer.status != "ACTIVE":
        raise ProblemError(409, "CUSTOMER_INACTIVE", "Inactive customers cannot create orders")

    order = OrderRecord(
        id=str(uuid4()),
        customer_id=str(request.customer_id),
        status="PENDING",
        total=0,
        correlation_id=correlation_id,
        created_at=now(),
    )
    session.add(order)
    total = 0.0
    for requested_item in request.items:
        product = session.get(ProductRecord, str(requested_item.product_id))
        if product is None:
            raise ProblemError(404, "PRODUCT_NOT_FOUND", "The product does not exist")
        if requested_item.quantity > product.inventory:
            raise ProblemError(
                409,
                "INSUFFICIENT_INVENTORY",
                f"Requested {requested_item.quantity}; available {product.inventory}",
                field="quantity",
            )
        total += product.price * requested_item.quantity
        order.items.append(
            OrderItemRecord(
                id=str(uuid4()),
                product_id=product.id,
                quantity=requested_item.quantity,
                unit_price=product.price,
            )
        )
    order.total = round(total, 2)
    emit_event(
        session,
        event_type="OrderCreated",
        aggregate_id=order.id,
        correlation_id=correlation_id,
        sequence=1,
        payload={"order_id": order.id, "customer_id": order.customer_id, "total": order.total},
    )
    session.flush()
    return order


def confirm_order_record(
    session: Session,
    *,
    order: OrderRecord,
    gateway: PaymentGateway,
    scenario: str,
    idempotency_key: str,
) -> tuple[OrderRecord, PaymentRecord, bool]:
    existing = session.scalar(
        select(PaymentRecord).where(PaymentRecord.idempotency_key == idempotency_key)
    )
    if existing is not None:
        if existing.order_id != order.id:
            raise ProblemError(
                409,
                "IDEMPOTENCY_KEY_REUSED",
                "The idempotency key belongs to a different order",
            )
        return order, existing, True
    if order.status != "PENDING":
        raise ProblemError(
            409,
            "INVALID_ORDER_STATE",
            f"Order in state {order.status} cannot be confirmed",
        )

    result = retry_call(
        lambda: gateway.authorise(
            order_id=order.id,
            amount=order.total,
            correlation_id=order.correlation_id,
            scenario=scenario,
        ),
        should_retry=lambda decision: decision.status in {"RETRYABLE", "TIMEOUT"},
        max_attempts=3,
    )
    approved = result.value.status == "APPROVED"
    payment_status = (
        "APPROVED" if approved else "DECLINED" if result.value.status == "DECLINED" else "ERROR"
    )
    payment = PaymentRecord(
        id=str(uuid4()),
        order_id=order.id,
        status=payment_status,
        attempts=result.attempts,
        idempotency_key=idempotency_key,
        created_at=now(),
    )
    order.payments.append(payment)
    if approved:
        for item in order.items:
            product = session.get(ProductRecord, item.product_id)
            if product is None or product.inventory < item.quantity:
                raise ProblemError(
                    409,
                    "INVENTORY_CHANGED",
                    "Inventory changed before confirmation",
                )
            product.inventory -= item.quantity
        order.status = "CONFIRMED"
        emit_event(
            session,
            event_type="OrderConfirmed",
            aggregate_id=order.id,
            correlation_id=order.correlation_id,
            sequence=2,
            payload={"order_id": order.id, "payment_id": payment.id},
        )
    else:
        order.status = "PAYMENT_FAILED"
        emit_event(
            session,
            event_type="PaymentFailed",
            aggregate_id=order.id,
            correlation_id=order.correlation_id,
            sequence=2,
            payload={"order_id": order.id, "attempts": payment.attempts},
        )
    session.flush()
    return order, payment, False
