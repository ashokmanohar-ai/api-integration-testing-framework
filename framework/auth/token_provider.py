"""Token provider abstraction; secrets stay outside tests and logs."""

from dataclasses import dataclass
from typing import Protocol

from framework.clients.auth_client import AuthClient


class TokenProvider(Protocol):
    def get_token(self) -> str: ...


@dataclass(frozen=True)
class StaticTokenProvider:
    """Safe only for the local demo's documented non-secret tokens."""

    token: str

    def get_token(self) -> str:
        return self.token


@dataclass
class PasswordTokenProvider:
    client: AuthClient
    username: str
    password: str

    def get_token(self) -> str:
        return self.client.token(self.username, self.password)
