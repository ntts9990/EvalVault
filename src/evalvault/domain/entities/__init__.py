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
from evalvault.domain.entities.improvement import (
    EffortLevel,
    EvidenceSource,
    FailureSample,
    ImprovementAction,
    ImprovementEvidence,
    ImprovementPriority,
    ImprovementReport,
    PatternEvidence,
    PatternType,
    RAGComponent,
    RAGImprovementGuide,
)
from evalvault.domain.entities.kg import EntityModel, RelationModel
from evalvault.domain.entities.rag_trace import (
    GenerationData,
    RAGTraceData,
    RerankMethod,
    RetrievalData,
    RetrievalMethod,
    RetrievedDocument,
)
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
    # Improvement
    "EffortLevel",
    "EvidenceSource",
    "FailureSample",
    "ImprovementAction",
    "ImprovementEvidence",
    "ImprovementPriority",
    "ImprovementReport",
    "PatternEvidence",
    "PatternType",
    "RAGComponent",
    "RAGImprovementGuide",
    # KG
    "EntityModel",
    "RelationModel",
    # RAG Trace
    "GenerationData",
    "RAGTraceData",
    "RerankMethod",
    "RetrievalData",
    "RetrievalMethod",
    "RetrievedDocument",
    # Result
    "EvaluationRun",
    "MetricScore",
    "MetricType",
    "TestCaseResult",
]
