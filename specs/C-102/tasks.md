# C-102: The synthetic world (tasks)

Paul's repo is at C-101 plus part of C-102. Tick a task only after its check passes; paste the
summary line after the arrow. Every command runs in `api/` unless it says otherwise.

Branch: `c-102`

- [ ] **T0. Inventory.** Compare the repo with T1 to T6: for each task, say whether its files
  exist and whether its check passes. Tick the done ones with the evidence, and wait for Paul to
  confirm before T1. Check: `git status`, `git log --oneline -5`, `ls ../data api/app`... ->
- [ ] **T1. The world.** Paul copies `data/world.json` from the starter zip (an agent never
  writes it). Check (repo root): the count line in spec criterion 1 ->
- [ ] **T2. Tests first.** Change `tests/conftest.py` (`TEST_DATABASE_URL`, `db_url`,
  `world_db`) and add `tests/test_world.py` (two tests). Check: `uv run pytest -q` stops at
  collection with `ModuleNotFoundError: No module named 'app.load_world'` (conftest.py imports
  the loader at the top, so no test runs, the C-101 tests included, until T5) ->
- [ ] **T3. The schema.** `app/schema.sql`: extensions, then cardmembers and cards; agents,
  enablements and merchants; intents and transactions (and the index); cart_lines and returns.
  Check: read it against spec criterion 3, one table at a time, with Paul ->
- [ ] **T4. The pool and the schema runner.** `app/db.py`. Check: `uv run pyright` clean;
  `uv run python -c "import app.db"` runs with Postgres stopped ->
- [ ] **T5. The loader.** `app/load_world.py`: `TABLES`, `upsert_sql`, `prepare`,
  `read_world`, `load`, `main`. Check: `uv run pytest -q` -> `4 passed` ->
- [ ] **T6. Run it like Paul will.** `uv run python -m app.load_world` twice (same counts), then
  the two bad inserts from the guide in psql (both refused; Paul runs them, `docker compose exec`
  asks first). Check: paste both count tables and both `ERROR:` lines ->
- [ ] **T7. Verify and review.** `/verify`, then the `reviewer` subagent with "C-102".
  Check: verdict approve, critical findings fixed ->
- [ ] **T8. Commit and pull request.** Commit as `C-102: the synthetic world: schema.sql and an
  idempotent loader`. Paul pushes (`git push -u origin c-102`); open the PR with
  `gh pr create --fill` and the body from the template; the Claude review workflow comments,
  and each comment is answered; Paul merges on GitHub (`gh pr merge --squash --delete-branch`).
  Check: `git status` clean, the PR merged ->
