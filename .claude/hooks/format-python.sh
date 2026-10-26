#!/usr/bin/env bash
# PostToolUse hook for Edit|Write: after Claude changes a Python file in api/ or llmkit/, run
# that project's own ruff (the locked version, its pyproject's settings) to format the file
# and apply safe lint fixes. Whatever ruff can't fix goes back to Claude as context.
# It never blocks: the edit already happened, and an unused import mid-change is normal.
set -euo pipefail

input=$(cat)
file_path=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' <<<"$input")
[[ "$file_path" == *.py && -f "$file_path" ]] || exit 0

project="${CLAUDE_PROJECT_DIR:-$PWD}"
rel="${file_path#"$project"/}"
case "$rel" in
  api/*) pkg="$project/api" ;;
  llmkit/*) pkg="$project/llmkit" ;;
  *) exit 0 ;;   # Python outside the two uv projects: nothing to run it with
esac

ruff="$pkg/.venv/bin/ruff"
if [[ ! -x "$ruff" ]]; then
  # No virtual environment yet. Running `uv sync` here would be slow and touch the network.
  echo "format-python: $ruff not found; run 'uv sync' in ${pkg#"$project"/}/" >&2
  exit 0
fi

cd "$pkg"   # ruff reads [tool.ruff] from this project's pyproject.toml
"$ruff" format --quiet -- "$file_path" || true
# Safe fixes only (ruff's default). F401 (unused import) is left to Claude: deleting an import
# that the next edit is about to use would undo its work.
"$ruff" check --fix --quiet --unfixable F401 -- "$file_path" >/dev/null 2>&1 || true
problems=$("$ruff" check --quiet --output-format concise -- "$file_path" 2>&1 || true)

if [[ -n "$problems" ]]; then
  python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "ruff still reports (fix before you call the task done; an unused import is fine mid-change):\n" + sys.argv[1]}}))' "$problems"
fi
exit 0
