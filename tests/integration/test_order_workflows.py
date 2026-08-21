"""Showcase workflows validate API, payment dependency, DB and events together."""

import pytest
from sqlalchemy import select

from demo_system.database import Database, EventRecord, PaymentRecord, ProductRecord
from framework.clients.order_client import OrderClient
from framework.clients.product_client import ProductClient
from framework.models.order import OrderResponse
from framework.models.product import ProductResponse


@pytest.mark.integration
@pytest.mark.critical
def test_successful_order_showcase_workflow(
    database: Database,
    order_client: OrderClient,
    product_client: ProductClient,
    order: OrderResponse,
    product: ProductResponse,
) -> None:
    response = order_client.confirm_order(
        str(order.id), scenario="approved", idempotency_key="success-showcase"
    )
    assert response.status_code == 200
    assert response.json()["order"]["status"] == "CONFIRMED"
    assert response.json()["payment"]["status"] == "APPROVED"

    persisted_product = product_client.get_product(str(product.id))
    assert persisted_product.inventory == product.inventory - 1
    with database.session() as session:
        events = session.scalars(
            select(EventRecord)
            .where(EventRecord.aggregate_id == str(order.id))
            .order_by(EventRecord.sequence)
        ).all()
        payments = session.scalars(
            select(PaymentRecord).where(PaymentRecord.order_id == str(order.id))
        ).all()
        assert [event.event_type for event in events] == ["OrderCreated", "OrderConfirmed"]
        assert all(event.correlation_id == str(order.correlation_id) for event in events)
        assert len(payments) == 1


@pytest.mark.integration
@pytest.mark.resilience
@pytest.mark.critical
def test_payment_503_showcase_failure_workflow(
    database: Database,
    order_client: OrderClient,
    order: OrderResponse,
    product: ProductResponse,
) -> None:
    response = order_client.confirm_order(
        str(order.id), scenario="unavailable", idempotency_key="failure-showcase"
    )
    assert response.status_code == 502
    assert response.json()["order"]["status"] == "PAYMENT_FAILED"
    assert response.json()["payment"]["attempts"] == 3
    with database.session() as session:
        unchanged_product = session.get(ProductRecord, str(product.id))
        events = session.scalars(
            select(EventRecord).where(EventRecord.aggregate_id == str(order.id))
        ).all()
        assert unchanged_product is not None
        assert unchanged_product.inventory == product.inventory
        assert [event.event_type for event in events] == ["OrderCreated", "PaymentFailed"]
        assert "OrderConfirmed" not in [event.event_type for event in events]


@pytest.mark.integration
@pytest.mark.resilience
def test_transient_dependency_recovers_on_third_attempt(
    order_client: OrderClient,
    order: OrderResponse,
) -> None:
    response = order_client.confirm_order(
        str(order.id), scenario="transient", idempotency_key="transient-showcase"
    )
    assert response.status_code == 200
    assert response.json()["order"]["status"] == "CONFIRMED"
    assert response.json()["payment"]["attempts"] == 3


@pytest.mark.integration
def test_payment_idempotency_prevents_duplicate_side_effects(
    database: Database,
    order_client: OrderClient,
    order: OrderResponse,
) -> None:
    first = order_client.confirm_order(str(order.id), idempotency_key="same-key")
    second = order_client.confirm_order(str(order.id), idempotency_key="same-key")
    assert first.status_code == second.status_code == 200
    assert second.headers["X-Idempotent-Replay"] == "true"
    assert first.json()["payment"]["id"] == second.json()["payment"]["id"]
    with database.session() as session:
        payments = session.scalars(
            select(PaymentRecord).where(PaymentRecord.order_id == str(order.id))
        ).all()
        confirmation_events = session.scalars(
            select(EventRecord).where(
                EventRecord.aggregate_id == str(order.id),
                EventRecord.event_type == "OrderConfirmed",
            )
        ).all()
        assert len(payments) == 1
        assert len(confirmation_events) == 1
