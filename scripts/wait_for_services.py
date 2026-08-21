"""Wait for Docker dependencies with bounded polling and useful diagnostics."""

from __future__ import annotations

import socket
import sys

import httpx

from framework.utils.polling import PollTimeoutError, await_until


def http_up(url: str) -> bool:
    try:
        return httpx.get(url, timeout=1).status_code < 500
    except httpx.HTTPError:
        return False


def port_up(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def main() -> None:
    checks = {
        "Acme API": lambda: http_up("http://localhost:8000/health"),
        "WireMock": lambda: http_up("http://localhost:8080/__admin/health"),
        "PostgreSQL": lambda: port_up("localhost", 5432),
        "Redpanda": lambda: port_up("localhost", 19092),
    }
    try:
        for name, check in checks.items():
            await_until(check, timeout=90, poll_interval=1, description=name)
            print(f"PASS {name}")
    except PollTimeoutError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
