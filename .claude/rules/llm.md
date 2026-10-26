---
paths:
  - "api/prompts/**"
  - "api/app/prompts.py"
  - "llmsvc/**"
  - "proto/**"
  - "contracts/**"
---

# Prompts, llmsvc and contracts: arrive in C-202 and C-205

None of these exist at C-102. Prompts arrive in C-202, llmsvc, `proto/` and `contracts/` in
C-205. If you are about to create one, stop and ask Paul: it is outside the current ticket.

When they land, replace this file with real rules: versioned
prompt files that are never edited in place, structured outputs checked again on arrival,
personal data masked before anything leaves, no test calling a real model, the provider key
only in llmsvc, additive proto changes checked by `buf breaking`, and generated stubs written
only by `make proto`.
