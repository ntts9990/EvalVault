"""Dataset feature analyzer module."""

from __future__ import annotations

import itertools
import math
import re
from collections import Counter
from typing import Any, cast

import numpy as np
from scipy import stats

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output
from evalvault.adapters.outbound.improvement.pattern_detector import PatternDetector
from evalvault.domain.entities import EvaluationRun

try:
    from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer
except Exception:  # pragma: no cover - optional dependency
    KiwiTokenizer = None  # type: ignore[assignment]


_WORD_PATTERN = re.compile(r"[A-Za-z0-9가-힣]+")
_SENTENCE_PATTERN = re.compile(r"[.!?。！？]+")
_HANGUL_PATTERN = re.compile(r"[가-힣]")
_LATIN_PATTERN = re.compile(r"[A-Za-z]")


class DatasetFeatureAnalyzerModule(BaseAnalysisModule):
    """Extract dataset features and analyze metric relationships."""

    module_id = "dataset_feature_analyzer"
    name = "Dataset Feature Analyzer"
    description = "질문/답변/정답/컨텍스트의 특성을 추출하고 점수 연관성을 분석합니다."
    input_types = ["run"]
    output_types = ["dataset_feature_analysis"]
    requires = ["data_loader"]
    tags = ["analysis", "features", "nlp"]

    def __init__(self) -> None:
        self._detector = PatternDetector()
        self._tokenizer = KiwiTokenizer() if KiwiTokenizer else None

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")

        if not isinstance(run, EvaluationRun):
            return {"summary": {"run_id": None, "feature_count": 0}}

        params = params or {}
        include_vectors = bool(params.get("include_vectors", False))
        max_nodes = int(params.get("max_graph_nodes", 50))
        max_edges = int(params.get("max_graph_edges", 200))
        min_samples = int(params.get("min_samples", 5))

        feature_vectors = self._build_feature_vectors(run)
        feature_stats = self._summarize_features(feature_vectors)
        correlation_report = self._analyze_correlations(feature_vectors, min_samples=min_samples)
        importance_report = self._analyze_feature_importance(
            feature_vectors, min_samples=min_samples
        )
        graph = self._build_entity_graph(feature_vectors, max_nodes=max_nodes, max_edges=max_edges)

        summary = {
            "run_id": run.run_id,
            "total_cases": len(feature_vectors),
            "feature_count": len(feature_stats),
            "metrics": list(run.metrics_evaluated),
            "analysis_methods": ["correlation", importance_report.get("method")],
        }

        payload: dict[str, Any] = {
            "summary": summary,
            "feature_stats": feature_stats,
            "feature_correlations": correlation_report,
            "feature_importance": importance_report,
            "entity_graph": graph,
        }
        if include_vectors:
            payload["feature_vectors"] = [
                {
                    "test_case_id": v["test_case_id"],
                    "features": v["features"],
                    "metric_scores": v["metric_scores"],
                }
                for v in feature_vectors
            ]

        return payload

    def _build_feature_vectors(self, run: EvaluationRun) -> list[dict[str, Any]]:
        vectors = []
        feature_vectors = self._detector.extract_feature_vectors(run)
        for vector in feature_vectors:
            features = dict(vector.features)
            features.update(
                self._text_features(vector.question, vector.answer, vector.ground_truth)
            )
            features.update(self._context_features(vector.contexts))
            features.update(
                self._overlap_features(
                    vector.question, vector.answer, vector.ground_truth, vector.contexts
                )
            )
            features.update(
                self._language_features(
                    vector.question, vector.answer, vector.ground_truth, vector.contexts
                )
            )

            vectors.append(
                {
                    "test_case_id": vector.test_case_id,
                    "features": features,
                    "metric_scores": dict(vector.metric_scores),
                    "tokens": self._extract_tokens(
                        vector.question, vector.answer, vector.ground_truth, vector.contexts
                    ),
                }
            )
        return vectors

    def _text_features(
        self, question: str, answer: str, ground_truth: str | None
    ) -> dict[str, float]:
        q_stats = self._basic_stats(question)
        a_stats = self._basic_stats(answer)
        gt_stats = self._basic_stats(ground_truth or "")
        return {
            "question_char_count": q_stats["char_count"],
            "question_word_count": q_stats["word_count"],
            "question_sentence_count": q_stats["sentence_count"],
            "question_unique_word_ratio": q_stats["unique_word_ratio"],
            "answer_char_count": a_stats["char_count"],
            "answer_word_count": a_stats["word_count"],
            "answer_sentence_count": a_stats["sentence_count"],
            "answer_unique_word_ratio": a_stats["unique_word_ratio"],
            "ground_truth_char_count": gt_stats["char_count"],
            "ground_truth_word_count": gt_stats["word_count"],
            "ground_truth_sentence_count": gt_stats["sentence_count"],
            "ground_truth_unique_word_ratio": gt_stats["unique_word_ratio"],
        }

    def _context_features(self, contexts: list[str]) -> dict[str, float]:
        merged = " ".join([ctx for ctx in contexts if ctx])
        stats = self._basic_stats(merged)
        total_length = sum(len(ctx) for ctx in contexts if ctx)
        avg_length = total_length / len(contexts) if contexts else 0.0
        return {
            "context_count": float(len(contexts)),
            "context_total_char_count": float(total_length),
            "context_avg_char_count": float(avg_length),
            "context_word_count": stats["word_count"],
            "context_sentence_count": stats["sentence_count"],
            "context_unique_word_ratio": stats["unique_word_ratio"],
        }

    def _overlap_features(
        self,
        question: str,
        answer: str,
        ground_truth: str | None,
        contexts: list[str],
    ) -> dict[str, float]:
        question_tokens = self._token_set(question)
        answer_tokens = self._token_set(answer)
        truth_tokens = self._token_set(ground_truth or "")
        context_tokens = self._token_set(" ".join(contexts))

        return {
            "question_answer_jaccard": self._jaccard(question_tokens, answer_tokens),
            "question_context_jaccard": self._jaccard(question_tokens, context_tokens),
            "answer_context_jaccard": self._jaccard(answer_tokens, context_tokens),
            "question_truth_jaccard": self._jaccard(question_tokens, truth_tokens),
            "answer_truth_jaccard": self._jaccard(answer_tokens, truth_tokens),
            "truth_context_jaccard": self._jaccard(truth_tokens, context_tokens),
        }

    def _language_features(
        self,
        question: str,
        answer: str,
        ground_truth: str | None,
        contexts: list[str],
    ) -> dict[str, float]:
        merged_context = " ".join([ctx for ctx in contexts if ctx])
        return {
            "question_korean_ratio": self._char_ratio(question, _HANGUL_PATTERN),
            "question_english_ratio": self._char_ratio(question, _LATIN_PATTERN),
            "answer_korean_ratio": self._char_ratio(answer, _HANGUL_PATTERN),
            "answer_english_ratio": self._char_ratio(answer, _LATIN_PATTERN),
            "ground_truth_korean_ratio": self._char_ratio(ground_truth or "", _HANGUL_PATTERN),
            "ground_truth_english_ratio": self._char_ratio(ground_truth or "", _LATIN_PATTERN),
            "context_korean_ratio": self._char_ratio(merged_context, _HANGUL_PATTERN),
            "context_english_ratio": self._char_ratio(merged_context, _LATIN_PATTERN),
        }

    def _basic_stats(self, text: str) -> dict[str, float]:
        stripped = text.strip()
        if not stripped:
            return {
                "char_count": 0.0,
                "word_count": 0.0,
                "sentence_count": 0.0,
                "unique_word_ratio": 0.0,
            }
        words = self._tokenize_words(stripped)
        sentences = [s for s in _SENTENCE_PATTERN.split(stripped) if s.strip()]
        unique_ratio = len({w.lower() for w in words}) / len(words) if words else 0.0
        return {
            "char_count": float(len(stripped)),
            "word_count": float(len(words)),
            "sentence_count": float(max(len(sentences), 1)),
            "unique_word_ratio": float(unique_ratio),
        }

    def _tokenize_words(self, text: str) -> list[str]:
        if self._tokenizer and _HANGUL_PATTERN.search(text):
            return self._tokenizer.tokenize(text)
        return _WORD_PATTERN.findall(text)

    def _token_set(self, text: str) -> set[str]:
        return {token.lower() for token in self._tokenize_words(text) if token}

    def _jaccard(self, left: set[str], right: set[str]) -> float:
        if not left and not right:
            return 0.0
        union = left | right
        if not union:
            return 0.0
        return len(left & right) / len(union)

    def _char_ratio(self, text: str, pattern: re.Pattern[str]) -> float:
        if not text:
            return 0.0
        count = len(pattern.findall(text))
        return count / max(len(text), 1)

    def _summarize_features(self, vectors: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
        if not vectors:
            return {}
        feature_names = sorted(vectors[0]["features"].keys())
        stats_map: dict[str, dict[str, float]] = {}
        for name in feature_names:
            values = [v["features"].get(name, 0.0) for v in vectors]
            arr = np.array(values, dtype=float)
            stats_map[name] = {
                "mean": float(arr.mean()),
                "std": float(arr.std()),
                "min": float(arr.min()),
                "max": float(arr.max()),
                "median": float(np.median(arr)),
            }
        return stats_map

    def _analyze_correlations(
        self,
        vectors: list[dict[str, Any]],
        *,
        min_samples: int,
    ) -> dict[str, list[dict[str, float | str]]]:
        if not vectors:
            return {}
        feature_names = sorted(vectors[0]["features"].keys())
        correlations: dict[str, list[dict[str, float | str]]] = {}
        for metric in self._metric_names(vectors):
            pairs = []
            xs, ys = self._aligned_series(vectors, metric, feature_names)
            for name, values in xs.items():
                target = ys.get(name)
                if target is None or len(target) < min_samples:
                    continue
                if len(set(values)) <= 1:
                    continue
                try:
                    result = stats.pearsonr(values, target)
                    corr = cast(float, getattr(result, "statistic", result[0]))
                    p_value = cast(float, getattr(result, "pvalue", result[1]))
                except Exception:
                    continue
                pairs.append(
                    {
                        "feature": name,
                        "correlation": corr,
                        "p_value": p_value,
                    }
                )
            pairs.sort(key=lambda item: abs(item["correlation"]), reverse=True)
            correlations[metric] = pairs[:50]
        return correlations

    def _analyze_feature_importance(
        self,
        vectors: list[dict[str, Any]],
        *,
        min_samples: int,
    ) -> dict[str, Any]:
        if not vectors:
            return {"method": "none", "metrics": {}}
        feature_names = sorted(vectors[0]["features"].keys())
        metrics: dict[str, list[dict[str, Any]]] = {}

        xgb_regressor = None
        try:
            from xgboost import XGBRegressor

            xgb_regressor = XGBRegressor
        except Exception:
            xgb_regressor = None

        for metric in self._metric_names(vectors):
            xs, ys = self._aligned_matrix(vectors, metric, feature_names)
            if xs is None or ys is None or len(ys) < min_samples:
                continue
            importances: list[dict[str, Any]] = []
            if xgb_regressor is not None and len(ys) >= max(min_samples, 10):
                try:
                    model = xgb_regressor(
                        n_estimators=200,
                        max_depth=4,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        tree_method="hist",
                        objective="reg:squarederror",
                        random_state=42,
                    )
                    model.fit(xs, ys)
                    for name, score in zip(feature_names, model.feature_importances_, strict=True):
                        importances.append({"feature": name, "importance": float(score)})
                except Exception:
                    importances = []

            if not importances:
                corr_map = self._simple_importance_from_correlation(xs, ys, feature_names)
                importances = [{"feature": name, "importance": score} for name, score in corr_map]

            importances.sort(key=lambda item: item["importance"], reverse=True)
            metrics[metric] = importances[:50]

        return {
            "method": "xgboost" if xgb_regressor is not None else "correlation",
            "metrics": metrics,
        }

    def _simple_importance_from_correlation(
        self,
        xs: np.ndarray,
        ys: np.ndarray,
        feature_names: list[str],
    ) -> list[tuple[str, float]]:
        importance: list[tuple[str, float]] = []
        for idx, name in enumerate(feature_names):
            values = xs[:, idx]
            if len(set(values)) <= 1:
                continue
            try:
                corr = float(np.corrcoef(values, ys)[0, 1])
            except Exception:
                continue
            if math.isnan(corr):
                continue
            importance.append((name, abs(corr)))
        return importance

    def _metric_names(self, vectors: list[dict[str, Any]]) -> list[str]:
        names = set()
        for vector in vectors:
            names.update(vector["metric_scores"].keys())
        return sorted(names)

    def _aligned_series(
        self,
        vectors: list[dict[str, Any]],
        metric: str,
        feature_names: list[str],
    ) -> tuple[dict[str, list[float]], dict[str, list[float]]]:
        xs: dict[str, list[float]] = {name: [] for name in feature_names}
        ys: dict[str, list[float]] = {name: [] for name in feature_names}
        for vector in vectors:
            score = vector["metric_scores"].get(metric)
            if score is None:
                continue
            for name in feature_names:
                xs[name].append(float(vector["features"].get(name, 0.0)))
                ys[name].append(float(score))
        return xs, ys

    def _aligned_matrix(
        self,
        vectors: list[dict[str, Any]],
        metric: str,
        feature_names: list[str],
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
        rows: list[list[float]] = []
        targets: list[float] = []
        for vector in vectors:
            score = vector["metric_scores"].get(metric)
            if score is None:
                continue
            rows.append([float(vector["features"].get(name, 0.0)) for name in feature_names])
            targets.append(float(score))
        if not rows:
            return None, None
        return np.array(rows, dtype=float), np.array(targets, dtype=float)

    def _extract_tokens(
        self,
        question: str,
        answer: str,
        ground_truth: str | None,
        contexts: list[str],
    ) -> list[str]:
        texts = [question, answer, ground_truth or ""] + [ctx for ctx in contexts if ctx]
        tokens: list[str] = []
        for text in texts:
            if self._tokenizer and _HANGUL_PATTERN.search(text):
                tokens.extend(self._tokenizer.extract_keywords(text))
            else:
                tokens.extend(_WORD_PATTERN.findall(text.lower()))
        return [t for t in tokens if t]

    def _build_entity_graph(
        self,
        vectors: list[dict[str, Any]],
        *,
        max_nodes: int,
        max_edges: int,
    ) -> dict[str, Any]:
        node_counts: Counter[str] = Counter()
        edge_counts: Counter[tuple[str, str]] = Counter()
        for vector in vectors:
            tokens = vector.get("tokens") or []
            unique_tokens = list({t for t in tokens if t})
            node_counts.update(unique_tokens)
            for left, right in itertools.combinations(sorted(unique_tokens), 2):
                edge_counts[(left, right)] += 1

        top_nodes = [node for node, _count in node_counts.most_common(max_nodes)]
        node_set = set(top_nodes)

        edges = [
            {"source": left, "target": right, "weight": count}
            for (left, right), count in edge_counts.most_common(max_edges)
            if left in node_set and right in node_set
        ]
        nodes = [{"id": node, "count": node_counts[node]} for node in top_nodes]
        return {
            "nodes": nodes,
            "edges": edges,
        }
