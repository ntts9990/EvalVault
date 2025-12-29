"""Analysis adapters."""

from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter
from evalvault.adapters.outbound.analysis.statistical_adapter import (
    StatisticalAnalysisAdapter,
)

__all__ = [
    "NLPAnalysisAdapter",
    "StatisticalAnalysisAdapter",
]
