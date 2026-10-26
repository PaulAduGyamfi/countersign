# C-102: The synthetic world (plan)

Status: approved by Paul

## Approach

The world is data, so it is copied, never typed or generated. The schema is one SQL file of
`IF NOT EXISTS` statements that the loader runs first, so the loader works on an empty
database. The loader builds one upsert per table from a small map of key and other columns,
using psycopg's `sql` module so names are quoted and values travel separately from the SQL. All
nine tables load in one transaction, parents first. **The one idea:** `INSERT ... ON CONFLICT
(key) DO UPDATE SET col = EXCLUDED.col` turns a repeat into an overwrite with the same values,
which is what makes the loader safe to run again.

## Files

| File | New or changed | What goes in it |
|---|---|---|
| `data/world.json` | new (copied) | From `countersign-starter.zip`. Paul copies it. |
| `api/app/schema.sql` | new | Extensions, then the nine tables in parent-to-child order, the index. |
| `api/app/db.py` | new | `SCHEMA: bytes` (read once at import); `async def apply_schema(conn: psycopg.AsyncConnection) -> None`; `def make_pool(url: str) -> AsyncConnectionPool` (`min_size=1, max_size=5, open=False`, `row_factory=dict_row`). |
| `api/app/load_world.py` | new | `WORLD` path (`parents[2] / "data" / "world.json"`); `TABLES: dict[str, tuple[str, str]]` (key columns, other columns); `upsert_sql(table, keys, cols) -> sql.Composed`; `prepare(row) -> dict` (wraps `attributes` in `Jsonb`); `read_world(path=WORLD) -> dict`; `async def load(url, world=None) -> dict[str, int]` (one connection, one transaction, returns counts); `main()` (reads `DATABASE_URL`, prints counts). |
| `api/tests/conftest.py` | changed | `TEST_DATABASE_URL` from the environment, default `.../countersign_test`; session fixtures `db_url` (skip if Postgres is down; refuse names not ending `_test`; `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`) and `world_db` (loads once). The C-101 `client` fixture stays as it is. |
| `api/tests/test_world.py` | new | The two tests below. |

## Data and schema

The nine tables and their constraints are listed in the spec (criterion 3); column names are
the keys of `world.json`. No settings change: `DATABASE_URL` and `TEST_DATABASE_URL` are already
in `.env.example` from C-101.

## Tests first

Write these before the loader exists; they fail with an import error, then pass at T5.

- `test_loading_twice_changes_nothing` (`world_db`): two `load()` calls return equal counts,
  and the counts equal the lengths in the file for `transactions` and `cart_lines`.
- `test_mayas_shoes_are_in_the_database` (`world_db`): one join of `transactions`, `intents` and
  `cart_lines` for `TXN-1001` returns the four values in spec criterion 6. The `jsonb` column
  comes back as a dict.

## Dependencies

None. `psycopg[binary]` and `psycopg-pool` are already in `api/pyproject.toml` from C-101.

## Risks and how we'll know

- A foreign key fails during load because a child table loads first. Caught by the tests; the
  fix is the order of `TABLES`, never removing the constraint.
- `executemany` sends a dict for `attributes` and psycopg refuses it. Caught by the tests; the
  fix is `Jsonb(...)` in `prepare()`.
- The tests wipe the wrong database. Prevented by the `_test` check, which runs before the
  `DROP`; the reviewer confirms it is still first.
- Paul's Postgres volume has no `countersign_test`: `uv run pytest` shows `2 skipped` or a
  "does not exist" error. Fix once: `docker compose exec db createdb -U countersign
  countersign_test`.

## Decision record

None. Upserts and integer cents follow from ADR 0001 and AGENTS.md.

## Paul should be able to answer

1. How is the loader both safe to repeat and safe from SQL injection?
2. Why does Countersign store money as integer cents?
3. The loader crashes on table 7 of 9. What is in the database afterwards, and why?
4. Name two rules the schema enforces and the bug each one prevents.
