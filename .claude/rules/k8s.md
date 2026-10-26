---
paths:
  - "deploy/**"
  - "platform/**"
  - "api/migrations/**"
  - "Makefile"
---

# Kubernetes, migrations and the Makefile: arrive in C-203

None of these exist at C-102, except a `Makefile` with one target, `hooks` (Paul's). If you are
about to create `deploy/`, `platform/`, `api/migrations/` or another `make` target, stop: they
belong to C-203 (the paved road). Ask Paul first.

When C-203 lands, replace this file with real rules: Kustomize
layout, images pinned by tag, non-root pods with probes and resources, no secrets in manifests,
Alembic migrations with `--rev-id` numbers, never editing a migration that has been applied,
and the API never running DDL.
