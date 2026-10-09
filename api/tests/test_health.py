import httpx


async def test_health(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


async def test_unknown_route_uses_the_one_error_format(client: httpx.AsyncClient) -> None:
    response = await client.get("/nope", headers={"X-Request-ID": "req-123"})
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Not Found", "request_id": "req-123"}
    }
