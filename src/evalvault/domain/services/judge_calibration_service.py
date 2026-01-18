from __future__ import annotations

import logging
import math
from collections.abc import Iterable
from dataclasses import asdict
from datetime import datetime

from evalvault.domain.entities import EvaluationRun, SatisfactionFeedback
from evalvault.domain.entities.judge_calibration import (
    JudgeCalibrationCase,
    JudgeCalibrationMetric,
    JudgeCalibrationResult,
    JudgeCalibrationSummary,
)
from evalvault.ports.outbound.judge_calibration_port import JudgeCalibrationPort

logger = logging.getLogger(__name__)


class JudgeCalibrationService(JudgeCalibrationPort):
    def calibrate(
        self,
        run: EvaluationRun,
        feedbacks: list[SatisfactionFeedback],
        *,
        labels_source: str,
        method: str,
        metrics: list[str],
        holdout_ratio: float,
        seed: int,
        parallel: bool = False,
        concurrency: int = 8,
    ) -> JudgeCalibrationResult:
        resolved_metrics = self._resolve_metrics(run, metrics)
        logger.info(
            "Judge 보정 시작: run_id=%s metrics=%s method=%s parallel=%s concurrency=%s",
            run.run_id,
            ",".join(resolved_metrics),
            method,
            parallel,
            concurrency,
        )

        feedback_index = self._build_feedback_index(feedbacks)
        total_labels = 0
        case_results: dict[str, list[JudgeCalibrationCase]] = {}
        metric_results: list[JudgeCalibrationMetric] = []
        warnings: list[str] = []
        gate_threshold = 0.6
        gate_passed = True
        if labels_source == "gold":
            warning = "gold 라벨 소스는 아직 지원되지 않습니다."
            warnings.append(warning)
            logger.error("Judge 보정 실패: %s", warning)
            summary = JudgeCalibrationSummary(
                run_id=run.run_id,
                labels_source=labels_source,
                method=method,
                metrics=resolved_metrics,
                holdout_ratio=holdout_ratio,
                seed=seed,
                total_labels=0,
                total_samples=len(run.results),
                gate_passed=False,
                gate_threshold=gate_threshold,
                notes=warnings,
            )
            logger.info(
                "Judge 보정 종료: run_id=%s gate_passed=%s",
                run.run_id,
                summary.gate_passed,
            )
            return JudgeCalibrationResult(
                summary=summary,
                metrics=[],
                case_results={},
                warnings=warnings,
            )

        for metric in resolved_metrics:
            scores, labels, label_sources, sample_ids = self._collect_metric_samples(
                run,
                feedback_index,
                metric,
                labels_source,
            )
            if not labels:
                warning = f"{metric} 라벨이 없어 보정을 건너뜁니다."
                warnings.append(warning)
                metric_results.append(
                    JudgeCalibrationMetric(
                        metric=metric,
                        method=method,
                        sample_count=0,
                        label_count=0,
                        mae=None,
                        pearson=None,
                        spearman=None,
                        temperature=None,
                        parameters={},
                        gate_passed=False,
                        warning=warning,
                    )
                )
                gate_passed = False
                continue
            total_labels += len(labels)
            if not scores:
                warning = f"{metric} 점수가 없어 보정을 건너뜁니다."
                warnings.append(warning)
                metric_results.append(
                    JudgeCalibrationMetric(
                        metric=metric,
                        method=method,
                        sample_count=0,
                        label_count=len(labels),
                        mae=None,
                        pearson=None,
                        spearman=None,
                        temperature=None,
                        parameters={},
                        gate_passed=False,
                        warning=warning,
                    )
                )
                gate_passed = False
                continue

            fit = self._fit_calibration(
                scores,
                labels,
                method=method,
                holdout_ratio=holdout_ratio,
                seed=seed,
            )
            calibrated_scores = fit[0]
            mae, pearson, spearman = fit[1], fit[2], fit[3]
            parameters = fit[4]
            temperature = parameters.get("temperature") if parameters else None
            gate_metric_pass = self._passes_gate(pearson, spearman, gate_threshold)
            warning = None
            if len(labels) < 2:
                warning = f"{metric} 라벨이 부족해 보정 품질을 계산하지 못했습니다."
                warnings.append(warning)
                gate_metric_pass = False

            if not gate_metric_pass:
                gate_passed = False

            metric_results.append(
                JudgeCalibrationMetric(
                    metric=metric,
                    method=method,
                    sample_count=len(scores),
                    label_count=len(labels),
                    mae=mae,
                    pearson=pearson,
                    spearman=spearman,
                    temperature=temperature,
                    parameters=parameters,
                    gate_passed=gate_metric_pass,
                    warning=warning,
                )
            )

            case_entries = []
            label_count = len(labels)
            for idx, (test_case_id, raw_score, calibrated, label_source) in enumerate(
                zip(sample_ids, scores, calibrated_scores, label_sources, strict=False)
            ):
                label_value = labels[idx] if idx < label_count else None
                case_entries.append(
                    JudgeCalibrationCase(
                        test_case_id=test_case_id,
                        raw_score=raw_score,
                        calibrated_score=calibrated,
                        label=label_value,
                        label_source=label_source,
                    )
                )
            case_results[metric] = case_entries

        summary = JudgeCalibrationSummary(
            run_id=run.run_id,
            labels_source=labels_source,
            method=method,
            metrics=resolved_metrics,
            holdout_ratio=holdout_ratio,
            seed=seed,
            total_labels=total_labels,
            total_samples=len(run.results),
            gate_passed=gate_passed,
            gate_threshold=gate_threshold,
            notes=warnings,
        )

        logger.info(
            "Judge 보정 종료: run_id=%s gate_passed=%s",
            run.run_id,
            gate_passed,
        )
        return JudgeCalibrationResult(
            summary=summary,
            metrics=metric_results,
            case_results=case_results,
            warnings=warnings,
        )

    def to_dict(self, result: JudgeCalibrationResult) -> dict[str, object]:
        return {
            "summary": asdict(result.summary),
            "metrics": [asdict(metric) for metric in result.metrics],
            "case_results": {
                metric: [asdict(entry) for entry in entries]
                for metric, entries in result.case_results.items()
            },
            "warnings": list(result.warnings),
        }

    def _resolve_metrics(self, run: EvaluationRun, metrics: list[str]) -> list[str]:
        if metrics:
            return list(dict.fromkeys(metrics))
        return list(run.metrics_evaluated)

    def _build_feedback_index(
        self, feedbacks: list[SatisfactionFeedback]
    ) -> dict[str, SatisfactionFeedback]:
        latest: dict[str, SatisfactionFeedback] = {}
        for feedback in feedbacks:
            current = latest.get(feedback.test_case_id)
            if current is None:
                latest[feedback.test_case_id] = feedback
                continue
            current_time = current.created_at
            feedback_time = feedback.created_at
            if (feedback_time or datetime.min) >= (current_time or datetime.min):
                latest[feedback.test_case_id] = feedback
        return latest

    def _collect_metric_samples(
        self,
        run: EvaluationRun,
        feedback_index: dict[str, SatisfactionFeedback],
        metric: str,
        labels_source: str,
    ) -> tuple[list[float], list[float], list[str | None], list[str]]:
        scores: list[float] = []
        labels: list[float] = []
        label_sources: list[str | None] = []
        sample_ids: list[str] = []
        for result in run.results:
            metric_score = result.get_metric(metric)
            if metric_score is None or metric_score.score is None:
                continue
            scores.append(float(metric_score.score))
            sample_ids.append(result.test_case_id)
            label_value, label_source = self._resolve_label(
                feedback_index.get(result.test_case_id),
                labels_source=labels_source,
            )
            if label_value is not None:
                labels.append(label_value)
                label_sources.append(label_source)
        return scores, labels, label_sources, sample_ids

    def _resolve_label(
        self,
        feedback: SatisfactionFeedback | None,
        *,
        labels_source: str,
    ) -> tuple[float | None, str | None]:
        if feedback is None:
            return None, None
        if labels_source in {"feedback", "hybrid"}:
            if feedback.satisfaction_score is not None:
                return float(feedback.satisfaction_score), "feedback"
            if feedback.thumb_feedback:
                thumb = feedback.thumb_feedback.lower()
                if thumb == "up":
                    return 4.0, "thumb"
                if thumb == "down":
                    return 2.0, "thumb"
        return None, None

    def _fit_calibration(
        self,
        scores: list[float],
        labels: list[float],
        *,
        method: str,
        holdout_ratio: float,
        seed: int,
    ) -> tuple[list[float], float | None, float | None, float | None, dict[str, float | None]]:
        if not labels:
            return scores, None, None, None, {}
        train_scores, train_labels, test_scores, test_labels = self._split_holdout(
            scores,
            labels,
            holdout_ratio=holdout_ratio,
            seed=seed,
        )
        if method == "none":
            calibrated = scores
            mae = self._mae(test_scores, test_labels)
            pearson = self._pearson(test_scores, test_labels)
            spearman = self._spearman(test_scores, test_labels)
            return calibrated, mae, pearson, spearman, {}
        if method == "temperature":
            temperature = self._fit_temperature(train_scores, train_labels)
            calibrated = [self._calibrate_temperature(score, temperature) for score in scores]
            calibrated_test = [
                self._calibrate_temperature(score, temperature) for score in test_scores
            ]
            mae = self._mae(calibrated_test, test_labels)
            pearson = self._pearson(calibrated_test, test_labels)
            spearman = self._spearman(calibrated_test, test_labels)
            return (
                calibrated,
                mae,
                pearson,
                spearman,
                {"temperature": temperature},
            )
        if method == "platt":
            slope, intercept = self._fit_platt(train_scores, train_labels)
            calibrated = [self._calibrate_platt(score, slope, intercept) for score in scores]
            calibrated_test = [
                self._calibrate_platt(score, slope, intercept) for score in test_scores
            ]
            mae = self._mae(calibrated_test, test_labels)
            pearson = self._pearson(calibrated_test, test_labels)
            spearman = self._spearman(calibrated_test, test_labels)
            return (
                calibrated,
                mae,
                pearson,
                spearman,
                {"slope": slope, "intercept": intercept},
            )
        if method == "isotonic":
            calibrated = self._calibrate_isotonic(train_scores, train_labels, scores)
            calibrated_test = self._calibrate_isotonic(train_scores, train_labels, test_scores)
            mae = self._mae(calibrated_test, test_labels)
            pearson = self._pearson(calibrated_test, test_labels)
            spearman = self._spearman(calibrated_test, test_labels)
            return calibrated, mae, pearson, spearman, {}
        calibrated = scores
        mae = self._mae(test_scores, test_labels)
        pearson = self._pearson(test_scores, test_labels)
        spearman = self._spearman(test_scores, test_labels)
        return calibrated, mae, pearson, spearman, {}

    def _split_holdout(
        self,
        scores: list[float],
        labels: list[float],
        *,
        holdout_ratio: float,
        seed: int,
    ) -> tuple[list[float], list[float], list[float], list[float]]:
        pair_count = min(len(scores), len(labels))
        paired = list(zip(scores[:pair_count], labels[:pair_count], strict=False))
        if holdout_ratio <= 0 or holdout_ratio >= 1 or len(paired) < 2:
            return scores, labels, scores, labels
        rng = self._random(seed)
        rng.shuffle(paired)
        cutoff = max(1, int(len(paired) * (1 - holdout_ratio)))
        train = paired[:cutoff]
        test = paired[cutoff:]
        train_scores = [score for score, _ in train]
        train_labels = [label for _, label in train]
        test_scores = [score for score, _ in test] or train_scores
        test_labels = [label for _, label in test] or train_labels
        return train_scores, train_labels, test_scores, test_labels

    def _fit_temperature(self, scores: list[float], labels: list[float]) -> float:
        if not scores:
            return 1.0
        mean_score = sum(scores) / len(scores)
        mean_label = sum(labels) / len(labels)
        if mean_score <= 0:
            return 1.0
        return max(0.1, min(10.0, mean_label / mean_score))

    def _calibrate_temperature(self, score: float, temperature: float) -> float:
        return self._clip(score * temperature)

    def _fit_platt(self, scores: list[float], labels: list[float]) -> tuple[float, float]:
        if not scores:
            return 1.0, 0.0
        mean_score = sum(scores) / len(scores)
        mean_label = sum(labels) / len(labels)
        var_score = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        if var_score == 0:
            return 1.0, 0.0
        pair_count = min(len(scores), len(labels))
        if pair_count == 0:
            return 1.0, 0.0
        cov = (
            sum(
                (score - mean_score) * (label - mean_label)
                for score, label in zip(scores[:pair_count], labels[:pair_count], strict=False)
            )
            / pair_count
        )
        slope = cov / var_score
        intercept = mean_label - slope * mean_score
        return slope, intercept

    def _calibrate_platt(self, score: float, slope: float, intercept: float) -> float:
        return self._clip(score * slope + intercept)

    def _calibrate_isotonic(
        self, train_scores: list[float], train_labels: list[float], scores: list[float]
    ) -> list[float]:
        if not train_scores:
            return [self._clip(score) for score in scores]
        pairs = sorted(zip(train_scores, train_labels, strict=False), key=lambda x: x[0])
        calibrated = []
        for score in scores:
            calibrated.append(self._calibrate_isotonic_point(score, pairs))
        return calibrated

    def _calibrate_isotonic_point(self, score: float, pairs: list[tuple[float, float]]) -> float:
        if not pairs:
            return self._clip(score)
        prev_score, prev_label = pairs[0]
        if score <= prev_score:
            return self._clip(prev_label)
        for current_score, current_label in pairs[1:]:
            if score <= current_score:
                ratio = (score - prev_score) / (current_score - prev_score)
                value = prev_label + ratio * (current_label - prev_label)
                return self._clip(value)
            prev_score, prev_label = current_score, current_label
        return self._clip(pairs[-1][1])

    def _mae(self, scores: Iterable[float], labels: Iterable[float]) -> float | None:
        values = list(zip(scores, labels, strict=False))
        if not values:
            return None
        return sum(abs(score - label) for score, label in values) / len(values)

    def _pearson(self, scores: Iterable[float], labels: Iterable[float]) -> float | None:
        values = list(zip(scores, labels, strict=False))
        if len(values) < 2:
            return None
        score_vals = [score for score, _ in values]
        label_vals = [label for _, label in values]
        mean_score = sum(score_vals) / len(score_vals)
        mean_label = sum(label_vals) / len(label_vals)
        numerator = sum(
            (score - mean_score) * (label - mean_label)
            for score, label in zip(score_vals, label_vals, strict=False)
        )
        denom_score = math.sqrt(sum((score - mean_score) ** 2 for score in score_vals))
        denom_label = math.sqrt(sum((label - mean_label) ** 2 for label in label_vals))
        if denom_score == 0 or denom_label == 0:
            return None
        return numerator / (denom_score * denom_label)

    def _spearman(self, scores: Iterable[float], labels: Iterable[float]) -> float | None:
        values = list(zip(scores, labels, strict=False))
        if len(values) < 2:
            return None
        score_vals = [score for score, _ in values]
        label_vals = [label for _, label in values]
        score_ranks = self._rank(score_vals)
        label_ranks = self._rank(label_vals)
        return self._pearson(score_ranks, label_ranks)

    def _rank(self, values: list[float]) -> list[float]:
        sorted_vals = sorted(enumerate(values), key=lambda item: item[1])
        ranks = [0.0] * len(values)
        for rank, (index, _) in enumerate(sorted_vals, start=1):
            ranks[index] = float(rank)
        return ranks

    def _clip(self, value: float) -> float:
        return max(0.0, min(1.0, value))

    def _passes_gate(
        self, pearson: float | None, spearman: float | None, gate_threshold: float
    ) -> bool:
        candidates = [metric for metric in (pearson, spearman) if metric is not None]
        if not candidates:
            return False
        return max(candidates) >= gate_threshold

    def _random(self, seed: int):
        import random

        rng = random.Random(seed)
        return rng
