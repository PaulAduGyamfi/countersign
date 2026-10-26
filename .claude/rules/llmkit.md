---
paths:
  - "llmkit/**/*.py"
---

# llmkit (Paul's library)

- llmkit is a library other projects install. It never imports from `app` or knows about
  Countersign's domain (claims, merchants, cents).
- Public names are exported in `src/llmkit/__init__.py` and listed in `__all__`. Changing or
  removing one is a breaking change: stop and ask.
- Pyright runs in **strict** mode here (`uv run pyright` in `llmkit/`). No `Any` leaks, no
  `# type: ignore` without a comment saying why.
- Settings use the `LLMKIT_` prefix and are documented in `llmkit/README.md` (update the table
  when you add one).
- Tests use `httpx.MockTransport`, never the network. `client.request()` returns the response
  and does not raise on error statuses; keep that contract.
- Run llmkit's own checks (`uv run pytest -q`, `ruff`, `pyright` in `llmkit/`) whenever you touch
  it, and the API's too, because the API installs llmkit as an editable path dependency.
