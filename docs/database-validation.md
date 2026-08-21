# Database validation

Database assertions complement API behaviour when persistence is a contractual risk. They verify
customer fields, order header/items, payment cardinality, inventory changes and failure rollback.

Tests query through small repositories/helpers, never scatter SQL across scenario bodies. Unique
factory values prevent collisions. Each local test gets its own SQLite database; Docker tests use a
recreated PostgreSQL volume and explicit cleanup.

Avoid asserting internal columns with no business relevance. Database checks increase coupling and
should focus on high-risk state transitions, audit/outbox records and duplicate prevention.

