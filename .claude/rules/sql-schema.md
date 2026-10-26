---
paths:
  - "api/app/schema.sql"
  - "api/app/db.py"
  - "api/app/load_world.py"
  - "**/*.sql"
---

# Schema and SQL

Until C-203, `api/app/schema.sql` is the whole schema and runs on every start and every load.
Versioned migrations (Alembic) replace it in C-203; don't add a migration tool before then.

- Every statement is repeatable: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`,
  `CREATE EXTENSION IF NOT EXISTS`. Running the file twice must change nothing.
- `IF NOT EXISTS` never changes a table that already exists. To change a column on Paul's
  database you need a plan step that says how (until C-203: rebuild the dev database). Stop and
  ask before altering an existing table.
- The database enforces the rules: `NOT NULL` unless absence means something (then say what in a
  comment, like `max_amount_cents` NULL = no limit), `CHECK` for allowed values and positive
  amounts, `REFERENCES` for every id that points at another table.
- Money columns are `int` (or `bigint`) named `*_cents`. Never `numeric`, `real` or `float`.
- Times are `timestamptz`. Flexible per-product attributes go in `jsonb`; everything the rules
  read is a real column.
- Ids are `text` primary keys from the world (`CM-001`, `TXN-1001`).
- In Python: trusted SQL is a literal or bytes from our own file; names via `sql.Identifier`,
  values via `sql.Placeholder` or `%(name)s` parameters. Never format values into SQL.
- The loader upserts parents before children (dict order in `TABLES`) inside one transaction.
- Tables, columns and constraints must match the keys in `data/world.json`. If they disagree,
  the world wins: stop and ask rather than editing the world.
