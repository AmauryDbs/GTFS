"""Application entrypoint with optional FastAPI integration."""

from __future__ import annotations

import logging
from pathlib import Path

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except Exception:  # pragma: no cover - FastAPI optional in tests
    FastAPI = None  # type: ignore
    CORSMiddleware = None  # type: ignore

try:  # pragma: no cover - optional dependency when serving the SPA
    from starlette.staticfiles import StaticFiles
except Exception:  # pragma: no cover - StaticFiles optional in tests
    StaticFiles = None  # type: ignore


logger = logging.getLogger(__name__)


def create_app():  # type: ignore[override]
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Install fastapi to use the web API layer.")

    from .api.router import local_router, router  # Imported lazily to avoid FastAPI dependency during tests

    application = FastAPI(title="GTFS Analytics Toolkit", version="0.1.0")
    if CORSMiddleware is not None:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    application.include_router(router)
    application.include_router(local_router)

    if StaticFiles is not None:
        frontend_dist = Path(__file__).resolve().parents[5] / "frontend" / "dist"
        if frontend_dist.exists() and any(frontend_dist.iterdir()):
            application.mount(
                "/",
                StaticFiles(directory=str(frontend_dist), html=True),
                name="frontend",
            )
            logger.info("Mounted frontend build from %s", frontend_dist)
        else:
            logger.debug("Frontend build directory not found at %s; skipping mount", frontend_dist)

    @application.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return application


__all__ = ["create_app"]
