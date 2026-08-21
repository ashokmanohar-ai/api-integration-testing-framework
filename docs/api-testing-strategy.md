# API testing strategy

API tests validate business behaviour earlier and more precisely than UI-only coverage. The scope is
REST and GraphQL boundaries, typed schemas, authentication, authorization, error contracts,
pagination/filtering, idempotency and selected latency thresholds.

Positive tests prove state transitions and returned data. Negative and boundary cases use
parameterization for required fields, formats, enums, ranges, empty collections and maximum page
sizes. Error assertions require status, stable code, optional field, correlation and timestamp.

Pydantic validates types, required fields, enums, nesting and nullability. Pact expresses what a
consumer actually needs and provider verification detects drift. Integration tests then prove real
wiring and state; mocks and contracts do not replace them.

Functional auth/RBAC/ownership tests are included. Penetration testing, fuzzing and load/capacity
testing are separate disciplines and should use dedicated tools and authorisation.

