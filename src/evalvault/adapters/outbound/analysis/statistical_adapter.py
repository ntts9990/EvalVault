"""통계 분석 어댑터.

numpy/scipy 기반 통계 분석 기능을 제공합니다.
- 메트릭별 기술통계
- 상관관계 분석
- t-test, Mann-Whitney U 검정
- Cohen's d 효과 크기
"""

from __future__ import annotations

import logging
from typing import Any, Literal, cast

import numpy as np
from scipy import stats

from evalvault.adapters.outbound.analysis.common import BaseAnalysisAdapter
from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.analysis import (
    ComparisonResult,
    CorrelationInsight,
    LowPerformerInfo,
    MetricStats,
    StatisticalAnalysis,
)

logger = logging.getLogger(__name__)


class StatisticalAnalysisAdapter(BaseAnalysisAdapter):
    """통계 분석 어댑터.

    AnalysisPort 인터페이스를 구현합니다.
    """

    def __init__(self) -> None:
        super().__init__()

    def analyze(self, run: EvaluationRun, **kwargs):
        """BaseAnalysisAdapter 규약: 기본 분석 진입점."""
        return self.analyze_statistics(run, **kwargs)

    def analyze_statistics(
        self,
        run: EvaluationRun,
        *,
        include_correlations: bool = True,
        include_low_performers: bool = True,
        low_performer_threshold: float = 0.5,
    ) -> StatisticalAnalysis:
        """통계 분석을 수행합니다."""
        if not run.results:
            return StatisticalAnalysis(
                run_id=run.run_id,
                insights=["No test cases to analyze"],
            )

        # 메트릭별 점수 추출
        metric_scores = self.processor.extract_metric_scores(run)

        # 메트릭별 통계 요약
        metrics_summary = {}
        for metric_name, scores in metric_scores.items():
            if scores:
                metrics_summary[metric_name] = self._calculate_metric_stats(scores)

        # 상관관계 분석
        correlation_matrix: list[list[float]] = []
        correlation_metrics: list[str] = []
        significant_correlations: list[CorrelationInsight] = []

        if include_correlations and len(metric_scores) >= 2:
            (
                correlation_matrix,
                correlation_metrics,
                significant_correlations,
            ) = self._analyze_correlations(metric_scores)

        # 낮은 성능 케이스 분석
        low_performers: list[LowPerformerInfo] = []
        if include_low_performers:
            low_performers = self._find_low_performers(run, low_performer_threshold)

        # Pass rate 분석
        overall_pass_rate = run.pass_rate
        metric_pass_rates = self.processor.calculate_metric_pass_rates(run)

        # 인사이트 생성
        insights = self._generate_insights(
            metrics_summary,
            significant_correlations,
            low_performers,
            overall_pass_rate,
        )

        return StatisticalAnalysis(
            run_id=run.run_id,
            metrics_summary=metrics_summary,
            correlation_matrix=correlation_matrix,
            correlation_metrics=correlation_metrics,
            significant_correlations=significant_correlations,
            low_performers=low_performers,
            insights=insights,
            overall_pass_rate=overall_pass_rate,
            metric_pass_rates=metric_pass_rates,
        )

    def compare_runs(
        self,
        run_a: EvaluationRun,
        run_b: EvaluationRun,
        metrics: list[str] | None = None,
        test_type: Literal["t-test", "mann-whitney"] = "t-test",
    ) -> list[ComparisonResult]:
        """두 실행을 통계적으로 비교합니다."""
        scores_a = self.processor.extract_metric_scores(run_a)
        scores_b = self.processor.extract_metric_scores(run_b)

        # 비교할 메트릭 결정 (공통 메트릭)
        if metrics is None:
            common_metrics = set(scores_a.keys()) & set(scores_b.keys())
            metrics = list(common_metrics)

        results = []
        for metric in metrics:
            if metric not in scores_a or metric not in scores_b:
                continue

            values_a = scores_a[metric]
            values_b = scores_b[metric]

            if not values_a or not values_b:
                continue

            result = self._compare_metric(
                run_a.run_id,
                run_b.run_id,
                metric,
                values_a,
                values_b,
                test_type,
            )
            results.append(result)

        return results

    def calculate_effect_size(
        self,
        values_a: list[float],
        values_b: list[float],
    ) -> float:
        """Cohen's d 효과 크기를 계산합니다."""
        if not values_a or not values_b:
            return 0.0

        arr_a = np.array(values_a)
        arr_b = np.array(values_b)

        mean_diff = arr_b.mean() - arr_a.mean()
        pooled_std = np.sqrt((arr_a.var() + arr_b.var()) / 2)

        if pooled_std == 0:
            return 0.0

        return float(mean_diff / pooled_std)

    def _calculate_metric_stats(self, scores: list[float]) -> MetricStats:
        """점수 목록에서 통계를 계산합니다."""
        arr = np.array(scores)

        return MetricStats(
            mean=float(arr.mean()),
            std=float(arr.std()),
            min=float(arr.min()),
            max=float(arr.max()),
            median=float(np.median(arr)),
            percentile_25=float(np.percentile(arr, 25)),
            percentile_75=float(np.percentile(arr, 75)),
            count=len(scores),
        )

    def _analyze_correlations(
        self, metric_scores: dict[str, list[float]]
    ) -> tuple[list[list[float]], list[str], list[CorrelationInsight]]:
        """메트릭 간 상관관계를 분석합니다."""
        metric_names = list(metric_scores.keys())

        # 모든 메트릭의 길이가 같은지 확인
        min_len = min(len(v) for v in metric_scores.values())

        # 상관관계 행렬 계산
        matrix: list[list[float]] = []
        significant_correlations: list[CorrelationInsight] = []

        for i, metric_i in enumerate(metric_names):
            row = []
            scores_i = metric_scores[metric_i][:min_len]

            for j, metric_j in enumerate(metric_names):
                scores_j = metric_scores[metric_j][:min_len]

                if i == j:
                    row.append(1.0)
                elif len(scores_i) < 3 or len(scores_j) < 3:
                    row.append(0.0)
                else:
                    try:
                        result = cast(Any, stats.pearsonr(scores_i, scores_j))
                        corr = float(getattr(result, "statistic", result[0]))
                        p_value = float(getattr(result, "pvalue", result[1]))
                        row.append(corr)

                        # 유의미한 상관관계만 기록 (i < j로 중복 방지)
                        if i < j and p_value < 0.05 and abs(corr) >= 0.3:
                            interpretation = self._interpret_correlation(corr)
                            significant_correlations.append(
                                CorrelationInsight(
                                    variable1=metric_i,
                                    variable2=metric_j,
                                    correlation=float(corr),
                                    p_value=float(p_value),
                                    is_significant=True,
                                    interpretation=interpretation,
                                )
                            )
                    except Exception:
                        row.append(0.0)

            matrix.append(row)

        return matrix, metric_names, significant_correlations

    def _interpret_correlation(self, corr: float) -> str:
        """상관계수를 해석합니다."""
        abs_corr = abs(corr)
        direction = "positive" if corr > 0 else "negative"

        if abs_corr >= 0.7:
            strength = "strong"
        elif abs_corr >= 0.5:
            strength = "moderate"
        else:
            strength = "weak"

        return f"{strength} {direction} correlation"

    def _find_low_performers(self, run: EvaluationRun, threshold: float) -> list[LowPerformerInfo]:
        """낮은 성능 케이스를 찾습니다."""
        low_performers = []

        for result in run.results:
            for metric in result.metrics:
                if metric.score < threshold:
                    question_preview = ""
                    if result.question:
                        question_preview = (
                            result.question[:47] + "..."
                            if len(result.question) > 50
                            else result.question
                        )

                    low_performers.append(
                        LowPerformerInfo(
                            test_case_id=result.test_case_id,
                            metric_name=metric.name,
                            score=metric.score,
                            threshold=metric.threshold,
                            question_preview=question_preview,
                            potential_causes=self._infer_causes(metric.name, metric.score),
                        )
                    )

        # 점수 기준 정렬 (낮은 순)
        low_performers.sort(key=lambda x: x.score)

        return low_performers[:20]  # 상위 20개만

    def _infer_causes(self, metric_name: str, score: float) -> list[str]:
        """낮은 점수의 잠재적 원인을 추론합니다."""
        causes = []

        if metric_name == "faithfulness":
            if score < 0.3:
                causes.append("Answer contains information not in context")
                causes.append("Possible hallucination")
            else:
                causes.append("Partial mismatch with context")
        elif metric_name == "summary_faithfulness":
            if score < 0.3:
                causes.append("Summary contains unsupported statements")
                causes.append("Possible hallucination in summary")
            else:
                causes.append("Summary partially mismatches context")

        elif metric_name == "answer_relevancy":
            if score < 0.3:
                causes.append("Answer does not address the question")
            else:
                causes.append("Answer partially addresses the question")

        elif metric_name == "context_precision":
            causes.append("Retrieved contexts contain irrelevant information")

        elif metric_name == "context_recall":
            causes.append("Missing relevant context for the question")

        elif metric_name == "factual_correctness":
            causes.append("Answer differs from ground truth")

        elif metric_name == "semantic_similarity":
            causes.append("Answer meaning differs from ground truth")
        elif metric_name == "summary_score":
            if score < 0.3:
                causes.append("Summary misses key information from context")
            else:
                causes.append("Summary partially covers key information")
        elif metric_name == "entity_preservation":
            if score < 0.3:
                causes.append("Critical entities are missing or altered in summary")
            else:
                causes.append("Some key entities are missing in summary")

        return causes

    def _compare_metric(
        self,
        run_id_a: str,
        run_id_b: str,
        metric: str,
        values_a: list[float],
        values_b: list[float],
        test_type: str,
    ) -> ComparisonResult:
        """단일 메트릭에 대해 두 실행을 비교합니다."""
        arr_a = np.array(values_a)
        arr_b = np.array(values_b)

        mean_a = float(arr_a.mean())
        mean_b = float(arr_b.mean())

        # 통계 검정
        if len(arr_a) < 2 or len(arr_b) < 2 or np.std(arr_a) == 0.0 and np.std(arr_b) == 0.0:
            p_value = 1.0
        elif test_type == "t-test":
            result = cast(Any, stats.ttest_ind(arr_a, arr_b))
            p_value = float(getattr(result, "pvalue", result[1]))
        elif test_type == "mann-whitney":
            result = cast(Any, stats.mannwhitneyu(arr_a, arr_b, alternative="two-sided"))
            p_value = float(getattr(result, "pvalue", result[1]))
        else:
            raise ValueError(f"Unknown test type: {test_type}")

        # 효과 크기
        effect_size = self.calculate_effect_size(values_a, values_b)

        return ComparisonResult.from_values(
            run_id_a=run_id_a,
            run_id_b=run_id_b,
            metric=metric,
            mean_a=mean_a,
            mean_b=mean_b,
            p_value=float(p_value),
            effect_size=effect_size,
        )

    def _generate_insights(
        self,
        metrics_summary: dict[str, MetricStats],
        correlations: list[CorrelationInsight],
        low_performers: list[LowPerformerInfo],
        pass_rate: float,
    ) -> list[str]:
        """분석 결과에서 인사이트를 생성합니다."""
        insights = []

        # Pass rate 기반 인사이트
        if pass_rate >= 0.9:
            insights.append(f"Excellent overall pass rate: {pass_rate:.1%}")
        elif pass_rate >= 0.7:
            insights.append(f"Good overall pass rate: {pass_rate:.1%}")
        elif pass_rate >= 0.5:
            insights.append(f"Moderate pass rate needs improvement: {pass_rate:.1%}")
        else:
            insights.append(f"Low pass rate requires attention: {pass_rate:.1%}")

        # 가장 낮은 메트릭 식별
        if metrics_summary:
            worst_metric = min(metrics_summary.items(), key=lambda x: x[1].mean)
            best_metric = max(metrics_summary.items(), key=lambda x: x[1].mean)

            insights.append(
                f"Best performing metric: {best_metric[0]} (mean: {best_metric[1].mean:.3f})"
            )
            insights.append(
                f"Worst performing metric: {worst_metric[0]} (mean: {worst_metric[1].mean:.3f})"
            )

            # 분산이 큰 메트릭
            high_variance_metrics = [
                (name, stat) for name, stat in metrics_summary.items() if stat.std > 0.2
            ]
            if high_variance_metrics:
                names = ", ".join(m[0] for m in high_variance_metrics)
                insights.append(f"High variance metrics (std > 0.2): {names}")

        # 상관관계 인사이트
        if correlations:
            strong = [c for c in correlations if abs(c.correlation) >= 0.7]
            if strong:
                for c in strong[:2]:  # 상위 2개만
                    insights.append(
                        f"Strong correlation between {c.variable1} and {c.variable2} "
                        f"(r={c.correlation:.2f})"
                    )

        # 낮은 성능 케이스 인사이트
        if low_performers:
            insights.append(
                f"Found {len(low_performers)} low-performing test cases (score < threshold)"
            )

            # 가장 문제가 많은 메트릭
            metric_counts: dict[str, int] = {}
            for lp in low_performers:
                metric_counts[lp.metric_name] = metric_counts.get(lp.metric_name, 0) + 1

            if metric_counts:
                worst = max(metric_counts.items(), key=lambda x: x[1])
                insights.append(f"Most problematic metric: {worst[0]} ({worst[1]} low performers)")

        return insights
