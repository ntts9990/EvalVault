"""Session state management for Streamlit web UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evalvault.ports.inbound.web_port import EvalProgress, RunSummary


@dataclass
class WebSession:
    """웹 세션 상태.

    Streamlit의 session_state를 래핑하여 타입 안전성을 제공합니다.
    """

    # 현재 작업 상태
    current_run_id: str | None = None
    is_evaluating: bool = False
    eval_progress: EvalProgress | None = None
    eval_task_id: str | None = None

    # 선택 상태
    selected_dataset: str | None = None
    selected_model: str | None = None
    selected_metrics: list[str] = field(default_factory=list)

    # 평가 옵션
    langfuse_enabled: bool = False
    parallel_processing: bool = True

    # 필터 상태
    filter_dataset: str | None = None
    filter_model: str | None = None
    filter_pass_rate: float = 0.0

    # 보고서 상태
    selected_report_run_id: str | None = None
    report_format: str = "Markdown"
    include_nlp: bool = True
    include_causal: bool = True

    # 캐시
    runs_cache: list[RunSummary] | None = None
    cache_updated_at: datetime | None = None

    # UI 상태
    show_advanced_options: bool = False
    selected_tab: str = "home"

    @classmethod
    def get(cls) -> WebSession:
        """Streamlit 세션에서 WebSession 인스턴스 가져오기.

        없으면 새로 생성합니다.
        """
        try:
            import streamlit as st

            if "web_session" not in st.session_state:
                st.session_state.web_session = cls()
            return st.session_state.web_session
        except ImportError:
            # Streamlit이 없는 환경 (테스트 등)
            return cls()

    def invalidate_cache(self) -> None:
        """캐시 무효화."""
        self.runs_cache = None
        self.cache_updated_at = None

    def reset_evaluation_state(self) -> None:
        """평가 상태 초기화."""
        self.is_evaluating = False
        self.eval_progress = None
        self.eval_task_id = None

    def set_evaluation_started(self, task_id: str) -> None:
        """평가 시작 상태 설정."""
        self.is_evaluating = True
        self.eval_task_id = task_id
        self.eval_progress = None

    def update_progress(self, progress: EvalProgress) -> None:
        """진행률 업데이트."""
        self.eval_progress = progress

    def set_evaluation_completed(self, run_id: str) -> None:
        """평가 완료 상태 설정."""
        self.is_evaluating = False
        self.current_run_id = run_id
        self.eval_task_id = None
        self.invalidate_cache()

    def get_default_metrics(self) -> list[str]:
        """기본 메트릭 목록 반환."""
        if self.selected_metrics:
            return self.selected_metrics
        return ["faithfulness", "answer_relevancy"]


def init_session() -> WebSession:
    """세션 초기화 헬퍼 함수."""
    return WebSession.get()
