"""Causal analysis adapter implementation."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import TYPE_CHECKING

import numpy as np
from scipy import stats

from evalvault.adapters.outbound.analysis.common import BaseAnalysisAdapter
from evalvault.domain.entities.analysis import (
    CausalAnalysis,
    CausalFactorType,
    CausalRelationship,
    FactorImpact,
    FactorStats,
    ImpactDirection,
    ImpactStrength,
    InterventionSuggestion,
    RootCause,
    StratifiedGroup,
)

if TYPE_CHECKING:
    from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer
    from evalvault.domain.entities import EvaluationRun

logger = logging.getLogger(__name__)


class CausalAnalysisAdapter(BaseAnalysisAdapter):
    """인과 분석 어댑터.

    평가 결과에서 인과 관계를 분석하여 근본 원인을 파악하고
    개선 제안을 생성합니다.
    """

    def __init__(
        self,
        *,
        num_strata: int = 3,
        min_group_size: int = 3,
        korean_tokenizer: KiwiTokenizer | None = None,
    ):
        """초기화.

        Args:
            num_strata: 계층화 그룹 수 (기본: 3 - low/medium/high)
            min_group_size: 그룹별 최소 샘플 수
            korean_tokenizer: 한국어 형태소 분석기 (KiwiTokenizer)
        """
        super().__init__()
        self._num_strata = num_strata
        self._min_group_size = min_group_size
        self._korean_tokenizer = korean_tokenizer
        self._korean_checker = None

        # 한국어 토크나이저가 있으면 KoreanFaithfulnessChecker 초기화
        if korean_tokenizer is not None:
            try:
                from evalvault.adapters.outbound.nlp.korean import (
                    KoreanFaithfulnessChecker,
                )

                self._korean_checker = KoreanFaithfulnessChecker(korean_tokenizer)
                logger.info("Korean keyword overlap enabled with morphological analysis")
            except ImportError:
                logger.warning("Korean NLP module not available, using basic keyword overlap")

    def analyze(self, run: EvaluationRun, **kwargs):
        """BaseAnalysisAdapter 규약."""
        return self.analyze_causality(run, **kwargs)

    def analyze_causality(
        self,
        run: EvaluationRun,
        *,
        min_samples: int = 10,
        significance_level: float = 0.05,
    ) -> CausalAnalysis:
        """인과 분석 수행.

        Args:
            run: 분석할 평가 실행
            min_samples: 분석에 필요한 최소 샘플 수
            significance_level: 유의 수준 (기본: 0.05)

        Returns:
            CausalAnalysis 결과
        """
        logger.info(f"Starting causal analysis for run: {run.run_id}")

        # 결과가 부족하면 빈 분석 반환
        if len(run.results) < min_samples:
            logger.warning(
                f"Insufficient samples ({len(run.results)}) for causal analysis "
                f"(minimum: {min_samples})"
            )
            return CausalAnalysis(
                run_id=run.run_id,
                insights=[
                    f"Insufficient samples for causal analysis ({len(run.results)} < {min_samples})"
                ],
            )

        # 요인 추출
        factors = self._extract_factors(run)
        metrics = run.metrics_evaluated

        # 요인별 통계
        factor_stats = self._calculate_factor_stats(factors)

        # 메트릭 점수 추출
        metric_scores = self.processor.extract_metric_scores(run, metrics)

        # 요인-메트릭 영향 분석
        factor_impacts = self._analyze_factor_impacts(
            factors, metric_scores, metrics, significance_level
        )

        # 인과 관계 식별
        causal_relationships = self._identify_causal_relationships(factor_impacts, len(run.results))

        # 근본 원인 분석
        root_causes = self._analyze_root_causes(factor_impacts, metrics)

        # 개선 제안 생성
        interventions = self._generate_interventions(factor_impacts, root_causes, run.thresholds)

        # 인사이트 생성
        insights = self._generate_insights(factor_impacts, causal_relationships, root_causes)

        return CausalAnalysis(
            run_id=run.run_id,
            factor_stats=factor_stats,
            factor_impacts=factor_impacts,
            causal_relationships=causal_relationships,
            root_causes=root_causes,
            interventions=interventions,
            insights=insights,
        )

    def _extract_factors(self, run: EvaluationRun) -> dict[CausalFactorType, list[float]]:
        """테스트 케이스에서 인과 요인 추출."""
        factors: dict[CausalFactorType, list[float]] = defaultdict(list)

        for tc_result in run.results:
            # TestCaseResult has direct fields: question, answer, contexts, ground_truth
            question = tc_result.question or ""
            answer = tc_result.answer or ""
            contexts = tc_result.contexts or []
            ground_truth = tc_result.ground_truth

            # 질문 길이 (단어 수)
            question_words = len(question.split())
            factors[CausalFactorType.QUESTION_LENGTH].append(float(question_words))

            # 답변 길이 (단어 수)
            answer_words = len(answer.split()) if answer else 0
            factors[CausalFactorType.ANSWER_LENGTH].append(float(answer_words))

            # 컨텍스트 수
            context_count = len(contexts) if contexts else 0
            factors[CausalFactorType.CONTEXT_COUNT].append(float(context_count))

            # 컨텍스트 총 길이 (단어 수)
            context_length = sum(len(c.split()) for c in contexts) if contexts else 0
            factors[CausalFactorType.CONTEXT_LENGTH].append(float(context_length))

            # 질문 복잡도 (문장 수 + 특수문자 비율)
            complexity = self._calculate_question_complexity(question)
            factors[CausalFactorType.QUESTION_COMPLEXITY].append(complexity)

            # ground_truth 존재 여부
            has_gt = 1.0 if ground_truth else 0.0
            factors[CausalFactorType.HAS_GROUND_TRUTH].append(has_gt)

            # 질문-컨텍스트 키워드 겹침
            overlap = self._calculate_keyword_overlap(question, contexts)
            factors[CausalFactorType.KEYWORD_OVERLAP].append(overlap)

        return dict(factors)

    def _calculate_question_complexity(self, question: str) -> float:
        """질문 복잡도 계산 (0-1 정규화)."""
        # 문장 수
        sentences = len(re.split(r"[.?!]+", question.strip()))

        # 특수문자 비율
        special_chars = len(re.findall(r"[^\w\s]", question))
        total_chars = max(len(question), 1)
        special_ratio = special_chars / total_chars

        # 평균 단어 길이
        words = question.split()
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)

        # 복잡도 = 문장수 * 0.3 + 특수문자비율 * 0.2 + 평균단어길이/10 * 0.5
        complexity = (sentences * 0.3) + (special_ratio * 0.2) + (avg_word_len / 10 * 0.5)

        return min(complexity, 1.0)

    def _calculate_keyword_overlap(self, question: str, contexts: list[str] | None) -> float:
        """질문과 컨텍스트 간 키워드 겹침 비율 계산.

        한국어 토크나이저가 설정된 경우 형태소 분석 기반으로 계산합니다.
        """
        if not contexts:
            return 0.0

        # 한국어 형태소 분석 기반 키워드 겹침 (개선된 버전)
        if self._korean_checker is not None:
            return self._korean_checker.calculate_keyword_overlap(question, contexts)

        # 기본 구현: 간단한 키워드 추출 (불용어 제외)
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "이",
            "그",
            "저",
            "것",
            "수",
            "등",
            "및",
            "또는",
            "그리고",
            "하지만",
            "그러나",
            "때문에",
            "위해",
        }

        question_words = {
            w.lower()
            for w in re.findall(r"\w+", question)
            if w.lower() not in stopwords and len(w) > 2
        }

        if not question_words:
            return 0.0

        context_text = " ".join(contexts)
        context_words = {
            w.lower()
            for w in re.findall(r"\w+", context_text)
            if w.lower() not in stopwords and len(w) > 2
        }

        overlap = len(question_words & context_words)
        return overlap / len(question_words)

    def _calculate_factor_stats(
        self, factors: dict[CausalFactorType, list[float]]
    ) -> dict[CausalFactorType, FactorStats]:
        """요인별 통계 계산."""
        stats_dict = {}

        for factor_type, values in factors.items():
            if not values:
                continue

            arr = np.array(values)
            stats_dict[factor_type] = FactorStats(
                factor_type=factor_type,
                mean=float(np.mean(arr)),
                std=float(np.std(arr)),
                min=float(np.min(arr)),
                max=float(np.max(arr)),
                median=float(np.median(arr)),
            )

        return stats_dict

    def _analyze_factor_impacts(
        self,
        factors: dict[CausalFactorType, list[float]],
        metric_scores: dict[str, list[float]],
        metrics: list[str],
        significance_level: float,
    ) -> list[FactorImpact]:
        """요인-메트릭 영향 분석."""
        impacts = []

        for factor_type, factor_values in factors.items():
            for metric in metrics:
                if metric not in metric_scores:
                    continue

                scores = metric_scores[metric]

                # 데이터 길이 맞추기
                n = min(len(factor_values), len(scores))
                if n < self._min_group_size * 2:
                    continue

                x = np.array(factor_values[:n])
                y = np.array(scores[:n])

                # 상관 분석
                try:
                    x_std = float(np.std(x))
                    y_std = float(np.std(y))
                    if np.isclose(x_std, 0.0) or np.isclose(y_std, 0.0):
                        correlation = 0.0
                        p_value = 1.0
                    else:
                        correlation, p_value = stats.pearsonr(x, y)
                        # Handle NaN (constant input)
                        if np.isnan(correlation):
                            correlation = 0.0
                            p_value = 1.0
                except Exception:
                    correlation = 0.0
                    p_value = 1.0

                # 유의성 판단
                is_significant = p_value < significance_level

                # 영향 방향 결정
                direction = self._determine_direction(correlation, is_significant)

                # 영향 강도 결정
                strength = self._determine_strength(abs(correlation))

                # 효과 크기 (Cohen's d 유사)
                effect_size = abs(correlation) * 2

                # 계층화 분석
                stratified_groups = self._stratify_analysis(x, y, metric)

                # 해석 생성
                interpretation = self._generate_interpretation(
                    factor_type, metric, direction, strength, correlation
                )

                impacts.append(
                    FactorImpact(
                        factor_type=factor_type,
                        metric_name=metric,
                        direction=direction,
                        strength=strength,
                        correlation=float(correlation),
                        p_value=float(p_value),
                        is_significant=is_significant,
                        effect_size=effect_size,
                        stratified_groups=stratified_groups,
                        interpretation=interpretation,
                    )
                )

        return impacts

    def _determine_direction(self, correlation: float, is_significant: bool) -> ImpactDirection:
        """영향 방향 결정."""
        if not is_significant or abs(correlation) < 0.1:
            return ImpactDirection.NEUTRAL

        return ImpactDirection.POSITIVE if correlation > 0 else ImpactDirection.NEGATIVE

    def _determine_strength(self, abs_correlation: float) -> ImpactStrength:
        """영향 강도 결정."""
        if abs_correlation < 0.1:
            return ImpactStrength.NEGLIGIBLE
        elif abs_correlation < 0.3:
            return ImpactStrength.WEAK
        elif abs_correlation < 0.5:
            return ImpactStrength.MODERATE
        else:
            return ImpactStrength.STRONG

    def _stratify_analysis(
        self, factor_values: np.ndarray, scores: np.ndarray, metric: str
    ) -> list[StratifiedGroup]:
        """계층화 분석 수행."""
        groups = []

        # 분위수로 그룹 나누기
        try:
            percentiles = np.percentile(
                factor_values, [100 * i / self._num_strata for i in range(1, self._num_strata)]
            )
        except Exception:
            return groups

        group_names = (
            ["low", "medium", "high"]
            if self._num_strata == 3
            else [f"group_{i}" for i in range(self._num_strata)]
        )

        bounds = [factor_values.min()] + list(percentiles) + [factor_values.max()]

        for i in range(self._num_strata):
            lower = bounds[i]
            upper = bounds[i + 1]

            # 그룹에 속하는 인덱스
            if i == self._num_strata - 1:
                mask = (factor_values >= lower) & (factor_values <= upper)
            else:
                mask = (factor_values >= lower) & (factor_values < upper)

            group_scores = scores[mask]

            if len(group_scores) >= self._min_group_size:
                groups.append(
                    StratifiedGroup(
                        group_name=group_names[i] if i < len(group_names) else f"group_{i}",
                        lower_bound=float(lower),
                        upper_bound=float(upper),
                        count=int(len(group_scores)),
                        avg_scores={metric: float(np.mean(group_scores))},
                    )
                )

        return groups

    def _generate_interpretation(
        self,
        factor_type: CausalFactorType,
        metric: str,
        direction: ImpactDirection,
        strength: ImpactStrength,
        correlation: float,
    ) -> str:
        """영향 해석 생성."""
        factor_names = {
            CausalFactorType.QUESTION_LENGTH: "Question length",
            CausalFactorType.ANSWER_LENGTH: "Answer length",
            CausalFactorType.CONTEXT_COUNT: "Number of contexts",
            CausalFactorType.CONTEXT_LENGTH: "Total context length",
            CausalFactorType.QUESTION_COMPLEXITY: "Question complexity",
            CausalFactorType.HAS_GROUND_TRUTH: "Ground truth availability",
            CausalFactorType.KEYWORD_OVERLAP: "Question-context keyword overlap",
        }

        factor_name = factor_names.get(factor_type, factor_type.value)

        if direction == ImpactDirection.NEUTRAL:
            return f"{factor_name} has no significant effect on {metric}"

        direction_str = "increases" if direction == ImpactDirection.POSITIVE else "decreases"
        strength_str = strength.value

        return (
            f"{factor_name} has a {strength_str} {direction.value} effect on {metric} "
            f"(r={correlation:.2f}): Higher {factor_name.lower()} {direction_str} {metric}"
        )

    def _identify_causal_relationships(
        self, impacts: list[FactorImpact], sample_size: int
    ) -> list[CausalRelationship]:
        """인과 관계 식별."""
        relationships = []

        for impact in impacts:
            if not impact.is_significant:
                continue

            if impact.strength in (ImpactStrength.MODERATE, ImpactStrength.STRONG):
                # 신뢰도 계산: 상관계수 강도 + 유의성 기반
                confidence = min(abs(impact.correlation) + (1 - impact.p_value) * 0.3, 1.0)

                # 계층화 분석 결과로 근거 생성
                evidence = self._build_evidence(impact)

                relationships.append(
                    CausalRelationship(
                        cause=impact.factor_type,
                        effect_metric=impact.metric_name,
                        direction=impact.direction,
                        confidence=confidence,
                        evidence=evidence,
                        sample_size=sample_size,
                    )
                )

        return relationships

    def _build_evidence(self, impact: FactorImpact) -> str:
        """인과 관계 근거 생성."""
        if not impact.stratified_groups:
            return f"Correlation: {impact.correlation:.2f}, p-value: {impact.p_value:.4f}"

        # 그룹별 점수 비교
        scores_by_group = []
        for group in impact.stratified_groups:
            avg = group.avg_scores.get(impact.metric_name, 0)
            scores_by_group.append(f"{group.group_name}={avg:.2f}")

        return (
            f"Stratified analysis shows {' < '.join(scores_by_group) if impact.direction == ImpactDirection.POSITIVE else ' > '.join(scores_by_group)}. "
            f"Correlation: {impact.correlation:.2f}, p-value: {impact.p_value:.4f}"
        )

    def _analyze_root_causes(
        self, impacts: list[FactorImpact], metrics: list[str]
    ) -> list[RootCause]:
        """근본 원인 분석."""
        root_causes = []

        for metric in metrics:
            metric_impacts = [i for i in impacts if i.metric_name == metric]

            if not metric_impacts:
                continue

            # 유의미한 영향 정렬 (효과 크기 기준)
            significant = sorted(
                [i for i in metric_impacts if i.is_significant],
                key=lambda x: abs(x.correlation),
                reverse=True,
            )

            if not significant:
                continue

            # 주요 원인 (상위 2개)
            primary = [i.factor_type for i in significant[:2]]

            # 기여 요인 (나머지)
            contributing = [i.factor_type for i in significant[2:4]]

            # 설명 생성
            explanation = self._generate_root_cause_explanation(metric, significant[:2])

            root_causes.append(
                RootCause(
                    metric_name=metric,
                    primary_causes=primary,
                    contributing_factors=contributing,
                    explanation=explanation,
                )
            )

        return root_causes

    def _generate_root_cause_explanation(self, metric: str, top_impacts: list[FactorImpact]) -> str:
        """근본 원인 설명 생성."""
        if not top_impacts:
            return f"No significant causal factors identified for {metric}"

        explanations = []
        for impact in top_impacts:
            direction = (
                "positively" if impact.direction == ImpactDirection.POSITIVE else "negatively"
            )
            explanations.append(
                f"{impact.factor_type.value} {direction} affects {metric} "
                f"(r={impact.correlation:.2f})"
            )

        return "; ".join(explanations)

    def _generate_interventions(
        self,
        impacts: list[FactorImpact],
        root_causes: list[RootCause],
        thresholds: dict[str, float],
    ) -> list[InterventionSuggestion]:
        """개선 제안 생성."""
        interventions = []

        # 인터벤션 템플릿
        intervention_templates = {
            CausalFactorType.QUESTION_LENGTH: {
                ImpactDirection.NEGATIVE: (
                    "Consider simplifying or shortening questions",
                    "May improve {metric} by reducing question complexity",
                ),
                ImpactDirection.POSITIVE: (
                    "Consider providing more detailed questions",
                    "More context in questions may improve {metric}",
                ),
            },
            CausalFactorType.CONTEXT_COUNT: {
                ImpactDirection.NEGATIVE: (
                    "Reduce the number of contexts to focus on relevant information",
                    "Fewer, more relevant contexts may improve {metric}",
                ),
                ImpactDirection.POSITIVE: (
                    "Provide more contextual information",
                    "Additional contexts may improve {metric}",
                ),
            },
            CausalFactorType.CONTEXT_LENGTH: {
                ImpactDirection.NEGATIVE: (
                    "Use more concise contexts",
                    "Shorter, focused contexts may improve {metric}",
                ),
                ImpactDirection.POSITIVE: (
                    "Provide more comprehensive context information",
                    "More detailed contexts may improve {metric}",
                ),
            },
            CausalFactorType.KEYWORD_OVERLAP: {
                ImpactDirection.POSITIVE: (
                    "Improve retrieval to better match question keywords",
                    "Better keyword alignment may improve {metric}",
                ),
                ImpactDirection.NEGATIVE: (
                    "Diversify context vocabulary beyond question keywords",
                    "Broader context coverage may improve {metric}",
                ),
            },
            CausalFactorType.QUESTION_COMPLEXITY: {
                ImpactDirection.NEGATIVE: (
                    "Simplify complex questions or break them into parts",
                    "Simpler questions may improve {metric}",
                ),
                ImpactDirection.POSITIVE: (
                    "Ensure answers match question complexity",
                    "More detailed answers for complex questions may improve {metric}",
                ),
            },
        }

        # 우선순위별 인터벤션 생성
        for root_cause in root_causes:
            priority = 1
            for factor in root_cause.primary_causes:
                # 해당 요인의 영향 찾기
                factor_impact = next(
                    (
                        i
                        for i in impacts
                        if i.factor_type == factor and i.metric_name == root_cause.metric_name
                    ),
                    None,
                )

                if not factor_impact or factor_impact.direction == ImpactDirection.NEUTRAL:
                    continue

                templates = intervention_templates.get(factor, {})
                template = templates.get(factor_impact.direction)

                if template:
                    intervention_text, expected_impact = template
                    interventions.append(
                        InterventionSuggestion(
                            target_metric=root_cause.metric_name,
                            intervention=intervention_text,
                            expected_impact=expected_impact.format(metric=root_cause.metric_name),
                            priority=priority,
                            related_factors=[factor],
                        )
                    )

                priority += 1

        # 중복 제거 및 우선순위 정렬
        seen = set()
        unique_interventions = []
        for intervention in sorted(interventions, key=lambda x: x.priority):
            key = (intervention.intervention, intervention.target_metric)
            if key not in seen:
                seen.add(key)
                unique_interventions.append(intervention)

        return unique_interventions[:10]  # 상위 10개만

    def _generate_insights(
        self,
        impacts: list[FactorImpact],
        relationships: list[CausalRelationship],
        root_causes: list[RootCause],
    ) -> list[str]:
        """인사이트 생성."""
        insights = []

        # 유의미한 영향 수
        significant_count = len([i for i in impacts if i.is_significant])
        total_count = len(impacts)

        if significant_count > 0:
            insights.append(
                f"Found {significant_count} significant factor-metric relationships "
                f"out of {total_count} analyzed"
            )

        # 강한 인과 관계
        strong_relationships = [r for r in relationships if r.confidence > 0.7]
        if strong_relationships:
            insights.append(
                f"Identified {len(strong_relationships)} strong causal relationships "
                f"with confidence > 0.7"
            )

        # 가장 영향력 있는 요인
        if impacts:
            most_impactful = max(
                [i for i in impacts if i.is_significant] or impacts,
                key=lambda x: abs(x.correlation),
            )
            insights.append(
                f"Most impactful factor: {most_impactful.factor_type.value} "
                f"on {most_impactful.metric_name} (r={most_impactful.correlation:.2f})"
            )

        # 주요 근본 원인
        if root_causes:
            all_primary = []
            for rc in root_causes:
                all_primary.extend(rc.primary_causes)

            if all_primary:
                from collections import Counter

                most_common = Counter(all_primary).most_common(1)[0]
                insights.append(
                    f"Most common root cause across metrics: {most_common[0].value} "
                    f"(appears in {most_common[1]} metrics)"
                )

        # 영향 없는 요인
        neutral_factors = {i.factor_type for i in impacts if i.direction == ImpactDirection.NEUTRAL}
        if neutral_factors:
            factor_names = [f.value for f in list(neutral_factors)[:3]]
            insights.append(f"Factors with no significant impact: {', '.join(factor_names)}")

        return insights
