# Troubleshooting

## Configuration fails

Run `python scripts/validate_environment.py`. QA/UAT require explicit `API_BASE_URL` and
`GRAPHQL_URL`; verify `TEST_ENV` and do not paste secrets into YAML.

## Docker service is unhealthy

Run `docker compose ps`, `docker compose logs api`, `docker compose logs wiremock`, then
`python scripts/wait_for_services.py`. Check that ports 5432, 8000, 8080 and 19092 are free. Recreate
with `docker compose down -v` only when deleting local test data is acceptable.

## Pact verification fails

Confirm the Pact provider name, request path/header and provider startup. A provider replay failure
is normally a real contract mismatch; do not regenerate the contract from provider output to hide it.

## Parallel-only failures

Search for shared IDs, module/session mutable fixtures, fixed idempotency keys, WireMock scenario
state or one broker consumer group. Namespace by test/run or isolate the suite.

## Useful diagnostics

The assertion layer prints method, endpoint, expected/actual status, correlation and a sanitised body.
Use the correlation value to join API logs, order state and outbox events.

