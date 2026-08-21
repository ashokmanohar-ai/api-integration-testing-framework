"""Opt-in checks prove the Compose API, WireMock and Redpanda endpoints are real."""

import os
from uuid import uuid4

import httpx
import pytest

from framework.messaging.consumer import consume_events

pytestmark = [
    pytest.mark.docker,
    pytest.mark.skipif(
        os.getenv("RUN_DOCKER_TESTS") != "1",
        reason="Set RUN_DOCKER_TESTS=1 after docker compose up -d",
    ),
]


def test_compose_api_and_postgres_work_together() -> None:
    headers = {"Authorization": "Bearer admin-token"}
    response = httpx.post(
        "http://localhost:8000/customers",
        headers=headers,
        json={
            "first_name": "Docker",
            "last_name": "Check",
            "email": f"docker-{os.getpid()}@example.com",
        },
        timeout=5,
    )
    assert response.status_code in {201, 409}


def test_wiremock_payment_mapping_is_loaded() -> None:
    response = httpx.post(
        "http://localhost:8080/payments/authorise",
        headers={"X-Payment-Scenario": "approved"},
        json={"order_id": "docker-check", "amount": 1.0},
        timeout=5,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_order_event_is_delivered_to_redpanda() -> None:
    headers = {"Authorization": "Bearer admin-token"}
    unique = uuid4().hex[:10]
    customer = httpx.post(
        "http://localhost:8000/customers",
        headers=headers,
        json={
            "first_name": "Broker",
            "last_name": "Check",
            "email": f"broker-{unique}@example.com",
        },
        timeout=5,
    )
    customer.raise_for_status()
    product = httpx.post(
        "http://localhost:8000/products",
        headers=headers,
        json={
            "sku": f"BROKER-{unique.upper()}",
            "name": "Broker check",
            "price": 1.0,
            "inventory": 1,
        },
        timeout=5,
    )
    product.raise_for_status()
    order = httpx.post(
        "http://localhost:8000/orders",
        headers=headers,
        json={
            "customer_id": customer.json()["id"],
            "items": [{"product_id": product.json()["id"], "quantity": 1}],
        },
        timeout=5,
    )
    order.raise_for_status()
    received = next(
        (
            event
            for event in consume_events(
                "localhost:19092",
                "acme.order-events",
                group_id=f"docker-check-{unique}",
                timeout_ms=10_000,
            )
            if event.get("aggregate_id") == order.json()["id"]
        ),
        None,
    )
    assert received is not None
    assert received["event_type"] == "OrderCreated"
