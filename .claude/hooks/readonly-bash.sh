#!/usr/bin/env bash
# PreToolUse hook used only by the reviewer subagents (their frontmatter registers it).
# A reviewer may look and run the checks, never change anything: each command must start with
# one of the allowed prefixes below, optionally after one `cd <folder> &&`, and contain no
# other shell operators, redirects or substitutions.
set -euo pipefail

input=$(cat)
cmd=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' <<<"$input")
[[ -z "$cmd" ]] && exit 0

deny() {
  echo "Blocked by .claude/hooks/readonly-bash.sh: reviewers are read-only. $1" >&2
  exit 2
}

rest="$cmd"
# One leading `cd <folder> &&` is fine (`cd api && uv run pytest -q`).
if [[ "$rest" =~ ^cd[[:space:]]+([A-Za-z0-9_./-]+)[[:space:]]*\&\&[[:space:]]*(.*)$ ]]; then
  rest="${BASH_REMATCH[2]}"
fi

# Anything that chains, redirects or substitutes could hide a write.
# shellcheck disable=SC2016 # the single-quoted '$(' is the literal text we look for
case "$rest" in
  *';'* | *'&'* | *'|'* | *'>'* | *'<'* | *'`'* | *'$('* | *$'\n'*)
    deny "Run one plain command at a time, without ; & | > < or \$( )." ;;
esac

allowed=(
  "git diff" "git log" "git show" "git status" "git blame" "git ls-files" "git merge-base"
  "git rev-parse" "git branch --show-current" "git grep"
  "uv run pytest" "uv run --directory api pytest" "uv run --directory llmkit pytest"
  "uv run pyright" "uv run ruff check" "uv run ruff format --check"
  "uv run ruff format --diff" "ls" "wc"
  "gh pr view" # the plan and tasks live in the pull request's description, not the repo
)
for prefix in "${allowed[@]}"; do
  if [[ "$rest" == "$prefix" || "$rest" == "$prefix "* ]]; then
    # These flags would write files: ruff's fixes, git's --output=<file>.
    [[ "$rest" == *"--fix"* ]] && deny "ruff check --fix edits files."
    [[ "$rest" == *"--output"* && "$rest" != *"--output-format"* ]] && deny "--output writes a file."
    exit 0
  fi
done

deny "'$rest' is not on the reviewer's list (git diff/log/show/status, uv run pytest/pyright/ruff check, gh pr view)."
