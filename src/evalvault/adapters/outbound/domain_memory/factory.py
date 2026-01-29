from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from evalvault.adapters.outbound.domain_memory.postgres_adapter import PostgresDomainMemoryAdapter
from evalvault.adapters.outbound.domain_memory.sqlite_adapter import SQLiteDomainMemoryAdapter

if TYPE_CHECKING:
    from evalvault.config.settings import Settings
    from evalvault.ports.outbound.domain_memory_port import DomainMemoryPort

logger = logging.getLogger(__name__)


def build_domain_memory_adapter(
    *,
    settings: Settings | None = None,
    db_path: Path | None = None,
    fallback_to_sqlite: bool = True,
) -> DomainMemoryPort:
    """Build domain memory adapter based on settings and parameters.

    Args:
        settings: Application settings (uses default if None)
        db_path: Explicit SQLite database path (forces SQLite if provided)
        fallback_to_sqlite: Fall back to SQLite if Postgres fails

    Returns:
        DomainMemoryPort implementation (Postgres by default, SQLite if specified)
    """
    from evalvault.config.settings import Settings

    resolved_settings = settings or Settings()

    if db_path is not None:
        return SQLiteDomainMemoryAdapter(db_path=db_path)

    backend = getattr(resolved_settings, "db_backend", "postgres")
    if backend == "sqlite":
        resolved_db_path = resolved_settings.evalvault_memory_db_path
        if resolved_db_path is None:
            raise RuntimeError("SQLite backend selected but evalvault_memory_db_path is not set.")
        return SQLiteDomainMemoryAdapter(db_path=resolved_db_path)

    conn_string = resolved_settings.postgres_connection_string
    if not conn_string:
        host = resolved_settings.postgres_host or "localhost"
        port = resolved_settings.postgres_port
        database = resolved_settings.postgres_database
        user = resolved_settings.postgres_user or "postgres"
        password = resolved_settings.postgres_password or ""
        conn_string = f"host={host} port={port} dbname={database} user={user} password={password}"

    try:
        return PostgresDomainMemoryAdapter(connection_string=conn_string)
    except Exception as exc:
        if not fallback_to_sqlite:
            raise
        logger.warning("PostgreSQL domain memory adapter failed (%s). Falling back to SQLite.", exc)
        resolved_db_path = resolved_settings.evalvault_memory_db_path
        if resolved_db_path is None:
            raise
        return SQLiteDomainMemoryAdapter(db_path=resolved_db_path)


__all__ = ["build_domain_memory_adapter"]
