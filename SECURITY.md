# Security policy

## Supported versions

The `main` branch and latest tagged release receive security fixes.

## Reporting

Do not open a public issue for an exploitable vulnerability. Use GitHub's private vulnerability
reporting for this repository and include the affected version, reproduction, impact and suggested
remediation. Do not include real customer data or credentials.

## Credential and data rules

- Never commit bearer tokens, client secrets, database passwords, API keys, private certificates or
  `.env` files.
- Inject CI values through GitHub Environments/Secrets, Jenkins credentials or Azure Key Vault.
- Treat local `admin-demo`, `support-demo` and deterministic tokens as public test values only.
- Generate synthetic test data. Do not copy production PII into fixtures, contracts or reports.
- Logging masks authorization, passwords, tokens, client secrets and email addresses recursively.
- Store generated reports as time-limited CI artifacts because failure bodies may contain business data.
- Pact telemetry is disabled in the test harness (`PACT_DO_NOT_TRACK=true`) so contract metadata stays local.

## Dependency and container security

Use Dependabot/Renovate plus `pip-audit` or OSV-Scanner for Python dependencies, and Trivy/Grype for
the built image. Pin actions to reviewed major versions (or commit SHAs in regulated environments),
review transitive upgrades and rebuild images regularly. The application container runs as a
non-root user.

## Scope

The security tests here are functional controls (auth, RBAC, ownership and input validation), not a
penetration test. Use an authorised DAST/SAST/secrets/container-scanning process for release evidence.
