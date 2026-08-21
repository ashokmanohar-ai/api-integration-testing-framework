"""Transactional outbox, schema, correlation and asynchronous event behaviour."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from framework.clients.base_client import BaseApiClient
from framework.clients.order_client import OrderClient
from framework.messaging.event_assertions import assert_unique_event_ids, find_event
from framework.models.event import DomainEvent, OrderConfirmedEvent, OrderCreatedEvent
from framework.models.order import OrderResponse
from framework.utils.polling import PollTimeoutError, await_until


def events_for(client: BaseApiClient, order_id: str) -> list[dict[str, object]]:
    response = client.get("/events", params={"aggregate_id": order_id})
    response.raise_for_status()
    return response.json()["items"]


@pytest.mark.messaging
def test_order_created_event_has_typed_schema(
    order_client: OrderClient,
    order: OrderResponse,
) -> None:
    event = find_event(events_for(order_client, str(order.id)), "OrderCreated")
    typed = OrderCreatedEvent.model_validate(event.model_dump())
    assert typed.aggregate_id == order.id
    assert typed.correlation_id == order.correlation_id
    assert typed.sequence == 1


@pytest.mark.messaging
def test_confirmation_event_follows_order_created(
    order_client: OrderClient,
    order: OrderResponse,
) -> None:
    order_client.confirm_order(str(order.id), idempotency_key="event-order")
    events = events_for(order_client, str(order.id))
    assert [event["event_type"] for event in events] == ["OrderCreated", "OrderConfirmed"]
    assert [event["sequence"] for event in events] == [1, 2]
    OrderConfirmedEvent.model_validate(events[1])


@pytest.mark.messaging
def test_events_have_unique_identifiers(
    order_client: OrderClient,
    order: OrderResponse,
) -> None:
    order_client.confirm_order(str(order.id), idempotency_key="unique-event")
    assert_unique_event_ids(events_for(order_client, str(order.id)))


@pytest.mark.messaging
@pytest.mark.negative
def test_poison_event_schema_is_rejected() -> None:
    poison = {
        "event_id": str(uuid4()),
        "aggregate_id": str(uuid4()),
        "event_type": "OrderCreated",
        "correlation_id": str(uuid4()),
        "timestamp": "not-a-date",
        "sequence": 1,
        "payload": {},
    }
    with pytest.raises(ValidationError):
        DomainEvent.model_validate(poison)


@pytest.mark.messaging
def test_bounded_polling_observes_event(
    order_client: OrderClient,
    order: OrderResponse,
) -> None:
    observed = await_until(
        lambda: events_for(order_client, str(order.id)),
        timeout=1,
        poll_interval=0.01,
        description="OrderCreated outbox event",
    )
    assert observed[0]["event_type"] == "OrderCreated"


@pytest.mark.messaging
@pytest.mark.negative
def test_polling_timeout_has_diagnostics() -> None:
    with pytest.raises(PollTimeoutError, match="missing event"):
        await_until(
            lambda: None,
            timeout=0.03,
            poll_interval=0.01,
            description="missing event",
        )
