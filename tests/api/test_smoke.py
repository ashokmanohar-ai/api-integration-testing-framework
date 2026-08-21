"""Release-blocking smoke coverage."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.smoke
@pytest.mark.critical
def test_health_endpoint_is_up(transport: TestClient) -> None:
    response = transport.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "UP",
        "service": "acme-commerce-api",
        "version": "1.0.0",
    }


@pytest.mark.smoke
@pytest.mark.critical
def test_openapi_document_is_available(transport: TestClient) -> None:
    response = transport.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Acme Commerce API"


@pytest.mark.smoke
@pytest.mark.critical
def test_admin_can_obtain_a_token(transport: TestClient) -> None:
    response = transport.post("/auth/token", json={"username": "admin", "password": "admin-demo"})
    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"
    assert response.json()["token_type"] == "bearer"
