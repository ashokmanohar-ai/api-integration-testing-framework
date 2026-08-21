"""Pact provider verification replays a committed contract against the real FastAPI target."""

from __future__ import annotations

import socket
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest
import uvicorn
from pact import Verifier

from demo_system.app import create_app
from framework.utils.polling import await_until


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def provider_url(tmp_path: Path) -> Iterator[str]:
    port = free_port()
    app = create_app(database_url=f"sqlite:///{tmp_path / 'provider.db'}")
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", lifespan="on")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    await_until(lambda: server.started, timeout=10, description="Pact provider")
    yield f"http://localhost:{port}"
    server.should_exit = True
    thread.join(timeout=10)


@pytest.mark.contract
@pytest.mark.critical
def test_provider_satisfies_committed_pact(provider_url: str) -> None:
    verifier = (
        Verifier("AcmeCommerceApi").add_source("contracts/pacts").add_transport(url=provider_url)
    )
    verifier.verify()
