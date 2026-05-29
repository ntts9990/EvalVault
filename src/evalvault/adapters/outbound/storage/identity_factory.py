from __future__ import annotations

from evalvault.adapters.outbound.storage.sqlite_identity import SqliteIdentityStorageAdapter
from evalvault.config.settings import Settings
from evalvault.ports.outbound.identity_port import IdentityStoragePort


def _build_postgres_identity_storage(connection_string: str) -> IdentityStoragePort:
    from evalvault.adapters.outbound.storage.postgres_identity import (
        PostgresIdentityStorageAdapter,
    )

    return PostgresIdentityStorageAdapter(connection_string=connection_string)


def build_identity_storage_adapter(settings: Settings | None = None) -> IdentityStoragePort:
    """Build the identity store matching the configured persistence backend."""
    resolved_settings = settings or Settings()
    backend = getattr(resolved_settings, "db_backend", "postgres")
    if backend == "sqlite":
        return SqliteIdentityStorageAdapter(db_path=resolved_settings.evalvault_db_path)

    conn_string = resolved_settings.postgres_connection_string
    if not conn_string:
        host = resolved_settings.postgres_host or "localhost"
        port = resolved_settings.postgres_port
        database = resolved_settings.postgres_database
        user = resolved_settings.postgres_user or "postgres"
        password = resolved_settings.postgres_password or ""
        conn_string = f"host={host} port={port} dbname={database} user={user} password={password}"
    return _build_postgres_identity_storage(conn_string)


__all__ = ["build_identity_storage_adapter"]
