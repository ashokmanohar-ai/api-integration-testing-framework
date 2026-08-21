# Service virtualization

WireMock represents a payment provider when the real dependency is unavailable, costly, unsafe or
unable to produce a required edge condition. Mappings provide deterministic approval, decline,
timeout, malformed response, 500, 503 and stateful recovery.

Mocks are appropriate for consumer behaviour and controlled failure simulation. They become
dangerous when their contract is guessed, drifts from production or is treated as proof that real
authentication/network/TLS integration works. Review mappings against provider contracts and retain
at least one real integration stage.

Reset stateful WireMock scenarios between tests. Do not run the same shared scenario in parallel
without a per-test namespace or isolated instance.

