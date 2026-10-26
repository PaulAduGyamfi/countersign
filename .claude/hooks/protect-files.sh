#!/usr/bin/env bash
# PreToolUse hook for Edit|Write: guards the files an agent must never change, and asks Paul
# before it changes the harness itself or starts a folder from a later ticket.
#   exit 2 + stderr  -> the edit is blocked and Claude reads the reason
#   JSON "ask"       -> Paul gets a permission prompt with the reason (even in auto mode)
#   exit 0, no output -> no opinion; the normal permission rules apply
set -euo pipefail

input=$(cat)
# python3 is on every machine this repo runs on (uv needs it), so no jq dependency.
file_path=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' <<<"$input")
[[ -z "$file_path" ]] && exit 0

project="${CLAUDE_PROJECT_DIR:-$PWD}"
file_path="${file_path//\\//}"   # Windows separators, so the patterns below still match
rel="${file_path#"$project"/}"   # path inside the repo (unchanged if outside it)
name="${file_path##*/}"

block() {
  echo "Blocked by .claude/hooks/protect-files.sh: $1" >&2
  exit 2
}

ask() {
  python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": sys.argv[1]}}))' "$1"
  exit 0
}

# 1. Secrets. .env.example is the committed template and stays editable.
case "$name" in
  .env.example) ;;
  .env | .env.*) block "$rel holds secrets. Add new settings to .env.example with a placeholder; Paul edits .env himself." ;;
  *.pem | *.key | id_rsa | id_ed25519) block "$rel looks like a private key. Keys never live in the repo." ;;
esac

# 2. Files that only a tool or the starter zip may write.
case "$name" in
  uv.lock | package-lock.json) block "$rel is generated. Change dependencies with uv add / npm install, after Paul agrees." ;;
esac
case "$rel" in
  data/world.json) block "data/world.json is the synthetic world from the starter zip. It is never written by an agent." ;;
  .git/*) block "$rel is git's own state." ;;
esac

# 3. The harness itself: allowed, but only with me watching.
case "$rel" in
  .claude/settings.json | .claude/settings.local.json | .claude/hooks/* | .claude/agents/* | .claude/skills/*)
    # Skills too: a skill's allowed-tools line grants permissions while it runs.
    ask "This edit changes the agent harness ($rel). Approve only if you asked for it." ;;
  .github/workflows/*)
    ask "This edit changes a workflow ($rel), which runs on GitHub with its secrets. Approve only if the plan says so." ;;
  .pre-commit-config.yaml | Makefile)
    # The commit checks, and what `make hooks` installs: dropping a hook here loosens every commit.
    ask "This edit changes the commit checks ($rel). Approve only if you asked for it." ;;
esac

# 4. A new top-level folder or file means a new area, which arrives with its own ticket.
if [[ "$rel" != "$file_path" ]]; then
  top="${rel%%/*}"
  if [[ ! -e "$project/$top" ]]; then
    ask "This creates '$top' at the repo root. New areas arrive with their ticket (AGENTS.md: Layout). Approve only if the plan says so."
  fi
fi

exit 0
