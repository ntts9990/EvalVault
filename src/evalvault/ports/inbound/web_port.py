"""Web UI inbound port interface."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Protocol

if TYPE_CHECKING:
    from evalvault.domain.entities import EvaluationRun
    from evalvault.domain.entities.stage import StageEvent, StageMetric


@dataclass
class EvalRequest:
    """평가 실행 요청."""

    dataset_path: str
    metrics: list[str]
    model_name: str = "ollama/qwen3:14b"
    evaluation_task: str = "qa"
    langfuse_enabled: bool = False
    thresholds: dict[str, float] = field(default_factory=dict)
    threshold_profile: str | None = None
    parallel: bool = True
    batch_size: int = 5
    project_name: str | None = None
    retriever_config: dict[str, Any] | None = None
    memory_config: dict[str, Any] | None = None
    tracker_config: dict[str, Any] | None = None
    stage_store: bool = False
    prompt_config: dict[str, Any] | None = None
    system_prompt: str | None = None
    system_prompt_name: str | None = None
    prompt_set_name: str | None = None
    prompt_set_description: str | None = None
    ragas_prompt_overrides: dict[str, str] | None = None


@dataclass
class EvalProgress:
    """평가 진행 상태."""

    current: int
    total: int
    current_metric: str
    percent: float
    status: str = "running"  # running, completed, failed
    error_message: str | None = None
    elapsed_seconds: float | None = None
    eta_seconds: float | None = None
    rate: float | None = None


@dataclass
class RunSummary:
    """평가 실행 요약."""

    run_id: str
    dataset_name: str
    model_name: str
    pass_rate: float
    total_test_cases: int
    started_at: datetime
    finished_at: datetime | None
    metrics_evaluated: list[str]
    passed_test_cases: int = 0
    run_mode: str | None = None
    evaluation_task: str | None = None
    threshold_profile: str | None = None
    total_tokens: int = 0
    total_cost_usd: float | None = None
    phoenix_precision: float | None = None
    phoenix_drift: float | None = None
    phoenix_experiment_url: str | None = None
    phoenix_dataset_url: str | None = None
    phoenix_prompts: list[dict[str, Any]] = field(default_factory=list)
    project_name: str | None = None
    avg_metric_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class RunFilters:
    """평가 목록 필터."""

    dataset_name: str | None = None
    model_name: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    min_pass_rate: float | None = None
    max_pass_rate: float | None = None
    run_mode: str | None = None
    project_names: list[str] = field(default_factory=list)


class WebUIPort(Protocol):
    """웹 UI 인바운드 포트.

    웹 UI가 도메인 서비스에 접근하기 위한 인터페이스입니다.
    CLI와 마찬가지로 도메인 서비스를 호출하여 평가, 분석, 보고서 생성 등을 수행합니다.
    """

    async def run_evaluation(
        self,
        request: EvalRequest,
        *,
        on_progress: Callable[[EvalProgress], None] | None = None,
    ) -> EvaluationRun:
        """평가 실행.

        Args:
            request: 평가 실행 요청
            on_progress: 진행률 콜백 함수

        Returns:
            평가 실행 결과
        """
        ...

    def list_runs(
        self,
        limit: int = 50,
        offset: int = 0,
        filters: RunFilters | None = None,
    ) -> list[RunSummary]:
        """평가 목록 조회.

        Args:
            limit: 최대 조회 개수
            offset: 조회 시작 위치
            filters: 필터 조건

        Returns:
            평가 실행 요약 목록
        """
        ...

    def get_run_details(self, run_id: str) -> EvaluationRun:
        """평가 상세 조회.

        Args:
            run_id: 평가 실행 ID

        Returns:
            평가 실행 상세 정보

        Raises:
            KeyError: 평가를 찾을 수 없는 경우
        """
        ...

    def delete_run(self, run_id: str) -> bool:
        """평가 삭제.

        Args:
            run_id: 삭제할 평가 ID

        Returns:
            삭제 성공 여부
        """
        ...

    def generate_report(
        self,
        run_id: str,
        output_format: Literal["markdown", "html"] = "markdown",
        *,
        include_nlp: bool = True,
        include_causal: bool = True,
        use_cache: bool = True,
        save: bool = False,
    ) -> str:
        """보고서 생성.

        Args:
            run_id: 평가 실행 ID
            output_format: 출력 포맷 (markdown, html)
            include_nlp: NLP 분석 포함 여부
            include_causal: 인과 분석 포함 여부
            use_cache: 캐시된 보고서 사용 여부
            save: DB 저장 여부

        Returns:
            생성된 보고서 문자열
        """
        ...

    def get_available_metrics(self) -> list[str]:
        """사용 가능한 메트릭 목록 조회.

        Returns:
            메트릭 이름 목록
        """
        ...

    def get_metric_specs(self) -> list[dict[str, object]]:
        """메트릭 스펙 목록 조회."""
        ...

    def list_stage_events(
        self,
        run_id: str,
        *,
        stage_type: str | None = None,
    ) -> list[StageEvent]:
        """Stage 이벤트 목록 조회."""
        ...

    def list_stage_metrics(
        self,
        run_id: str,
        *,
        stage_id: str | None = None,
        metric_name: str | None = None,
    ) -> list[StageMetric]:
        """Stage 메트릭 목록 조회."""
        ...
