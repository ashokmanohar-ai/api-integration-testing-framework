# Validation report

Date: 21 August 2026  
Runtime: Linux, Python 3.12.13

## Results

| Check | Result | Evidence |
|---|---|---|
| Editable dependency installation | PASS | `python -m pip install -e ".[dev,messaging,postgres]"` |
| Ruff lint | PASS | `ruff check .` |
| Ruff formatting | PASS | `ruff format --check .` |
| Strict MyPy | PASS | 54 source files, zero issues |
| Python compilation | PASS | `python -m compileall` |
| Test collection | PASS | 79 meaningful tests collected |
| Smoke | PASS | 3 passed |
| REST API | PASS | 33 passed |
| GraphQL | PASS | 7 passed |
| Pact contracts | PASS | 5 passed (consumer, provider and evolution) |
| Integration | PASS | 5 passed |
| Database | PASS | 4 passed |
| Messaging/outbox | PASS | 6 passed |
| Resilience | PASS | 10 passed |
| Full local suite | PASS | 76 passed, 3 opt-in Docker tests deselected |
| Parallel execution | PASS | 76 passed with `pytest -n auto` |
| JUnit and HTML reports | PASS | `reports/junit.xml`, `reports/report.html` generated |
| Quality gate | PASS | 76/76, 100.00%, release decision PASS |
| DEV environment validation | PASS | Local defaults accepted |
| QA environment validation | PASS | Explicit API/GraphQL/database overrides accepted |
| Missing QA API URL | PASS | Failed early with the expected clear configuration error |
| Compose/workflow YAML and JSON assets | PASS | 5 YAML files plus Pact/WireMock JSON parsed |
| Docker Compose runtime | PASS | GitHub CI built and started all services, passed health checks and tore down volumes |
| PostgreSQL + WireMock integration | PASS | Opt-in Docker API and service-virtualization checks passed |
| Redpanda event delivery | PASS | Docker suite consumed the real `OrderCreated` event from Redpanda |
| GitHub Actions CI | PASS | [CI run #2](https://github.com/ashokmanohar-ai/api-integration-testing-framework/actions/runs/32453285255) |
| Dedicated Pact workflow | PASS | [Contract run #2](https://github.com/ashokmanohar-ai/api-integration-testing-framework/actions/runs/32453285160) |

## Hosted Docker evidence

GitHub Actions built and started PostgreSQL, WireMock, Redpanda, the Acme API and the outbox worker;
waited for health; executed the opt-in Docker suite; consumed a real `OrderCreated` message from
Redpanda; uploaded evidence; and tore the environment down with volumes. Every executed step in the
quality job passed. Docker was not installed in the local authoring workspace, so the hosted run is
the authoritative container evidence.

## Privacy and warnings

Pact telemetry is disabled with `PACT_DO_NOT_TRACK=true`; contract execution remains local. The test
run reports a third-party Starlette warning that its current TestClient bridge will migrate from
HTTPX to `httpx2`; this does not affect results and is retained visibly rather than suppressed.

## Current decision

Local critical issues: **0**  
Local release gate: **PASS**  
Overall: **READY FOR USE AND REVIEW**
