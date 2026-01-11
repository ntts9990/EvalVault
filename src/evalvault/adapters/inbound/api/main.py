"""FastAPI entry point for EvalVault API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from evalvault.adapters.inbound.api.adapter import WebUIAdapter, create_adapter
from evalvault.config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    # Startup: Initialize adapter
    adapter = create_adapter()
    app.state.adapter = adapter
    yield
    # Shutdown: Cleanup if necessary
    pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="EvalVault API",
        description="REST API for EvalVault RAG Evaluation System",
        version="1.0.0",
        lifespan=lifespan,
    )

    settings = get_settings()
    cors_origins = [
        origin.strip() for origin in (settings.cors_origins or "").split(",") if origin.strip()
    ] or ["http://localhost:5173"]

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from .routers import benchmark, config, domain, knowledge, pipeline, runs

    app.include_router(runs.router, prefix="/api/v1/runs", tags=["runs"])
    app.include_router(benchmark.router, prefix="/api/v1/benchmarks", tags=["benchmarks"])
    app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
    app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["pipeline"])
    app.include_router(domain.router, prefix="/api/v1/domain", tags=["domain"])
    app.include_router(config.router, prefix="/api/v1/config", tags=["config"])

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    @app.get("/")
    def root():
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/docs")

    return app


# Dependency to get the adapter
def get_adapter(app: FastAPI) -> WebUIAdapter:
    """Dependency to retrieve the WebUIAdapter from app state."""
    # When using Depends(), we can't easily access 'app' directly in standard dependency signature
    # unless we use Request. So we usually do:
    pass


def get_web_adapter(request: Request) -> WebUIAdapter:
    """FastAPI dependency to get the WebUIAdapter."""
    return request.app.state.adapter


AdapterDep = Annotated[WebUIAdapter, Depends(get_web_adapter)]
