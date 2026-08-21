# Integration testing

| Test type | Boundary | Project example |
|---|---|---|
| Unit | One function/class | retry and quality-gate decisions |
| Component | One deployable with controlled edges | FastAPI + isolated SQLite/payment adapter |
| API | Public HTTP contract | customer, product, order and GraphQL suites |
| Contract | Consumer assumption vs provider | Pact mock and provider replay |
| Integration | Multiple technical boundaries | order + DB + payment + outbox |
| E2E | Critical business journey | confirmed order and terminal payment failure |

An API test can validate an endpoint while treating downstream state as opaque. An integration test
crosses a boundary and inspects the resulting database/event/dependency behaviour. Contract tests are
faster and more targeted than E2E but cannot prove deployment configuration, network policy or data
consistency.

The showcase success and failure workflows are deliberately few and deep. Each owns its data and
executes all steps inside one test, preserving diagnostic context without test-order coupling.

