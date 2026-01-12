"""Helpers for analysis pipeline IO."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from evalvault.adapters.outbound.analysis.pipeline_helpers import to_serializable
from evalvault.domain.entities.analysis_pipeline import PipelineResult
from evalvault.domain.entities.result import EvaluationRun


def resolve_output_paths(
    *,
    base_dir: Path | None,
    output_path: Path | None,
    report_path: Path | None,
    prefix: str,
) -> tuple[Path, Path]:
    """Resolve output/report paths and ensure parent directories exist."""
    resolved_base = (base_dir or Path("reports/analysis")).expanduser()
    output_path = (output_path or resolved_base / f"{prefix}.json").expanduser()
    report_path = (report_path or resolved_base / f"{prefix}.md").expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path, report_path


def resolve_artifact_dir(
    *,
    base_dir: Path | None,
    output_path: Path,
    report_path: Path,
    prefix: str,
) -> Path:
    """Resolve artifact directory and ensure it exists."""
    if base_dir is not None:
        resolved_base = base_dir.expanduser()
    else:
        resolved_base = output_path.parent
        if resolved_base is None:
            resolved_base = report_path.parent
    artifact_dir = resolved_base / "artifacts" / prefix
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return artifact_dir


def _safe_artifact_name(name: str) -> str:
    """Return a filesystem-safe artifact name."""
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")
    return sanitized or "artifact"


def write_pipeline_artifacts(
    result: PipelineResult,
    *,
    artifacts_dir: Path,
) -> dict[str, Any]:
    """Write per-node pipeline artifacts and return index metadata."""
    nodes: list[dict[str, Any]] = []

    for node_id, node_res in result.node_results.items():
        status = getattr(node_res, "status", None)
        if hasattr(status, "value"):
            status = status.value

        artifact_name = _safe_artifact_name(node_id)
        artifact_path = artifacts_dir / f"{artifact_name}.json"
        node_payload = {
            "node_id": node_id,
            "status": status,
            "duration_ms": getattr(node_res, "duration_ms", None),
            "error": getattr(node_res, "error", None),
            "output": to_serializable(getattr(node_res, "output", None)),
        }
        write_json(artifact_path, node_payload)

        nodes.append(
            {
                "node_id": node_id,
                "status": status,
                "duration_ms": getattr(node_res, "duration_ms", None),
                "error": getattr(node_res, "error", None),
                "path": str(artifact_path),
            }
        )

    final_output_path = None
    if result.final_output is not None:
        final_output_path = artifacts_dir / "final_output.json"
        write_json(final_output_path, {"output": to_serializable(result.final_output)})

    index_payload = {
        "pipeline_id": result.pipeline_id,
        "intent": result.intent.value if result.intent else None,
        "duration_ms": result.total_duration_ms,
        "started_at": result.started_at.isoformat() if result.started_at else None,
        "finished_at": result.finished_at.isoformat() if result.finished_at else None,
        "nodes": nodes,
        "final_output_path": str(final_output_path) if final_output_path else None,
    }
    index_path = artifacts_dir / "index.json"
    write_json(index_path, index_payload)

    return {
        "dir": str(artifacts_dir),
        "index": str(index_path),
    }


def serialize_pipeline_result(result: PipelineResult) -> dict[str, Any]:
    """Serialize PipelineResult into JSON-ready payload."""
    node_results = {}
    for node_id, node_res in result.node_results.items():
        status = getattr(node_res, "status", None)
        if hasattr(status, "value"):
            status = status.value
        node_results[node_id] = {
            "status": status,
            "error": getattr(node_res, "error", None),
            "duration_ms": getattr(node_res, "duration_ms", None),
            "output": to_serializable(getattr(node_res, "output", None)),
        }

    return {
        "intent": result.intent.value if result.intent else None,
        "pipeline_id": result.pipeline_id,
        "is_complete": result.is_complete,
        "duration_ms": result.total_duration_ms,
        "started_at": result.started_at.isoformat() if result.started_at else None,
        "finished_at": result.finished_at.isoformat() if result.finished_at else None,
        "final_output": to_serializable(result.final_output),
        "node_results": node_results,
    }


def extract_markdown_report(final_output: Any) -> str | None:
    """Extract markdown report text from pipeline output."""
    if isinstance(final_output, dict):
        if "report" in final_output and isinstance(final_output["report"], str):
            return final_output["report"]
        for value in final_output.values():
            if isinstance(value, dict):
                report = value.get("report")
                if isinstance(report, str):
                    return report
    return None


def get_node_output(result: PipelineResult, node_id: str) -> dict[str, Any]:
    """Return a dict output for a pipeline node."""
    node = result.get_node_result(node_id)
    if not node or not isinstance(node.output, dict):
        return {}
    return node.output


def build_metric_scorecard(
    run: EvaluationRun | None,
    stats_output: dict[str, Any],
    ragas_output: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build per-metric scorecard rows for CLI summaries."""
    stats_detail = stats_output.get("statistics", {}) if isinstance(stats_output, dict) else {}
    pass_rates = stats_output.get("metric_pass_rates", {}) if isinstance(stats_output, dict) else {}
    ragas_metrics = ragas_output.get("metrics", {}) if isinstance(ragas_output, dict) else {}

    metrics = set()
    if isinstance(stats_detail, dict):
        metrics.update(stats_detail.keys())
    if isinstance(pass_rates, dict):
        metrics.update(pass_rates.keys())
    if isinstance(ragas_metrics, dict):
        metrics.update(ragas_metrics.keys())
    if isinstance(run, EvaluationRun):
        metrics.update(run.metrics_evaluated)

    scorecard = []
    for metric in sorted(metrics):
        stats = stats_detail.get(metric, {}) if isinstance(stats_detail, dict) else {}
        mean = stats.get("mean")
        if mean is None and isinstance(ragas_metrics, dict):
            mean = ragas_metrics.get(metric)
        threshold = _resolve_threshold(run, metric)
        pass_rate = pass_rates.get(metric) if isinstance(pass_rates, dict) else None
        status = "unknown"
        if isinstance(mean, int | float):
            status = "pass" if float(mean) >= threshold else "risk"
        elif isinstance(pass_rate, int | float):
            status = "pass" if float(pass_rate) >= 0.7 else "risk"
        scorecard.append(
            {
                "metric": metric,
                "mean": mean,
                "threshold": threshold,
                "pass_rate": pass_rate,
                "status": status,
            }
        )
    return scorecard


def build_comparison_scorecard(comparison_output: dict[str, Any]) -> list[dict[str, Any]]:
    """Build comparison scorecard rows for CLI summaries."""
    comparisons = (
        comparison_output.get("comparisons", []) if isinstance(comparison_output, dict) else []
    )
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
                "direction": item.get("direction"),
            }
        )
    return scorecard


def build_quality_summary(
    run: EvaluationRun | None,
    ragas_output: dict[str, Any],
    time_series_output: dict[str, Any],
    change_summary: dict[str, Any],
) -> dict[str, Any]:
    """Summarize data quality flags for CLI display."""
    ragas_summary = ragas_output.get("summary", {}) if isinstance(ragas_output, dict) else {}
    time_series_summary = (
        time_series_output.get("summary", {}) if isinstance(time_series_output, dict) else {}
    )
    total_cases = run.total_test_cases if isinstance(run, EvaluationRun) else None
    sample_count = ragas_summary.get("sample_count")
    coverage = None
    if isinstance(sample_count, int) and isinstance(total_cases, int) and total_cases > 0:
        coverage = sample_count / total_cases

    flags = []
    if isinstance(total_cases, int) and total_cases < 30:
        flags.append("표본 수가 적음")
    if coverage is not None and coverage < 1.0:
        flags.append("평가 샘플이 전체보다 적음")
    if change_summary.get("summary", {}).get("dataset_changed"):
        flags.append("데이터셋 변경 존재")
    if time_series_summary.get("run_count", 0) < 3:
        flags.append("추세 분석을 위한 실행 이력 부족")

    return {
        "total_cases": total_cases,
        "sample_count": sample_count,
        "coverage": coverage,
        "flags": flags,
    }


def build_priority_highlights(priority_summary: dict[str, Any]) -> dict[str, Any]:
    """Extract top priority cases for CLI display."""
    if not isinstance(priority_summary, dict):
        return {"bottom_cases": [], "impact_cases": []}

    return {
        "bottom_cases": _trim_priority_cases(priority_summary.get("bottom_cases", [])),
        "impact_cases": _trim_priority_cases(priority_summary.get("impact_cases", [])),
    }


def _trim_priority_cases(cases: Any) -> list[dict[str, Any]]:
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
                "question_preview": item.get("question_preview"),
                "tags": item.get("tags"),
            }
        )
    return trimmed


def _resolve_threshold(run: EvaluationRun | None, metric: str) -> float:
    if isinstance(run, EvaluationRun):
        return float(run._get_threshold(metric))
    return 0.7


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON payload to disk."""
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def append_artifact_links(
    report_text: str,
    artifact_index: dict[str, Any],
    report_path: Path,
) -> str:
    """Ensure report contains linked artifact appendix."""
    link_section = _build_artifact_link_section(artifact_index, report_path)
    if not link_section:
        return report_text

    appendix_pattern = re.compile(
        r"^##\s*\d*\.?\s*부록.*?(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    cleaned = appendix_pattern.sub("", report_text).rstrip()
    if not cleaned:
        return link_section + "\n"
    return cleaned + "\n\n" + link_section + "\n"


def _build_artifact_link_section(
    artifact_index: dict[str, Any],
    report_path: Path,
) -> str:
    index_path_value = artifact_index.get("index")
    if not index_path_value:
        return ""
    index_path = Path(index_path_value)
    if not index_path.exists():
        return ""

    try:
        with index_path.open("r", encoding="utf-8") as handle:
            index_payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return ""

    artifact_paths: list[Path] = []
    for node in index_payload.get("nodes", []):
        if isinstance(node, dict) and node.get("path"):
            artifact_paths.append(Path(node["path"]))
    final_output_path = index_payload.get("final_output_path")
    if final_output_path:
        artifact_paths.append(Path(final_output_path))
    artifact_paths.append(index_path)

    seen = set()
    lines = ["## 부록(산출물 링크)", ""]
    for artifact_path in artifact_paths:
        artifact_key = str(artifact_path)
        if artifact_key in seen:
            continue
        seen.add(artifact_key)
        link = _relative_link(artifact_path, report_path.parent)
        lines.append(f"- [{artifact_path.name}]({link})")

    if len(lines) <= 2:
        return ""
    return "\n".join(lines)


def _relative_link(target: Path, base_dir: Path) -> str:
    try:
        return os.path.relpath(target, start=base_dir).replace("\\", "/")
    except ValueError:
        return str(target)
