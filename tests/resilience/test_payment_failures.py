"""Dependency failures validate retry policy and resulting business state."""

import pytest
from sqlalchemy import select

from demo_system.database import Database, EventRecord, PaymentRecord
from framework.assertions.api_assertions import assert_error
from framework.clients.order_client import OrderClient
from framework.models.order import OrderResponse


@pytest.mark.resilience
@pytest.mark.parametrize(
    ("scenario", "payment_status"),
    [
        ("declined", "DECLINED"),
        ("unavailable", "ERROR"),
        ("malformed", "ERROR"),
    ],
)
def test_dependency_failure_leaves_consistent_business_state(
    order_client: OrderClient,
    order: OrderResponse,
    scenario: str,
    payment_status: str,
) -> None:
    response = order_client.confirm_order(
        str(order.id), scenario=scenario, idempotency_key=f"failure-{scenario}"
    )
    assert response.status_code == 502
    assert response.json()["order"]["status"] == "PAYMENT_FAILED"
    assert response.json()["payment"]["status"] == payment_status


@pytest.mark.resilience
def test_decline_is_not_retried(
    order_client: OrderClient,
    order: OrderResponse,
) -> None:
    response = order_client.confirm_order(
        str(order.id), scenario="declined", idempotency_key="no-retry-decline"
    )
    assert response.json()["payment"]["attempts"] == 1


@pytest.mark.resilience
def test_timeout_is_bounded_to_three_attempts(
    order_client: OrderClient,
    order: OrderResponse,
) -> None:
    response = order_client.confirm_order(
        str(order.id), scenario="timeout", idempotency_key="bounded-timeout"
    )
    assert response.json()["payment"]["attempts"] == 3


@pytest.mark.resilience
@pytest.mark.negative
def test_failed_order_cannot_be_confirmed_again_with_a_new_key(
    order_client: OrderClient,
    order: OrderResponse,
) -> None:
    order_client.confirm_order(str(order.id), scenario="declined", idempotency_key="first-fail")
    response = order_client.confirm_order(
        str(order.id), scenario="approved", idempotency_key="second-attempt"
    )
    assert_error(response, status=409, code="INVALID_ORDER_STATE")


@pytest.mark.resilience
@pytest.mark.negative
def test_idempotency_key_cannot_move_between_orders(
    order_client: OrderClient,
    order: OrderResponse,
    customer: object,
    product: object,
) -> None:
    from framework.data.factories import order_factory

    first = order_client.confirm_order(str(order.id), idempotency_key="global-key")
    assert first.status_code == 200
    second_order = order_client.create_order(
        order_factory(str(customer.id), str(product.id))  # type: ignore[attr-defined]
    )
    response = order_client.confirm_order(str(second_order.id), idempotency_key="global-key")
    assert_error(response, status=409, code="IDEMPOTENCY_KEY_REUSED")


@pytest.mark.resilience
def test_failure_emits_one_terminal_event(
    database: Database,
    order_client: OrderClient,
    order: OrderResponse,
) -> None:
    order_client.confirm_order(str(order.id), scenario="unavailable", idempotency_key="one-failure")
    with database.session() as session:
        events = session.scalars(
            select(EventRecord).where(EventRecord.aggregate_id == str(order.id))
        ).all()
        payments = session.scalars(
            select(PaymentRecord).where(PaymentRecord.order_id == str(order.id))
        ).all()
        assert [event.event_type for event in events] == ["OrderCreated", "PaymentFailed"]
        assert len(payments) == 1
