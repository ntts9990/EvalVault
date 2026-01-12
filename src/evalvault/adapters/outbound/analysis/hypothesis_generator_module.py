from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import (
    get_upstream_output,
    to_serializable,
)


@dataclass
class Hypothesis:
    text: str
    metric_name: str = ""
    confidence: float = 0.0
    evidence: str = ""
    generated_at: str = ""


@dataclass
class HypothesisGenerationResult:
    run_id: str
    method: str
    hypotheses: list[Hypothesis] = field(default_factory=list)
    total_count: int = 0
    confidence_threshold: float = 0.7
    insights: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class HypothesisGeneratorModule(BaseAnalysisModule):
    module_id = "hypothesis_generator"
    name = "Hypothesis Generator"
    description = "Generate hypothesis candidates based on metrics and low performers."
    input_types = ["statistics", "low_performers"]
    output_types = ["hypotheses"]
    requires = ["statistical_analyzer"]
    tags = ["analysis", "hypothesis"]

    def __init__(self, method: str = "heuristic", num_hypotheses: int = 5) -> None:
        self.method = self._normalize_method(method)
        self.num_hypotheses = max(1, int(num_hypotheses))

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        context = inputs.get("__context__", {})
        additional_params = context.get("additional_params", {}) or {}

        method = additional_params.get("method") or params.get("method") or self.method
        num_hypotheses = (
            additional_params.get("num_hypotheses")
            or params.get("num_hypotheses")
            or self.num_hypotheses
        )

        stats_output = get_upstream_output(inputs, "statistics", "statistical_analyzer") or {}
        low_samples_output = get_upstream_output(inputs, "low_samples", "low_performers") or {}

        statistics = stats_output.get("statistics", {}) or {}
        metric_scores: dict[str, float] = {}
        for metric_name, stats in statistics.items():
            if not isinstance(stats, dict):
                continue
            mean_value = stats.get("mean")
            if mean_value is None:
                continue
            try:
                metric_scores[str(metric_name)] = float(mean_value)
            except (TypeError, ValueError):
                continue

        low_performers = low_samples_output.get("low_performers") or stats_output.get(
            "low_performers", []
        )
        low_performers_payload: list[dict[str, Any]] = []
        for low_perf in low_performers:
            if not isinstance(low_perf, dict):
                continue
            question = (
                low_perf.get("question")
                or low_perf.get("question_preview")
                or low_perf.get("test_case_id")
                or ""
            )
            metric_name = low_perf.get("metric_name") or ""
            low_performers_payload.append(
                {"question": str(question), "metric_name": str(metric_name)}
            )

        run_id = stats_output.get("run_id") or context.get("run_id") or ""
        generator = HypothesisGeneratorModule(
            method=str(method),
            num_hypotheses=int(num_hypotheses),
        )
        hypotheses = generator.generate_simple_hypotheses(
            str(run_id), metric_scores, low_performers_payload
        )
        insights = generator._generate_insights(hypotheses)

        return {
            "run_id": run_id,
            "method": generator.method,
            "hypotheses": to_serializable(hypotheses),
            "total_count": len(hypotheses),
            "insights": insights,
        }

    def generate_hypotheses(
        self,
        dataset_path: str,
        config_path: str,
        api_key: str | None = None,
    ) -> HypothesisGenerationResult:
        _ = (config_path, api_key)

        run_id = ""
        metric_scores: dict[str, float] = {}
        low_performers: list[dict[str, Any]] = []

        path = Path(dataset_path)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                data = None

            if isinstance(data, dict):
                run_id = str(data.get("run_id", ""))
                metric_scores = self._extract_metric_scores(data)
                low_performers = self._extract_low_performers(data)

        hypotheses = self.generate_simple_hypotheses(run_id, metric_scores, low_performers)
        insights = self._generate_insights(hypotheses)

        return HypothesisGenerationResult(
            run_id=run_id,
            method=self.method,
            hypotheses=hypotheses,
            total_count=len(hypotheses),
            insights=insights,
        )

    def generate_simple_hypotheses(
        self,
        run_id: str,
        metric_scores: dict[str, float],
        low_performers: Sequence[dict[str, Any]] | None = None,
    ) -> list[Hypothesis]:
        low_performers_list = list(low_performers or [])
        hypotheses: list[Hypothesis] = []
        now = datetime.now().isoformat()

        alias_note = ""
        if (
            self.method == "heuristic"
            and run_id == ""
            and metric_scores == {}
            and not low_performers_list
        ):
            alias_note = "No analysis payload provided; generated generic hypotheses."

        metric_threshold = 0.7
        metric_items = sorted(metric_scores.items(), key=lambda item: item[1])
        for metric_name, mean in metric_items:
            score = float(mean)
            if score >= metric_threshold:
                continue
            hypotheses.append(
                Hypothesis(
                    text=f"{metric_name} mean score ({score:.2f}) below threshold ({metric_threshold:.2f})",
                    metric_name=metric_name,
                    confidence=min(0.95, 0.7 + (metric_threshold - score)),
                    evidence=f"mean={score:.4f}",
                    generated_at=now,
                )
            )

        context_metrics = ["context_precision", "context_recall"]
        context_values: list[float] = []
        for metric in context_metrics:
            value = metric_scores.get(metric)
            if value is not None:
                context_values.append(float(value))
        if context_values:
            context_avg = float(np.mean(context_values))
            if context_avg < metric_threshold:
                hypotheses.append(
                    Hypothesis(
                        text=f"Context quality (avg {context_avg:.2f}) below threshold ({metric_threshold:.2f})",
                        metric_name="context_precision",
                        confidence=0.85,
                        evidence=f"metrics={context_metrics}",
                        generated_at=now,
                    )
                )

        metric_failure_counts: dict[str, int] = {}
        failing_questions: list[str] = []
        for low_perf in low_performers_list:
            if not isinstance(low_perf, dict):
                continue
            metric_name = str(low_perf.get("metric_name", "") or "")
            if metric_name:
                metric_failure_counts[metric_name] = metric_failure_counts.get(metric_name, 0) + 1
            q = low_perf.get("question")
            if isinstance(q, str) and q:
                failing_questions.append(q)

        if metric_failure_counts:
            sorted_metrics = sorted(
                metric_failure_counts.items(), key=lambda item: item[1], reverse=True
            )
            top_metric, top_count = sorted_metrics[0]
            hypotheses.append(
                Hypothesis(
                    text=f"Failures are concentrated in {top_metric} ({top_count} cases)",
                    metric_name=top_metric,
                    confidence=0.8,
                    evidence=f"counts={dict(sorted_metrics[:3])}",
                    generated_at=now,
                )
            )

        if failing_questions:
            sample = failing_questions[: min(10, len(failing_questions))]
            lengths = [len(q) for q in sample]
            avg_length = float(np.mean(lengths)) if lengths else 0.0
            if avg_length > 120:
                hypotheses.append(
                    Hypothesis(
                        text=f"Long questions (avg {avg_length:.0f} chars) correlate with lower scores",
                        metric_name="answer_relevancy",
                        confidence=0.78,
                        evidence=f"lengths={lengths}",
                        generated_at=now,
                    )
                )

            type_keywords = ["difference", "compare", "how", "what"]
            hits = []
            for q in sample:
                q_lower = q.lower()
                if any(keyword in q_lower for keyword in type_keywords):
                    hits.append(q_lower)
            if hits:
                hypotheses.append(
                    Hypothesis(
                        text="Comparative questions show lower performance",
                        metric_name="answer_relevancy",
                        confidence=0.75,
                        evidence=f"examples={hits[:3]}",
                        generated_at=now,
                    )
                )

        if alias_note:
            hypotheses.append(
                Hypothesis(
                    text=alias_note,
                    metric_name="general",
                    confidence=0.72,
                    evidence="",
                    generated_at=now,
                )
            )

        refined = self._refine(hypotheses)
        return refined[: self.num_hypotheses]

    def _normalize_method(self, method: str) -> str:
        normalized = str(method or "").strip().lower()
        if normalized in {"hypogenic", "heuristic"}:
            return "heuristic"
        if normalized in {"hyporefine", "union"}:
            return normalized
        return "heuristic"

    def _extract_metric_scores(self, data: dict[str, Any]) -> dict[str, float]:
        metrics_summary = data.get("metrics_summary")
        if not isinstance(metrics_summary, dict):
            return {}

        metric_scores: dict[str, float] = {}
        for metric_name, stats in metrics_summary.items():
            if isinstance(stats, dict) and "mean" in stats:
                try:
                    metric_scores[str(metric_name)] = float(stats["mean"])
                except Exception:
                    continue
        return metric_scores

    def _extract_low_performers(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        low_performers = data.get("low_performers")
        if isinstance(low_performers, list):
            return [lp for lp in low_performers if isinstance(lp, dict)]
        return []

    def _refine(self, hypotheses: list[Hypothesis]) -> list[Hypothesis]:
        deduped: dict[tuple[str, str], Hypothesis] = {}
        for hypothesis in hypotheses:
            key = (hypothesis.metric_name.strip().lower(), hypothesis.text.strip().lower())
            existing = deduped.get(key)
            if existing is None or hypothesis.confidence > existing.confidence:
                deduped[key] = hypothesis

        ordered = sorted(deduped.values(), key=lambda h: h.confidence, reverse=True)
        if self.method == "union":
            return ordered
        return ordered

    def _generate_insights(self, hypotheses: list[Hypothesis]) -> list[str]:
        if not hypotheses:
            return ["No hypotheses generated."]

        metric_counts: dict[str, int] = {}
        for hypothesis in hypotheses:
            metric = hypothesis.metric_name or "general"
            metric_counts[metric] = metric_counts.get(metric, 0) + 1

        insights: list[str] = []
        insights.append(
            f"Generated {len(hypotheses)} hypotheses across {len(metric_counts)} metrics"
        )

        high_confidence = [h for h in hypotheses if h.confidence >= 0.8]
        if high_confidence:
            insights.append(f"High confidence hypotheses: {len(high_confidence)}/{len(hypotheses)}")

        insights.extend(self._identify_patterns(hypotheses))
        return insights

    def _identify_patterns(self, hypotheses: list[Hypothesis]) -> list[str]:
        patterns: list[str] = []

        if any("length" in h.text.lower() for h in hypotheses):
            patterns.append("Question length impact hypotheses detected")

        if any("context" in h.text.lower() for h in hypotheses):
            patterns.append("Context count impact hypotheses detected")

        if any("compar" in h.text.lower() for h in hypotheses):
            patterns.append("Question type impact hypotheses detected")

        if any("retriev" in h.text.lower() for h in hypotheses):
            patterns.append("Retrieval-related hypotheses detected")

        return patterns
