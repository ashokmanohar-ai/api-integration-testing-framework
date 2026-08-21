"""Payment dependency boundary with deterministic fault simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

import httpx

PaymentStatus = Literal["APPROVED", "DECLINED", "RETRYABLE", "TIMEOUT", "INVALID"]


@dataclass(frozen=True)
class PaymentDecision:
    status: PaymentStatus
    provider_reference: str | None = None


class PaymentGateway(Protocol):
    def authorise(
        self,
        *,
        order_id: str,
        amount: float,
        correlation_id: str,
        scenario: str,
    ) -> PaymentDecision: ...


class DeterministicPaymentGateway:
    """Stateful local adapter that models the WireMock scenarios exactly."""

    def __init__(self) -> None:
        self.attempts: dict[tuple[str, str], int] = {}

    def authorise(
        self,
        *,
        order_id: str,
        amount: float,
        correlation_id: str,
        scenario: str,
    ) -> PaymentDecision:
        key = (order_id, scenario)
        attempt = self.attempts.get(key, 0) + 1
        self.attempts[key] = attempt
        if scenario == "approved":
            return PaymentDecision("APPROVED", f"pay-{order_id}")
        if scenario == "declined":
            return PaymentDecision("DECLINED")
        if scenario == "transient":
            return PaymentDecision(
                "APPROVED" if attempt >= 3 else "RETRYABLE",
                f"pay-{order_id}" if attempt >= 3 else None,
            )
        if scenario == "timeout":
            return PaymentDecision("TIMEOUT")
        if scenario in {"unavailable", "server-error"}:
            return PaymentDecision("RETRYABLE")
        return PaymentDecision("INVALID")


class HttpPaymentGateway:
    """Real HTTP adapter used by Docker Compose against WireMock."""

    def __init__(self, base_url: str, timeout: float = 1.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def authorise(
        self,
        *,
        order_id: str,
        amount: float,
        correlation_id: str,
        scenario: str,
    ) -> PaymentDecision:
        try:
            response = httpx.post(
                f"{self.base_url}/payments/authorise",
                json={"order_id": order_id, "amount": amount},
                headers={
                    "X-Correlation-ID": correlation_id,
                    "X-Payment-Scenario": scenario,
                },
                timeout=self.timeout,
            )
        except httpx.TimeoutException:
            return PaymentDecision("TIMEOUT")
        if response.status_code == 200:
            try:
                payload = response.json()
                return PaymentDecision(
                    "APPROVED" if payload["status"] == "APPROVED" else "DECLINED",
                    payload.get("provider_reference"),
                )
            except (ValueError, KeyError, TypeError):
                return PaymentDecision("INVALID")
        if response.status_code in {500, 502, 503, 504}:
            return PaymentDecision("RETRYABLE")
        return PaymentDecision("INVALID")
