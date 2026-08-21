"""Isolated fixtures shared across API, integration and persistence suites."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from demo_system.app import create_app
from demo_system.database import Database
from demo_system.payment import DeterministicPaymentGateway
from framework.clients.customer_client import CustomerClient
from framework.clients.graphql_client import GraphQLClient
from framework.clients.order_client import OrderClient
from framework.clients.product_client import ProductClient
from framework.data.factories import customer_factory, order_factory, product_factory
from framework.models.customer import CustomerResponse
from framework.models.order import OrderResponse
from framework.models.product import ProductResponse

ADMIN_TOKEN = "admin-token"

# Pact honours this documented opt-out before its FFI is imported by contract modules.
os.environ.setdefault("PACT_DO_NOT_TRACK", "true")


@pytest.fixture
def app(tmp_path: Path) -> FastAPI:
    database_url = f"sqlite:///{tmp_path / 'acme-test.db'}"
    return create_app(
        database_url=database_url,
        payment_gateway=DeterministicPaymentGateway(),
    )


@pytest.fixture
def transport(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client


@pytest.fixture
def database(app: FastAPI) -> Database:
    return app.state.database


@pytest.fixture
def customer_client(transport: TestClient) -> CustomerClient:
    return CustomerClient("http://testserver", token=ADMIN_TOKEN, transport=transport)


@pytest.fixture
def product_client(transport: TestClient) -> ProductClient:
    return ProductClient("http://testserver", token=ADMIN_TOKEN, transport=transport)


@pytest.fixture
def order_client(transport: TestClient) -> OrderClient:
    return OrderClient("http://testserver", token=ADMIN_TOKEN, transport=transport)


@pytest.fixture
def graphql_client(transport: TestClient) -> GraphQLClient:
    return GraphQLClient("http://testserver", token=ADMIN_TOKEN, transport=transport)


@pytest.fixture
def customer(customer_client: CustomerClient) -> CustomerResponse:
    return customer_client.create_customer(customer_factory())


@pytest.fixture
def product(product_client: ProductClient) -> ProductResponse:
    return product_client.create_product(product_factory())


@pytest.fixture
def order(
    order_client: OrderClient,
    customer: CustomerResponse,
    product: ProductResponse,
) -> OrderResponse:
    return order_client.create_order(order_factory(str(customer.id), str(product.id)))
