"""Rule-based pattern detector for RAG improvement.

평가 결과에서 규칙 기반으로 문제 패턴을 탐지합니다.
플레이북의 detection_rules를 사용하여 패턴을 식별하고 증거를 수집합니다.
"""

from __future__ import annotations

import contextlib
import logging
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy import stats

from evalvault.adapters.outbound.improvement.playbook_loader import (
    DetectionRule,
    Playbook,
    get_default_playbook,
)
from evalvault.domain.entities.improvement import (
    EvidenceSource,
    FailureSample,
    PatternEvidence,
    PatternType,
)
from evalvault.ports.outbound.improvement_port import PatternDefinitionProtocol

if TYPE_CHECKING:
    from evalvault.domain.entities import EvaluationRun, TestCaseResult

logger = logging.getLogger(__name__)


@dataclass
class FeatureVector:
    """테스트 케이스별 피처 벡터."""

    test_case_id: str
    features: dict[str, float] = field(default_factory=dict)
    metric_scores: dict[str, float] = field(default_factory=dict)

    # 원본 데이터 (실패 샘플용)
    question: str = ""
    answer: str = ""
    contexts: list[str] = field(default_factory=list)
    ground_truth: str | None = None


class PatternDetector:
    """규칙 기반 패턴 탐지기.

    플레이북의 규칙을 사용하여 평가 결과에서 문제 패턴을 탐지합니다.
    """

    def __init__(
        self,
        playbook: Playbook | None = None,
        *,
        min_sample_size: int = 1,
        significance_level: float = 0.05,
        max_representative_samples: int = 3,
    ):
        """초기화.

        Args:
            playbook: 사용할 플레이북 (None이면 기본 플레이북)
            min_sample_size: 패턴 탐지를 위한 최소 샘플 수
            significance_level: 통계적 유의수준
            max_representative_samples: 대표 실패 사례 최대 수
        """
        self._playbook = playbook or get_default_playbook()
        self._min_sample_size = min_sample_size
        self._significance_level = significance_level
        self._max_samples = max_representative_samples

        # 규칙 타입별 핸들러 등록
        self._rule_handlers: dict[str, Callable] = {
            "metric_threshold": self._check_metric_threshold,
            "feature_threshold": self._check_feature_threshold,
            "correlation": self._check_correlation,
            "metric_combination": self._check_metric_combination,
            "text_analysis": self._check_text_analysis,
            "feature_comparison": self._check_feature_comparison,
        }

    def detect_patterns(
        self,
        run: EvaluationRun,
        metrics: Sequence[str] | None = None,
    ) -> dict[str, list[PatternEvidence]]:
        """패턴 탐지 수행.

        Args:
            run: 분석할 평가 실행
            metrics: 분석할 메트릭 목록 (None이면 평가된 모든 메트릭)

        Returns:
            메트릭별 탐지된 패턴 목록
        """
        if len(run.results) < self._min_sample_size:
            logger.warning(
                f"Insufficient samples ({len(run.results)}) for pattern detection "
                f"(minimum: {self._min_sample_size})"
            )
            return {}

        # 피처 벡터 추출
        feature_vectors = self._extract_features(run)

        # 분석할 메트릭 결정
        target_metrics = metrics or run.metrics_evaluated

        results: dict[str, list[PatternEvidence]] = {}

        for metric in target_metrics:
            metric_playbook = self._playbook.metrics.get(metric)
            if not metric_playbook:
                logger.debug(f"No playbook found for metric: {metric}")
                continue

            metric_patterns = []
            for pattern_def in metric_playbook.patterns:
                evidence = self._detect_single_pattern(
                    pattern_def=pattern_def,
                    feature_vectors=feature_vectors,
                    target_metric=metric,
                    threshold=run.thresholds.get(metric, metric_playbook.default_threshold),
                )
                if evidence:
                    metric_patterns.append(evidence)

            if metric_patterns:
                results[metric] = metric_patterns
                logger.info(f"Detected {len(metric_patterns)} patterns for {metric}")

        return results

    def extract_feature_vectors(self, run: EvaluationRun) -> list[FeatureVector]:
        """Expose feature vectors for downstream analysis."""
        return self._extract_features(run)

    def _extract_features(self, run: EvaluationRun) -> list[FeatureVector]:
        """테스트 케이스별 피처 추출."""
        vectors = []

        for result in run.results:
            features = self._compute_features(result)
            metric_scores = {m.name: m.score for m in result.metrics}

            vector = FeatureVector(
                test_case_id=result.test_case_id,
                features=features,
                metric_scores=metric_scores,
                question=result.question or "",
                answer=result.answer or "",
                contexts=result.contexts or [],
                ground_truth=result.ground_truth,
            )
            vectors.append(vector)

        return vectors

    def _compute_features(self, result: TestCaseResult) -> dict[str, float]:
        """개별 테스트 케이스의 피처 계산."""
        features: dict[str, float] = {}

        # 텍스트 길이 피처
        question = result.question or ""
        answer = result.answer or ""
        contexts = result.contexts or []

        features["question_length"] = float(len(question))
        features["answer_length"] = float(len(answer))
        features["context_count"] = float(len(contexts))
        features["total_context_length"] = float(sum(len(c) for c in contexts))
        features["avg_context_length"] = (
            features["total_context_length"] / len(contexts) if contexts else 0.0
        )

        # 단어 수 피처
        features["question_word_count"] = float(len(question.split()))
        features["answer_word_count"] = float(len(answer.split()))

        # 키워드 겹침 피처
        question_words = set(self._extract_keywords(question))
        answer_words = set(self._extract_keywords(answer))
        context_words = set()
        for ctx in contexts:
            context_words.update(self._extract_keywords(ctx))

        if question_words:
            features["question_context_overlap"] = len(question_words & context_words) / len(
                question_words
            )
            features["question_answer_overlap"] = len(question_words & answer_words) / len(
                question_words
            )
        else:
            features["question_context_overlap"] = 0.0
            features["question_answer_overlap"] = 0.0

        features["keyword_overlap"] = features["question_context_overlap"]

        # ground_truth 존재 여부
        features["has_ground_truth"] = 1.0 if result.ground_truth else 0.0

        # 질문 유형 (간단한 휴리스틱)
        features["is_reasoning_question"] = 1.0 if self._is_reasoning_question(question) else 0.0
        features["is_multi_part_question"] = 1.0 if self._is_multi_part_question(question) else 0.0

        # 숫자/날짜 포함 여부
        features["answer_has_numbers"] = 1.0 if re.search(r"\d+", answer) else 0.0
        features["context_has_numbers"] = (
            1.0 if any(re.search(r"\d+", c) for c in contexts) else 0.0
        )

        return features

    def _extract_keywords(self, text: str) -> list[str]:
        """텍스트에서 키워드 추출 (간단한 버전)."""
        # 한국어 + 영어 단어 추출
        words = re.findall(r"[가-힣]+|[a-zA-Z]+", text.lower())
        # 2글자 이상만 유지
        return [w for w in words if len(w) >= 2]

    def _is_reasoning_question(self, question: str) -> bool:
        """추론형 질문 여부."""
        reasoning_patterns = ["왜", "어떻게", "why", "how", "원인", "이유", "방법"]
        return any(p in question.lower() for p in reasoning_patterns)

    def _is_multi_part_question(self, question: str) -> bool:
        """복합 질문 여부."""
        # 접속사나 구분자로 여러 부분을 포함하는지 확인
        multi_patterns = [
            "그리고",
            "또한",
            "및",
            "와/과",
            "와",
            "과",
            ",",
            "1)",
            "2)",
            "첫째",
            "둘째",
        ]
        question_lower = question.lower()
        return sum(1 for p in multi_patterns if p in question_lower) >= 2 or question.count("?") > 1

    def _detect_single_pattern(
        self,
        pattern_def: PatternDefinitionProtocol,
        feature_vectors: list[FeatureVector],
        target_metric: str,
        threshold: float,
    ) -> PatternEvidence | None:
        """단일 패턴 탐지."""
        # 각 규칙 확인 (AND 로직: 모든 규칙을 만족해야 매칭)
        rule_results: list[dict[str, Any]] = []
        all_rule_matched_ids: list[set[str]] = []

        for rule in pattern_def.detection_rules:
            handler = self._rule_handlers.get(rule.rule_type)
            if not handler:
                logger.warning(f"Unknown rule type: {rule.rule_type}")
                continue

            result = handler(
                rule=rule,
                vectors=feature_vectors,
                target_metric=target_metric,
                threshold=threshold,
            )
            rule_results.append(result)

            # 각 규칙별 매칭된 ID 수집
            if result.get("matched"):
                matched_ids = {v.test_case_id for v in result.get("matched_vectors", [])}
                all_rule_matched_ids.append(matched_ids)
            else:
                # 규칙이 매칭되지 않으면 빈 집합
                all_rule_matched_ids.append(set())

        # 규칙이 없으면 패턴 없음
        if not all_rule_matched_ids:
            return None

        # AND 로직: 모든 규칙에서 매칭된 ID의 교집합
        common_ids = all_rule_matched_ids[0]
        for ids in all_rule_matched_ids[1:]:
            common_ids = common_ids & ids

        # 교집합이 비어있으면 패턴 없음
        if not common_ids:
            return None

        # 매칭된 벡터 추출
        matched_vectors = [v for v in feature_vectors if v.test_case_id in common_ids]

        # 최소 샘플 수 확인 (최소 1개 이상이면 패턴 탐지)
        if len(matched_vectors) < 1:
            return None

        # 통계 계산
        total_count = len(feature_vectors)
        affected_count = len(matched_vectors)

        # 영향받은/받지 않은 그룹의 메트릭 점수
        affected_scores = [v.metric_scores.get(target_metric, 0) for v in matched_vectors]
        unaffected_ids = {v.test_case_id for v in feature_vectors} - common_ids
        unaffected_scores = [
            v.metric_scores.get(target_metric, 0)
            for v in feature_vectors
            if v.test_case_id in unaffected_ids
        ]

        mean_affected = float(np.mean(affected_scores)) if affected_scores else 0.0
        mean_unaffected = float(np.mean(unaffected_scores)) if unaffected_scores else 0.0

        # 통계적 유의성 검정
        p_value = None
        correlation = None
        if len(affected_scores) >= 3 and len(unaffected_scores) >= 3:
            with contextlib.suppress(ValueError):
                _, p_value = stats.mannwhitneyu(
                    affected_scores, unaffected_scores, alternative="less"
                )

        # 상관관계 계산 (해당하는 경우)
        for result in rule_results:
            if result.get("correlation") is not None:
                correlation = result["correlation"]
                if result.get("p_value") is not None and p_value is None:
                    p_value = result["p_value"]
                break

        # 대표 실패 사례 선택 (점수가 낮은 순)
        sorted_matched = sorted(
            matched_vectors, key=lambda v: v.metric_scores.get(target_metric, 0)
        )
        representative_failures = [
            self._create_failure_sample(v, pattern_def.pattern_type, target_metric)
            for v in sorted_matched[: self._max_samples]
        ]

        # 패턴 타입 변환
        try:
            pattern_type = PatternType(pattern_def.pattern_type)
        except ValueError:
            pattern_type = PatternType.UNKNOWN

        return PatternEvidence(
            pattern_type=pattern_type,
            affected_count=affected_count,
            total_count=total_count,
            correlation=correlation,
            p_value=p_value,
            mean_score_affected=mean_affected,
            mean_score_unaffected=mean_unaffected,
            threshold_used={"metric_threshold": threshold},
            representative_failures=representative_failures,
            source=EvidenceSource.RULE_BASED,
        )

    def _create_failure_sample(
        self,
        vector: FeatureVector,
        pattern_type: str,
        target_metric: str,
    ) -> FailureSample:
        """실패 샘플 생성."""
        try:
            p_type = PatternType(pattern_type)
        except ValueError:
            p_type = PatternType.UNKNOWN

        return FailureSample(
            test_case_id=vector.test_case_id,
            question=vector.question,
            answer=vector.answer,
            contexts=vector.contexts,
            ground_truth=vector.ground_truth,
            metric_scores=vector.metric_scores,
            failure_reason=f"Low {target_metric} score with {pattern_type} pattern",
            detected_patterns=[p_type],
            analysis_source=EvidenceSource.RULE_BASED,
        )

    # =========================================================================
    # 규칙 핸들러
    # =========================================================================

    def _check_metric_threshold(
        self,
        rule: DetectionRule,
        vectors: list[FeatureVector],
        target_metric: str,
        threshold: float,
    ) -> dict[str, Any]:
        """메트릭 임계값 규칙 확인."""
        if not rule.condition:
            return {"matched": False, "matched_vectors": []}

        matched = []
        for v in vectors:
            if self._evaluate_condition(rule.condition, v.metric_scores, v.features):
                matched.append(v)

        return {"matched": bool(matched), "matched_vectors": matched}

    def _check_feature_threshold(
        self,
        rule: DetectionRule,
        vectors: list[FeatureVector],
        target_metric: str,
        threshold: float,
    ) -> dict[str, Any]:
        """피처 임계값 규칙 확인."""
        if not rule.feature or rule.threshold is None:
            return {"matched": False, "matched_vectors": []}

        feature = rule.feature
        thresh = rule.threshold
        direction = rule.direction or "greater_than"

        matched = []
        for v in vectors:
            value = v.features.get(feature, 0)
            if (
                direction == "greater_than"
                and value > thresh
                or direction == "less_than"
                and value < thresh
                or direction == "greater_than_or_equal"
                and value >= thresh
                or direction == "less_than_or_equal"
                and value <= thresh
            ):
                matched.append(v)

        return {"matched": bool(matched), "matched_vectors": matched}

    def _check_correlation(
        self,
        rule: DetectionRule,
        vectors: list[FeatureVector],
        target_metric: str,
        threshold: float,
    ) -> dict[str, Any]:
        """상관관계 규칙 확인."""
        if len(rule.variables) < 2:
            return {"matched": False, "matched_vectors": [], "correlation": None}

        var1, var2 = rule.variables[0], rule.variables[1]
        min_corr = rule.min_correlation or 0.3
        expected_dir = rule.expected_direction

        # 변수 값 수집
        values1 = []
        values2 = []
        for v in vectors:
            # 변수가 메트릭인지 피처인지 확인
            val1 = v.metric_scores.get(var1) or v.features.get(var1)
            val2 = v.metric_scores.get(var2) or v.features.get(var2)

            if val1 is not None and val2 is not None:
                values1.append(val1)
                values2.append(val2)

        if len(values1) < 5:
            return {"matched": False, "matched_vectors": [], "correlation": None}

        if max(values1) == min(values1) or max(values2) == min(values2):
            return {"matched": False, "matched_vectors": [], "correlation": None}

        # 상관계수 계산
        try:
            result = stats.pearsonr(values1, values2)
            corr_raw = getattr(result, "statistic", None)
            p_value_raw = getattr(result, "pvalue", None)
            if corr_raw is None or p_value_raw is None:
                corr_raw, p_value_raw = result
            corr = float(corr_raw)
            p_value = float(p_value_raw)
        except Exception:
            return {"matched": False, "matched_vectors": [], "correlation": None}

        # 방향 및 강도 확인
        matched = False
        if (
            expected_dir == "negative"
            and corr < -abs(min_corr)
            or expected_dir == "positive"
            and corr > abs(min_corr)
            or expected_dir is None
            and abs(corr) > abs(min_corr)
        ):
            matched = True

        # 상관관계가 유의미하면 모든 벡터를 반환 (전체 패턴이므로)
        matched_vectors = vectors if matched else []

        return {
            "matched": matched,
            "matched_vectors": matched_vectors,
            "correlation": corr,
            "p_value": p_value,
        }

    def _check_metric_combination(
        self,
        rule: DetectionRule,
        vectors: list[FeatureVector],
        target_metric: str,
        threshold: float,
    ) -> dict[str, Any]:
        """메트릭 조합 규칙 확인."""
        if not rule.condition:
            return {"matched": False, "matched_vectors": []}

        matched = []
        for v in vectors:
            if self._evaluate_condition(rule.condition, v.metric_scores, v.features):
                matched.append(v)

        return {"matched": bool(matched), "matched_vectors": matched}

    def _check_text_analysis(
        self,
        rule: DetectionRule,
        vectors: list[FeatureVector],
        target_metric: str,
        threshold: float,
    ) -> dict[str, Any]:
        """텍스트 분석 규칙 확인."""
        if not rule.condition:
            return {"matched": False, "matched_vectors": []}

        condition = rule.condition
        matched = []

        for v in vectors:
            if (
                (
                    condition == "answer_has_numbers_not_in_context"
                    and self._answer_has_numbers_not_in_context(v)
                )
                or (
                    condition == "answer_has_dates_not_in_context"
                    and self._answer_has_dates_not_in_context(v)
                )
                or (
                    condition == "question_has_multiple_parts AND answer_coverage < 0.7"
                    and v.features.get("is_multi_part_question", 0) > 0
                )
                or (
                    condition == "ground_truth_entities_not_in_any_context"
                    and self._ground_truth_not_in_context(v)
                )
            ):
                matched.append(v)

        return {"matched": bool(matched), "matched_vectors": matched}

    def _check_feature_comparison(
        self,
        rule: DetectionRule,
        vectors: list[FeatureVector],
        target_metric: str,
        threshold: float,
    ) -> dict[str, Any]:
        """피처 비교 규칙 확인."""
        if not rule.condition:
            return {"matched": False, "matched_vectors": []}

        matched = []
        for v in vectors:
            if self._evaluate_condition(rule.condition, v.metric_scores, v.features):
                matched.append(v)

        return {"matched": bool(matched), "matched_vectors": matched}

    # =========================================================================
    # 헬퍼 메서드
    # =========================================================================

    def _evaluate_condition(
        self,
        condition: str,
        metric_scores: dict[str, float],
        features: dict[str, float],
    ) -> bool:
        """조건문 평가.

        간단한 조건문을 평가합니다.
        예: "faithfulness < 0.6", "context_precision < 0.5 AND context_recall < 0.6"
        """
        # 변수를 실제 값으로 치환
        all_vars = {**metric_scores, **features}

        # AND/OR 분리
        if " AND " in condition:
            parts = condition.split(" AND ")
            return all(self._evaluate_single_condition(p.strip(), all_vars) for p in parts)
        elif " OR " in condition:
            parts = condition.split(" OR ")
            return any(self._evaluate_single_condition(p.strip(), all_vars) for p in parts)
        else:
            return self._evaluate_single_condition(condition, all_vars)

    def _evaluate_single_condition(
        self,
        condition: str,
        variables: dict[str, float],
    ) -> bool:
        """단일 조건 평가."""
        # 비교 연산자 파싱
        for op in ["<=", ">=", "<", ">", "=="]:
            if op in condition:
                parts = condition.split(op)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()

                    left_val = variables.get(left)
                    if left_val is None:
                        try:
                            left_val = float(left)
                        except ValueError:
                            return False

                    try:
                        right_val = float(right)
                    except ValueError:
                        right_val = variables.get(right)
                        if right_val is None:
                            return False

                    if op == "<":
                        return left_val < right_val
                    elif op == ">":
                        return left_val > right_val
                    elif op == "<=":
                        return left_val <= right_val
                    elif op == ">=":
                        return left_val >= right_val
                    elif op == "==":
                        return abs(left_val - right_val) < 0.0001

        return False

    def _answer_has_numbers_not_in_context(self, v: FeatureVector) -> bool:
        """답변에 컨텍스트에 없는 숫자가 있는지 확인."""
        answer_numbers = set(re.findall(r"\d+(?:\.\d+)?", v.answer))
        context_numbers = set()
        for ctx in v.contexts:
            context_numbers.update(re.findall(r"\d+(?:\.\d+)?", ctx))

        # 답변에만 있는 숫자가 있으면 True
        return bool(answer_numbers - context_numbers)

    def _answer_has_dates_not_in_context(self, v: FeatureVector) -> bool:
        """답변에 컨텍스트에 없는 날짜가 있는지 확인."""
        date_pattern = r"\d{4}[-./년]\d{1,2}[-./월]?\d{0,2}일?"

        answer_dates = set(re.findall(date_pattern, v.answer))
        context_dates = set()
        for ctx in v.contexts:
            context_dates.update(re.findall(date_pattern, ctx))

        return bool(answer_dates - context_dates)

    def _ground_truth_not_in_context(self, v: FeatureVector) -> bool:
        """ground_truth의 핵심 엔티티가 컨텍스트에 없는지 확인."""
        if not v.ground_truth:
            return False

        gt_keywords = set(self._extract_keywords(v.ground_truth))
        context_keywords = set()
        for ctx in v.contexts:
            context_keywords.update(self._extract_keywords(ctx))

        # ground_truth 키워드의 50% 이상이 컨텍스트에 없으면 True
        if not gt_keywords:
            return False

        overlap = len(gt_keywords & context_keywords) / len(gt_keywords)
        return overlap < 0.5
