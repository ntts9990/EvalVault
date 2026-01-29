from __future__ import annotations

import logging
from pathlib import Path

from evalvault.adapters.outbound.storage.postgres_adapter import PostgreSQLStorageAdapter
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.config.settings import Settings
from evalvault.ports.outbound.storage_port import StoragePort

logger = logging.getLogger(__name__)


def build_storage_adapter(
    *,
    settings: Settings | None = None,
    db_path: Path | None = None,
    fallback_to_sqlite: bool = True,
) -> StoragePort:
    resolved_settings = settings or Settings()

    if db_path is not None:
        return SQLiteStorageAdapter(db_path=db_path)

    backend = getattr(resolved_settings, "db_backend", "postgres")
    if backend == "sqlite":
        resolved_db_path = resolved_settings.evalvault_db_path
        if resolved_db_path is None:
            raise RuntimeError("SQLite backend selected but evalvault_db_path is not set.")
        return SQLiteStorageAdapter(db_path=resolved_db_path)

    conn_string = resolved_settings.postgres_connection_string
    if not conn_string:
        host = resolved_settings.postgres_host or "localhost"
        port = resolved_settings.postgres_port
        database = resolved_settings.postgres_database
        user = resolved_settings.postgres_user or "postgres"
        password = resolved_settings.postgres_password or ""
        conn_string = f"host={host} port={port} dbname={database} user={user} password={password}"

    try:
        return PostgreSQLStorageAdapter(connection_string=conn_string)
    except Exception as exc:
        if not fallback_to_sqlite:
            raise
        logger.warning("PostgreSQL adapter failed (%s). Falling back to SQLite.", exc)
        resolved_db_path = resolved_settings.evalvault_db_path
        if resolved_db_path is None:
            raise
        return SQLiteStorageAdapter(db_path=resolved_db_path)


__all__ = ["build_storage_adapter"]
