"""Priority summary module for identifying high-impact cases."""

from __future__ import annotations

import math
import re
from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter
from evalvault.adapters.outbound.analysis.pipeline_helpers import (
    get_upstream_output,
    safe_mean,
    truncate_text,
)
from evalvault.domain.entities import EvaluationRun, TestCaseResult
from evalvault.domain.entities.analysis import QuestionType


class PrioritySummaryModule(BaseAnalysisModule):
    """Summarize lowest-performing and high-impact test cases."""

    module_id = "priority_summary"
    name = "Priority Summary"
    description = "Identify bottom-percentile and high-impact test cases for remediation."
    input_types = ["run", "metrics", "analysis"]
    output_types = ["priority_summary"]
    requires = ["data_loader"]
    tags = ["analysis", "diagnostic"]

    METRIC_WEIGHTS: dict[str, float] = {
        "factual_correctness": 1.0,
        "faithfulness": 0.95,
        "summary_faithfulness": 0.95,
        "answer_relevancy": 0.8,
        "context_recall": 0.7,
        "context_precision": 0.6,
        "semantic_similarity": 0.5,
        "summary_score": 0.8,
        "entity_preservation": 0.9,
    }

    METRIC_HINTS: dict[str, str] = {
        "factual_correctness": "사실 오류 가능성",
        "faithfulness": "컨텍스트-답변 정합성 점검 필요",
        "summary_faithfulness": "요약 근거 불일치 가능성",
        "answer_relevancy": "질문 의도와 답변 불일치 가능성",
        "context_recall": "필수 컨텍스트 누락 가능성",
        "context_precision": "컨텍스트 노이즈/중복 가능성",
        "semantic_similarity": "답변 표현/구조 차이",
        "summary_score": "요약 정보 보존/간결성 이슈",
        "entity_preservation": "핵심 엔티티 누락 가능성",
    }

    QUESTION_TYPE_LABELS: dict[QuestionType, str] = {
        QuestionType.FACTUAL: "사실",
        QuestionType.REASONING: "추론/이유",
        QuestionType.COMPARATIVE: "비교",
        QuestionType.PROCEDURAL: "방법/절차",
        QuestionType.OPINION: "의견",
    }

    QUESTION_TYPE_WEIGHTS: dict[QuestionType, float] = {
        QuestionType.FACTUAL: 1.0,
        QuestionType.PROCEDURAL: 0.95,
        QuestionType.REASONING: 0.8,
        QuestionType.COMPARATIVE: 0.7,
        QuestionType.OPINION: 0.5,
    }

    QUESTION_PRIORITY_ORDER = [
        QuestionType.PROCEDURAL,
        QuestionType.COMPARATIVE,
        QuestionType.REASONING,
        QuestionType.FACTUAL,
        QuestionType.OPINION,
    ]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        context = inputs.get("__context__", {})
        additional = context.get("additional_params", {}) or {}

        bottom_percentile = self._resolve_float(
            params.get("bottom_percentile")
            or additional.get("bottom_percentile")
            or additional.get("priority_bottom_percentile")
            or 10
        )
        impact_limit = self._resolve_int(
            params.get("impact_limit")
            or additional.get("impact_limit")
            or additional.get("priority_impact_limit")
        )

        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")
        run_summary = (
            run.to_summary_dict()
            if isinstance(run, EvaluationRun)
            else loader_output.get("summary")
        )

        if not isinstance(run, EvaluationRun) or not run.results:
            return {
                "bottom_percentile": bottom_percentile,
                "impact_count": 0,
                "total_cases": 0,
                "bottom_count": 0,
                "bottom_cases": [],
                "impact_cases": [],
                "run_metadata": run_summary or {},
            }

        ragas_output = get_upstream_output(inputs, "ragas_eval", "ragas_evaluator") or {}
        per_case = ragas_output.get("per_case", []) if isinstance(ragas_output, dict) else []
        per_case_map = {
            item.get("test_case_id"): item
            for item in per_case
            if isinstance(item, dict) and item.get("test_case_id")
        }

        cases = [self._build_case_summary(result, run, per_case_map) for result in run.results]
        cases = [case for case in cases if case]
        total_cases = len(cases)

        if total_cases == 0:
            return {
                "bottom_percentile": bottom_percentile,
                "impact_count": 0,
                "total_cases": 0,
                "bottom_count": 0,
                "bottom_cases": [],
                "impact_cases": [],
                "run_metadata": run_summary or {},
            }

        bottom_count = max(1, math.ceil(total_cases * bottom_percentile / 100))
        bottom_count = min(bottom_count, total_cases)

        if impact_limit is None:
            impact_limit = max(3, math.ceil(total_cases * 0.1))
        impact_limit = max(1, min(int(impact_limit), total_cases))

        bottom_cases = sorted(cases, key=lambda item: item.get("avg_score", 1.0))[:bottom_count]
        impact_cases = sorted(
            cases,
            key=lambda item: item.get("impact_score", 0.0),
            reverse=True,
        )[:impact_limit]

        for case in bottom_cases:
            case.setdefault("tags", []).append("bottom_percentile")
        for case in impact_cases:
            case.setdefault("tags", []).append("high_impact")

        return {
            "bottom_percentile": bottom_percentile,
            "impact_count": impact_limit,
            "total_cases": total_cases,
            "bottom_count": bottom_count,
            "bottom_cases": bottom_cases,
            "impact_cases": impact_cases,
            "run_metadata": run_summary or {},
        }

    def _build_case_summary(
        self,
        result: TestCaseResult,
        run: EvaluationRun,
        per_case_map: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        per_case = per_case_map.get(result.test_case_id) or {}
        metrics = per_case.get("metrics")
        if not isinstance(metrics, dict):
            metrics = {metric.name: metric.score for metric in result.metrics}

        if not metrics:
            return None

        avg_score = per_case.get("avg_score")
        if not isinstance(avg_score, int | float):
            avg_score = safe_mean(metrics.values())

        gap_by_metric: dict[str, float] = {}
        failed_metrics: list[str] = []
        weighted_gap_sum = 0.0
        weight_total = 0.0
        worst_metric = None
        worst_gap = 0.0
        worst_score = None

        for metric_name, score in metrics.items():
            threshold = self._resolve_threshold(metric_name, result, run)
            gap = max(threshold - float(score), 0.0)
            if gap > 0:
                gap_by_metric[metric_name] = round(gap, 4)
                failed_metrics.append(metric_name)

            weight = self.METRIC_WEIGHTS.get(metric_name, 0.6)
            weighted_gap_sum += gap * weight
            weight_total += weight

            if gap > worst_gap:
                worst_gap = gap
                worst_metric = metric_name
                worst_score = float(score)

        shortfall = safe_mean(gap_by_metric.values()) if gap_by_metric else 0.0
        severity = shortfall
        coverage = len(failed_metrics) / max(len(metrics), 1)
        criticality = (weighted_gap_sum / weight_total) if weight_total else 0.0

        question = result.question or ""
        question_type = self._classify_question_type(question)
        question_weight = self.QUESTION_TYPE_WEIGHTS.get(question_type, 0.7)

        impact_score = 0.45 * severity + 0.25 * coverage + 0.2 * criticality + 0.1 * question_weight

        analysis_hints = self._build_hints(failed_metrics)
        if question_type:
            analysis_hints.append(f"질문 유형: {self.QUESTION_TYPE_LABELS.get(question_type, '')}")

        return {
            "test_case_id": result.test_case_id,
            "avg_score": round(float(avg_score), 4),
            "failed_metrics": failed_metrics,
            "failed_metric_count": len(failed_metrics),
            "gap_by_metric": gap_by_metric,
            "shortfall": round(shortfall, 4),
            "impact_score": round(impact_score, 4),
            "worst_metric": worst_metric,
            "worst_score": round(worst_score, 4) if worst_score is not None else None,
            "worst_gap": round(worst_gap, 4) if worst_gap else None,
            "question_type": question_type.value if question_type else None,
            "question_type_label": self.QUESTION_TYPE_LABELS.get(question_type, None),
            "question_preview": truncate_text(question, 120),
            "analysis_hints": analysis_hints,
            "metadata": run.retrieval_metadata.get(result.test_case_id)
            if run.retrieval_metadata
            else None,
            "tags": [],
        }

    def _resolve_threshold(
        self,
        metric_name: str,
        result: TestCaseResult,
        run: EvaluationRun,
    ) -> float:
        if run.thresholds and metric_name in run.thresholds:
            return float(run.thresholds[metric_name])
        metric = result.get_metric(metric_name)
        if metric and metric.threshold is not None:
            return float(metric.threshold)
        return 0.7

    def _classify_question_type(self, question: str) -> QuestionType | None:
        if not question:
            return None
        question_lower = question.lower()
        patterns = NLPAnalysisAdapter.QUESTION_PATTERNS
        for q_type in self.QUESTION_PRIORITY_ORDER:
            for pattern in patterns.get(q_type, []):
                if re.search(pattern, question_lower, re.IGNORECASE):
                    return q_type
        return QuestionType.FACTUAL

    def _build_hints(self, failed_metrics: list[str]) -> list[str]:
        hints = []
        for metric in failed_metrics:
            hint = self.METRIC_HINTS.get(metric)
            if hint:
                hints.append(hint)
        return hints

    def _resolve_float(self, value: Any) -> float:
        try:
            return max(1.0, min(float(value), 100.0))
        except (TypeError, ValueError):
            return 10.0

    def _resolve_int(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return None
