from unittest.mock import MagicMock

from evalvault.domain.entities.analysis import ComparisonResult
from evalvault.domain.entities.analysis_pipeline import AnalysisIntent, PipelineResult
from evalvault.domain.services.run_comparison_service import (
    RunComparisonRequest,
    RunComparisonService,
)


def _build_run(run_id: str):
    run = MagicMock()
    run.run_id = run_id
    run.metrics_evaluated = ["faithfulness"]
    return run


def test_run_comparison_success() -> None:
    storage = MagicMock()
    run_a = _build_run("run-1")
    run_b = _build_run("run-2")
    storage.get_run.side_effect = [run_a, run_b]

    analysis = MagicMock()
    analysis.compare_runs.return_value = [
        ComparisonResult.from_values(
            run_id_a="run-1",
            run_id_b="run-2",
            metric="faithfulness",
            mean_a=0.7,
            mean_b=0.8,
            p_value=0.02,
            effect_size=0.4,
        )
    ]

    pipeline_result = PipelineResult(
        pipeline_id="pipe-1",
        intent=AnalysisIntent.GENERATE_COMPARISON,
    )
    pipeline_result.mark_complete(final_output={"report": "# 비교 보고서"}, total_duration_ms=100)

    pipeline = MagicMock()
    pipeline.run_comparison.return_value = pipeline_result

    service = RunComparisonService(storage=storage, analysis_port=analysis, pipeline_port=pipeline)
    request = RunComparisonRequest(run_id_a="run-1", run_id_b="run-2")

    outcome = service.compare_runs(request)

    assert outcome.status == "ok"
    assert outcome.report_text.startswith("# 비교 보고서")
    assert outcome.duration_ms >= 0


def test_run_comparison_degraded_on_pipeline_error() -> None:
    storage = MagicMock()
    run_a = _build_run("run-1")
    run_b = _build_run("run-2")
    storage.get_run.side_effect = [run_a, run_b]

    analysis = MagicMock()
    analysis.compare_runs.return_value = [
        ComparisonResult.from_values(
            run_id_a="run-1",
            run_id_b="run-2",
            metric="faithfulness",
            mean_a=0.7,
            mean_b=0.8,
            p_value=0.02,
            effect_size=0.4,
        )
    ]

    pipeline = MagicMock()
    pipeline.run_comparison.side_effect = RuntimeError("pipeline failed")

    service = RunComparisonService(storage=storage, analysis_port=analysis, pipeline_port=pipeline)
    request = RunComparisonRequest(run_id_a="run-1", run_id_b="run-2")

    outcome = service.compare_runs(request)

    assert outcome.status == "degraded"
    assert "pipeline_error" in outcome.degraded_reasons
    assert outcome.finished_at >= outcome.started_at
    assert isinstance(outcome.duration_ms, int)
