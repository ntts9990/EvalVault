"""Improvement Guide Service.

규칙 기반 패턴 탐지와 LLM 기반 인사이트 생성을 결합하여
RAG 시스템 개선 가이드를 생성하는 서비스입니다.
"""

from __future__ import annotations

import contextlib
import logging
from collections import defaultdict
from collections.abc import Mapping
from typing import Any

from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.improvement import (
    EffortLevel,
    EvidenceSource,
    ImprovementAction,
    ImprovementEvidence,
    ImprovementPriority,
    ImprovementReport,
    PatternEvidence,
    RAGComponent,
    RAGImprovementGuide,
)
from evalvault.domain.entities.stage import StageMetric
from evalvault.domain.services.stage_metric_guide_service import StageMetricGuideService
from evalvault.ports.outbound.improvement_port import (
    ActionDefinitionProtocol,
    InsightGeneratorPort,
    PatternDefinitionProtocol,
    PatternDetectorPort,
    PlaybookPort,
)

logger = logging.getLogger(__name__)


class ImprovementGuideService:
    """개선 가이드 서비스.

    Rule-based Pattern Detector와 LLM-based Insight Generator를
    결합하여 하이브리드 분석을 수행합니다.

    분석 흐름:
    1. Rule-based: 플레이북 규칙으로 패턴 탐지 (빠름, 결정적)
    2. LLM-based: 규칙으로 탐지하기 어려운 패턴 분석 (깊음, 확률적)
    3. Hybrid: 두 결과를 결합하여 종합 리포트 생성
    """

    def __init__(
        self,
        pattern_detector: PatternDetectorPort,
        insight_generator: InsightGeneratorPort | None = None,
        playbook: PlaybookPort | None = None,
        stage_metric_playbook: Mapping[str, Mapping[str, Any]] | None = None,
        *,
        enable_llm_enrichment: bool = True,
        max_llm_samples: int = 5,
    ):
        """초기화.

        Args:
            pattern_detector: 규칙 기반 패턴 탐지기
            insight_generator: LLM 기반 인사이트 생성기 (선택)
            playbook: 플레이북 (None이면 기본 플레이북)
            enable_llm_enrichment: LLM으로 결과 보강 여부
            max_llm_samples: LLM 분석에 사용할 최대 샘플 수
        """
        self._detector = pattern_detector
        self._generator = insight_generator
        self._playbook = playbook
        self._stage_metric_playbook = stage_metric_playbook
        self._enable_llm = enable_llm_enrichment and insight_generator is not None
        self._max_llm_samples = max_llm_samples

    def generate_report(
        self,
        run: EvaluationRun,
        metrics: list[str] | None = None,
        stage_metrics: list[StageMetric] | None = None,
        *,
        include_llm_analysis: bool | None = None,
    ) -> ImprovementReport:
        """개선 리포트 생성.

        Args:
            run: 분석할 평가 실행
            metrics: 분석할 메트릭 (None이면 모두)
            include_llm_analysis: LLM 분석 포함 여부 (None이면 설정 사용)

        Returns:
            ImprovementReport 종합 리포트
        """
        logger.info(f"Generating improvement report for run: {run.run_id}")

        use_llm = include_llm_analysis if include_llm_analysis is not None else self._enable_llm

        # 1. 기본 정보 수집
        metric_scores = {}
        metric_thresholds = {}
        metric_gaps = {}

        target_metrics = metrics or run.metrics_evaluated

        for metric in target_metrics:
            avg_score = run.get_avg_score(metric)
            threshold = run.thresholds.get(metric, 0.7)

            if avg_score is not None:
                metric_scores[metric] = avg_score
                metric_thresholds[metric] = threshold
                metric_gaps[metric] = threshold - avg_score

        # 2. Rule-based 패턴 탐지
        logger.debug("Running rule-based pattern detection")
        detected_patterns = self._detector.detect_patterns(run, target_metrics)

        # 3. 개선 가이드 생성
        guides: list[RAGImprovementGuide] = []
        analysis_methods = [EvidenceSource.RULE_BASED]

        for metric, patterns in detected_patterns.items():
            for pattern in patterns:
                guide = self._create_guide_from_pattern(
                    metric=metric,
                    pattern=pattern,
                    threshold=metric_thresholds.get(metric, 0.7),
                    run_id=run.run_id,
                )
                if guide:
                    guides.append(guide)

        # 4. LLM 분석으로 보강 (선택적)
        if use_llm and self._generator:
            logger.debug("Running LLM-based analysis")
            analysis_methods.append(EvidenceSource.LLM_ANALYSIS)

            guides = self._enrich_with_llm(
                guides=guides,
                run=run,
                metric_scores=metric_scores,
                metric_thresholds=metric_thresholds,
            )

        # 5. StageMetric 기반 가이드 추가 (선택)
        if stage_metrics:
            stage_guides = StageMetricGuideService(
                action_overrides=self._stage_metric_playbook
            ).build_guides(stage_metrics)
            guides.extend(stage_guides)

        # 6. 가이드 정렬 (우선순위 순)
        guides = self._sort_guides(guides)

        # 7. 예상 개선폭 계산
        total_expected = {}
        for guide in guides:
            for metric in guide.target_metrics:
                if metric not in total_expected:
                    total_expected[metric] = 0.0
                total_expected[metric] += guide.total_expected_improvement

        # 8. 리포트 생성
        metadata: dict[str, Any] = {}
        if stage_metrics:
            metadata["stage_metrics_summary"] = _summarize_stage_metrics(stage_metrics)

        report = ImprovementReport(
            run_id=run.run_id,
            total_test_cases=run.total_test_cases,
            failed_test_cases=run.total_test_cases - run.passed_test_cases,
            pass_rate=run.pass_rate,
            metric_scores=metric_scores,
            metric_thresholds=metric_thresholds,
            metric_gaps=metric_gaps,
            guides=guides,
            total_expected_improvement=total_expected,
            analysis_methods_used=analysis_methods,
            metadata=metadata,
        )

        logger.info(
            f"Generated report with {len(guides)} improvement guides "
            f"for {len(detected_patterns)} metrics"
        )

        return report

    def _create_guide_from_pattern(
        self,
        metric: str,
        pattern: PatternEvidence,
        threshold: float,
        run_id: str,
    ) -> RAGImprovementGuide | None:
        """패턴 증거에서 개선 가이드 생성."""
        # 플레이북에서 패턴 정의 찾기
        pattern_def = self._find_pattern_definition(metric, pattern.pattern_type.value)
        if not pattern_def:
            logger.debug(
                f"No pattern definition found for {pattern.pattern_type.value} in {metric}"
            )
            return None

        # 컴포넌트 변환
        try:
            component = RAGComponent(pattern_def.component)
        except ValueError:
            component = RAGComponent.RETRIEVER

        # 우선순위 변환
        priority = self._convert_priority(pattern_def.priority)

        # 액션 생성
        actions = [self._convert_action(action_def, pattern) for action_def in pattern_def.actions]

        # 증거 생성
        evidence = ImprovementEvidence(
            target_metric=metric,
            detected_patterns=[pattern],
            total_failures=pattern.affected_count,
            avg_score_failures=pattern.mean_score_affected or 0.0,
            avg_score_passes=pattern.mean_score_unaffected or 0.0,
            analysis_methods=[EvidenceSource.RULE_BASED],
        )

        # 영향받은 테스트 케이스 ID
        affected_ids = [f.test_case_id for f in pattern.representative_failures]

        # 검증 명령어
        verification_cmd = self._generate_verification_command(metric, run_id)

        return RAGImprovementGuide(
            component=component,
            target_metrics=[metric],
            priority=priority,
            actions=actions,
            evidence=evidence,
            affected_test_case_ids=affected_ids,
            verification_command=verification_cmd,
            metadata={
                "pattern_type": pattern.pattern_type.value,
                "affected_ratio": pattern.affected_ratio,
            },
        )

    def _find_pattern_definition(
        self,
        metric: str,
        pattern_type: str,
    ) -> PatternDefinitionProtocol | None:
        """플레이북에서 패턴 정의 찾기."""
        if not self._playbook:
            return None

        playbook = self._playbook.get_metric_playbook(metric)
        if not playbook:
            return None

        for pattern in playbook.patterns:
            if pattern.pattern_type == pattern_type:
                return pattern

        return None

    def _convert_priority(self, priority_str: str) -> ImprovementPriority:
        """문자열 우선순위를 Enum으로 변환."""
        mapping = {
            "p0_critical": ImprovementPriority.P0_CRITICAL,
            "p1_high": ImprovementPriority.P1_HIGH,
            "p2_medium": ImprovementPriority.P2_MEDIUM,
            "p3_low": ImprovementPriority.P3_LOW,
        }
        return mapping.get(priority_str.lower(), ImprovementPriority.P2_MEDIUM)

    def _convert_action(
        self,
        action_def: ActionDefinitionProtocol,
        pattern: PatternEvidence,
    ) -> ImprovementAction:
        """액션 정의를 ImprovementAction으로 변환."""
        effort = EffortLevel.MEDIUM
        with contextlib.suppress(ValueError):
            effort = EffortLevel(action_def.effort)

        # 우선순위 점수 계산 (영향력 / 노력)
        effort_weight = {"low": 1.0, "medium": 2.0, "high": 3.0}
        priority_score = (
            action_def.expected_improvement
            * pattern.affected_ratio
            / effort_weight.get(action_def.effort, 2.0)
        )

        return ImprovementAction(
            title=action_def.title,
            description=action_def.description,
            implementation_hint=action_def.implementation_hint,
            expected_improvement=action_def.expected_improvement,
            expected_improvement_range=action_def.expected_improvement_range,
            effort=effort,
            priority_score=priority_score,
        )

    def _enrich_with_llm(
        self,
        guides: list[RAGImprovementGuide],
        run: EvaluationRun,
        metric_scores: dict[str, float],
        metric_thresholds: dict[str, float],
    ) -> list[RAGImprovementGuide]:
        """LLM 분석으로 가이드 보강."""
        if not self._generator:
            return guides

        for guide in guides:
            if not guide.evidence or not guide.evidence.detected_patterns:
                continue

            # 대표 실패 사례 수집
            failures = []
            for pattern in guide.evidence.detected_patterns:
                failures.extend(pattern.representative_failures)

            if not failures:
                continue

            # 샘플 수 제한
            sample_failures = failures[: self._max_llm_samples]

            # 각 실패 사례 LLM으로 보강
            for failure in sample_failures:
                try:
                    enriched = self._generator.enrich_failure_sample(failure)
                    # 실패 샘플 업데이트
                    failure.failure_reason = enriched.failure_reason
                    failure.suggested_answer = enriched.suggested_answer
                    failure.analysis_source = EvidenceSource.HYBRID
                except Exception as e:
                    logger.warning(f"Failed to enrich failure sample: {e}")

            # 배치 분석으로 추가 인사이트 생성
            if len(sample_failures) >= 2:
                try:
                    for metric in guide.target_metrics:
                        batch_insight = self._generator.analyze_batch_failures(
                            failures=sample_failures,
                            metric_name=metric,
                            avg_score=metric_scores.get(metric, 0),
                            threshold=metric_thresholds.get(metric, 0.7),
                        )

                        # LLM 분석 결과를 증거에 추가
                        if batch_insight.overall_assessment:
                            guide.evidence.llm_analysis = batch_insight.overall_assessment
                            guide.evidence.llm_confidence = batch_insight.confidence

                        # LLM 제안 액션 추가
                        for imp in batch_insight.prioritized_improvements:
                            if not self._action_exists(guide.actions, imp.get("action", "")):
                                new_action = ImprovementAction(
                                    title=imp.get("action", "LLM 제안"),
                                    description=f"LLM 분석 기반 제안 (신뢰도: {batch_insight.confidence:.0%})",
                                    expected_improvement=imp.get("expected_improvement", 0.05),
                                    effort=self._convert_effort(imp.get("effort", "medium")),
                                    priority_score=0.5,  # LLM 제안은 중간 우선순위
                                )
                                guide.actions.append(new_action)

                except Exception as e:
                    logger.warning(f"Failed batch LLM analysis: {e}")

            # 분석 방법 업데이트
            if EvidenceSource.LLM_ANALYSIS not in guide.evidence.analysis_methods:
                guide.evidence.analysis_methods.append(EvidenceSource.LLM_ANALYSIS)

        return guides

    def _action_exists(self, actions: list[ImprovementAction], title: str) -> bool:
        """동일한 제목의 액션이 있는지 확인."""
        return any(a.title.lower() == title.lower() for a in actions)

    def _convert_effort(self, effort_str: str) -> EffortLevel:
        """문자열 노력을 Enum으로 변환."""
        try:
            return EffortLevel(effort_str.lower())
        except ValueError:
            return EffortLevel.MEDIUM

    def _sort_guides(
        self,
        guides: list[RAGImprovementGuide],
    ) -> list[RAGImprovementGuide]:
        """가이드를 우선순위 순으로 정렬."""
        priority_order = {
            ImprovementPriority.P0_CRITICAL: 0,
            ImprovementPriority.P1_HIGH: 1,
            ImprovementPriority.P2_MEDIUM: 2,
            ImprovementPriority.P3_LOW: 3,
        }

        return sorted(
            guides,
            key=lambda g: (
                priority_order.get(g.priority, 2),
                -g.total_expected_improvement,
            ),
        )

    def _generate_verification_command(self, metric: str, run_id: str) -> str:
        """검증 명령어 생성."""
        return f"""# 개선 전/후 비교
evalvault run dataset.json --metrics {metric} --tag baseline
# ... 개선 적용 ...
evalvault run dataset.json --metrics {metric} --tag after_fix
evalvault compare baseline after_fix --metrics {metric}"""

    def generate_quick_analysis(
        self,
        run: EvaluationRun,
    ) -> dict[str, list[str]]:
        """빠른 분석 (규칙 기반만).

        LLM 없이 규칙 기반 분석만 수행하여 빠른 결과를 반환합니다.

        Args:
            run: 분석할 평가 실행

        Returns:
            메트릭별 개선 제안 목록
        """
        detected_patterns = self._detector.detect_patterns(run)

        results: dict[str, list[str]] = {}

        for metric, patterns in detected_patterns.items():
            suggestions = []
            for pattern in patterns:
                pattern_def = self._find_pattern_definition(metric, pattern.pattern_type.value)
                if pattern_def:
                    for action in pattern_def.actions[:2]:  # 상위 2개만
                        suggestions.append(
                            f"[{pattern.pattern_type.value}] {action.title} "
                            f"(예상 +{action.expected_improvement:.0%})"
                        )
            if suggestions:
                results[metric] = suggestions

        return results


def _summarize_stage_metrics(metrics: list[StageMetric]) -> dict[str, Any]:
    total = len(metrics)
    evaluated = 0
    passed = 0
    failed = 0
    failures: dict[str, list[StageMetric]] = defaultdict(list)

    for metric in metrics:
        if metric.threshold is None:
            continue
        evaluated += 1
        if metric.passed:
            passed += 1
        else:
            failed += 1
            failures[metric.metric_name].append(metric)

    pass_rate = (passed / evaluated) if evaluated else None
    top_failures: list[dict[str, Any]] = []
    for name, items in failures.items():
        avg_score = sum(item.score for item in items) / len(items)
        threshold = next((item.threshold for item in items if item.threshold is not None), None)
        top_failures.append(
            {
                "metric_name": name,
                "count": len(items),
                "avg_score": avg_score,
                "threshold": threshold,
            }
        )

    top_failures.sort(key=lambda item: item["count"], reverse=True)

    return {
        "total": total,
        "evaluated": evaluated,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "top_failures": top_failures[:5],
    }
