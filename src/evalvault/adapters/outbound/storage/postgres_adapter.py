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

from evalvault.adapters.outbound.analysis.pipeline_helpers import to_serializable
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
from evalvault.domain.entities.experiment import Experiment
from evalvault.domain.entities.prompt import Prompt, PromptSet, PromptSetBundle, PromptSetItem
from evalvault.domain.entities.stage import StageEvent, StageMetric


class PostgresQueries(SQLQueries):
    def __init__(self) -> None:
        super().__init__(
            placeholder="%s",
            metric_name_column="name",
            test_case_returning_clause="RETURNING id",
            feedback_returning_clause="RETURNING id",
        )

    def upsert_regression_baseline(self) -> str:
        return """
        INSERT INTO regression_baselines (
            baseline_key, run_id, dataset_name, branch, commit_sha, metadata,
            created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (baseline_key) DO UPDATE SET
            run_id = EXCLUDED.run_id,
            dataset_name = EXCLUDED.dataset_name,
            branch = EXCLUDED.branch,
            commit_sha = EXCLUDED.commit_sha,
            metadata = EXCLUDED.metadata,
            updated_at = EXCLUDED.updated_at
        """


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
        super().__init__(PostgresQueries())
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
            self._apply_migrations(conn)
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

    def _apply_migrations(self, conn) -> None:
        """Apply schema migrations for legacy databases."""
        cursor = conn.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'evaluation_runs'
              AND column_name IN ('metadata', 'retrieval_metadata')
            """
        )
        columns = {row[0] for row in cursor.fetchall()}
        if "metadata" not in columns:
            conn.execute("ALTER TABLE evaluation_runs ADD COLUMN metadata JSONB")
        if "retrieval_metadata" not in columns:
            conn.execute("ALTER TABLE evaluation_runs ADD COLUMN retrieval_metadata JSONB")

        pipeline_cursor = conn.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'pipeline_results'
              AND column_name IN ('profile', 'tags', 'metadata')
            """
        )
        pipeline_columns = {row[0] for row in pipeline_cursor.fetchall()}
        if pipeline_columns:
            if "profile" not in pipeline_columns:
                conn.execute("ALTER TABLE pipeline_results ADD COLUMN profile VARCHAR(50)")
            if "tags" not in pipeline_columns:
                conn.execute("ALTER TABLE pipeline_results ADD COLUMN tags JSONB")
            if "metadata" not in pipeline_columns:
                conn.execute("ALTER TABLE pipeline_results ADD COLUMN metadata JSONB")

        cluster_cursor = conn.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'run_cluster_maps'
            """
        )
        cluster_columns = {row[0] for row in cluster_cursor.fetchall()}
        if cluster_columns and "map_id" not in cluster_columns:
            conn.execute("ALTER TABLE run_cluster_maps RENAME TO run_cluster_maps_legacy")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_cluster_maps (
                    run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
                    map_id UUID NOT NULL,
                    test_case_id VARCHAR(255) NOT NULL,
                    cluster_id VARCHAR(255) NOT NULL,
                    source TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (run_id, map_id, test_case_id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cluster_maps_run_id ON run_cluster_maps(run_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cluster_maps_map_id ON run_cluster_maps(map_id)"
            )

            legacy_rows = conn.execute(
                """
                SELECT run_id, test_case_id, cluster_id, source, created_at
                FROM run_cluster_maps_legacy
                """
            ).fetchall()
            if legacy_rows:
                import uuid
                from datetime import UTC, datetime

                grouped: dict[tuple[str, str | None], list[tuple]] = {}
                for row in legacy_rows:
                    run_id = str(row[0])
                    source = row[3]
                    grouped.setdefault((run_id, source), []).append(row)
                for (run_id, source), rows in grouped.items():
                    map_id = uuid.uuid4()
                    created_at = rows[0][4] or datetime.now(UTC)
                    for row in rows:
                        conn.execute(
                            """
                            INSERT INTO run_cluster_maps (
                                run_id, map_id, test_case_id, cluster_id, source, metadata, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                run_id,
                                map_id,
                                row[1],
                                row[2],
                                source,
                                None,
                                created_at,
                            ),
                        )
        elif cluster_columns and "metadata" not in cluster_columns:
            conn.execute("ALTER TABLE run_cluster_maps ADD COLUMN metadata JSONB")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS satisfaction_feedback (
                id SERIAL PRIMARY KEY,
                run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
                test_case_id VARCHAR(255) NOT NULL,
                satisfaction_score DECIMAL(4, 2),
                thumb_feedback VARCHAR(10),
                comment TEXT,
                rater_id VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_feedback_run_id ON satisfaction_feedback(run_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_feedback_test_case_id ON satisfaction_feedback(test_case_id)"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS multiturn_runs (
                run_id UUID PRIMARY KEY,
                dataset_name VARCHAR(255) NOT NULL,
                dataset_version VARCHAR(50),
                model_name VARCHAR(255),
                started_at TIMESTAMP WITH TIME ZONE NOT NULL,
                finished_at TIMESTAMP WITH TIME ZONE,
                conversation_count INTEGER DEFAULT 0,
                turn_count INTEGER DEFAULT 0,
                metrics_evaluated JSONB,
                drift_threshold DOUBLE PRECISION,
                summary JSONB,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_multiturn_runs_dataset ON multiturn_runs(dataset_name)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_multiturn_runs_started_at ON multiturn_runs(started_at DESC)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS multiturn_conversations (
                id SERIAL PRIMARY KEY,
                run_id UUID NOT NULL REFERENCES multiturn_runs(run_id) ON DELETE CASCADE,
                conversation_id VARCHAR(255) NOT NULL,
                turn_count INTEGER DEFAULT 0,
                drift_score DOUBLE PRECISION,
                drift_threshold DOUBLE PRECISION,
                drift_detected BOOLEAN DEFAULT FALSE,
                summary JSONB
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_multiturn_conversations_run_id ON multiturn_conversations(run_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_multiturn_conversations_conv_id ON multiturn_conversations(conversation_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS multiturn_turn_results (
                id SERIAL PRIMARY KEY,
                run_id UUID NOT NULL REFERENCES multiturn_runs(run_id) ON DELETE CASCADE,
                conversation_id VARCHAR(255) NOT NULL,
                turn_id VARCHAR(255) NOT NULL,
                turn_index INTEGER,
                role VARCHAR(50) NOT NULL,
                passed BOOLEAN DEFAULT FALSE,
                latency_ms INTEGER,
                metadata JSONB
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_multiturn_turns_run_id ON multiturn_turn_results(run_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_multiturn_turns_conv_id ON multiturn_turn_results(conversation_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS multiturn_metric_scores (
                id SERIAL PRIMARY KEY,
                turn_result_id INTEGER NOT NULL REFERENCES multiturn_turn_results(id) ON DELETE CASCADE,
                metric_name VARCHAR(100) NOT NULL,
                score DECIMAL(5, 4) NOT NULL,
                threshold DECIMAL(5, 4)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_multiturn_scores_turn_id ON multiturn_metric_scores(turn_result_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_multiturn_scores_metric_name ON multiturn_metric_scores(metric_name)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS regression_baselines (
                baseline_key TEXT PRIMARY KEY,
                run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
                dataset_name VARCHAR(255),
                branch TEXT,
                commit_sha VARCHAR(64),
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_baselines_run_id ON regression_baselines(run_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_baselines_dataset ON regression_baselines(dataset_name)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_baselines_updated_at ON regression_baselines(updated_at DESC)"
        )

    # Prompt set methods

    def save_prompt_set(self, bundle: PromptSetBundle) -> None:
        """Save prompt set, prompts, and join items."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO prompt_sets (
                    prompt_set_id, name, description, metadata, created_at
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (prompt_set_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    metadata = EXCLUDED.metadata
                """,
                (
                    bundle.prompt_set.prompt_set_id,
                    bundle.prompt_set.name,
                    bundle.prompt_set.description,
                    json.dumps(bundle.prompt_set.metadata),
                    bundle.prompt_set.created_at,
                ),
            )

            for prompt in bundle.prompts:
                conn.execute(
                    """
                    INSERT INTO prompts (
                        prompt_id, name, kind, content, checksum,
                        source, notes, metadata, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (prompt_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        kind = EXCLUDED.kind,
                        content = EXCLUDED.content,
                        checksum = EXCLUDED.checksum,
                        source = EXCLUDED.source,
                        notes = EXCLUDED.notes,
                        metadata = EXCLUDED.metadata
                    """,
                    (
                        prompt.prompt_id,
                        prompt.name,
                        prompt.kind,
                        prompt.content,
                        prompt.checksum,
                        prompt.source,
                        prompt.notes,
                        json.dumps(prompt.metadata),
                        prompt.created_at,
                    ),
                )

            conn.execute(
                "DELETE FROM prompt_set_items WHERE prompt_set_id = %s",
                (bundle.prompt_set.prompt_set_id,),
            )
            for item in bundle.items:
                conn.execute(
                    """
                    INSERT INTO prompt_set_items (
                        prompt_set_id, prompt_id, role, item_order, metadata
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        item.prompt_set_id,
                        item.prompt_id,
                        item.role,
                        item.item_order,
                        json.dumps(item.metadata),
                    ),
                )
            conn.commit()

    def link_prompt_set_to_run(self, run_id: str, prompt_set_id: str) -> None:
        """Attach a prompt set to a run."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO run_prompt_sets (
                    run_id, prompt_set_id, created_at
                ) VALUES (%s, %s, %s)
                ON CONFLICT (run_id, prompt_set_id) DO NOTHING
                """,
                (
                    run_id,
                    prompt_set_id,
                    datetime.now(UTC),
                ),
            )
            conn.commit()

    def get_prompt_set(self, prompt_set_id: str) -> PromptSetBundle:
        """Load a prompt set bundle by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT prompt_set_id, name, description, metadata, created_at
                FROM prompt_sets
                WHERE prompt_set_id = %s
                """,
                (prompt_set_id,),
            ).fetchone()
            if not row:
                raise KeyError(f"Prompt set not found: {prompt_set_id}")

            prompt_set = PromptSet(
                prompt_set_id=str(row["prompt_set_id"]),
                name=row["name"],
                description=row.get("description") or "",
                metadata=row["metadata"] or {},
                created_at=row["created_at"],
            )

            item_rows = conn.execute(
                """
                SELECT prompt_id, role, item_order, metadata
                FROM prompt_set_items
                WHERE prompt_set_id = %s
                ORDER BY item_order, id
                """,
                (prompt_set_id,),
            ).fetchall()

            items = [
                PromptSetItem(
                    prompt_set_id=str(prompt_set_id),
                    prompt_id=str(item["prompt_id"]),
                    role=item["role"],
                    item_order=item.get("item_order") or 0,
                    metadata=item.get("metadata") or {},
                )
                for item in item_rows
            ]

            prompt_ids = [item.prompt_id for item in items]
            prompts: list[Prompt] = []
            if prompt_ids:
                prompt_rows = conn.execute(
                    """
                    SELECT prompt_id, name, kind, content, checksum,
                           source, notes, metadata, created_at
                    FROM prompts
                    WHERE prompt_id = ANY(%s)
                    """,
                    (prompt_ids,),
                ).fetchall()
                for prompt_row in prompt_rows:
                    prompts.append(
                        Prompt(
                            prompt_id=str(prompt_row["prompt_id"]),
                            name=prompt_row["name"],
                            kind=prompt_row["kind"],
                            content=prompt_row["content"],
                            checksum=prompt_row["checksum"],
                            source=prompt_row.get("source"),
                            notes=prompt_row.get("notes"),
                            metadata=prompt_row.get("metadata") or {},
                            created_at=prompt_row["created_at"],
                        )
                    )

            return PromptSetBundle(prompt_set=prompt_set, prompts=prompts, items=items)

    def get_prompt_set_for_run(self, run_id: str) -> PromptSetBundle | None:
        """Load the prompt set linked to a run."""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT prompt_set_id
                FROM run_prompt_sets
                WHERE run_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (run_id,),
            ).fetchone()
            if not row:
                return None
        return self.get_prompt_set(str(row["prompt_set_id"]))

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

    def save_analysis_result(
        self,
        *,
        run_id: str,
        analysis_type: str,
        result_data: dict[str, Any],
        analysis_id: str | None = None,
    ) -> str:
        """분석 결과(JSON)를 저장합니다."""
        analysis_id = analysis_id or f"analysis-{analysis_type}-{run_id}-{uuid.uuid4().hex[:8]}"
        payload = to_serializable(result_data)

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
                    run_id,
                    analysis_type,
                    json.dumps(payload, ensure_ascii=False),
                    datetime.now(UTC),
                ),
            )
            conn.commit()
        return analysis_id

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

    def save_dataset_feature_analysis(
        self,
        *,
        run_id: str,
        result_data: dict[str, Any],
        analysis_id: str | None = None,
    ) -> str:
        """데이터셋 특성 분석 결과를 저장합니다."""
        analysis_id = analysis_id or f"dataset-features-{run_id}-{uuid.uuid4().hex[:8]}"

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
                    run_id,
                    AnalysisType.DATASET_FEATURES.value,
                    json.dumps(result_data, ensure_ascii=False),
                    datetime.now(UTC),
                ),
            )
            conn.commit()
        return analysis_id

    def get_dataset_feature_analysis(self, analysis_id: str) -> dict[str, Any]:
        """데이터셋 특성 분석 결과를 조회합니다."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT result_data
                FROM analysis_results
                WHERE analysis_id = %s AND analysis_type = %s
                """,
                (analysis_id, AnalysisType.DATASET_FEATURES.value),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"Dataset feature analysis not found: {analysis_id}")

            return self._ensure_json(row["result_data"])

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

    # Pipeline result history 관련 메서드

    def save_pipeline_result(self, record: dict[str, Any]) -> None:
        """파이프라인 분석 결과 히스토리를 저장합니다."""
        created_at = record.get("created_at") or datetime.now(UTC)
        is_complete = bool(record.get("is_complete", False))

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO pipeline_results (
                    result_id, intent, query, run_id, pipeline_id,
                    profile, tags, metadata,
                    is_complete, duration_ms, final_output, node_results,
                    started_at, finished_at, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (result_id) DO UPDATE SET
                    intent = EXCLUDED.intent,
                    query = EXCLUDED.query,
                    run_id = EXCLUDED.run_id,
                    pipeline_id = EXCLUDED.pipeline_id,
                    profile = EXCLUDED.profile,
                    tags = EXCLUDED.tags,
                    metadata = EXCLUDED.metadata,
                    is_complete = EXCLUDED.is_complete,
                    duration_ms = EXCLUDED.duration_ms,
                    final_output = EXCLUDED.final_output,
                    node_results = EXCLUDED.node_results,
                    started_at = EXCLUDED.started_at,
                    finished_at = EXCLUDED.finished_at,
                    created_at = EXCLUDED.created_at
                """,
                (
                    record.get("result_id"),
                    record.get("intent"),
                    record.get("query"),
                    record.get("run_id"),
                    record.get("pipeline_id"),
                    record.get("profile"),
                    self._serialize_pipeline_json(record.get("tags")),
                    self._serialize_pipeline_json(record.get("metadata")),
                    is_complete,
                    record.get("duration_ms"),
                    self._serialize_pipeline_json(record.get("final_output")),
                    self._serialize_pipeline_json(record.get("node_results")),
                    record.get("started_at"),
                    record.get("finished_at"),
                    created_at,
                ),
            )
            conn.commit()

    def save_analysis_report(
        self,
        *,
        report_id: str | None,
        run_id: str | None,
        experiment_id: str | None,
        report_type: str,
        format: str,
        content: str | None,
        metadata: dict[str, Any] | None = None,
        created_at: str | None = None,
    ) -> str:
        report_id = report_id or str(uuid.uuid4())
        if created_at is None:
            created_at_value = datetime.now(UTC)
        else:
            created_at_value = (
                datetime.fromisoformat(created_at) if isinstance(created_at, str) else created_at
            )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO analysis_reports (
                    report_id, run_id, experiment_id, report_type, format, content, metadata, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (report_id) DO UPDATE SET
                    run_id = EXCLUDED.run_id,
                    experiment_id = EXCLUDED.experiment_id,
                    report_type = EXCLUDED.report_type,
                    format = EXCLUDED.format,
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    created_at = EXCLUDED.created_at
                """,
                (
                    report_id,
                    run_id,
                    experiment_id,
                    report_type,
                    format,
                    content,
                    self._serialize_pipeline_json(metadata),
                    created_at_value,
                ),
            )
            conn.commit()

        return report_id

    def list_analysis_reports(
        self,
        *,
        run_id: str,
        report_type: str | None = None,
        format: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        clauses = ["run_id = %s"]
        params: list[Any] = [run_id]
        if report_type:
            clauses.append("report_type = %s")
            params.append(report_type)
        if format:
            clauses.append("format = %s")
            params.append(format)
        params.append(limit)

        query = (
            "SELECT report_id, run_id, experiment_id, report_type, format, content, metadata, created_at "
            "FROM analysis_reports WHERE "
            + " AND ".join(clauses)
            + " ORDER BY created_at DESC LIMIT %s"
        )

        with self._get_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        reports: list[dict[str, Any]] = []
        for row in rows:
            reports.append(
                {
                    "report_id": row["report_id"],
                    "run_id": row["run_id"],
                    "experiment_id": row["experiment_id"],
                    "report_type": row["report_type"],
                    "format": row["format"],
                    "content": row["content"],
                    "metadata": self._deserialize_json(row["metadata"]),
                    "created_at": row["created_at"].isoformat()
                    if isinstance(row["created_at"], datetime)
                    else row["created_at"],
                }
            )
        return reports

    def save_ops_report(
        self,
        *,
        report_id: str | None,
        run_id: str | None,
        report_type: str,
        format: str,
        content: str | None,
        metadata: dict[str, Any] | None = None,
        created_at: str | None = None,
    ) -> str:
        report_id = report_id or str(uuid.uuid4())
        if created_at is None:
            created_at_value = datetime.now(UTC)
        else:
            created_at_value = (
                datetime.fromisoformat(created_at) if isinstance(created_at, str) else created_at
            )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO ops_reports (
                    report_id, run_id, report_type, format, content, metadata, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (report_id) DO UPDATE SET
                    run_id = EXCLUDED.run_id,
                    report_type = EXCLUDED.report_type,
                    format = EXCLUDED.format,
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    created_at = EXCLUDED.created_at
                """,
                (
                    report_id,
                    run_id,
                    report_type,
                    format,
                    content,
                    self._serialize_pipeline_json(metadata),
                    created_at_value,
                ),
            )
            conn.commit()

        return report_id

    def list_ops_reports(
        self,
        *,
        run_id: str,
        report_type: str | None = None,
        format: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        clauses = ["run_id = %s"]
        params: list[Any] = [run_id]
        if report_type:
            clauses.append("report_type = %s")
            params.append(report_type)
        if format:
            clauses.append("format = %s")
            params.append(format)
        params.append(limit)

        query = (
            "SELECT report_id, run_id, report_type, format, content, metadata, created_at "
            "FROM ops_reports WHERE " + " AND ".join(clauses) + " ORDER BY created_at DESC LIMIT %s"
        )

        with self._get_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        reports: list[dict[str, Any]] = []
        for row in rows:
            reports.append(
                {
                    "report_id": row["report_id"],
                    "run_id": row["run_id"],
                    "report_type": row["report_type"],
                    "format": row["format"],
                    "content": row["content"],
                    "metadata": self._deserialize_json(row["metadata"]),
                    "created_at": row["created_at"].isoformat()
                    if isinstance(row["created_at"], datetime)
                    else row["created_at"],
                }
            )
        return reports

    def list_pipeline_results(self, limit: int = 50) -> list[dict[str, Any]]:
        """파이프라인 분석 결과 목록을 조회합니다."""
        query = """
            SELECT result_id, intent, query, run_id, pipeline_id,
                   profile, tags,
                   is_complete, duration_ms, created_at, started_at, finished_at
            FROM pipeline_results
            ORDER BY created_at DESC
            LIMIT %s
        """
        with self._get_connection() as conn:
            rows = conn.execute(query, (limit,)).fetchall()
        return [self._deserialize_pipeline_result(row, include_payload=False) for row in rows]

    def save_stage_events(self, events: list[StageEvent]) -> int:
        if not events:
            return 0
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT INTO stage_events (
                    run_id, stage_id, parent_stage_id, stage_type, stage_name,
                    status, attempt, started_at, finished_at, duration_ms,
                    input_ref, output_ref, attributes, metadata, trace_id, span_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id, stage_id) DO UPDATE SET
                    parent_stage_id = EXCLUDED.parent_stage_id,
                    stage_type = EXCLUDED.stage_type,
                    stage_name = EXCLUDED.stage_name,
                    status = EXCLUDED.status,
                    attempt = EXCLUDED.attempt,
                    started_at = EXCLUDED.started_at,
                    finished_at = EXCLUDED.finished_at,
                    duration_ms = EXCLUDED.duration_ms,
                    input_ref = EXCLUDED.input_ref,
                    output_ref = EXCLUDED.output_ref,
                    attributes = EXCLUDED.attributes,
                    metadata = EXCLUDED.metadata,
                    trace_id = EXCLUDED.trace_id,
                    span_id = EXCLUDED.span_id
                """,
                [self._serialize_stage_event(event) for event in events],
            )
            conn.commit()
        return len(events)

    def list_stage_events(
        self,
        run_id: str,
        *,
        stage_type: str | None = None,
    ) -> list[StageEvent]:
        query = (
            "SELECT run_id, stage_id, parent_stage_id, stage_type, stage_name, status, attempt, "
            "started_at, finished_at, duration_ms, input_ref, output_ref, attributes, metadata, "
            "trace_id, span_id FROM stage_events WHERE run_id = %s"
        )
        params: list[Any] = [run_id]
        if stage_type:
            query += " AND stage_type = %s"
            params.append(stage_type)
        query += " ORDER BY id"
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._deserialize_stage_event(row) for row in rows]

    def save_stage_metrics(self, metrics: list[StageMetric]) -> int:
        if not metrics:
            return 0
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT INTO stage_metrics (
                    run_id, stage_id, metric_name, score, threshold, evidence
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [self._serialize_stage_metric(metric) for metric in metrics],
            )
            conn.commit()
        return len(metrics)

    def list_stage_metrics(
        self,
        run_id: str,
        *,
        stage_id: str | None = None,
        metric_name: str | None = None,
    ) -> list[StageMetric]:
        query = (
            "SELECT run_id, stage_id, metric_name, score, threshold, evidence "
            "FROM stage_metrics WHERE run_id = %s"
        )
        params: list[Any] = [run_id]
        if stage_id:
            query += " AND stage_id = %s"
            params.append(stage_id)
        if metric_name:
            query += " AND metric_name = %s"
            params.append(metric_name)
        query += " ORDER BY id"
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._deserialize_stage_metric(row) for row in rows]

    def _serialize_stage_event(self, event: StageEvent) -> tuple[Any, ...]:
        return (
            event.run_id,
            event.stage_id,
            event.parent_stage_id,
            event.stage_type,
            event.stage_name,
            event.status,
            event.attempt,
            event.started_at,
            event.finished_at,
            event.duration_ms,
            self._serialize_payload_ref(event.input_ref),
            self._serialize_payload_ref(event.output_ref),
            self._serialize_pipeline_json(event.attributes),
            self._serialize_pipeline_json(event.metadata),
            event.trace_id,
            event.span_id,
        )

    def _serialize_stage_metric(self, metric: StageMetric) -> tuple[Any, ...]:
        return (
            metric.run_id,
            metric.stage_id,
            metric.metric_name,
            metric.score,
            metric.threshold,
            self._serialize_pipeline_json(metric.evidence),
        )

    def _serialize_payload_ref(self, ref: Any) -> str | None:
        if ref is None:
            return None
        payload = ref.to_dict() if hasattr(ref, "to_dict") else ref
        return self._serialize_pipeline_json(payload)

    def _deserialize_stage_event(self, row: dict[str, Any]) -> StageEvent:
        payload = {
            "run_id": row.get("run_id"),
            "stage_id": row.get("stage_id"),
            "parent_stage_id": row.get("parent_stage_id"),
            "stage_type": row.get("stage_type"),
            "stage_name": row.get("stage_name"),
            "status": row.get("status"),
            "attempt": row.get("attempt"),
            "started_at": row.get("started_at"),
            "finished_at": row.get("finished_at"),
            "duration_ms": row.get("duration_ms"),
            "input_ref": self._ensure_json(row.get("input_ref")),
            "output_ref": self._ensure_json(row.get("output_ref")),
            "attributes": self._ensure_json(row.get("attributes")) or {},
            "metadata": self._ensure_json(row.get("metadata")) or {},
            "trace_id": row.get("trace_id"),
            "span_id": row.get("span_id"),
        }
        return StageEvent.from_dict(payload)

    def _deserialize_stage_metric(self, row: dict[str, Any]) -> StageMetric:
        payload = {
            "run_id": row.get("run_id"),
            "stage_id": row.get("stage_id"),
            "metric_name": row.get("metric_name"),
            "score": row.get("score"),
            "threshold": row.get("threshold"),
            "evidence": self._ensure_json(row.get("evidence")),
        }
        return StageMetric.from_dict(payload)

    def get_pipeline_result(self, result_id: str) -> dict[str, Any]:
        """저장된 파이프라인 분석 결과를 조회합니다."""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT result_id, intent, query, run_id, pipeline_id,
                       profile, tags, metadata,
                       is_complete, duration_ms, created_at,
                       started_at, finished_at, final_output, node_results
                FROM pipeline_results
                WHERE result_id = %s
                """,
                (result_id,),
            ).fetchone()
        if not row:
            raise KeyError(f"Pipeline result not found: {result_id}")
        return self._deserialize_pipeline_result(row, include_payload=True)

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

    def _serialize_pipeline_json(self, value: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False)

    def _deserialize_pipeline_result(
        self,
        row: dict[str, Any],
        *,
        include_payload: bool,
    ) -> dict[str, Any]:
        item = {
            "result_id": row.get("result_id"),
            "intent": row.get("intent"),
            "query": row.get("query"),
            "run_id": row.get("run_id"),
            "pipeline_id": row.get("pipeline_id"),
            "profile": row.get("profile"),
            "tags": self._ensure_json(row.get("tags")),
            "is_complete": bool(row.get("is_complete")),
            "duration_ms": self._maybe_float(row.get("duration_ms")),
            "created_at": self._normalize_timestamp(row.get("created_at")),
            "started_at": self._normalize_timestamp(row.get("started_at")),
            "finished_at": self._normalize_timestamp(row.get("finished_at")),
        }
        if include_payload:
            item["final_output"] = self._ensure_json(row.get("final_output"))
            item["node_results"] = self._ensure_json(row.get("node_results"))
            item["metadata"] = self._ensure_json(row.get("metadata"))
        return item

    def _normalize_timestamp(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _ensure_json(self, value: Any) -> Any:
        """JSONB 값을 파이썬 타입으로 변환."""
        if value is None:
            return None
        if isinstance(value, dict | list):
            return value
        if isinstance(value, str):
            return json.loads(value)
        return value
