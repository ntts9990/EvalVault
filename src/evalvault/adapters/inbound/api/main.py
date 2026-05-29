"""FastAPI entry point for EvalVault API."""

from __future__ import annotations

import hashlib
import logging
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import JSONResponse

from evalvault.adapters.inbound.api.adapter import WebUIAdapter, create_adapter
from evalvault.adapters.inbound.api.principal import (
    InsufficientRoleError,
    PrincipalRequiredError,
    ProjectAccessDeniedError,
    resolve_current_project_id,
    resolve_principal,
)
from evalvault.config.runtime_services import ensure_local_observability
from evalvault.config.settings import Settings, get_settings, is_production_profile
from evalvault.domain.services.authorization import Principal

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
    ensure_local_observability(get_settings())
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


# Hosts that only accept connections from the local machine.
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", "0:0:0:0:0:0:0:1", ""}


def is_loopback_host(host: str | None) -> bool:
    """True if binding ``host`` only exposes the API to the local machine."""
    return (host or "").strip().lower() in _LOOPBACK_HOSTS


def ensure_safe_network_bind(host: str, settings: Settings) -> None:
    """Fail-closed (EvalVault Auth P1.0): refuse to expose the API on a
    non-loopback interface when no authentication is configured.

    Binding to a non-loopback host (e.g. ``0.0.0.0``) publishes every
    ``/api/v1`` endpoint to the network. Until project-scoped auth is enforced,
    doing so without at least a shared API token is an unauthenticated network
    exposure, so we refuse to start. Local-only binds are unaffected.

    Escape hatch: set ``EVALVAULT_ALLOW_INSECURE_NETWORK=1`` to override (e.g.
    when fronted by an external auth proxy). Not recommended.
    """
    if is_loopback_host(host):
        return
    if _normalize_api_tokens(settings.api_auth_tokens):
        return
    if os.getenv("EVALVAULT_ALLOW_INSECURE_NETWORK") == "1":
        logger.warning(
            "EVALVAULT_ALLOW_INSECURE_NETWORK=1: binding to %r without authentication.",
            host,
        )
        return
    raise RuntimeError(
        f"Refusing to bind the EvalVault API to non-loopback host {host!r} without "
        "authentication. Set API_AUTH_TOKENS to require a token, bind to 127.0.0.1 for "
        "local-only use, or set EVALVAULT_ALLOW_INSECURE_NETWORK=1 to override (not recommended)."
    )


def require_api_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(auth_scheme)],
    settings: Settings = Depends(get_settings),
) -> str | None:
    tokens = _normalize_api_tokens(settings.api_auth_tokens)
    if not tokens:
        return None
    raw_token = credentials.credentials if credentials else None
    if raw_token and raw_token in tokens:
        return raw_token
    if raw_token and _resolve_principal_from_token(request, raw_token) is not None:
        return raw_token
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API token",
        headers={"WWW-Authenticate": "Bearer"},
    )


# --- Project-scoped principal resolution (G4 live route wiring) -------------
# Providers prefer an injected ``app.state`` value (tests / DI) and otherwise
# build lazily from settings. They are only reached when a request actually
# carries a bearer token, so legacy / no-project requests pay nothing and behave
# exactly as before (the shared API token alone confers no project membership).


def _resolve_identity_store(request: Request):
    store = getattr(request.app.state, "identity_store", None)
    if store is not None:
        return store
    from evalvault.adapters.outbound.storage.sqlite_identity import (
        SqliteIdentityStorageAdapter,
    )

    store = SqliteIdentityStorageAdapter(db_path=get_settings().evalvault_db_path)
    request.app.state.identity_store = store
    return store


def _resolve_token_service(request: Request):
    service = getattr(request.app.state, "token_service", None)
    if service is not None:
        return service
    secret = get_settings().auth_secret_key
    if not secret:
        return None
    from evalvault.adapters.outbound.auth.jwt_token_service import JwtTokenService

    service = JwtTokenService(secret=secret)
    request.app.state.token_service = service
    return service


def _resolve_password_hasher(request: Request):
    hasher = getattr(request.app.state, "password_hasher", None)
    if hasher is not None:
        return hasher
    from evalvault.adapters.outbound.auth.argon2_hasher import Argon2PasswordHasher

    hasher = Argon2PasswordHasher()
    request.app.state.password_hasher = hasher
    return hasher


class _NoJwtTokenService:
    def decode(self, token: str, *, expected_type: str | None = None) -> dict:
        from evalvault.ports.outbound.auth_port import TokenError

        raise TokenError("JWT auth is not configured")


def _resolve_principal_from_token(request: Request, token: str | None) -> Principal | None:
    if not token:
        return None
    token_service = _resolve_token_service(request) or _NoJwtTokenService()
    hasher = _resolve_password_hasher(request)
    store = _resolve_identity_store(request)
    if store is None or hasher is None:
        return None
    return resolve_principal(
        token, identity_store=store, token_service=token_service, hasher=hasher
    )


def get_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(auth_scheme)],
) -> Principal | None:
    """Resolve a project-scoped principal from the bearer token, or ``None``.

    Returns ``None`` when no token is presented or identity is not configured,
    so legacy / no-project requests are unaffected. A shared API token that is
    not a real identity credential resolves to ``None`` (no project membership).
    """
    token = credentials.credentials if credentials else None
    return _resolve_principal_from_token(request, token)


def get_current_project_id(request: Request, project_id: str | None = None) -> str | None:
    """Current project id with documented precedence: ``X-Project-Id`` header →
    ``project_id`` query param. Body-supplied project_id is handled per-route."""
    return resolve_current_project_id(
        header=request.headers.get("X-Project-Id"),
        query=project_id,
    )


PrincipalDep = Annotated[Principal | None, Depends(get_principal)]
ProjectIdDep = Annotated[str | None, Depends(get_current_project_id)]


def _handle_principal_required(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": "Authentication required"},
        headers={"WWW-Authenticate": "Bearer"},
    )


def _handle_project_access_denied(request: Request, exc: Exception) -> JSONResponse:
    # 404 (not 403) so a non-member cannot tell a foreign project/run apart from
    # one that does not exist.
    return JSONResponse(status_code=404, content={"detail": "Run not found"})


def _handle_insufficient_role(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=403, content={"detail": "Insufficient role for this operation"}
    )


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
    if not _normalize_api_tokens(settings.api_auth_tokens):
        logger.warning(
            "API authentication is DISABLED: api_auth_tokens (API_AUTH_TOKENS) is empty, "
            "so all /api/v1 endpoints are reachable without a bearer token. "
            "Set API_AUTH_TOKENS to require authentication."
        )
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

    # Map the project-scoped denial policy to HTTP status codes (G4).
    app.add_exception_handler(PrincipalRequiredError, _handle_principal_required)
    app.add_exception_handler(ProjectAccessDeniedError, _handle_project_access_denied)
    app.add_exception_handler(InsufficientRoleError, _handle_insufficient_role)

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
