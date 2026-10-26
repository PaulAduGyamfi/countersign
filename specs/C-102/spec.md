# C-102: The synthetic world (spec)

Status: approved by Paul
Ticket: C-102, Day 2. Guide page: "The database schema and an idempotent loader
that fills Postgres with ten cardmembers, fifty transactions, their intents, carts and returns.
Run it twice: same world."

## Why

Countersign judges purchases, so it needs purchases to judge. Real card data is off limits, so
the project runs on a synthetic world: invented cardmembers, cards, shopping agents, merchants,
authenticated intents, and fifty transactions with carts and returns. Every golden scenario
later in the build lives in this one file, starting with Maya's shoes (`TXN-1001`: she asked for
black trail runners in size 10 under $120 and got White/Grey size 11 for 13999 cents).

This ticket gives that world a home in Postgres: tables whose rules the database enforces on
every write, and a loader that is safe to run any number of times. A bank loads reference data
the same way: a rerun after a failed batch must never duplicate rows.

## What ships

- `data/world.json`, copied from the starter zip (not written by an agent).
- `api/app/schema.sql`: the extensions and nine tables of the world.
- `api/app/db.py`: the schema as trusted bytes, `apply_schema()`, `make_pool()`.
- `api/app/load_world.py`: the loader, runnable as `uv run python -m app.load_world`.
- `api/tests/conftest.py` (changed) and `api/tests/test_world.py` (new).

## Acceptance criteria

1. **The world is present.** Check (repo root):
   `python3 -c "import json; w = json.load(open('data/world.json')); print({k: len(v) for k, v in w.items() if isinstance(v, list)})"`
   prints `{'cardmembers': 10, 'cards': 10, 'agents': 6, 'enablements': 12, 'merchants': 17,
   'intents': 32, 'transactions': 50, 'cart_lines': 46, 'returns': 19, 'claims': 36}`.
2. **The schema is repeatable.** `schema.sql` creates extensions `vector` and `pg_trgm` and the
   tables `cardmembers`, `cards`, `agents`, `enablements`, `merchants`, `intents`,
   `transactions`, `cart_lines`, `returns`, every statement `IF NOT EXISTS`. Columns match the
   keys in `world.json` exactly. Check: loading twice raises nothing (criterion 5).
3. **The database guards the data.** At least these rules live in the schema:
   - text primary keys; composite keys `enablements (card_id, agent_id)` and
     `cart_lines (transaction_id, line_no)`; `returns` keyed by `transaction_id`;
   - foreign keys from every `*_id` to its table (`transactions.merchant_id` is the merchant of
     record);
   - `CHECK`s: `cards.issued_by` in (`network`, `partner_bank`), `cards.kind` in (`credit`,
     `prepaid`), `merchants.kind` in (`direct`, `facilitator`), `returns.status` in
     (`initiated`, `received`, `refunded`), `transactions.amount_cents > 0`,
     `cart_lines.qty > 0`;
   - money as `int` columns named `*_cents`; `intents.max_amount_cents` nullable (NULL means no
     limit); times as `timestamptz`; `cart_lines.attributes` as `jsonb`; `merchants.aliases`
     as `text[]`;
   - an index on `transactions (card_id, posted_at)`.
   Check: in psql, a transaction with `amount_cents = -500` fails with
   `violates check constraint "transactions_amount_cents_check"`, and a card for `CM-999` fails
   with `violates foreign key constraint "cards_cardmember_id_fkey"`.
4. **One pool helper, no surprise connections.** `make_pool(url)` returns an
   `AsyncConnectionPool` (1 to 5 connections, rows as dicts) that does not connect until opened.
   Importing `app.db` never touches the network.
5. **The loader is idempotent and atomic.** `uv run python -m app.load_world` (in `api/`) upserts
   every table, parents before children, in one transaction, then prints
   `Loaded the world in N.Ns` and one count line per table. Run twice: the same counts both
   times. With `DATABASE_URL` unset it exits with a one-line message, not a traceback.
6. **Tests prove it.** In `api/`, with Postgres running, `uv run pytest -q` prints `4 passed`:
   the two C-101 tests plus `test_loading_twice_changes_nothing` and
   `test_mayas_shoes_are_in_the_database` (`TXN-1001`: descriptor
   `NORTHWIND RUNNING #0412 PORTLAND OR`, `13999` cents, "size 10" in the instruction, cart
   attributes `{"color": "White/Grey", "size": "11", "width": "D"}`). The test database fixture
   refuses any database whose name doesn't end in `_test` before it wipes anything; with
   Postgres down the two database tests skip with a hint.
7. **Clean and committed.** `uv run ruff format --check .`, `uv run ruff check .` and
   `uv run pyright` are clean in `api/`; the work is committed as
   `C-102: the synthetic world: schema.sql and an idempotent loader` (or small commits with that
   prefix).

## Rules that apply

- Money is integer cents (AGENTS.md: Domain rules). The CHECK on `amount_cents` is the
  database's copy of that rule.
- Safe to repeat and one transaction (AGENTS.md: Domain rules; `.claude/rules/sql-schema.md`).
- SQL built only from `sql.Identifier` and `sql.Placeholder` (AGENTS.md: Code style).
- Synthetic data only: `world.json` is never generated or edited by an agent.
- Test databases end in `_test` (`.claude/rules/tests.md`).

## Harness changes

- The whole harness arrives today (AGENTS.md, CLAUDE.md, `.claude/`, Cursor and Copilot files,
  the PR template, the Claude review workflow; see the guide page's harness section).
- `.pre-commit-config.yaml`: on every commit, by anyone or any tool: YAML, JSON and TOML
  parse, end-of-file and trailing whitespace, merge markers, large files, private keys,
  gitleaks on the staged diff, no commits on `main`, ruff check and ruff format for every
  Python project. pyright and the tests stay in `/verify` and CI (too slow for a commit).
  Every hook repo is pinned by commit SHA, and check-yaml's ruamel.yaml exactly.
- `Makefile`: `make hooks` (pre-commit 4.6.2 as a uv tool, the git hook, every environment).
  llmkit's dangling `uv run pre-commit install` line and its `pre-commit` dev dependency go.
- `settings.json`: `~/.cache/pre-commit` writable in the sandbox (the agent's commits run the
  hooks there); `pre-commit run *` allowed; the ways to skip a hook denied. `guard-bash.sh`
  blocks `--no-verify`/`-n` on commit, `core.hooksPath`, `SKIP=`, `PRE_COMMIT_ALLOW_NO_CONFIG`
  and `pre-commit uninstall`; `protect-files.sh` asks before edits to the config and the
  Makefile.

## Out of scope

- The `claims` key in `world.json` (36 claims): no table today. Claims arrive in C-104.
- Merchant name matching with `pg_trgm` (C-103). The extension is created today, nothing more.
- Opening the pool in the app's lifespan and any route that reads the database (C-104).
- Versioned migrations and the rest of the `Makefile` (C-203); the test CI (C-107), which also
  runs `pre-commit run --all-files`. The Claude review workflow is already on the repo.

## Open questions

1. Which parts of C-102 are already in Paul's repo? T0 in `tasks.md` inventories them; Paul
   confirms before work starts.
2. Is Paul's `countersign_test` database present? (`docker compose exec db psql -U countersign
   -c '\l'`.) If the volume predates `docker/initdb.sql`, it must be created once by hand.
