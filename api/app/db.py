from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

SCHEMA = Path(__file__).with_name("schema.sql").read_bytes()


async def apply_schema(conn: psycopg.AsyncConnection) -> None:
    """Run schema.sql in one go. Every statement is IF NOT EXISTS, so it is safe to repeat."""
    await conn.execute(SCHEMA)


def make_pool(url: str) -> AsyncConnectionPool:
    """A few open connections, lent to requests and returned. Rows come back as dicts."""
    return AsyncConnectionPool(
        url, min_size=1, max_size=5, open=False, kwargs={"row_factory": dict_row}
    )
