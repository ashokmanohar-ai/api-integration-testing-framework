"""Product client."""

import httpx

from framework.clients.base_client import BaseApiClient
from framework.models.product import CreateProductRequest, ProductResponse


class ProductClient(BaseApiClient):
    def create_product(self, request: CreateProductRequest) -> ProductResponse:
        response = self.post("/products", json=request.model_dump())
        response.raise_for_status()
        return ProductResponse.model_validate(response.json())

    def get_product(self, product_id: str) -> ProductResponse:
        response = self.get(f"/products/{product_id}")
        response.raise_for_status()
        return ProductResponse.model_validate(response.json())

    def list_products(self, **params: object) -> httpx.Response:
        return self.get("/products", params=params)
