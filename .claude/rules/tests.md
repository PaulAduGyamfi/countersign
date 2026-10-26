---
paths:
  - "api/tests/**/*.py"
  - "llmkit/tests/**/*.py"
---

# Tests

- Fixtures live in `conftest.py`. Use the ones that exist before writing new ones:
  - `client`: the app through `httpx.ASGITransport`, no server, no database, admin key
    `test-key`.
  - `db_url`: a wiped test database. It refuses any database whose name doesn't end in `_test`.
    Never weaken that check.
  - `world_db`: `db_url` with the world loaded once per session.
- Database tests skip when Postgres is down. A skip is not a pass: report it.
- One promise per test, named as a sentence. Assert on exact values from the world (Maya's
  `TXN-1001` is `13999` cents), not on "truthy".
- To prove "safe to repeat", run the operation twice and compare.
- To prove a database rule, attempt the bad write and assert the specific error
  (`psycopg.errors.CheckViolation`, `ForeignKeyViolation`), inside a transaction you roll back.
- No real network, no real model, no `time.sleep`, no dependence on test order or the clock.
- Test data is synthetic. Use `example.com` emails and obviously fake keys (`test-key`).
- Never delete, skip (`pytest.skip`, `xfail`) or loosen a test to get green without Paul's
  written approval in the plan.
