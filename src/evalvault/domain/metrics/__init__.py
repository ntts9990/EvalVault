"""Custom domain-specific metrics for RAG evaluation."""

from evalvault.domain.metrics.confidence import ConfidenceScore
from evalvault.domain.metrics.contextual_relevancy import ContextualRelevancy
from evalvault.domain.metrics.entity_preservation import EntityPreservation
from evalvault.domain.metrics.insurance import InsuranceTermAccuracy
from evalvault.domain.metrics.multiturn_metrics import (
    calculate_context_coherence,
    calculate_drift_rate,
    calculate_turn_faithfulness,
    calculate_turn_latency_p95,
)
from evalvault.domain.metrics.no_answer import NoAnswerAccuracy, is_no_answer
from evalvault.domain.metrics.retrieval_rank import MRR, NDCG, HitRate
from evalvault.domain.metrics.summary_accuracy import SummaryAccuracy
from evalvault.domain.metrics.summary_needs_followup import SummaryNeedsFollowup
from evalvault.domain.metrics.summary_non_definitive import SummaryNonDefinitive
from evalvault.domain.metrics.summary_risk_coverage import SummaryRiskCoverage
from evalvault.domain.metrics.text_match import ExactMatch, F1Score

__all__ = [
    "ConfidenceScore",
    "ContextualRelevancy",
    "EntityPreservation",
    "ExactMatch",
    "F1Score",
    "HitRate",
    "InsuranceTermAccuracy",
    "MRR",
    "NDCG",
    "NoAnswerAccuracy",
    "SummaryAccuracy",
    "SummaryNeedsFollowup",
    "SummaryNonDefinitive",
    "SummaryRiskCoverage",
    "is_no_answer",
    "calculate_context_coherence",
    "calculate_drift_rate",
    "calculate_turn_faithfulness",
    "calculate_turn_latency_p95",
]
