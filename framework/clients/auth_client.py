"""Authentication client."""

from framework.clients.base_client import BaseApiClient


class AuthClient(BaseApiClient):
    def token(self, username: str, password: str) -> str:
        response = self.post("/auth/token", json={"username": username, "password": password})
        response.raise_for_status()
        return str(response.json()["access_token"])
