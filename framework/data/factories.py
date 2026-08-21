"""Parallel-safe synthetic test-data factories."""

from __future__ import annotations

from uuid import uuid4

from framework.models.customer import CreateCustomerRequest
from framework.models.order import CreateOrderRequest, OrderItemRequest
from framework.models.product import CreateProductRequest


def customer_factory(**overrides: object) -> CreateCustomerRequest:
    unique = uuid4().hex[:10]
    values: dict[str, object] = {
        "first_name": "Avery",
        "last_name": f"Test-{unique}",
        "email": f"avery.{unique}@example.com",
    }
    values.update(overrides)
    return CreateCustomerRequest.model_validate(values)


def product_factory(**overrides: object) -> CreateProductRequest:
    unique = uuid4().hex[:10].upper()
    values: dict[str, object] = {
        "sku": f"SKU-{unique}",
        "name": f"Test product {unique}",
        "price": 19.99,
        "inventory": 10,
    }
    values.update(overrides)
    return CreateProductRequest.model_validate(values)


def order_factory(customer_id: str, product_id: str, **overrides: object) -> CreateOrderRequest:
    values: dict[str, object] = {
        "customer_id": customer_id,
        "items": [OrderItemRequest(product_id=product_id, quantity=1)],
    }
    values.update(overrides)
    return CreateOrderRequest.model_validate(values)
