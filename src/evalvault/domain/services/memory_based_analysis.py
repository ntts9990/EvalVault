"""Memory-driven analysis utilities."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from evalvault.domain.entities import EvaluationRun, TestCase
from evalvault.ports.outbound.domain_memory_port import MemoryInsightPort


class MemoryBasedAnalysis:
    """Generate insights by combining EvaluationRun data with Domain Memory."""

    def __init__(self, memory_port: MemoryInsightPort):
        self.memory_port = memory_port

    def generate_insights(
        self,
        *,
        evaluation_run: EvaluationRun,
        domain: str,
        language: str = "ko",
        history_limit: int = 10,
    ) -> dict[str, Any]:
        """Return a summarized insight payload."""

        historical = self.memory_port.list_learnings(
            domain=domain,
            language=language,
            limit=history_limit,
        )
        current_metrics = self._extract_metrics(evaluation_run)
        trends = self._analyze_trends(current_metrics, historical)
        related = self.memory_port.hybrid_search(
            query=evaluation_run.run_id,
            domain=domain,
            language=language,
            limit=5,
        )
        recommendations = self._generate_recommendations(trends, related.get("facts", []))

        return {
            "trends": trends,
            "related_facts": related.get("facts", []),
            "recommendations": recommendations,
        }

    def apply_successful_behaviors(
        self,
        *,
        test_case: TestCase,
        domain: str,
        language: str = "ko",
        min_success_rate: float = 0.8,
        limit: int = 5,
    ) -> list[str]:
        """Return reusable actions for the given context."""

        behaviors = self.memory_port.search_behaviors(
            context=test_case.question,
            domain=domain,
            language=language,
            limit=limit * 2,
        )
        filtered = [b for b in behaviors if b.success_rate >= min_success_rate][:limit]

        actions: list[str] = []
        for behavior in filtered:
            actions.extend(behavior.action_sequence)
        return actions

    def _extract_metrics(self, run: EvaluationRun) -> dict[str, float]:
        """Aggregate metric averages from the evaluation run."""

        scores: dict[str, float] = defaultdict(float)
        counts: dict[str, int] = defaultdict(int)

        for result in run.results:
            for metric in result.metrics:
                scores[metric.name] += metric.score
                counts[metric.name] += 1

        return {
            metric: (scores[metric] / counts[metric]) if counts[metric] else 0.0
            for metric in scores
        }

    def _analyze_trends(
        self,
        current_metrics: dict[str, float],
        historical_learnings,
    ) -> dict[str, dict[str, float]]:
        """Compare current scores with historical learning averages."""

        baseline_sum: dict[str, float] = defaultdict(float)
        baseline_count: dict[str, int] = defaultdict(int)

        for learning in historical_learnings:
            for metric, score in learning.faithfulness_by_entity_type.items():
                baseline_sum[metric] += score
                baseline_count[metric] += 1

        trends: dict[str, dict[str, float]] = {}
        for metric, current in current_metrics.items():
            baseline = (
                baseline_sum[metric] / baseline_count[metric] if baseline_count[metric] else current
            )
            trends[metric] = {
                "current": current,
                "baseline": baseline,
                "delta": current - baseline,
            }
        return trends

    def _generate_recommendations(
        self,
        trends: dict[str, dict[str, float]],
        facts: list,
    ) -> list[str]:
        """Create lightweight textual recommendations."""

        recommendations: list[str] = []
        for metric, info in trends.items():
            delta = info["delta"]
            if delta < -0.05:
                recommendations.append(f"{metric} 감소 감지: 문제 원인을 분석하세요.")
            elif delta > 0.05:
                recommendations.append(f"{metric} 개선 중: 현재 전략을 유지하거나 확장하세요.")

        if facts:
            recommendations.append(
                f"관련 사실 {len(facts)}건을 검토하여 추가 컨텍스트를 확보하세요."
            )
        return recommendations
