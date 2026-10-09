from collections.abc import AsyncIterator

import httpx
import pytest

from app.main import create_app
from app.settings import Settings


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """An HTTP client wired straight into the app: no server, no network."""
    app = create_app(Settings(database_url=None, countersign_admin_key="test-key"))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
