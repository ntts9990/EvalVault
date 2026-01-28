"""Analysis pipeline factory for CLI/API usage."""

from __future__ import annotations

from typing import TYPE_CHECKING

from evalvault.adapters.outbound import analysis as analysis_modules
from evalvault.ports.outbound.llm_port import LLMPort
from evalvault.ports.outbound.storage_port import StoragePort

if TYPE_CHECKING:
    from evalvault.domain.services.pipeline_orchestrator import AnalysisPipelineService


def build_analysis_pipeline_service(
    *,
    storage: StoragePort | None,
    llm_adapter: LLMPort | None,
) -> AnalysisPipelineService:
    """Register pipeline modules and return a service instance."""
    from evalvault.domain.services.pipeline_orchestrator import AnalysisPipelineService

    service = AnalysisPipelineService()

    service.register_module(analysis_modules.DataLoaderModule(storage=storage))
    service.register_module(analysis_modules.RunLoaderModule(storage=storage))
    service.register_module(analysis_modules.StatisticalAnalyzerModule())
    service.register_module(analysis_modules.NLPAnalyzerModule())
    service.register_module(analysis_modules.CausalAnalyzerModule())
    service.register_module(analysis_modules.SummaryReportModule())
    service.register_module(analysis_modules.DetailedReportModule())
    service.register_module(analysis_modules.AnalysisReportModule())
    service.register_module(analysis_modules.VerificationReportModule())
    service.register_module(analysis_modules.ComparisonReportModule())
    service.register_module(analysis_modules.LLMReportModule(llm_adapter=llm_adapter))
    service.register_module(analysis_modules.PrioritySummaryModule())

    service.register_module(analysis_modules.MorphemeAnalyzerModule())
    service.register_module(analysis_modules.MorphemeQualityCheckerModule())
    service.register_module(analysis_modules.EmbeddingAnalyzerModule())
    service.register_module(analysis_modules.EmbeddingDistributionModule())
    service.register_module(analysis_modules.RetrievalAnalyzerModule())
    service.register_module(analysis_modules.RetrievalBenchmarkModule())
    service.register_module(analysis_modules.RetrievalQualityCheckerModule())
    service.register_module(analysis_modules.BM25SearcherModule())
    service.register_module(analysis_modules.EmbeddingSearcherModule())
    service.register_module(analysis_modules.HybridRRFModule())
    service.register_module(analysis_modules.HybridWeightedModule())
    service.register_module(analysis_modules.SearchComparatorModule())
    service.register_module(analysis_modules.ModelAnalyzerModule())
    service.register_module(analysis_modules.RunAnalyzerModule())
    service.register_module(analysis_modules.StatisticalComparatorModule())
    service.register_module(analysis_modules.RunComparatorModule())
    service.register_module(analysis_modules.RunMetricComparatorModule())
    service.register_module(analysis_modules.RunChangeDetectorModule(storage=storage))
    service.register_module(analysis_modules.RagasEvaluatorModule(llm_adapter=llm_adapter))
    service.register_module(analysis_modules.LowPerformerExtractorModule())
    service.register_module(analysis_modules.DiagnosticPlaybookModule())
    service.register_module(analysis_modules.RootCauseAnalyzerModule())
    service.register_module(analysis_modules.PatternDetectorModule())
    service.register_module(analysis_modules.DatasetFeatureAnalyzerModule())
    service.register_module(analysis_modules.MultiTurnAnalyzerModule())
    service.register_module(analysis_modules.TimeSeriesAnalyzerModule())
    service.register_module(analysis_modules.TimeSeriesAdvancedModule())
    service.register_module(analysis_modules.TrendDetectorModule())
    service.register_module(analysis_modules.NetworkAnalyzerModule())
    service.register_module(analysis_modules.HypothesisGeneratorModule())

    return service
