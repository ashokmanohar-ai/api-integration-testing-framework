"""GraphQL schema over the same service and persistence layers as REST."""

from __future__ import annotations

from typing import Any

from graphql import GraphQLError, build_schema, graphql
from sqlalchemy import select
from sqlalchemy.orm import Session

from demo_system.auth import Principal
from demo_system.database import CustomerRecord, ProductRecord
from demo_system.problems import ProblemError
from demo_system.services import (
    create_order_record,
    customer_payload,
    order_payload,
    product_payload,
)
from framework.models.order import CreateOrderRequest

SCHEMA = build_schema(
    """
    type Customer {
      id: ID!
      firstName: String!
      lastName: String!
      email: String!
      status: String!
      createdAt: String!
    }
    type Product {
      id: ID!
      sku: String!
      name: String!
      price: Float!
      inventory: Int!
      createdAt: String!
    }
    type OrderItem { productId: ID!, quantity: Int!, unitPrice: Float! }
    type Order {
      id: ID!
      customerId: ID!
      status: String!
      total: Float!
      correlationId: ID!
      items: [OrderItem!]!
      createdAt: String!
    }
    input OrderItemInput { productId: ID!, quantity: Int! }
    type Query {
      products(limit: Int = 20): [Product!]!
      customer(id: ID!): Customer
    }
    type Mutation {
      createOrder(customerId: ID!, items: [OrderItemInput!]!): Order!
    }
    """
)


def camelise(payload: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "first_name": "firstName",
        "last_name": "lastName",
        "created_at": "createdAt",
        "customer_id": "customerId",
        "correlation_id": "correlationId",
        "product_id": "productId",
        "unit_price": "unitPrice",
    }
    return {
        mapping.get(key, key): (
            [camelise(item) for item in value]
            if isinstance(value, list)
            else value.isoformat()
            if hasattr(value, "isoformat")
            else value
        )
        for key, value in payload.items()
    }


def require_graphql_auth(info: Any) -> Principal:
    principal: Principal | None = info.context.get("principal")
    if principal is None:
        raise GraphQLError("Authentication required", extensions={"code": "AUTH_REQUIRED"})
    return principal


def resolve_products(_root: object, info: Any, limit: int = 20) -> list[dict[str, Any]]:
    require_graphql_auth(info)
    if limit < 1 or limit > 100:
        raise GraphQLError(
            "limit must be between 1 and 100",
            extensions={"code": "VALIDATION_ERROR", "field": "limit"},
        )
    session: Session = info.context["session"]
    products = session.scalars(select(ProductRecord).limit(limit)).all()
    return [camelise(product_payload(product)) for product in products]


def resolve_customer(_root: object, info: Any, id: str) -> dict[str, Any] | None:
    principal = require_graphql_auth(info)
    if principal.role == "CUSTOMER" and principal.subject != id:
        raise GraphQLError("Forbidden", extensions={"code": "FORBIDDEN"})
    session: Session = info.context["session"]
    customer = session.get(CustomerRecord, id)
    return camelise(customer_payload(customer)) if customer else None


def resolve_create_order(
    _root: object,
    info: Any,
    customerId: str,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    principal = require_graphql_auth(info)
    if principal.role == "CUSTOMER" and principal.subject != customerId:
        raise GraphQLError("Forbidden", extensions={"code": "FORBIDDEN"})
    session: Session = info.context["session"]
    request = CreateOrderRequest.model_validate(
        {
            "customer_id": customerId,
            "items": [
                {"product_id": item["productId"], "quantity": item["quantity"]} for item in items
            ],
        }
    )
    try:
        order = create_order_record(session, request, info.context["correlation_id"])
    except ProblemError as exc:
        raise GraphQLError(exc.message, extensions={"code": exc.code}) from exc
    return camelise(order_payload(order))


SCHEMA.get_type("Query").fields["products"].resolve = resolve_products  # type: ignore[union-attr]
SCHEMA.get_type("Query").fields["customer"].resolve = resolve_customer  # type: ignore[union-attr]
SCHEMA.get_type("Mutation").fields["createOrder"].resolve = resolve_create_order  # type: ignore[union-attr]


async def execute_graphql(
    query: str,
    *,
    variables: dict[str, Any],
    operation_name: str | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    result = await graphql(
        SCHEMA,
        query,
        variable_values=variables,
        operation_name=operation_name,
        context_value=context,
    )
    payload: dict[str, Any] = {"data": result.data}
    if result.errors:
        payload["errors"] = [
            {
                "message": error.message,
                "locations": [location.formatted for location in error.locations or []],
                "path": error.path,
                "extensions": error.extensions,
            }
            for error in result.errors
        ]
    return payload
