"""Analysis metric registry for pipeline outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from evalvault.domain.metrics.registry import SignalGroup

AnalysisMetricSource = Literal[
    "retrieval_analyzer",
    "embedding_analyzer",
    "bm25_searcher",
    "embedding_searcher",
    "hybrid_rrf",
    "hybrid_weighted",
]


@dataclass(frozen=True)
class AnalysisMetricSpec:
    key: str
    label: str
    description: str
    signal_group: SignalGroup
    module_id: AnalysisMetricSource
    output_path: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "signal_group": self.signal_group,
            "module_id": self.module_id,
            "output_path": list(self.output_path),
        }


_ANALYSIS_METRICS: tuple[AnalysisMetricSpec, ...] = (
    AnalysisMetricSpec(
        key="retrieval.avg_contexts",
        label="Avg contexts per query",
        description="Average number of contexts retrieved per query",
        signal_group="retrieval_effectiveness",
        module_id="retrieval_analyzer",
        output_path=("summary", "avg_contexts"),
    ),
    AnalysisMetricSpec(
        key="retrieval.empty_context_rate",
        label="Empty context rate",
        description="Share of queries with empty contexts",
        signal_group="retrieval_effectiveness",
        module_id="retrieval_analyzer",
        output_path=("summary", "empty_context_rate"),
    ),
    AnalysisMetricSpec(
        key="retrieval.avg_context_tokens",
        label="Avg context tokens",
        description="Average token count across contexts",
        signal_group="retrieval_effectiveness",
        module_id="retrieval_analyzer",
        output_path=("summary", "avg_context_tokens"),
    ),
    AnalysisMetricSpec(
        key="retrieval.keyword_overlap",
        label="Keyword overlap",
        description="Keyword overlap between question and contexts",
        signal_group="retrieval_effectiveness",
        module_id="retrieval_analyzer",
        output_path=("summary", "avg_keyword_overlap"),
    ),
    AnalysisMetricSpec(
        key="retrieval.ground_truth_hit_rate",
        label="Ground truth hit rate",
        description="Share of cases where ground truth appears in contexts",
        signal_group="retrieval_effectiveness",
        module_id="retrieval_analyzer",
        output_path=("summary", "ground_truth_hit_rate"),
    ),
    AnalysisMetricSpec(
        key="retrieval.avg_faithfulness_proxy",
        label="Context faithfulness proxy",
        description="Proxy faithfulness from context-grounding check",
        signal_group="groundedness",
        module_id="retrieval_analyzer",
        output_path=("summary", "avg_faithfulness"),
    ),
    AnalysisMetricSpec(
        key="retrieval.avg_retrieval_score",
        label="Avg retrieval score",
        description="Average retrieval score from metadata",
        signal_group="retrieval_effectiveness",
        module_id="retrieval_analyzer",
        output_path=("summary", "avg_retrieval_score"),
    ),
    AnalysisMetricSpec(
        key="retrieval.avg_retrieval_time_ms",
        label="Avg retrieval latency (ms)",
        description="Average retrieval latency in milliseconds",
        signal_group="efficiency",
        module_id="retrieval_analyzer",
        output_path=("summary", "avg_retrieval_time_ms"),
    ),
    AnalysisMetricSpec(
        key="bm25.avg_recall_at_k",
        label="BM25 avg recall@k",
        description="Average recall@k for BM25 retrieval",
        signal_group="retrieval_effectiveness",
        module_id="bm25_searcher",
        output_path=("summary", "avg_recall_at_k"),
    ),
    AnalysisMetricSpec(
        key="bm25.avg_top_score",
        label="BM25 avg top score",
        description="Average top score for BM25 retrieval",
        signal_group="retrieval_effectiveness",
        module_id="bm25_searcher",
        output_path=("summary", "avg_top_score"),
    ),
    AnalysisMetricSpec(
        key="embedding.avg_recall_at_k",
        label="Embedding avg recall@k",
        description="Average recall@k for dense retrieval",
        signal_group="retrieval_effectiveness",
        module_id="embedding_searcher",
        output_path=("summary", "avg_recall_at_k"),
    ),
    AnalysisMetricSpec(
        key="embedding.avg_top_score",
        label="Embedding avg top score",
        description="Average top score for dense retrieval",
        signal_group="retrieval_effectiveness",
        module_id="embedding_searcher",
        output_path=("summary", "avg_top_score"),
    ),
    AnalysisMetricSpec(
        key="hybrid_rrf.avg_recall_at_k",
        label="Hybrid RRF avg recall@k",
        description="Average recall@k for RRF hybrid retrieval",
        signal_group="retrieval_effectiveness",
        module_id="hybrid_rrf",
        output_path=("summary", "avg_recall_at_k"),
    ),
    AnalysisMetricSpec(
        key="hybrid_rrf.avg_top_score",
        label="Hybrid RRF avg top score",
        description="Average top score for RRF hybrid retrieval",
        signal_group="retrieval_effectiveness",
        module_id="hybrid_rrf",
        output_path=("summary", "avg_top_score"),
    ),
    AnalysisMetricSpec(
        key="hybrid_weighted.avg_recall_at_k",
        label="Hybrid weighted avg recall@k",
        description="Average recall@k for weighted hybrid retrieval",
        signal_group="retrieval_effectiveness",
        module_id="hybrid_weighted",
        output_path=("summary", "avg_recall_at_k"),
    ),
    AnalysisMetricSpec(
        key="hybrid_weighted.avg_top_score",
        label="Hybrid weighted avg top score",
        description="Average top score for weighted hybrid retrieval",
        signal_group="retrieval_effectiveness",
        module_id="hybrid_weighted",
        output_path=("summary", "avg_top_score"),
    ),
    AnalysisMetricSpec(
        key="embedding.avg_norm",
        label="Embedding avg norm",
        description="Average embedding vector norm",
        signal_group="embedding_quality",
        module_id="embedding_analyzer",
        output_path=("summary", "avg_norm"),
    ),
    AnalysisMetricSpec(
        key="embedding.norm_std",
        label="Embedding norm std",
        description="Std-dev of embedding norms",
        signal_group="embedding_quality",
        module_id="embedding_analyzer",
        output_path=("summary", "norm_std"),
    ),
    AnalysisMetricSpec(
        key="embedding.norm_min",
        label="Embedding norm min",
        description="Minimum embedding norm",
        signal_group="embedding_quality",
        module_id="embedding_analyzer",
        output_path=("summary", "norm_min"),
    ),
    AnalysisMetricSpec(
        key="embedding.norm_max",
        label="Embedding norm max",
        description="Maximum embedding norm",
        signal_group="embedding_quality",
        module_id="embedding_analyzer",
        output_path=("summary", "norm_max"),
    ),
    AnalysisMetricSpec(
        key="embedding.mean_cosine_to_centroid",
        label="Embedding mean cosine",
        description="Mean cosine similarity to centroid",
        signal_group="embedding_quality",
        module_id="embedding_analyzer",
        output_path=("summary", "mean_cosine_to_centroid"),
    ),
)


def list_analysis_metric_specs() -> list[AnalysisMetricSpec]:
    return list(_ANALYSIS_METRICS)


def list_analysis_metric_keys() -> list[str]:
    return [spec.key for spec in _ANALYSIS_METRICS]
