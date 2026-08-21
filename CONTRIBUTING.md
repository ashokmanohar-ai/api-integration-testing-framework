# Contributing

## Workflow

1. Branch from `main` using `feature/<short-name>`, `fix/<short-name>` or `test/<short-name>`.
2. Keep commits focused and use an imperative subject.
3. Add or update tests and documentation with behaviour changes.
4. Run `ruff check .`, `ruff format --check .`, `mypy .` and `pytest -n auto`.
5. Open a pull request with risk, evidence, contract impact and rollback notes.

## Test conventions

- Name tests as observable behaviour: `test_<condition>_<expected_outcome>`.
- Use registered markers and keep release-critical coverage intentionally small.
- Generate unique data through factories; do not depend on IDs or execution order.
- Keep a workflow inside one test/fixture rather than chaining tests.
- Assert business state, error code and correlation—not status alone.
- Use bounded polling for asynchronous behaviour; arbitrary sleeps are rejected.

## Contract changes

Update consumer tests first, regenerate/review the Pact, verify the provider and document whether the
change is additive or breaking. A changed Pact file is production code and requires consumer and
provider review.

## Pull-request evidence

Attach JUnit/HTML links, commands executed, environment, test count, quality-gate decision and any
unexecuted checks. Do not claim an integration passed when its dependency was unavailable.

