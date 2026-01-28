"""Metric registry for CLI/Web UI integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MetricSource = Literal["ragas", "custom"]
MetricCategory = Literal["qa", "summary", "retrieval", "domain"]
SignalGroup = Literal[
    "groundedness",
    "intent_alignment",
    "retrieval_effectiveness",
    "summary_fidelity",
    "embedding_quality",
    "efficiency",
]


@dataclass(frozen=True)
class MetricSpec:
    name: str
    description: str
    requires_ground_truth: bool
    requires_embeddings: bool
    source: MetricSource
    category: MetricCategory
    signal_group: SignalGroup

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "requires_ground_truth": self.requires_ground_truth,
            "requires_embeddings": self.requires_embeddings,
            "source": self.source,
            "category": self.category,
            "signal_group": self.signal_group,
        }


_METRIC_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec(
        name="faithfulness",
        description="Measures factual accuracy of the answer based on contexts",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="ragas",
        category="qa",
        signal_group="groundedness",
    ),
    MetricSpec(
        name="answer_relevancy",
        description="Measures how relevant the answer is to the question",
        requires_ground_truth=False,
        requires_embeddings=True,
        source="ragas",
        category="qa",
        signal_group="intent_alignment",
    ),
    MetricSpec(
        name="context_precision",
        description="Measures ranking quality of retrieved contexts",
        requires_ground_truth=True,
        requires_embeddings=False,
        source="ragas",
        category="qa",
        signal_group="retrieval_effectiveness",
    ),
    MetricSpec(
        name="context_recall",
        description="Measures if all relevant info is in retrieved contexts",
        requires_ground_truth=True,
        requires_embeddings=False,
        source="ragas",
        category="qa",
        signal_group="retrieval_effectiveness",
    ),
    MetricSpec(
        name="factual_correctness",
        description="Measures factual correctness against ground truth",
        requires_ground_truth=True,
        requires_embeddings=False,
        source="ragas",
        category="qa",
        signal_group="groundedness",
    ),
    MetricSpec(
        name="semantic_similarity",
        description="Measures semantic similarity between answer and ground truth",
        requires_ground_truth=True,
        requires_embeddings=True,
        source="ragas",
        category="qa",
        signal_group="intent_alignment",
    ),
    MetricSpec(
        name="mrr",
        description="Measures reciprocal rank of the first relevant context",
        requires_ground_truth=True,
        requires_embeddings=False,
        source="custom",
        category="retrieval",
        signal_group="retrieval_effectiveness",
    ),
    MetricSpec(
        name="ndcg",
        description="Measures ranking quality across relevant contexts",
        requires_ground_truth=True,
        requires_embeddings=False,
        source="custom",
        category="retrieval",
        signal_group="retrieval_effectiveness",
    ),
    MetricSpec(
        name="hit_rate",
        description="Measures whether any relevant context appears in top K",
        requires_ground_truth=True,
        requires_embeddings=False,
        source="custom",
        category="retrieval",
        signal_group="retrieval_effectiveness",
    ),
    MetricSpec(
        name="summary_score",
        description="(LLM) Measures summary coverage and conciseness against contexts",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="ragas",
        category="summary",
        signal_group="summary_fidelity",
    ),
    MetricSpec(
        name="summary_faithfulness",
        description="(LLM) Measures whether summary statements are grounded in contexts",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="ragas",
        category="summary",
        signal_group="summary_fidelity",
    ),
    MetricSpec(
        name="turn_faithfulness",
        description="(Multi-turn) Average faithfulness across assistant turns",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="custom",
        category="qa",
        signal_group="groundedness",
    ),
    MetricSpec(
        name="context_coherence",
        description="(Multi-turn) Context continuity across turns",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="custom",
        category="qa",
        signal_group="intent_alignment",
    ),
    MetricSpec(
        name="drift_rate",
        description="(Multi-turn) Distance between initial intent and final response",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="custom",
        category="qa",
        signal_group="intent_alignment",
    ),
    MetricSpec(
        name="turn_latency",
        description="(Multi-turn) P95 response latency across turns (ms)",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="custom",
        category="qa",
        signal_group="efficiency",
    ),
    MetricSpec(
        name="entity_preservation",
        description="(Rule) Measures preservation of key insurance entities in summaries",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="custom",
        category="summary",
        signal_group="summary_fidelity",
    ),
    MetricSpec(
        name="summary_accuracy",
        description="(Rule) Measures whether summary entities are grounded in contexts",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="custom",
        category="summary",
        signal_group="summary_fidelity",
    ),
    MetricSpec(
        name="summary_risk_coverage",
        description="(Rule) Measures coverage of expected insurance risk tags in summaries",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="custom",
        category="summary",
        signal_group="summary_fidelity",
    ),
    MetricSpec(
        name="summary_non_definitive",
        description="(Rule) Measures avoidance of definitive claims in summaries",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="custom",
        category="summary",
        signal_group="summary_fidelity",
    ),
    MetricSpec(
        name="summary_needs_followup",
        description="(Rule) Measures follow-up guidance when required",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="custom",
        category="summary",
        signal_group="summary_fidelity",
    ),
    MetricSpec(
        name="insurance_term_accuracy",
        description="Measures if insurance terms in answer are grounded in contexts",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="custom",
        category="domain",
        signal_group="groundedness",
    ),
    MetricSpec(
        name="contextual_relevancy",
        description="Measures how well contexts align with the question intent",
        requires_ground_truth=False,
        requires_embeddings=False,
        source="custom",
        category="qa",
        signal_group="retrieval_effectiveness",
    ),
)


def list_metric_specs() -> list[MetricSpec]:
    return list(_METRIC_SPECS)


def list_metric_names() -> list[str]:
    return [spec.name for spec in _METRIC_SPECS]


def get_metric_descriptions() -> dict[str, str]:
    return {spec.name: spec.description for spec in _METRIC_SPECS}


def get_metric_spec_map() -> dict[str, MetricSpec]:
    return {spec.name: spec for spec in _METRIC_SPECS}
