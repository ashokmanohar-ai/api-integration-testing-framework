"""Real Pact V4 consumer tests execute production clients against a mock provider."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from pact import Pact, match

from framework.clients.customer_client import CustomerClient
from framework.clients.product_client import ProductClient


@pytest.fixture
def customer_pact(tmp_path: Path) -> Iterator[Pact]:
    pact = Pact("AcmeWeb", "AcmeCommerceApi").with_specification("V4")
    yield pact
    pact.write_file(tmp_path)


@pytest.mark.contract
def test_customer_consumer_contract(customer_pact: Pact) -> None:
    customer_id = "11111111-1111-4111-8111-111111111111"
    expected = {
        "id": match.regex(customer_id, regex=r"^[0-9a-f-]{36}$"),
        "first_name": match.str("Avery"),
        "last_name": match.str("Tester"),
        "email": match.regex("avery@example.com", regex=r"^.+@.+\..+$"),
        "status": match.regex("ACTIVE", regex=r"^(ACTIVE|INACTIVE)$"),
        "created_at": match.datetime("2026-01-01T00:00:00Z"),
    }
    (
        customer_pact.upon_receiving("a request for an existing customer")
        .given("customer exists", id=customer_id)
        .with_request("GET", f"/customers/{customer_id}")
        .will_respond_with(200)
        .with_body(expected, content_type="application/json")
    )
    with customer_pact.serve() as server:
        client = CustomerClient(str(server.url), token="admin-token")
        customer = client.get_customer(customer_id)
        assert str(customer.id) == customer_id
        assert customer.status == "ACTIVE"


@pytest.fixture
def product_pact(tmp_path: Path) -> Iterator[Pact]:
    pact = Pact("OrderService", "AcmeCommerceApi").with_specification("V4")
    yield pact
    pact.write_file(tmp_path)


@pytest.mark.contract
def test_product_consumer_contract(product_pact: Pact) -> None:
    product_id = "22222222-2222-4222-8222-222222222222"
    expected = {
        "id": match.regex(product_id, regex=r"^[0-9a-f-]{36}$"),
        "sku": match.str("SKU-CONTRACT"),
        "name": match.str("Contract product"),
        "price": match.decimal(29.99),
        "inventory": match.int(10),
        "created_at": match.datetime("2026-01-01T00:00:00Z"),
    }
    (
        product_pact.upon_receiving("a request for an orderable product")
        .given("product exists", id=product_id)
        .with_request("GET", f"/products/{product_id}")
        .will_respond_with(200)
        .with_body(expected, content_type="application/json")
    )
    with product_pact.serve() as server:
        client = ProductClient(str(server.url), token="admin-token")
        product = client.get_product(product_id)
        assert str(product.id) == product_id
        assert product.inventory == 10
