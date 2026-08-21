# Interview walkthrough

## Two-minute explanation

> This project demonstrates enterprise API and integration Quality Engineering across REST,
> GraphQL, contracts, databases, messaging, service virtualization, resilience, CI/CD and release
> quality gates. The strongest tests prove both successful and failed order journeys across API,
> payment, persistence and events, including correlation and duplicate-side-effect prevention.

## Five-minute route

1. `README.md`: architecture and two showcase workflows.
2. `framework/clients`: thin HTTPX boundary and typed domain clients.
3. `framework/models`: separate request/response/error/event contracts.
4. `tests/contracts`: real Pact mock and provider replay.
5. `mocks/wiremock`: deterministic payment faults and recovery.
6. `tests/integration`: API + DB + dependency + events.
7. `docker-compose.yml`: PostgreSQL, WireMock, Redpanda and health checks.
8. `.github/workflows` and `framework/quality`: evidence to release decision.

## Questions to prepare

- **Why HTTPX?** Modern sync/async transport, pooling and explicit timeouts without hiding HTTP.
- **Why Pydantic?** Executable types, enums, nullability and actionable schema failures.
- **API vs integration test?** API validates one public boundary; integration proves connected state.
- **Contract vs integration test?** Contract detects interface drift quickly; integration proves wiring.
- **Why Pact?** Consumer-owned expectations and provider replay without a huge E2E dependency graph.
- **Why WireMock?** Deterministic external faults, timeouts and recovery; never a replacement for all real integration.
- **How avoid brittleness?** Stable business assertions, factories, typed models and no execution order.
- **Authentication?** Token provider abstraction, environment secrets and sanitised logs.
- **Asynchronous systems?** Correlation, typed events, bounded polling, unique IDs and eventual state.
- **Database state?** Repositories for only business-critical persistence and cardinality.
- **Data collisions?** UUID-derived factories, per-test DB and namespaced idempotency/group keys.
- **100 microservices?** Domain packages, ownership, shared standards—not one giant universal client.
- **Kubernetes?** Ephemeral namespace per run, probes, sealed secrets and guaranteed teardown.
- **Azure DevOps?** Equivalent pipeline YAML, secure variables, JUnit publishing and environment gates.
- **Kafka/Redpanda?** Real adapter, schema registry, keyed order, consumer groups, DLQ and lag checks.
- **Retries?** Control dependency outcomes and assert attempts, final state and no duplicate side effects.
- **Idempotency?** Repeat a business key and prove one payment/event; reject cross-order reuse.
- **Quality gates?** Convert evidence and criticality into a deterministic promotion decision.
- **Distributed tracing?** Propagate trace/correlation headers and link logs, spans, DB and events.
- **AI triage?** Summarise sanitised evidence and rank causes; deterministic tests remain the authority.

