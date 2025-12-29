"""SQLite storage adapter for evaluation results."""

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.analysis import (
    AnalysisType,
    CorrelationInsight,
    LowPerformerInfo,
    MetricStats,
    StatisticalAnalysis,
)
from evalvault.domain.entities.experiment import Experiment, ExperimentGroup


class SQLiteStorageAdapter:
    """SQLite 기반 평가 결과 저장 어댑터.

    Implements StoragePort using SQLite database for local persistence.
    """

    def __init__(self, db_path: str | Path = "evalvault.db"):
        """Initialize SQLite storage adapter.

        Args:
            db_path: Path to SQLite database file (default: evalvault.db)
        """
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

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def save_run(self, run: EvaluationRun) -> str:
        """평가 실행 결과를 저장합니다.

        Args:
            run: 저장할 평가 실행 결과

        Returns:
            저장된 run의 ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Insert evaluation run
            cursor.execute(
                """
                INSERT INTO evaluation_runs (
                    run_id, dataset_name, dataset_version, model_name,
                    started_at, finished_at, total_tokens, total_cost_usd,
                    pass_rate, metrics_evaluated, thresholds, langfuse_trace_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.dataset_name,
                    run.dataset_version,
                    run.model_name,
                    run.started_at.isoformat(),
                    run.finished_at.isoformat() if run.finished_at else None,
                    run.total_tokens,
                    run.total_cost_usd,
                    run.pass_rate,
                    json.dumps(run.metrics_evaluated),
                    json.dumps(run.thresholds),
                    run.langfuse_trace_id,
                ),
            )

            # Insert test case results
            for result in run.results:
                cursor.execute(
                    """
                    INSERT INTO test_case_results (
                        run_id, test_case_id, tokens_used, latency_ms,
                        cost_usd, trace_id, started_at, finished_at,
                        question, answer, contexts, ground_truth
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run.run_id,
                        result.test_case_id,
                        result.tokens_used,
                        result.latency_ms,
                        result.cost_usd,
                        result.trace_id,
                        result.started_at.isoformat() if result.started_at else None,
                        result.finished_at.isoformat() if result.finished_at else None,
                        result.question,
                        result.answer,
                        json.dumps(result.contexts) if result.contexts else None,
                        result.ground_truth,
                    ),
                )

                result_id = cursor.lastrowid

                # Insert metric scores
                for metric in result.metrics:
                    cursor.execute(
                        """
                        INSERT INTO metric_scores (
                            result_id, metric_name, score, threshold, reason
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            result_id,
                            metric.name,
                            metric.score,
                            metric.threshold,
                            metric.reason,
                        ),
                    )

            conn.commit()
            return run.run_id

        finally:
            conn.close()

    def get_run(self, run_id: str) -> EvaluationRun:
        """저장된 평가 실행 결과를 조회합니다.

        Args:
            run_id: 조회할 run의 ID

        Returns:
            EvaluationRun 객체

        Raises:
            KeyError: run_id에 해당하는 결과가 없는 경우
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Fetch evaluation run
            cursor.execute(
                """
                SELECT run_id, dataset_name, dataset_version, model_name,
                       started_at, finished_at, total_tokens, total_cost_usd,
                       pass_rate, metrics_evaluated, thresholds, langfuse_trace_id
                FROM evaluation_runs
                WHERE run_id = ?
                """,
                (run_id,),
            )
            run_row = cursor.fetchone()

            if not run_row:
                raise KeyError(f"Run not found: {run_id}")

            # Fetch test case results
            cursor.execute(
                """
                SELECT id, test_case_id, tokens_used, latency_ms, cost_usd,
                       trace_id, started_at, finished_at, question, answer,
                       contexts, ground_truth
                FROM test_case_results
                WHERE run_id = ?
                ORDER BY id
                """,
                (run_id,),
            )
            result_rows = cursor.fetchall()

            # Reconstruct test case results
            results = []
            for result_row in result_rows:
                result_id = result_row[0]

                # Fetch metric scores for this result
                cursor.execute(
                    """
                    SELECT metric_name, score, threshold, reason
                    FROM metric_scores
                    WHERE result_id = ?
                    ORDER BY id
                    """,
                    (result_id,),
                )
                metric_rows = cursor.fetchall()

                metrics = [
                    MetricScore(
                        name=m[0],
                        score=m[1],
                        threshold=m[2],
                        reason=m[3],
                    )
                    for m in metric_rows
                ]

                results.append(
                    TestCaseResult(
                        test_case_id=result_row[1],
                        metrics=metrics,
                        tokens_used=result_row[2],
                        latency_ms=result_row[3],
                        cost_usd=result_row[4],
                        trace_id=result_row[5],
                        started_at=(
                            datetime.fromisoformat(result_row[6]) if result_row[6] else None
                        ),
                        finished_at=(
                            datetime.fromisoformat(result_row[7]) if result_row[7] else None
                        ),
                        question=result_row[8],
                        answer=result_row[9],
                        contexts=json.loads(result_row[10]) if result_row[10] else None,
                        ground_truth=result_row[11],
                    )
                )

            # Reconstruct EvaluationRun
            return EvaluationRun(
                run_id=run_row[0],
                dataset_name=run_row[1],
                dataset_version=run_row[2],
                model_name=run_row[3],
                started_at=datetime.fromisoformat(run_row[4]),
                finished_at=(datetime.fromisoformat(run_row[5]) if run_row[5] else None),
                total_tokens=run_row[6],
                total_cost_usd=run_row[7],
                results=results,
                metrics_evaluated=json.loads(run_row[9]),
                thresholds=json.loads(run_row[10]),
                langfuse_trace_id=run_row[11],
            )

        finally:
            conn.close()

    def list_runs(
        self,
        limit: int = 100,
        dataset_name: str | None = None,
        model_name: str | None = None,
    ) -> list[EvaluationRun]:
        """저장된 평가 실행 결과 목록을 조회합니다.

        Args:
            limit: 최대 조회 개수
            dataset_name: 필터링할 데이터셋 이름 (선택)
            model_name: 필터링할 모델 이름 (선택)

        Returns:
            EvaluationRun 객체 리스트 (최신순)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Build query with optional filters
            query = "SELECT run_id FROM evaluation_runs WHERE 1=1"
            params = []

            if dataset_name:
                query += " AND dataset_name = ?"
                params.append(dataset_name)

            if model_name:
                query += " AND model_name = ?"
                params.append(model_name)

            query += " ORDER BY started_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            run_ids = [row[0] for row in cursor.fetchall()]

            # Fetch full runs
            runs = [self.get_run(run_id) for run_id in run_ids]
            return runs

        finally:
            conn.close()

    def delete_run(self, run_id: str) -> bool:
        """평가 실행 결과를 삭제합니다.

        Args:
            run_id: 삭제할 run의 ID

        Returns:
            삭제 성공 여부
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM evaluation_runs WHERE run_id = ?", (run_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

        finally:
            conn.close()

    # Experiment 관련 메서드

    def save_experiment(self, experiment: Experiment) -> str:
        """실험을 저장합니다.

        Args:
            experiment: 저장할 실험

        Returns:
            저장된 experiment의 ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
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

        finally:
            conn.close()

    def get_experiment(self, experiment_id: str) -> Experiment:
        """실험을 조회합니다.

        Args:
            experiment_id: 조회할 실험 ID

        Returns:
            Experiment 객체

        Raises:
            KeyError: 실험을 찾을 수 없는 경우
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
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

        finally:
            conn.close()

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
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
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

        finally:
            conn.close()

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
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
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

        finally:
            conn.close()

    def get_analysis(self, analysis_id: str) -> StatisticalAnalysis:
        """분석 결과를 조회합니다.

        Args:
            analysis_id: 조회할 분석 ID

        Returns:
            StatisticalAnalysis 객체

        Raises:
            KeyError: 분석을 찾을 수 없는 경우
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
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

        finally:
            conn.close()

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
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
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

        finally:
            conn.close()

    def delete_analysis(self, analysis_id: str) -> bool:
        """분석 결과를 삭제합니다.

        Args:
            analysis_id: 삭제할 분석 ID

        Returns:
            삭제 성공 여부
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM analysis_results WHERE analysis_id = ?",
                (analysis_id,),
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

        finally:
            conn.close()

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
