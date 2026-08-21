"""Kafka-compatible producer used with Redpanda in Docker environments."""

from __future__ import annotations

import json
from typing import Any, Protocol


class ProducerTransport(Protocol):
    def send(self, topic: str, value: bytes, key: bytes | None = None) -> Any: ...

    def flush(self, timeout: float | None = None) -> Any: ...


class KafkaEventProducer:
    def __init__(self, broker_url: str, *, transport: ProducerTransport | None = None) -> None:
        if transport is None:
            from kafka import KafkaProducer

            transport = KafkaProducer(bootstrap_servers=broker_url)
        self._producer = transport

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        key = str(event.get("aggregate_id", "")).encode()
        self._producer.send(topic, value=json.dumps(event, default=str).encode(), key=key)
        self._producer.flush(timeout=5)
