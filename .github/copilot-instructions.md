# Countersign: instructions for GitHub Copilot

Countersign is an independent prototype on synthetic data, not affiliated with American Express.
The full rulebook is `AGENTS.md` at the repo root. The rules below are the ones that matter
most, copied here because a Copilot review doesn't follow links.

## Conventions

- Python 3.12 with uv. Run checks from `api/` or `llmkit/`: `uv run ruff format .`,
  `uv run ruff check .`, `uv run pyright`, `uv run pytest -q`. Copilot has no hooks here, so
  run the formatter yourself.
- Money is integer cents (`*_cents: int`). Never floats.
- Anything that can run twice leaves the same state: `IF NOT EXISTS`, upserts with
  `ON CONFLICT ... DO UPDATE`, one transaction per unit of work.
- SQL values go as parameters, names as `psycopg.sql.Identifier`. Never f-strings in SQL.
- Errors use `ApiError(status, code, message)` and the one `{"error": {...}}` shape.
- Settings come only from `app.settings.Settings`. Secrets live in `.env`, which is never read,
  printed or committed. New settings go in `.env.example` with placeholders.
- Data is synthetic. Emails use `example.com` or `countersign.example`.

## Code review

When Paul asks for a review ("Review selection" in the editor), you are the second vendor's
eye. The code was written by Claude Code and reviewed by Claude subagents and the Claude review
workflow, one model family, so look hardest where they would share a blind spot: an
acceptance criterion no test proves, a test that passes for the wrong reason, a rule from
AGENTS.md the diff quietly bends. Review against the ticket's `specs/<ticket>/spec.md` when the
pull request links one, and the plan in the pull request's description. Flag, in this order:

1. **Correctness:** an acceptance criterion in the spec that the code doesn't meet.
2. **Tests:** new behavior without a test that would fail without it; a test deleted, skipped
   or loosened; a test that uses the network, a real model or the dev database.
3. **Money and repeatability:** floats for amounts; a write that isn't safe to repeat; several
   writes outside one transaction.
4. **Security:** secrets or real personal data in code, tests or logs; SQL built from strings;
   `.env`, `.venv` or caches committed; error responses that leak SQL or stack traces.
5. **Scope:** files outside the plan, new dependencies without an exact lower bound and an
   updated `uv.lock`, folders that belong to a later ticket.

Don't comment on formatting or import order; ruff enforces those. Prefer one comment that names
the file, the line, the risk and the smallest fix over several general remarks.
