"""Domain entities."""

from evalvault.domain.entities.analysis import (
    AnalysisBundle,
    AnalysisResult,
    AnalysisType,
    ComparisonResult,
    CorrelationInsight,
    EffectSizeLevel,
    LowPerformerInfo,
    MetaAnalysisResult,
    MetricStats,
    StatisticalAnalysis,
)
from evalvault.domain.entities.dataset import Dataset, TestCase
from evalvault.domain.entities.experiment import Experiment, ExperimentGroup
from evalvault.domain.entities.kg import EntityModel, RelationModel
from evalvault.domain.entities.result import (
    EvaluationRun,
    MetricScore,
    MetricType,
    TestCaseResult,
)

__all__ = [
    # Analysis
    "AnalysisBundle",
    "AnalysisResult",
    "AnalysisType",
    "ComparisonResult",
    "CorrelationInsight",
    "EffectSizeLevel",
    "LowPerformerInfo",
    "MetaAnalysisResult",
    "MetricStats",
    "StatisticalAnalysis",
    # Dataset
    "Dataset",
    "TestCase",
    # Experiment
    "Experiment",
    "ExperimentGroup",
    # KG
    "EntityModel",
    "RelationModel",
    # Result
    "EvaluationRun",
    "MetricScore",
    "MetricType",
    "TestCaseResult",
]
