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
        if not isinstance(run, EvaluationRun):
            runs_output = get_upstream_output(inputs, "load_runs", "run_loader") or {}
            if isinstance(runs_output, dict):
                runs = runs_output.get("runs", [])
                if runs:
                    run = runs[0]

        stats_output = get_upstream_output(inputs, "statistics", "statistical_analyzer") or {}
        ragas_output = get_upstream_output(inputs, "ragas_eval", "ragas_evaluator") or {}
        root_cause = get_upstream_output(inputs, "root_cause", "root_cause_analyzer") or {}
        pattern = get_upstream_output(inputs, "pattern_detection", "pattern_detector") or {}
        trend = get_upstream_output(inputs, "trend_detection", "trend_detector") or {}
        comparison = get_upstream_output(inputs, "run_comparison", "run_comparator") or {}
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
            "report_type": report_type or "analysis",
            "stats_summary": stats_output.get("summary") if isinstance(stats_output, dict) else {},
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
            "root_causes": root_cause.get("causes") if isinstance(root_cause, dict) else [],
            "recommendations": (
                root_cause.get("recommendations") if isinstance(root_cause, dict) else []
            ),
            "patterns": pattern.get("patterns") if isinstance(pattern, dict) else [],
            "trends": trend.get("trends") if isinstance(trend, dict) else [],
            "comparison": comparison if isinstance(comparison, dict) else {},
            "quality_checks": (
                quality_check.get("checks") if isinstance(quality_check, dict) else []
            ),
        }

    def _build_evidence(
        self,
        run: EvaluationRun | None,
        max_cases: int = 6,
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
            item["evidence_id"] = f"E{idx}"
        return trimmed

    def _build_prompt(self, context: dict[str, Any], evidence: list[dict[str, Any]]) -> str:
        run = context.get("run")
        run_summary = self._build_run_summary(run)
        summary_payload = {
            "report_type": context.get("report_type"),
            "query": context.get("query"),
            "run_summary": run_summary,
            "stats_summary": context.get("stats_summary"),
            "metric_pass_rates": context.get("metric_pass_rates"),
            "ragas_summary": context.get("ragas_summary"),
            "ragas_metrics": context.get("ragas_metrics"),
            "root_causes": context.get("root_causes"),
            "recommendations": context.get("recommendations"),
            "patterns": context.get("patterns"),
            "trends": context.get("trends"),
            "comparison": context.get("comparison"),
            "quality_checks": context.get("quality_checks"),
        }

        summary_json = json.dumps(summary_payload, ensure_ascii=False, indent=2)
        evidence_json = json.dumps(evidence, ensure_ascii=False, indent=2)

        return (
            "당신은 RAG 평가 분석 보고서 작성자입니다. "
            "아래 데이터와 증거를 기반으로 Markdown 보고서를 작성하세요.\n"
            "\n"
            "요구사항:\n"
            "1) 출력 언어: 한국어\n"
            "2) 핵심 주장/원인/개선안에는 evidence_id를 [E1] 형식으로 인용\n"
            "3) 섹션: 요약, 문제 진단, 증거 기반 분석, 개선 제안, 다음 단계\n"
            "4) 증거가 부족하면 '추가 데이터 필요'라고 명시\n"
            "\n"
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
        return {
            "run_id": run.run_id,
            "dataset_name": run.dataset_name,
            "dataset_version": run.dataset_version,
            "model_name": run.model_name,
            "total_test_cases": run.total_test_cases,
            "pass_rate": round(run.pass_rate, 4),
            "metrics": metric_avgs,
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
        run_summary = self._build_run_summary(context.get("run"))
        report_lines = [
            "# 분석 보고서",
            "",
            "## 요약",
        ]

        if run_summary:
            report_lines.extend(
                [
                    f"- 데이터셋: {run_summary.get('dataset_name', '-')}",
                    f"- 모델: {run_summary.get('model_name', '-')}",
                    f"- 테스트 케이스: {run_summary.get('total_test_cases', 0)}",
                    f"- 통과율: {run_summary.get('pass_rate', 0):.2%}",
                    "",
                ]
            )

        report_lines.append("## 증거 샘플")
        if evidence:
            for idx, item in enumerate(evidence, start=1):
                evidence_id = item.get("evidence_id") or f"E{idx}"
                report_lines.append(
                    f"- [{evidence_id}] {item.get('test_case_id', 'unknown')}: "
                    f"avg {item.get('avg_score', 0):.2f}"
                )
        else:
            report_lines.append("- 증거 데이터가 없습니다.")

        report_lines.extend(
            [
                "",
                "## 개선 제안",
                "- 추가 데이터 및 LLM 분석을 통해 상세 원인을 도출하세요.",
            ]
        )

        return self._build_output(
            context,
            evidence,
            "\n".join(report_lines),
            llm_used=llm_used,
        )
