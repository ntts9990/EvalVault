"""Phase 14.4: Analysis Module Adapters 단위 테스트.

TDD Red Phase - 테스트 먼저 작성.
"""

from __future__ import annotations

from unittest.mock import MagicMock

# =============================================================================
# BaseAnalysisModule Tests
# =============================================================================


class TestBaseAnalysisModule:
    """BaseAnalysisModule 테스트 - 분석 모듈 기본 클래스."""

    def test_base_module_has_module_id(self):
        """module_id 속성 존재."""
        from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule

        class TestModule(BaseAnalysisModule):
            module_id = "test_module"
            name = "Test Module"
            description = "테스트 모듈"
            input_types = ["input"]
            output_types = ["output"]

            def execute(self, inputs, params=None):
                return {}

        module = TestModule()
        assert module.module_id == "test_module"

    def test_base_module_has_metadata(self):
        """metadata 속성 존재."""
        from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
        from evalvault.domain.entities.analysis_pipeline import ModuleMetadata

        class TestModule(BaseAnalysisModule):
            module_id = "test_module"
            name = "Test Module"
            description = "테스트 모듈"
            input_types = ["input"]
            output_types = ["output"]

            def execute(self, inputs, params=None):
                return {}

        module = TestModule()
        assert isinstance(module.metadata, ModuleMetadata)
        assert module.metadata.module_id == "test_module"
        assert module.metadata.name == "Test Module"

    def test_base_module_validate_inputs_default(self):
        """validate_inputs 기본 구현."""
        from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule

        class TestModule(BaseAnalysisModule):
            module_id = "test"
            name = "Test"
            description = "Test"
            input_types = []
            output_types = []

            def execute(self, inputs, params=None):
                return {}

        module = TestModule()
        assert module.validate_inputs({}) is True
        assert module.validate_inputs({"any": "data"}) is True


# =============================================================================
# DataLoaderModule Tests
# =============================================================================


class TestDataLoaderModule:
    """DataLoaderModule 테스트 - 데이터 로드 모듈."""

    def test_module_id(self):
        """모듈 ID 확인."""
        from evalvault.adapters.outbound.analysis.data_loader_module import (
            DataLoaderModule,
        )

        module = DataLoaderModule()
        assert module.module_id == "data_loader"

    def test_execute_with_context(self):
        """컨텍스트에서 데이터 로드."""
        from evalvault.adapters.outbound.analysis.data_loader_module import (
            DataLoaderModule,
        )

        module = DataLoaderModule()
        inputs = {
            "__context__": {
                "query": "테스트 쿼리",
                "run_id": "run-123",
            }
        }

        result = module.execute(inputs)

        assert result["loaded"] is True
        assert result["query"] == "테스트 쿼리"
        assert "metrics" in result
        assert "faithfulness" in result["metrics"]

    def test_execute_with_run_id(self):
        """run_id가 있을 때 결과에 포함."""
        from evalvault.adapters.outbound.analysis.data_loader_module import (
            DataLoaderModule,
        )

        module = DataLoaderModule()
        inputs = {
            "__context__": {
                "query": "분석해줘",
                "run_id": "run-456",
            }
        }

        result = module.execute(inputs)

        assert result["run_id"] == "run-456"

    def test_execute_loads_run_from_storage(self):
        """StoragePort에서 EvaluationRun 로드."""
        from evalvault.adapters.outbound.analysis.data_loader_module import (
            DataLoaderModule,
        )
        from evalvault.domain.entities import EvaluationRun
        from evalvault.domain.entities.result import MetricScore, TestCaseResult

        run = EvaluationRun(
            run_id="run-storage-1",
            metrics_evaluated=["faithfulness"],
        )
        run.results.append(
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="faithfulness", score=0.9)],
            )
        )

        class DummyStorage:
            def get_run(self, run_id: str) -> EvaluationRun:
                assert run_id == "run-storage-1"
                return run

        module = DataLoaderModule(storage=DummyStorage())
        inputs = {
            "__context__": {
                "query": "분석",
                "run_id": "run-storage-1",
            }
        }

        result = module.execute(inputs)

        assert result["run"] is run
        assert "summary" in result
        assert result["summary"]["run_id"] == "run-storage-1"
        assert result["metrics"]["faithfulness"] == [0.9]


# =============================================================================
# StatisticalAnalyzerModule Tests
# =============================================================================


class TestStatisticalAnalyzerModule:
    """StatisticalAnalyzerModule 테스트 - 통계 분석 모듈."""

    def test_module_id(self):
        """모듈 ID 확인."""
        from evalvault.adapters.outbound.analysis.statistical_analyzer_module import (
            StatisticalAnalyzerModule,
        )

        module = StatisticalAnalyzerModule()
        assert module.module_id == "statistical_analyzer"

    def test_execute_with_data(self):
        """데이터로 통계 분석."""
        from evalvault.adapters.outbound.analysis.statistical_analyzer_module import (
            StatisticalAnalyzerModule,
        )

        module = StatisticalAnalyzerModule()
        inputs = {
            "__context__": {"query": "분석"},
            "data_loader": {
                "loaded": True,
                "metrics": {
                    "faithfulness": [0.8, 0.9, 0.7, 0.85],
                    "answer_relevancy": [0.75, 0.8, 0.85, 0.9],
                },
            },
        }

        result = module.execute(inputs)

        assert "statistics" in result
        assert "summary" in result

    def test_execute_calculates_mean(self):
        """평균 계산."""
        from evalvault.adapters.outbound.analysis.statistical_analyzer_module import (
            StatisticalAnalyzerModule,
        )

        module = StatisticalAnalyzerModule()
        inputs = {
            "__context__": {"query": "분석"},
            "data_loader": {
                "loaded": True,
                "metrics": {
                    "faithfulness": [0.8, 0.8, 0.8, 0.8],
                },
            },
        }

        result = module.execute(inputs)

        assert result["statistics"]["faithfulness"]["mean"] == 0.8

    def test_execute_with_evaluation_run(self):
        """EvaluationRun을 사용해 어댑터 분석."""
        from evalvault.adapters.outbound.analysis.statistical_analyzer_module import (
            StatisticalAnalyzerModule,
        )
        from evalvault.domain.entities import EvaluationRun
        from evalvault.domain.entities.analysis import StatisticalAnalysis
        from evalvault.domain.entities.result import MetricScore, TestCaseResult

        run = EvaluationRun(
            run_id="run-001",
            metrics_evaluated=["faithfulness", "answer_relevancy"],
        )
        run.results = [
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[
                    MetricScore(name="faithfulness", score=0.9),
                    MetricScore(name="answer_relevancy", score=0.85),
                ],
            ),
            TestCaseResult(
                test_case_id="tc-2",
                metrics=[
                    MetricScore(name="faithfulness", score=0.4, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.6),
                ],
            ),
        ]

        module = StatisticalAnalyzerModule()
        result = module.execute(
            {
                "__context__": {"query": "분석"},
                "data_loader": {"run": run},
            }
        )

        assert result["summary"]["total_metrics"] == 2
        assert "faithfulness" in result["statistics"]
        assert "analysis" in result
        assert isinstance(result["analysis"], StatisticalAnalysis)
        assert result["low_performers"], "낮은 성능 케이스 정보가 포함되어야 함"
        assert result["low_performers"][0]["test_case_id"] == "tc-2"
        assert result["insights"], "생성된 인사이트가 포함되어야 함"


# =============================================================================
# SummaryReportModule Tests
# =============================================================================


class TestSummaryReportModule:
    """SummaryReportModule 테스트 - 요약 보고서 모듈."""

    def test_module_id(self):
        """모듈 ID 확인."""
        from evalvault.adapters.outbound.analysis.summary_report_module import (
            SummaryReportModule,
        )

        module = SummaryReportModule()
        assert module.module_id == "summary_report"

    def test_execute_generates_report(self):
        """보고서 생성."""
        from evalvault.adapters.outbound.analysis.summary_report_module import (
            SummaryReportModule,
        )

        module = SummaryReportModule()
        inputs = {
            "__context__": {"query": "요약해줘"},
            "statistical_analyzer": {
                "statistics": {
                    "faithfulness": {"mean": 0.85, "std": 0.05},
                    "answer_relevancy": {"mean": 0.82, "std": 0.08},
                },
                "summary": {
                    "total_metrics": 2,
                    "average_score": 0.835,
                },
            },
        }

        result = module.execute(inputs)

        assert "report" in result
        assert "format" in result
        assert result["format"] == "markdown"

    def test_execute_report_contains_statistics(self):
        """보고서에 통계 포함."""
        from evalvault.adapters.outbound.analysis.summary_report_module import (
            SummaryReportModule,
        )

        module = SummaryReportModule()
        inputs = {
            "__context__": {"query": "요약해줘"},
            "statistical_analyzer": {
                "statistics": {
                    "faithfulness": {"mean": 0.9, "std": 0.02},
                },
                "summary": {
                    "total_metrics": 1,
                    "average_score": 0.9,
                },
            },
        }

        result = module.execute(inputs)

        assert "faithfulness" in result["report"] or "0.9" in result["report"]

    def test_execute_includes_insights_and_low_performers(self):
        """인사이트/저성과 케이스 섹션과 analysis 객체 전달 확인."""
        from evalvault.adapters.outbound.analysis.summary_report_module import (
            SummaryReportModule,
        )
        from evalvault.domain.entities.analysis import StatisticalAnalysis

        analysis = StatisticalAnalysis(run_id="run-456", overall_pass_rate=0.62)

        module = SummaryReportModule()
        inputs = {
            "__context__": {"query": "요약해줘"},
            "statistical_analyzer": {
                "statistics": {
                    "faithfulness": {"mean": 0.45, "std": 0.1, "min": 0.2, "max": 0.8},
                },
                "summary": {
                    "total_metrics": 1,
                    "average_score": 0.45,
                    "overall_pass_rate": 0.62,
                },
                "insights": ["Low pass rate requires attention: 62.0%"],
                "metric_pass_rates": {"faithfulness": 0.4},
                "low_performers": [
                    {
                        "test_case_id": "tc-low",
                        "metric_name": "faithfulness",
                        "score": 0.2,
                        "threshold": 0.7,
                    }
                ],
                "analysis": analysis,
            },
        }

        result = module.execute(inputs)

        assert "주의가 필요한 테스트 케이스" in result["report"]
        assert "Low pass rate requires attention" in result["report"]
        assert "tc-low" in result["report"]
        assert result["low_performers"]
        assert result["analysis"] is analysis


# =============================================================================
# NLPAnalyzerModule Tests
# =============================================================================


class TestNLPAnalyzerModule:
    """NLPAnalyzerModule 테스트 - NLP 분석 모듈."""

    def test_execute_with_run(self):
        """EvaluationRun이 주어졌을 때 어댑터 호출."""
        from evalvault.adapters.outbound.analysis.nlp_analyzer_module import (
            NLPAnalyzerModule,
        )
        from evalvault.domain.entities import EvaluationRun
        from evalvault.domain.entities.analysis import (
            KeywordInfo,
            NLPAnalysis,
            QuestionType,
            QuestionTypeStats,
            TextStats,
            TopicCluster,
        )

        mock_adapter = MagicMock()
        analysis = NLPAnalysis(
            run_id="run-42",
            question_stats=TextStats(
                char_count=100,
                word_count=20,
                sentence_count=2,
                avg_word_length=4.0,
                unique_word_ratio=0.75,
            ),
            question_types=[
                QuestionTypeStats(
                    question_type=QuestionType.FACTUAL,
                    count=5,
                    percentage=0.5,
                )
            ],
            top_keywords=[KeywordInfo(keyword="보험", frequency=3, tfidf_score=0.9)],
            topic_clusters=[TopicCluster(cluster_id=1, keywords=["보험"], document_count=10)],
            insights=["확률형 질문 비중이 높음"],
        )
        mock_adapter.analyze.return_value = analysis

        module = NLPAnalyzerModule(adapter=mock_adapter)
        run = EvaluationRun(run_id="run-42")
        inputs = {"__context__": {"query": "패턴 분석"}, "data_loader": {"run": run}}

        result = module.execute(inputs)

        assert result["analysis"] is analysis
        assert result["insights"] == ["확률형 질문 비중이 높음"]
        assert result["summary"]["run_id"] == "run-42"
        assert result["question_types"][0]["question_type"] == QuestionType.FACTUAL.value
        assert "statistics" in result
        assert result["statistics"]["text_stats"]["questions"]["char_count"] == 100
        assert "question_stats_preview" in result["summary"]
        mock_adapter.analyze.assert_called_once()

    def test_execute_without_run_returns_empty(self):
        """run 정보가 없으면 빈 결과."""
        from evalvault.adapters.outbound.analysis.nlp_analyzer_module import (
            NLPAnalyzerModule,
        )

        module = NLPAnalyzerModule(adapter=MagicMock())
        result = module.execute({"__context__": {}, "data_loader": {}})

        assert result["analysis"] is None
        assert result["insights"] == []
        assert result["summary"] == {}
        assert result["statistics"] == {}


# =============================================================================
# CausalAnalyzerModule Tests
# =============================================================================


class TestCausalAnalyzerModule:
    """CausalAnalyzerModule 테스트 - 인과 분석 모듈."""

    def test_execute_with_run(self):
        """EvaluationRun이 주어졌을 때 인과 분석 수행."""
        from evalvault.adapters.outbound.analysis.causal_analyzer_module import (
            CausalAnalyzerModule,
        )
        from evalvault.domain.entities import EvaluationRun
        from evalvault.domain.entities.analysis import (
            CausalAnalysis,
            CausalFactorType,
            FactorImpact,
            FactorStats,
            ImpactDirection,
            ImpactStrength,
            InterventionSuggestion,
            RootCause,
            StratifiedGroup,
        )

        mock_adapter = MagicMock()
        analysis = CausalAnalysis(run_id="run-99")
        analysis.factor_stats = {
            CausalFactorType.QUESTION_LENGTH: FactorStats(
                factor_type=CausalFactorType.QUESTION_LENGTH,
                mean=10,
                std=2,
                min=6,
                max=15,
                median=9,
            )
        }
        analysis.factor_impacts = [
            FactorImpact(
                factor_type=CausalFactorType.QUESTION_LENGTH,
                metric_name="faithfulness",
                direction=ImpactDirection.NEGATIVE,
                strength=ImpactStrength.MODERATE,
                correlation=-0.45,
                p_value=0.01,
                is_significant=True,
                effect_size=0.5,
                stratified_groups=[
                    StratifiedGroup(
                        group_name="long",
                        lower_bound=12,
                        upper_bound=20,
                        count=5,
                        avg_scores={"faithfulness": 0.6},
                    )
                ],
                interpretation="긴 질문에서 충실도가 떨어짐",
            )
        ]
        analysis.root_causes = [
            RootCause(
                metric_name="faithfulness",
                primary_causes=[CausalFactorType.QUESTION_LENGTH],
                contributing_factors=[],
                explanation="질문 길이 증가가 주요 원인",
            )
        ]
        analysis.interventions = [
            InterventionSuggestion(
                target_metric="faithfulness",
                intervention="긴 질문 분리",
                expected_impact="+0.05",
                related_factors=[CausalFactorType.QUESTION_LENGTH],
            )
        ]
        analysis.insights = ["긴 질문에서 오류 비중 증가"]
        mock_adapter.analyze.return_value = analysis

        module = CausalAnalyzerModule(adapter=mock_adapter)
        run = EvaluationRun(run_id="run-99")
        inputs = {"__context__": {"query": "원인 분석"}, "data_loader": {"run": run}}

        result = module.execute(inputs)

        assert result["analysis"] is analysis
        assert result["factor_stats"]["question_length"]["mean"] == 10
        assert result["significant_impacts"][0]["metric_name"] == "faithfulness"
        assert result["insights"] == ["긴 질문에서 오류 비중 증가"]
        assert result["statistics"]["factor_stats"]["question_length"]["mean"] == 10
        assert result["statistics"]["significant_impacts"][0]["metric_name"] == "faithfulness"
        mock_adapter.analyze.assert_called_once()

    def test_execute_without_run_returns_empty(self):
        """run 정보가 없으면 빈 결과."""
        from evalvault.adapters.outbound.analysis.causal_analyzer_module import (
            CausalAnalyzerModule,
        )

        module = CausalAnalyzerModule(adapter=MagicMock())
        result = module.execute({"__context__": {}, "data_loader": {}})

        assert result["analysis"] is None
        assert result["insights"] == []
        assert result["summary"] == {}
        assert result["statistics"] == {}


# =============================================================================
# DiagnosticPlaybookModule Tests
# =============================================================================


class TestDiagnosticPlaybookModule:
    """DiagnosticPlaybookModule 테스트 - 진단 플레이북 모듈."""

    def test_execute_uses_run_thresholds(self):
        """run threshold를 우선 적용."""
        from evalvault.adapters.outbound.analysis.diagnostic_playbook_module import (
            DiagnosticPlaybookModule,
        )
        from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult

        run = EvaluationRun(
            run_id="run-1",
            thresholds={"faithfulness": 0.8},
            results=[
                TestCaseResult(
                    test_case_id="tc-1",
                    metrics=[MetricScore(name="faithfulness", score=0.75, threshold=0.8)],
                )
            ],
        )

        module = DiagnosticPlaybookModule()
        inputs = {
            "load_data": {"run": run},
            "ragas_eval": {"metrics": {"faithfulness": 0.75}},
        }

        result = module.execute(inputs)

        assert result["diagnostics"][0]["threshold"] == 0.8
        assert result["diagnostics"][0]["gap"] == 0.05
        assert result["recommendations"]

    def test_execute_fallback_threshold(self):
        """run 정보가 없으면 기본 threshold 사용."""
        from evalvault.adapters.outbound.analysis.diagnostic_playbook_module import (
            DiagnosticPlaybookModule,
        )

        module = DiagnosticPlaybookModule()
        inputs = {"ragas_eval": {"metrics": {"faithfulness": 0.55}}}

        result = module.execute(inputs, params={"metric_threshold": 0.6})

        assert result["diagnostics"][0]["threshold"] == 0.6
        assert result["threshold"] == 0.6

    def test_execute_summary_faithfulness_hint(self):
        """요약 메트릭 힌트 적용."""
        from evalvault.adapters.outbound.analysis.diagnostic_playbook_module import (
            DiagnosticPlaybookModule,
        )
        from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult

        run = EvaluationRun(
            run_id="run-summary",
            thresholds={"summary_faithfulness": 0.9},
            results=[
                TestCaseResult(
                    test_case_id="tc-1",
                    metrics=[MetricScore(name="summary_faithfulness", score=0.5, threshold=0.9)],
                )
            ],
        )

        module = DiagnosticPlaybookModule()
        inputs = {
            "load_data": {"run": run},
            "ragas_eval": {"metrics": {"summary_faithfulness": 0.5}},
        }

        result = module.execute(inputs)

        assert result["diagnostics"][0]["threshold"] == 0.9
        assert any("요약 근거" in rec for rec in result["recommendations"])


# =============================================================================
# RetrievalBenchmarkModule Tests
# =============================================================================


class TestRetrievalBenchmarkModule:
    """RetrievalBenchmarkModule 테스트 - 검색 벤치마크 모듈."""

    def test_execute_requires_path(self):
        """benchmark_path 없으면 에러."""
        from evalvault.adapters.outbound.analysis.retrieval_benchmark_module import (
            RetrievalBenchmarkModule,
        )

        module = RetrievalBenchmarkModule()
        result = module.execute({"__context__": {}})

        assert result["available"] is False
        assert "benchmark_path" in result["error"]

    def test_execute_invalid_path(self):
        """존재하지 않는 경로면 에러."""
        from evalvault.adapters.outbound.analysis.retrieval_benchmark_module import (
            RetrievalBenchmarkModule,
        )

        module = RetrievalBenchmarkModule()
        result = module.execute(
            {"__context__": {}},
            params={"benchmark_path": "not-found.json"},
        )

        assert result["available"] is False
        assert "벤치마크 파일" in result["error"]


# =============================================================================
# VerificationReportModule Tests
# =============================================================================


class TestVerificationReportModule:
    """VerificationReportModule 테스트 - 검증 보고서 모듈."""

    def test_module_id(self):
        """모듈 ID 확인."""
        from evalvault.adapters.outbound.analysis.verification_report_module import (
            VerificationReportModule,
        )

        module = VerificationReportModule()
        assert module.module_id == "verification_report"

    def test_execute_generates_verification_report(self):
        """검증 보고서 생성."""
        from evalvault.adapters.outbound.analysis.verification_report_module import (
            VerificationReportModule,
        )

        module = VerificationReportModule()
        inputs = {
            "__context__": {"query": "형태소 분석 확인"},
            "quality_check": {
                "passed": True,
                "checks": [
                    {"name": "토큰화", "status": "pass"},
                    {"name": "품사 태깅", "status": "pass"},
                ],
            },
        }

        result = module.execute(inputs)

        assert "report" in result
        assert "verification_status" in result
        assert result["verification_status"] == "passed"


# =============================================================================
# ComparisonReportModule Tests
# =============================================================================


class TestComparisonReportModule:
    """ComparisonReportModule 테스트 - 비교 보고서 모듈."""

    def test_module_id(self):
        """모듈 ID 확인."""
        from evalvault.adapters.outbound.analysis.comparison_report_module import (
            ComparisonReportModule,
        )

        module = ComparisonReportModule()
        assert module.module_id == "comparison_report"

    def test_execute_generates_comparison_report(self):
        """비교 보고서 생성."""
        from evalvault.adapters.outbound.analysis.comparison_report_module import (
            ComparisonReportModule,
        )

        module = ComparisonReportModule()
        inputs = {
            "__context__": {"query": "비교해줘"},
            "comparison": {
                "method_a": {"score": 0.85},
                "method_b": {"score": 0.78},
                "winner": "method_a",
            },
        }

        result = module.execute(inputs)

        assert "report" in result
        assert "comparison_summary" in result


# =============================================================================
# AnalysisReportModule Tests
# =============================================================================


class TestAnalysisReportModule:
    """AnalysisReportModule 테스트 - 분석 보고서 모듈."""

    def test_module_id(self):
        """모듈 ID 확인."""
        from evalvault.adapters.outbound.analysis.analysis_report_module import (
            AnalysisReportModule,
        )

        module = AnalysisReportModule()
        assert module.module_id == "analysis_report"

    def test_execute_generates_analysis_report(self):
        """분석 보고서 생성."""
        from evalvault.adapters.outbound.analysis.analysis_report_module import (
            AnalysisReportModule,
        )

        module = AnalysisReportModule()
        inputs = {
            "__context__": {"query": "낮은 메트릭 원인 분석"},
            "root_cause": {
                "causes": [
                    {"metric": "faithfulness", "reason": "컨텍스트 부족"},
                ],
                "recommendations": ["컨텍스트 보강 필요"],
            },
        }

        result = module.execute(inputs)

        assert "report" in result
        assert "analysis_summary" in result


# =============================================================================
# ModuleRegistry Integration Tests
# =============================================================================


class TestModuleRegistryIntegration:
    """모듈 레지스트리 통합 테스트."""

    def test_register_all_basic_modules(self):
        """기본 모듈들 등록."""
        from evalvault.adapters.outbound.analysis import (
            DataLoaderModule,
            StatisticalAnalyzerModule,
            SummaryReportModule,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        # 기본 모듈들 등록
        orchestrator.register_module(DataLoaderModule())
        orchestrator.register_module(StatisticalAnalyzerModule())
        orchestrator.register_module(SummaryReportModule())

        assert orchestrator.get_module("data_loader") is not None
        assert orchestrator.get_module("statistical_analyzer") is not None
        assert orchestrator.get_module("summary_report") is not None

    def test_execute_summary_pipeline_with_real_modules(self):
        """실제 모듈로 요약 파이프라인 실행."""
        from evalvault.adapters.outbound.analysis import (
            DataLoaderModule,
            StatisticalAnalyzerModule,
            SummaryReportModule,
        )
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            AnalysisPipelineService,
        )

        service = AnalysisPipelineService()

        # 모듈 등록
        service.register_module(DataLoaderModule())
        service.register_module(StatisticalAnalyzerModule())
        service.register_module(SummaryReportModule())

        # 파이프라인 실행
        result = service.analyze("결과를 요약해줘")

        assert result is not None
        assert result.is_complete
        assert result.intent == AnalysisIntent.GENERATE_SUMMARY


# =============================================================================
# RunChangeDetectorModule Tests
# =============================================================================


class TestRunChangeDetectorModule:
    """RunChangeDetectorModule 테스트."""

    def test_compare_summary_only_prompt_changes(self):
        """Prompt set 요약만 있을 때 변경 요약을 반환."""
        from evalvault.adapters.outbound.analysis.run_change_detector_module import (
            RunChangeDetectorModule,
        )
        from evalvault.domain.entities import EvaluationRun
        from evalvault.domain.entities.result import MetricScore, TestCaseResult

        run_a = EvaluationRun(
            run_id="run-a",
            dataset_name="dataset-1",
            model_name="model-a",
            metrics_evaluated=["faithfulness"],
        )
        run_a.results.append(
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="faithfulness", score=0.6)],
            )
        )
        run_a.tracker_metadata["prompt_set"] = {
            "system_prompt_checksum": "chk-a",
            "ragas_prompt_checksums": {"faithfulness": "ragas-a"},
        }

        run_b = EvaluationRun(
            run_id="run-b",
            dataset_name="dataset-1",
            model_name="model-b",
            metrics_evaluated=["faithfulness"],
        )
        run_b.results.append(
            TestCaseResult(
                test_case_id="tc-1",
                metrics=[MetricScore(name="faithfulness", score=0.8)],
            )
        )
        run_b.tracker_metadata["prompt_set"] = {
            "system_prompt_checksum": "chk-b",
            "ragas_prompt_checksums": {"faithfulness": "ragas-b"},
        }

        module = RunChangeDetectorModule(storage=None)
        inputs = {"run_loader": {"runs": [run_a, run_b], "missing_run_ids": []}}
        result = module.execute(inputs)

        assert result["summary"]["dataset_changed"] is False
        assert result["prompt_changes"]["status"] == "summary_only"
        assert result["prompt_changes"]["summary"]["changed"] >= 1


# =============================================================================
# RunMetricComparatorModule Tests
# =============================================================================


class TestRunMetricComparatorModule:
    """RunMetricComparatorModule 테스트."""

    def test_compare_runs(self):
        """두 실행의 메트릭 비교 결과를 반환."""
        from evalvault.adapters.outbound.analysis.run_metric_comparator_module import (
            RunMetricComparatorModule,
        )
        from evalvault.domain.entities import EvaluationRun
        from evalvault.domain.entities.result import MetricScore, TestCaseResult

        run_a = EvaluationRun(
            run_id="run-a",
            dataset_name="dataset-1",
            model_name="model-a",
            metrics_evaluated=["faithfulness"],
        )
        run_a.results.extend(
            [
                TestCaseResult(
                    test_case_id="tc-1",
                    metrics=[MetricScore(name="faithfulness", score=0.6)],
                ),
                TestCaseResult(
                    test_case_id="tc-2",
                    metrics=[MetricScore(name="faithfulness", score=0.7)],
                ),
            ]
        )

        run_b = EvaluationRun(
            run_id="run-b",
            dataset_name="dataset-1",
            model_name="model-b",
            metrics_evaluated=["faithfulness"],
        )
        run_b.results.extend(
            [
                TestCaseResult(
                    test_case_id="tc-1",
                    metrics=[MetricScore(name="faithfulness", score=0.8)],
                ),
                TestCaseResult(
                    test_case_id="tc-2",
                    metrics=[MetricScore(name="faithfulness", score=0.9)],
                ),
            ]
        )

        module = RunMetricComparatorModule()
        inputs = {"run_loader": {"runs": [run_a, run_b]}}
        result = module.execute(inputs)

        assert result["summary"]["total_metrics"] == 1
        assert len(result["comparisons"]) == 1
        assert result["comparisons"][0]["direction"] == "up"
