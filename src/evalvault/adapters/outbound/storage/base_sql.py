"""Shared SQL storage helpers for multiple adapters."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Sequence
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from evalvault.domain.entities import (
    EvaluationRun,
    FeedbackSummary,
    MetricScore,
    RunClusterMap,
    RunClusterMapInfo,
    SatisfactionFeedback,
    TestCaseResult,
)


class SQLQueries:
    """Generates SQL statements with adapter-specific placeholders."""

    def __init__(
        self,
        *,
        placeholder: str = "?",
        metric_name_column: str = "metric_name",
        test_case_returning_clause: str = "",
        feedback_returning_clause: str = "",
    ) -> None:
        self.placeholder = placeholder
        self.metric_name_column = metric_name_column
        self._test_case_returning = test_case_returning_clause
        self._feedback_returning = feedback_returning_clause

    def _values(self, count: int) -> str:
        return ", ".join([self.placeholder] * count)

    def insert_run(self) -> str:
        values = self._values(14)
        return f"""
        INSERT INTO evaluation_runs (
            run_id, dataset_name, dataset_version, model_name,
            started_at, finished_at, total_tokens, total_cost_usd,
            pass_rate, metrics_evaluated, thresholds, langfuse_trace_id,
            metadata, retrieval_metadata
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

    def insert_cluster_map(self) -> str:
        values = self._values(7)
        return f"""
        INSERT INTO run_cluster_maps (
            run_id, map_id, test_case_id, cluster_id, source, metadata, created_at
        ) VALUES ({values})
        """

    def insert_feedback(self) -> str:
        values = self._values(7)
        query = f"""
        INSERT INTO satisfaction_feedback (
            run_id, test_case_id, satisfaction_score, thumb_feedback, comment, rater_id, created_at
        ) VALUES ({values})
        """
        if self._feedback_returning:
            query = f"{query.strip()} {self._feedback_returning}"
        return query

    def select_feedback_by_run(self) -> str:
        return f"""
        SELECT id, run_id, test_case_id, satisfaction_score, thumb_feedback, comment, rater_id, created_at
        FROM satisfaction_feedback
        WHERE run_id = {self.placeholder}
        ORDER BY created_at DESC
        """

    def select_run(self) -> str:
        return f"""
        SELECT run_id, dataset_name, dataset_version, model_name,
               started_at, finished_at, total_tokens, total_cost_usd,
               pass_rate, metrics_evaluated, thresholds, langfuse_trace_id,
               metadata, retrieval_metadata
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

    def select_cluster_map(self) -> str:
        return f"""
        SELECT test_case_id, cluster_id, source, map_id, created_at, metadata
        FROM run_cluster_maps
        WHERE run_id = {self.placeholder} AND map_id = {self.placeholder}
        ORDER BY test_case_id
        """

    def select_cluster_map_latest(self) -> str:
        return f"""
        SELECT map_id, source, created_at
        FROM run_cluster_maps
        WHERE run_id = {self.placeholder}
        ORDER BY created_at DESC
        LIMIT 1
        """

    def select_cluster_map_sets(self) -> str:
        return f"""
        SELECT map_id, source, created_at, COUNT(*) AS item_count
        FROM run_cluster_maps
        WHERE run_id = {self.placeholder}
        GROUP BY map_id, source, created_at
        ORDER BY created_at DESC
        """

    def update_run_metadata(self) -> str:
        return f"""
        UPDATE evaluation_runs
        SET metadata = {self.placeholder}
        WHERE run_id = {self.placeholder}
        """

    def delete_run(self) -> str:
        return f"DELETE FROM evaluation_runs WHERE run_id = {self.placeholder}"

    def delete_cluster_map(self) -> str:
        return f"DELETE FROM run_cluster_maps WHERE run_id = {self.placeholder} AND map_id = {self.placeholder}"

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
                tracker_metadata=self._deserialize_json(run_row["metadata"]) or {},
                retrieval_metadata=self._deserialize_json(run_row["retrieval_metadata"]) or {},
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

    def update_run_metadata(self, run_id: str, metadata: dict[str, Any]) -> None:
        payload = self._serialize_json(metadata)
        with self._get_connection() as conn:
            self._execute(conn, self.queries.update_run_metadata(), (payload, run_id))
            conn.commit()

    def save_run_cluster_map(
        self,
        run_id: str,
        mapping: dict[str, str],
        source: str | None = None,
        map_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if not mapping:
            raise ValueError("Cluster map is empty")
        if map_id is None:
            from uuid import uuid4

            map_id = str(uuid4())
        created_at = self._serialize_datetime(datetime.now())
        metadata_payload = self._serialize_json(metadata)
        with self._get_connection() as conn:
            self._execute(conn, self.queries.delete_cluster_map(), (run_id, map_id))
            for test_case_id, cluster_id in mapping.items():
                self._execute(
                    conn,
                    self.queries.insert_cluster_map(),
                    (
                        run_id,
                        map_id,
                        test_case_id,
                        cluster_id,
                        source,
                        metadata_payload,
                        created_at,
                    ),
                )
            conn.commit()
        return map_id

    def get_run_cluster_map(self, run_id: str, map_id: str | None = None) -> RunClusterMap | None:
        with self._get_connection() as conn:
            source: str | None = None
            created_at: datetime | None = None
            metadata: dict[str, Any] | None = None
            if map_id is None:
                latest_row = self._execute(
                    conn, self.queries.select_cluster_map_latest(), (run_id,)
                ).fetchone()
                if not latest_row:
                    return None
                map_id = self._row_value(latest_row, "map_id")
                source = self._row_value(latest_row, "source")
                created_at = self._deserialize_datetime(self._row_value(latest_row, "created_at"))
                if map_id is None:
                    return None

            rows = self._execute(
                conn, self.queries.select_cluster_map(), (run_id, map_id)
            ).fetchall()
            if not rows:
                return None

            mapping: dict[str, str] = {}
            for row in rows:
                test_case_id = self._row_value(row, "test_case_id")
                cluster_id = self._row_value(row, "cluster_id")
                row_source = self._row_value(row, "source")
                row_created_at = self._row_value(row, "created_at")
                row_metadata = self._row_value(row, "metadata")
                if row_source and not source:
                    source = row_source
                if row_created_at and created_at is None:
                    created_at = self._deserialize_datetime(row_created_at)
                if metadata is None and row_metadata not in (None, ""):
                    metadata = self._deserialize_json(row_metadata)
                if test_case_id and cluster_id:
                    mapping[str(test_case_id)] = str(cluster_id)

            if not mapping:
                return None
            return RunClusterMap(
                map_id=str(map_id),
                mapping=mapping,
                source=source,
                created_at=created_at,
                metadata=metadata,
            )

    def list_run_cluster_maps(self, run_id: str) -> list[RunClusterMapInfo]:
        with self._get_connection() as conn:
            rows = self._execute(conn, self.queries.select_cluster_map_sets(), (run_id,)).fetchall()
            results: list[RunClusterMapInfo] = []
            for row in rows:
                results.append(
                    RunClusterMapInfo(
                        map_id=str(self._row_value(row, "map_id") or ""),
                        source=self._row_value(row, "source"),
                        created_at=self._deserialize_datetime(self._row_value(row, "created_at")),
                        item_count=int(self._row_value(row, "item_count") or 0),
                    )
                )
            return results

    def delete_run_cluster_map(self, run_id: str, map_id: str) -> int:
        with self._get_connection() as conn:
            cursor = self._execute(conn, self.queries.delete_cluster_map(), (run_id, map_id))
            deleted = cursor.rowcount if cursor.rowcount is not None else 0
            conn.commit()
            return deleted

    def save_feedback(self, feedback: SatisfactionFeedback) -> str:
        created_at = feedback.created_at or datetime.now()
        with self._get_connection() as conn:
            cursor = self._execute(
                conn,
                self.queries.insert_feedback(),
                (
                    feedback.run_id,
                    feedback.test_case_id,
                    feedback.satisfaction_score,
                    feedback.thumb_feedback,
                    feedback.comment,
                    feedback.rater_id,
                    self._serialize_datetime(created_at),
                ),
            )
            feedback_id = self._fetch_lastrowid(cursor)
            conn.commit()
            return str(feedback_id)

    def list_feedback(self, run_id: str) -> list[SatisfactionFeedback]:
        with self._get_connection() as conn:
            rows = self._execute(conn, self.queries.select_feedback_by_run(), (run_id,)).fetchall()
            return [self._row_to_feedback(row) for row in rows]

    def get_feedback_summary(self, run_id: str) -> FeedbackSummary:
        feedbacks = self.list_feedback(run_id)
        scores = [f.satisfaction_score for f in feedbacks if f.satisfaction_score is not None]
        thumbs = [f.thumb_feedback for f in feedbacks if f.thumb_feedback in {"up", "down"}]
        avg_score = sum(scores) / len(scores) if scores else None
        thumb_up_rate = None
        if thumbs:
            thumb_up_rate = thumbs.count("up") / len(thumbs)
        return FeedbackSummary(
            avg_satisfaction_score=avg_score,
            thumb_up_rate=thumb_up_rate,
            total_feedback=len(feedbacks),
        )

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
            self._serialize_json(run.tracker_metadata),
            self._serialize_json(run.retrieval_metadata),
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

    def _row_to_feedback(self, row) -> SatisfactionFeedback:
        feedback_id = self._row_value(row, "id")
        run_id = self._row_value(row, "run_id")
        test_case_id = self._row_value(row, "test_case_id")
        created_at = self._deserialize_datetime(self._row_value(row, "created_at"))
        return SatisfactionFeedback(
            feedback_id=str(feedback_id or ""),
            run_id=str(run_id or ""),
            test_case_id=str(test_case_id or ""),
            satisfaction_score=self._maybe_float(self._row_value(row, "satisfaction_score")),
            thumb_feedback=self._row_value(row, "thumb_feedback"),
            comment=self._row_value(row, "comment"),
            rater_id=self._row_value(row, "rater_id"),
            created_at=created_at,
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
