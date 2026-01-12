"""분석 서비스.

평가 결과에 대한 통계, NLP, 인과 분석을 오케스트레이션합니다.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import TYPE_CHECKING, Literal

from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.analysis import (
    AnalysisBundle,
    ComparisonResult,
    MetaAnalysisResult,
)

if TYPE_CHECKING:
    from evalvault.ports.outbound import AnalysisCachePort, AnalysisPort
    from evalvault.ports.outbound.causal_analysis_port import CausalAnalysisPort
    from evalvault.ports.outbound.nlp_analysis_port import NLPAnalysisPort

logger = logging.getLogger(__name__)


class AnalysisService:
    """분석 서비스.

    여러 분석 어댑터를 조합하여 종합 분석을 제공합니다.
    """

    def __init__(
        self,
        analysis_adapter: AnalysisPort,
        nlp_adapter: NLPAnalysisPort | None = None,
        causal_adapter: CausalAnalysisPort | None = None,
        cache_adapter: AnalysisCachePort | None = None,
    ):
        """초기화.

        Args:
            analysis_adapter: 통계 분석 어댑터 (AnalysisPort 구현체)
            nlp_adapter: NLP 분석 어댑터 (선택)
            causal_adapter: 인과 분석 어댑터 (선택)
            cache_adapter: 캐시 어댑터 (선택)
        """
        self._analysis = analysis_adapter
        self._nlp = nlp_adapter
        self._causal = causal_adapter
        self._cache = cache_adapter

    def analyze_run(
        self,
        run: EvaluationRun,
        *,
        include_nlp: bool = False,
        include_causal: bool = False,
        use_cache: bool = True,
    ) -> AnalysisBundle:
        """평가 실행에 대한 종합 분석을 수행합니다.

        Args:
            run: 분석할 평가 실행
            include_nlp: NLP 분석 포함 여부
            include_causal: 인과 분석 포함 여부
            use_cache: 캐시 사용 여부

        Returns:
            AnalysisBundle (통계, NLP, 인과 분석 결과)
        """
        # 캐시 키 생성
        cache_key = self._make_cache_key(run.run_id, include_nlp, include_causal)

        # 캐시 조회
        if use_cache and self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for analysis: {run.run_id}")
                return cached

        logger.info(f"Analyzing run: {run.run_id}")

        # 통계 분석 (항상 수행)
        statistical = self._analysis.analyze_statistics(run)

        # NLP 분석 (선택적)
        nlp = None
        if include_nlp and self._nlp is not None:
            logger.debug(f"Running NLP analysis for: {run.run_id}")
            nlp = self._nlp.analyze(run)

        # 인과 분석 (선택적)
        causal = None
        if include_causal and self._causal is not None:
            logger.debug(f"Running causal analysis for: {run.run_id}")
            causal = self._causal.analyze_causality(run)

        bundle = AnalysisBundle(
            run_id=run.run_id,
            statistical=statistical,
            nlp=nlp,
            causal=causal,
        )

        # 캐시 저장
        if use_cache and self._cache:
            self._cache.set(cache_key, bundle)
            logger.debug(f"Cached analysis for: {run.run_id}")

        return bundle

    def compare_runs(
        self,
        run_a: EvaluationRun,
        run_b: EvaluationRun,
        metrics: list[str] | None = None,
        test_type: Literal["t-test", "mann-whitney"] = "t-test",
    ) -> list[ComparisonResult]:
        """두 평가 실행을 비교합니다.

        Args:
            run_a: 첫 번째 평가 실행
            run_b: 두 번째 평가 실행
            metrics: 비교할 메트릭 (None이면 공통 메트릭 모두)
            test_type: 통계 검정 유형 ('t-test', 'mann-whitney')

        Returns:
            메트릭별 ComparisonResult 리스트
        """
        logger.info(f"Comparing runs: {run_a.run_id} vs {run_b.run_id}")

        return self._analysis.compare_runs(
            run_a,
            run_b,
            metrics=metrics,
            test_type=test_type,
        )

    def meta_analyze(
        self,
        runs: list[EvaluationRun],
        metrics: list[str] | None = None,
        test_type: Literal["t-test", "mann-whitney"] = "t-test",
    ) -> MetaAnalysisResult:
        """여러 평가 실행에 대한 메타 분석을 수행합니다.

        Args:
            runs: 분석할 평가 실행 목록
            metrics: 비교할 메트릭
            test_type: 통계 검정 유형

        Returns:
            MetaAnalysisResult
        """
        if len(runs) < 2:
            return MetaAnalysisResult(
                run_ids=[r.run_id for r in runs],
                recommendations=["At least 2 runs required for meta-analysis"],
            )

        logger.info(f"Meta-analyzing {len(runs)} runs")

        # 모든 쌍에 대해 비교
        all_comparisons: list[ComparisonResult] = []
        run_ids = [r.run_id for r in runs]

        for i, run_a in enumerate(runs):
            for run_b in runs[i + 1 :]:
                comparisons = self.compare_runs(run_a, run_b, metrics, test_type)
                all_comparisons.extend(comparisons)

        # 메트릭별 최고/최저 실행 찾기
        best_runs, worst_runs = self._find_best_worst_runs(runs, metrics)

        # 전체 순위 계산
        overall_ranking = self._calculate_overall_ranking(runs, metrics)

        # 일관성 점수 계산
        consistency_score = self._calculate_consistency(all_comparisons)

        # 권장사항 생성
        recommendations = self._generate_recommendations(all_comparisons, best_runs, worst_runs)

        return MetaAnalysisResult(
            run_ids=run_ids,
            comparisons=all_comparisons,
            best_runs=best_runs,
            worst_runs=worst_runs,
            overall_ranking=overall_ranking,
            consistency_score=consistency_score,
            recommendations=recommendations,
        )

    def _make_cache_key(self, run_id: str, include_nlp: bool, include_causal: bool) -> str:
        """캐시 키를 생성합니다."""
        key_data = {
            "run_id": run_id,
            "nlp": include_nlp,
            "causal": include_causal,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"analysis:{hashlib.md5(key_str.encode()).hexdigest()}"

    def _find_best_worst_runs(
        self,
        runs: list[EvaluationRun],
        metrics: list[str] | None = None,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """메트릭별 최고/최저 실행을 찾습니다."""
        if not runs:
            return {}, {}

        # 메트릭 결정
        if metrics is None:
            metrics = runs[0].metrics_evaluated

        best_runs: dict[str, str] = {}
        worst_runs: dict[str, str] = {}

        for metric in metrics:
            metric_scores: list[tuple[str, float]] = []

            for run in runs:
                avg = run.get_avg_score(metric)
                if avg is not None:
                    metric_scores.append((run.run_id, avg))

            if metric_scores:
                best = max(metric_scores, key=lambda x: x[1])
                worst = min(metric_scores, key=lambda x: x[1])
                best_runs[metric] = best[0]
                worst_runs[metric] = worst[0]

        return best_runs, worst_runs

    def _calculate_overall_ranking(
        self,
        runs: list[EvaluationRun],
        metrics: list[str] | None = None,
    ) -> list[str]:
        """전체 순위를 계산합니다 (평균 점수 기준)."""
        if not runs:
            return []

        if metrics is None:
            metrics = runs[0].metrics_evaluated

        # 각 실행의 전체 평균 계산
        run_averages: list[tuple[str, float]] = []

        for run in runs:
            scores = []
            for metric in metrics:
                avg = run.get_avg_score(metric)
                if avg is not None:
                    scores.append(avg)

            if scores:
                overall_avg = sum(scores) / len(scores)
                run_averages.append((run.run_id, overall_avg))

        # 점수 내림차순 정렬
        run_averages.sort(key=lambda x: x[1], reverse=True)

        return [run_id for run_id, _ in run_averages]

    def _calculate_consistency(self, comparisons: list[ComparisonResult]) -> float:
        """비교 결과의 일관성 점수를 계산합니다.

        일관성 = 유의미한 차이가 있는 비교의 비율
        """
        if not comparisons:
            return 1.0

        significant_count = sum(1 for c in comparisons if c.is_significant)
        return significant_count / len(comparisons)

    def _generate_recommendations(
        self,
        comparisons: list[ComparisonResult],
        best_runs: dict[str, str],
        worst_runs: dict[str, str],
    ) -> list[str]:
        """메타 분석 결과에서 권장사항을 생성합니다."""
        recommendations = []

        # 가장 많이 우승한 실행
        win_counts: dict[str, int] = {}
        for c in comparisons:
            if c.winner:
                win_counts[c.winner] = win_counts.get(c.winner, 0) + 1

        if win_counts:
            best_overall = max(win_counts.items(), key=lambda x: x[1])
            recommendations.append(
                f"Best overall run: {best_overall[0]} (won {best_overall[1]} comparisons)"
            )

        # 일관되게 최고인 메트릭 확인
        if best_runs:
            best_run_counts: dict[str, int] = {}
            for run_id in best_runs.values():
                best_run_counts[run_id] = best_run_counts.get(run_id, 0) + 1

            most_consistent = max(best_run_counts.items(), key=lambda x: x[1])
            if most_consistent[1] > 1:
                recommendations.append(
                    f"Run {most_consistent[0]} is best in {most_consistent[1]} metrics"
                )

        # 개선이 필요한 메트릭 식별
        if worst_runs:
            worst_run_counts: dict[str, int] = {}
            for run_id in worst_runs.values():
                worst_run_counts[run_id] = worst_run_counts.get(run_id, 0) + 1

            most_problematic = max(worst_run_counts.items(), key=lambda x: x[1])
            if most_problematic[1] > 1:
                recommendations.append(
                    f"Run {most_problematic[0]} needs improvement in {most_problematic[1]} metrics"
                )

        if not recommendations:
            recommendations.append("No significant differences found between runs")

        return recommendations
