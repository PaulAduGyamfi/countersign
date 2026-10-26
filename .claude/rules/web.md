---
paths:
  - "web/**"
---

# The console (`web/`): arrives in C-106

There is no `web/` folder at C-102. If you are about to create one, stop: it belongs to C-106
and is outside the current ticket. Ask Paul first.

When C-106 lands, replace this file with the console's real rules. Start from these:

- `cd web && npm ci`, then `npm run lint` (oxlint) and `npm run build`; from C-204 also
  `npm run typecheck`. Name the exact scripts that exist in `web/package.json`.
- The console only talks to the API. No secrets in frontend code or `vite.config`; anything in
  `web/` ships to every browser.
- Money arrives as integer cents and is formatted for display in one helper.
- One Idempotency-Key per claim form, made once, reused on every retry of that submit.
- Add packages with an exact version at least 14 days old (`npm install pkg@X.Y.Z`), and commit
  `package-lock.json`. Never edit the lock by hand.
