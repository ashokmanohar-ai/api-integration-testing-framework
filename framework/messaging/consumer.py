"""Bounded Kafka-compatible event consumer for integration checks."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any


def consume_events(
    broker_url: str,
    topic: str,
    *,
    group_id: str,
    timeout_ms: int = 5_000,
) -> Iterator[dict[str, Any]]:
    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=broker_url,
        group_id=group_id,
        auto_offset_reset="earliest",
        consumer_timeout_ms=timeout_ms,
        enable_auto_commit=False,
    )
    try:
        for message in consumer:
            yield json.loads(message.value)
    finally:
        consumer.close()
