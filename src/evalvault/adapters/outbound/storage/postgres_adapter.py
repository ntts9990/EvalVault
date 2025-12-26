"""PostgreSQL storage adapter for evaluation results."""

import json
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.experiment import Experiment


class PostgreSQLStorageAdapter:
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

    def _get_connection(self) -> psycopg.Connection:
        """Get a database connection with dict row factory."""
        return psycopg.connect(self._conn_string, row_factory=dict_row)

    def save_run(self, run: EvaluationRun) -> str:
        """평가 실행 결과를 저장합니다.

        Args:
            run: 저장할 평가 실행 결과

        Returns:
            저장된 run의 ID
        """
        with self._get_connection() as conn:
            # Insert evaluation run
            conn.execute(
                """
                INSERT INTO evaluation_runs (
                    run_id, dataset_name, dataset_version, model_name,
                    started_at, finished_at, total_tokens, total_cost_usd,
                    pass_rate, metrics_evaluated, thresholds, langfuse_trace_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run.run_id,
                    run.dataset_name,
                    run.dataset_version,
                    run.model_name,
                    run.started_at,
                    run.finished_at,
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
                cursor = conn.execute(
                    """
                    INSERT INTO test_case_results (
                        run_id, test_case_id, tokens_used, latency_ms,
                        cost_usd, trace_id, started_at, finished_at,
                        question, answer, contexts, ground_truth
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        run.run_id,
                        result.test_case_id,
                        result.tokens_used,
                        result.latency_ms,
                        result.cost_usd,
                        result.trace_id,
                        result.started_at,
                        result.finished_at,
                        result.question,
                        result.answer,
                        json.dumps(result.contexts) if result.contexts else None,
                        result.ground_truth,
                    ),
                )

                result_id = cursor.fetchone()["id"]

                # Insert metric scores
                for metric in result.metrics:
                    conn.execute(
                        """
                        INSERT INTO metric_scores (
                            result_id, name, score, threshold, reason
                        ) VALUES (%s, %s, %s, %s, %s)
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

    def get_run(self, run_id: str) -> EvaluationRun:
        """저장된 평가 실행 결과를 조회합니다.

        Args:
            run_id: 조회할 run의 ID

        Returns:
            EvaluationRun 객체

        Raises:
            KeyError: run_id에 해당하는 결과가 없는 경우
        """
        with self._get_connection() as conn:
            # Fetch evaluation run
            cursor = conn.execute(
                """
                SELECT run_id, dataset_name, dataset_version, model_name,
                       started_at, finished_at, total_tokens, total_cost_usd,
                       pass_rate, metrics_evaluated, thresholds, langfuse_trace_id
                FROM evaluation_runs
                WHERE run_id = %s
                """,
                (run_id,),
            )
            run_row = cursor.fetchone()

            if not run_row:
                raise KeyError(f"Run not found: {run_id}")

            # Fetch test case results
            cursor = conn.execute(
                """
                SELECT id, test_case_id, tokens_used, latency_ms, cost_usd,
                       trace_id, started_at, finished_at, question, answer,
                       contexts, ground_truth
                FROM test_case_results
                WHERE run_id = %s
                ORDER BY id
                """,
                (run_id,),
            )
            result_rows = cursor.fetchall()

            # Reconstruct test case results
            results = []
            for result_row in result_rows:
                result_id = result_row["id"]

                # Fetch metric scores for this result
                metric_cursor = conn.execute(
                    """
                    SELECT name, score, threshold, reason
                    FROM metric_scores
                    WHERE result_id = %s
                    ORDER BY id
                    """,
                    (result_id,),
                )
                metric_rows = metric_cursor.fetchall()

                metrics = [
                    MetricScore(
                        name=m["name"],
                        score=float(m["score"]),
                        threshold=float(m["threshold"]),
                        reason=m["reason"],
                    )
                    for m in metric_rows
                ]

                results.append(
                    TestCaseResult(
                        test_case_id=result_row["test_case_id"],
                        metrics=metrics,
                        tokens_used=result_row["tokens_used"],
                        latency_ms=result_row["latency_ms"],
                        cost_usd=float(result_row["cost_usd"]) if result_row["cost_usd"] else None,
                        trace_id=result_row["trace_id"],
                        started_at=result_row["started_at"],
                        finished_at=result_row["finished_at"],
                        question=result_row["question"],
                        answer=result_row["answer"],
                        contexts=(
                            json.loads(result_row["contexts"]) if result_row["contexts"] else None
                        ),
                        ground_truth=result_row["ground_truth"],
                    )
                )

            # Reconstruct EvaluationRun
            return EvaluationRun(
                run_id=run_row["run_id"],
                dataset_name=run_row["dataset_name"],
                dataset_version=run_row["dataset_version"],
                model_name=run_row["model_name"],
                started_at=run_row["started_at"],
                finished_at=run_row["finished_at"],
                total_tokens=run_row["total_tokens"],
                total_cost_usd=(
                    float(run_row["total_cost_usd"]) if run_row["total_cost_usd"] else None
                ),
                results=results,
                metrics_evaluated=json.loads(run_row["metrics_evaluated"]),
                thresholds=json.loads(run_row["thresholds"]),
                langfuse_trace_id=run_row["langfuse_trace_id"],
            )

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
        with self._get_connection() as conn:
            # Build query with optional filters
            query = "SELECT run_id FROM evaluation_runs WHERE 1=1"
            params = []

            if dataset_name:
                query += " AND dataset_name = %s"
                params.append(dataset_name)

            if model_name:
                query += " AND model_name = %s"
                params.append(model_name)

            query += " ORDER BY started_at DESC LIMIT %s"
            params.append(limit)

            cursor = conn.execute(query, params)
            run_ids = [row["run_id"] for row in cursor.fetchall()]

            # Fetch full runs
            runs = [self.get_run(run_id) for run_id in run_ids]
            return runs

    def delete_run(self, run_id: str) -> bool:
        """평가 실행 결과를 삭제합니다.

        Args:
            run_id: 삭제할 run의 ID

        Returns:
            삭제 성공 여부
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM evaluation_runs WHERE run_id = %s", (run_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    # Experiment 관련 메서드 (TODO: 구현 필요)

    def save_experiment(self, experiment: Experiment) -> str:
        """실험을 저장합니다.

        Args:
            experiment: 저장할 실험

        Returns:
            저장된 experiment의 ID
        """
        raise NotImplementedError("PostgreSQL experiment storage not implemented yet")

    def get_experiment(self, experiment_id: str) -> Experiment:
        """실험을 조회합니다.

        Args:
            experiment_id: 조회할 실험 ID

        Returns:
            Experiment 객체

        Raises:
            KeyError: 실험을 찾을 수 없는 경우
        """
        raise NotImplementedError("PostgreSQL experiment storage not implemented yet")

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
        raise NotImplementedError("PostgreSQL experiment storage not implemented yet")

    def update_experiment(self, experiment: Experiment) -> None:
        """실험을 업데이트합니다.

        Args:
            experiment: 업데이트할 실험
        """
        raise NotImplementedError("PostgreSQL experiment storage not implemented yet")
