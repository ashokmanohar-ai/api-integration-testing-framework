"""GraphQL query, mutation, variable, nested and error semantics."""

from pathlib import Path

import pytest

from framework.clients.graphql_client import GraphQLClient
from framework.models.customer import CustomerResponse
from framework.models.product import ProductResponse

QUERY_DIR = Path("framework/schemas/graphql")


@pytest.mark.graphql
def test_query_products(
    graphql_client: GraphQLClient,
    product: ProductResponse,
) -> None:
    response = graphql_client.execute_file(QUERY_DIR / "products.graphql", variables={"limit": 10})
    data = graphql_client.assert_success(response)
    assert data["products"][0]["id"] == str(product.id)
    assert data["products"][0]["inventory"] == product.inventory


@pytest.mark.graphql
def test_query_customer(
    graphql_client: GraphQLClient,
    customer: CustomerResponse,
) -> None:
    response = graphql_client.execute_file(
        QUERY_DIR / "customer.graphql", variables={"id": str(customer.id)}
    )
    data = graphql_client.assert_success(response)
    assert data["customer"]["email"] == str(customer.email)
    assert data["customer"]["status"] == "ACTIVE"


@pytest.mark.graphql
@pytest.mark.integration
def test_create_order_mutation_with_nested_items(
    graphql_client: GraphQLClient,
    customer: CustomerResponse,
    product: ProductResponse,
) -> None:
    response = graphql_client.execute_file(
        QUERY_DIR / "create_order.graphql",
        variables={
            "customerId": str(customer.id),
            "items": [{"productId": str(product.id), "quantity": 2}],
        },
    )
    data = graphql_client.assert_success(response)
    assert data["createOrder"]["status"] == "PENDING"
    assert data["createOrder"]["items"] == [
        {"productId": str(product.id), "quantity": 2, "unitPrice": product.price}
    ]


@pytest.mark.graphql
@pytest.mark.negative
def test_invalid_query_field_returns_graphql_error(graphql_client: GraphQLClient) -> None:
    response = graphql_client.execute("query { products { doesNotExist } }")
    assert response.status_code == 200
    assert response.json()["data"] is None
    assert "errors" in response.json()


@pytest.mark.graphql
@pytest.mark.negative
def test_missing_required_variable_returns_graphql_error(graphql_client: GraphQLClient) -> None:
    response = graphql_client.execute(
        "query Customer($id: ID!) { customer(id: $id) { id } }",
        variables={},
    )
    assert response.status_code == 200
    assert response.json()["errors"][0]["message"]


@pytest.mark.graphql
@pytest.mark.security
def test_graphql_authorization_failure(
    transport: object,
    customer: CustomerResponse,
) -> None:
    client = GraphQLClient("http://testserver", transport=transport)  # type: ignore[arg-type]
    response = client.execute(
        "query Customer($id: ID!) { customer(id: $id) { id } }",
        variables={"id": str(customer.id)},
    )
    assert response.status_code == 200
    assert response.json()["errors"][0]["extensions"]["code"] == "AUTH_REQUIRED"


@pytest.mark.graphql
@pytest.mark.negative
def test_graphql_limit_boundary(graphql_client: GraphQLClient) -> None:
    response = graphql_client.execute(
        "query Products($limit: Int!) { products(limit: $limit) { id } }",
        variables={"limit": 101},
    )
    assert response.status_code == 200
    assert response.json()["errors"][0]["extensions"]["field"] == "limit"
