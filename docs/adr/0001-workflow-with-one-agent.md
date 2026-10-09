# ADR 0001: A workflow with one agent, not an agent with tools for everything

Date: 2026-10-08
Status: accepted

## Context

Countersign decides claims under Agent Purchase Protection: did a registered AI agent's purchase
deviate from what the cardmember authenticated? Every decision can move money, may be denied,
and has to be explained to the cardmember, to a reviewer, and possibly to a regulator years later.

Most steps are known in advance: gather the charge, the intent, the cart and the return; check
eligibility; compare clause by clause; apply the terms; route for review; post a credit. A few
questions are open-ended: which merchant is really behind "PAYPAL *NWRUNNINGCO"? Is there a
second, related charge?

## Decision

Code owns the sequence (a workflow). The model fills three narrow, typed jobs: turn the
authenticated intent into checkable clauses, judge fuzzy matches such as "black" against
"Black/Anthracite", and draft the cardmember letter. One read-only investigator agent runs only
when deterministic triggers fire, with a step budget and a gate before every tool call.

## Consequences

- Most of the system is testable with no model calls, and every failure points at one step.
- Amounts, eligibility and outcomes are computed by code, so the model can never move money.
- The agent can only read, so its worst failure is a wasted lookup, not a wrong credit.
- We give up some flexibility: a new kind of claim means new code, not a new prompt. That is the
  right trade for a system that pays out money.
