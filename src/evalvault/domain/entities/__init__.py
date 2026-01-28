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
from evalvault.domain.entities.feedback import (
    CalibrationCaseResult,
    CalibrationResult,
    CalibrationSummary,
    FeedbackSummary,
    SatisfactionFeedback,
)
from evalvault.domain.entities.graph_rag import EntityNode, KnowledgeSubgraph, RelationEdge
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
from evalvault.domain.entities.judge_calibration import (
    JudgeCalibrationCase,
    JudgeCalibrationMetric,
    JudgeCalibrationResult,
    JudgeCalibrationSummary,
)
from evalvault.domain.entities.kg import EntityModel, RelationModel
from evalvault.domain.entities.method import MethodInput, MethodInputDataset, MethodOutput
from evalvault.domain.entities.multiturn import (
    ConversationTurn,
    DriftAnalysis,
    MultiTurnConversationRecord,
    MultiTurnEvaluationResult,
    MultiTurnRunRecord,
    MultiTurnTestCase,
    MultiTurnTurnResult,
)
from evalvault.domain.entities.prompt import Prompt, PromptSet, PromptSetBundle, PromptSetItem
from evalvault.domain.entities.prompt_suggestion import (
    PromptCandidate,
    PromptCandidateSampleScore,
    PromptCandidateScore,
    PromptSuggestionResult,
)
from evalvault.domain.entities.rag_trace import (
    GenerationData,
    RAGTraceData,
    RerankMethod,
    RetrievalData,
    RetrievalMethod,
    RetrievedDocument,
)
from evalvault.domain.entities.result import (
    ClaimLevelResult,
    ClaimVerdict,
    EvaluationRun,
    MetricScore,
    MetricType,
    RunClusterMap,
    RunClusterMapInfo,
    TestCaseResult,
)
from evalvault.domain.entities.stage import (
    REQUIRED_STAGE_TYPES,
    StageEvent,
    StageMetric,
    StagePayloadRef,
    StageSummary,
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
    "CalibrationCaseResult",
    "CalibrationResult",
    "CalibrationSummary",
    "FeedbackSummary",
    "SatisfactionFeedback",
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
    "JudgeCalibrationCase",
    "JudgeCalibrationMetric",
    "JudgeCalibrationResult",
    "JudgeCalibrationSummary",
    "ConversationTurn",
    "MultiTurnConversationRecord",
    "MultiTurnTestCase",
    "MultiTurnTurnResult",
    "MultiTurnEvaluationResult",
    "DriftAnalysis",
    "MultiTurnRunRecord",
    "EntityNode",
    "KnowledgeSubgraph",
    "RelationEdge",
    # KG
    "EntityModel",
    "RelationModel",
    # Method
    "MethodInput",
    "MethodInputDataset",
    "MethodOutput",
    # Prompt
    "Prompt",
    "PromptSet",
    "PromptSetBundle",
    "PromptSetItem",
    "PromptCandidate",
    "PromptCandidateSampleScore",
    "PromptCandidateScore",
    "PromptSuggestionResult",
    # RAG Trace
    "GenerationData",
    "RAGTraceData",
    "RerankMethod",
    "RetrievalData",
    "RetrievalMethod",
    "RetrievedDocument",
    # Stage
    "REQUIRED_STAGE_TYPES",
    "StageEvent",
    "StageMetric",
    "StagePayloadRef",
    "StageSummary",
    # Result
    "ClaimLevelResult",
    "ClaimVerdict",
    "EvaluationRun",
    "MetricScore",
    "MetricType",
    "RunClusterMap",
    "RunClusterMapInfo",
    "TestCaseResult",
]
