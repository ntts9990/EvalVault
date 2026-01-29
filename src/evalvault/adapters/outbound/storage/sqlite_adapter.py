"""SQLite storage adapter for evaluation results."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import AbstractContextManager, closing
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

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
from evalvault.domain.entities.experiment import Experiment, ExperimentGroup
from evalvault.domain.entities.prompt import Prompt, PromptSet, PromptSetBundle, PromptSetItem
from evalvault.domain.entities.stage import StageEvent, StageMetric, StagePayloadRef

if TYPE_CHECKING:
    from evalvault.domain.entities.benchmark_run import BenchmarkRun


class SQLiteQueries(SQLQueries):
    def upsert_regression_baseline(self) -> str:
        return """
        INSERT OR REPLACE INTO regression_baselines (
            baseline_key, run_id, dataset_name, branch, commit_sha, metadata,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """


class SQLiteStorageAdapter(BaseSQLStorageAdapter):
    """SQLite 기반 평가 결과 저장 어댑터.

    Implements StoragePort using SQLite database for local persistence.
    """

    def __init__(self, db_path: str | Path = "data/db/evalvault.db"):
        """Initialize SQLite storage adapter.

        Args:
            db_path: Path to SQLite database file (default: data/db/evalvault.db)
        """
        super().__init__(SQLiteQueries())
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema from schema.sql."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        conn.executescript(schema_sql)
        self._apply_migrations(conn)
        conn.commit()
        conn.close()

    def _connect(self) -> Any:
        """Create a DB-API connection with the expected options."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _get_connection(self) -> AbstractContextManager[sqlite3.Connection]:
        conn = self._connect()
        return closing(cast(sqlite3.Connection, conn))

    def _apply_migrations(self, conn: Any) -> None:
        """Apply schema migrations for legacy databases."""
        conn = cast(Any, conn)
        cursor = conn.execute("PRAGMA table_info(evaluation_runs)")
        columns = {row[1] for row in cursor.fetchall()}
        if "metadata" not in columns:
            conn.execute("ALTER TABLE evaluation_runs ADD COLUMN metadata TEXT")
        if "retrieval_metadata" not in columns:
            conn.execute("ALTER TABLE evaluation_runs ADD COLUMN retrieval_metadata TEXT")

        cluster_cursor = conn.execute("PRAGMA table_info(run_cluster_maps)")
        cluster_columns = {row[1] for row in cluster_cursor.fetchall()}
        if cluster_columns and "map_id" not in cluster_columns:
            conn.execute("ALTER TABLE run_cluster_maps RENAME TO run_cluster_maps_legacy")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_cluster_maps (
                    run_id TEXT NOT NULL,
                    map_id TEXT NOT NULL,
                    test_case_id TEXT NOT NULL,
                    cluster_id TEXT NOT NULL,
                    source TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (run_id, map_id, test_case_id),
                    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
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
                from datetime import datetime

                grouped: dict[tuple[str, str | None], list[sqlite3.Row]] = {}
                for row in legacy_rows:
                    key = (row["run_id"], row["source"])
                    grouped.setdefault(key, []).append(row)
                for (run_id, source), rows in grouped.items():
                    map_id = str(uuid.uuid4())
                    created_at = rows[0]["created_at"] or datetime.now().isoformat()
                    for row in rows:
                        conn.execute(
                            """
                            INSERT INTO run_cluster_maps (
                                run_id, map_id, test_case_id, cluster_id, source, metadata, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                run_id,
                                map_id,
                                row["test_case_id"],
                                row["cluster_id"],
                                source,
                                None,
                                created_at,
                            ),
                        )
        elif cluster_columns and "metadata" not in cluster_columns:
            conn.execute("ALTER TABLE run_cluster_maps ADD COLUMN metadata TEXT")

        feedback_cursor = conn.execute("PRAGMA table_info(satisfaction_feedback)")
        feedback_columns = {row[1] for row in feedback_cursor.fetchall()}
        if not feedback_columns:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS satisfaction_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    test_case_id TEXT NOT NULL,
                    satisfaction_score REAL,
                    thumb_feedback TEXT,
                    comment TEXT,
                    rater_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_feedback_run_id ON satisfaction_feedback(run_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_feedback_test_case_id ON satisfaction_feedback(test_case_id)"
            )

        pipeline_cursor = conn.execute("PRAGMA table_info(pipeline_results)")
        pipeline_columns = {row[1] for row in pipeline_cursor.fetchall()}
        if pipeline_columns:
            if "profile" not in pipeline_columns:
                conn.execute("ALTER TABLE pipeline_results ADD COLUMN profile TEXT")
            if "tags" not in pipeline_columns:
                conn.execute("ALTER TABLE pipeline_results ADD COLUMN tags TEXT")
            if "metadata" not in pipeline_columns:
                conn.execute("ALTER TABLE pipeline_results ADD COLUMN metadata TEXT")

        multiturn_cursor = conn.execute("PRAGMA table_info(multiturn_runs)")
        multiturn_columns = {row[1] for row in multiturn_cursor.fetchall()}
        if not multiturn_columns:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS multiturn_runs (
                    run_id TEXT PRIMARY KEY,
                    dataset_name TEXT NOT NULL,
                    dataset_version TEXT,
                    model_name TEXT,
                    started_at TIMESTAMP NOT NULL,
                    finished_at TIMESTAMP,
                    conversation_count INTEGER DEFAULT 0,
                    turn_count INTEGER DEFAULT 0,
                    metrics_evaluated TEXT,
                    drift_threshold REAL,
                    summary TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_multiturn_runs_dataset ON multiturn_runs(dataset_name);
                CREATE INDEX IF NOT EXISTS idx_multiturn_runs_started_at ON multiturn_runs(started_at DESC);

                CREATE TABLE IF NOT EXISTS multiturn_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    turn_count INTEGER DEFAULT 0,
                    drift_score REAL,
                    drift_threshold REAL,
                    drift_detected INTEGER DEFAULT 0,
                    summary TEXT,
                    FOREIGN KEY (run_id) REFERENCES multiturn_runs(run_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_multiturn_conversations_run_id ON multiturn_conversations(run_id);
                CREATE INDEX IF NOT EXISTS idx_multiturn_conversations_conv_id ON multiturn_conversations(conversation_id);

                CREATE TABLE IF NOT EXISTS multiturn_turn_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    turn_id TEXT NOT NULL,
                    turn_index INTEGER,
                    role TEXT NOT NULL,
                    passed INTEGER DEFAULT 0,
                    latency_ms INTEGER,
                    metadata TEXT,
                    FOREIGN KEY (run_id) REFERENCES multiturn_runs(run_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_multiturn_turns_run_id ON multiturn_turn_results(run_id);
                CREATE INDEX IF NOT EXISTS idx_multiturn_turns_conv_id ON multiturn_turn_results(conversation_id);

                CREATE TABLE IF NOT EXISTS multiturn_metric_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    turn_result_id INTEGER NOT NULL,
                    metric_name TEXT NOT NULL,
                    score REAL NOT NULL,
                    threshold REAL,
                    FOREIGN KEY (turn_result_id) REFERENCES multiturn_turn_results(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_multiturn_scores_turn_id ON multiturn_metric_scores(turn_result_id);
                CREATE INDEX IF NOT EXISTS idx_multiturn_scores_metric_name ON multiturn_metric_scores(metric_name);
                """
            )

        baseline_cursor = conn.execute("PRAGMA table_info(regression_baselines)")
        baseline_columns = {row[1] for row in baseline_cursor.fetchall()}
        if not baseline_columns:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS regression_baselines (
                    baseline_key TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    dataset_name TEXT,
                    branch TEXT,
                    commit_sha TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_baselines_run_id ON regression_baselines(run_id);
                CREATE INDEX IF NOT EXISTS idx_baselines_dataset ON regression_baselines(dataset_name);
                CREATE INDEX IF NOT EXISTS idx_baselines_updated_at ON regression_baselines(updated_at DESC);
                """
            )

    # Prompt set methods

    def save_prompt_set(self, bundle: PromptSetBundle) -> None:
        """Save prompt set, prompts, and join items."""
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO prompt_sets (
                    prompt_set_id, name, description, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    bundle.prompt_set.prompt_set_id,
                    bundle.prompt_set.name,
                    bundle.prompt_set.description,
                    json.dumps(bundle.prompt_set.metadata),
                    bundle.prompt_set.created_at.isoformat(),
                ),
            )

            for prompt in bundle.prompts:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO prompts (
                        prompt_id, name, kind, content, checksum,
                        source, notes, metadata, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        prompt.created_at.isoformat(),
                    ),
                )

            cursor.execute(
                "DELETE FROM prompt_set_items WHERE prompt_set_id = ?",
                (bundle.prompt_set.prompt_set_id,),
            )
            for item in bundle.items:
                cursor.execute(
                    """
                    INSERT INTO prompt_set_items (
                        prompt_set_id, prompt_id, role, item_order, metadata
                    ) VALUES (?, ?, ?, ?, ?)
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
            conn = cast(Any, conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO run_prompt_sets (
                    run_id, prompt_set_id, created_at
                ) VALUES (?, ?, ?)
                """,
                (
                    run_id,
                    prompt_set_id,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()

    def get_prompt_set(self, prompt_set_id: str) -> PromptSetBundle:
        """Load a prompt set bundle by ID."""
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            cursor = conn.execute(
                """
                SELECT prompt_set_id, name, description, metadata, created_at
                FROM prompt_sets
                WHERE prompt_set_id = ?
                """,
                (prompt_set_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Prompt set not found: {prompt_set_id}")

            created_at = self._deserialize_datetime(row["created_at"])
            if created_at is None:
                created_at = datetime.now()
            assert created_at is not None

            prompt_set = PromptSet(
                prompt_set_id=row["prompt_set_id"],
                name=row["name"],
                description=row["description"] or "",
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                created_at=created_at,
            )

            item_rows = conn.execute(
                """
                SELECT prompt_id, role, item_order, metadata
                FROM prompt_set_items
                WHERE prompt_set_id = ?
                ORDER BY item_order, id
                """,
                (prompt_set_id,),
            ).fetchall()

            items = [
                PromptSetItem(
                    prompt_set_id=prompt_set_id,
                    prompt_id=item["prompt_id"],
                    role=item["role"],
                    item_order=item["item_order"] or 0,
                    metadata=json.loads(item["metadata"]) if item["metadata"] else {},
                )
                for item in item_rows
            ]

            prompt_ids = [item.prompt_id for item in items]
            prompts: list[Prompt] = []
            if prompt_ids:
                placeholders = ", ".join("?" for _ in prompt_ids)
                prompt_rows = conn.execute(
                    f"""
                    SELECT prompt_id, name, kind, content, checksum, source,
                           notes, metadata, created_at
                    FROM prompts
                    WHERE prompt_id IN ({placeholders})
                    """,
                    tuple(prompt_ids),
                ).fetchall()
                for prompt_row in prompt_rows:
                    created_at = self._deserialize_datetime(prompt_row["created_at"])
                    if created_at is None:
                        created_at = datetime.now()
                    assert created_at is not None

                    prompts.append(
                        Prompt(
                            prompt_id=prompt_row["prompt_id"],
                            name=prompt_row["name"],
                            kind=prompt_row["kind"],
                            content=prompt_row["content"],
                            checksum=prompt_row["checksum"],
                            source=prompt_row["source"],
                            notes=prompt_row["notes"],
                            metadata=json.loads(prompt_row["metadata"])
                            if prompt_row["metadata"]
                            else {},
                            created_at=created_at,
                        )
                    )

            return PromptSetBundle(prompt_set=prompt_set, prompts=prompts, items=items)

    def get_prompt_set_for_run(self, run_id: str) -> PromptSetBundle | None:
        """Load the prompt set linked to a run."""
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            row = conn.execute(
                """
                SELECT prompt_set_id
                FROM run_prompt_sets
                WHERE run_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (run_id,),
            ).fetchone()
            if not row:
                return None
        return self.get_prompt_set(row["prompt_set_id"])

    # Experiment 관련 메서드

    def save_experiment(self, experiment: Experiment) -> str:
        """실험을 저장합니다.

        Args:
            experiment: 저장할 실험

        Returns:
            저장된 experiment의 ID
        """
        with self._get_connection() as conn:
            conn = cast(Any, conn)
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
            conn = cast(Any, conn)
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
            conn = cast(Any, conn)
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
            conn = cast(Any, conn)
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
            conn = cast(Any, conn)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO analysis_results (
                    analysis_id, run_id, analysis_type, result_data, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    run_id,
                    analysis_type,
                    json.dumps(payload, ensure_ascii=False),
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            return analysis_id

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
            conn = cast(Any, conn)
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
            conn = cast(Any, conn)
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
            conn = cast(Any, conn)
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
            conn = cast(Any, conn)
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
            conn = cast(Any, conn)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO analysis_results (
                    analysis_id, run_id, analysis_type, result_data, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    run_id,
                    AnalysisType.DATASET_FEATURES.value,
                    json.dumps(result_data, ensure_ascii=False),
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            return analysis_id

    def get_dataset_feature_analysis(self, analysis_id: str) -> dict[str, Any]:
        """데이터셋 특성 분석 결과를 조회합니다."""
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT analysis_id, result_data
                FROM analysis_results
                WHERE analysis_id = ? AND analysis_type = ?
                """,
                (analysis_id, AnalysisType.DATASET_FEATURES.value),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"Dataset feature analysis not found: {analysis_id}")

            return json.loads(row[1])

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
            conn = cast(Any, conn)
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
            conn = cast(Any, conn)
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

    # Pipeline result history 관련 메서드

    def save_pipeline_result(self, record: dict[str, Any]) -> None:
        """파이프라인 분석 결과 히스토리를 저장합니다."""
        created_at = record.get("created_at") or datetime.now().isoformat()
        is_complete = 1 if record.get("is_complete", False) else 0

        with self._get_connection() as conn:
            conn = cast(Any, conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO pipeline_results (
                    result_id, intent, query, run_id, pipeline_id,
                    profile, tags, metadata,
                    is_complete, duration_ms, final_output, node_results,
                    started_at, finished_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.get("result_id"),
                    record.get("intent"),
                    record.get("query"),
                    record.get("run_id"),
                    record.get("pipeline_id"),
                    record.get("profile"),
                    self._serialize_json(record.get("tags")),
                    self._serialize_json(record.get("metadata")),
                    is_complete,
                    record.get("duration_ms"),
                    self._serialize_json(record.get("final_output")),
                    self._serialize_json(record.get("node_results")),
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
        created_at = created_at or datetime.now().isoformat()

        with self._get_connection() as conn:
            conn = cast(Any, conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO analysis_reports (
                    report_id, run_id, experiment_id, report_type, format, content, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    run_id,
                    experiment_id,
                    report_type,
                    format,
                    content,
                    self._serialize_json(metadata),
                    created_at,
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
        query = (
            "SELECT report_id, run_id, experiment_id, report_type, format, content, metadata, created_at "
            "FROM analysis_reports WHERE run_id = ?"
        )
        params: list[Any] = [run_id]
        if report_type:
            query += " AND report_type = ?"
            params.append(report_type)
        if format:
            query += " AND format = ?"
            params.append(format)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            conn = cast(Any, conn)
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
                    "created_at": row["created_at"],
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
        created_at = created_at or datetime.now().isoformat()

        with self._get_connection() as conn:
            conn = cast(Any, conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO ops_reports (
                    report_id, run_id, report_type, format, content, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    run_id,
                    report_type,
                    format,
                    content,
                    self._serialize_json(metadata),
                    created_at,
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
        query = (
            "SELECT report_id, run_id, report_type, format, content, metadata, created_at "
            "FROM ops_reports WHERE run_id = ?"
        )
        params: list[Any] = [run_id]
        if report_type:
            query += " AND report_type = ?"
            params.append(report_type)
        if format:
            query += " AND format = ?"
            params.append(format)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            conn = cast(Any, conn)
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
                    "created_at": row["created_at"],
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
            LIMIT ?
        """
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            rows = conn.execute(query, (limit,)).fetchall()
        return [self._deserialize_pipeline_result(row, include_payload=False) for row in rows]

    def get_pipeline_result(self, result_id: str) -> dict[str, Any]:
        """저장된 파이프라인 분석 결과를 조회합니다."""
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            row = conn.execute(
                """
            SELECT result_id, intent, query, run_id, pipeline_id,
                   profile, tags, metadata,
                   is_complete, duration_ms, created_at,
                   started_at, finished_at, final_output, node_results
            FROM pipeline_results
            WHERE result_id = ?
            """,
                (result_id,),
            ).fetchone()
        if not row:
            raise KeyError(f"Pipeline result not found: {result_id}")
        return self._deserialize_pipeline_result(row, include_payload=True)

    def _deserialize_pipeline_result(
        self,
        row: sqlite3.Row,
        *,
        include_payload: bool,
    ) -> dict[str, Any]:
        item = {
            "result_id": row["result_id"],
            "intent": row["intent"],
            "query": row["query"],
            "run_id": row["run_id"],
            "pipeline_id": row["pipeline_id"],
            "profile": row["profile"],
            "tags": self._deserialize_json(row["tags"]),
            "is_complete": bool(row["is_complete"]),
            "duration_ms": self._maybe_float(row["duration_ms"]),
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
        }
        if include_payload:
            item["final_output"] = self._deserialize_json(row["final_output"])
            item["node_results"] = self._deserialize_json(row["node_results"])
            item["metadata"] = self._deserialize_json(row["metadata"])
        return item

    # Stage event/metric 관련 메서드

    def save_stage_event(self, event: StageEvent) -> str:
        """단계 이벤트를 저장합니다."""
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO stage_events (
                    run_id, stage_id, parent_stage_id, stage_type, stage_name,
                    status, attempt, started_at, finished_at, duration_ms,
                    input_ref, output_ref, attributes, metadata, trace_id, span_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._serialize_stage_event(event),
            )
            conn.commit()
        return event.stage_id

    def save_stage_events(self, events: list[StageEvent]) -> int:
        """여러 단계 이벤트를 저장합니다."""
        if not events:
            return 0
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            conn.executemany(
                """
                INSERT OR REPLACE INTO stage_events (
                    run_id, stage_id, parent_stage_id, stage_type, stage_name,
                    status, attempt, started_at, finished_at, duration_ms,
                    input_ref, output_ref, attributes, metadata, trace_id, span_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        """특정 실행의 단계 이벤트를 조회합니다."""
        query = """
            SELECT run_id, stage_id, parent_stage_id, stage_type, stage_name,
                   status, attempt, started_at, finished_at, duration_ms,
                   input_ref, output_ref, attributes, metadata, trace_id, span_id
            FROM stage_events
            WHERE run_id = ?
        """
        params: list[Any] = [run_id]
        if stage_type:
            query += " AND stage_type = ?"
            params.append(stage_type)
        query += " ORDER BY id"
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        return [self._deserialize_stage_event(row) for row in rows]

    def save_stage_metrics(self, metrics: list[StageMetric]) -> int:
        """여러 단계 메트릭을 저장합니다."""
        if not metrics:
            return 0
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            conn.executemany(
                """
                INSERT INTO stage_metrics (
                    run_id, stage_id, metric_name, score, threshold, evidence
                ) VALUES (?, ?, ?, ?, ?, ?)
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
        """특정 실행의 단계 메트릭을 조회합니다."""
        query = """
            SELECT run_id, stage_id, metric_name, score, threshold, evidence
            FROM stage_metrics
            WHERE run_id = ?
        """
        params: list[Any] = [run_id]
        if stage_id:
            query += " AND stage_id = ?"
            params.append(stage_id)
        if metric_name:
            query += " AND metric_name = ?"
            params.append(metric_name)
        query += " ORDER BY id"
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
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
            self._serialize_datetime(event.started_at),
            self._serialize_datetime(event.finished_at),
            event.duration_ms,
            self._serialize_payload_ref(event.input_ref),
            self._serialize_payload_ref(event.output_ref),
            self._serialize_json(event.attributes),
            self._serialize_json(event.metadata),
            event.trace_id,
            event.span_id,
        )

    def _deserialize_stage_event(self, row: sqlite3.Row) -> StageEvent:
        return StageEvent(
            run_id=row["run_id"],
            stage_id=row["stage_id"],
            parent_stage_id=row["parent_stage_id"],
            stage_type=row["stage_type"],
            stage_name=row["stage_name"],
            status=row["status"],
            attempt=row["attempt"],
            started_at=self._deserialize_datetime(row["started_at"]),
            finished_at=self._deserialize_datetime(row["finished_at"]),
            duration_ms=self._maybe_float(row["duration_ms"]),
            input_ref=self._deserialize_payload_ref(row["input_ref"]),
            output_ref=self._deserialize_payload_ref(row["output_ref"]),
            attributes=self._deserialize_json(row["attributes"]) or {},
            metadata=self._deserialize_json(row["metadata"]) or {},
            trace_id=row["trace_id"],
            span_id=row["span_id"],
        )

    def _serialize_stage_metric(self, metric: StageMetric) -> tuple[Any, ...]:
        return (
            metric.run_id,
            metric.stage_id,
            metric.metric_name,
            metric.score,
            metric.threshold,
            self._serialize_json(metric.evidence),
        )

    def _deserialize_stage_metric(self, row: sqlite3.Row) -> StageMetric:
        return StageMetric(
            run_id=row["run_id"],
            stage_id=row["stage_id"],
            metric_name=row["metric_name"],
            score=self._maybe_float(row["score"]) or 0.0,
            threshold=self._maybe_float(row["threshold"]),
            evidence=self._deserialize_json(row["evidence"]),
        )

    def _serialize_payload_ref(self, ref: StagePayloadRef | None) -> str | None:
        if ref is None:
            return None
        return json.dumps(ref.to_dict(), ensure_ascii=False)

    def _deserialize_payload_ref(self, raw: Any) -> StagePayloadRef | None:
        payload = self._deserialize_json(raw)
        if not payload:
            return None
        if isinstance(payload, dict):
            return StagePayloadRef.from_dict(payload)
        return None

    def save_benchmark_run(self, run: BenchmarkRun) -> str:
        with self._get_connection() as conn:
            conn = cast(Any, conn)
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

            conn.execute(
                """
                INSERT OR REPLACE INTO benchmark_runs (
                    run_id, benchmark_type, model_name, backend, tasks,
                    status, task_scores, overall_accuracy, num_fewshot,
                    started_at, finished_at, duration_seconds,
                    error_message, phoenix_trace_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
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
                ),
            )
            conn.commit()
        return run.run_id

    def get_benchmark_run(self, run_id: str) -> BenchmarkRun:
        from evalvault.domain.entities.benchmark_run import (
            BenchmarkRun,
            BenchmarkStatus,
            BenchmarkTaskScore,
            BenchmarkType,
        )

        with self._get_connection() as conn:
            conn = cast(Any, conn)
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

        tasks_raw = row["tasks"]
        tasks = json.loads(tasks_raw) if tasks_raw else []

        metadata_raw = row["metadata"]
        metadata = json.loads(metadata_raw) if metadata_raw else {}

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

    def list_benchmark_runs(
        self,
        benchmark_type: str | None = None,
        model_name: str | None = None,
        limit: int = 100,
    ) -> list[BenchmarkRun]:
        query = """
            SELECT run_id FROM benchmark_runs WHERE 1=1
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
            conn = cast(Any, conn)
            cursor = conn.execute(query, params)
            run_ids = [row["run_id"] for row in cursor.fetchall()]

        return [self.get_benchmark_run(run_id) for run_id in run_ids]

    def delete_benchmark_run(self, run_id: str) -> bool:
        with self._get_connection() as conn:
            conn = cast(Any, conn)
            cursor = conn.execute(
                "DELETE FROM benchmark_runs WHERE run_id = ?",
                (run_id,),
            )
            deleted = cursor.rowcount > 0
            conn.commit()
        return deleted
