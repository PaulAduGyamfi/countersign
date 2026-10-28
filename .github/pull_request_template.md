## What this does

<!-- One or two sentences in plain words. Link the spec: specs/C-NNN/spec.md -->

Ticket: C-NNN · Spec: `specs/C-NNN/spec.md`

## Plan

<!-- The approved plan, from specs/TEMPLATE/plan.md (files, functions, tests first, risks).
     It lives here, not in the repo; the reviewers judge the diff against it and the spec. -->

## Tasks

<!-- The task list from specs/TEMPLATE/tasks.md, each ticked with its check's summary line. -->

## How I verified it

<!-- Paste the summary lines, not "tests pass". -->

```text
api     ruff format / ruff check / pyright:
api     pytest:
llmkit  pytest:
other (loader twice, psql, curl):
```

## AI assistance

- **Agent and model:** <!-- e.g. Claude Code with Claude Opus 5.5; Cursor; Copilot. "None" is fine. -->
- **What the agent generated:** <!-- files or parts, e.g. "load_world.py and test_world.py from my plan" -->
- **What I wrote or changed myself:**
- **What I verified, and how:** <!-- read every line; ran the checks; tried the failure case; asked the reviewer subagent -->
- **Reviewer findings:** <!-- reviewer subagents, the Claude review on this PR, Copilot's Review selection: critical ones fixed, the rest listed or "none" -->

## Checklist

- [ ] I can explain every line in this diff without notes.
- [ ] Every new behavior has a test that fails without it; no test was deleted, skipped or loosened.
- [ ] Checks pass in every project I touched (output above), with Postgres running.
- [ ] Money is integer cents; anything that can run twice is safe to repeat.
- [ ] Synthetic data only; no secrets, keys or `.env` in the diff.
- [ ] Only files the plan names; no new dependency unless the plan agreed it (exact lower bound, lock updated).
- [ ] `AGENTS.md` and `.claude/rules/` updated if a command, folder or convention changed.
- [ ] Small enough to review: about 300 lines or fewer, lock files and data excluded.

## Not in this pull request

<!-- What you deliberately left for later, and why. -->
