"""Customer CRUD, error contract and business behaviour."""

import pytest
from fastapi.testclient import TestClient

from framework.assertions.api_assertions import assert_error
from framework.clients.customer_client import CustomerClient
from framework.data.factories import customer_factory
from framework.models.customer import CustomerResponse


@pytest.mark.api
@pytest.mark.regression
def test_customer_crud_workflow(customer_client: CustomerClient) -> None:
    created = customer_client.create_customer(customer_factory())
    fetched = customer_client.get_customer(str(created.id))
    assert fetched == created

    updated = customer_client.update_customer(
        str(created.id), {"first_name": "Updated", "status": "INACTIVE"}
    )
    assert updated.status_code == 200
    assert updated.json()["first_name"] == "Updated"
    assert updated.json()["status"] == "INACTIVE"

    deleted = customer_client.delete_customer(str(created.id))
    assert deleted.status_code == 204
    assert customer_client.get_customer_response(str(created.id)).status_code == 404


@pytest.mark.api
@pytest.mark.negative
def test_duplicate_customer_returns_stable_error(customer_client: CustomerClient) -> None:
    request = customer_factory()
    customer_client.create_customer(request)
    response = customer_client.post("/customers", json=request.model_dump(mode="json"))
    problem = assert_error(response, status=409, code="DUPLICATE_CUSTOMER", field="email")
    assert problem.correlation_id
    assert problem.timestamp


@pytest.mark.api
@pytest.mark.negative
def test_unknown_customer_returns_not_found(customer_client: CustomerClient) -> None:
    response = customer_client.get_customer_response("00000000-0000-0000-0000-000000000099")
    assert_error(response, status=404, code="CUSTOMER_NOT_FOUND")


@pytest.mark.api
def test_customer_schema_is_strongly_typed(
    customer_client: CustomerClient,
) -> None:
    customer = customer_client.create_customer(customer_factory())
    parsed = CustomerResponse.model_validate(
        customer_client.get_customer_response(str(customer.id)).json()
    )
    assert parsed.email == customer.email
    assert parsed.status == "ACTIVE"


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"last_name": "Tester", "email": "a@example.com"}, "first_name"),
        ({"first_name": "", "last_name": "Tester", "email": "a@example.com"}, "first_name"),
        ({"first_name": "A", "last_name": "Tester", "email": "not-email"}, "email"),
        ({"first_name": "A", "last_name": "x" * 51, "email": "a@example.com"}, "last_name"),
    ],
    ids=["missing-required", "blank", "invalid-email", "last-name-max"],
)
def test_invalid_customer_boundaries(
    transport: TestClient,
    payload: dict[str, str],
    field: str,
) -> None:
    response = transport.post(
        "/customers",
        json=payload,
        headers={"Authorization": "Bearer admin-token"},
    )
    assert_error(response, status=400, code="VALIDATION_ERROR", field=field)
