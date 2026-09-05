import logging
import os
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api import admin, agent, gallery, matches, players, stats
from backend.media_storage import MEDIA_ROOT


logger = logging.getLogger("supersonic.http")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST = Path(
    os.getenv("FRONTEND_DIST") or PROJECT_ROOT / "frontend" / "dist"
)


def _allowed_origins() -> list[str]:
    configured_origin = os.getenv("FRONTEND_ORIGIN", "").strip().rstrip("/")
    if os.getenv("APP_ENV", "development").lower() == "production":
        return [configured_origin] if configured_origin else []
    origins = ["http://127.0.0.1:5173", "http://localhost:5173"]
    if configured_origin and configured_origin not in origins:
        origins.append(configured_origin)
    return origins

app = FastAPI(
    title="Supersonic FC API",
    version="0.1.0",
    description=(
        "Supersonic FC product API. Agent chat invokes the existing LangGraph "
        "product entry point; season and media data remain file-backed."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_http_request(request: Request, call_next):
    started_at = perf_counter()
    response = await call_next(request)
    elapsed_ms = (perf_counter() - started_at) * 1000
    logger.info(
        "%s %s %s %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response

app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")


@app.get("/", tags=["system"])
async def service_root():
    if (
        os.getenv("SERVE_FRONTEND", "false").lower() == "true"
        and (FRONTEND_DIST / "index.html").is_file()
    ):
        return FileResponse(FRONTEND_DIST / "index.html")
    return {
        "service": "Supersonic FC API",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/api/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Cheap liveness check that does not initialize the Agent or RAG models."""

    return {"status": "ok"}

for router in (
    admin.router,
    agent.router,
    players.router,
    matches.router,
    stats.router,
    gallery.router,
):
    app.include_router(router, prefix="/api")


if (
    os.getenv("SERVE_FRONTEND", "false").lower() == "true"
    and (FRONTEND_DIST / "index.html").is_file()
):
    frontend_root = FRONTEND_DIST.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str) -> FileResponse:
        requested_file = (frontend_root / full_path).resolve()
        if requested_file.is_relative_to(frontend_root) and requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(frontend_root / "index.html")
