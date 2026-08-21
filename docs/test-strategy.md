# Test strategy

## Objective

Provide fast interface confidence and deep workflow evidence without relying on a large, brittle E2E
suite. Risk—not endpoint count—drives coverage.

## Layers

| Layer | Main risk | Evidence |
|---|---|---|
| Contract | Consumer/provider drift | Pact interaction and provider replay |
| API | Business and error behaviour | body, schema, headers, state and correlation |
| Integration | Incorrect wiring/state | API + DB + payment + event assertions |
| E2E | Critical journey failure | successful and failed order workflows |

Smoke and critical tests must pass 100%. Contract failures block release. A production regression
gate may allow a configurable non-critical pass rate, but this reference gate defaults to 100%.

Data is synthetic and unique. Tests establish and clean their own preconditions. Shared external
scenarios are reset or isolated from parallel execution. Evidence includes environment, duration,
error contract, correlation ID, JUnit and an HTML report.

