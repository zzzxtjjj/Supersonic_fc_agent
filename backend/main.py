from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api import admin, agent, gallery, matches, players, stats
from backend.media_storage import MEDIA_ROOT

app = FastAPI(
    title="Supersonic FC API",
    version="0.1.0",
    description=(
        "Non-core API contract skeleton. It does not connect to LangGraph, "
        "the existing Agent, RAG, or a database."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")


@app.get("/", tags=["system"])
async def service_root() -> dict[str, str]:
    return {
        "service": "Supersonic FC API",
        "status": "ok",
        "docs": "/docs",
    }

for router in (
    admin.router,
    agent.router,
    players.router,
    matches.router,
    stats.router,
    gallery.router,
):
    app.include_router(router, prefix="/api")
