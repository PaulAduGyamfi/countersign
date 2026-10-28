"""Load data/world.json into Postgres. Run it as often as you like: it upserts."""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from app.db import apply_schema
from app.settings import get_settings

WORLD = Path(__file__).resolve().parents[2] / "data" / "world.json"

# Table -> (key columns, other columns). The order is the load order: parents before the
# children whose foreign keys point at them. `claims` is left out until C-104.
TABLES: dict[str, tuple[str, str]] = {
    "cardmembers": ("id", "full_name email"),
    "cards": ("id", "cardmember_id last4 product_tier issued_by market kind segment"),
    "agents": ("id", "name developer registered registered_at suspended_at"),
    "enablements": ("card_id agent_id", "enabled_at"),
    "merchants": (
        "id",
        "name kind aliases mcc sku_prefix returnable return_window_days"
        " restocking_fee_pct return_shipping_cents return_note",
    ),
    "intents": ("id", "card_id agent_id instruction max_amount_cents authenticated_at auth_method"),
    "transactions": (
        "id",
        "card_id descriptor amount_cents currency posted_at agent_id intent_id merchant_id mcc",
    ),
    "cart_lines": (
        "transaction_id line_no",
        "sku title attributes qty unit_price_cents merchant_note",
    ),
    "returns": ("transaction_id", "status initiated_at refunded_cents return_shipping_paid_cents"),
}


def upsert_sql(table: str, keys: list[str], cols: list[str]) -> sql.Composed:
    """INSERT one row, or overwrite the row with the same key: running it twice changes nothing."""
    names = keys + cols
    # Names go in as quoted identifiers and values as %(name)s placeholders, never as text.
    return sql.SQL(
        "INSERT INTO {table} ({names}) VALUES ({values}) ON CONFLICT ({keys}) DO UPDATE SET {sets}"
    ).format(
        table=sql.Identifier(table),
        names=sql.SQL(", ").join(map(sql.Identifier, names)),
        values=sql.SQL(", ").join(map(sql.Placeholder, names)),
        keys=sql.SQL(", ").join(map(sql.Identifier, keys)),
        sets=sql.SQL(", ").join(
            sql.SQL("{c} = EXCLUDED.{c}").format(c=sql.Identifier(c)) for c in cols
        ),
    )


def prepare(row: dict[str, Any]) -> dict[str, Any]:
    """Make one row ready to send. psycopg won't guess that a dict is jsonb, so we say so."""
    if "attributes" in row:
        return {**row, "attributes": Jsonb(row["attributes"])}
    return row


def read_world(path: Path = WORLD) -> dict[str, Any]:
    """The synthetic world, exactly as the file has it."""
    return json.loads(path.read_text())


async def load(url: str, world: dict[str, Any] | None = None) -> dict[str, int]:
    """Upsert every table in one transaction and return the row count of each."""
    world = world if world is not None else read_world()
    counts: dict[str, int] = {}
    async with await psycopg.AsyncConnection.connect(url) as conn:
        # One transaction: a failure on any table rolls back every table, schema included.
        async with conn.transaction():
            await apply_schema(conn)
            async with conn.cursor() as cur:
                for table, (keys, cols) in TABLES.items():
                    query = upsert_sql(table, keys.split(), cols.split())
                    await cur.executemany(query, [prepare(r) for r in world[table]])
                    # Count what the table holds, not what we sent: that is what proves no dupes.
                    await cur.execute(
                        sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))
                    )
                    row = await cur.fetchone()
                    counts[table] = row[0] if row else 0
    return counts


def main() -> None:
    url = get_settings().database_url
    if not url:
        raise SystemExit("DATABASE_URL is not set. Add it to the repo's env file.")
    start = time.perf_counter()
    counts = asyncio.run(load(url))
    print(f"Loaded the world in {time.perf_counter() - start:.1f}s")
    for table, n in counts.items():
        print(f"  {table:<12} {n}")


if __name__ == "__main__":
    main()
