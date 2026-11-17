from pathlib import Path
from typing import Any

import psycopg
from psycopg.abc import Params

# psycopg's `Query` also allows 3.14 template strings, which `execute()` refuses to type-check.
from psycopg.abc import QueryNoTemplate as Query
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

SCHEMA = Path(__file__).with_name("schema.sql").read_bytes()


async def apply_schema(conn: psycopg.AsyncConnection) -> None:
    """Run schema.sql in one go. Every statement is IF NOT EXISTS, so it is safe to repeat."""
    await conn.execute(SCHEMA)


def make_pool(url: str) -> AsyncConnectionPool:
    """A few open connections, lent to requests and returned."""
    return AsyncConnectionPool(url, min_size=1, max_size=5, open=False)


class Store:
    """The domain's reads. Each call borrows a connection from the pool and gives it back."""

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self.pool = pool

    async def one(self, query: Query, params: Params | None = None) -> dict[str, Any] | None:
        """The first row as a dict, or None when there is none."""
        async with self.pool.connection() as conn:
            # dict_row on the cursor (not on the pool) so pyright knows rows are dicts.
            cur = await conn.cursor(row_factory=dict_row).execute(query, params)
            return await cur.fetchone()

    async def all(self, query: Query, params: Params | None = None) -> list[dict[str, Any]]:
        """Every row as a dict, in the order the query gives them."""
        async with self.pool.connection() as conn:
            cur = await conn.cursor(row_factory=dict_row).execute(query, params)
            return await cur.fetchall()

    async def merchant(self, merchant_id: str) -> dict[str, Any]:
        """One merchant by id. Raises KeyError if the world has no such merchant."""
        row = await self.one(
            "SELECT id, name, kind FROM merchants WHERE id = %(id)s", {"id": merchant_id}
        )
        if row is None:
            raise KeyError(merchant_id)
        return row

    async def similar_merchants(self, name: str, limit: int = 3) -> list[dict[str, Any]]:
        """Direct merchants named like `name`: one row each with its best score, best first."""
        # `%%` is pg_trgm's `%` operator, doubled because psycopg reads `%` as a placeholder.
        # It passes names whose similarity reaches pg_trgm.similarity_threshold (0.3 by
        # default) and lets Postgres use the GIN trigram index. max() keeps a merchant's best
        # alias; m.id breaks ties so the order never depends on the plan Postgres picks.
        return await self.all(
            """
            SELECT m.id AS merchant_id, m.name, max(similarity(n.name, %(name)s)) AS score
            FROM merchant_names n
            JOIN merchants m ON m.id = n.merchant_id
            WHERE m.kind = 'direct' AND n.name %% %(name)s
            GROUP BY m.id, m.name
            ORDER BY score DESC, m.id
            LIMIT %(limit)s
            """,
            {"name": name, "limit": limit},
        )
