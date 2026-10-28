import os
from collections.abc import AsyncIterator

import httpx
import psycopg
import pytest
import pytest_asyncio
from psycopg.conninfo import conninfo_to_dict

from app.load_world import load
from app.main import create_app
from app.settings import Settings

# Tests may read the environment directly: they are not app code. The default is the local
# Compose database (its password is the public dev default in docker-compose.yml).
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://countersign:countersign@localhost:5432/countersign_test"
)


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """An HTTP client wired straight into the app: no server, no network."""
    app = create_app(Settings(database_url=None, countersign_admin_key="test-key"))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_url() -> str:
    """An empty test database, wiped once per session. Refuses anything not named *_test."""
    # This check must come before any connection: a wrong URL must never reach the DROP.
    name = str(conninfo_to_dict(TEST_DATABASE_URL).get("dbname", ""))
    if not name.endswith("_test"):
        raise RuntimeError(f"refusing to wipe database {name!r}: its name must end in _test")
    try:
        conn = await psycopg.AsyncConnection.connect(TEST_DATABASE_URL, autocommit=True)
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres is down ({exc.__class__.__name__}): docker compose up -d db")
    async with conn:
        # Dropping the schema removes every table, so each session starts from nothing.
        await conn.execute("DROP SCHEMA public CASCADE")
        await conn.execute("CREATE SCHEMA public")
    return TEST_DATABASE_URL


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def world_db(db_url: str) -> str:
    """The test database with the world loaded once."""
    await load(db_url)
    return db_url
