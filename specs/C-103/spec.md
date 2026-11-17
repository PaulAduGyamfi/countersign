# C-103: Merchant names (spec)

Status: approved by Paul
Ticket: C-103, Day 3. Guide page: "A descriptor normalizer and a trigram resolver
that turn `SQ *COBALT COFFEE ROA` into Cobalt Coffee Roasters, with a confidence band, and say
\"I can't tell\" when the evidence is thin."

## Why

Maya's intent says "from Northwind Running"; a statement line says `PAYPAL *NWRUNNINGCO`. No
claim can be judged until we know who really sold the goods, and a descriptor is a smudged,
truncated, prefixed copy of the seller's name. Policy DOH-3.2 says it plainly: when a payment
facilitator (Square, PayPal) sits in the middle, find the real seller first, and if you can't,
escalate rather than guess. This ticket handles most charges with plain code and a Postgres
trigram index, and labels the hard ones honestly for the investigator (C-207).

## What ships

- `api/app/merchants.py`: `normalize()`, `band()`, `Candidate`, `Resolution`, `resolve_name()`,
  `resolve_seller()`, and a small CLI (`uv run python -m app.merchants "<descriptor>"`).
- `schema.sql`: table `merchant_names(merchant_id, name)` with a GIN `gin_trgm_ops` index.
- `load_world.refresh_merchant_names()` rebuilds it from the names and aliases of direct merchants.
- `db.py`: `Store(pool)` with `one()`, `all()`, `merchant()` and `similar_merchants()`.
- Tests for the normalizer, the bands and the resolver.

## Acceptance criteria

1. `normalize()` uppercases, strips one facilitator prefix (`SQ *`, `TST*`, `PAYPAL *`, `SP *`,
   `PY *`), turns `&` into `AND`, and removes phone numbers, `#store` numbers, `*ORDER` refs,
   `.COM`, runs of 4+ digits, other punctuation and a trailing US state code. Check: unit tests
   on the world's descriptors.
2. Bands are named constants `HIGH, MEDIUM = 0.6, 0.3`; `band()` is tested at and just
   below each. Check: `test_band_edges` (`at HIGH`, `just below HIGH`, `at MEDIUM`, ...).
3. `uv run python -m app.merchants "SQ *COBALT COFFEE ROA"` resolves to `M-CBC` with `high`.
4. `PAYPAL *NWRUNNINGCO` returns no merchant (`merchant_id` None), low confidence, and no
   candidates. A direct merchant of record resolves `high` by `merchant_of_record`. Check:
   `test_resolve_seller`, `test_a_thin_descriptor_lists_no_candidates`.
4a. A `medium` match names the seller (`merchant_id` and `name` set) and lists the candidates;
   only `low` names none. Check: `test_a_medium_match_names_the_seller`. (Added in T5 at Paul's
   request.)
5. The loader reports 24 merchant names, all of direct merchants, and loading twice still
   changes nothing. Check: `test_the_loader_names_only_direct_merchants`.
6. `uv run pytest -q` in `api/` shows `34 passed` with Postgres up; ruff and pyright clean.

## Rules that apply

- "I can't tell" beats a weak guess (AGENTS.md: Domain rules): below `MEDIUM` no seller is
  named, and the claim escalates (DOH-3.2); thresholds as named constants
  (`.claude/rules/python-api.md`).
- SQL values as parameters, including the `%(q)s` passed to `similarity()` and `%`.
- Safe to repeat: `refresh_merchant_names()` rebuilds inside the loader's one transaction.

## Harness changes

- `AGENTS.md`: `merchants.py` in the layout, its CLI in the commands, the "I can't tell beats a
  guess" domain rule, the test count.
- `.claude/rules/python-api.md`: cut-offs as named constants, resolvers return `None` at `low`
  and name the seller at `medium` or `high`, domain reads through `Store` (the loader excepted).
- `.claude/agents/reviewer.md`: the area checks start (bands tested at their edges).
- `.claude/settings.json`: `uv run --directory api python -m app.merchants *` allowed and
  excluded from the sandbox (it needs Postgres).
- `.github/copilot-instructions.md`: a resolver below `MEDIUM` never guesses.

## Out of scope

- Claims, routes or any API change (C-104).
- The investigator that digs into low-confidence sellers using the cart (C-207).
- A model call of any kind. This ticket is plain code and an index.

## Open questions

1. Should the CLI print the candidates for a medium match, or only the winner? Answered in T6:
   every candidate with its score and band, best first, so the winner is the first line
   (plan.md).
