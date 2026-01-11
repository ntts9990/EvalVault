"""SQLite storage adapter for benchmark run persistence.

Implements BenchmarkStoragePort for persisting benchmark evaluation results.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from evalvault.domain.entities.benchmark_run import (
    BenchmarkRun,
    BenchmarkStatus,
    BenchmarkTaskScore,
    BenchmarkType,
)
from evalvault.ports.outbound.benchmark_port import BenchmarkStoragePort


class SQLiteBenchmarkStorageAdapter(BenchmarkStoragePort):
    """SQLite-based storage adapter for benchmark runs.

    Implements BenchmarkStoragePort interface for local persistence.
    Follows existing SQLite adapter patterns in the codebase.
    """

    def __init__(self, db_path: str | Path = "data/db/evalvault.db"):
        """Initialize SQLite benchmark storage adapter.

        Args:
            db_path: Path to SQLite database file (default: data/db/evalvault.db)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Ensure benchmark_runs table exists."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS benchmark_runs (
                    run_id TEXT PRIMARY KEY,
                    benchmark_type TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    backend TEXT NOT NULL,
                    tasks TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    task_scores TEXT,
                    overall_accuracy REAL,
                    num_fewshot INTEGER DEFAULT 0,
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP,
                    duration_seconds REAL DEFAULT 0.0,
                    error_message TEXT,
                    phoenix_trace_id TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_benchmark_runs_type
                ON benchmark_runs(benchmark_type)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_benchmark_runs_model
                ON benchmark_runs(model_name)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_benchmark_runs_created_at
                ON benchmark_runs(created_at DESC)
            """
            )
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Create a DB-API connection with the expected options."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save_benchmark_run(self, run: BenchmarkRun) -> str:
        """Save a benchmark run to storage.

        Args:
            run: BenchmarkRun entity to save

        Returns:
            Saved run_id
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO benchmark_runs (
                    run_id, benchmark_type, model_name, backend, tasks,
                    status, task_scores, overall_accuracy, num_fewshot,
                    started_at, finished_at, duration_seconds,
                    error_message, phoenix_trace_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._serialize_run(run),
            )
            conn.commit()
        return run.run_id

    def get_benchmark_run(self, run_id: str) -> BenchmarkRun:
        """Retrieve a benchmark run by ID.

        Args:
            run_id: Run identifier

        Returns:
            BenchmarkRun entity

        Raises:
            KeyError: If run not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT run_id, benchmark_type, model_name, backend, tasks,
                       status, task_scores, overall_accuracy, num_fewshot,
                       started_at, finished_at, duration_seconds,
                       error_message, phoenix_trace_id, metadata
                FROM benchmark_runs
                WHERE run_id = ?
                """,
                (run_id,),
            )
            row = cursor.fetchone()

        if not row:
            raise KeyError(f"Benchmark run not found: {run_id}")

        return self._deserialize_run(row)

    def list_benchmark_runs(
        self,
        benchmark_type: str | None = None,
        model_name: str | None = None,
        limit: int = 100,
    ) -> list[BenchmarkRun]:
        """List benchmark runs with optional filtering.

        Args:
            benchmark_type: Filter by benchmark type
            model_name: Filter by model name
            limit: Maximum number of results

        Returns:
            List of BenchmarkRun entities
        """
        query = """
            SELECT run_id, benchmark_type, model_name, backend, tasks,
                   status, task_scores, overall_accuracy, num_fewshot,
                   started_at, finished_at, duration_seconds,
                   error_message, phoenix_trace_id, metadata
            FROM benchmark_runs
            WHERE 1=1
        """
        params: list[Any] = []

        if benchmark_type:
            query += " AND benchmark_type = ?"
            params.append(benchmark_type)

        if model_name:
            query += " AND model_name = ?"
            params.append(model_name)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [self._deserialize_run(row) for row in rows]

    def delete_benchmark_run(self, run_id: str) -> bool:
        """Delete a benchmark run.

        Args:
            run_id: Run identifier

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM benchmark_runs WHERE run_id = ?",
                (run_id,),
            )
            deleted = cursor.rowcount > 0
            conn.commit()
        return deleted

    def _serialize_run(self, run: BenchmarkRun) -> tuple[Any, ...]:
        """Serialize BenchmarkRun to database row parameters."""
        task_scores_json = json.dumps(
            [
                {
                    "task_name": ts.task_name,
                    "accuracy": ts.accuracy,
                    "num_samples": ts.num_samples,
                    "metrics": ts.metrics,
                    "version": ts.version,
                }
                for ts in run.task_scores
            ],
            ensure_ascii=False,
        )

        return (
            run.run_id,
            run.benchmark_type.value,
            run.model_name,
            run.backend,
            json.dumps(run.tasks, ensure_ascii=False),
            run.status.value,
            task_scores_json,
            run.overall_accuracy,
            run.num_fewshot,
            run.started_at.isoformat() if run.started_at else None,
            run.finished_at.isoformat() if run.finished_at else None,
            run.duration_seconds,
            run.error_message,
            run.phoenix_trace_id,
            json.dumps(run.metadata, ensure_ascii=False) if run.metadata else None,
        )

    def _deserialize_run(self, row: sqlite3.Row) -> BenchmarkRun:
        """Deserialize database row to BenchmarkRun entity."""
        # Parse task scores
        task_scores_raw = row["task_scores"]
        task_scores: list[BenchmarkTaskScore] = []
        if task_scores_raw:
            for ts_data in json.loads(task_scores_raw):
                task_scores.append(
                    BenchmarkTaskScore(
                        task_name=ts_data["task_name"],
                        accuracy=ts_data["accuracy"],
                        num_samples=ts_data["num_samples"],
                        metrics=ts_data.get("metrics", {}),
                        version=ts_data.get("version", "0"),
                    )
                )

        # Parse tasks
        tasks_raw = row["tasks"]
        tasks = json.loads(tasks_raw) if tasks_raw else []

        # Parse metadata
        metadata_raw = row["metadata"]
        metadata = json.loads(metadata_raw) if metadata_raw else {}

        # Parse timestamps
        started_at = row["started_at"]
        finished_at = row["finished_at"]

        return BenchmarkRun(
            run_id=row["run_id"],
            benchmark_type=BenchmarkType(row["benchmark_type"]),
            model_name=row["model_name"],
            backend=row["backend"],
            tasks=tasks,
            status=BenchmarkStatus(row["status"]),
            task_scores=task_scores,
            overall_accuracy=row["overall_accuracy"],
            num_fewshot=row["num_fewshot"] or 0,
            started_at=datetime.fromisoformat(started_at) if started_at else datetime.now(),
            finished_at=datetime.fromisoformat(finished_at) if finished_at else None,
            duration_seconds=row["duration_seconds"] or 0.0,
            error_message=row["error_message"],
            phoenix_trace_id=row["phoenix_trace_id"],
            metadata=metadata,
        )
