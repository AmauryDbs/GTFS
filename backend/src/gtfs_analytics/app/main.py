"""Application entrypoint with optional FastAPI integration."""

from __future__ import annotations

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except Exception:  # pragma: no cover - FastAPI optional in tests
    FastAPI = None  # type: ignore
    CORSMiddleware = None  # type: ignore


def create_app():  # type: ignore[override]
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Install fastapi to use the web API layer.")

    from .api.router import router  # Imported lazily to avoid FastAPI dependency during tests

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

    @application.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return application


__all__ = ["create_app"]
