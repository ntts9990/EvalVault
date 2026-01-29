from __future__ import annotations

from typing import Any

from evalvault.config.langfuse_support import get_langfuse_trace_url
from evalvault.config.phoenix_support import get_phoenix_trace_url
from evalvault.domain.entities.ops_report import OpsReport
from evalvault.domain.entities.stage import StageEvent, StageMetric, StageSummary
from evalvault.domain.services.stage_metric_guide_service import StageMetricGuideService
from evalvault.domain.services.stage_metric_service import StageMetricService
from evalvault.domain.services.stage_summary_service import StageSummaryService
from evalvault.ports.outbound.stage_storage_port import StageStoragePort
from evalvault.ports.outbound.storage_port import StoragePort


class OpsReportService:
    """Build an operational report for an evaluation run."""

    def __init__(
        self,
        *,
        metric_service: StageMetricService | None = None,
        summary_service: StageSummaryService | None = None,
        guide_service: StageMetricGuideService | None = None,
    ) -> None:
        self._metric_service = metric_service or StageMetricService()
        self._summary_service = summary_service or StageSummaryService()
        self._guide_service = guide_service or StageMetricGuideService()

    def build_report(
        self,
        run_id: str,
        *,
        storage: StoragePort,
        stage_storage: StageStoragePort,
    ) -> OpsReport:
        run = storage.get_run(run_id)
        run_summary = run.to_summary_dict()
        phoenix_trace_url = get_phoenix_trace_url(run.tracker_metadata)
        langfuse_trace_url = get_langfuse_trace_url(run.tracker_metadata)

        events = stage_storage.list_stage_events(run_id)
        stage_summary = self._summarize_events(events)

        stage_metrics = stage_storage.list_stage_metrics(run_id)
        if not stage_metrics and events:
            stage_metrics = self._metric_service.build_metrics(events)

        bottlenecks = self._build_bottlenecks(stage_summary)
        recommendations = self._build_recommendations(stage_metrics)

        ops_kpis = self._build_ops_kpis(run, events)

        metadata = {
            "phoenix_trace_url": phoenix_trace_url,
            "langfuse_trace_url": langfuse_trace_url,
        }

        return OpsReport(
            run_summary=run_summary,
            ops_kpis=ops_kpis,
            stage_summary=stage_summary,
            stage_metrics=stage_metrics,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            metadata=metadata,
        )

    def _summarize_events(self, events: list[StageEvent]) -> StageSummary | None:
        if not events:
            return None
        return self._summary_service.summarize(events)

    def _build_bottlenecks(self, summary: StageSummary | None) -> list[dict[str, Any]]:
        if summary is None:
            return []
        bottlenecks: list[dict[str, Any]] = []

        for stage_type in summary.missing_required_stage_types:
            bottlenecks.append(
                {
                    "type": "missing_stage",
                    "stage_type": stage_type,
                    "detail": "required stage missing",
                }
            )

        durations = summary.stage_type_avg_durations
        if durations:
            top = sorted(durations.items(), key=lambda item: item[1], reverse=True)[:3]
            for stage_type, duration in top:
                bottlenecks.append(
                    {
                        "type": "latency",
                        "stage_type": stage_type,
                        "avg_duration_ms": round(duration, 3),
                    }
                )
        return bottlenecks

    def _build_recommendations(self, metrics: list[StageMetric]) -> list[str]:
        if not metrics:
            return []
        guides = self._guide_service.build_guides(metrics)
        recommendations: list[str] = []
        for guide in guides:
            top_action = guide.top_action
            if top_action is None:
                continue
            hint = top_action.implementation_hint or top_action.description
            label = f"[{guide.priority.value}] {guide.component.value}"
            if hint:
                recommendations.append(f"{label}: {top_action.title} - {hint}")
            else:
                recommendations.append(f"{label}: {top_action.title}")
        return recommendations

    def _build_ops_kpis(self, run, events: list[StageEvent]) -> dict[str, Any]:
        total_cases = run.total_test_cases
        latencies = [r.latency_ms for r in run.results if r.latency_ms]
        tokens_used = [r.tokens_used for r in run.results if r.tokens_used]
        costs = [r.cost_usd for r in run.results if r.cost_usd is not None]

        avg_latency = _average(latencies)
        p95_latency = _percentile(latencies, 0.95)
        avg_tokens = _average(tokens_used)
        avg_cost = _average(costs)
        pass_rate = run.pass_rate
        failure_rate = None if pass_rate is None else max(0.0, 1.0 - pass_rate)

        error_rate = _stage_error_rate(events)
        error_severity = _stage_error_severity(error_rate)

        return {
            "total_test_cases": total_cases,
            "pass_rate": pass_rate,
            "failure_rate": failure_rate,
            "stage_error_rate": error_rate,
            "stage_error_severity": error_severity,
            "duration_seconds": run.duration_seconds,
            "total_tokens": run.total_tokens,
            "total_cost_usd": run.total_cost_usd,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "avg_tokens_per_case": avg_tokens,
            "avg_cost_per_case_usd": avg_cost,
        }


def _average(values: list[float | int]) -> float | None:
    if not values:
        return None
    return float(sum(values)) / len(values)


def _percentile(values: list[float | int], ratio: float) -> float | None:
    if not values:
        return None
    if ratio <= 0:
        return float(min(values))
    if ratio >= 1:
        return float(max(values))
    sorted_values = sorted(values)
    index = int(round((len(sorted_values) - 1) * ratio))
    return float(sorted_values[index])


def _stage_error_rate(events: list[StageEvent]) -> float | None:
    if not events:
        return None
    total = len(events)
    failure_statuses = {"failed", "error", "timeout", "aborted"}
    success_statuses = {"success", "ok", "completed", "pass"}
    failures = 0
    for event in events:
        status = str(event.status or "").strip().lower()
        if status in failure_statuses:
            failures += 1
            continue
        if status and status not in success_statuses:
            failures += 1
    return failures / total


def _stage_error_severity(rate: float | None) -> str | None:
    if rate is None:
        return None
    if rate >= 0.05:
        return "critical"
    if rate >= 0.02:
        return "warning"
    return "ok"
