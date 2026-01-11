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
class ClaimVerdict:
    """개별 claim 검증 결과.

    Attributes:
        claim_id: 고유 식별자 (예: "tc-001-claim-0")
        claim_text: 추출된 claim 텍스트
        verdict: 검증 결과 ("supported", "not_supported", "partially_supported")
        confidence: 신뢰도 (0.0 ~ 1.0)
        reason: 판정 이유
        source_context_indices: claim을 지지하는 컨텍스트 인덱스
    """

    claim_id: str
    claim_text: str
    verdict: str  # "supported" | "not_supported" | "partially_supported"
    confidence: float = 0.0
    reason: str | None = None
    source_context_indices: list[int] | None = None

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "reason": self.reason,
            "source_context_indices": self.source_context_indices,
        }


@dataclass
class ClaimLevelResult:
    """Claim-level faithfulness 결과.

    Attributes:
        total_claims: 총 claim 수
        supported_claims: 지지된 claim 수
        not_supported_claims: 지지되지 않은 claim 수
        partially_supported_claims: 부분 지지 claim 수
        claims: 개별 claim 결과 리스트
        extraction_method: claim 추출 방법 ("korean_nlp", "ragas", "sentence")
    """

    total_claims: int = 0
    supported_claims: int = 0
    not_supported_claims: int = 0
    partially_supported_claims: int = 0
    claims: list[ClaimVerdict] = field(default_factory=list)
    extraction_method: str = "korean_nlp"

    @property
    def support_rate(self) -> float:
        """지지율 계산."""
        if self.total_claims == 0:
            return 1.0
        return self.supported_claims / self.total_claims

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            "total_claims": self.total_claims,
            "supported_claims": self.supported_claims,
            "not_supported_claims": self.not_supported_claims,
            "partially_supported_claims": self.partially_supported_claims,
            "support_rate": self.support_rate,
            "extraction_method": self.extraction_method,
            "claims": [c.to_dict() for c in self.claims],
        }


@dataclass
class MetricScore:
    """개별 메트릭 점수."""

    name: str  # MetricType value
    score: float  # 0.0 ~ 1.0
    threshold: float = 0.7  # SLA 임계값
    reason: str | None = None  # LLM 평가 이유 (있는 경우)
    claim_details: ClaimLevelResult | None = None  # Claim-level 세부 결과

    @property
    def passed(self) -> bool:
        """threshold 통과 여부."""
        return self.score >= self.threshold

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환."""
        result = {
            "name": self.name,
            "score": self.score,
            "threshold": self.threshold,
            "passed": self.passed,
            "reason": self.reason,
        }
        if self.claim_details:
            result["claim_details"] = self.claim_details.to_dict()
        return result


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
    tracker_metadata: dict[str, Any] = field(default_factory=dict)
    retrieval_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def total_test_cases(self) -> int:
        return len(self.results)

    @property
    def passed_test_cases(self) -> int:
        """모든 메트릭을 통과한 테스트 케이스 수."""
        return sum(1 for r in self.results if r.all_passed)

    @property
    def pass_rate(self) -> float:
        """테스트 케이스 통과율.

        모든 메트릭을 통과한 테스트 케이스의 비율을 반환합니다.
        예: 10개 테스트 케이스 중 7개가 모든 메트릭 통과 → 70%
        """
        if not self.results:
            return 0.0
        return self.passed_test_cases / self.total_test_cases

    @property
    def metric_pass_rate(self) -> float:
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
            "tracker_metadata": self.tracker_metadata,
            "metrics_evaluated": list(self.metrics_evaluated),
        }
        phoenix_meta = self.tracker_metadata.get("phoenix")
        if isinstance(phoenix_meta, dict):
            trace_url = phoenix_meta.get("trace_url")
            if trace_url:
                summary["phoenix_trace_url"] = trace_url
        run_mode = self.tracker_metadata.get("run_mode")
        if isinstance(run_mode, str) and run_mode:
            summary["run_mode"] = run_mode
        evaluation_task = self.tracker_metadata.get("evaluation_task")
        if isinstance(evaluation_task, str) and evaluation_task:
            summary["evaluation_task"] = evaluation_task
        threshold_profile = self.tracker_metadata.get("threshold_profile")
        if isinstance(threshold_profile, str) and threshold_profile:
            summary["threshold_profile"] = threshold_profile
        project_name = self.tracker_metadata.get("project") or self.tracker_metadata.get(
            "project_name"
        )
        if isinstance(project_name, str) and project_name:
            summary["project_name"] = project_name
        summary["thresholds"] = {
            metric: self._get_threshold(metric) for metric in self.metrics_evaluated
        }
        # 각 메트릭 평균
        for metric in self.metrics_evaluated:
            avg = self.get_avg_score(metric)
            summary[f"avg_{metric}"] = avg
        return summary


@dataclass
class RunClusterMap:
    """런별 클러스터 맵."""

    map_id: str
    mapping: dict[str, str] = field(default_factory=dict)
    source: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class RunClusterMapInfo:
    """클러스터 맵 버전 요약."""

    map_id: str
    item_count: int
    source: str | None = None
    created_at: datetime | None = None
