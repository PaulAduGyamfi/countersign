# C-102 has one target; the rest of the Makefile arrives with C-203.
PRE_COMMIT := pre-commit==4.6.2
# A tool install has no lock file, so its dependencies resolve as they were on this date: the
# 14-day cooldown (AGENTS.md), for every package it pulls in.
COOLDOWN := 2026-10-10

.PHONY: hooks
# Paul runs this once, outside Claude Code, and again after .pre-commit-config.yaml changes.
# 1. pre-commit itself, pinned, as a uv tool (its own environment, on your PATH).
# 2. The git hook (.git/hooks/pre-commit), plus every hook's environment built now: the agent's
#    sandbox can't reach GitHub, so it can only use environments that already exist.
hooks:
	uv tool install $(PRE_COMMIT) --exclude-newer $(COOLDOWN)
	"$$(uv tool dir --bin)/pre-commit" install --install-hooks
