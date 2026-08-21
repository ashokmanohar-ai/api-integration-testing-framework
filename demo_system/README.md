# Acme Commerce demo system

This deliberately small FastAPI application is a stable test target, not the portfolio's primary
product. Logical identity, customer, product, order, payment and notification concerns share one
deployable process to keep local startup fast. Their API, persistence and dependency boundaries
remain separate so the tests still demonstrate distributed-system risks.

The Docker profile runs the API with PostgreSQL, WireMock and Redpanda. The default Pytest profile
uses an isolated SQLite database and the deterministic payment adapter; both adapters implement the
same scenarios and business contract.

Local credentials (`admin-demo`, `support-demo`) and tokens are non-secret demo values. Never reuse
this deterministic identity implementation outside a test target.

