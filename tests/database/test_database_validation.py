"""API-to-database consistency and isolation."""

import pytest
from sqlalchemy import select

from demo_system.database import (
    CustomerRecord,
    Database,
    EventRecord,
    OrderItemRecord,
    OrderRecord,
    PaymentRecord,
)
from framework.assertions.database_assertions import assert_record_count, assert_record_exists
from framework.clients.customer_client import CustomerClient
from framework.clients.order_client import OrderClient
from framework.data.factories import customer_factory
from framework.models.customer import CustomerResponse
from framework.models.order import OrderResponse


@pytest.mark.database
def test_customer_api_persists_expected_record(
    database: Database,
    customer_client: CustomerClient,
) -> None:
    customer = customer_client.create_customer(customer_factory())
    with database.session() as session:
        record = assert_record_exists(session, CustomerRecord, str(customer.id))
        assert record.email == str(customer.email)
        assert record.status == "ACTIVE"


@pytest.mark.database
def test_order_api_persists_header_and_items(database: Database, order: OrderResponse) -> None:
    with database.session() as session:
        header = assert_record_exists(session, OrderRecord, str(order.id))
        items = session.scalars(
            select(OrderItemRecord).where(OrderItemRecord.order_id == str(order.id))
        ).all()
        assert header.total == order.total
        assert len(items) == 1
        assert items[0].quantity == 1


@pytest.mark.database
def test_confirmation_persists_one_payment(
    database: Database,
    order_client: OrderClient,
    order: OrderResponse,
) -> None:
    response = order_client.confirm_order(str(order.id), idempotency_key="db-check")
    assert response.status_code == 200
    with database.session() as session:
        payments = session.scalars(
            select(PaymentRecord).where(PaymentRecord.order_id == str(order.id))
        ).all()
        assert len(payments) == 1
        assert payments[0].status == "APPROVED"


@pytest.mark.database
def test_each_test_starts_with_isolated_database(
    database: Database,
    customer: CustomerResponse,
) -> None:
    with database.session() as session:
        assert_record_count(session, CustomerRecord, 1)
        assert_record_count(session, OrderRecord, 0)
        assert_record_count(session, PaymentRecord, 0)
        assert_record_count(session, EventRecord, 0)
