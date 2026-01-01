"""Shared SQL storage helpers for multiple adapters."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Sequence
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult


class SQLQueries:
    """Generates SQL statements with adapter-specific placeholders."""

    def __init__(
        self,
        *,
        placeholder: str = "?",
        metric_name_column: str = "metric_name",
        test_case_returning_clause: str = "",
    ) -> None:
        self.placeholder = placeholder
        self.metric_name_column = metric_name_column
        self._test_case_returning = test_case_returning_clause

    def _values(self, count: int) -> str:
        return ", ".join([self.placeholder] * count)

    def insert_run(self) -> str:
        values = self._values(12)
        return f"""
        INSERT INTO evaluation_runs (
            run_id, dataset_name, dataset_version, model_name,
            started_at, finished_at, total_tokens, total_cost_usd,
            pass_rate, metrics_evaluated, thresholds, langfuse_trace_id
        ) VALUES ({values})
        """

    def insert_test_case(self) -> str:
        values = self._values(12)
        query = f"""
        INSERT INTO test_case_results (
            run_id, test_case_id, tokens_used, latency_ms,
            cost_usd, trace_id, started_at, finished_at,
            question, answer, contexts, ground_truth
        ) VALUES ({values})
        """
        if self._test_case_returning:
            query = f"{query.strip()} {self._test_case_returning}"
        return query

    def insert_metric_score(self) -> str:
        values = self._values(5)
        return f"""
        INSERT INTO metric_scores (
            result_id, {self.metric_name_column}, score, threshold, reason
        ) VALUES ({values})
        """

    def select_run(self) -> str:
        return f"""
        SELECT run_id, dataset_name, dataset_version, model_name,
               started_at, finished_at, total_tokens, total_cost_usd,
               pass_rate, metrics_evaluated, thresholds, langfuse_trace_id
        FROM evaluation_runs
        WHERE run_id = {self.placeholder}
        """

    def select_test_case_results(self) -> str:
        return f"""
        SELECT id, test_case_id, tokens_used, latency_ms, cost_usd,
               trace_id, started_at, finished_at, question, answer,
               contexts, ground_truth
        FROM test_case_results
        WHERE run_id = {self.placeholder}
        ORDER BY id
        """

    def select_metric_scores(self) -> str:
        return f"""
        SELECT {self.metric_name_column} AS metric_name, score, threshold, reason
        FROM metric_scores
        WHERE result_id = {self.placeholder}
        ORDER BY id
        """

    def delete_run(self) -> str:
        return f"DELETE FROM evaluation_runs WHERE run_id = {self.placeholder}"

    def list_runs_base(self) -> str:
        return "SELECT run_id FROM evaluation_runs WHERE 1=1"

    def list_runs_ordering(self) -> str:
        return f" ORDER BY started_at DESC LIMIT {self.placeholder}"


class BaseSQLStorageAdapter(ABC):
    """Shared serialization and SQL helpers for DB-API based adapters."""

    def __init__(self, queries: SQLQueries) -> None:
        self.queries = queries

    # Connection helpers -------------------------------------------------

    @abstractmethod
    def _connect(self):
        """Return a new DB-API compatible connection."""

    @contextmanager
    def _get_connection(self):
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    def _fetch_lastrowid(self, cursor) -> int:
        return cursor.lastrowid

    def _execute(self, conn, query: str, params: Sequence[Any] | None = None):
        if params is None:
            params = ()
        return conn.execute(query, tuple(params))

    # CRUD helpers -------------------------------------------------------

    def save_run(self, run: EvaluationRun) -> str:
        with self._get_connection() as conn:
            self._execute(conn, self.queries.insert_run(), self._run_params(run))

            for result in run.results:
                result_id = self._insert_test_case(conn, run.run_id, result)
                for metric in result.metrics:
                    self._execute(
                        conn,
                        self.queries.insert_metric_score(),
                        self._metric_params(result_id, metric),
                    )

            conn.commit()
            return run.run_id

    def _insert_test_case(self, conn, run_id: str, result: TestCaseResult) -> int:
        cursor = self._execute(
            conn,
            self.queries.insert_test_case(),
            self._test_case_params(run_id, result),
        )
        return self._fetch_lastrowid(cursor)

    def get_run(self, run_id: str) -> EvaluationRun:
        with self._get_connection() as conn:
            cursor = self._execute(conn, self.queries.select_run(), (run_id,))
            run_row = cursor.fetchone()
            if not run_row:
                raise KeyError(f"Run not found: {run_id}")

            result_rows = self._execute(
                conn, self.queries.select_test_case_results(), (run_id,)
            ).fetchall()

            results = [self._row_to_test_case(conn, row) for row in result_rows]

            return EvaluationRun(
                run_id=run_row["run_id"],
                dataset_name=run_row["dataset_name"],
                dataset_version=run_row["dataset_version"],
                model_name=run_row["model_name"],
                started_at=self._deserialize_datetime(run_row["started_at"]),
                finished_at=self._deserialize_datetime(run_row["finished_at"]),
                total_tokens=run_row["total_tokens"],
                total_cost_usd=self._maybe_float(run_row["total_cost_usd"]),
                results=results,
                metrics_evaluated=self._deserialize_json(run_row["metrics_evaluated"]) or [],
                thresholds=self._deserialize_json(run_row["thresholds"]) or {},
                langfuse_trace_id=run_row["langfuse_trace_id"],
            )

    def list_runs(
        self,
        limit: int = 100,
        dataset_name: str | None = None,
        model_name: str | None = None,
    ) -> list[EvaluationRun]:
        with self._get_connection() as conn:
            query = self.queries.list_runs_base()
            params: list[Any] = []

            if dataset_name:
                query += f" AND dataset_name = {self.queries.placeholder}"
                params.append(dataset_name)

            if model_name:
                query += f" AND model_name = {self.queries.placeholder}"
                params.append(model_name)

            query += self.queries.list_runs_ordering()
            params.append(limit)

            cursor = self._execute(conn, query, params)
            run_ids = [row["run_id"] for row in cursor.fetchall()]

        return [self.get_run(run_id) for run_id in run_ids]

    def delete_run(self, run_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = self._execute(conn, self.queries.delete_run(), (run_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    # Serialization helpers --------------------------------------------

    def _run_params(self, run: EvaluationRun) -> Sequence[Any]:
        return (
            run.run_id,
            run.dataset_name,
            run.dataset_version,
            run.model_name,
            self._serialize_datetime(run.started_at),
            self._serialize_datetime(run.finished_at),
            run.total_tokens,
            run.total_cost_usd,
            run.pass_rate,
            self._serialize_json(run.metrics_evaluated),
            self._serialize_json(run.thresholds),
            run.langfuse_trace_id,
        )

    def _test_case_params(self, run_id: str, result: TestCaseResult) -> Sequence[Any]:
        return (
            run_id,
            result.test_case_id,
            result.tokens_used,
            result.latency_ms,
            result.cost_usd,
            result.trace_id,
            self._serialize_datetime(result.started_at),
            self._serialize_datetime(result.finished_at),
            result.question,
            result.answer,
            self._serialize_contexts(result.contexts),
            result.ground_truth,
        )

    def _metric_params(self, result_id: int, metric: MetricScore) -> Sequence[Any]:
        return (
            result_id,
            metric.name,
            metric.score,
            metric.threshold,
            metric.reason,
        )

    def _row_to_test_case(self, conn, row) -> TestCaseResult:
        result_id = row["id"]
        metrics = self._fetch_metric_scores(conn, result_id)
        return TestCaseResult(
            test_case_id=row["test_case_id"],
            metrics=metrics,
            tokens_used=row["tokens_used"],
            latency_ms=row["latency_ms"],
            cost_usd=self._maybe_float(row["cost_usd"]),
            trace_id=row["trace_id"],
            started_at=self._deserialize_datetime(row["started_at"]),
            finished_at=self._deserialize_datetime(row["finished_at"]),
            question=row["question"],
            answer=row["answer"],
            contexts=self._deserialize_contexts(row["contexts"]),
            ground_truth=row["ground_truth"],
        )

    def _fetch_metric_scores(self, conn, result_id: int) -> list[MetricScore]:
        rows = self._execute(conn, self.queries.select_metric_scores(), (result_id,)).fetchall()
        metric_column = self.queries.metric_name_column
        return [
            MetricScore(
                name=self._resolve_metric_name(row, metric_column),
                score=self._maybe_float(self._row_value(row, "score")),
                threshold=self._maybe_float(self._row_value(row, "threshold")),
                reason=self._row_value(row, "reason"),
            )
            for row in rows
        ]

    def _resolve_metric_name(self, row, fallback_column: str) -> str:
        name = self._row_value(row, "metric_name")
        if name is None and fallback_column != "metric_name":
            name = self._row_value(row, fallback_column)
        return name or ""

    def _serialize_datetime(self, value: datetime | None) -> str | None:
        return value.isoformat() if value else None

    def _deserialize_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value)

    def _serialize_json(self, value: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False)

    def _deserialize_json(self, value: Any) -> Any:
        if value in (None, ""):
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value

    def _serialize_contexts(self, contexts: list[str] | None) -> str | None:
        if not contexts:
            return None
        return json.dumps(contexts, ensure_ascii=False)

    def _deserialize_contexts(self, value: Any) -> list[str] | None:
        data = self._deserialize_json(value)
        if data is None:
            return None
        if isinstance(data, list):
            return data
        return [data]

    def _maybe_float(self, value: Any) -> float | None:
        if value is None:
            return None
        return float(value)

    def _row_value(self, row: Any, key: str) -> Any:
        if isinstance(row, dict):
            return row.get(key)
        try:
            return row[key]
        except (KeyError, TypeError, IndexError):
            return None
