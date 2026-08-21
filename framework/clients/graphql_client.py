"""Small GraphQL-over-HTTP client that honours GraphQL error semantics."""

from pathlib import Path
from typing import Any, cast

import httpx

from framework.clients.base_client import BaseApiClient


class GraphQLClient(BaseApiClient):
    def execute(
        self,
        query: str,
        *,
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None,
    ) -> httpx.Response:
        payload: dict[str, Any] = {"query": query, "variables": variables or {}}
        if operation_name:
            payload["operationName"] = operation_name
        return self.post("/graphql", json=payload)

    def execute_file(self, path: Path, **kwargs: Any) -> httpx.Response:
        return self.execute(path.read_text(encoding="utf-8"), **kwargs)

    @staticmethod
    def assert_success(response: httpx.Response) -> dict[str, Any]:
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        if payload.get("errors"):
            raise AssertionError(f"GraphQL errors: {payload['errors']}")
        return cast(dict[str, Any], payload["data"])
