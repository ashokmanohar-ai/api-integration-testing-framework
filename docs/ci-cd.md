# CI/CD

Pull requests run formatting, lint, strict typing, contract/provider verification, smoke/critical
coverage, the full isolated suite, JUnit/HTML generation and the quality gate. Nightly runs add
parallel regression and the Docker integration profile. Reports and Compose logs upload on failure.

Secrets are never in YAML. Use GitHub Secrets/Environments, Jenkins credentials binding or Azure Key
Vault variable groups. Least-privilege workflow permissions are `contents: read`.

Pact Broker adoption adds publish/verify/`can-i-deploy` between build and deployment. Kubernetes can
replace Compose with an ephemeral namespace per run, readiness probes, generated test IDs and a
guaranteed namespace teardown stage.

Jenkins and Azure examples live under `ci/`. They are intentionally straightforward translations,
not claims that every enterprise agent has Docker permissions.

