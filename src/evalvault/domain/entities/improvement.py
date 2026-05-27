"""RAG Improvement Guide entities.

평가 결과를 기반으로 RAG 시스템 개선을 위한 엔티티들을 정의합니다.
Rule-based 패턴 탐지와 LLM-based 인사이트 생성을 결합한 하이브리드 분석을 지원합니다.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class RAGComponent(StrEnum):
    """RAG 파이프라인 컴포넌트."""

    RETRIEVER = "retriever"
    RERANKER = "reranker"
    GENERATOR = "generator"
    CHUNKER = "chunker"
    EMBEDDER = "embedder"
    QUERY_PROCESSOR = "query_processor"
    PROMPT = "prompt"


class ImprovementPriority(StrEnum):
    """개선 우선순위."""

    P0_CRITICAL = "p0_critical"  # 즉시 수정 필요
    P1_HIGH = "p1_high"  # 높은 우선순위
    P2_MEDIUM = "p2_medium"  # 중간 우선순위
    P3_LOW = "p3_low"  # 낮은 우선순위


class PatternType(StrEnum):
    """문제 패턴 유형."""

    # Retrieval 관련
    LONG_QUERY_LOW_PRECISION = "long_query_low_precision"
    LOW_KEYWORD_OVERLAP = "low_keyword_overlap"
    MISSING_CONTEXT = "missing_context"
    IRRELEVANT_CONTEXT = "irrelevant_context"
    CONTEXT_BOUNDARY_ISSUE = "context_boundary_issue"

    # Generation 관련
    HALLUCINATION = "hallucination"
    INCOMPLETE_ANSWER = "incomplete_answer"
    OFF_TOPIC_RESPONSE = "off_topic_response"
    VERBOSE_RESPONSE = "verbose_response"

    # 복합 문제
    MULTI_HOP_FAILURE = "multi_hop_failure"
    REASONING_FAILURE = "reasoning_failure"

    # 기타
    UNKNOWN = "unknown"
    STAGE_METRIC_BELOW_THRESHOLD = "stage_metric_below_threshold"


class EffortLevel(StrEnum):
    """개선 노력 수준."""

    LOW = "low"  # 설정 변경, 파라미터 조정
    MEDIUM = "medium"  # 코드 수정, 새 컴포넌트 추가
    HIGH = "high"  # 아키텍처 변경, 모델 재학습


class EvidenceSource(StrEnum):
    """증거 출처."""

    RULE_BASED = "rule_based"  # 규칙 기반 탐지
    STATISTICAL = "statistical"  # 통계 분석
    LLM_ANALYSIS = "llm_analysis"  # LLM 분석
    HYBRID = "hybrid"  # 복합 분석


@dataclass
class FailureSample:
    """실패 사례 샘플.

    개선이 필요한 이유를 설명하는 구체적인 실패 사례입니다.
    """

    test_case_id: str
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str | None = None

    # 메트릭 점수
    metric_scores: dict[str, float] = field(default_factory=dict)

    # 실패 분석
    failure_reason: str = ""
    detected_patterns: list[PatternType] = field(default_factory=list)

    # 개선 방향 (LLM 생성 또는 규칙 기반)
    suggested_context: str | None = None  # 이런 컨텍스트가 있었다면...
    suggested_answer: str | None = None  # 이렇게 답했어야...

    # 메타데이터
    analysis_source: EvidenceSource = EvidenceSource.RULE_BASED

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "test_case_id": self.test_case_id,
            "question": self.question,
            "answer": self.answer,
            "contexts": self.contexts,
            "ground_truth": self.ground_truth,
            "metric_scores": self.metric_scores,
            "failure_reason": self.failure_reason,
            "detected_patterns": [p.value for p in self.detected_patterns],
            "suggested_context": self.suggested_context,
            "suggested_answer": self.suggested_answer,
            "analysis_source": self.analysis_source.value,
        }


@dataclass
class PatternEvidence:
    """패턴 탐지 증거.

    특정 문제 패턴이 발견되었음을 증명하는 데이터입니다.
    """

    pattern_type: PatternType

    # 해당 케이스 통계
    affected_count: int
    total_count: int

    # 통계적 근거
    correlation: float | None = None  # 메트릭과의 상관계수
    p_value: float | None = None
    mean_score_affected: float | None = None  # 해당 패턴 케이스의 평균 점수
    mean_score_unaffected: float | None = None  # 비해당 케이스의 평균 점수

    # 임계값 (규칙 기반 탐지에 사용된 값)
    threshold_used: dict[str, Any] = field(default_factory=dict)

    # 대표 실패 사례
    representative_failures: list[FailureSample] = field(default_factory=list)

    # 분석 출처
    source: EvidenceSource = EvidenceSource.RULE_BASED

    @property
    def affected_ratio(self) -> float:
        """영향받은 케이스 비율."""
        if self.total_count == 0:
            return 0.0
        return self.affected_count / self.total_count

    @property
    def is_statistically_significant(self) -> bool:
        """통계적 유의성 여부 (p < 0.05)."""
        return self.p_value is not None and self.p_value < 0.05

    @property
    def score_gap(self) -> float | None:
        """영향/비영향 그룹 간 점수 차이."""
        if self.mean_score_affected is None or self.mean_score_unaffected is None:
            return None
        return self.mean_score_unaffected - self.mean_score_affected

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "pattern_type": self.pattern_type.value,
            "affected_count": self.affected_count,
            "total_count": self.total_count,
            "affected_ratio": self.affected_ratio,
            "correlation": self.correlation,
            "p_value": self.p_value,
            "mean_score_affected": self.mean_score_affected,
            "mean_score_unaffected": self.mean_score_unaffected,
            "score_gap": self.score_gap,
            "is_significant": self.is_statistically_significant,
            "threshold_used": self.threshold_used,
            "source": self.source.value,
            "representative_failures": [f.to_dict() for f in self.representative_failures],
        }


@dataclass
class ImprovementEvidence:
    """개선 제안의 증거 데이터.

    왜 이 개선이 필요한지를 증명하는 종합 증거입니다.
    """

    evidence_id: str = field(default_factory=lambda: str(uuid4()))

    # 관련 메트릭
    target_metric: str = ""

    # 탐지된 패턴들
    detected_patterns: list[PatternEvidence] = field(default_factory=list)

    # 종합 통계
    total_failures: int = 0
    avg_score_failures: float = 0.0
    avg_score_passes: float = 0.0

    # 분석 방법
    analysis_methods: list[EvidenceSource] = field(default_factory=list)

    # LLM 분석 결과 (선택적)
    llm_analysis: str | None = None
    llm_confidence: float | None = None

    # 유사 시스템 벤치마크 참조 (선택적)
    benchmark_reference: str | None = None

    @property
    def primary_pattern(self) -> PatternEvidence | None:
        """가장 영향력 있는 패턴."""
        if not self.detected_patterns:
            return None
        # affected_count 기준 정렬
        return max(self.detected_patterns, key=lambda p: p.affected_count)

    @property
    def has_statistical_evidence(self) -> bool:
        """통계적 증거 존재 여부."""
        return any(p.is_statistically_significant for p in self.detected_patterns)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "evidence_id": self.evidence_id,
            "target_metric": self.target_metric,
            "detected_patterns": [p.to_dict() for p in self.detected_patterns],
            "total_failures": self.total_failures,
            "avg_score_failures": self.avg_score_failures,
            "avg_score_passes": self.avg_score_passes,
            "analysis_methods": [m.value for m in self.analysis_methods],
            "llm_analysis": self.llm_analysis,
            "llm_confidence": self.llm_confidence,
            "benchmark_reference": self.benchmark_reference,
            "has_statistical_evidence": self.has_statistical_evidence,
        }


@dataclass
class ImprovementAction:
    """구체적인 개선 액션.

    RAG 시스템을 개선하기 위한 단일 액션입니다.
    """

    action_id: str = field(default_factory=lambda: str(uuid4()))

    # 액션 설명
    title: str = ""  # "top_k 증가", "Reranker 도입"
    description: str = ""  # 상세 설명
    implementation_hint: str = ""  # 구현 힌트 (코드 예시 등)

    # 예상 효과
    expected_improvement: float = 0.0  # 0.05 = 5% 개선 예상
    expected_improvement_range: tuple[float, float] = (0.0, 0.0)  # 범위

    # 노력 수준
    effort: EffortLevel = EffortLevel.LOW

    # 우선순위 점수 (높을수록 우선)
    priority_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "action_id": self.action_id,
            "title": self.title,
            "description": self.description,
            "implementation_hint": self.implementation_hint,
            "expected_improvement": self.expected_improvement,
            "expected_improvement_range": list(self.expected_improvement_range),
            "effort": self.effort.value,
            "priority_score": self.priority_score,
        }


@dataclass
class RAGImprovementGuide:
    """RAG 파이프라인 개선 가이드.

    특정 컴포넌트에 대한 개선 가이드입니다.
    """

    guide_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    # 대상 컴포넌트
    component: RAGComponent = RAGComponent.RETRIEVER

    # 관련 메트릭
    target_metrics: list[str] = field(default_factory=list)

    # 우선순위
    priority: ImprovementPriority = ImprovementPriority.P2_MEDIUM

    # 개선 액션 목록
    actions: list[ImprovementAction] = field(default_factory=list)

    # 증거 데이터
    evidence: ImprovementEvidence | None = None

    # 영향받는 테스트 케이스
    affected_test_case_ids: list[str] = field(default_factory=list)

    # 검증 방법
    verification_command: str = ""  # evalvault compare baseline after_fix

    # 메타데이터
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_expected_improvement(self) -> float:
        """모든 액션의 예상 개선 합계 (중복 고려하지 않은 단순 합)."""
        return sum(a.expected_improvement for a in self.actions)

    @property
    def top_action(self) -> ImprovementAction | None:
        """가장 우선순위 높은 액션."""
        if not self.actions:
            return None
        return max(self.actions, key=lambda a: a.priority_score)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "guide_id": self.guide_id,
            "created_at": self.created_at.isoformat(),
            "component": self.component.value,
            "target_metrics": self.target_metrics,
            "priority": self.priority.value,
            "actions": [a.to_dict() for a in self.actions],
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "affected_test_case_ids": self.affected_test_case_ids,
            "verification_command": self.verification_command,
            "total_expected_improvement": self.total_expected_improvement,
            "metadata": self.metadata,
        }


@dataclass
class ImprovementReport:
    """종합 개선 리포트.

    평가 결과에 대한 전체 개선 가이드 모음입니다.
    """

    report_id: str = field(default_factory=lambda: str(uuid4()))
    run_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    # 요약 정보
    total_test_cases: int = 0
    failed_test_cases: int = 0
    pass_rate: float = 0.0

    # 메트릭별 점수
    metric_scores: dict[str, float] = field(default_factory=dict)
    metric_thresholds: dict[str, float] = field(default_factory=dict)
    metric_gaps: dict[str, float] = field(default_factory=dict)  # threshold - score

    # 개선 가이드 목록 (우선순위 순)
    guides: list[RAGImprovementGuide] = field(default_factory=list)

    # 전체 예상 개선폭
    total_expected_improvement: dict[str, float] = field(default_factory=dict)

    # 분석 방법
    analysis_methods_used: list[EvidenceSource] = field(default_factory=list)

    # 메타데이터
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_guides_by_metric(self, metric: str) -> list[RAGImprovementGuide]:
        """특정 메트릭 관련 가이드 조회."""
        return [g for g in self.guides if metric in g.target_metrics]

    def get_guides_by_priority(self, priority: ImprovementPriority) -> list[RAGImprovementGuide]:
        """특정 우선순위 가이드 조회."""
        return [g for g in self.guides if g.priority == priority]

    def get_critical_guides(self) -> list[RAGImprovementGuide]:
        """P0 (Critical) 가이드만 조회."""
        return self.get_guides_by_priority(ImprovementPriority.P0_CRITICAL)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "report_id": self.report_id,
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat(),
            "total_test_cases": self.total_test_cases,
            "failed_test_cases": self.failed_test_cases,
            "pass_rate": self.pass_rate,
            "metric_scores": self.metric_scores,
            "metric_thresholds": self.metric_thresholds,
            "metric_gaps": self.metric_gaps,
            "guides": [g.to_dict() for g in self.guides],
            "total_expected_improvement": self.total_expected_improvement,
            "analysis_methods_used": [m.value for m in self.analysis_methods_used],
            "metadata": self.metadata,
        }

    def to_markdown(self) -> str:
        """마크다운 형식 리포트 생성."""
        lines = [
            "# RAG 개선 가이드 리포트",
            "",
            "## 요약",
            "",
            f"- **평가 ID**: `{self.run_id}`",
            f"- **생성 시간**: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **테스트 케이스**: {self.total_test_cases}개",
            f"- **통과율**: {self.pass_rate:.1%}",
            "",
            "### 메트릭별 현황",
            "",
            "| 메트릭 | 점수 | 목표 | 갭 | 상태 |",
            "|--------|------|------|-----|------|",
        ]

        for metric, score in self.metric_scores.items():
            threshold = self.metric_thresholds.get(metric, 0.7)
            gap = self.metric_gaps.get(metric, threshold - score)
            status = "✅" if score >= threshold else "❌"
            lines.append(f"| {metric} | {score:.3f} | {threshold:.2f} | {gap:+.3f} | {status} |")

        stage_summary = self.metadata.get("stage_metrics_summary")
        if stage_summary:
            pass_rate = stage_summary.get("pass_rate")
            pass_rate_text = f"{pass_rate:.1%}" if pass_rate is not None else "n/a"
            lines.extend(
                [
                    "",
                    "### 단계 메트릭 요약",
                    "",
                    f"- 총 메트릭: {stage_summary.get('total', 0)}개",
                    f"- 평가 대상(임계값 있음): {stage_summary.get('evaluated', 0)}개",
                    f"- 통과: {stage_summary.get('passed', 0)}개 / 실패: {stage_summary.get('failed', 0)}개",
                    f"- 통과율: {pass_rate_text}",
                ]
            )
            top_failures = stage_summary.get("top_failures", [])
            if top_failures:
                lines.extend(
                    [
                        "",
                        "| 메트릭 | 실패 건수 | 평균 점수 | 임계값 |",
                        "|--------|----------|-----------|--------|",
                    ]
                )
                for item in top_failures:
                    threshold = item.get("threshold")
                    threshold_text = f"{threshold:.3f}" if threshold is not None else "-"
                    lines.append(
                        f"| {item.get('metric_name')} | {item.get('count', 0)} | "
                        f"{item.get('avg_score', 0.0):.3f} | {threshold_text} |"
                    )

        lines.extend(["", "---", ""])

        # 가이드별 상세
        for i, guide in enumerate(self.guides, 1):
            priority_emoji = {
                ImprovementPriority.P0_CRITICAL: "🔴",
                ImprovementPriority.P1_HIGH: "🟠",
                ImprovementPriority.P2_MEDIUM: "🟡",
                ImprovementPriority.P3_LOW: "🟢",
            }
            emoji = priority_emoji.get(guide.priority, "⚪")

            lines.extend(
                [
                    f"## {i}. {guide.component.value.title()} 개선 {emoji}",
                    "",
                    f"**우선순위**: {guide.priority.value}",
                    f"**대상 메트릭**: {', '.join(guide.target_metrics)}",
                    "",
                ]
            )

            # 증거 요약
            if guide.evidence and guide.evidence.detected_patterns:
                lines.append("### 문제 패턴")
                lines.append("")
                for pattern in guide.evidence.detected_patterns:
                    lines.append(
                        f"- **{pattern.pattern_type.value}**: "
                        f"{pattern.affected_count}/{pattern.total_count}건 "
                        f"({pattern.affected_ratio:.1%})"
                    )
                    if pattern.score_gap:
                        lines.append(f"  - 점수 차이: {pattern.score_gap:+.3f}")
                lines.append("")

            # 개선 액션
            if guide.actions:
                lines.append("### 개선 액션")
                lines.append("")
                for j, action in enumerate(guide.actions, 1):
                    effort_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}
                    e_emoji = effort_emoji.get(action.effort.value, "⚪")
                    lines.append(
                        f"#### {j}. {action.title} (예상 개선: +{action.expected_improvement:.0%}) {e_emoji}"
                    )
                    lines.append("")
                    if action.description:
                        lines.append(action.description)
                        lines.append("")
                    if action.implementation_hint:
                        lines.append("```")
                        lines.append(action.implementation_hint)
                        lines.append("```")
                        lines.append("")

            # 검증 방법
            if guide.verification_command:
                lines.extend(
                    [
                        "### 검증 방법",
                        "",
                        "```bash",
                        guide.verification_command,
                        "```",
                        "",
                    ]
                )

            lines.extend(["---", ""])

        lines.append("*Generated by EvalVault*")

        return "\n".join(lines)
