# Event-driven testing

Asynchronous systems require assertions over eventual state, not arbitrary sleeps. The polling
utility has a deadline, interval, attempt count and last-error diagnostic.

Every event has a unique event ID, aggregate ID, type, correlation ID, timestamp, sequence and typed
payload. Tests validate publication intent in the transactional outbox, ordering (`OrderCreated`
before `OrderConfirmed`/`PaymentFailed`), schema rejection, duplicates and correlation.

The Redpanda adapter uses the Kafka protocol. An enterprise extension should add Schema Registry
compatibility, consumer-group lag, retry topics, poison-message quarantine/DLQ, idempotent consumer
state, replay and explicit ordering keys. Producer idempotence alone does not make a whole workflow
idempotent; business keys and consumer storage still matter.

