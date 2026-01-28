"""FastAPI entry point for EvalVault API."""

from __future__ import annotations

import hashlib
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import JSONResponse

from evalvault.adapters.inbound.api.adapter import WebUIAdapter, create_adapter
from evalvault.config.settings import Settings, get_settings, is_production_profile

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._blocked_counts: dict[str, int] = defaultdict(int)

    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int | None, int]:
        now = time.monotonic()
        window = max(window_seconds, 1)
        queue = self._requests[key]
        while queue and now - queue[0] >= window:
            queue.popleft()
        if len(queue) >= limit:
            self._blocked_counts[key] += 1
            retry_after = int(window - (now - queue[0])) if queue else window
            return False, max(retry_after, 1), self._blocked_counts[key]
        queue.append(now)
        return True, None, self._blocked_counts[key]


rate_limiter = RateLimiter()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:8]


def _rate_limit_key(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        if token:
            return f"token:{_hash_token(token)}"
    client = request.client
    host = client.host if client else "unknown"
    return f"ip:{host}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    # Startup: Initialize adapter
    adapter = create_adapter()
    app.state.adapter = adapter
    try:
        from evalvault.adapters.inbound.api.routers.chat import warm_rag_index

        await warm_rag_index()
    except Exception as exc:
        logger.warning("RAG preload failed: %s", exc)
    yield
    # Shutdown: Cleanup if necessary
    pass


auth_scheme = HTTPBearer(auto_error=False)


def _normalize_api_tokens(raw_tokens: str | None) -> set[str]:
    if not raw_tokens:
        return set()
    return {token.strip() for token in raw_tokens.split(",") if token.strip()}


def require_api_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(auth_scheme)],
    settings: Settings = Depends(get_settings),
) -> str | None:
    tokens = _normalize_api_tokens(settings.api_auth_tokens)
    if not tokens:
        return None
    if credentials is None or credentials.credentials not in tokens:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="EvalVault API",
        description="REST API for EvalVault RAG Evaluation System",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        limit = max(settings.rate_limit_requests, 1)
        window_seconds = max(settings.rate_limit_window_seconds, 1)
        key = _rate_limit_key(request)
        allowed, retry_after, blocked_count = rate_limiter.check(
            key,
            limit,
            window_seconds,
        )
        if not allowed:
            if blocked_count >= settings.rate_limit_block_threshold:
                logger.warning(
                    "Rate limit blocked request",
                    extra={
                        "rate_limit_key": key,
                        "blocked_count": blocked_count,
                    },
                )
            headers = {"Retry-After": str(retry_after)} if retry_after else None
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers=headers,
            )
        return await call_next(request)

    settings = get_settings()
    cors_origins = [
        origin.strip() for origin in (settings.cors_origins or "").split(",") if origin.strip()
    ]
    if not cors_origins:
        if is_production_profile(settings.evalvault_profile):
            raise RuntimeError("CORS_ORIGINS must be set for production profile.")
        cors_origins = ["http://localhost:5173"]

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from .routers import (
        benchmark,
        calibration,
        chat,
        config,
        domain,
        knowledge,
        mcp,
        pipeline,
        runs,
    )

    auth_dependencies = [Depends(require_api_token)]

    app.include_router(
        runs.router,
        prefix="/api/v1/runs",
        tags=["runs"],
        dependencies=auth_dependencies,
    )
    app.include_router(
        chat.router,
        prefix="/api/v1/chat",
        tags=["chat"],
        dependencies=auth_dependencies,
    )
    app.include_router(
        benchmark.router,
        prefix="/api/v1/benchmarks",
        tags=["benchmarks"],
        dependencies=auth_dependencies,
    )
    app.include_router(
        knowledge.router,
        prefix="/api/v1/knowledge",
        tags=["knowledge"],
        dependencies=auth_dependencies,
    )
    app.include_router(
        pipeline.router,
        prefix="/api/v1/pipeline",
        tags=["pipeline"],
        dependencies=auth_dependencies,
    )
    app.include_router(
        domain.router,
        prefix="/api/v1/domain",
        tags=["domain"],
        dependencies=auth_dependencies,
    )
    app.include_router(
        config.router,
        prefix="/api/v1/config",
        tags=["config"],
        dependencies=auth_dependencies,
    )
    app.include_router(
        mcp.router,
        prefix="/api/v1/mcp",
        tags=["mcp"],
        dependencies=auth_dependencies,
    )
    app.include_router(
        calibration.router,
        prefix="/api/v1/calibration",
        tags=["calibration"],
        dependencies=auth_dependencies,
    )

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
    return app.state.adapter


def get_web_adapter(request: Request) -> WebUIAdapter:
    """FastAPI dependency to get the WebUIAdapter."""
    return request.app.state.adapter


AdapterDep = Annotated[WebUIAdapter, Depends(get_web_adapter)]
