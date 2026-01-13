"""RAGAS evaluator module for pipeline."""

from __future__ import annotations

from typing import Any, cast

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import (
    average_scores,
    get_upstream_output,
    group_scores_by_metric,
    safe_mean,
    truncate_text,
)
from evalvault.adapters.outbound.llm import SettingsLLMFactory
from evalvault.adapters.outbound.nlp.korean.toolkit_factory import try_create_korean_toolkit
from evalvault.config.settings import Settings
from evalvault.domain.entities import Dataset, EvaluationRun, TestCase
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.ports.outbound.llm_port import LLMPort


class RagasEvaluatorModule(BaseAnalysisModule):
    """Summarize RAGAS-style metric scores from run data."""

    module_id = "ragas_evaluator"
    name = "RAGAS Evaluator"
    description = "Aggregate per-case RAGAS scores for downstream diagnostics."
    input_types = ["run", "metrics"]
    output_types = ["ragas_summary", "metrics"]
    requires = ["data_loader"]
    tags = ["analysis", "ragas"]

    def __init__(self, llm_adapter: LLMPort | None = None) -> None:
        self._llm_adapter = llm_adapter
        settings = Settings()
        llm_factory = SettingsLLMFactory(settings)
        korean_toolkit = try_create_korean_toolkit()
        self._evaluator = RagasEvaluator(korean_toolkit=korean_toolkit, llm_factory=llm_factory)

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")
        metrics = loader_output.get("metrics", {}) or {}

        per_case: list[dict[str, Any]] = []
        if isinstance(run, EvaluationRun):
            metrics = group_scores_by_metric(run)
            for result in run.results:
                metric_scores = {m.name: m.score for m in result.metrics}
                avg_score = safe_mean(metric_scores.values())
                per_case.append(
                    {
                        "test_case_id": result.test_case_id,
                        "metrics": metric_scores,
                        "avg_score": round(avg_score, 4),
                        "question_preview": truncate_text(result.question),
                    }
                )

        return self._build_output(metrics, per_case, recomputed=False)

    async def execute_async(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        context = inputs.get("__context__", {})
        additional = context.get("additional_params", {}) or {}
        recompute = params.get("recompute")
        if recompute is None:
            recompute = additional.get("recompute_ragas", False)
        if isinstance(recompute, str):
            recompute = recompute.strip().lower() in {"1", "true", "yes", "y", "on"}

        if not recompute:
            return self.execute(inputs, params)

        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")
        if not isinstance(run, EvaluationRun):
            output = self.execute(inputs, params)
            output["recomputed"] = False
            output["error"] = "Evaluation run not available for RAGAS recompute."
            return output

        if self._llm_adapter is None:
            output = self.execute(inputs, params)
            output["recomputed"] = False
            output["error"] = "LLM adapter is not configured for RAGAS recompute."
            return output

        dataset = self._build_dataset_from_run(run)
        metrics = params.get("metrics") or additional.get("ragas_metrics") or run.metrics_evaluated
        if isinstance(metrics, str):
            metrics = [item.strip() for item in metrics.split(",") if item.strip()]
        thresholds = run.thresholds or {}
        parallel = params.get("parallel")
        if parallel is None:
            parallel = additional.get("ragas_parallel", False)
        if isinstance(parallel, str):
            parallel = parallel.strip().lower() in {"1", "true", "yes", "y", "on"}
        batch_size = params.get("batch_size") or additional.get("ragas_batch_size") or 5

        try:
            recomputed_run = await self._evaluator.evaluate(
                dataset=dataset,
                metrics=list(metrics),
                llm=self._llm_adapter,
                thresholds=thresholds,
                parallel=bool(parallel),
                batch_size=int(batch_size),
            )
        except Exception as exc:
            output = self.execute(inputs, params)
            output["recomputed"] = False
            output["error"] = f"RAGAS recompute failed: {exc}"
            return output

        metrics_map = group_scores_by_metric(recomputed_run)
        per_case = []
        for result in recomputed_run.results:
            metric_scores = {m.name: m.score for m in result.metrics}
            avg_score = safe_mean(metric_scores.values())
            per_case.append(
                {
                    "test_case_id": result.test_case_id,
                    "metrics": metric_scores,
                    "avg_score": round(avg_score, 4),
                    "question_preview": truncate_text(result.question),
                }
            )

        output = self._build_output(metrics_map, per_case, recomputed=True)
        output["recomputed"] = True
        output["llm_model"] = self._llm_adapter.get_model_name()
        return output

    def _build_output(
        self,
        metrics: dict[str, list[float]] | dict[str, float],
        per_case: list[dict[str, Any]],
        *,
        recomputed: bool,
    ) -> dict[str, Any]:
        if metrics and all(isinstance(value, list) for value in metrics.values()):
            metrics_lists = cast(dict[str, list[float]], metrics)
            avg_scores = average_scores(metrics_lists)
            sample_count = max((len(values) for values in metrics_lists.values()), default=0)
        else:
            avg_scores = cast(dict[str, float], metrics)
            sample_count = len(per_case)

        overall = safe_mean(avg_scores.values()) if avg_scores else 0.0
        summary = {
            "metric_count": len(avg_scores),
            "sample_count": sample_count,
            "overall_score": round(overall, 4),
            "recomputed": recomputed,
        }

        return {
            "summary": summary,
            "metrics": avg_scores,
            "per_case": per_case,
        }

    def _build_dataset_from_run(self, run: EvaluationRun) -> Dataset:
        test_cases: list[TestCase] = []
        for result in run.results:
            question = result.question or ""
            answer = result.answer or ""
            contexts = result.contexts or []
            if not question and not answer:
                continue
            test_cases.append(
                TestCase(
                    id=result.test_case_id,
                    question=question,
                    answer=answer,
                    contexts=list(contexts),
                    ground_truth=result.ground_truth,
                )
            )

        return Dataset(
            name=run.dataset_name or "evaluation-run",
            version=run.dataset_version or "",
            test_cases=test_cases,
            thresholds=run.thresholds or {},
        )
