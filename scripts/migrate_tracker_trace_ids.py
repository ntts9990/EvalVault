"""One-shot migration: legacy ``langfuse_trace_id`` -> ``tracker_trace_ids``.

A-S4 refactor (`refactor(domain+storage)`) replaced the vendor-specific
``EvaluationRun.langfuse_trace_id`` field with a provider-keyed
``tracker_trace_ids: dict[str, str]``. The storage layer now writes a
new ``tracker_trace_ids`` JSON column on ``evaluation_runs`` and keeps
the legacy ``langfuse_trace_id`` column around for backward-compat
reads. This script back-fills historical rows so they hydrate without
falling back to the legacy column at every read.

Idempotency contract
--------------------
* If the ``tracker_trace_ids`` column does not exist yet, ``ALTER TABLE``
  adds it (SQLite ``TEXT``; Postgres ``JSONB``).
* Rows with a populated ``langfuse_trace_id`` and a NULL / empty
  ``tracker_trace_ids`` are updated to
  ``{"langfuse": "<legacy value>"}``.
* Rows where ``tracker_trace_ids`` is already non-NULL / non-empty are
  left untouched. Re-running the script is therefore a no-op once every
  legacy row has been backfilled.

Backend detection
-----------------
The active backend is inferred from ``Settings``:

* If ``POSTGRES_HOST`` (or any explicit Postgres setting) is configured
  -- ``Settings.postgres_host`` is non-None or ``postgres_connection_string``
  is set -- run against Postgres.
* Otherwise run against SQLite at ``data/db/evalvault.db`` (the same
  default ``SQLiteStorageAdapter`` uses).

Pass ``--db sqlite:<path>`` or ``--db postgres:<conn>`` to override.

Examples
--------

::

    # Default detection (env-driven)
    uv run python scripts/migrate_tracker_trace_ids.py

    # Explicit SQLite path
    uv run python scripts/migrate_tracker_trace_ids.py --db sqlite:data/db/evalvault.db

    # Explicit Postgres
    uv run python scripts/migrate_tracker_trace_ids.py --db "postgres:host=localhost dbname=evalvault user=postgres"

The script logs how many rows it altered so re-runs print "0 rows
updated" once the migration is complete.
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("migrate_tracker_trace_ids")


def _column_exists_sqlite(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def migrate_sqlite(db_path: str | Path) -> int:
    """Run the migration against a SQLite database.

    Returns the number of rows actually updated. Idempotent: running on
    an already-migrated DB returns 0.
    """
    path = Path(db_path)
    if not path.exists():
        logger.warning("SQLite DB not found at %s; nothing to migrate.", path)
        return 0

    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        if not _column_exists_sqlite(conn, "evaluation_runs", "tracker_trace_ids"):
            logger.info("Adding tracker_trace_ids column to evaluation_runs (SQLite).")
            conn.execute("ALTER TABLE evaluation_runs ADD COLUMN tracker_trace_ids TEXT")
            conn.commit()

        if not _column_exists_sqlite(conn, "evaluation_runs", "langfuse_trace_id"):
            logger.info("No legacy langfuse_trace_id column; nothing to backfill.")
            return 0

        cursor = conn.execute(
            """
            SELECT run_id, langfuse_trace_id
            FROM evaluation_runs
            WHERE langfuse_trace_id IS NOT NULL
              AND langfuse_trace_id <> ''
              AND (tracker_trace_ids IS NULL OR tracker_trace_ids = '' OR tracker_trace_ids = '{}')
            """
        )
        rows = cursor.fetchall()
        updated = 0
        for row in rows:
            payload = json.dumps({"langfuse": row["langfuse_trace_id"]}, ensure_ascii=False)
            conn.execute(
                "UPDATE evaluation_runs SET tracker_trace_ids = ? WHERE run_id = ?",
                (payload, row["run_id"]),
            )
            updated += 1
        conn.commit()
        logger.info("SQLite: backfilled %d row(s).", updated)
        return updated
    finally:
        conn.close()


def _column_exists_postgres(conn: Any, table: str, column: str) -> bool:
    cursor = conn.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        LIMIT 1
        """,
        (table, column),
    )
    return cursor.fetchone() is not None


def migrate_postgres(connection_string: str) -> int:
    """Run the migration against a PostgreSQL database.

    Returns the number of rows actually updated. Idempotent across
    re-runs and across partially-migrated databases.
    """
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - dependency gate
        raise RuntimeError(
            "psycopg is required for Postgres migrations. Install with `uv sync --extra postgres`."
        ) from exc

    with psycopg.connect(connection_string) as conn:
        if not _column_exists_postgres(conn, "evaluation_runs", "tracker_trace_ids"):
            logger.info("Adding tracker_trace_ids column to evaluation_runs (Postgres).")
            conn.execute("ALTER TABLE evaluation_runs ADD COLUMN tracker_trace_ids JSONB")
            conn.commit()

        if not _column_exists_postgres(conn, "evaluation_runs", "langfuse_trace_id"):
            logger.info("No legacy langfuse_trace_id column; nothing to backfill.")
            return 0

        # Use jsonb_build_object so we don't string-concat user data into
        # a JSON literal. ``tracker_trace_ids IS NULL`` covers the NULL
        # case; ``tracker_trace_ids = '{}'::jsonb`` covers an empty dict
        # written by an earlier partial migration.
        result = conn.execute(
            """
            UPDATE evaluation_runs
            SET tracker_trace_ids = jsonb_build_object('langfuse', langfuse_trace_id)
            WHERE langfuse_trace_id IS NOT NULL
              AND langfuse_trace_id <> ''
              AND (tracker_trace_ids IS NULL OR tracker_trace_ids = '{}'::jsonb)
            """
        )
        updated = result.rowcount or 0
        conn.commit()
        logger.info("Postgres: backfilled %d row(s).", updated)
        return updated


def _detect_backend(db_arg: str | None) -> tuple[str, str]:
    """Return ``(backend, target)`` where backend is 'sqlite' or 'postgres'."""
    if db_arg:
        if db_arg.startswith("sqlite:"):
            return "sqlite", db_arg[len("sqlite:") :]
        if db_arg.startswith("postgres:") or db_arg.startswith("postgresql:"):
            # Strip the scheme prefix; what follows is a libpq-style
            # connection string ("host=... dbname=... user=...").
            _, _, conn = db_arg.partition(":")
            return "postgres", conn
        raise ValueError(
            "Unrecognized --db prefix. Use 'sqlite:<path>' or 'postgres:<conn>'."
        )

    try:
        from evalvault.config.settings import get_settings
    except ImportError:  # pragma: no cover - bootstrap fallback
        return "sqlite", "data/db/evalvault.db"

    settings = get_settings()
    if getattr(settings, "postgres_connection_string", None):
        return "postgres", settings.postgres_connection_string
    if getattr(settings, "postgres_host", None):
        # Build a libpq-style connection string from individual settings.
        parts = [
            f"host={settings.postgres_host}",
            f"port={settings.postgres_port}",
            f"dbname={settings.postgres_database}",
        ]
        if settings.postgres_user:
            parts.append(f"user={settings.postgres_user}")
        if settings.postgres_password:
            parts.append(f"password={settings.postgres_password}")
        return "postgres", " ".join(parts)
    return "sqlite", "data/db/evalvault.db"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill EvaluationRun rows from the legacy langfuse_trace_id "
            "column into the new tracker_trace_ids JSON column."
        )
    )
    parser.add_argument(
        "--db",
        help=(
            "Override the target DB. Format: 'sqlite:<path>' or "
            "'postgres:<libpq-conn>'. Defaults to env-driven detection."
        ),
        default=None,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug-level logging.",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    backend, target = _detect_backend(args.db)
    logger.info("Running migration against %s backend: %s", backend, target)
    if backend == "sqlite":
        migrate_sqlite(target)
    elif backend == "postgres":
        migrate_postgres(target)
    else:  # pragma: no cover - defensive
        logger.error("Unknown backend: %s", backend)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
