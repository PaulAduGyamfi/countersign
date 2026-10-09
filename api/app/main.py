import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from llmkit import configure, request_id

from app.errors import register_error_handlers
from app.settings import Settings, get_settings

log = logging.getLogger("countersign")


def create_app(settings: Settings | None = None) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure()
        app.state.settings = settings or get_settings()
        log.info("startup", extra={"ctx": {"service": "countersign"}})
        yield

    app = FastAPI(title="Countersign", lifespan=lifespan)
    register_error_handlers(app)

    @app.middleware("http")
    async def add_request_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request_id.set(rid)
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        log.info(
            "request",
            extra={
                "ctx": {
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "elapsed_ms": elapsed_ms,
                }
            },
        )
        response.headers["X-Request-ID"] = rid
        return response

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
