"""Authentication, role and IDOR-style authorization coverage."""

import pytest
from fastapi.testclient import TestClient

from framework.assertions.api_assertions import assert_error
from framework.clients.customer_client import CustomerClient
from framework.data.factories import customer_factory


@pytest.mark.api
@pytest.mark.security
@pytest.mark.negative
@pytest.mark.parametrize(
    ("authorization", "code"),
    [
        (None, "AUTH_REQUIRED"),
        ("Basic abc", "INVALID_TOKEN"),
        ("Bearer unknown", "INVALID_TOKEN"),
        ("Bearer expired-token", "TOKEN_EXPIRED"),
    ],
)
def test_invalid_authentication(
    transport: TestClient,
    authorization: str | None,
    code: str,
) -> None:
    headers = {"Authorization": authorization} if authorization else {}
    response = transport.get("/products", headers=headers)
    assert_error(response, status=401, code=code)


@pytest.mark.api
@pytest.mark.security
def test_customer_can_read_own_profile(
    transport: TestClient,
    customer_client: CustomerClient,
) -> None:
    customer = customer_client.create_customer(customer_factory())
    response = transport.get(
        f"/customers/{customer.id}",
        headers={"Authorization": f"Bearer customer-token:{customer.id}"},
    )
    assert response.status_code == 200


@pytest.mark.api
@pytest.mark.security
def test_customer_cannot_read_another_profile(
    transport: TestClient,
    customer_client: CustomerClient,
) -> None:
    first = customer_client.create_customer(customer_factory())
    second = customer_client.create_customer(customer_factory())
    response = transport.get(
        f"/customers/{second.id}",
        headers={"Authorization": f"Bearer customer-token:{first.id}"},
    )
    assert_error(response, status=403, code="FORBIDDEN")


@pytest.mark.api
@pytest.mark.security
def test_support_cannot_delete_customer(
    transport: TestClient,
    customer_client: CustomerClient,
) -> None:
    customer = customer_client.create_customer(customer_factory())
    response = transport.delete(
        f"/customers/{customer.id}",
        headers={"Authorization": "Bearer support-token"},
    )
    assert_error(response, status=403, code="FORBIDDEN")


@pytest.mark.api
@pytest.mark.security
def test_customer_cannot_escalate_own_status(
    transport: TestClient,
    customer_client: CustomerClient,
) -> None:
    customer = customer_client.create_customer(customer_factory())
    response = transport.patch(
        f"/customers/{customer.id}",
        json={"status": "INACTIVE"},
        headers={"Authorization": f"Bearer customer-token:{customer.id}"},
    )
    assert_error(response, status=403, code="FORBIDDEN")
