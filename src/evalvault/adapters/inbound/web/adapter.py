"""Web UI adapter implementing WebUIPort."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

from evalvault.ports.inbound.web_port import (
    EvalProgress,
    EvalRequest,
    RunFilters,
    RunSummary,
)

if TYPE_CHECKING:
    from evalvault.domain.entities import EvaluationRun
    from evalvault.ports.outbound.storage_port import StoragePort

logger = logging.getLogger(__name__)

# 지원하는 메트릭 목록
AVAILABLE_METRICS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "factual_correctness",
    "semantic_similarity",
    "insurance_term_accuracy",
]


class WebUIAdapter:
    """웹 UI 어댑터.

    WebUIPort 프로토콜을 구현하여 웹 UI가 도메인 서비스에
    접근할 수 있도록 합니다.
    """

    def __init__(
        self,
        storage: StoragePort | None = None,
        evaluator: object | None = None,
        report_generator: object | None = None,
    ):
        """어댑터 초기화.

        Args:
            storage: 저장소 어댑터 (선택적)
            evaluator: 평가 서비스 (선택적)
            report_generator: 보고서 생성기 (선택적)
        """
        self._storage = storage
        self._evaluator = evaluator
        self._report_generator = report_generator

    def run_evaluation(
        self,
        request: EvalRequest,
        *,
        on_progress: Callable[[EvalProgress], None] | None = None,
    ) -> EvaluationRun:
        """평가 실행.

        Args:
            request: 평가 요청
            on_progress: 진행률 콜백

        Returns:
            평가 결과
        """
        # TODO: 실제 평가 로직 구현
        # 현재는 CLI의 run 명령어 로직을 재사용할 예정
        raise NotImplementedError("Evaluation execution not yet implemented")

    def list_runs(
        self,
        limit: int = 50,
        filters: RunFilters | None = None,
    ) -> list[RunSummary]:
        """평가 목록 조회.

        Args:
            limit: 최대 조회 개수
            filters: 필터 조건

        Returns:
            평가 요약 목록
        """
        if self._storage is None:
            logger.warning("Storage not configured, returning empty list")
            return []

        try:
            # 저장소에서 평가 목록 조회
            runs = self._storage.list_runs(limit=limit)

            # RunSummary로 변환
            summaries = []
            for run in runs:
                summary = RunSummary(
                    run_id=run.run_id,
                    dataset_name=run.dataset_name,
                    model_name=run.model_name,
                    pass_rate=run.pass_rate,
                    total_test_cases=run.total_test_cases,
                    started_at=run.started_at,
                    finished_at=run.finished_at,
                    metrics_evaluated=run.metrics_evaluated,
                    total_tokens=run.total_tokens,
                    total_cost_usd=run.total_cost_usd,
                )

                # 필터 적용
                if filters:
                    if filters.dataset_name and filters.dataset_name != summary.dataset_name:
                        continue
                    if filters.model_name and filters.model_name != summary.model_name:
                        continue
                    if filters.min_pass_rate and summary.pass_rate < filters.min_pass_rate:
                        continue
                    if filters.max_pass_rate and summary.pass_rate > filters.max_pass_rate:
                        continue

                summaries.append(summary)

            return summaries

        except Exception as e:
            logger.error(f"Failed to list runs: {e}")
            return []

    def get_run_details(self, run_id: str) -> EvaluationRun:
        """평가 상세 조회.

        Args:
            run_id: 평가 ID

        Returns:
            평가 상세 정보

        Raises:
            KeyError: 평가를 찾을 수 없는 경우
        """
        if self._storage is None:
            raise RuntimeError("Storage not configured")

        run = self._storage.get_run(run_id)
        if run is None:
            raise KeyError(f"Run not found: {run_id}")

        return run

    def delete_run(self, run_id: str) -> bool:
        """평가 삭제.

        Args:
            run_id: 삭제할 평가 ID

        Returns:
            삭제 성공 여부
        """
        if self._storage is None:
            return False

        try:
            return self._storage.delete_run(run_id)
        except Exception as e:
            logger.error(f"Failed to delete run {run_id}: {e}")
            return False

    def generate_report(
        self,
        run_id: str,
        output_format: Literal["markdown", "html"] = "markdown",
        *,
        include_nlp: bool = True,
        include_causal: bool = True,
    ) -> str:
        """보고서 생성.

        Args:
            run_id: 평가 ID
            output_format: 출력 포맷
            include_nlp: NLP 분석 포함 여부
            include_causal: 인과 분석 포함 여부

        Returns:
            생성된 보고서
        """
        # TODO: 실제 보고서 생성 로직 구현
        raise NotImplementedError("Report generation not yet implemented")

    def get_available_metrics(self) -> list[str]:
        """사용 가능한 메트릭 목록 반환."""
        return AVAILABLE_METRICS.copy()

    def get_metric_descriptions(self) -> dict[str, str]:
        """메트릭별 설명 반환."""
        return {
            "faithfulness": "답변이 컨텍스트에 충실한지 평가",
            "answer_relevancy": "답변이 질문과 관련있는지 평가",
            "context_precision": "검색된 컨텍스트의 정밀도 평가",
            "context_recall": "필요한 정보가 검색되었는지 평가",
            "factual_correctness": "ground_truth 대비 사실적 정확성 평가",
            "semantic_similarity": "답변과 ground_truth 간 의미적 유사도 평가",
            "insurance_term_accuracy": "보험 용어 정확성 평가",
        }


def create_adapter() -> WebUIAdapter:
    """WebUIAdapter 인스턴스 생성 팩토리.

    설정에 따라 적절한 저장소와 서비스를 주입합니다.
    """
    # TODO: 실제 설정에서 저장소와 서비스 로드
    return WebUIAdapter()
