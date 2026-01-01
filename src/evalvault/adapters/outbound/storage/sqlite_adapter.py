"""SQLite storage adapter for evaluation results."""

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

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
    TopicCluster,
)
from evalvault.domain.entities.experiment import Experiment, ExperimentGroup


class SQLiteStorageAdapter(BaseSQLStorageAdapter):
    """SQLite 기반 평가 결과 저장 어댑터.

    Implements StoragePort using SQLite database for local persistence.
    """

    def __init__(self, db_path: str | Path = "evalvault.db"):
        """Initialize SQLite storage adapter.

        Args:
            db_path: Path to SQLite database file (default: evalvault.db)
        """
        super().__init__(SQLQueries())
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema from schema.sql."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()

    def _connect(self) -> sqlite3.Connection:
        """Create a DB-API connection with the expected options."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # Experiment 관련 메서드

    def save_experiment(self, experiment: Experiment) -> str:
        """실험을 저장합니다.

        Args:
            experiment: 저장할 실험

        Returns:
            저장된 experiment의 ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Insert or replace experiment
            cursor.execute(
                """
                INSERT OR REPLACE INTO experiments (
                    experiment_id, name, description, hypothesis, status,
                    metrics_to_compare, conclusion, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment.experiment_id,
                    experiment.name,
                    experiment.description,
                    experiment.hypothesis,
                    experiment.status,
                    json.dumps(experiment.metrics_to_compare),
                    experiment.conclusion,
                    experiment.created_at.isoformat(),
                    datetime.now().isoformat(),
                ),
            )

            # Delete existing groups and re-insert
            cursor.execute(
                "DELETE FROM experiment_groups WHERE experiment_id = ?",
                (experiment.experiment_id,),
            )

            # Insert groups
            for group in experiment.groups:
                cursor.execute(
                    """
                    INSERT INTO experiment_groups (experiment_id, name, description)
                    VALUES (?, ?, ?)
                    """,
                    (experiment.experiment_id, group.name, group.description),
                )
                group_id = cursor.lastrowid

                # Insert group runs
                for run_id in group.run_ids:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO experiment_group_runs (group_id, run_id)
                        VALUES (?, ?)
                        """,
                        (group_id, run_id),
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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Fetch experiment
            cursor.execute(
                """
                SELECT experiment_id, name, description, hypothesis, status,
                       metrics_to_compare, conclusion, created_at
                FROM experiments
                WHERE experiment_id = ?
                """,
                (experiment_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"Experiment not found: {experiment_id}")

            # Fetch groups
            cursor.execute(
                """
                SELECT id, name, description
                FROM experiment_groups
                WHERE experiment_id = ?
                ORDER BY id
                """,
                (experiment_id,),
            )
            group_rows = cursor.fetchall()

            groups = []
            for group_row in group_rows:
                group_id = group_row[0]

                # Fetch run IDs for this group
                cursor.execute(
                    """
                    SELECT run_id FROM experiment_group_runs
                    WHERE group_id = ?
                    ORDER BY added_at
                    """,
                    (group_id,),
                )
                run_ids = [r[0] for r in cursor.fetchall()]

                groups.append(
                    ExperimentGroup(
                        name=group_row[1],
                        description=group_row[2] or "",
                        run_ids=run_ids,
                    )
                )

            return Experiment(
                experiment_id=row[0],
                name=row[1],
                description=row[2] or "",
                hypothesis=row[3] or "",
                status=row[4],
                metrics_to_compare=json.loads(row[5]) if row[5] else [],
                conclusion=row[6],
                created_at=datetime.fromisoformat(row[7]),
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
            cursor = conn.cursor()
            query = "SELECT experiment_id FROM experiments WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            experiment_ids = [row[0] for row in cursor.fetchall()]

            return [self.get_experiment(exp_id) for exp_id in experiment_ids]

    def update_experiment(self, experiment: Experiment) -> None:
        """실험을 업데이트합니다.

        Args:
            experiment: 업데이트할 실험
        """
        self.save_experiment(experiment)

    # Analysis 관련 메서드

    def save_analysis(self, analysis: StatisticalAnalysis) -> str:
        """분석 결과를 저장합니다.

        Args:
            analysis: 저장할 분석 결과

        Returns:
            저장된 analysis의 ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Serialize analysis to JSON
            result_data = self._serialize_analysis(analysis)

            cursor.execute(
                """
                INSERT OR REPLACE INTO analysis_results (
                    analysis_id, run_id, analysis_type, result_data, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    analysis.analysis_id,
                    analysis.run_id,
                    analysis.analysis_type.value,
                    json.dumps(result_data, ensure_ascii=False),
                    analysis.created_at.isoformat(),
                ),
            )

            conn.commit()
            return analysis.analysis_id

    def get_analysis(self, analysis_id: str) -> StatisticalAnalysis:
        """분석 결과를 조회합니다.

        Args:
            analysis_id: 조회할 분석 ID

        Returns:
            StatisticalAnalysis 객체

        Raises:
            KeyError: 분석을 찾을 수 없는 경우
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT analysis_id, run_id, analysis_type, result_data, created_at
                FROM analysis_results
                WHERE analysis_id = ?
                """,
                (analysis_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"Analysis not found: {analysis_id}")

            result_data = json.loads(row[3])
            return self._deserialize_analysis(
                analysis_id=row[0],
                run_id=row[1],
                analysis_type=row[2],
                result_data=result_data,
                created_at=row[4],
            )

    def get_analysis_by_run(
        self,
        run_id: str,
        analysis_type: str | None = None,
    ) -> list[StatisticalAnalysis]:
        """특정 실행의 분석 결과를 조회합니다.

        Args:
            run_id: 실행 ID
            analysis_type: 분석 유형 필터 (선택)

        Returns:
            StatisticalAnalysis 리스트
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT analysis_id, run_id, analysis_type, result_data, created_at
                FROM analysis_results
                WHERE run_id = ?
            """
            params: list[Any] = [run_id]

            if analysis_type:
                query += " AND analysis_type = ?"
                params.append(analysis_type)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                self._deserialize_analysis(
                    analysis_id=row[0],
                    run_id=row[1],
                    analysis_type=row[2],
                    result_data=json.loads(row[3]),
                    created_at=row[4],
                )
                for row in rows
            ]

    def delete_analysis(self, analysis_id: str) -> bool:
        """분석 결과를 삭제합니다.

        Args:
            analysis_id: 삭제할 분석 ID

        Returns:
            삭제 성공 여부
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM analysis_results WHERE analysis_id = ?",
                (analysis_id,),
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

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
        created_at: str,
    ) -> StatisticalAnalysis:
        """JSON 데이터를 StatisticalAnalysis로 역직렬화합니다."""
        # Reconstruct MetricStats
        metrics_summary = {
            name: MetricStats(**stats)
            for name, stats in result_data.get("metrics_summary", {}).items()
        }

        # Reconstruct CorrelationInsight
        significant_correlations = [
            CorrelationInsight(**c) for c in result_data.get("significant_correlations", [])
        ]

        # Reconstruct LowPerformerInfo
        low_performers = [LowPerformerInfo(**lp) for lp in result_data.get("low_performers", [])]

        return StatisticalAnalysis(
            analysis_id=analysis_id,
            run_id=run_id,
            analysis_type=AnalysisType(analysis_type),
            created_at=datetime.fromisoformat(created_at),
            metrics_summary=metrics_summary,
            correlation_matrix=result_data.get("correlation_matrix", []),
            correlation_metrics=result_data.get("correlation_metrics", []),
            significant_correlations=significant_correlations,
            low_performers=low_performers,
            insights=result_data.get("insights", []),
            overall_pass_rate=result_data.get("overall_pass_rate", 0.0),
            metric_pass_rates=result_data.get("metric_pass_rates", {}),
        )

    # NLP Analysis 관련 메서드

    def save_nlp_analysis(self, analysis: NLPAnalysis) -> str:
        """NLP 분석 결과를 저장합니다.

        Args:
            analysis: 저장할 NLP 분석 결과

        Returns:
            저장된 analysis의 ID
        """
        import uuid

        with self._get_connection() as conn:
            cursor = conn.cursor()
            analysis_id = f"nlp-{analysis.run_id}-{uuid.uuid4().hex[:8]}"
            result_data = self._serialize_nlp_analysis(analysis)

            cursor.execute(
                """
                INSERT OR REPLACE INTO analysis_results (
                    analysis_id, run_id, analysis_type, result_data, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    analysis.run_id,
                    AnalysisType.NLP.value,
                    json.dumps(result_data, ensure_ascii=False),
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            return analysis_id

    def get_nlp_analysis(self, analysis_id: str) -> NLPAnalysis:
        """NLP 분석 결과를 조회합니다.

        Args:
            analysis_id: 조회할 분석 ID

        Returns:
            NLPAnalysis 객체

        Raises:
            KeyError: 분석을 찾을 수 없는 경우
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT analysis_id, run_id, analysis_type, result_data, created_at
                FROM analysis_results
                WHERE analysis_id = ? AND analysis_type = ?
                """,
                (analysis_id, AnalysisType.NLP.value),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"NLP Analysis not found: {analysis_id}")

            result_data = json.loads(row[3])
            return self._deserialize_nlp_analysis(row[1], result_data)

    def get_nlp_analysis_by_run(self, run_id: str) -> NLPAnalysis | None:
        """특정 실행의 NLP 분석 결과를 조회합니다.

        Args:
            run_id: 실행 ID

        Returns:
            NLPAnalysis 또는 None (분석 결과가 없는 경우)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT analysis_id, run_id, analysis_type, result_data, created_at
                FROM analysis_results
                WHERE run_id = ? AND analysis_type = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (run_id, AnalysisType.NLP.value),
            )
            row = cursor.fetchone()

            if not row:
                return None

            result_data = json.loads(row[3])
            return self._deserialize_nlp_analysis(row[1], result_data)

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
            "topic_clusters": [asdict(tc) for tc in analysis.topic_clusters],
            "insights": analysis.insights,
        }

    def _deserialize_nlp_analysis(
        self,
        run_id: str,
        result_data: dict[str, Any],
    ) -> NLPAnalysis:
        """JSON 데이터를 NLPAnalysis로 역직렬화합니다."""
        # Reconstruct TextStats
        question_stats = None
        if result_data.get("question_stats"):
            question_stats = TextStats(**result_data["question_stats"])

        answer_stats = None
        if result_data.get("answer_stats"):
            answer_stats = TextStats(**result_data["answer_stats"])

        context_stats = None
        if result_data.get("context_stats"):
            context_stats = TextStats(**result_data["context_stats"])

        # Reconstruct QuestionTypeStats
        question_types = [
            QuestionTypeStats(
                question_type=QuestionType(qt["question_type"]),
                count=qt["count"],
                percentage=qt["percentage"],
                avg_scores=qt.get("avg_scores", {}),
            )
            for qt in result_data.get("question_types", [])
        ]

        # Reconstruct KeywordInfo
        top_keywords = [KeywordInfo(**kw) for kw in result_data.get("top_keywords", [])]

        topic_clusters = [
            TopicCluster(
                cluster_id=tc.get("cluster_id", idx),
                keywords=list(tc.get("keywords", [])),
                document_count=tc.get("document_count", 0),
                avg_scores=tc.get("avg_scores", {}),
                representative_questions=tc.get("representative_questions", []),
            )
            for idx, tc in enumerate(result_data.get("topic_clusters", []))
        ]

        return NLPAnalysis(
            run_id=run_id,
            question_stats=question_stats,
            answer_stats=answer_stats,
            context_stats=context_stats,
            question_types=question_types,
            top_keywords=top_keywords,
            topic_clusters=topic_clusters,
            insights=result_data.get("insights", []),
        )
