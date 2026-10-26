---
name: verify
description: Run Countersign's checks (tests, ruff format and lint, pyright, and the world loader twice) in each project the current change touches, and report the summary lines. Use before saying a task is done and before every commit.
allowed-tools: Bash(uv sync *) Bash(uv run --directory api ruff *) Bash(uv run --directory api pyright *) Bash(uv run --directory api pytest *) Bash(uv run --directory llmkit ruff *) Bash(uv run --directory llmkit pyright *) Bash(uv run --directory llmkit pytest *) Bash(uv run --directory api python -m app.load_world) Bash(docker compose ps *) Bash(git status *) Bash(git diff *)
---

# Verify

Changed files:

!`git status --short`

1. Decide which projects changed: anything under `api/` means **api**, under `llmkit/` means
   **llmkit and api** (the API installs llmkit). Docs or specs alone: say so and stop.
2. For **api**, first check Postgres: `docker compose ps db` must show it up. If it is down,
   say so and ask Paul to run `docker compose up -d db`; database tests would only skip.
3. For each project (`api` or `llmkit` below as `<p>`), run these from the repo root, one
   command per call, in this order, and stop at the first failure. Each is one plain command
   on purpose: `uv run --directory <p> pytest` is on the sandbox's exclusion list, so the
   database tests reach Postgres; a `cd <p> &&` in front would keep it sandboxed and they skip.

   ```bash
   uv run --directory <p> ruff format --check .
   uv run --directory <p> ruff check .
   uv run --directory <p> pyright
   uv run --directory <p> pytest -q
   ```

4. If the change touched `schema.sql`, `db.py`, `load_world.py` or `data/`, also run
   `uv run --directory api python -m app.load_world` twice and compare the counts.
5. Report one line per check with the tool's own summary, copied, not paraphrased:

   ```text
   api     ruff format: 10 files already formatted
   api     ruff check:  All checks passed!
   api     pyright:     0 errors, 0 warnings, 0 informations
   api     pytest:      4 passed in 1.82s
   api     loader x2:   same counts (transactions 50, cart_lines 46)
   ```

6. Anything failing or skipped: show the first error and stop. Don't fix it inside this skill
   and don't call the work done.
