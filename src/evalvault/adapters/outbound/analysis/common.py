"""공통 분석 어댑터 유틸리티."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from evalvault.domain.entities import EvaluationRun


class AnalysisDataProcessor:
    """분석 어댑터 전반에서 공유하는 데이터 처리 유틸리티."""

    def extract_metric_scores(
        self,
        run: EvaluationRun,
        metrics: Iterable[str] | None = None,
    ) -> dict[str, list[float]]:
        """EvaluationRun에서 메트릭별 점수 리스트를 추출합니다."""
        target_metrics = set(metrics) if metrics else None
        metric_scores: dict[str, list[float]] = defaultdict(list)

        for result in run.results:
            for metric in result.metrics:
                if target_metrics and metric.name not in target_metrics:
                    continue
                metric_scores[metric.name].append(metric.score)

        if target_metrics:
            return {metric: metric_scores.get(metric, []) for metric in target_metrics}
        return dict(metric_scores)

    def calculate_metric_pass_rates(self, run: EvaluationRun) -> dict[str, float]:
        """각 메트릭의 pass rate를 계산합니다."""
        if not run.results:
            return {}

        totals: dict[str, int] = defaultdict(int)
        passes: dict[str, int] = defaultdict(int)

        for result in run.results:
            for metric in result.metrics:
                totals[metric.name] += 1
                threshold = metric.threshold
                if threshold is None:
                    threshold = run.thresholds.get(metric.name, 0.0)
                if metric.score >= threshold:
                    passes[metric.name] += 1

        return {
            metric: (passes[metric] / totals[metric]) if totals[metric] else 0.0
            for metric in totals
        }

    def collect_text_fields(self, run: EvaluationRun) -> dict[str, list[str]]:
        """질문/답변/컨텍스트 텍스트 목록을 수집합니다."""
        questions: list[str] = []
        answers: list[str] = []
        contexts: list[str] = []

        for result in run.results:
            if result.question:
                questions.append(result.question)
            if result.answer:
                answers.append(result.answer)
            if result.contexts:
                contexts.extend(result.contexts)

        return {
            "questions": questions,
            "answers": answers,
            "contexts": contexts,
        }

    def ensure_min_samples(self, run: EvaluationRun, *, minimum: int) -> bool:
        """평가 실행이 최소 샘플 수를 충족하는지 확인합니다."""
        return len(run.results) >= minimum

    def to_serializable(self, value: Any) -> Any:
        """데이터 클래스를 포함한 객체를 직렬화 가능한 형태로 변환."""
        if value is None:
            return None
        if is_dataclass(value):
            return self.to_serializable(asdict(value))
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {key: self.to_serializable(val) for key, val in value.items()}
        if isinstance(value, list | tuple):
            return [self.to_serializable(item) for item in value]
        return value

    def build_output_payload(
        self,
        analysis: Any | None,
        *,
        summary: dict[str, Any] | None = None,
        statistics: dict[str, Any] | None = None,
        insights: Iterable[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """파이프라인 모듈이 공통 포맷으로 결과를 노출하도록 정규화."""
        resolved_insights: list[str] = []
        if insights is not None:
            resolved_insights = list(insights)
        elif analysis is not None and hasattr(analysis, "insights"):
            resolved_insights = list(getattr(analysis, "insights", []) or [])

        payload: dict[str, Any] = {
            "analysis": analysis,
            "summary": summary or {},
            "statistics": statistics or {},
            "insights": resolved_insights,
        }

        if analysis is not None:
            payload["analysis_id"] = getattr(analysis, "analysis_id", None)
            payload["run_id"] = getattr(analysis, "run_id", None)

        if extra:
            payload.update(extra)

        return payload


class BaseAnalysisAdapter(ABC):
    """분석 어댑터 공통 베이스 클래스."""

    def __init__(self) -> None:
        self.processor = AnalysisDataProcessor()

    @abstractmethod
    def analyze(self, run: EvaluationRun, **kwargs: Any):
        """분석 수행."""
        raise NotImplementedError

    def has_enough_samples(self, run: EvaluationRun, *, minimum: int = 1) -> bool:
        """분석에 필요한 최소 샘플 수 확인."""
        return self.processor.ensure_min_samples(run, minimum=minimum)

    def build_module_output(
        self,
        analysis: Any | None,
        *,
        summary: dict[str, Any] | None = None,
        statistics: dict[str, Any] | None = None,
        insights: Iterable[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """분석 모듈이 재사용 가능한 공통 출력 포맷을 가질 수 있도록 조립."""
        return self.processor.build_output_payload(
            analysis,
            summary=summary,
            statistics=statistics,
            insights=insights,
            extra=extra,
        )
