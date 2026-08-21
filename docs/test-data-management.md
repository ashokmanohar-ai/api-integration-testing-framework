# Test-data management

- Factories generate UUID-derived emails and SKUs and accept explicit overrides.
- A test owns its customer, product, order and idempotency keys.
- No globally shared IDs or test-order dependencies are allowed.
- DEV/QA/UAT endpoints are configuration; test records are generated at runtime.
- Production PII must never be copied into source, contracts, logs or reports.
- Cleanup belongs in fixture/context teardown and runs after failure.
- Parallel tests require unique identifiers and isolated DB/mock/broker state.

For regulated environments, add synthetic-data approval, retention rules, environment tagging and a
janitor that deletes only records carrying a verified test-run identifier.

