"""Merchant names: turn a card descriptor into the merchant it most likely names.

A descriptor such as `SQ *COBALT COFFEE ROA` is noisy. `normalize()` removes the noise so that
Postgres can compare what is left with the merchants' names by trigram similarity. A `high` or
`medium` match names a merchant; a `low` one names none: "I can't tell" beats a weak guess.
"""

import asyncio
import re
import sys
from typing import Any, Literal

from pydantic import BaseModel

from app.db import Store, make_pool
from app.settings import get_settings

# Trigram-similarity cut-offs, from 0 (nothing shared) to 1 (identical). A best score at or above
# MEDIUM names the merchant (HIGH marks the surer matches); below MEDIUM we can't tell.
# MEDIUM equals pg_trgm's default similarity_threshold, the cut-off its `%` operator uses.
HIGH, MEDIUM = 0.6, 0.3

# Payment facilitators process for many small sellers, so the seller is only in the text.
FACILITATOR_PREFIXES = ("SQ *", "TST*", "PAYPAL *", "SP *", "PY *")

# The 50 state codes plus DC. Descriptors often end with the seller's state.
US_STATES = frozenset(
    {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        "DC",
    }
)  # fmt: skip


def normalize(descriptor: str) -> str:
    """Return the descriptor without its noise, in upper case with single spaces.

    The steps run in order, and the order matters (see the comments).
    """
    # One case, so `Cobalt` and `COBALT` compare equal.
    text = descriptor.upper().strip()
    # At most one facilitator prefix. A second one is part of the name we were given.
    for prefix in FACILITATOR_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    # `HARBOR&PINE` and `Harbor and Pine` are the same name.
    text = re.sub(r"&", " AND ", text)
    # Phone numbers. Before the digit-run step, or `800-555-0199` would leave `800 555` behind.
    text = re.sub(r"\d{3}-\d{3}-\d{4}", " ", text)
    # Store numbers such as `#0412`.
    text = re.sub(r"#\d+", " ", text)
    # Order references such as `*ORDER 7731` (the number goes in the digit-run step).
    text = re.sub(r"\*\s*ORDER\b", " ", text)
    # A web address's `.COM`: `MERIDIANELECTRONICS.COM` names the shop, not the domain.
    text = re.sub(r"\.COM\b", " ", text)
    # Runs of 4 or more digits: ticket, order and terminal numbers.
    text = re.sub(r"\d{4,}", " ", text)
    # Any other punctuation separates words: `LUMEN*STREAMING` is two words.
    text = re.sub(r"[^A-Z0-9 ]", " ", text)
    # Single spaces, none at the ends.
    text = re.sub(r"\s+", " ", text).strip()
    # One trailing state code, but never the only word left (a merchant could be called `OR`).
    words = text.split(" ")
    if len(words) > 1 and words[-1] in US_STATES:
        words = words[:-1]
    return " ".join(words)


# How sure we are. `high` and `medium` name a merchant; `low` names none (policy DOH-3.2).
Confidence = Literal["high", "medium", "low"]


def band(score: float) -> Confidence:
    """The confidence for a similarity score. Each cut-off belongs to the band above it."""
    if score >= HIGH:
        return "high"
    if score >= MEDIUM:
        return "medium"
    return "low"


class Candidate(BaseModel):
    """A direct merchant whose name looks like the descriptor, and how alike they are."""

    merchant_id: str
    name: str
    score: float


class Resolution(BaseModel):
    """The answer for one charge. `merchant_id` and `name` are None when the confidence is `low`."""

    merchant_id: str | None
    name: str | None
    confidence: Confidence
    method: Literal["merchant_of_record", "descriptor"]
    normalized: str
    candidates: list[Candidate]


async def resolve_name(store: Store, text: str) -> list[Candidate]:
    """Best matches for any merchant name: a descriptor, or 'Northwind Running' in an intent."""
    rows = await store.similar_merchants(normalize(text))
    return [Candidate(**r) for r in rows]


async def resolve_seller(store: Store, transaction: dict[str, Any]) -> Resolution:
    """The seller behind a charge: the merchant of record, unless a facilitator sits between."""
    record = await store.merchant(transaction["merchant_id"])
    normalized = normalize(transaction["descriptor"])
    if record["kind"] == "direct":
        return Resolution(
            merchant_id=record["id"],
            name=record["name"],
            confidence="high",
            method="merchant_of_record",
            normalized=normalized,
            candidates=[],
        )
    candidates = await resolve_name(store, transaction["descriptor"])
    best = candidates[0] if candidates else None
    confidence = band(best.score) if best else "low"
    return Resolution(
        merchant_id=best.merchant_id if best and confidence != "low" else None,
        name=best.name if best and confidence != "low" else None,
        confidence=confidence,
        method="descriptor",
        normalized=normalized,
        candidates=candidates,
    )


async def show(url: str, descriptor: str) -> None:
    """Print the cleaned descriptor and its best matches, each with its score and band."""
    async with make_pool(url) as pool:
        store = Store(pool)
        print(f"normalized: {normalize(descriptor)!r}")
        for c in await resolve_name(store, descriptor):
            print(f"  {c.score:.2f}  {band(c.score):<6}  {c.merchant_id}  {c.name}")


def main() -> None:
    url = get_settings().database_url
    if not url:
        raise SystemExit("DATABASE_URL is not set.")
    asyncio.run(show(url, " ".join(sys.argv[1:]) or "SQ *COBALT COFFEE ROA"))


if __name__ == "__main__":
    main()
