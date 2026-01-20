"""Build quadrant/3D visualization coordinates for evaluation runs."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from statistics import mean
from typing import Any, Literal

from evalvault.config.phoenix_support import PhoenixExperimentResolver
from evalvault.domain.entities import EvaluationRun, TestCaseResult
from evalvault.domain.entities.stage import StageEvent, StageMetric
from evalvault.domain.services.prompt_status import extract_prompt_entries, summarize_prompt_counts
from evalvault.domain.services.stage_metric_service import (
    DEFAULT_STAGE_THRESHOLDS,
    StageMetricService,
)
from evalvault.ports.outbound.domain_memory_port import MemoryInsightPort
from evalvault.ports.outbound.stage_storage_port import StageStoragePort
from evalvault.ports.outbound.storage_port import StoragePort

Granularity = Literal["run", "cluster", "case"]

DEFAULT_METRIC_THRESHOLD = 0.7
DEFAULT_RERANK_NDCG_THRESHOLD = 0.2
RESULT_COUNT_RATIO_THRESHOLD = 0.5
PHOENIX_DRIFT_TARGET = 0.18
VARIANCE_TARGET = 0.10
REGRESSION_RATE_TARGET = 0.05
PROMPT_RISK_TARGET = 0.10


@dataclass(frozen=True)
class VisualSpaceQuery:
    run_id: str
    granularity: Granularity = "run"
    base_run_id: str | None = None
    auto_base: bool = True
    include: set[str] | None = None
    limit: int | None = None
    offset: int | None = None
    cluster_map: dict[str, str] | None = None


class VisualSpaceService:
    """Compute visualization coordinates for runs/cases/clusters."""

    def __init__(
        self,
        *,
        storage: StoragePort,
        stage_storage: StageStoragePort | None = None,
        phoenix_resolver: PhoenixExperimentResolver | None = None,
        memory_port: MemoryInsightPort | None = None,
    ) -> None:
        self._storage = storage
        self._stage_storage = stage_storage
        self._phoenix = phoenix_resolver
        self._memory_port = memory_port
        self._stage_metric_service = StageMetricService()

    def build(self, query: VisualSpaceQuery) -> dict[str, Any]:
        run = self._storage.get_run(query.run_id)
        stage_events = self._list_stage_events(query.run_id)
        stage_metrics = self._list_stage_metrics(query.run_id, stage_events)
        stage_metric_map = _aggregate_stage_metrics(stage_metrics)

        base_run, base_meta = self._resolve_base_run(run, query)
        regression_rate, case_deltas = _compute_regression_rate(base_run, run)

        run_coords = _build_run_coords(
            run=run,
            stage_metric_map=stage_metric_map,
            stage_events=stage_events,
            phoenix_resolver=self._phoenix,
            memory_port=self._memory_port,
            regression_rate=regression_rate,
        )

        points: list[dict[str, Any]] = []
        warnings: list[str] = []

        if query.granularity == "run":
            points = [_build_run_point(run, run_coords, regression_rate)]
        elif query.granularity == "case":
            points = _build_case_points(
                run=run,
                run_coords=run_coords,
                base_run=base_run,
                case_deltas=case_deltas,
            )
        else:
            points, warning = _build_cluster_points(
                run,
                base_run,
                case_deltas,
                run_coords,
                query.cluster_map,
            )
            if warning:
                warnings.append(warning)

        points = _apply_paging(points, query.limit, query.offset)

        response: dict[str, Any] = {
            "run_id": query.run_id,
            "granularity": query.granularity,
            "axis": {
                "x": "evidence_sufficiency",
                "y": "answer_integrity",
                "z": "robustness",
                "normalization": "centered_norm + inv_norm",
                "targets": {
                    "phoenix_drift": PHOENIX_DRIFT_TARGET,
                    "variance": VARIANCE_TARGET,
                    "regression_rate": REGRESSION_RATE_TARGET,
                    "prompt_risk": PROMPT_RISK_TARGET,
                },
            },
            "points": points,
            "warnings": warnings,
        }

        if base_meta:
            response["base"] = base_meta

        summary = _summarize_points(points, case_deltas)
        if summary:
            response["summary"] = summary

        if query.include:
            if "summary" not in query.include:
                response.pop("summary", None)
            if "encoding" not in query.include:
                for point in response["points"]:
                    point.pop("encoding", None)
            if "breakdown" not in query.include:
                for point in response["points"]:
                    point.pop("breakdown", None)

        return response

    def _resolve_base_run(
        self,
        run: EvaluationRun,
        query: VisualSpaceQuery,
    ) -> tuple[EvaluationRun | None, dict[str, Any] | None]:
        if query.base_run_id:
            base_run = self._storage.get_run(query.base_run_id)
            return base_run, {"run_id": base_run.run_id, "auto_selected": False, "criteria": {}}

        if not query.auto_base:
            return None, None

        base_run = _auto_select_base_run(self._storage, run)
        if not base_run:
            return None, None

        criteria = _base_match_criteria(run)
        return base_run, {
            "run_id": base_run.run_id,
            "auto_selected": True,
            "criteria": criteria,
        }

    def _list_stage_events(self, run_id: str) -> list[StageEvent]:
        if not self._stage_storage or not hasattr(self._stage_storage, "list_stage_events"):
            return []
        return self._stage_storage.list_stage_events(run_id)

    def _list_stage_metrics(
        self,
        run_id: str,
        stage_events: Iterable[StageEvent],
    ) -> list[StageMetric]:
        if not self._stage_storage or not hasattr(self._stage_storage, "list_stage_metrics"):
            return []
        metrics = self._stage_storage.list_stage_metrics(run_id)
        if metrics:
            return metrics
        if stage_events:
            metrics = self._stage_metric_service.build_metrics(stage_events)
            if hasattr(self._stage_storage, "save_stage_metrics"):
                self._stage_storage.save_stage_metrics(metrics)
        return metrics


def _centered_norm(value: float | None, threshold: float | None) -> float | None:
    if value is None:
        return None
    resolved = DEFAULT_METRIC_THRESHOLD if threshold is None else threshold
    if resolved <= 0:
        return None
    if value >= resolved:
        denom = 1 - resolved
        if denom <= 0:
            return 0.0
        return (value - resolved) / denom
    return (value - resolved) / resolved


def _inv_norm(value: float | None, target: float) -> float | None:
    if value is None:
        return None
    if target <= 0:
        return None
    score = 1 - (value / target)
    if score > 1:
        return 1.0
    if score < -1:
        return -1.0
    return score


def _weighted_average(values: list[tuple[float | None, float]]) -> float | None:
    total = 0.0
    weight_sum = 0.0
    for value, weight in values:
        if value is None:
            continue
        total += value * weight
        weight_sum += weight
    if weight_sum == 0:
        return None
    return total / weight_sum


def _aggregate_stage_metrics(metrics: Iterable[StageMetric]) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[StageMetric]] = defaultdict(list)
    for metric in metrics:
        buckets[metric.metric_name].append(metric)

    aggregated: dict[str, dict[str, float]] = {}
    for name, entries in buckets.items():
        scores = [m.score for m in entries if m.score is not None]
        threshold = next(
            (m.threshold for m in entries if m.threshold is not None),
            DEFAULT_STAGE_THRESHOLDS.get(name),
        )
        aggregated[name] = {
            "avg": mean(scores) if scores else 0.0,
            "threshold": threshold if threshold is not None else DEFAULT_METRIC_THRESHOLD,
        }
    return aggregated


def _base_match_criteria(run: EvaluationRun) -> dict[str, Any]:
    metadata = run.tracker_metadata or {}
    criteria = {
        "dataset_name": run.dataset_name,
        "metrics_evaluated": list(run.metrics_evaluated),
        "threshold_profile": metadata.get("threshold_profile"),
        "evaluation_task": metadata.get("evaluation_task"),
        "project_name": metadata.get("project") or metadata.get("project_name"),
        "run_mode": metadata.get("run_mode"),
    }
    return {k: v for k, v in criteria.items() if v}


def _auto_select_base_run(storage: StoragePort, run: EvaluationRun) -> EvaluationRun | None:
    criteria = _base_match_criteria(run)
    candidates = storage.list_runs(limit=200)
    filtered = []
    for candidate in candidates:
        if candidate.run_id == run.run_id:
            continue
        if candidate.dataset_name != criteria.get("dataset_name"):
            continue
        if sorted(candidate.metrics_evaluated) != sorted(criteria.get("metrics_evaluated", [])):
            continue
        meta = candidate.tracker_metadata or {}
        if criteria.get("threshold_profile") and meta.get("threshold_profile") != criteria.get(
            "threshold_profile"
        ):
            continue
        if criteria.get("evaluation_task") and meta.get("evaluation_task") != criteria.get(
            "evaluation_task"
        ):
            continue
        if criteria.get("project_name") and (
            meta.get("project") or meta.get("project_name")
        ) != criteria.get("project_name"):
            continue
        if criteria.get("run_mode") and meta.get("run_mode") != criteria.get("run_mode"):
            continue
        filtered.append(candidate)

    if filtered:
        return max(filtered, key=lambda item: item.started_at)

    relaxed = []
    for candidate in candidates:
        if candidate.run_id == run.run_id:
            continue
        if candidate.dataset_name != criteria.get("dataset_name"):
            continue
        if sorted(candidate.metrics_evaluated) != sorted(criteria.get("metrics_evaluated", [])):
            continue
        meta = candidate.tracker_metadata or {}
        if criteria.get("threshold_profile") and meta.get("threshold_profile") != criteria.get(
            "threshold_profile"
        ):
            continue
        if criteria.get("evaluation_task") and meta.get("evaluation_task") != criteria.get(
            "evaluation_task"
        ):
            continue
        if criteria.get("project_name") and (
            meta.get("project") or meta.get("project_name")
        ) != criteria.get("project_name"):
            continue
        relaxed.append(candidate)

    if relaxed:
        return max(relaxed, key=lambda item: item.started_at)
    return None


def _compute_regression_rate(
    base_run: EvaluationRun | None,
    target_run: EvaluationRun,
) -> tuple[float | None, dict[str, str]]:
    if base_run is None:
        return None, {}

    base_map = {result.test_case_id: result for result in base_run.results}
    target_map = {result.test_case_id: result for result in target_run.results}
    case_ids = set(base_map) | set(target_map)
    if not case_ids:
        return None, {}

    regressions = 0
    improvements = 0
    same_pass = 0
    same_fail = 0
    case_deltas: dict[str, str] = {}

    for case_id in case_ids:
        base_case = base_map.get(case_id)
        target_case = target_map.get(case_id)
        if base_case is None or target_case is None:
            continue
        base_passed = base_case.all_passed
        target_passed = target_case.all_passed
        if base_passed and target_passed:
            same_pass += 1
            case_deltas[case_id] = "same_pass"
        elif not base_passed and not target_passed:
            same_fail += 1
            case_deltas[case_id] = "same_fail"
        elif base_passed and not target_passed:
            regressions += 1
            case_deltas[case_id] = "regression"
        else:
            improvements += 1
            case_deltas[case_id] = "improvement"

    total = regressions + improvements + same_pass + same_fail
    if total == 0:
        return None, case_deltas
    return regressions / total, case_deltas


def _build_run_coords(
    *,
    run: EvaluationRun,
    stage_metric_map: dict[str, dict[str, float]],
    stage_events: list[StageEvent],
    phoenix_resolver: PhoenixExperimentResolver | None,
    memory_port: MemoryInsightPort | None,
    regression_rate: float | None,
) -> dict[str, Any]:
    x_value = _compute_x_axis(run, stage_metric_map, stage_events)
    y_value = _compute_y_axis(run, stage_metric_map)
    phoenix_drift = _resolve_phoenix_drift(run, phoenix_resolver)
    variance = _compute_variance(run)
    reliability = _resolve_reliability(run, memory_port)
    prompt_risk = _compute_prompt_risk(run, stage_metric_map)

    z_value = _weighted_average(
        [
            (_inv_norm(phoenix_drift, PHOENIX_DRIFT_TARGET), 0.40),
            (_inv_norm(regression_rate, REGRESSION_RATE_TARGET), 0.25),
            (_inv_norm(variance, VARIANCE_TARGET), 0.20),
            (reliability, 0.10),
            (_inv_norm(prompt_risk, PROMPT_RISK_TARGET), 0.05),
        ]
    )

    return {
        "x": x_value,
        "y": y_value,
        "z": z_value,
        "breakdown": {
            "phoenix_drift": phoenix_drift,
            "regression_rate": regression_rate,
            "variance": variance,
            "reliability": reliability,
            "prompt_risk": prompt_risk,
        },
    }


def _compute_x_axis(
    run: EvaluationRun,
    stage_metric_map: dict[str, dict[str, float]],
    stage_events: list[StageEvent],
) -> float | None:
    context_precision = _resolve_run_metric(run, "context_precision")
    context_precision_t = _resolve_run_threshold(run, "context_precision")
    context_recall = _resolve_run_metric(run, "context_recall")
    context_recall_t = _resolve_run_threshold(run, "context_recall")

    retrieval_precision = _resolve_stage_metric(stage_metric_map, "retrieval.precision_at_k")
    retrieval_precision_t = _resolve_stage_threshold(stage_metric_map, "retrieval.precision_at_k")
    retrieval_recall = _resolve_stage_metric(stage_metric_map, "retrieval.recall_at_k")
    retrieval_recall_t = _resolve_stage_threshold(stage_metric_map, "retrieval.recall_at_k")

    rerank_ndcg = _resolve_stage_metric(stage_metric_map, "rerank.ndcg_at_k")
    rerank_ndcg_t = _resolve_stage_threshold(
        stage_metric_map, "rerank.ndcg_at_k", DEFAULT_RERANK_NDCG_THRESHOLD
    )

    score_gap = _resolve_stage_metric(stage_metric_map, "retrieval.score_gap")
    score_gap_target = _resolve_stage_threshold(
        stage_metric_map, "retrieval.score_gap", DEFAULT_STAGE_THRESHOLDS.get("retrieval.score_gap")
    )

    result_count_norm = _resolve_result_count_norm(stage_events)

    precision_like = _weighted_average(
        [
            (_centered_norm(context_precision, context_precision_t), 0.45),
            (_centered_norm(retrieval_precision, retrieval_precision_t), 0.25),
            (_centered_norm(rerank_ndcg, rerank_ndcg_t), 0.20),
            (_inv_norm(score_gap, score_gap_target or 0.1), 0.10),
        ]
    )

    recall_like = _weighted_average(
        [
            (_centered_norm(context_recall, context_recall_t), 0.55),
            (_centered_norm(retrieval_recall, retrieval_recall_t), 0.30),
            (
                _centered_norm(result_count_norm, RESULT_COUNT_RATIO_THRESHOLD),
                0.15,
            ),
        ]
    )

    return _weighted_average([(precision_like, 0.5), (recall_like, 0.5)])


def _compute_y_axis(
    run: EvaluationRun,
    stage_metric_map: dict[str, dict[str, float]],
) -> float | None:
    faithfulness = _resolve_run_metric(run, "faithfulness")
    faithfulness_t = _resolve_run_threshold(run, "faithfulness")
    factual_correctness = _resolve_run_metric(run, "factual_correctness")
    factual_correctness_t = _resolve_run_threshold(run, "factual_correctness")

    grounding_ratio = _resolve_stage_metric(stage_metric_map, "grounding.grounded_ratio")
    grounding_ratio_t = _resolve_stage_threshold(stage_metric_map, "grounding.grounded_ratio")

    answer_relevancy = _resolve_run_metric(run, "answer_relevancy")
    answer_relevancy_t = _resolve_run_threshold(run, "answer_relevancy")
    semantic_similarity = _resolve_run_metric(run, "semantic_similarity")
    semantic_similarity_t = _resolve_run_threshold(run, "semantic_similarity")

    core_fidelity = _weighted_average(
        [
            (_centered_norm(faithfulness, faithfulness_t), 0.45),
            (_centered_norm(factual_correctness, factual_correctness_t), 0.35),
            (_centered_norm(grounding_ratio, grounding_ratio_t), 0.20),
        ]
    )

    return _weighted_average(
        [
            (core_fidelity, 0.60),
            (_centered_norm(answer_relevancy, answer_relevancy_t), 0.25),
            (_centered_norm(semantic_similarity, semantic_similarity_t), 0.15),
        ]
    )


def _resolve_run_metric(run: EvaluationRun, name: str) -> float | None:
    return run.get_avg_score(name)


def _resolve_run_threshold(run: EvaluationRun, name: str) -> float:
    if run.thresholds and name in run.thresholds:
        return run.thresholds[name]
    for result in run.results:
        for metric in result.metrics:
            if metric.name == name:
                return metric.threshold
    return DEFAULT_METRIC_THRESHOLD


def _resolve_stage_metric(
    stage_metric_map: dict[str, dict[str, float]],
    name: str,
) -> float | None:
    entry = stage_metric_map.get(name)
    if not entry:
        return None
    return entry.get("avg")


def _resolve_stage_threshold(
    stage_metric_map: dict[str, dict[str, float]],
    name: str,
    fallback: float | None = None,
) -> float | None:
    entry = stage_metric_map.get(name)
    if entry and entry.get("threshold") is not None:
        return entry["threshold"]
    if fallback is not None:
        return fallback
    return DEFAULT_METRIC_THRESHOLD


def _resolve_phoenix_drift(
    run: EvaluationRun,
    resolver: PhoenixExperimentResolver | None,
) -> float | None:
    if not resolver:
        return None
    stats = resolver.get_stats(run.tracker_metadata)
    if not stats:
        return None
    return stats.drift_score


def _resolve_reliability(
    run: EvaluationRun,
    memory_port: MemoryInsightPort | None,
) -> float | None:
    if memory_port is None:
        return None
    domain_meta = (run.tracker_metadata or {}).get("domain_memory") or {}
    domain = domain_meta.get("domain")
    language = domain_meta.get("language")
    if not isinstance(domain, str) or not isinstance(language, str):
        return None
    try:
        reliability = memory_port.get_aggregated_reliability(domain=domain, language=language)
    except Exception:
        return None
    if not reliability:
        return None
    return mean(reliability.values())


def _compute_prompt_risk(
    run: EvaluationRun,
    stage_metric_map: dict[str, dict[str, float]],
) -> float | None:
    entries = extract_prompt_entries(run.tracker_metadata)
    prompt_drift_rate = None
    if entries:
        summary = summarize_prompt_counts(entries)
        total = summary.get("total", 0) or 0
        drift = summary.get("drift", 0) or 0
        if total > 0:
            prompt_drift_rate = drift / total

    policy_violation_rate = _resolve_stage_metric(
        stage_metric_map, "system_prompt.policy_violation_rate"
    )
    if prompt_drift_rate is None and policy_violation_rate is None:
        return None
    if prompt_drift_rate is None:
        return policy_violation_rate
    if policy_violation_rate is None:
        return prompt_drift_rate
    return max(prompt_drift_rate, policy_violation_rate)


def _resolve_result_count_norm(stage_events: list[StageEvent]) -> float | None:
    retrieval_events = [event for event in stage_events if event.stage_type == "retrieval"]
    if not retrieval_events:
        return None
    counts: list[int] = []
    top_ks: list[int] = []
    for event in retrieval_events:
        doc_ids = event.attributes.get("doc_ids")
        if isinstance(doc_ids, list):
            counts.append(len(doc_ids))
            top_k = event.attributes.get("top_k")
            if isinstance(top_k, int | float) and top_k > 0:
                top_ks.append(int(top_k))
            else:
                top_ks.append(len(doc_ids))
    if not counts:
        return None
    avg_count = mean(counts)
    avg_top_k = mean(top_ks) if top_ks else None
    if avg_top_k and avg_top_k > 0:
        return min(avg_count / avg_top_k, 1.0)
    return 1.0 if avg_count > 0 else 0.0


def _compute_variance(run: EvaluationRun) -> float | None:
    values = []
    for result in run.results:
        score = _case_metric_score(
            result, ("faithfulness", "factual_correctness", "answer_relevancy")
        )
        if score is not None:
            values.append(score)
    if len(values) < 20:
        return None
    values_sorted = sorted(values)
    p90 = _percentile(values_sorted, 0.9)
    p10 = _percentile(values_sorted, 0.1)
    return max(0.0, p90 - p10)


def _case_metric_score(result: TestCaseResult, priority: Iterable[str]) -> float | None:
    scores = {metric.name: metric.score for metric in result.metrics}
    for name in priority:
        if name in scores:
            return scores[name]
    return None


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    index = int(round((len(values) - 1) * q))
    index = max(0, min(index, len(values) - 1))
    return values[index]


def _build_run_point(
    run: EvaluationRun,
    coords: dict[str, Any],
    regression_rate: float | None,
) -> dict[str, Any]:
    quadrant = _quadrant_label(coords.get("x"), coords.get("y"))
    return {
        "id": run.run_id,
        "coords": {"x": coords.get("x"), "y": coords.get("y"), "z": coords.get("z")},
        "breakdown": coords.get("breakdown"),
        "encoding": {
            "color": _risk_color(coords.get("x"), coords.get("y")),
            "size": (
                min(1.0, max(0.2, run.total_test_cases / 100.0)) if run.total_test_cases else 0.4
            ),
            "shape": "regression" if regression_rate and regression_rate > 0 else "stable",
            "opacity": 0.8,
            "border": "pass" if run.pass_rate >= 0.7 else "fail",
        },
        "labels": {
            "name": run.run_id,
            "quadrant": quadrant,
            "guide_hint": _quadrant_hint(quadrant),
        },
        "stats": {
            "pass_rate": run.pass_rate,
            "variance": coords.get("breakdown", {}).get("variance"),
            "prompt_risk": coords.get("breakdown", {}).get("prompt_risk"),
        },
    }


def _build_case_points(
    *,
    run: EvaluationRun,
    run_coords: dict[str, Any],
    base_run: EvaluationRun | None,
    case_deltas: dict[str, str],
) -> list[dict[str, Any]]:
    base_map = {result.test_case_id: result for result in base_run.results} if base_run else {}
    points = []
    for result in run.results:
        coords = _build_case_coords(result)
        quadrant = _quadrant_label(coords.get("x"), coords.get("y"))
        delta = case_deltas.get(result.test_case_id)
        encoding = {
            "color": "risk.fail" if not result.all_passed else "risk.ok",
            "shape": delta or "case",
            "opacity": 0.7,
            "border": "pass" if result.all_passed else "fail",
        }
        if delta == "regression":
            encoding["color"] = "risk.regression"
        elif delta == "improvement":
            encoding["color"] = "risk.improvement"
        elif delta == "same_fail":
            encoding["color"] = "risk.fail"
        elif delta == "same_pass":
            encoding["color"] = "risk.ok"

        base_case = base_map.get(result.test_case_id)
        points.append(
            {
                "id": result.test_case_id,
                "coords": {
                    "x": coords.get("x"),
                    "y": coords.get("y"),
                    "z": run_coords.get("z"),
                },
                "encoding": encoding,
                "labels": {
                    "name": result.test_case_id,
                    "quadrant": quadrant,
                    "guide_hint": _quadrant_hint(quadrant),
                },
                "stats": {
                    "pass_rate": 1.0 if result.all_passed else 0.0,
                    "delta": delta,
                    "base_passed": base_case.all_passed if base_case else None,
                },
            }
        )
    return points


def _build_case_coords(result: TestCaseResult) -> dict[str, float | None]:
    scores = {metric.name: metric.score for metric in result.metrics}
    thresholds = {metric.name: metric.threshold for metric in result.metrics}
    precision_like = _weighted_average(
        [
            (
                _centered_norm(
                    scores.get("context_precision"),
                    thresholds.get("context_precision"),
                ),
                1.0,
            ),
        ]
    )
    recall_like = _weighted_average(
        [
            (_centered_norm(scores.get("context_recall"), thresholds.get("context_recall")), 1.0),
        ]
    )
    x_value = _weighted_average([(precision_like, 0.5), (recall_like, 0.5)])

    core_fidelity = _weighted_average(
        [
            (_centered_norm(scores.get("faithfulness"), thresholds.get("faithfulness")), 0.45),
            (
                _centered_norm(
                    scores.get("factual_correctness"),
                    thresholds.get("factual_correctness"),
                ),
                0.35,
            ),
        ]
    )
    y_value = _weighted_average(
        [
            (core_fidelity, 0.60),
            (
                _centered_norm(scores.get("answer_relevancy"), thresholds.get("answer_relevancy")),
                0.25,
            ),
            (
                _centered_norm(
                    scores.get("semantic_similarity"),
                    thresholds.get("semantic_similarity"),
                ),
                0.15,
            ),
        ]
    )

    if x_value is None:
        x_value = _weighted_average(
            [
                (
                    _centered_norm(
                        scores.get("summary_accuracy"), thresholds.get("summary_accuracy")
                    ),
                    0.4,
                ),
                (
                    _centered_norm(
                        scores.get("summary_risk_coverage"),
                        thresholds.get("summary_risk_coverage"),
                    ),
                    0.3,
                ),
                (
                    _centered_norm(
                        scores.get("summary_faithfulness"),
                        thresholds.get("summary_faithfulness"),
                    ),
                    0.2,
                ),
                (
                    _centered_norm(scores.get("summary_score"), thresholds.get("summary_score")),
                    0.1,
                ),
                (
                    _centered_norm(
                        scores.get("entity_preservation"),
                        thresholds.get("entity_preservation"),
                    ),
                    0.2,
                ),
            ]
        )

    if y_value is None:
        y_value = _weighted_average(
            [
                (
                    _centered_norm(
                        scores.get("summary_accuracy"), thresholds.get("summary_accuracy")
                    ),
                    0.35,
                ),
                (
                    _centered_norm(
                        scores.get("summary_non_definitive"),
                        thresholds.get("summary_non_definitive"),
                    ),
                    0.35,
                ),
                (
                    _centered_norm(
                        scores.get("summary_needs_followup"),
                        thresholds.get("summary_needs_followup"),
                    ),
                    0.3,
                ),
                (
                    _centered_norm(
                        scores.get("entity_preservation"),
                        thresholds.get("entity_preservation"),
                    ),
                    0.2,
                ),
            ]
        )

    return {"x": x_value, "y": y_value}


def _build_cluster_points(
    run: EvaluationRun,
    base_run: EvaluationRun | None,
    case_deltas: dict[str, str],
    run_coords: dict[str, Any],
    cluster_map: dict[str, str] | None,
) -> tuple[list[dict[str, Any]], str | None]:
    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    tracker_cluster_map = _resolve_cluster_map_from_tracker(run)
    for result in run.results:
        cluster_id = _extract_cluster_id(
            run,
            result.test_case_id,
            cluster_map,
            tracker_cluster_map,
        )
        if cluster_id is None:
            continue
        coords = _build_case_coords(result)
        clusters[str(cluster_id)].append(coords)

    if not clusters:
        return [], "cluster data unavailable"

    points = []
    for cluster_id, coords_list in clusters.items():
        x_values = [
            value for value in (c.get("x") for c in coords_list) if isinstance(value, (int, float))
        ]
        y_values = [
            value for value in (c.get("y") for c in coords_list) if isinstance(value, (int, float))
        ]
        x_avg = mean(x_values) if x_values else None
        y_avg = mean(y_values) if y_values else None
        quadrant = _quadrant_label(x_avg, y_avg)
        points.append(
            {
                "id": cluster_id,
                "coords": {"x": x_avg, "y": y_avg, "z": run_coords.get("z")},
                "encoding": {
                    "color": _risk_color(x_avg, y_avg),
                    "size": min(1.0, max(0.2, len(coords_list) / 50.0)),
                    "shape": "cluster",
                    "opacity": 0.8,
                },
                "labels": {
                    "name": f"cluster-{cluster_id}",
                    "quadrant": quadrant,
                    "guide_hint": _quadrant_hint(quadrant),
                },
                "stats": {"count": len(coords_list)},
            }
        )
    return points, None


def _extract_cluster_id(
    run: EvaluationRun,
    case_id: str,
    cluster_map: dict[str, str] | None,
    tracker_cluster_map: dict[str, str] | None,
) -> str | None:
    if cluster_map and case_id in cluster_map:
        return str(cluster_map[case_id])
    if tracker_cluster_map and case_id in tracker_cluster_map:
        return str(tracker_cluster_map[case_id])

    meta = run.retrieval_metadata.get(case_id) if run.retrieval_metadata else None
    if not isinstance(meta, dict):
        return None
    for key in ("cluster_id", "cluster", "hdbscan_cluster", "phoenix_cluster_id"):
        value = meta.get(key)
        if value is not None:
            return str(value)
    return None


def _resolve_cluster_map_from_tracker(run: EvaluationRun) -> dict[str, str] | None:
    metadata = run.tracker_metadata or {}
    candidates: list[Any] = []
    for key in ("cluster_map", "cluster_by_case", "cluster_id_map"):
        if key in metadata:
            candidates.append(metadata.get(key))
    phoenix_meta = metadata.get("phoenix")
    if isinstance(phoenix_meta, dict):
        for key in (
            "cluster_map",
            "cluster_by_case",
            "cluster_id_map",
            "hdbscan_clusters",
        ):
            if key in phoenix_meta:
                candidates.append(phoenix_meta.get(key))

    for candidate in candidates:
        normalized = _normalize_cluster_map(candidate)
        if normalized:
            return normalized
    return None


def _normalize_cluster_map(raw: Any) -> dict[str, str] | None:
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items()}
    if isinstance(raw, list):
        normalized: dict[str, str] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            case_id = item.get("test_case_id") or item.get("case_id") or item.get("id")
            cluster_id = item.get("cluster_id") or item.get("cluster")
            if case_id is None or cluster_id is None:
                continue
            normalized[str(case_id)] = str(cluster_id)
        return normalized or None
    return None


def _quadrant_label(x_value: float | None, y_value: float | None) -> str | None:
    if x_value is None or y_value is None:
        return None
    if x_value >= 0 and y_value >= 0:
        return "expand"
    if x_value < 0 and y_value >= 0:
        return "search_boost"
    if x_value >= 0 and y_value < 0:
        return "generation_fix"
    return "reset"


def _quadrant_hint(label: str | None) -> str | None:
    if label == "expand":
        return "확장 준비"
    if label == "search_boost":
        return "검색 커버리지 개선"
    if label == "generation_fix":
        return "답변 정합성 개선"
    if label == "reset":
        return "파이프라인 재점검"
    return None


def _risk_color(x_value: float | None, y_value: float | None) -> str:
    if x_value is None or y_value is None:
        return "risk.unknown"
    if y_value < 0:
        return "risk.hallucination"
    if x_value < 0:
        return "risk.coverage"
    return "risk.ok"


def _apply_paging(
    points: list[dict[str, Any]],
    limit: int | None,
    offset: int | None,
) -> list[dict[str, Any]]:
    if not points:
        return points
    start = max(0, offset or 0)
    if limit is None:
        return points[start:]
    return points[start : start + max(0, limit)]


def _summarize_points(
    points: list[dict[str, Any]],
    case_deltas: dict[str, str],
) -> dict[str, Any] | None:
    if not points:
        return None
    quadrant_counts = defaultdict(int)
    for point in points:
        label = (point.get("labels") or {}).get("quadrant")
        if label:
            quadrant_counts[label] += 1
    regressions = sum(1 for value in case_deltas.values() if value == "regression")
    improvements = sum(1 for value in case_deltas.values() if value == "improvement")
    return {
        "quadrant_counts": dict(quadrant_counts),
        "regressions": regressions,
        "improvements": improvements,
    }
