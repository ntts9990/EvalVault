"""PostgreSQL storage adapter for evaluation results."""

import json
import uuid
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from evalvault.adapters.outbound.storage.base_sql import BaseSQLStorageAdapter, SQLQueries
from evalvault.domain.entities.analysis import (
    AnalysisType,
    CorrelationInsight,
    KeywordInfo,
    LowPerformerInfo,
    MetricStats,
    NLPAnalysis,
    QuestionType,
    QuestionTypeStats,
    StatisticalAnalysis,
    TextStats,
)
from evalvault.domain.entities.experiment import Experiment


class PostgreSQLStorageAdapter(BaseSQLStorageAdapter):
    """PostgreSQL 기반 평가 결과 저장 어댑터.

    Implements StoragePort using PostgreSQL database for production persistence.
    Supports advanced features like JSONB, UUID, and better concurrency.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "evalvault",
        user: str = "postgres",
        password: str = "",
        connection_string: str | None = None,
    ):
        """Initialize PostgreSQL storage adapter.

        Args:
            host: PostgreSQL server host (default: localhost)
            port: PostgreSQL server port (default: 5432)
            database: Database name (default: evalvault)
            user: Database user (default: postgres)
            password: Database password
            connection_string: Full connection string (overrides other params if provided)
        """
        super().__init__(
            SQLQueries(
                placeholder="%s",
                metric_name_column="name",
                test_case_returning_clause="RETURNING id",
            )
        )
        if connection_string:
            self._conn_string = connection_string
        else:
            self._conn_string = (
                f"host={host} port={port} dbname={database} user={user} password={password}"
            )
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema from postgres_schema.sql."""
        schema_path = Path(__file__).parent / "postgres_schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        with psycopg.connect(self._conn_string) as conn:
            conn.execute(schema_sql)
            conn.commit()

    def _connect(self) -> psycopg.Connection:
        """Get a database connection with dict row factory."""
        return psycopg.connect(self._conn_string, row_factory=dict_row)

    def _fetch_lastrowid(self, cursor) -> int:
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("Failed to fetch inserted row id")
        return row["id"]

    @contextmanager
    def _get_connection(self):
        with psycopg.connect(self._conn_string, row_factory=dict_row) as conn:
            yield conn

    # Experiment 관련 메서드

    def save_experiment(self, experiment: Experiment) -> str:
        """실험을 저장합니다.

        Args:
            experiment: 저장할 실험

        Returns:
            저장된 experiment의 ID
        """
        with self._get_connection() as conn:
            # Insert experiment
            conn.execute(
                """
                INSERT INTO experiments (
                    experiment_id, name, description, hypothesis,
                    created_at, status, metrics_to_compare, conclusion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    experiment.experiment_id,
                    experiment.name,
                    experiment.description,
                    experiment.hypothesis,
                    experiment.created_at,
                    experiment.status,
                    json.dumps(experiment.metrics_to_compare),
                    experiment.conclusion,
                ),
            )

            # Insert experiment groups
            for group in experiment.groups:
                conn.execute(
                    """
                    INSERT INTO experiment_groups (
                        experiment_id, name, description, run_ids
                    ) VALUES (%s, %s, %s, %s)
                    """,
                    (
                        experiment.experiment_id,
                        group.name,
                        group.description,
                        json.dumps(group.run_ids),
                    ),
                )

            conn.commit()
            return experiment.experiment_id

    def get_experiment(self, experiment_id: str) -> Experiment:
        """실험을 조회합니다.

        Args:
            experiment_id: 조회할 실험 ID

        Returns:
            Experiment 객체

        Raises:
            KeyError: 실험을 찾을 수 없는 경우
        """
        from evalvault.domain.entities.experiment import ExperimentGroup

        with self._get_connection() as conn:
            # Fetch experiment
            cursor = conn.execute(
                """
                SELECT experiment_id, name, description, hypothesis,
                       created_at, status, metrics_to_compare, conclusion
                FROM experiments
                WHERE experiment_id = %s
                """,
                (experiment_id,),
            )
            exp_row = cursor.fetchone()

            if not exp_row:
                raise KeyError(f"Experiment not found: {experiment_id}")

            # Fetch groups
            cursor = conn.execute(
                """
                SELECT name, description, run_ids
                FROM experiment_groups
                WHERE experiment_id = %s
                ORDER BY id
                """,
                (experiment_id,),
            )
            group_rows = cursor.fetchall()

            # Reconstruct groups
            groups = [
                ExperimentGroup(
                    name=g["name"],
                    description=g["description"] or "",
                    run_ids=json.loads(g["run_ids"]) if g["run_ids"] else [],
                )
                for g in group_rows
            ]

            # Reconstruct Experiment
            return Experiment(
                experiment_id=exp_row["experiment_id"],
                name=exp_row["name"],
                description=exp_row["description"] or "",
                hypothesis=exp_row["hypothesis"] or "",
                created_at=exp_row["created_at"],
                status=exp_row["status"],
                metrics_to_compare=(
                    json.loads(exp_row["metrics_to_compare"])
                    if exp_row["metrics_to_compare"]
                    else []
                ),
                conclusion=exp_row["conclusion"],
                groups=groups,
            )

    def list_experiments(
        self,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Experiment]:
        """실험 목록을 조회합니다.

        Args:
            status: 필터링할 상태 (선택)
            limit: 최대 조회 개수

        Returns:
            Experiment 객체 리스트
        """
        with self._get_connection() as conn:
            # Build query with optional filter
            query = "SELECT experiment_id FROM experiments WHERE 1=1"
            params = []

            if status:
                query += " AND status = %s"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)

            cursor = conn.execute(query, params)
            exp_ids = [row["experiment_id"] for row in cursor.fetchall()]

            # Fetch full experiments
            return [self.get_experiment(exp_id) for exp_id in exp_ids]

    def update_experiment(self, experiment: Experiment) -> None:
        """실험을 업데이트합니다.

        Args:
            experiment: 업데이트할 실험
        """
        with self._get_connection() as conn:
            # Update experiment
            conn.execute(
                """
                UPDATE experiments SET
                    name = %s,
                    description = %s,
                    hypothesis = %s,
                    status = %s,
                    metrics_to_compare = %s,
                    conclusion = %s
                WHERE experiment_id = %s
                """,
                (
                    experiment.name,
                    experiment.description,
                    experiment.hypothesis,
                    experiment.status,
                    json.dumps(experiment.metrics_to_compare),
                    experiment.conclusion,
                    experiment.experiment_id,
                ),
            )

            # Delete existing groups and re-insert
            conn.execute(
                "DELETE FROM experiment_groups WHERE experiment_id = %s",
                (experiment.experiment_id,),
            )

            for group in experiment.groups:
                conn.execute(
                    """
                    INSERT INTO experiment_groups (
                        experiment_id, name, description, run_ids
                    ) VALUES (%s, %s, %s, %s)
                    """,
                    (
                        experiment.experiment_id,
                        group.name,
                        group.description,
                        json.dumps(group.run_ids),
                    ),
                )

            conn.commit()

    # Analysis 관련 메서드

    def save_analysis(self, analysis: StatisticalAnalysis) -> str:
        """분석 결과를 저장합니다."""
        result_data = self._serialize_analysis(analysis)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO analysis_results (
                    analysis_id, run_id, analysis_type, result_data, created_at
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (analysis_id) DO UPDATE SET
                    run_id = EXCLUDED.run_id,
                    analysis_type = EXCLUDED.analysis_type,
                    result_data = EXCLUDED.result_data,
                    created_at = EXCLUDED.created_at
                """,
                (
                    analysis.analysis_id,
                    analysis.run_id,
                    analysis.analysis_type.value,
                    json.dumps(result_data, ensure_ascii=False),
                    analysis.created_at,
                ),
            )
            conn.commit()
        return analysis.analysis_id

    def get_analysis(self, analysis_id: str) -> StatisticalAnalysis:
        """분석 결과를 조회합니다."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT analysis_id, run_id, analysis_type, result_data, created_at
                FROM analysis_results
                WHERE analysis_id = %s
                """,
                (analysis_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"Analysis not found: {analysis_id}")

            result_data = self._ensure_json(row["result_data"])
            return self._deserialize_analysis(
                analysis_id=row["analysis_id"],
                run_id=row["run_id"],
                analysis_type=row["analysis_type"],
                result_data=result_data,
                created_at=row["created_at"],
            )

    def get_analysis_by_run(
        self,
        run_id: str,
        analysis_type: str | None = None,
    ) -> list[StatisticalAnalysis]:
        """특정 실행의 분석 결과를 조회합니다."""
        with self._get_connection() as conn:
            query = """
                SELECT analysis_id, run_id, analysis_type, result_data, created_at
                FROM analysis_results
                WHERE run_id = %s
            """
            params: list[Any] = [run_id]

            if analysis_type:
                query += " AND analysis_type = %s"
                params.append(analysis_type)

            query += " ORDER BY created_at DESC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [
            self._deserialize_analysis(
                analysis_id=row["analysis_id"],
                run_id=row["run_id"],
                analysis_type=row["analysis_type"],
                result_data=self._ensure_json(row["result_data"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def delete_analysis(self, analysis_id: str) -> bool:
        """분석 결과를 삭제합니다."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM analysis_results WHERE analysis_id = %s",
                (analysis_id,),
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    def save_nlp_analysis(self, analysis: NLPAnalysis) -> str:
        """NLP 분석 결과를 저장합니다."""
        analysis_id = f"nlp-{analysis.run_id}-{uuid.uuid4().hex[:8]}"
        result_data = self._serialize_nlp_analysis(analysis)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO analysis_results (
                    analysis_id, run_id, analysis_type, result_data, created_at
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (analysis_id) DO UPDATE SET
                    result_data = EXCLUDED.result_data,
                    created_at = EXCLUDED.created_at
                """,
                (
                    analysis_id,
                    analysis.run_id,
                    AnalysisType.NLP.value,
                    json.dumps(result_data, ensure_ascii=False),
                    datetime.now(UTC),
                ),
            )
            conn.commit()
        return analysis_id

    def get_nlp_analysis(self, analysis_id: str) -> NLPAnalysis:
        """NLP 분석 결과를 조회합니다."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT analysis_id, run_id, result_data
                FROM analysis_results
                WHERE analysis_id = %s AND analysis_type = %s
                """,
                (analysis_id, AnalysisType.NLP.value),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"NLP Analysis not found: {analysis_id}")

            return self._deserialize_nlp_analysis(
                row["run_id"], self._ensure_json(row["result_data"])
            )

    def get_nlp_analysis_by_run(self, run_id: str) -> NLPAnalysis | None:
        """특정 실행의 NLP 분석 결과를 조회합니다."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT result_data
                FROM analysis_results
                WHERE run_id = %s AND analysis_type = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (run_id, AnalysisType.NLP.value),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._deserialize_nlp_analysis(run_id, self._ensure_json(row["result_data"]))

    def _serialize_analysis(self, analysis: StatisticalAnalysis) -> dict[str, Any]:
        """분석 결과를 JSON 직렬화 가능한 형태로 변환합니다."""
        return {
            "metrics_summary": {
                name: asdict(stats) for name, stats in analysis.metrics_summary.items()
            },
            "correlation_matrix": analysis.correlation_matrix,
            "correlation_metrics": analysis.correlation_metrics,
            "significant_correlations": [asdict(c) for c in analysis.significant_correlations],
            "low_performers": [asdict(lp) for lp in analysis.low_performers],
            "insights": analysis.insights,
            "overall_pass_rate": analysis.overall_pass_rate,
            "metric_pass_rates": analysis.metric_pass_rates,
        }

    def _deserialize_analysis(
        self,
        analysis_id: str,
        run_id: str,
        analysis_type: str,
        result_data: dict[str, Any],
        created_at: datetime,
    ) -> StatisticalAnalysis:
        """JSON 데이터를 StatisticalAnalysis로 역직렬화합니다."""
        metrics_summary = {
            name: MetricStats(**stats)
            for name, stats in result_data.get("metrics_summary", {}).items()
        }

        significant_correlations = [
            CorrelationInsight(**c) for c in result_data.get("significant_correlations", [])
        ]

        low_performers = [LowPerformerInfo(**lp) for lp in result_data.get("low_performers", [])]

        return StatisticalAnalysis(
            analysis_id=analysis_id,
            run_id=run_id,
            analysis_type=AnalysisType(analysis_type),
            created_at=created_at,
            metrics_summary=metrics_summary,
            correlation_matrix=result_data.get("correlation_matrix", []),
            correlation_metrics=result_data.get("correlation_metrics", []),
            significant_correlations=significant_correlations,
            low_performers=low_performers,
            insights=result_data.get("insights", []),
            overall_pass_rate=result_data.get("overall_pass_rate", 0.0),
            metric_pass_rates=result_data.get("metric_pass_rates", {}),
        )

    def _serialize_nlp_analysis(self, analysis: NLPAnalysis) -> dict[str, Any]:
        """NLP 분석 결과를 JSON 직렬화 가능한 형태로 변환합니다."""
        return {
            "run_id": analysis.run_id,
            "question_stats": asdict(analysis.question_stats) if analysis.question_stats else None,
            "answer_stats": asdict(analysis.answer_stats) if analysis.answer_stats else None,
            "context_stats": asdict(analysis.context_stats) if analysis.context_stats else None,
            "question_types": [
                {
                    "question_type": qt.question_type.value,
                    "count": qt.count,
                    "percentage": qt.percentage,
                    "avg_scores": qt.avg_scores,
                }
                for qt in analysis.question_types
            ],
            "top_keywords": [asdict(kw) for kw in analysis.top_keywords],
            "topic_clusters": [asdict(tc) for tc in getattr(analysis, "topic_clusters", [])],
            "insights": analysis.insights,
        }

    def _deserialize_nlp_analysis(
        self,
        run_id: str,
        result_data: dict[str, Any],
    ) -> NLPAnalysis:
        """JSON 데이터를 NLPAnalysis로 역직렬화합니다."""
        question_stats = (
            TextStats(**result_data["question_stats"])
            if result_data.get("question_stats")
            else None
        )
        answer_stats = (
            TextStats(**result_data["answer_stats"]) if result_data.get("answer_stats") else None
        )
        context_stats = (
            TextStats(**result_data["context_stats"]) if result_data.get("context_stats") else None
        )

        question_types = [
            QuestionTypeStats(
                question_type=QuestionType(qt["question_type"]),
                count=qt["count"],
                percentage=qt["percentage"],
                avg_scores=qt.get("avg_scores", {}),
            )
            for qt in result_data.get("question_types", [])
        ]

        top_keywords = [KeywordInfo(**kw) for kw in result_data.get("top_keywords", [])]

        analysis = NLPAnalysis(
            run_id=run_id,
            question_stats=question_stats,
            answer_stats=answer_stats,
            context_stats=context_stats,
            question_types=question_types,
            top_keywords=top_keywords,
            insights=result_data.get("insights", []),
        )
        if topic_clusters := result_data.get("topic_clusters"):
            analysis.topic_clusters = topic_clusters
        return analysis

    def _ensure_json(self, value: Any) -> dict[str, Any]:
        """JSONB 값을 dict로 변환."""
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            return json.loads(value)
        return dict(value or {})
