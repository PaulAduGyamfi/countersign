---
paths:
  - "api/app/kafka.py"
  - "api/app/relay.py"
  - "api/app/worker.py"
  - "deploy/**/kafka*.yaml"
---

# Kafka, the outbox and the worker: arrive in C-211

None of these exist at C-102. If you are about to create one, stop: events arrive in C-211.
Ask Paul first.

When C-211 lands, replace this file with real rules: the claim and
its event written in one transaction through the outbox, every handler idempotent and keyed by
claim id, failures parked on a dead-letter topic, CloudEvents headers, and no topic created
from application code.
