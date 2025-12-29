"""Tests for Analysis Service."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from evalvault.adapters.outbound.analysis.statistical_adapter import (
    StatisticalAnalysisAdapter,
)
from evalvault.adapters.outbound.cache.memory_cache import MemoryCacheAdapter
from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.analysis import (
    AnalysisBundle,
    ComparisonResult,
    MetricStats,
    StatisticalAnalysis,
)
from evalvault.domain.services.analysis_service import AnalysisService


class TestAnalysisServiceBasic:
    """AnalysisService 기본 기능 테스트."""

    @pytest.fixture
    def mock_analysis_adapter(self):
        """Mock 분석 어댑터."""
        adapter = MagicMock(spec=StatisticalAnalysisAdapter)
        adapter.analyze_statistics.return_value = StatisticalAnalysis(
            run_id="run-001",
            metrics_summary={
                "faithfulness": MetricStats(
                    mean=0.8,
                    std=0.1,
                    min=0.6,
                    max=1.0,
                    median=0.8,
                    percentile_25=0.75,
                    percentile_75=0.85,
                    count=10,
                )
            },
            overall_pass_rate=0.8,
            insights=["Good pass rate"],
        )
        return adapter

    @pytest.fixture
    def mock_cache_adapter(self):
        """Mock 캐시 어댑터."""
        return MagicMock(spec=MemoryCacheAdapter)

    @pytest.fixture
    def sample_run(self):
        """테스트용 샘플 EvaluationRun."""
        results = [
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[
                    MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                ],
            ),
            TestCaseResult(
                test_case_id="tc-002",
                metrics=[
                    MetricScore(name="faithfulness", score=0.7, threshold=0.7),
                ],
            ),
        ]
        return EvaluationRun(
            run_id="run-001",
            dataset_name="test-dataset",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=results,
            metrics_evaluated=["faithfulness"],
        )

    def test_analyze_run_basic(self, mock_analysis_adapter, sample_run):
        """기본 분석 테스트."""
        service = AnalysisService(analysis_adapter=mock_analysis_adapter)

        result = service.analyze_run(sample_run)

        assert isinstance(result, AnalysisBundle)
        assert result.run_id == "run-001"
        assert result.has_statistical is True
        mock_analysis_adapter.analyze_statistics.assert_called_once_with(sample_run)

    def test_analyze_run_without_cache(self, mock_analysis_adapter, sample_run):
        """캐시 없이 분석 테스트."""
        service = AnalysisService(analysis_adapter=mock_analysis_adapter)

        result = service.analyze_run(sample_run, use_cache=False)

        assert result.has_statistical is True

    def test_analyze_run_with_nlp_flag(self, mock_analysis_adapter, sample_run):
        """NLP 분석 플래그 테스트 (아직 미구현)."""
        service = AnalysisService(analysis_adapter=mock_analysis_adapter)

        result = service.analyze_run(sample_run, include_nlp=True)

        # NLP는 아직 미구현이므로 None
        assert result.has_nlp is False

    def test_analyze_run_with_causal_flag(self, mock_analysis_adapter, sample_run):
        """인과 분석 플래그 테스트 (아직 미구현)."""
        service = AnalysisService(analysis_adapter=mock_analysis_adapter)

        result = service.analyze_run(sample_run, include_causal=True)

        # 인과 분석은 아직 미구현이므로 None
        assert result.has_causal is False


class TestAnalysisServiceCache:
    """AnalysisService 캐시 관련 테스트."""

    @pytest.fixture
    def mock_analysis_adapter(self):
        adapter = MagicMock(spec=StatisticalAnalysisAdapter)
        adapter.analyze_statistics.return_value = StatisticalAnalysis(
            run_id="run-001",
            overall_pass_rate=0.8,
        )
        return adapter

    @pytest.fixture
    def mock_cache_adapter(self):
        return MagicMock(spec=MemoryCacheAdapter)

    @pytest.fixture
    def sample_run(self):
        return EvaluationRun(
            run_id="run-001",
            dataset_name="test",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[],
            metrics_evaluated=[],
        )

    def test_cache_hit(self, mock_analysis_adapter, mock_cache_adapter, sample_run):
        """캐시 히트 테스트."""
        cached_bundle = AnalysisBundle(
            run_id="run-001",
            statistical=StatisticalAnalysis(run_id="run-001"),
        )
        mock_cache_adapter.get.return_value = cached_bundle

        service = AnalysisService(
            analysis_adapter=mock_analysis_adapter,
            cache_adapter=mock_cache_adapter,
        )

        result = service.analyze_run(sample_run, use_cache=True)

        # 캐시에서 반환되므로 분석 어댑터는 호출되지 않음
        mock_analysis_adapter.analyze_statistics.assert_not_called()
        assert result == cached_bundle

    def test_cache_miss(self, mock_analysis_adapter, mock_cache_adapter, sample_run):
        """캐시 미스 테스트."""
        mock_cache_adapter.get.return_value = None

        service = AnalysisService(
            analysis_adapter=mock_analysis_adapter,
            cache_adapter=mock_cache_adapter,
        )

        _result = service.analyze_run(sample_run, use_cache=True)

        # 캐시 미스이므로 분석 수행
        mock_analysis_adapter.analyze_statistics.assert_called_once()
        # 결과가 캐시에 저장됨
        mock_cache_adapter.set.assert_called_once()
        assert _result is not None

    def test_cache_disabled(self, mock_analysis_adapter, mock_cache_adapter, sample_run):
        """캐시 비활성화 테스트."""
        service = AnalysisService(
            analysis_adapter=mock_analysis_adapter,
            cache_adapter=mock_cache_adapter,
        )

        _result = service.analyze_run(sample_run, use_cache=False)

        # 캐시가 비활성화되면 조회/저장 모두 하지 않음
        mock_cache_adapter.get.assert_not_called()
        assert _result is not None
        mock_cache_adapter.set.assert_not_called()
        mock_analysis_adapter.analyze_statistics.assert_called_once()


class TestAnalysisServiceComparison:
    """AnalysisService 비교 기능 테스트."""

    @pytest.fixture
    def mock_analysis_adapter(self):
        adapter = MagicMock(spec=StatisticalAnalysisAdapter)
        adapter.compare_runs.return_value = [
            ComparisonResult.from_values(
                run_id_a="run-001",
                run_id_b="run-002",
                metric="faithfulness",
                mean_a=0.7,
                mean_b=0.85,
                p_value=0.01,
                effect_size=0.6,
            )
        ]
        return adapter

    @pytest.fixture
    def run_a(self):
        return EvaluationRun(
            run_id="run-001",
            dataset_name="test",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.7, threshold=0.7)],
                )
            ],
            metrics_evaluated=["faithfulness"],
        )

    @pytest.fixture
    def run_b(self):
        return EvaluationRun(
            run_id="run-002",
            dataset_name="test",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=0.85, threshold=0.7)],
                )
            ],
            metrics_evaluated=["faithfulness"],
        )

    def test_compare_runs(self, mock_analysis_adapter, run_a, run_b):
        """두 실행 비교 테스트."""
        service = AnalysisService(analysis_adapter=mock_analysis_adapter)

        results = service.compare_runs(run_a, run_b)

        assert len(results) == 1
        assert results[0].metric == "faithfulness"
        mock_analysis_adapter.compare_runs.assert_called_once_with(
            run_a, run_b, metrics=None, test_type="t-test"
        )

    def test_compare_runs_with_specific_metrics(self, mock_analysis_adapter, run_a, run_b):
        """특정 메트릭으로 비교 테스트."""
        service = AnalysisService(analysis_adapter=mock_analysis_adapter)

        service.compare_runs(run_a, run_b, metrics=["faithfulness"])

        mock_analysis_adapter.compare_runs.assert_called_once_with(
            run_a, run_b, metrics=["faithfulness"], test_type="t-test"
        )

    def test_compare_runs_with_mann_whitney(self, mock_analysis_adapter, run_a, run_b):
        """Mann-Whitney 검정으로 비교 테스트."""
        service = AnalysisService(analysis_adapter=mock_analysis_adapter)

        service.compare_runs(run_a, run_b, test_type="mann-whitney")

        mock_analysis_adapter.compare_runs.assert_called_once_with(
            run_a, run_b, metrics=None, test_type="mann-whitney"
        )


class TestAnalysisServiceMetaAnalysis:
    """AnalysisService 메타 분석 테스트."""

    @pytest.fixture
    def mock_analysis_adapter(self):
        adapter = MagicMock(spec=StatisticalAnalysisAdapter)
        adapter.compare_runs.return_value = [
            ComparisonResult.from_values(
                run_id_a="run-001",
                run_id_b="run-002",
                metric="faithfulness",
                mean_a=0.7,
                mean_b=0.85,
                p_value=0.01,
                effect_size=0.6,
            )
        ]
        return adapter

    def _create_run(self, run_id, score):
        """테스트용 EvaluationRun 생성."""
        return EvaluationRun(
            run_id=run_id,
            dataset_name="test",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    metrics=[MetricScore(name="faithfulness", score=score, threshold=0.7)],
                )
            ],
            metrics_evaluated=["faithfulness"],
        )

    def test_meta_analyze_single_run(self, mock_analysis_adapter):
        """단일 실행 메타 분석 테스트."""
        service = AnalysisService(analysis_adapter=mock_analysis_adapter)
        runs = [self._create_run("run-001", 0.8)]

        result = service.meta_analyze(runs)

        assert len(result.run_ids) == 1
        assert "At least 2 runs required" in result.recommendations[0]

    def test_meta_analyze_multiple_runs(self, mock_analysis_adapter):
        """여러 실행 메타 분석 테스트."""
        service = AnalysisService(analysis_adapter=mock_analysis_adapter)
        runs = [
            self._create_run("run-001", 0.7),
            self._create_run("run-002", 0.85),
            self._create_run("run-003", 0.9),
        ]

        result = service.meta_analyze(runs)

        assert len(result.run_ids) == 3
        # 3개 실행이면 3개 쌍 비교 (1-2, 1-3, 2-3)
        assert mock_analysis_adapter.compare_runs.call_count == 3

    def test_meta_analyze_best_worst_runs(self, mock_analysis_adapter):
        """최고/최저 실행 식별 테스트."""
        service = AnalysisService(analysis_adapter=mock_analysis_adapter)
        runs = [
            self._create_run("run-001", 0.6),
            self._create_run("run-002", 0.9),
        ]

        result = service.meta_analyze(runs)

        assert result.best_runs.get("faithfulness") == "run-002"
        assert result.worst_runs.get("faithfulness") == "run-001"

    def test_meta_analyze_overall_ranking(self, mock_analysis_adapter):
        """전체 순위 테스트."""
        service = AnalysisService(analysis_adapter=mock_analysis_adapter)
        runs = [
            self._create_run("run-001", 0.6),
            self._create_run("run-002", 0.9),
            self._create_run("run-003", 0.75),
        ]

        result = service.meta_analyze(runs)

        # 점수 내림차순: run-002, run-003, run-001
        assert result.overall_ranking == ["run-002", "run-003", "run-001"]


class TestAnalysisServiceIntegration:
    """AnalysisService 통합 테스트 (실제 어댑터 사용)."""

    @pytest.fixture
    def service(self):
        """실제 어댑터를 사용하는 서비스."""
        adapter = StatisticalAnalysisAdapter()
        cache = MemoryCacheAdapter(max_size=10, default_ttl_seconds=60)
        return AnalysisService(analysis_adapter=adapter, cache_adapter=cache)

    @pytest.fixture
    def sample_run(self):
        """테스트용 샘플 EvaluationRun."""
        results = [
            TestCaseResult(
                test_case_id=f"tc-{i:03d}",
                question=f"Question {i}?",
                metrics=[
                    MetricScore(
                        name="faithfulness",
                        score=0.5 + i * 0.05,
                        threshold=0.7,
                    ),
                    MetricScore(
                        name="answer_relevancy",
                        score=0.6 + i * 0.04,
                        threshold=0.7,
                    ),
                ],
            )
            for i in range(10)
        ]
        return EvaluationRun(
            run_id="run-integration",
            dataset_name="integration-test",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=results,
            metrics_evaluated=["faithfulness", "answer_relevancy"],
            thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
        )

    def test_full_analysis_workflow(self, service, sample_run):
        """전체 분석 워크플로우 테스트."""
        # 첫 번째 분석 (캐시 미스)
        result1 = service.analyze_run(sample_run)

        assert result1.has_statistical
        assert "faithfulness" in result1.statistical.metrics_summary
        assert "answer_relevancy" in result1.statistical.metrics_summary

        # 두 번째 분석 (캐시 히트)
        result2 = service.analyze_run(sample_run)

        # 같은 결과 반환
        assert result2.statistical.run_id == result1.statistical.run_id

    def test_comparison_workflow(self, service):
        """비교 워크플로우 테스트."""
        run_a = EvaluationRun(
            run_id="run-a",
            dataset_name="test",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id=f"tc-{i:03d}",
                    metrics=[MetricScore(name="faithfulness", score=0.6 + i * 0.02, threshold=0.7)],
                )
                for i in range(10)
            ],
            metrics_evaluated=["faithfulness"],
        )

        run_b = EvaluationRun(
            run_id="run-b",
            dataset_name="test",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id=f"tc-{i:03d}",
                    metrics=[MetricScore(name="faithfulness", score=0.8 + i * 0.01, threshold=0.7)],
                )
                for i in range(10)
            ],
            metrics_evaluated=["faithfulness"],
        )

        results = service.compare_runs(run_a, run_b)

        assert len(results) == 1
        assert results[0].metric == "faithfulness"
        assert results[0].mean_b > results[0].mean_a


class TestCacheKeyGeneration:
    """캐시 키 생성 테스트."""

    def test_cache_key_uniqueness(self):
        """캐시 키 고유성 테스트."""
        adapter = MagicMock()
        service = AnalysisService(analysis_adapter=adapter)

        key1 = service._make_cache_key("run-001", False, False)
        key2 = service._make_cache_key("run-001", True, False)
        key3 = service._make_cache_key("run-001", False, True)
        key4 = service._make_cache_key("run-002", False, False)

        # 모든 키가 고유해야 함
        keys = {key1, key2, key3, key4}
        assert len(keys) == 4

    def test_cache_key_consistency(self):
        """동일 입력에 대한 캐시 키 일관성 테스트."""
        adapter = MagicMock()
        service = AnalysisService(analysis_adapter=adapter)

        key1 = service._make_cache_key("run-001", True, False)
        key2 = service._make_cache_key("run-001", True, False)

        assert key1 == key2


class TestAnalysisServiceNLPIntegration:
    """AnalysisService NLP 분석 통합 테스트."""

    @pytest.fixture
    def mock_analysis_adapter(self):
        """Mock 통계 분석 어댑터."""
        adapter = MagicMock(spec=StatisticalAnalysisAdapter)
        adapter.analyze_statistics.return_value = StatisticalAnalysis(
            run_id="run-001",
            overall_pass_rate=0.8,
        )
        return adapter

    @pytest.fixture
    def mock_nlp_adapter(self):
        """Mock NLP 분석 어댑터."""
        from evalvault.domain.entities.analysis import (
            KeywordInfo,
            NLPAnalysis,
            QuestionType,
            QuestionTypeStats,
            TextStats,
        )

        adapter = MagicMock()
        adapter.analyze.return_value = NLPAnalysis(
            run_id="run-001",
            question_stats=TextStats(
                char_count=100,
                word_count=20,
                sentence_count=2,
                avg_word_length=4.5,
                unique_word_ratio=0.9,
            ),
            question_types=[
                QuestionTypeStats(
                    question_type=QuestionType.FACTUAL,
                    count=3,
                    percentage=0.6,
                    avg_scores={"faithfulness": 0.85},
                ),
            ],
            top_keywords=[
                KeywordInfo(keyword="보험", frequency=5, tfidf_score=0.8),
            ],
            insights=["High vocabulary diversity"],
        )
        return adapter

    @pytest.fixture
    def sample_run(self):
        """테스트용 샘플 EvaluationRun."""
        return EvaluationRun(
            run_id="run-001",
            dataset_name="test-dataset",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="이 보험의 보장금액은 얼마인가요?",
                    answer="보장금액은 1억원입니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

    def test_analyze_run_with_nlp_adapter(
        self, mock_analysis_adapter, mock_nlp_adapter, sample_run
    ):
        """NLP 어댑터가 있을 때 NLP 분석 수행."""
        service = AnalysisService(
            analysis_adapter=mock_analysis_adapter,
            nlp_adapter=mock_nlp_adapter,
        )

        result = service.analyze_run(sample_run, include_nlp=True)

        assert result.has_nlp is True
        assert result.nlp is not None
        assert result.nlp.run_id == "run-001"
        mock_nlp_adapter.analyze.assert_called_once()

    def test_analyze_run_nlp_disabled_by_default(
        self, mock_analysis_adapter, mock_nlp_adapter, sample_run
    ):
        """기본적으로 NLP 분석 비활성화 확인."""
        service = AnalysisService(
            analysis_adapter=mock_analysis_adapter,
            nlp_adapter=mock_nlp_adapter,
        )

        result = service.analyze_run(sample_run)  # include_nlp=False (기본값)

        assert result.has_nlp is False
        mock_nlp_adapter.analyze.assert_not_called()

    def test_analyze_run_without_nlp_adapter(self, mock_analysis_adapter, sample_run):
        """NLP 어댑터 없이 include_nlp=True 시 graceful 처리."""
        service = AnalysisService(
            analysis_adapter=mock_analysis_adapter,
            nlp_adapter=None,  # NLP 어댑터 없음
        )

        result = service.analyze_run(sample_run, include_nlp=True)

        # NLP 어댑터가 없으면 NLP 분석은 None
        assert result.has_nlp is False

    def test_analyze_run_nlp_with_cache(self, mock_analysis_adapter, mock_nlp_adapter, sample_run):
        """NLP 분석 결과 캐싱 테스트."""
        cache_adapter = MagicMock(spec=MemoryCacheAdapter)
        cache_adapter.get.return_value = None  # 첫 번째 호출은 캐시 미스

        service = AnalysisService(
            analysis_adapter=mock_analysis_adapter,
            nlp_adapter=mock_nlp_adapter,
            cache_adapter=cache_adapter,
        )

        result = service.analyze_run(sample_run, include_nlp=True, use_cache=True)

        # 분석 수행됨
        mock_nlp_adapter.analyze.assert_called_once()
        # 캐시에 저장됨
        cache_adapter.set.assert_called_once()
        assert result.has_nlp is True

    def test_analyze_run_nlp_content(self, mock_analysis_adapter, mock_nlp_adapter, sample_run):
        """NLP 분석 결과 내용 검증."""
        service = AnalysisService(
            analysis_adapter=mock_analysis_adapter,
            nlp_adapter=mock_nlp_adapter,
        )

        result = service.analyze_run(sample_run, include_nlp=True)

        # 텍스트 통계
        assert result.nlp.question_stats is not None
        assert result.nlp.question_stats.char_count == 100

        # 질문 유형
        assert len(result.nlp.question_types) == 1
        assert result.nlp.question_types[0].question_type.value == "factual"

        # 키워드
        assert len(result.nlp.top_keywords) == 1
        assert result.nlp.top_keywords[0].keyword == "보험"

        # 인사이트
        assert "High vocabulary diversity" in result.nlp.insights
