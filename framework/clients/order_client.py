"""Order workflow client."""

import httpx

from framework.clients.base_client import BaseApiClient
from framework.models.order import CreateOrderRequest, OrderResponse


class OrderClient(BaseApiClient):
    def create_order(self, request: CreateOrderRequest) -> OrderResponse:
        response = self.post("/orders", json=request.model_dump(mode="json"))
        response.raise_for_status()
        return OrderResponse.model_validate(response.json())

    def get_order(self, order_id: str) -> OrderResponse:
        response = self.get(f"/orders/{order_id}")
        response.raise_for_status()
        return OrderResponse.model_validate(response.json())

    def confirm_order(
        self,
        order_id: str,
        *,
        scenario: str = "approved",
        idempotency_key: str | None = None,
    ) -> httpx.Response:
        headers = {"X-Payment-Scenario": scenario}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return self.post(f"/orders/{order_id}/confirm", headers=headers)
