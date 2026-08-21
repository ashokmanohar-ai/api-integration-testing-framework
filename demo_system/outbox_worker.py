"""Publish committed outbox records to the Kafka-compatible Redpanda broker."""

from __future__ import annotations

import os
import signal
import time
from pathlib import Path

from sqlalchemy import select

from demo_system.database import Database, EventRecord
from framework.messaging.producer import KafkaEventProducer
from framework.utils.logger import configure_logging

RUNNING = True
TOPIC = "acme.order-events"


def stop(_signum: int, _frame: object) -> None:
    global RUNNING
    RUNNING = False


def dispatch_once(database: Database, producer: KafkaEventProducer) -> int:
    with database.session() as session:
        records = session.scalars(
            select(EventRecord)
            .where(EventRecord.processed.is_(False))
            .order_by(EventRecord.timestamp)
            .limit(100)
        ).all()
        for record in records:
            producer.publish(
                TOPIC,
                {
                    "event_id": record.event_id,
                    "aggregate_id": record.aggregate_id,
                    "event_type": record.event_type,
                    "correlation_id": record.correlation_id,
                    "timestamp": record.timestamp.isoformat(),
                    "sequence": record.sequence,
                    "payload": record.payload,
                },
            )
            record.processed = True
        return len(records)


def main() -> None:
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))
    database_url = os.environ["DATABASE_URL"]
    broker_url = os.environ["BROKER_URL"]
    database = Database(database_url)
    database.create()
    producer = KafkaEventProducer(broker_url)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    Path("/tmp/outbox-worker.ready").touch()
    while RUNNING:
        dispatch_once(database, producer)
        time.sleep(0.25)
    database.dispose()


if __name__ == "__main__":
    main()
