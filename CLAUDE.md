@AGENTS.md

## Claude Code

<!-- Claude-only notes. Shared rules belong in AGENTS.md, area rules in .claude/rules/. -->

- **Plan first.** Sessions start in plan mode and auto mode is switched off
  (`.claude/settings.json`), so I approve every edit while I learn. For a ticket, run
  `/ticket <id>`: it writes `specs/<id>/` and stops for my approval. Edit nothing until I
  approve the plan.
- **Verify before you say done.** Run `/verify` and paste its summary lines. If you did not run
  a check, say so. Never write "should pass".
- **Review in a fresh context.** Before proposing a commit or a pull request, delegate to the
  `reviewer` subagent with the spec path and the task. Also use `security-reviewer` when the diff
  touches SQL, settings, secrets, dependencies, `.claude/` or `.github/`. Fix what they mark
  critical; list the rest for me. Don't chase optional findings into extra code. Both share
  your model (`model: inherit`). The independent reviews come after: the Claude review
  workflow (`.github/workflows/claude-review.yml`) runs on GitHub on every pull request, seeing
  only the PR and the repo, and I run Copilot Free's "Review selection" in my editor for a
  second vendor's eye. Read the PR's comments with `gh pr view --comments` and answer each one,
  fixed or explained.
- **Hooks are guardrails.** A hook formats and lints each Python file you edit and reports what
  it could not fix. Another blocks edits to `.env`, `data/world.json` and lock files, and
  dangerous shell commands. When a hook blocks you, tell me what you were trying to do. Never
  work around it.
- **The sandbox.** Your Bash commands run in Claude Code's sandbox: no reads of `.env` or
  `~/.aws`, writes only inside the repo and the uv cache, network only to the package indexes.
  Commands that need Postgres or Docker are in `sandbox.excludedCommands` and run outside it,
  but only when the call is that one command: write `uv run --directory api pytest -q`, never
  `cd api && uv run pytest -q` (a `cd` keeps the call sandboxed, where Postgres is out of reach
  on Linux and the database tests skip). When the sandbox blocks a command, say so; don't look
  for another way round it. On Linux the sandbox needs `bubblewrap` and `socat` (Ubuntu 24.04+
  also an AppArmor profile for `bwrap`; `/sandbox` shows what is missing), and
  `failIfUnavailable` makes Claude Code refuse to start without it, so no command ever runs
  unsandboxed by accident.
- **Path rules** in `.claude/rules/` load when you touch matching files. If one says an area
  does not exist yet, stop and ask before creating it.
- **Context.** Use a subagent for wide searches. After two failed attempts at the same fix,
  stop, summarize what you tried, and ask.
- **Explain for me.** End each task with a short walkthrough of the diff: each new function,
  why each rule exists, and one question I should be able to answer about it.
