"""Product, pagination and order API behaviour."""

import pytest
from fastapi.testclient import TestClient

from framework.assertions.api_assertions import assert_error
from framework.clients.customer_client import CustomerClient
from framework.clients.order_client import OrderClient
from framework.clients.product_client import ProductClient
from framework.data.factories import customer_factory, order_factory, product_factory
from framework.models.customer import CustomerResponse
from framework.models.product import ProductResponse


@pytest.mark.api
@pytest.mark.regression
def test_create_and_get_product(product_client: ProductClient) -> None:
    created = product_client.create_product(product_factory(price=42.5, inventory=8))
    fetched = product_client.get_product(str(created.id))
    assert fetched == created


@pytest.mark.api
@pytest.mark.negative
def test_duplicate_product_sku(product_client: ProductClient) -> None:
    request = product_factory()
    product_client.create_product(request)
    response = product_client.post("/products", json=request.model_dump(mode="json"))
    assert_error(response, status=409, code="DUPLICATE_SKU", field="sku")


@pytest.mark.api
@pytest.mark.parametrize(
    ("page", "page_size", "expected_count"),
    [(1, 2, 2), (3, 2, 1), (4, 2, 0)],
)
def test_product_pagination(
    product_client: ProductClient,
    page: int,
    page_size: int,
    expected_count: int,
) -> None:
    for price in [10, 20, 30, 40, 50]:
        product_client.create_product(product_factory(price=price))
    response = product_client.list_products(page=page, page_size=page_size)
    assert response.status_code == 200
    assert len(response.json()["items"]) == expected_count
    assert response.json()["total"] == 5


@pytest.mark.api
def test_product_filter_and_descending_sort(product_client: ProductClient) -> None:
    for price, inventory in [(10, 0), (30, 8), (20, 5)]:
        product_client.create_product(product_factory(price=price, inventory=inventory))
    response = product_client.list_products(
        min_inventory=1, sort="price", direction="desc", page_size=100
    )
    payload = response.json()
    assert [item["price"] for item in payload["items"]] == [30, 20]


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"sku": "AB", "name": "P", "price": 10, "inventory": 1}, "sku"),
        ({"sku": "SKU-OK", "name": "", "price": 10, "inventory": 1}, "name"),
        ({"sku": "SKU-OK", "name": "P", "price": 0, "inventory": 1}, "price"),
        ({"sku": "SKU-OK", "name": "P", "price": 10, "inventory": -1}, "inventory"),
    ],
)
def test_invalid_product_boundaries(
    transport: TestClient,
    payload: dict[str, object],
    field: str,
) -> None:
    response = transport.post(
        "/products", json=payload, headers={"Authorization": "Bearer admin-token"}
    )
    assert_error(response, status=400, code="VALIDATION_ERROR", field=field)


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page_size": 101},
        {"direction": "sideways"},
    ],
)
def test_invalid_pagination_and_sorting(
    product_client: ProductClient,
    params: dict[str, object],
) -> None:
    response = product_client.list_products(**params)
    assert_error(response, status=400, code="VALIDATION_ERROR")


@pytest.mark.api
@pytest.mark.regression
def test_create_and_retrieve_order(
    order_client: OrderClient,
    customer: CustomerResponse,
    product: ProductResponse,
) -> None:
    order = order_client.create_order(
        order_factory(
            str(customer.id),
            str(product.id),
            items=[{"product_id": product.id, "quantity": 2}],
        )
    )
    fetched = order_client.get_order(str(order.id))
    assert fetched == order
    assert fetched.total == product.price * 2
    assert fetched.status == "PENDING"


@pytest.mark.api
@pytest.mark.negative
def test_order_rejects_insufficient_inventory(
    order_client: OrderClient,
    customer: CustomerResponse,
    product: ProductResponse,
) -> None:
    response = order_client.post(
        "/orders",
        json={
            "customer_id": str(customer.id),
            "items": [{"product_id": str(product.id), "quantity": 100}],
        },
    )
    assert_error(response, status=409, code="INSUFFICIENT_INVENTORY", field="quantity")


@pytest.mark.api
@pytest.mark.negative
def test_order_rejects_empty_items(
    order_client: OrderClient,
    customer: CustomerResponse,
) -> None:
    response = order_client.post("/orders", json={"customer_id": str(customer.id), "items": []})
    assert_error(response, status=400, code="VALIDATION_ERROR", field="items")


@pytest.mark.api
@pytest.mark.security
def test_customer_cannot_read_another_customers_order(
    transport: TestClient,
    customer_client: CustomerClient,
    order_client: OrderClient,
    customer: CustomerResponse,
    product: ProductResponse,
) -> None:
    other = customer_client.create_customer(customer_factory())
    order = order_client.create_order(order_factory(str(customer.id), str(product.id)))
    response = transport.get(
        f"/orders/{order.id}",
        headers={"Authorization": f"Bearer customer-token:{other.id}"},
    )
    assert_error(response, status=403, code="FORBIDDEN")
