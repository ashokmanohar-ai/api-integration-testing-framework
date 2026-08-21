"""Consumer-facing customer API client used by tests and Pact."""

from typing import Any

import httpx

from framework.clients.base_client import BaseApiClient
from framework.models.customer import CreateCustomerRequest, CustomerResponse


class CustomerClient(BaseApiClient):
    def create_customer(self, request: CreateCustomerRequest) -> CustomerResponse:
        response = self.post("/customers", json=request.model_dump())
        response.raise_for_status()
        return CustomerResponse.model_validate(response.json())

    def get_customer_response(self, customer_id: str) -> httpx.Response:
        return self.get(f"/customers/{customer_id}")

    def get_customer(self, customer_id: str) -> CustomerResponse:
        response = self.get_customer_response(customer_id)
        response.raise_for_status()
        return CustomerResponse.model_validate(response.json())

    def update_customer(self, customer_id: str, payload: dict[str, Any]) -> httpx.Response:
        return self.patch(f"/customers/{customer_id}", json=payload)

    def delete_customer(self, customer_id: str) -> httpx.Response:
        return self.delete(f"/customers/{customer_id}")
