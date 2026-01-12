"""LLM-powered analysis report module with evidence support."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import (
    get_upstream_output,
    safe_mean,
    truncate_text,
)
from evalvault.domain.entities import EvaluationRun
from evalvault.ports.outbound.llm_port import LLMPort


class LLMReportModule(BaseAnalysisModule):
    """Generate a report with LLM using evidence from evaluation runs."""

    module_id = "llm_report"
    name = "LLM 보고서"
    description = "LLM과 증거 데이터를 활용해 분석 보고서를 생성합니다."
    input_types = ["run", "metrics", "analysis", "report"]
    output_types = ["report", "evidence"]
    tags = ["report", "llm"]

    def __init__(self, llm_adapter: LLMPort | None = None) -> None:
        self._llm_adapter = llm_adapter

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        use_llm = self._resolve_use_llm(inputs, params)
        context = self._build_context(inputs, params)
        evidence_limit = self._resolve_evidence_limit(inputs, params)
        report_type = context.get("report_type")
        if report_type == "comparison":
            evidence = self._build_comparison_evidence(
                context.get("runs", []),
                max_cases_per_run=max(1, evidence_limit // 2),
            )
        else:
            evidence = self._build_evidence(context.get("run"), max_cases=evidence_limit)

        if not use_llm or self._llm_adapter is None:
            return self._fallback_report(context, evidence, llm_used=False)

        try:
            report = self._llm_adapter.generate_text(
                self._build_prompt(context, evidence),
            )
            return self._build_output(context, evidence, report, llm_used=True)
        except Exception as exc:
            output = self._fallback_report(context, evidence, llm_used=False)
            output["llm_error"] = str(exc)
            return output

    async def execute_async(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        use_llm = self._resolve_use_llm(inputs, params)
        context = self._build_context(inputs, params)
        evidence_limit = self._resolve_evidence_limit(inputs, params)
        report_type = context.get("report_type")
        if report_type == "comparison":
            evidence = self._build_comparison_evidence(
                context.get("runs", []),
                max_cases_per_run=max(1, evidence_limit // 2),
            )
        else:
            evidence = self._build_evidence(context.get("run"), max_cases=evidence_limit)

        if not use_llm or self._llm_adapter is None:
            return self._fallback_report(context, evidence, llm_used=False)

        try:
            if hasattr(self._llm_adapter, "agenerate_text"):
                report = await self._llm_adapter.agenerate_text(
                    self._build_prompt(context, evidence),
                )
            else:
                report = await asyncio.to_thread(
                    self._llm_adapter.generate_text,
                    self._build_prompt(context, evidence),
                )
            return self._build_output(context, evidence, report, llm_used=True)
        except Exception as exc:
            output = self._fallback_report(context, evidence, llm_used=False)
            output["llm_error"] = str(exc)
            return output

    def _resolve_use_llm(self, inputs: dict[str, Any], params: dict[str, Any]) -> bool:
        context = inputs.get("__context__", {})
        additional = context.get("additional_params", {}) or {}
        value = params.get("use_llm")
        if value is None:
            value = additional.get("use_llm_report", True)
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "on"}
        return bool(value)

    def _resolve_evidence_limit(self, inputs: dict[str, Any], params: dict[str, Any]) -> int:
        context = inputs.get("__context__", {})
        additional = context.get("additional_params", {}) or {}
        value = params.get("evidence_limit")
        if value is None:
            value = additional.get("evidence_limit", 6)
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return 6

    def _build_context(self, inputs: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        context = inputs.get("__context__", {})
        report_type = params.get("report_type") or context.get("additional_params", {}).get(
            "report_type"
        )

        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run") if isinstance(loader_output, dict) else None
        runs_output = get_upstream_output(inputs, "load_runs", "run_loader") or {}
        runs = []
        if isinstance(runs_output, dict):
            runs = runs_output.get("runs", [])
        if not isinstance(run, EvaluationRun) and runs:
            run = runs[0]

        stats_output = get_upstream_output(inputs, "statistics", "statistical_analyzer") or {}
        ragas_output = get_upstream_output(inputs, "ragas_eval", "ragas_evaluator") or {}
        diagnostic_output = get_upstream_output(inputs, "diagnostic", "diagnostic_playbook") or {}
        nlp_output = get_upstream_output(inputs, "nlp_analysis", "nlp_analyzer") or {}
        time_series_output = (
            get_upstream_output(inputs, "time_series", "time_series_analyzer") or {}
        )
        root_cause = get_upstream_output(inputs, "root_cause", "root_cause_analyzer") or {}
        pattern = get_upstream_output(inputs, "pattern_detection", "pattern_detector") or {}
        trend = get_upstream_output(inputs, "trend_detection", "trend_detector") or {}
        comparison_details = (
            get_upstream_output(inputs, "run_metric_comparison", "run_metric_comparator") or {}
        )
        comparison_summary = get_upstream_output(inputs, "run_comparison", "run_comparator") or {}
        comparison = comparison_details or comparison_summary or {}
        change_summary = (
            get_upstream_output(inputs, "run_change_detection", "run_change_detector") or {}
        )
        priority_summary = get_upstream_output(inputs, "priority_summary") or {}
        quality_check = (
            get_upstream_output(
                inputs,
                "quality_check",
                "retrieval_quality_checker",
            )
            or {}
        )

        return {
            "query": context.get("query"),
            "run": run if isinstance(run, EvaluationRun) else None,
            "runs": runs if isinstance(runs, list) else [],
            "report_type": report_type or "analysis",
            "stats_summary": stats_output.get("summary") if isinstance(stats_output, dict) else {},
            "stats_detail": (
                stats_output.get("statistics") if isinstance(stats_output, dict) else {}
            ),
            "stats_insights": (
                stats_output.get("insights") if isinstance(stats_output, dict) else []
            ),
            "significant_correlations": (
                stats_output.get("significant_correlations")
                if isinstance(stats_output, dict)
                else []
            ),
            "metric_pass_rates": (
                stats_output.get("metric_pass_rates") if isinstance(stats_output, dict) else {}
            ),
            "low_performers": (
                stats_output.get("low_performers") if isinstance(stats_output, dict) else []
            ),
            "ragas_summary": (
                ragas_output.get("summary") if isinstance(ragas_output, dict) else {}
            ),
            "ragas_metrics": (
                ragas_output.get("metrics") if isinstance(ragas_output, dict) else {}
            ),
            "diagnostics": (
                diagnostic_output.get("diagnostics") if isinstance(diagnostic_output, dict) else []
            ),
            "diagnostic_recommendations": (
                diagnostic_output.get("recommendations")
                if isinstance(diagnostic_output, dict)
                else []
            ),
            "diagnostic_threshold": (
                diagnostic_output.get("threshold") if isinstance(diagnostic_output, dict) else None
            ),
            "nlp_summary": (nlp_output.get("summary") if isinstance(nlp_output, dict) else {}),
            "nlp_statistics": (
                nlp_output.get("statistics") if isinstance(nlp_output, dict) else {}
            ),
            "nlp_question_types": (
                nlp_output.get("question_types") if isinstance(nlp_output, dict) else []
            ),
            "nlp_keywords": (
                nlp_output.get("top_keywords") if isinstance(nlp_output, dict) else []
            ),
            "root_causes": root_cause.get("causes") if isinstance(root_cause, dict) else [],
            "recommendations": (
                root_cause.get("recommendations") if isinstance(root_cause, dict) else []
            ),
            "patterns": pattern.get("patterns") if isinstance(pattern, dict) else [],
            "trends": trend.get("trends") if isinstance(trend, dict) else [],
            "time_series_summary": (
                time_series_output.get("summary") if isinstance(time_series_output, dict) else {}
            ),
            "comparison": comparison if isinstance(comparison, dict) else {},
            "comparison_summary": (
                comparison_summary if isinstance(comparison_summary, dict) else {}
            ),
            "comparison_details": (
                comparison_details if isinstance(comparison_details, dict) else {}
            ),
            "change_summary": change_summary if isinstance(change_summary, dict) else {},
            "priority_summary": (priority_summary if isinstance(priority_summary, dict) else {}),
            "quality_checks": (
                quality_check.get("checks") if isinstance(quality_check, dict) else []
            ),
            "artifact_nodes": self._collect_available_nodes(inputs),
        }

    def _build_evidence(
        self,
        run: EvaluationRun | None,
        max_cases: int = 6,
        *,
        prefix: str = "E",
    ) -> list[dict[str, Any]]:
        if not run or not run.results:
            return []

        evidence: list[dict[str, Any]] = []
        for result in run.results:
            metrics = {metric.name: metric.score for metric in result.metrics}
            avg_score = safe_mean(metrics.values()) if metrics else 0.0
            failed_metrics = [
                metric.name
                for metric in result.metrics
                if metric.score
                < (
                    metric.threshold
                    if metric.threshold is not None
                    else run.thresholds.get(metric.name, 0.7)
                )
            ]
            evidence.append(
                {
                    "test_case_id": result.test_case_id,
                    "avg_score": round(avg_score, 4),
                    "failed_metrics": failed_metrics,
                    "question": truncate_text(result.question, 240),
                    "answer": truncate_text(result.answer, 320),
                    "contexts": [truncate_text(ctx, 280) for ctx in (result.contexts or [])[:3]],
                    "ground_truth": truncate_text(result.ground_truth, 280),
                    "metrics": metrics,
                }
            )

        evidence.sort(key=lambda item: item.get("avg_score", 0.0))
        trimmed = evidence[:max_cases]
        for idx, item in enumerate(trimmed, start=1):
            item["evidence_id"] = f"{prefix}{idx}"
        return trimmed

    def _build_comparison_evidence(
        self,
        runs: list[EvaluationRun],
        *,
        max_cases_per_run: int = 3,
    ) -> list[dict[str, Any]]:
        evidence: list[dict[str, Any]] = []
        labels = ["A", "B"]
        for label, run in zip(labels, runs[:2], strict=False):
            for item in self._build_evidence(run, max_cases=max_cases_per_run, prefix=label):
                item["run_label"] = label
                item["run_id"] = run.run_id
                item["model_name"] = run.model_name
                evidence.append(item)
        return evidence

    def _collect_available_nodes(self, inputs: dict[str, Any]) -> list[str]:
        nodes = []
        for key, value in inputs.items():
            if key == "__context__":
                continue
            if value is None:
                continue
            nodes.append(key)
        return sorted(set(nodes))

    def _resolve_threshold(self, run: EvaluationRun | None, metric: str) -> float:
        if isinstance(run, EvaluationRun):
            return round(float(run._get_threshold(metric)), 4)
        return 0.7

    def _build_metric_scorecard(
        self,
        run: EvaluationRun | None,
        stats_detail: dict[str, Any] | None,
        pass_rates: dict[str, Any] | None,
        ragas_metrics: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        stats_detail = stats_detail or {}
        pass_rates = pass_rates or {}
        ragas_metrics = ragas_metrics or {}

        metrics = set(stats_detail.keys()) | set(pass_rates.keys()) | set(ragas_metrics.keys())
        if isinstance(run, EvaluationRun):
            metrics.update(run.metrics_evaluated)

        scorecard: list[dict[str, Any]] = []
        for metric in sorted(metrics):
            stats = stats_detail.get(metric, {}) if isinstance(stats_detail, dict) else {}
            mean = stats.get("mean")
            if mean is None and isinstance(ragas_metrics, dict):
                mean = ragas_metrics.get(metric)
            threshold = self._resolve_threshold(run, metric)
            pass_rate = pass_rates.get(metric) if isinstance(pass_rates, dict) else None
            status = "unknown"
            if isinstance(mean, int | float):
                status = "pass" if float(mean) >= threshold else "risk"
            elif isinstance(pass_rate, int | float):
                status = "pass" if float(pass_rate) >= 0.7 else "risk"

            scorecard.append(
                {
                    "metric": metric,
                    "mean": round(float(mean), 4) if isinstance(mean, int | float) else None,
                    "std": round(float(stats.get("std")), 4)
                    if isinstance(stats.get("std"), int | float)
                    else None,
                    "min": round(float(stats.get("min")), 4)
                    if isinstance(stats.get("min"), int | float)
                    else None,
                    "max": round(float(stats.get("max")), 4)
                    if isinstance(stats.get("max"), int | float)
                    else None,
                    "median": round(float(stats.get("median")), 4)
                    if isinstance(stats.get("median"), int | float)
                    else None,
                    "count": stats.get("count") if isinstance(stats.get("count"), int) else None,
                    "pass_rate": (
                        round(float(pass_rate), 4) if isinstance(pass_rate, int | float) else None
                    ),
                    "threshold": threshold,
                    "gap": round(threshold - float(mean), 4)
                    if isinstance(mean, int | float)
                    else None,
                    "status": status,
                }
            )
        return scorecard

    def _build_comparison_scorecard(
        self,
        comparison_details: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        comparison_details = comparison_details or {}
        comparisons = comparison_details.get("comparisons", [])
        if not isinstance(comparisons, list):
            return []

        scorecard = []
        for item in comparisons:
            if not isinstance(item, dict):
                continue
            scorecard.append(
                {
                    "metric": item.get("metric"),
                    "mean_a": item.get("mean_a"),
                    "mean_b": item.get("mean_b"),
                    "diff": item.get("diff"),
                    "diff_percent": item.get("diff_percent"),
                    "p_value": item.get("p_value"),
                    "effect_size": item.get("effect_size"),
                    "effect_level": item.get("effect_level"),
                    "is_significant": item.get("is_significant"),
                    "winner": item.get("winner"),
                    "direction": item.get("direction"),
                }
            )
        return scorecard

    def _build_priority_highlights(self, priority_summary: dict[str, Any] | None) -> dict[str, Any]:
        priority_summary = priority_summary or {}
        bottom_cases = priority_summary.get("bottom_cases", [])
        impact_cases = priority_summary.get("impact_cases", [])
        highlights = {
            "bottom_cases": self._trim_priority_cases(bottom_cases),
            "impact_cases": self._trim_priority_cases(impact_cases),
        }
        return highlights

    def _trim_priority_cases(self, cases: Any) -> list[dict[str, Any]]:
        if not isinstance(cases, list):
            return []
        trimmed = []
        for item in cases[:3]:
            if not isinstance(item, dict):
                continue
            trimmed.append(
                {
                    "test_case_id": item.get("test_case_id"),
                    "avg_score": item.get("avg_score"),
                    "failed_metrics": item.get("failed_metrics"),
                    "impact_score": item.get("impact_score"),
                    "worst_metric": item.get("worst_metric"),
                    "question_preview": item.get("question_preview"),
                    "analysis_hints": item.get("analysis_hints"),
                    "tags": item.get("tags"),
                }
            )
        return trimmed

    def _summarize_prompt_changes(self, change_summary: dict[str, Any] | None) -> dict[str, Any]:
        change_summary = change_summary or {}
        prompt_changes = change_summary.get("prompt_changes", {})
        if not isinstance(prompt_changes, dict):
            return {}

        changes = []
        for item in prompt_changes.get("changes", [])[:3]:
            if not isinstance(item, dict):
                continue
            changes.append(
                {
                    "role": item.get("role"),
                    "status": item.get("status"),
                    "prompt_a": item.get("prompt_a"),
                    "prompt_b": item.get("prompt_b"),
                    "diff_preview": item.get("diff_preview", [])[:8],
                }
            )

        return {
            "status": prompt_changes.get("status"),
            "summary": prompt_changes.get("summary"),
            "notes": prompt_changes.get("notes"),
            "changes": changes,
        }

    def _build_quality_summary(self, context: dict[str, Any]) -> dict[str, Any]:
        run = context.get("run")
        ragas_summary = context.get("ragas_summary") or {}
        time_series_summary = context.get("time_series_summary") or {}
        quality_checks = context.get("quality_checks") or []
        change_summary = context.get("change_summary") or {}

        total_cases = run.total_test_cases if isinstance(run, EvaluationRun) else None
        sample_count = ragas_summary.get("sample_count")
        coverage = None
        if isinstance(sample_count, int) and isinstance(total_cases, int) and total_cases > 0:
            coverage = round(sample_count / total_cases, 4)

        failed_checks = [
            item
            for item in quality_checks
            if isinstance(item, dict) and item.get("status") == "fail"
        ]
        flags = []
        if isinstance(total_cases, int) and total_cases < 30:
            flags.append("표본 수가 적음")
        if coverage is not None and coverage < 1.0:
            flags.append("평가 샘플이 전체보다 적음")
        if change_summary.get("summary", {}).get("dataset_changed"):
            flags.append("데이터셋 변경 존재")
        if isinstance(time_series_summary, dict) and time_series_summary.get("run_count", 0) < 3:
            flags.append("추세 분석을 위한 실행 이력 부족")
        if failed_checks:
            flags.append("품질 체크 실패 항목 존재")

        return {
            "total_cases": total_cases,
            "sample_count": sample_count,
            "coverage": coverage,
            "flags": flags,
            "failed_checks": failed_checks,
        }

    @staticmethod
    def _build_artifact_manifest(artifact_nodes: list[str]) -> list[str]:
        return [f"{node}.json" for node in artifact_nodes]

    @staticmethod
    def _format_float(value: Any, precision: int = 4) -> str:
        if value is None:
            return "-"
        try:
            return f"{float(value):.{precision}f}"
        except (TypeError, ValueError):
            return "-"

    @staticmethod
    def _format_percent(value: Any, precision: int = 1) -> str:
        if value is None:
            return "-"
        try:
            return f"{float(value):.{precision}%}"
        except (TypeError, ValueError):
            return "-"

    def _render_scorecard_table(self, scorecard: list[dict[str, Any]]) -> list[str]:
        if not scorecard:
            return ["- 스코어카드 데이터가 없습니다."]
        lines = [
            "| 메트릭 | 평균 | threshold | pass_rate | 상태 |",
            "| --- | --- | --- | --- | --- |",
        ]
        for row in scorecard:
            lines.append(
                "| {metric} | {mean} | {threshold} | {pass_rate} | {status} |".format(
                    metric=row.get("metric", "-"),
                    mean=self._format_float(row.get("mean")),
                    threshold=self._format_float(row.get("threshold")),
                    pass_rate=self._format_percent(row.get("pass_rate")),
                    status=row.get("status", "-"),
                )
            )
        return lines

    def _render_comparison_table(self, scorecard: list[dict[str, Any]]) -> list[str]:
        if not scorecard:
            return ["- 비교 스코어카드 데이터가 없습니다."]
        lines = [
            "| 메트릭 | A | B | diff | p-value | effect | 상태 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for row in scorecard:
            effect_size = row.get("effect_size")
            effect_level = row.get("effect_level")
            effect = self._format_float(effect_size, 3)
            if effect_level:
                effect = f"{effect} ({effect_level})"
            status = "유의" if row.get("is_significant") else "비유의"
            lines.append(
                (
                    "| {metric} | {mean_a} | {mean_b} | {diff} | {p_value} | {effect} | {status} |"
                ).format(
                    metric=row.get("metric", "-"),
                    mean_a=self._format_float(row.get("mean_a")),
                    mean_b=self._format_float(row.get("mean_b")),
                    diff=self._format_float(row.get("diff")),
                    p_value=self._format_float(row.get("p_value")),
                    effect=effect,
                    status=status,
                )
            )
        return lines

    def _build_prompt(self, context: dict[str, Any], evidence: list[dict[str, Any]]) -> str:
        run = context.get("run")
        run_summary = self._build_run_summary(run)
        comparison_runs = [
            self._build_run_summary(candidate)
            for candidate in (context.get("runs") or [])[:2]
            if isinstance(candidate, EvaluationRun)
        ]
        stats_detail = (
            context.get("stats_detail") if isinstance(context.get("stats_detail"), dict) else {}
        )
        metric_pass_rates = (
            context.get("metric_pass_rates")
            if isinstance(context.get("metric_pass_rates"), dict)
            else {}
        )
        ragas_metrics = (
            context.get("ragas_metrics") if isinstance(context.get("ragas_metrics"), dict) else {}
        )
        comparison_details = (
            context.get("comparison_details")
            if isinstance(context.get("comparison_details"), dict)
            else {}
        )
        scorecard = self._build_metric_scorecard(
            run,
            stats_detail,
            metric_pass_rates,
            ragas_metrics,
        )
        comparison_scorecard = self._build_comparison_scorecard(comparison_details)
        quality_summary = self._build_quality_summary(context)
        priority_highlights = self._build_priority_highlights(context.get("priority_summary"))
        prompt_change_summary = self._summarize_prompt_changes(context.get("change_summary"))
        artifact_manifest = self._build_artifact_manifest(context.get("artifact_nodes") or [])
        change_summary = context.get("change_summary")
        if isinstance(change_summary, dict) and prompt_change_summary:
            change_summary = dict(change_summary)
            change_summary["prompt_changes"] = prompt_change_summary
        elif not isinstance(change_summary, dict):
            change_summary = {}
        summary_payload = {
            "report_type": context.get("report_type"),
            "query": context.get("query"),
            "run_summary": run_summary,
            "comparison_runs": {
                "run_a": comparison_runs[0] if len(comparison_runs) > 0 else {},
                "run_b": comparison_runs[1] if len(comparison_runs) > 1 else {},
            },
            "stats_summary": context.get("stats_summary"),
            "stats_detail": stats_detail,
            "stats_insights": context.get("stats_insights"),
            "significant_correlations": context.get("significant_correlations"),
            "metric_pass_rates": context.get("metric_pass_rates"),
            "ragas_summary": context.get("ragas_summary"),
            "ragas_metrics": context.get("ragas_metrics"),
            "diagnostics": context.get("diagnostics"),
            "diagnostic_recommendations": context.get("diagnostic_recommendations"),
            "diagnostic_threshold": context.get("diagnostic_threshold"),
            "nlp_summary": context.get("nlp_summary"),
            "nlp_statistics": context.get("nlp_statistics"),
            "nlp_question_types": context.get("nlp_question_types"),
            "nlp_keywords": context.get("nlp_keywords"),
            "root_causes": context.get("root_causes"),
            "recommendations": context.get("recommendations"),
            "patterns": context.get("patterns"),
            "trends": context.get("trends"),
            "time_series_summary": context.get("time_series_summary"),
            "comparison_summary": context.get("comparison_summary"),
            "comparison": context.get("comparison"),
            "comparison_details": comparison_details,
            "comparison_scorecard": comparison_scorecard,
            "change_summary": change_summary,
            "priority_summary": context.get("priority_summary"),
            "priority_highlights": priority_highlights,
            "quality_checks": context.get("quality_checks"),
            "quality_summary": quality_summary,
            "scorecard": scorecard,
            "artifact_manifest": artifact_manifest,
        }

        summary_json = json.dumps(summary_payload, ensure_ascii=False, indent=2)
        evidence_json = json.dumps(evidence, ensure_ascii=False, indent=2)

        report_type = context.get("report_type")
        if report_type == "comparison":
            requirements = (
                "요구사항:\n"
                "1) 출력 언어: 한국어\n"
                "2) 핵심 주장/원인/개선안에는 evidence_id를 [A1]/[B1] 형식으로 인용\n"
                "3) 섹션: 요약, 변경 사항 요약, 지표 비교 스코어카드, 통계적 신뢰도, "
                "원인 분석, 개선 제안, 다음 단계, 부록(산출물)\n"
                "4) 요약은 한 문장 결론 + 핵심 3개 bullet(지표/변경 사항/사용자 영향)\n"
                "5) 스코어카드는 Markdown 표로 작성 (metric, A, B, diff, p-value, effect, 상태)\n"
                "6) 데이터셋 차이가 있으면 비교 해석 제한을 명확히 표기\n"
                "7) 변경 사항이 없거나 근거가 약하면 '추가 데이터 필요'라고 명시\n"
            )
        elif report_type == "summary":
            requirements = (
                "요구사항:\n"
                "1) 출력 언어: 한국어\n"
                "2) 핵심 주장/개선안에는 evidence_id를 [E1] 형식으로 인용\n"
                "3) 섹션: 요약, 지표 스코어카드, 개선 제안, 다음 단계, 부록(산출물)\n"
                "4) 요약은 한 문장 결론 + 핵심 3개 bullet\n"
                "5) 스코어카드는 Markdown 표로 작성 (metric, 평균, threshold, pass_rate, 상태)\n"
                "6) 근거가 부족하면 '추가 데이터 필요'라고 명시\n"
            )
        else:
            requirements = (
                "요구사항:\n"
                "1) 출력 언어: 한국어\n"
                "2) 핵심 주장/원인/개선안에는 evidence_id를 [E1] 형식으로 인용\n"
                "3) 섹션: 요약, 지표 스코어카드, 데이터 품질/신뢰도, 증거 기반 인사이트, "
                "원인 가설, 개선 제안, 다음 단계, 부록(산출물)\n"
                "4) 요약은 한 문장 결론 + 핵심 3개 bullet(지표/원인/사용자 영향)\n"
                "5) 스코어카드는 Markdown 표로 작성 (metric, 평균, threshold, pass_rate, 상태)\n"
                "6) 사용자 영향은 신뢰/이해/인지부하 관점으로 1~2문장\n"
                "7) 근거가 부족하면 '추가 데이터 필요'라고 명시\n"
            )

        return (
            "당신은 RAG 평가 분석 보고서 작성자입니다. "
            "아래 데이터와 증거를 기반으로 Markdown 보고서를 작성하세요.\n"
            "\n"
            f"{requirements}\n"
            "[요약 데이터]\n"
            f"{summary_json}\n"
            "\n"
            "[증거]\n"
            f"{evidence_json}\n"
        )

    def _build_run_summary(self, run: EvaluationRun | None) -> dict[str, Any]:
        if not run:
            return {}
        metric_avgs = {
            metric: round(run.get_avg_score(metric) or 0.0, 4) for metric in run.metrics_evaluated
        }
        thresholds = {
            metric: self._resolve_threshold(run, metric) for metric in run.metrics_evaluated
        }
        return {
            "run_id": run.run_id,
            "dataset_name": run.dataset_name,
            "dataset_version": run.dataset_version,
            "model_name": run.model_name,
            "total_test_cases": run.total_test_cases,
            "pass_rate": round(run.pass_rate, 4),
            "metric_pass_rate": round(run.metric_pass_rate, 4),
            "metrics": metric_avgs,
            "thresholds": thresholds,
        }

    def _build_output(
        self,
        context: dict[str, Any],
        evidence: list[dict[str, Any]],
        report: str,
        *,
        llm_used: bool,
    ) -> dict[str, Any]:
        run = context.get("run")
        return {
            "report": report,
            "format": "markdown",
            "llm_used": llm_used,
            "llm_model": self._llm_adapter.get_model_name() if self._llm_adapter else None,
            "run_id": run.run_id if isinstance(run, EvaluationRun) else None,
            "summary": {
                "report_type": context.get("report_type"),
                "total_evidence": len(evidence),
                "has_run": bool(run),
            },
            "evidence": evidence,
        }

    def _fallback_report(
        self,
        context: dict[str, Any],
        evidence: list[dict[str, Any]],
        *,
        llm_used: bool,
    ) -> dict[str, Any]:
        report_type = context.get("report_type") or "analysis"
        run_summary = self._build_run_summary(context.get("run"))
        comparison_runs = [
            self._build_run_summary(candidate)
            for candidate in (context.get("runs") or [])[:2]
            if isinstance(candidate, EvaluationRun)
        ]
        scorecard = self._build_metric_scorecard(
            context.get("run"),
            context.get("stats_detail"),
            context.get("metric_pass_rates"),
            context.get("ragas_metrics"),
        )
        comparison_scorecard = self._build_comparison_scorecard(context.get("comparison_details"))
        quality_summary = self._build_quality_summary(context)
        artifact_manifest = self._build_artifact_manifest(context.get("artifact_nodes") or [])

        if report_type == "comparison":
            title = "# 비교 분석 보고서"
        elif report_type == "summary":
            title = "# 요약 보고서"
        else:
            title = "# 분석 보고서"

        report_lines = [title, "", "## 요약"]

        if report_type == "comparison":
            run_a = comparison_runs[0] if len(comparison_runs) > 0 else {}
            run_b = comparison_runs[1] if len(comparison_runs) > 1 else {}
            comparison_summary = context.get("comparison_summary") or {}
            report_lines.extend(
                [
                    f"- A 실행: {run_a.get('run_id', '-')}",
                    f"- B 실행: {run_b.get('run_id', '-')}",
                    f"- A 모델: {run_a.get('model_name', '-')}",
                    f"- B 모델: {run_b.get('model_name', '-')}",
                    f"- 승자: {comparison_summary.get('winner', 'N/A')}",
                    "",
                ]
            )
        elif run_summary:
            report_lines.extend(
                [
                    f"- 데이터셋: {run_summary.get('dataset_name', '-')}",
                    f"- 모델: {run_summary.get('model_name', '-')}",
                    f"- 테스트 케이스: {run_summary.get('total_test_cases', 0)}",
                    f"- 통과율: {self._format_percent(run_summary.get('pass_rate'))}",
                    f"- 메트릭 통과율: {self._format_percent(run_summary.get('metric_pass_rate'))}",
                    "",
                ]
            )

        if report_type == "comparison":
            change_summary = context.get("change_summary") or {}
            dataset_changes = change_summary.get("dataset_changes", [])
            config_changes = change_summary.get("config_changes", [])
            prompt_changes = change_summary.get("prompt_changes", {})

            report_lines.append("## 변경 사항 요약")
            dataset_change_count = len(dataset_changes) if isinstance(dataset_changes, list) else 0
            config_change_count = len(config_changes) if isinstance(config_changes, list) else 0
            report_lines.extend(
                [
                    f"- 데이터셋 변경: {dataset_change_count}건",
                    f"- 설정 변경: {config_change_count}건",
                    f"- 프롬프트 변경 상태: {prompt_changes.get('status', 'unknown')}",
                    "",
                ]
            )

            report_lines.append("## 지표 비교 스코어카드")
            report_lines.extend(self._render_comparison_table(comparison_scorecard))
            report_lines.append("")
        else:
            report_lines.append("## 지표 스코어카드")
            report_lines.extend(self._render_scorecard_table(scorecard))
            report_lines.append("")

        if report_type != "summary":
            report_lines.append("## 데이터 품질/신뢰도")
            report_lines.extend(
                [
                    f"- 전체 케이스: {quality_summary.get('total_cases', '-')}",
                    f"- 평가 샘플: {quality_summary.get('sample_count', '-')}",
                    f"- 커버리지: {self._format_percent(quality_summary.get('coverage'))}",
                ]
            )
            for flag in quality_summary.get("flags", []):
                report_lines.append(f"- 주의: {flag}")
            report_lines.append("")

            report_lines.append("## 증거 샘플")
            if evidence:
                for idx, item in enumerate(evidence, start=1):
                    evidence_id = item.get("evidence_id") or f"E{idx}"
                    report_lines.append(
                        f"- [{evidence_id}] {item.get('test_case_id', 'unknown')}: "
                        f"avg {self._format_float(item.get('avg_score'))}"
                    )
            else:
                report_lines.append("- 증거 데이터가 없습니다. (추가 데이터 필요)")
            report_lines.append("")

        recommendations = []
        for item in context.get("recommendations") or []:
            if item:
                recommendations.append(item)
        for item in context.get("diagnostic_recommendations") or []:
            if item:
                recommendations.append(item)
        recommendations = list(dict.fromkeys(recommendations))

        report_lines.append("## 개선 제안")
        if recommendations:
            for rec in recommendations[:5]:
                report_lines.append(f"- {rec}")
        else:
            report_lines.append("- 추가 데이터 및 LLM 분석을 통해 상세 원인을 도출하세요.")

        report_lines.append("")
        report_lines.append("## 다음 단계")
        report_lines.append("- 우선순위 케이스를 대상으로 실험/재평가를 진행하세요.")

        report_lines.append("")
        report_lines.append("## 부록(산출물)")
        if artifact_manifest:
            for item in artifact_manifest:
                report_lines.append(f"- {item}")
        else:
            report_lines.append("- 산출물 정보가 없습니다.")

        return self._build_output(
            context,
            evidence,
            "\n".join(report_lines),
            llm_used=llm_used,
        )
