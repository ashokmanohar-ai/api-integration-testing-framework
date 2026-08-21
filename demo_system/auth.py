"""Deterministic demo authentication and RBAC boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import Header

from demo_system.problems import ProblemError

Role = Literal["ADMIN", "CUSTOMER", "SUPPORT"]


@dataclass(frozen=True)
class Principal:
    subject: str
    role: Role


def parse_token(token: str) -> Principal:
    if token == "admin-token":
        return Principal(subject="admin", role="ADMIN")
    if token == "support-token":
        return Principal(subject="support", role="SUPPORT")
    if token.startswith("customer-token:") and token.split(":", 1)[1]:
        return Principal(subject=token.split(":", 1)[1], role="CUSTOMER")
    if token == "expired-token":
        raise ProblemError(401, "TOKEN_EXPIRED", "The bearer token has expired")
    raise ProblemError(401, "INVALID_TOKEN", "The bearer token is malformed or unknown")


def authenticated(authorization: str | None = Header(default=None)) -> Principal:
    if not authorization:
        raise ProblemError(401, "AUTH_REQUIRED", "A bearer token is required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ProblemError(401, "INVALID_TOKEN", "Use 'Authorization: Bearer <token>'")
    return parse_token(token)


def require_role(principal: Principal, *roles: Role) -> None:
    if principal.role not in roles:
        raise ProblemError(403, "FORBIDDEN", "The current role cannot perform this operation")


def require_owner_or_role(principal: Principal, owner_id: str, *roles: Role) -> None:
    if principal.subject != owner_id and principal.role not in roles:
        raise ProblemError(403, "FORBIDDEN", "Access to another customer's resource is denied")
