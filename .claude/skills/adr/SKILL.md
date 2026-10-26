---
name: adr
description: Write an architecture decision record in docs/adr/ in the repo's format (Date, Status, Context, Decision, Consequences). Use when a ticket makes a lasting choice, such as a new dependency, service, data rule, contract or trade-off, or when Paul asks to record a decision.
argument-hint: "[short title of the decision]"
allowed-tools: Bash(ls docs/adr)
---

# Decision record: $ARGUMENTS

Existing records:

!`ls docs/adr`

1. **Number.** Take the highest number above and add one, four digits (`0002`). File name:
   `docs/adr/NNNN-<title-in-kebab-case>.md`. Never renumber or rewrite an accepted record; a
   new decision that replaces one gets its own record and the old one's Status becomes
   `superseded by NNNN`.
2. **Read first.** `docs/adr/0001-workflow-with-one-agent.md` is the house style. Read the
   ticket's spec and the approved plan (in the chat or the pull request) for the facts.
3. **Write** with exactly these parts:

   ```markdown
   # ADR NNNN: <the decision as a sentence>

   Date: YYYY-MM-DD
   Status: proposed

   ## Context

   The problem in plain words, tied to a case from the synthetic world (Maya's shoes, TXN-1001).
   What forces the choice: the bank's constraint, the failure we want to avoid.

   ## Decision

   What we do, specific enough to check in the code. Name files, functions, numbers.

   ## Consequences

   - What gets easier, what gets harder, what we gave up, what we must now keep doing.
   ```

4. **Rules for the words.** Short sentences, active voice. Say "a bank" or "a card issuer",
   never what a named company does internally. Only facts you can point to; mark anything
   uncertain as an open question instead of stating it.
5. Leave Status `proposed`. Paul changes it to `accepted` when he merges.
6. Link the record from the plan's "Decision record" section (in the pull request
   description) and name it in the spec's "Rules that apply".
