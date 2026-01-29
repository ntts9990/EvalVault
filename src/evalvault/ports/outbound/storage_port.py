"""결과 저장 인터페이스."""

from pathlib import Path
from typing import Any, Protocol

from evalvault.domain.entities import (
    EvaluationRun,
    FeedbackSummary,
    MultiTurnConversationRecord,
    MultiTurnRunRecord,
    MultiTurnTurnResult,
    PromptSetBundle,
    RunClusterMap,
    RunClusterMapInfo,
    SatisfactionFeedback,
)
from evalvault.domain.entities.experiment import Experiment
from evalvault.domain.entities.stage import StageEvent, StageMetric


class StoragePort(Protocol):
    """평가 결과 저장을 위한 포트 인터페이스.

    SQLite, PostgreSQL 등 다양한 저장소에 평가 결과를 저장합니다.
    """

    def save_run(self, run: EvaluationRun) -> str:
        """평가 실행 결과를 저장합니다.

        Args:
            run: 저장할 평가 실행 결과

        Returns:
            저장된 run의 ID
        """
        ...

    def save_multiturn_run(
        self,
        run: MultiTurnRunRecord,
        conversations: list[MultiTurnConversationRecord],
        turn_results: list[MultiTurnTurnResult],
        *,
        metric_thresholds: dict[str, float] | None = None,
    ) -> str:
        """멀티턴 평가 실행 결과를 저장합니다."""
        ...

    def save_prompt_set(self, bundle: PromptSetBundle) -> None:
        """Persist prompt set and prompt items."""
        ...

    def export_run_to_excel(self, run_id: str, output_path: str | Path) -> Path: ...

    def export_multiturn_run_to_excel(self, run_id: str, output_path: str | Path) -> Path: ...

    def link_prompt_set_to_run(self, run_id: str, prompt_set_id: str) -> None:
        """Attach a prompt set to an evaluation run."""
        ...

    def get_prompt_set(self, prompt_set_id: str) -> PromptSetBundle:
        """Load a prompt set bundle."""
        ...

    def get_prompt_set_for_run(self, run_id: str) -> PromptSetBundle | None:
        """Load the prompt set bundle linked to a run."""
        ...

    def get_run(self, run_id: str) -> EvaluationRun:
        """저장된 평가 실행 결과를 조회합니다.

        Args:
            run_id: 조회할 run의 ID

        Returns:
            EvaluationRun 객체

        Raises:
            KeyError: run_id에 해당하는 결과가 없는 경우
        """
        ...

    def list_runs(
        self,
        limit: int = 100,
        offset: int = 0,
        dataset_name: str | None = None,
        model_name: str | None = None,
    ) -> list[EvaluationRun]:
        """저장된 평가 실행 결과 목록을 조회합니다.

        Args:
            limit: 최대 조회 개수
            offset: 조회 시작 위치 (선택)
            dataset_name: 필터링할 데이터셋 이름 (선택)
            model_name: 필터링할 모델 이름 (선택)

        Returns:
            EvaluationRun 객체 리스트 (최신순)
        """
        ...

    def delete_run(self, run_id: str) -> bool: ...

    def save_stage_events(self, events: list[StageEvent]) -> int: ...

    def save_stage_metrics(self, metrics: list[StageMetric]) -> int: ...

    def list_stage_events(
        self,
        run_id: str,
        *,
        stage_type: str | None = None,
    ) -> list[StageEvent]: ...

    def list_stage_metrics(
        self,
        run_id: str,
        *,
        stage_id: str | None = None,
        metric_name: str | None = None,
    ) -> list[StageMetric]: ...

    def update_run_metadata(self, run_id: str, metadata: dict[str, Any]) -> None: ...

    def save_run_cluster_map(
        self,
        run_id: str,
        mapping: dict[str, str],
        source: str | None = None,
        map_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """런별 클러스터 맵을 저장합니다."""
        ...

    def get_run_cluster_map(self, run_id: str, map_id: str | None = None) -> RunClusterMap | None:
        """런별 클러스터 맵을 조회합니다."""
        ...

    def list_run_cluster_maps(self, run_id: str) -> list[RunClusterMapInfo]:
        """런별 클러스터 맵 버전을 조회합니다."""
        ...

    def delete_run_cluster_map(self, run_id: str, map_id: str) -> int:
        """런별 클러스터 맵을 삭제합니다."""
        ...

    def save_feedback(self, feedback: SatisfactionFeedback) -> str: ...

    def list_feedback(self, run_id: str) -> list[SatisfactionFeedback]: ...

    def get_feedback_summary(self, run_id: str) -> FeedbackSummary: ...

    # Experiment 관련 메서드

    def save_experiment(self, experiment: Experiment) -> str:
        """실험을 저장합니다.

        Args:
            experiment: 저장할 실험

        Returns:
            저장된 experiment의 ID
        """
        ...

    def get_experiment(self, experiment_id: str) -> Experiment:
        """실험을 조회합니다.

        Args:
            experiment_id: 조회할 실험 ID

        Returns:
            Experiment 객체

        Raises:
            KeyError: 실험을 찾을 수 없는 경우
        """
        ...

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
        ...

    def update_experiment(self, experiment: Experiment) -> None:
        """실험을 업데이트합니다.

        Args:
            experiment: 업데이트할 실험
        """
        ...

    # Pipeline result history 메서드

    def save_pipeline_result(self, record: dict[str, Any]) -> None:
        """파이프라인 분석 결과 히스토리를 저장합니다."""
        ...

    def save_analysis_result(
        self,
        *,
        run_id: str,
        analysis_type: str,
        result_data: dict[str, Any],
        analysis_id: str | None = None,
    ) -> str:
        """분석 결과(JSON)를 저장합니다."""
        ...

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
    ) -> str: ...

    def list_analysis_reports(
        self,
        *,
        run_id: str,
        report_type: str | None = None,
        format: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]: ...

    def list_pipeline_results(self, limit: int = 50) -> list[dict[str, Any]]:
        """파이프라인 분석 결과 목록을 조회합니다."""
        ...

    def get_pipeline_result(self, result_id: str) -> dict[str, Any]:
        """저장된 파이프라인 분석 결과를 조회합니다."""
        ...

    def export_analysis_results_to_excel(self, run_id: str, output_path: Path) -> Path:
        """분석 결과를 Excel로 내보냅니다."""
        ...

    def set_regression_baseline(
        self,
        baseline_key: str,
        run_id: str,
        *,
        dataset_name: str | None = None,
        branch: str | None = None,
        commit_sha: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """회귀 테스트 베이스라인을 설정합니다."""
        ...

    def get_regression_baseline(self, baseline_key: str) -> dict[str, Any] | None:
        """회귀 테스트 베이스라인을 조회합니다."""
        ...
