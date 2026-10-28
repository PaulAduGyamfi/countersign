import psycopg
from psycopg.rows import dict_row

from app.load_world import load, read_world


async def test_loading_twice_changes_nothing(world_db: str) -> None:
    world = read_world()
    first = await load(world_db)
    second = await load(world_db)
    assert first == second
    # Upserts, not inserts: the counts match the file, not twice the file.
    assert first["transactions"] == len(world["transactions"]) == 50
    assert first["cart_lines"] == len(world["cart_lines"]) == 46


async def test_mayas_shoes_are_in_the_database(world_db: str) -> None:
    query = """
        SELECT t.descriptor, t.amount_cents, i.instruction, c.attributes
        FROM transactions t
        JOIN intents i ON i.id = t.intent_id
        JOIN cart_lines c ON c.transaction_id = t.id
        WHERE t.id = %(id)s
    """
    async with await psycopg.AsyncConnection.connect(world_db) as conn:
        # dict_row on the cursor (not on connect) so pyright knows rows are dicts.
        cur = await conn.cursor(row_factory=dict_row).execute(query, {"id": "TXN-1001"})
        row = await cur.fetchone()
    assert row is not None
    assert row["descriptor"] == "NORTHWIND RUNNING #0412 PORTLAND OR"
    assert row["amount_cents"] == 13999
    assert "size 10" in row["instruction"]
    # jsonb comes back as a dict, so the attributes compare as data, not as text.
    assert row["attributes"] == {"color": "White/Grey", "size": "11", "width": "D"}
