---
paths:
  - "api/app/**/*.py"
---

# The claims API (`api/app/`)

- `main.py` is read top to bottom: `create_app(settings=None)` builds everything. Tests pass
  their own `Settings`; uvicorn uses the module-level `app`. Add routes inside `create_app`.
- Startup work goes in the `lifespan` (llmkit `configure()` first). Importing a module must
  never touch the network or the database: pools are made with `open=False` and opened in the
  lifespan.
- The request-ID middleware sets `request_id` for every log line and echoes `X-Request-ID`.
  Keep it the outermost behavior; don't add a second ID.
- Errors: raise `ApiError(status, code, message)` with a `snake_case` code. Unknown failures
  fall through to `internal_error` with a generic message; never return a stack trace or SQL.
- Settings: add a typed field to `Settings` (with a comment naming the env var) and a
  placeholder line to `.env.example`. `get_settings()` is the only reader.
- Scripts are modules run with `uv run python -m app.<name>` and end with
  `if __name__ == "__main__": main()`. A missing setting exits with a one-line message
  (`raise SystemExit(...)`), not a traceback.
- Money fields end in `_cents` and are `int`. Times are `timestamptz` / aware `datetime` in UTC.
- Keep functions short. A docstring says what the function promises; comments say why.
