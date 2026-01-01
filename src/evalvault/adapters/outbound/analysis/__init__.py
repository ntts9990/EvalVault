"""Analysis adapters.

Phase 2-3의 기존 분석 어댑터들과 Phase 14의 파이프라인 모듈 어댑터들입니다.
"""

# Phase 2-3: 기존 분석 어댑터
from evalvault.adapters.outbound.analysis.analysis_report_module import (
    AnalysisReportModule,
)

# Phase 14: 파이프라인 모듈 어댑터
from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.causal_adapter import CausalAnalysisAdapter
from evalvault.adapters.outbound.analysis.common import (
    AnalysisDataProcessor,
    BaseAnalysisAdapter,
)
from evalvault.adapters.outbound.analysis.comparison_report_module import (
    ComparisonReportModule,
)
from evalvault.adapters.outbound.analysis.data_loader_module import DataLoaderModule
from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter
from evalvault.adapters.outbound.analysis.statistical_adapter import (
    StatisticalAnalysisAdapter,
)
from evalvault.adapters.outbound.analysis.statistical_analyzer_module import (
    StatisticalAnalyzerModule,
)
from evalvault.adapters.outbound.analysis.summary_report_module import (
    SummaryReportModule,
)
from evalvault.adapters.outbound.analysis.verification_report_module import (
    VerificationReportModule,
)

__all__ = [
    # Phase 2-3
    "CausalAnalysisAdapter",
    "NLPAnalysisAdapter",
    "StatisticalAnalysisAdapter",
    "BaseAnalysisAdapter",
    "AnalysisDataProcessor",
    # Phase 14
    "BaseAnalysisModule",
    "DataLoaderModule",
    "StatisticalAnalyzerModule",
    "SummaryReportModule",
    "VerificationReportModule",
    "ComparisonReportModule",
    "AnalysisReportModule",
]
