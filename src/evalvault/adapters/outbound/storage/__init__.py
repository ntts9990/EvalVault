"""Storage adapters for evaluation results."""

from evalvault.adapters.outbound.storage.benchmark_storage_adapter import (
    SQLiteBenchmarkStorageAdapter,
)
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter

try:
    from evalvault.adapters.outbound.storage.postgres_adapter import (
        PostgreSQLStorageAdapter,
    )

    __all__ = [
        "SQLiteStorageAdapter",
        "PostgreSQLStorageAdapter",
        "SQLiteBenchmarkStorageAdapter",
    ]
except ImportError:
    # psycopg not installed
    __all__ = ["SQLiteStorageAdapter", "SQLiteBenchmarkStorageAdapter"]
