from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from evalvault.domain.entities import (
    CalibrationCaseResult,
    CalibrationResult,
    CalibrationSummary,
    EvaluationRun,
    SatisfactionFeedback,
)


@dataclass
class CalibrationModelResult:
    model_name: str
    mae: float | None
    pearson: float | None
    spearman: float | None


class SatisfactionCalibrationService:
    def __init__(self, *, thumb_mapping: dict[str, float] | None = None) -> None:
        self._thumb_mapping = thumb_mapping or {"up": 4.0, "down": 2.0}

    def build_calibration(
        self,
        run: EvaluationRun,
        feedbacks: list[SatisfactionFeedback],
        *,
        model: str = "both",
    ) -> CalibrationResult:
        feedback_index = self._build_feedback_index(feedbacks)
        feature_map = self._build_feature_matrix(run)
        labels, label_sources = self._build_labels(run, feedback_index)

        if not feedback_index:
            summary = CalibrationSummary(
                avg_satisfaction_score=None,
                thumb_up_rate=None,
                imputed_ratio=0.0,
            )
            return CalibrationResult(summary=summary, cases={})

        model_metrics: dict[str, dict[str, float | None]] = {}
        model_choice, predictors = self._train_models(
            feature_map,
            labels,
            model=model,
            model_metrics=model_metrics,
        )

        summary = self._build_summary(run, feedback_index)
        cases: dict[str, CalibrationCaseResult] = {}
        imputed_count = 0

        for test_case_id, features in feature_map.items():
            label = labels.get(test_case_id)
            source = label_sources.get(test_case_id)
            if label is not None:
                calibrated = self._clip_score(label)
                imputed = source != "label"
                imputation_source = source
            else:
                calibrated = self._predict_or_fallback(
                    predictors.get(model_choice),
                    features,
                    labels,
                )
                if calibrated is None:
                    imputed = False
                    imputation_source = None
                else:
                    imputed = True
                    imputation_source = "model" if predictors.get(model_choice) else "fallback_mean"

            if imputed:
                imputed_count += 1

            cases[test_case_id] = CalibrationCaseResult(
                test_case_id=test_case_id,
                calibrated_satisfaction=calibrated,
                imputed=imputed,
                imputation_source=imputation_source,
            )

        summary.imputed_ratio = imputed_count / len(cases) if cases else summary.imputed_ratio
        summary.model_metrics = model_metrics
        return CalibrationResult(summary=summary, cases=cases)

    def _build_feedback_index(
        self, feedbacks: list[SatisfactionFeedback]
    ) -> dict[str, SatisfactionFeedback]:
        latest: dict[str, SatisfactionFeedback] = {}
        for feedback in feedbacks:
            current = latest.get(feedback.test_case_id)
            if current is None:
                latest[feedback.test_case_id] = feedback
                continue
            current_time = current.created_at or datetime.min
            feedback_time = feedback.created_at or datetime.min
            if feedback_time >= current_time:
                latest[feedback.test_case_id] = feedback
        return latest

    def _build_feature_matrix(self, run: EvaluationRun) -> dict[str, list[float]]:
        feature_map: dict[str, list[float]] = {}

        for result in run.results:
            features = [
                self._metric_score(result, "faithfulness"),
                self._metric_score(result, "answer_relevancy"),
                self._metric_score(result, "context_precision"),
                self._metric_score(result, "context_recall"),
                self._answer_length(result.answer),
                self._keyword_missing_rate(result.question, result.answer, result.contexts),
                self._ttr(result.answer),
            ]
            feature_map[result.test_case_id] = features
        return feature_map

    def _build_labels(
        self,
        run: EvaluationRun,
        feedback_index: dict[str, SatisfactionFeedback],
    ) -> tuple[dict[str, float], dict[str, str]]:
        labels: dict[str, float] = {}
        sources: dict[str, str] = {}
        for result in run.results:
            feedback = feedback_index.get(result.test_case_id)
            if feedback is None:
                continue
            if feedback.satisfaction_score is not None:
                labels[result.test_case_id] = feedback.satisfaction_score
                sources[result.test_case_id] = "label"
                continue
            mapped = self._thumb_mapping.get((feedback.thumb_feedback or "").lower())
            if mapped is not None:
                labels[result.test_case_id] = mapped
                sources[result.test_case_id] = "thumb"
        return labels, sources

    def _train_models(
        self,
        feature_map: dict[str, list[float]],
        labels: dict[str, float],
        *,
        model: str,
        model_metrics: dict[str, dict[str, float | None]],
    ) -> tuple[str, dict[str, Any]]:
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import mean_absolute_error
        from sklearn.model_selection import train_test_split

        if not labels:
            return "linear", {}

        features_matrix: list[list[float]] = []
        labels_vector: list[float] = []
        for test_case_id, label in labels.items():
            features = feature_map.get(test_case_id)
            if features is None:
                continue
            features_matrix.append(features)
            labels_vector.append(label)

        if not features_matrix:
            return "linear", {}

        if len(labels_vector) >= 5:
            features_train, features_test, labels_train, labels_test = train_test_split(
                features_matrix, labels_vector, test_size=0.2, random_state=42
            )
        else:
            features_train, features_test, labels_train, labels_test = (
                features_matrix,
                features_matrix,
                labels_vector,
                labels_vector,
            )

        predictors: dict[str, Any] = {}

        linear = LinearRegression()
        linear.fit(features_train, labels_train)
        linear_pred = linear.predict(features_test)
        model_metrics["linear"] = self._build_metrics(labels_test, linear_pred, mean_absolute_error)
        predictors["linear"] = linear

        if model in {"xgb", "both"}:
            try:
                import importlib

                xgb_module = importlib.import_module("xgboost")
                xgb_regressor = xgb_module.XGBRegressor

                xgb = xgb_regressor(
                    objective="reg:squarederror",
                    n_estimators=150,
                    max_depth=5,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_alpha=0.1,
                    reg_lambda=1.0,
                    n_jobs=-1,
                    random_state=42,
                )
                xgb.fit(features_train, labels_train)
                xgb_pred = xgb.predict(features_test)
                model_metrics["xgb"] = self._build_metrics(
                    labels_test, xgb_pred, mean_absolute_error
                )
                predictors["xgb"] = xgb
            except Exception:
                model_metrics["xgb"] = {"mae": None, "pearson": None, "spearman": None}

        model_choice = "xgb" if model in {"xgb", "both"} and "xgb" in predictors else "linear"
        return model_choice, predictors

    def _build_metrics(
        self,
        y_true: list[float],
        y_pred: list[float],
        mae_func,
    ) -> dict[str, float | None]:
        mae = float(mae_func(y_true, y_pred)) if y_true else None
        pearson = self._safe_corr(y_true, y_pred, method="pearson")
        spearman = self._safe_corr(y_true, y_pred, method="spearman")
        return {"mae": mae, "pearson": pearson, "spearman": spearman}

    def _predict_or_fallback(
        self,
        predictor: Any | None,
        features: list[float],
        labels: dict[str, float],
    ) -> float | None:
        if predictor is not None:
            prediction = predictor.predict([features])[0]
            return self._clip_score(float(prediction))
        fallback = self._fallback_mean(labels)
        if fallback is None:
            return None
        return self._clip_score(fallback)

    def _fallback_mean(self, labels: dict[str, float]) -> float | None:
        if not labels:
            return None
        return sum(labels.values()) / len(labels)

    def _build_summary(
        self, run: EvaluationRun, feedback_index: dict[str, SatisfactionFeedback]
    ) -> CalibrationSummary:
        scores: list[float] = []
        thumbs: list[str] = []
        for result in run.results:
            feedback = feedback_index.get(result.test_case_id)
            if feedback is None:
                continue
            if feedback.satisfaction_score is not None:
                scores.append(feedback.satisfaction_score)
            if feedback.thumb_feedback in {"up", "down"}:
                thumbs.append(feedback.thumb_feedback)
        avg_score = sum(scores) / len(scores) if scores else None
        thumb_up_rate = None
        if thumbs:
            thumb_up_rate = thumbs.count("up") / len(thumbs)
        return CalibrationSummary(
            avg_satisfaction_score=avg_score,
            thumb_up_rate=thumb_up_rate,
            imputed_ratio=None,
        )

    def _metric_score(self, result, name: str) -> float:
        metric = result.get_metric(name)
        if metric and metric.score is not None:
            return float(metric.score)
        return 0.0

    def _answer_length(self, answer: str | None) -> float:
        tokens = self._tokenize(answer or "")
        return float(len(tokens))

    def _keyword_missing_rate(
        self,
        question: str | None,
        answer: str | None,
        contexts: list[str] | None,
    ) -> float:
        question_tokens = set(self._tokenize(question or ""))
        if not question_tokens:
            return 0.0
        combined = " ".join([answer or "", *(contexts or [])])
        combined_tokens = set(self._tokenize(combined))
        missing = [token for token in question_tokens if token not in combined_tokens]
        return len(missing) / len(question_tokens)

    def _ttr(self, answer: str | None) -> float:
        tokens = self._tokenize(answer or "")
        if not tokens:
            return 0.0
        return len(set(tokens)) / len(tokens)

    def _tokenize(self, text: str) -> list[str]:
        series = pd.Series([text])
        tokens = series.str.findall(r"[가-힣a-zA-Z0-9]{2,}").iloc[0]
        return [token.lower() for token in tokens]

    def _clip_score(self, score: float) -> float:
        return max(1.0, min(5.0, score))

    def _safe_corr(self, y_true: list[float], y_pred: list[float], *, method: str) -> float | None:
        if len(y_true) < 2 or len(y_pred) < 2:
            return None
        series_a = pd.Series(y_true)
        series_b = pd.Series(y_pred)
        if method == "spearman":
            series_a = series_a.rank()
            series_b = series_b.rank()
        try:
            corr = series_a.corr(series_b)
            return float(corr) if corr is not None else None
        except Exception:
            return None
