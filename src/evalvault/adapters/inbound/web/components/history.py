"""History page components."""

from __future__ import annotations

import csv
import io
import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

    from evalvault.ports.inbound.web_port import RunFilters, RunSummary

from evalvault.domain.services.prompt_status import format_prompt_summary_label


@dataclass
class RunFilter:
    """평가 실행 필터.

    다양한 조건으로 실행 목록을 필터링합니다.
    """

    dataset_name: str | None = None
    model_name: str | None = None
    min_pass_rate: float | None = None
    max_pass_rate: float | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    metrics: list[str] = field(default_factory=list)
    run_mode: str | None = None
    project_names: list[str] = field(default_factory=list)

    def apply(self, runs: list[RunSummary]) -> list[RunSummary]:
        """필터 적용.

        Args:
            runs: 필터링할 실행 목록

        Returns:
            필터링된 실행 목록
        """
        filtered = runs

        if self.dataset_name:
            filtered = [r for r in filtered if r.dataset_name == self.dataset_name]

        if self.model_name:
            filtered = [r for r in filtered if r.model_name == self.model_name]

        if self.min_pass_rate is not None:
            filtered = [r for r in filtered if r.pass_rate >= self.min_pass_rate]

        if self.max_pass_rate is not None:
            filtered = [r for r in filtered if r.pass_rate <= self.max_pass_rate]

        if self.date_from:
            filtered = [r for r in filtered if r.started_at >= self.date_from]

        if self.date_to:
            filtered = [r for r in filtered if r.started_at <= self.date_to]

        if self.metrics:
            filtered = [r for r in filtered if any(m in r.metrics_evaluated for m in self.metrics)]
        if self.run_mode:
            filtered = [
                r for r in filtered if r.run_mode and r.run_mode.lower() == self.run_mode.lower()
            ]
        if self.project_names:
            filtered = [r for r in filtered if r.project_name in self.project_names]

        return filtered

    def to_run_filters(self) -> RunFilters:
        """RunFilters 객체로 변환.

        Returns:
            RunFilters 인스턴스
        """
        from evalvault.ports.inbound.web_port import RunFilters

        return RunFilters(
            dataset_name=self.dataset_name,
            model_name=self.model_name,
            min_pass_rate=self.min_pass_rate,
            max_pass_rate=self.max_pass_rate,
            date_from=self.date_from,
            date_to=self.date_to,
            run_mode=self.run_mode,
            project_names=self.project_names,
        )

    def is_empty(self) -> bool:
        """필터가 비어있는지 확인."""
        return all(
            v is None or v == []
            for v in [
                self.dataset_name,
                self.model_name,
                self.min_pass_rate,
                self.max_pass_rate,
                self.date_from,
                self.date_to,
                self.metrics if self.metrics else None,
                self.run_mode,
                self.project_names if self.project_names else None,
            ]
        )


@dataclass
class RunTable:
    """평가 실행 테이블.

    페이지네이션과 정렬을 지원하는 테이블 컴포넌트입니다.
    """

    runs: list[RunSummary]
    page: int = 1
    page_size: int = 10
    sort_column: str = "date"
    sort_ascending: bool = False

    @property
    def total_pages(self) -> int:
        """총 페이지 수."""
        return math.ceil(len(self.runs) / self.page_size)

    def get_current_page_runs(self) -> list[RunSummary]:
        """현재 페이지의 실행 목록.

        Returns:
            현재 페이지에 해당하는 실행 목록
        """
        start = (self.page - 1) * self.page_size
        end = start + self.page_size
        return self.runs[start:end]

    def sort_by(self, column: str, ascending: bool = True) -> list[RunSummary]:
        """정렬.

        Args:
            column: 정렬 기준 컬럼
            ascending: 오름차순 여부

        Returns:
            정렬된 실행 목록
        """
        self.sort_column = column
        self.sort_ascending = ascending

        key_funcs = {
            "date": lambda r: r.started_at,
            "pass_rate": lambda r: r.pass_rate,
            "dataset": lambda r: r.dataset_name,
            "model": lambda r: r.model_name,
        }
        key_func = key_funcs.get(column, key_funcs["date"])

        sorted_runs = sorted(self.runs, key=key_func, reverse=not ascending)
        self.runs = sorted_runs
        return sorted_runs

    def to_dataframe(self) -> pd.DataFrame:
        """DataFrame으로 변환.

        Returns:
            pandas DataFrame
        """
        import pandas as pd

        data = []
        for run in self.runs:
            data.append(
                {
                    "run_id": run.run_id,
                    "dataset_name": run.dataset_name,
                    "project_name": run.project_name,
                    "run_mode": run.run_mode,
                    "model_name": run.model_name,
                    "pass_rate": run.pass_rate,
                    "total_test_cases": run.total_test_cases,
                    "started_at": run.started_at,
                    "metrics": ", ".join(run.metrics_evaluated),
                    "tokens": run.total_tokens,
                    "cost": run.total_cost_usd,
                    "phoenix_precision": run.phoenix_precision,
                    "phoenix_drift": run.phoenix_drift,
                    "phoenix_experiment_url": run.phoenix_experiment_url,
                    "phoenix_prompt_summary": format_prompt_summary_label(run.phoenix_prompts)
                    if run.phoenix_prompts
                    else None,
                    "phoenix_prompts": run.phoenix_prompts,
                }
            )

        return pd.DataFrame(data)


@dataclass
class RunDetailPanel:
    """평가 실행 상세 패널.

    선택된 실행의 상세 정보를 표시합니다.
    """

    run: RunSummary
    metric_scores: dict[str, float] = field(default_factory=dict)

    def get_summary_stats(self) -> dict:
        """요약 통계.

        Returns:
            통계 딕셔너리
        """
        duration = None
        if self.run.finished_at and self.run.started_at:
            duration = (self.run.finished_at - self.run.started_at).total_seconds()

        return {
            "pass_rate": self.run.pass_rate,
            "total_test_cases": self.run.total_test_cases,
            "metrics_count": len(self.run.metrics_evaluated),
            "duration": duration,
            "total_tokens": self.run.total_tokens,
            "total_cost": self.run.total_cost_usd,
        }

    def get_metrics_breakdown(self) -> dict[str, float | None]:
        """메트릭별 점수.

        Returns:
            메트릭 이름과 점수 딕셔너리
        """
        breakdown = {}
        for metric in self.run.metrics_evaluated:
            # 저장된 점수가 있으면 사용, 없으면 None
            breakdown[metric] = self.metric_scores.get(metric)
        return breakdown

    def get_prompt_entries(self) -> list[dict[str, Any]]:
        """Prompt manifest 상태."""
        return list(getattr(self.run, "phoenix_prompts", []) or [])

    def format_duration(self) -> str:
        """소요 시간 포맷.

        Returns:
            포맷된 소요 시간 문자열
        """
        if not self.run.finished_at or not self.run.started_at:
            return "N/A"

        seconds = (self.run.finished_at - self.run.started_at).total_seconds()

        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"

    def get_pass_rate_status(self) -> str:
        """통과율 상태.

        Returns:
            상태 문자열
        """
        rate = self.run.pass_rate
        if rate >= 0.9:
            return "excellent"
        elif rate >= 0.7:
            return "good"
        elif rate >= 0.5:
            return "warning"
        else:
            return "critical"


@dataclass
class HistoryExporter:
    """이력 내보내기.

    실행 이력을 다양한 형식으로 내보냅니다.
    """

    runs: list[RunSummary]

    def to_csv(self) -> str:
        """CSV로 내보내기.

        Returns:
            CSV 문자열
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # 헤더
        writer.writerow(
            [
                "run_id",
                "dataset_name",
                "project_name",
                "run_mode",
                "model_name",
                "pass_rate",
                "total_test_cases",
                "started_at",
                "finished_at",
                "metrics",
                "tokens",
                "cost_usd",
                "phoenix_precision",
                "phoenix_drift",
                "phoenix_experiment_url",
                "phoenix_prompt_summary",
                "phoenix_prompts",
            ]
        )

        # 데이터
        for run in self.runs:
            writer.writerow(
                [
                    run.run_id,
                    run.dataset_name,
                    run.project_name or "",
                    run.run_mode or "",
                    run.model_name,
                    f"{run.pass_rate:.4f}",
                    run.total_test_cases,
                    run.started_at.isoformat() if run.started_at else "",
                    run.finished_at.isoformat() if run.finished_at else "",
                    ",".join(run.metrics_evaluated),
                    run.total_tokens,
                    f"{run.total_cost_usd:.4f}" if run.total_cost_usd else "",
                    f"{run.phoenix_precision:.4f}" if run.phoenix_precision is not None else "",
                    f"{run.phoenix_drift:.4f}" if run.phoenix_drift is not None else "",
                    run.phoenix_experiment_url or "",
                    format_prompt_summary_label(run.phoenix_prompts) or "",
                    json.dumps(run.phoenix_prompts, ensure_ascii=False)
                    if run.phoenix_prompts
                    else "",
                ]
            )

        return output.getvalue()

    def to_json(self) -> str:
        """JSON으로 내보내기.

        Returns:
            JSON 문자열
        """
        data = []
        for run in self.runs:
            data.append(
                {
                    "run_id": run.run_id,
                    "dataset_name": run.dataset_name,
                    "project_name": run.project_name,
                    "model_name": run.model_name,
                    "run_mode": run.run_mode,
                    "pass_rate": run.pass_rate,
                    "total_test_cases": run.total_test_cases,
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                    "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                    "metrics_evaluated": run.metrics_evaluated,
                    "total_tokens": run.total_tokens,
                    "total_cost_usd": run.total_cost_usd,
                    "phoenix_precision": run.phoenix_precision,
                    "phoenix_drift": run.phoenix_drift,
                    "phoenix_experiment_url": run.phoenix_experiment_url,
                    "phoenix_prompt_summary": format_prompt_summary_label(run.phoenix_prompts)
                    if run.phoenix_prompts
                    else None,
                    "phoenix_prompts": run.phoenix_prompts,
                }
            )

        return json.dumps(data, indent=2, ensure_ascii=False)


@dataclass
class RunSearch:
    """실행 검색.

    텍스트 검색으로 실행을 찾습니다.
    """

    query: str = ""

    def search(self, runs: list[RunSummary]) -> list[RunSummary]:
        """검색 수행.

        Args:
            runs: 검색할 실행 목록

        Returns:
            검색 결과
        """
        if not self.query:
            return runs

        query_lower = self.query.lower()

        return [
            r
            for r in runs
            if query_lower in r.dataset_name.lower()
            or query_lower in r.model_name.lower()
            or query_lower in r.run_id.lower()
            or (r.run_mode and query_lower in r.run_mode.lower())
            or (r.project_name and query_lower in r.project_name.lower())
        ]
