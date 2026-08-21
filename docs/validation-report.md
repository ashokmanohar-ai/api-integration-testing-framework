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
| Docker Compose runtime | PENDING CI | Docker is not installed in the local validation workspace |
| GitHub Actions execution | PENDING | Will execute after the feature branch/PR is published |

## Docker scope awaiting CI

The CI workflow is configured to build and start PostgreSQL, WireMock, Redpanda, the Acme API and
the outbox worker; wait for health; execute the opt-in Docker suite; consume a real `OrderCreated`
message from Redpanda; capture diagnostics; and tear the environment down with volumes. These items
are not marked PASS until a GitHub Actions runner executes them.

## Privacy and warnings

Pact telemetry is disabled with `PACT_DO_NOT_TRACK=true`; contract execution remains local. The test
run reports a third-party Starlette warning that its current TestClient bridge will migrate from
HTTPX to `httpx2`; this does not affect results and is retained visibly rather than suppressed.

## Current decision

Local critical issues: **0**  
Local release gate: **PASS**  
Overall: **READY FOR DRAFT PR; DOCKER/CI EVIDENCE PENDING**
