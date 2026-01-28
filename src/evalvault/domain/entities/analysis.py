"""Analysis result entities for statistical, NLP, and causal analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class AnalysisType(str, Enum):
    """분석 유형."""

    STATISTICAL = "statistical"
    NLP = "nlp"
    CAUSAL = "causal"
    DATA_QUALITY = "data_quality"
    DATASET_FEATURES = "dataset_features"


class QuestionType(str, Enum):
    """질문 유형."""

    FACTUAL = "factual"  # 사실형: 무엇, 언제, 어디, 누가
    REASONING = "reasoning"  # 추론형: 왜, 어떻게
    COMPARATIVE = "comparative"  # 비교형: 비교, 차이
    PROCEDURAL = "procedural"  # 절차형: 방법, 단계
    OPINION = "opinion"  # 의견형: 생각, 의견


class EffectSizeLevel(str, Enum):
    """효과 크기 수준 (Cohen's d 기준)."""

    NEGLIGIBLE = "negligible"  # < 0.2
    SMALL = "small"  # 0.2 - 0.5
    MEDIUM = "medium"  # 0.5 - 0.8
    LARGE = "large"  # > 0.8


@dataclass
class MetricStats:
    """개별 메트릭의 통계 요약."""

    mean: float
    std: float
    min: float
    max: float
    median: float
    percentile_25: float
    percentile_75: float
    count: int = 0

    @property
    def iqr(self) -> float:
        """사분위 범위 (Interquartile Range)."""
        return self.percentile_75 - self.percentile_25


@dataclass
class CorrelationInsight:
    """두 변수 간의 상관관계 인사이트."""

    variable1: str
    variable2: str
    correlation: float  # -1.0 ~ 1.0
    p_value: float
    is_significant: bool = False  # p < 0.05
    interpretation: str = ""

    @property
    def strength(self) -> str:
        """상관관계 강도."""
        abs_corr = abs(self.correlation)
        if abs_corr < 0.3:
            return "weak"
        elif abs_corr < 0.7:
            return "moderate"
        else:
            return "strong"


@dataclass
class LowPerformerInfo:
    """낮은 성능을 보이는 테스트 케이스 정보."""

    test_case_id: str
    metric_name: str
    score: float
    threshold: float
    question_preview: str = ""  # 질문 미리보기 (50자)
    potential_causes: list[str] = field(default_factory=list)


@dataclass
class ComparisonResult:
    """두 실행 간 비교 결과."""

    run_id_a: str
    run_id_b: str
    metric: str
    mean_a: float
    mean_b: float
    diff: float
    diff_percent: float
    p_value: float
    is_significant: bool  # p < 0.05
    effect_size: float  # Cohen's d
    effect_level: EffectSizeLevel
    winner: str | None = None  # run_id_a, run_id_b, or None (no significant diff)

    @classmethod
    def from_values(
        cls,
        run_id_a: str,
        run_id_b: str,
        metric: str,
        mean_a: float,
        mean_b: float,
        p_value: float,
        effect_size: float,
    ) -> "ComparisonResult":
        """값들로부터 ComparisonResult 생성."""
        diff = mean_b - mean_a
        diff_percent = (diff / mean_a * 100) if mean_a != 0 else 0.0
        is_significant = p_value < 0.05

        # 효과 크기 수준 결정
        abs_effect = abs(effect_size)
        if abs_effect < 0.2:
            effect_level = EffectSizeLevel.NEGLIGIBLE
        elif abs_effect < 0.5:
            effect_level = EffectSizeLevel.SMALL
        elif abs_effect < 0.8:
            effect_level = EffectSizeLevel.MEDIUM
        else:
            effect_level = EffectSizeLevel.LARGE

        # 승자 결정 (유의미한 차이가 있을 때만)
        winner = None
        if is_significant:
            winner = run_id_b if mean_b > mean_a else run_id_a

        return cls(
            run_id_a=run_id_a,
            run_id_b=run_id_b,
            metric=metric,
            mean_a=mean_a,
            mean_b=mean_b,
            diff=diff,
            diff_percent=diff_percent,
            p_value=p_value,
            is_significant=is_significant,
            effect_size=effect_size,
            effect_level=effect_level,
            winner=winner,
        )


@dataclass
class AnalysisResult:
    """기본 분석 결과 컨테이너."""

    analysis_id: str = field(default_factory=lambda: str(uuid4()))
    run_id: str = ""
    analysis_type: AnalysisType = AnalysisType.STATISTICAL
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StatisticalAnalysis(AnalysisResult):
    """통계 분석 결과."""

    # 메트릭별 통계 요약
    metrics_summary: dict[str, MetricStats] = field(default_factory=dict)

    # 상관관계 행렬 (메트릭 이름 순서대로)
    correlation_matrix: list[list[float]] = field(default_factory=list)
    correlation_metrics: list[str] = field(default_factory=list)  # 행렬의 메트릭 순서

    # 유의미한 상관관계
    significant_correlations: list[CorrelationInsight] = field(default_factory=list)

    # 낮은 성능 케이스
    low_performers: list[LowPerformerInfo] = field(default_factory=list)

    # 자동 생성된 인사이트
    insights: list[str] = field(default_factory=list)

    # Pass rate 분석
    overall_pass_rate: float = 0.0
    metric_pass_rates: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.analysis_type = AnalysisType.STATISTICAL

    def get_metric_stats(self, metric_name: str) -> MetricStats | None:
        """특정 메트릭의 통계 조회."""
        return self.metrics_summary.get(metric_name)

    def get_correlation(self, metric1: str, metric2: str) -> float | None:
        """두 메트릭 간 상관계수 조회."""
        if not self.correlation_matrix or not self.correlation_metrics:
            return None
        try:
            idx1 = self.correlation_metrics.index(metric1)
            idx2 = self.correlation_metrics.index(metric2)
            return self.correlation_matrix[idx1][idx2]
        except (ValueError, IndexError):
            return None


@dataclass
class MetaAnalysisResult:
    """다중 실행 비교 분석 결과."""

    analysis_id: str = field(default_factory=lambda: str(uuid4()))
    run_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    # 비교 결과
    comparisons: list[ComparisonResult] = field(default_factory=list)

    # 메트릭별 최고/최저 실행
    best_runs: dict[str, str] = field(default_factory=dict)  # metric -> run_id
    worst_runs: dict[str, str] = field(default_factory=dict)

    # 전체 순위 (종합 점수 기준)
    overall_ranking: list[str] = field(default_factory=list)  # run_ids in order

    # 일관성 점수 (0-1, 모든 메트릭에서 일관된 결과인지)
    consistency_score: float = 0.0

    # 권장사항
    recommendations: list[str] = field(default_factory=list)

    def get_comparisons_for_metric(self, metric: str) -> list[ComparisonResult]:
        """특정 메트릭의 비교 결과만 조회."""
        return [c for c in self.comparisons if c.metric == metric]


@dataclass
class AnalysisBundle:
    """여러 분석 결과를 묶은 번들."""

    run_id: str
    statistical: StatisticalAnalysis | None = None
    nlp: Any | None = None  # NLPAnalysis (forward reference)
    causal: Any | None = None  # CausalAnalysis (set after class definition)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def has_statistical(self) -> bool:
        return self.statistical is not None

    @property
    def has_nlp(self) -> bool:
        return self.nlp is not None

    @property
    def has_causal(self) -> bool:
        return self.causal is not None


# =============================================================================
# NLP Analysis Entities (Phase 2)
# =============================================================================


@dataclass
class TextStats:
    """텍스트 기본 통계."""

    char_count: int
    word_count: int
    sentence_count: int
    avg_word_length: float
    unique_word_ratio: float  # 어휘 다양성 (0.0 ~ 1.0)

    @property
    def avg_sentence_length(self) -> float:
        """평균 문장 길이 (단어 수 기준)."""
        if self.sentence_count == 0:
            return 0.0
        return self.word_count / self.sentence_count


@dataclass
class QuestionTypeStats:
    """질문 유형별 통계."""

    question_type: QuestionType
    count: int
    percentage: float  # 0.0 ~ 1.0
    avg_scores: dict[str, float] = field(default_factory=dict)  # 메트릭별 평균 점수


@dataclass
class KeywordInfo:
    """키워드 정보."""

    keyword: str
    frequency: int
    tfidf_score: float
    avg_metric_scores: dict[str, float] | None = None  # 해당 키워드 포함 케이스의 평균 점수


@dataclass
class TopicCluster:
    """토픽 클러스터."""

    cluster_id: int
    keywords: list[str]
    document_count: int
    avg_scores: dict[str, float] = field(default_factory=dict)
    representative_questions: list[str] = field(default_factory=list)


@dataclass
class NLPAnalysis:
    """NLP 분석 결과."""

    run_id: str

    # 텍스트 통계
    question_stats: TextStats | None = None
    answer_stats: TextStats | None = None
    context_stats: TextStats | None = None

    # 질문 유형 분석
    question_types: list[QuestionTypeStats] = field(default_factory=list)

    # 키워드 분석
    top_keywords: list[KeywordInfo] = field(default_factory=list)

    # 토픽 클러스터링 (선택적)
    topic_clusters: list[TopicCluster] = field(default_factory=list)

    # 인사이트
    insights: list[str] = field(default_factory=list)

    @property
    def has_text_stats(self) -> bool:
        """텍스트 통계 존재 여부."""
        return any(
            [
                self.question_stats is not None,
                self.answer_stats is not None,
                self.context_stats is not None,
            ]
        )

    @property
    def has_question_type_analysis(self) -> bool:
        """질문 유형 분석 존재 여부."""
        return len(self.question_types) > 0

    @property
    def has_keyword_analysis(self) -> bool:
        """키워드 분석 존재 여부."""
        return len(self.top_keywords) > 0

    @property
    def dominant_question_type(self) -> QuestionType | None:
        """가장 많은 비중을 차지하는 질문 유형."""
        if not self.question_types:
            return None
        return max(self.question_types, key=lambda x: x.count).question_type


# =============================================================================
# Causal Analysis Entities (Phase 3)
# =============================================================================


class CausalFactorType(str, Enum):
    """인과 요인 유형."""

    QUESTION_LENGTH = "question_length"  # 질문 길이
    ANSWER_LENGTH = "answer_length"  # 답변 길이
    CONTEXT_COUNT = "context_count"  # 컨텍스트 수
    CONTEXT_LENGTH = "context_length"  # 컨텍스트 총 길이
    QUESTION_TYPE = "question_type"  # 질문 유형
    QUESTION_COMPLEXITY = "question_complexity"  # 질문 복잡도
    HAS_GROUND_TRUTH = "has_ground_truth"  # ground_truth 존재 여부
    KEYWORD_OVERLAP = "keyword_overlap"  # 질문-컨텍스트 키워드 겹침


class ImpactDirection(str, Enum):
    """영향 방향."""

    POSITIVE = "positive"  # 증가할수록 점수 증가
    NEGATIVE = "negative"  # 증가할수록 점수 감소
    NEUTRAL = "neutral"  # 유의미한 영향 없음
    NONLINEAR = "nonlinear"  # 비선형 관계 (예: U자형)


class ImpactStrength(str, Enum):
    """영향 강도."""

    NEGLIGIBLE = "negligible"  # < 0.1
    WEAK = "weak"  # 0.1 - 0.3
    MODERATE = "moderate"  # 0.3 - 0.5
    STRONG = "strong"  # > 0.5


@dataclass
class FactorStats:
    """요인별 통계."""

    factor_type: CausalFactorType
    mean: float
    std: float
    min: float
    max: float
    median: float


@dataclass
class StratifiedGroup:
    """계층화된 그룹 (요인 값 범위별 그룹)."""

    group_name: str  # "low", "medium", "high" 등
    lower_bound: float
    upper_bound: float
    count: int
    avg_scores: dict[str, float]  # 메트릭별 평균 점수


@dataclass
class FactorImpact:
    """요인이 메트릭에 미치는 영향."""

    factor_type: CausalFactorType
    metric_name: str
    direction: ImpactDirection
    strength: ImpactStrength
    correlation: float  # 상관계수
    p_value: float
    is_significant: bool  # p < 0.05
    effect_size: float  # 표준화된 효과 크기
    stratified_groups: list[StratifiedGroup] = field(default_factory=list)
    interpretation: str = ""


@dataclass
class CausalRelationship:
    """인과 관계."""

    cause: CausalFactorType
    effect_metric: str
    direction: ImpactDirection
    confidence: float  # 0.0 ~ 1.0
    evidence: str = ""  # 근거 설명
    sample_size: int = 0


@dataclass
class RootCause:
    """근본 원인 분석 결과."""

    metric_name: str
    primary_causes: list[CausalFactorType]  # 주요 원인 (영향력 순)
    contributing_factors: list[CausalFactorType]  # 기여 요인
    explanation: str = ""


@dataclass
class InterventionSuggestion:
    """개선 제안."""

    target_metric: str
    intervention: str  # 제안 내용
    expected_impact: str  # 예상 효과
    priority: int = 1  # 1=높음, 2=중간, 3=낮음
    related_factors: list[CausalFactorType] = field(default_factory=list)


@dataclass
class CausalAnalysis:
    """인과 분석 결과."""

    run_id: str
    analysis_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    # 요인별 통계
    factor_stats: dict[CausalFactorType, FactorStats] = field(default_factory=dict)

    # 요인-메트릭 영향 분석
    factor_impacts: list[FactorImpact] = field(default_factory=list)

    # 식별된 인과 관계
    causal_relationships: list[CausalRelationship] = field(default_factory=list)

    # 근본 원인 분석
    root_causes: list[RootCause] = field(default_factory=list)

    # 개선 제안
    interventions: list[InterventionSuggestion] = field(default_factory=list)

    # 인사이트
    insights: list[str] = field(default_factory=list)

    @property
    def significant_impacts(self) -> list[FactorImpact]:
        """유의미한 영향만 필터링."""
        return [fi for fi in self.factor_impacts if fi.is_significant]

    @property
    def strong_relationships(self) -> list[CausalRelationship]:
        """신뢰도 높은 인과 관계만 필터링 (confidence > 0.7)."""
        return [cr for cr in self.causal_relationships if cr.confidence > 0.7]

    def get_impacts_for_metric(self, metric_name: str) -> list[FactorImpact]:
        """특정 메트릭에 대한 모든 요인 영향 조회."""
        return [fi for fi in self.factor_impacts if fi.metric_name == metric_name]

    def get_impacts_for_factor(self, factor_type: CausalFactorType) -> list[FactorImpact]:
        """특정 요인의 모든 메트릭 영향 조회."""
        return [fi for fi in self.factor_impacts if fi.factor_type == factor_type]
