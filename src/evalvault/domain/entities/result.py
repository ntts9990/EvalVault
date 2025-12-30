"""Evaluation result entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class MetricType(str, Enum):
    """Ragas 평가 메트릭 타입."""

    FAITHFULNESS = "faithfulness"
    ANSWER_RELEVANCY = "answer_relevancy"
    CONTEXT_PRECISION = "context_precision"
    CONTEXT_RECALL = "context_recall"
    FACTUAL_CORRECTNESS = "factual_correctness"
    SEMANTIC_SIMILARITY = "semantic_similarity"


@dataclass
class MetricScore:
    """개별 메트릭 점수."""

    name: str  # MetricType value
    score: float  # 0.0 ~ 1.0
    threshold: float = 0.7  # SLA 임계값
    reason: str | None = None  # LLM 평가 이유 (있는 경우)

    @property
    def passed(self) -> bool:
        """threshold 통과 여부."""
        return self.score >= self.threshold


@dataclass
class TestCaseResult:
    """개별 테스트 케이스 결과."""

    __test__ = False

    test_case_id: str
    metrics: list[MetricScore]
    tokens_used: int = 0  # 총 토큰 사용량
    latency_ms: int = 0  # 응답 시간 (밀리초)
    cost_usd: float | None = None  # 비용 (계산 가능한 경우)
    trace_id: str | None = None  # Langfuse trace ID

    # 타이밍 정보 (Langfuse span timing용)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    # 원본 테스트 케이스 데이터 (Langfuse 로깅용)
    question: str | None = None
    answer: str | None = None
    contexts: list[str] | None = None
    ground_truth: str | None = None

    @property
    def all_passed(self) -> bool:
        """모든 메트릭이 threshold를 통과했는지."""
        return all(m.passed for m in self.metrics)

    def get_metric(self, name: str) -> MetricScore | None:
        """특정 메트릭 점수 조회."""
        for m in self.metrics:
            if m.name == name:
                return m
        return None


@dataclass
class EvaluationRun:
    """전체 평가 실행 결과."""

    run_id: str = field(default_factory=lambda: str(uuid4()))
    dataset_name: str = ""
    dataset_version: str = ""
    model_name: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None

    # 개별 결과
    results: list[TestCaseResult] = field(default_factory=list)

    # 메타데이터
    metrics_evaluated: list[str] = field(default_factory=list)
    thresholds: dict[str, float] = field(default_factory=dict)

    # 리소스 사용량
    total_tokens: int = 0
    total_cost_usd: float | None = None

    # Langfuse 연동
    langfuse_trace_id: str | None = None

    @property
    def total_test_cases(self) -> int:
        return len(self.results)

    @property
    def passed_test_cases(self) -> int:
        """모든 메트릭을 통과한 테스트 케이스 수 (strict)."""
        return sum(1 for r in self.results if r.all_passed)

    @property
    def strict_pass_rate(self) -> float:
        """모든 메트릭 통과 기준 통과율 (strict quality gate)."""
        if not self.results:
            return 0.0
        return self.passed_test_cases / self.total_test_cases

    @property
    def pass_rate(self) -> float:
        """메트릭 기준 통과율 (개별 메트릭 통과 비율).

        각 메트릭의 평균 점수가 임계값을 넘는 비율을 계산합니다.
        예: 7개 메트릭 중 4개가 평균적으로 임계값을 넘으면 4/7 = 57%
        """
        if not self.results or not self.metrics_evaluated:
            return 0.0

        passed_metrics = 0
        for metric_name in self.metrics_evaluated:
            avg_score = self.get_avg_score(metric_name)
            threshold = self._get_threshold(metric_name)
            if avg_score is not None and avg_score >= threshold:
                passed_metrics += 1

        return passed_metrics / len(self.metrics_evaluated)

    def _get_threshold(self, metric_name: str) -> float:
        """메트릭의 임계값 조회."""
        if self.thresholds and metric_name in self.thresholds:
            return self.thresholds[metric_name]
        # 결과에서 임계값 찾기
        for r in self.results:
            m = r.get_metric(metric_name)
            if m:
                return m.threshold
        return 0.7  # 기본값

    @property
    def duration_seconds(self) -> float | None:
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    def get_avg_score(self, metric_name: str) -> float | None:
        """특정 메트릭의 평균 점수."""
        scores = []
        for r in self.results:
            m = r.get_metric(metric_name)
            if m:
                scores.append(m.score)
        return sum(scores) / len(scores) if scores else None

    def to_summary_dict(self) -> dict[str, Any]:
        """요약 정보 딕셔너리."""
        summary = {
            "run_id": self.run_id,
            "dataset_name": self.dataset_name,
            "dataset_version": self.dataset_version,
            "model_name": self.model_name,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "total_test_cases": self.total_test_cases,
            "passed_test_cases": self.passed_test_cases,
            "pass_rate": self.pass_rate,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "duration_seconds": self.duration_seconds,
        }
        # 각 메트릭 평균
        for metric in self.metrics_evaluated:
            avg = self.get_avg_score(metric)
            summary[f"avg_{metric}"] = avg
        return summary
