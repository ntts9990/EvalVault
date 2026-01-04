"""Tests for NLP analysis adapter."""

from datetime import datetime

import pytest

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.analysis import (
    KeywordInfo,
    NLPAnalysis,
    QuestionType,
    QuestionTypeStats,
    TextStats,
)
from tests.optional_deps import kiwi_ready, sklearn_ready

# Check if kiwipiepy is available
try:
    from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer

    HAS_KIWI, KIWI_SKIP_REASON = kiwi_ready()
    KIWI_SKIP_REASON = KIWI_SKIP_REASON or "kiwipiepy unavailable"
except ImportError:
    HAS_KIWI = False
    KIWI_SKIP_REASON = "kiwipiepy not installed"

HAS_SKLEARN, SKLEARN_SKIP_REASON = sklearn_ready()
SKLEARN_SKIP_REASON = SKLEARN_SKIP_REASON or "scikit-learn unavailable"
SKLEARN_REQUIRED = pytest.mark.skipif(not HAS_SKLEARN, reason=SKLEARN_SKIP_REASON)


class TestNLPAnalysisAdapterTextStats:
    """텍스트 통계 분석 테스트."""

    @pytest.fixture
    def adapter(self):
        """NLPAnalysisAdapter 인스턴스."""
        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        return NLPAnalysisAdapter()

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
                    contexts=["해당 보험의 사망 보장금액은 1억원입니다."],
                    metrics=[
                        MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                    ],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    question="보험료 납입 기간은 어떻게 되나요?",
                    answer="납입 기간은 20년입니다.",
                    contexts=["보험료 납입 기간은 10년, 15년, 20년 중 선택 가능합니다."],
                    metrics=[
                        MetricScore(name="faithfulness", score=0.8, threshold=0.7),
                    ],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

    def test_analyze_text_statistics_returns_nlp_analysis(self, adapter, sample_run):
        """텍스트 통계 분석 결과가 NLPAnalysis인지 확인."""
        result = adapter.analyze_text_statistics(sample_run)

        assert isinstance(result, NLPAnalysis)
        assert result.run_id == "run-001"

    def test_analyze_text_statistics_question_stats(self, adapter, sample_run):
        """질문 텍스트 통계 분석."""
        result = adapter.analyze_text_statistics(sample_run)

        assert result.question_stats is not None
        assert isinstance(result.question_stats, TextStats)
        assert result.question_stats.char_count > 0
        assert result.question_stats.word_count > 0
        assert result.question_stats.sentence_count > 0
        assert 0 <= result.question_stats.unique_word_ratio <= 1

    def test_analyze_text_statistics_answer_stats(self, adapter, sample_run):
        """답변 텍스트 통계 분석."""
        result = adapter.analyze_text_statistics(sample_run)

        assert result.answer_stats is not None
        assert isinstance(result.answer_stats, TextStats)
        assert result.answer_stats.char_count > 0

    def test_analyze_text_statistics_context_stats(self, adapter, sample_run):
        """컨텍스트 텍스트 통계 분석."""
        result = adapter.analyze_text_statistics(sample_run)

        assert result.context_stats is not None
        assert isinstance(result.context_stats, TextStats)
        assert result.context_stats.char_count > 0

    def test_analyze_text_statistics_empty_run(self, adapter):
        """빈 실행 결과 처리."""
        empty_run = EvaluationRun(
            run_id="empty-run",
            dataset_name="test",
            model_name="test",
            started_at=datetime.now(),
            results=[],
            metrics_evaluated=[],
        )

        result = adapter.analyze_text_statistics(empty_run)

        assert result.run_id == "empty-run"
        assert result.question_stats is None
        assert result.answer_stats is None
        assert result.context_stats is None


class TestNLPAnalysisAdapterQuestionTypes:
    """질문 유형 분류 테스트."""

    @pytest.fixture
    def adapter(self):
        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        return NLPAnalysisAdapter()

    @pytest.fixture
    def factual_run(self):
        """사실형 질문 포함 실행 결과."""
        return EvaluationRun(
            run_id="factual-run",
            dataset_name="test",
            model_name="test",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="이 보험의 보장금액은 얼마인가요?",  # 사실형
                    answer="1억원입니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    question="What is the coverage amount?",  # 사실형 (영어)
                    answer="100 million won.",
                    metrics=[MetricScore(name="faithfulness", score=0.85, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-003",
                    question="보험 가입자는 누구인가요?",  # 사실형
                    answer="홍길동입니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.8, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

    @pytest.fixture
    def reasoning_run(self):
        """추론형 질문 포함 실행 결과."""
        return EvaluationRun(
            run_id="reasoning-run",
            dataset_name="test",
            model_name="test",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="왜 보험료가 인상되었나요?",  # 추론형
                    answer="물가 상승 때문입니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.7, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    question="How does the insurance policy work?",  # 추론형 (영어)
                    answer="It covers medical expenses.",
                    metrics=[MetricScore(name="faithfulness", score=0.75, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

    @pytest.fixture
    def mixed_run(self):
        """여러 유형 질문 포함 실행 결과."""
        return EvaluationRun(
            run_id="mixed-run",
            dataset_name="test",
            model_name="test",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="보장금액은 얼마인가요?",  # 사실형
                    answer="1억원입니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    question="왜 해지하면 손해인가요?",  # 추론형
                    answer="원금 손실이 발생합니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.7, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-003",
                    question="A 보험과 B 보험의 차이점은?",  # 비교형
                    answer="보장 범위가 다릅니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.75, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-004",
                    question="보험 청구 방법은 어떻게 되나요?",  # 절차형
                    answer="온라인으로 신청 가능합니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.8, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

    def test_classify_question_types_returns_list(self, adapter, factual_run):
        """질문 유형 분류 결과가 리스트인지 확인."""
        result = adapter.classify_question_types(factual_run)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, QuestionTypeStats) for item in result)

    def test_classify_factual_questions(self, adapter, factual_run):
        """사실형 질문 분류 테스트."""
        result = adapter.classify_question_types(factual_run)

        # 사실형 질문이 가장 많아야 함
        factual_stats = next((s for s in result if s.question_type == QuestionType.FACTUAL), None)
        assert factual_stats is not None
        assert factual_stats.count >= 2  # 최소 2개 이상

    def test_classify_reasoning_questions(self, adapter, reasoning_run):
        """추론형 질문 분류 테스트."""
        result = adapter.classify_question_types(reasoning_run)

        reasoning_stats = next(
            (s for s in result if s.question_type == QuestionType.REASONING), None
        )
        assert reasoning_stats is not None
        assert reasoning_stats.count >= 1

    def test_classify_mixed_questions(self, adapter, mixed_run):
        """여러 유형 질문 분류 테스트."""
        result = adapter.classify_question_types(mixed_run)

        # 여러 유형이 분류되어야 함
        assert len(result) >= 2

        # 전체 비율 합이 1
        total_percentage = sum(s.percentage for s in result)
        assert total_percentage == pytest.approx(1.0, rel=0.01)

    def test_classify_empty_run(self, adapter):
        """빈 실행 결과 처리."""
        empty_run = EvaluationRun(
            run_id="empty",
            dataset_name="test",
            model_name="test",
            started_at=datetime.now(),
            results=[],
            metrics_evaluated=[],
        )

        result = adapter.classify_question_types(empty_run)
        assert result == []

    def test_question_type_stats_includes_avg_scores(self, adapter, factual_run):
        """질문 유형별 평균 점수 포함 확인."""
        result = adapter.classify_question_types(factual_run)

        for stats in result:
            # avg_scores가 비어있지 않아야 함
            if stats.count > 0:
                assert isinstance(stats.avg_scores, dict)


@SKLEARN_REQUIRED
class TestNLPAnalysisAdapterKeywords:
    """키워드 추출 테스트."""

    @pytest.fixture
    def adapter(self):
        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        return NLPAnalysisAdapter()

    @pytest.fixture
    def keyword_rich_run(self):
        """키워드가 풍부한 실행 결과."""
        return EvaluationRun(
            run_id="keyword-run",
            dataset_name="test",
            model_name="test",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="이 보험의 보장금액은 얼마인가요?",
                    answer="이 보험의 사망 보장금액은 1억원입니다.",
                    contexts=["해당 보험의 사망 보장금액은 1억원입니다."],
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    question="보험료 납입 기간은?",
                    answer="보험료 납입 기간은 20년입니다.",
                    contexts=["보험료 납입 기간은 10년, 15년, 20년 선택 가능."],
                    metrics=[MetricScore(name="faithfulness", score=0.85, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-003",
                    question="보험 해지시 환급금은?",
                    answer="해지 환급금은 납입 보험료의 80%입니다.",
                    contexts=["해지 환급금은 납입 보험료 대비 80% 수준입니다."],
                    metrics=[MetricScore(name="faithfulness", score=0.8, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

    def test_extract_keywords_returns_list(self, adapter, keyword_rich_run):
        """키워드 추출 결과가 리스트인지 확인."""
        result = adapter.extract_keywords(keyword_rich_run)

        assert isinstance(result, list)
        assert all(isinstance(item, KeywordInfo) for item in result)

    def test_extract_keywords_not_empty(self, adapter, keyword_rich_run):
        """키워드 추출 결과가 비어있지 않음."""
        result = adapter.extract_keywords(keyword_rich_run)

        assert len(result) > 0

    def test_extract_keywords_top_k(self, adapter, keyword_rich_run):
        """top_k 파라미터 동작 확인."""
        result = adapter.extract_keywords(keyword_rich_run, top_k=5)

        assert len(result) <= 5

    def test_extract_keywords_sorted_by_tfidf(self, adapter, keyword_rich_run):
        """TF-IDF 점수 내림차순 정렬 확인."""
        result = adapter.extract_keywords(keyword_rich_run)

        if len(result) > 1:
            scores = [k.tfidf_score for k in result]
            assert scores == sorted(scores, reverse=True)

    def test_extract_keywords_has_frequency(self, adapter, keyword_rich_run):
        """키워드 빈도 포함 확인."""
        result = adapter.extract_keywords(keyword_rich_run)

        for keyword in result:
            assert keyword.frequency > 0

    def test_extract_keywords_empty_run(self, adapter):
        """빈 실행 결과 처리."""
        empty_run = EvaluationRun(
            run_id="empty",
            dataset_name="test",
            model_name="test",
            started_at=datetime.now(),
            results=[],
            metrics_evaluated=[],
        )

        result = adapter.extract_keywords(empty_run)
        assert result == []


@SKLEARN_REQUIRED
class TestNLPAnalysisAdapterIntegration:
    """통합 분석 테스트."""

    @pytest.fixture
    def adapter(self):
        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        return NLPAnalysisAdapter()

    @pytest.fixture
    def comprehensive_run(self):
        """종합 테스트용 실행 결과."""
        return EvaluationRun(
            run_id="comprehensive-run",
            dataset_name="insurance-qa",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="보험의 보장금액은 얼마인가요?",
                    answer="보장금액은 1억원입니다.",
                    contexts=["사망 보장금액 1억원"],
                    metrics=[
                        MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.85, threshold=0.7),
                    ],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    question="왜 보험료가 올랐나요?",
                    answer="물가 상승으로 인해 조정되었습니다.",
                    contexts=["2024년 물가 상승률 반영"],
                    metrics=[
                        MetricScore(name="faithfulness", score=0.75, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.8, threshold=0.7),
                    ],
                ),
                TestCaseResult(
                    test_case_id="tc-003",
                    question="보험 청구 절차는 어떻게 되나요?",
                    answer="온라인 또는 앱으로 청구 가능합니다.",
                    contexts=["보험 청구는 온라인/앱/방문 가능"],
                    metrics=[
                        MetricScore(name="faithfulness", score=0.8, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.78, threshold=0.7),
                    ],
                ),
            ],
            metrics_evaluated=["faithfulness", "answer_relevancy"],
        )

    def test_analyze_returns_complete_nlp_analysis(self, adapter, comprehensive_run):
        """통합 분석 결과 확인."""
        result = adapter.analyze(comprehensive_run)

        assert isinstance(result, NLPAnalysis)
        assert result.run_id == "comprehensive-run"
        assert result.has_text_stats is True
        assert result.has_question_type_analysis is True
        assert result.has_keyword_analysis is True

    def test_analyze_with_selective_options(self, adapter, comprehensive_run):
        """선택적 분석 옵션 테스트."""
        result = adapter.analyze(
            comprehensive_run,
            include_text_stats=True,
            include_question_types=False,
            include_keywords=False,
        )

        assert result.has_text_stats is True
        assert result.has_question_type_analysis is False
        assert result.has_keyword_analysis is False

    def test_analyze_generates_insights(self, adapter, comprehensive_run):
        """인사이트 생성 확인."""
        result = adapter.analyze(comprehensive_run)

        # 인사이트가 생성되어야 함
        assert isinstance(result.insights, list)


@SKLEARN_REQUIRED
class TestNLPAnalysisAdapterHybrid:
    """하이브리드 NLP 분석 테스트 (LLM/임베딩 통합)."""

    @pytest.fixture
    def sample_run(self):
        """테스트용 샘플 EvaluationRun."""
        return EvaluationRun(
            run_id="hybrid-run",
            dataset_name="test-dataset",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="이 보험의 보장금액은 얼마인가요?",
                    answer="보장금액은 1억원입니다.",
                    contexts=["해당 보험의 사망 보장금액은 1억원입니다."],
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    question="보험료 납입 방법은?",
                    answer="카드, 계좌이체, 자동이체 가능합니다.",
                    contexts=["보험료 납입은 다양한 방법으로 가능합니다."],
                    metrics=[MetricScore(name="faithfulness", score=0.85, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

    def test_adapter_init_without_llm(self):
        """LLM 없이 어댑터 초기화."""
        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        adapter = NLPAnalysisAdapter()

        assert adapter._llm_adapter is None
        assert adapter._use_embeddings is False
        assert adapter._use_llm_classification is False

    def test_adapter_init_with_llm_settings(self):
        """LLM 설정과 함께 어댑터 초기화."""
        from unittest.mock import MagicMock

        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        mock_llm = MagicMock()
        adapter = NLPAnalysisAdapter(
            llm_adapter=mock_llm,
            use_embeddings=True,
            use_llm_classification=True,
        )

        assert adapter._llm_adapter is mock_llm
        assert adapter._use_embeddings is True
        assert adapter._use_llm_classification is True

    def test_adapter_embeddings_disabled_when_no_llm(self):
        """LLM이 없으면 임베딩 비활성화."""
        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        adapter = NLPAnalysisAdapter(
            llm_adapter=None,
            use_embeddings=True,  # 요청했지만
        )

        assert adapter._use_embeddings is False  # LLM이 없어서 비활성화

    def test_extract_keywords_with_mock_embeddings(self, sample_run):
        """임베딩을 사용한 키워드 추출 테스트."""
        from unittest.mock import MagicMock

        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        # Mock embeddings
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3] for _ in range(10)]

        # Mock LLM adapter
        mock_llm = MagicMock()
        mock_llm.as_ragas_embeddings.return_value = mock_embeddings

        adapter = NLPAnalysisAdapter(llm_adapter=mock_llm, use_embeddings=True)

        result = adapter.extract_keywords(sample_run)

        # 키워드가 추출되어야 함
        assert len(result) > 0
        # 임베딩이 호출되었어야 함
        assert mock_llm.as_ragas_embeddings.called

    def test_extract_keywords_without_embeddings(self, sample_run):
        """임베딩 없이 TF-IDF만으로 키워드 추출."""
        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        adapter = NLPAnalysisAdapter(use_embeddings=False)

        result = adapter.extract_keywords(sample_run)

        # TF-IDF만으로도 키워드가 추출되어야 함
        assert len(result) > 0
        for kw in result:
            assert kw.tfidf_score > 0

    def test_embedding_enhancement_graceful_fallback(self, sample_run):
        """임베딩 실패 시 TF-IDF로 폴백."""
        from unittest.mock import MagicMock

        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        # 에러를 발생시키는 Mock
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.side_effect = Exception("Embedding failed")

        mock_llm = MagicMock()
        mock_llm.as_ragas_embeddings.return_value = mock_embeddings

        adapter = NLPAnalysisAdapter(llm_adapter=mock_llm, use_embeddings=True)

        result = adapter.extract_keywords(sample_run)

        # 에러가 발생해도 TF-IDF 결과는 반환되어야 함
        assert len(result) > 0

    def test_analyze_with_hybrid_approach(self, sample_run):
        """하이브리드 접근 방식으로 전체 분석."""
        from unittest.mock import MagicMock

        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        mock_llm = MagicMock()
        mock_llm.as_ragas_embeddings.return_value = None  # 임베딩 사용 안 함

        adapter = NLPAnalysisAdapter(
            llm_adapter=mock_llm,
            use_embeddings=True,
            use_llm_classification=False,
        )

        result = adapter.analyze(sample_run)

        # 모든 분석이 수행되어야 함
        assert result.run_id == "hybrid-run"
        assert result.has_text_stats is True
        assert result.has_question_type_analysis is True
        # 임베딩이 None이므로 TF-IDF만으로 키워드 추출
        assert result.has_keyword_analysis is True


@SKLEARN_REQUIRED
class TestTopicClustering:
    """토픽 클러스터링 테스트."""

    @pytest.fixture
    def clustering_run(self):
        """클러스터링 테스트용 샘플 EvaluationRun (충분한 질문 포함)."""
        return EvaluationRun(
            run_id="cluster-run",
            dataset_name="test-dataset",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[
                # 보험료 관련 질문 클러스터
                TestCaseResult(
                    test_case_id="tc-001",
                    question="보험료는 얼마인가요?",
                    answer="월 5만원입니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    question="보험료 납입 방법은?",
                    answer="카드 또는 계좌이체입니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.85, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-003",
                    question="보험료 할인 조건은?",
                    answer="가족 할인 10% 적용됩니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.8, threshold=0.7)],
                ),
                # 보장 관련 질문 클러스터
                TestCaseResult(
                    test_case_id="tc-004",
                    question="보장금액은 얼마인가요?",
                    answer="1억원입니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-005",
                    question="보장 기간은 어떻게 되나요?",
                    answer="10년 보장입니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.88, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-006",
                    question="보장 범위에 포함되는 것은?",
                    answer="질병, 사고, 입원 등입니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.82, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

    def test_cluster_topics_without_embeddings(self, clustering_run):
        """임베딩 없이 클러스터링 시 빈 리스트 반환."""
        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        adapter = NLPAnalysisAdapter(llm_adapter=None, use_embeddings=False)

        result = adapter.cluster_topics(clustering_run)

        assert result == []

    def test_cluster_topics_with_mock_embeddings(self, clustering_run):
        """Mock 임베딩으로 클러스터링 테스트."""
        from unittest.mock import MagicMock

        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        # Mock embeddings - 두 개의 클러스터로 분리되도록 설계
        mock_embeddings = MagicMock()

        # 보험료 관련 질문과 보장 관련 질문이 다른 클러스터에 속하도록
        mock_embeddings.embed_documents.return_value = [
            [0.1, 0.2, 0.3],  # 보험료 클러스터
            [0.1, 0.2, 0.4],  # 보험료 클러스터
            [0.1, 0.2, 0.35],  # 보험료 클러스터
            [0.9, 0.8, 0.7],  # 보장 클러스터
            [0.9, 0.8, 0.6],  # 보장 클러스터
            [0.9, 0.8, 0.65],  # 보장 클러스터
        ]

        mock_llm = MagicMock()
        mock_llm.as_ragas_embeddings.return_value = mock_embeddings

        adapter = NLPAnalysisAdapter(llm_adapter=mock_llm, use_embeddings=True)

        result = adapter.cluster_topics(clustering_run, min_cluster_size=2)

        # 클러스터가 생성되어야 함
        assert len(result) >= 1
        # 각 클러스터는 필수 속성을 가져야 함
        for cluster in result:
            assert cluster.cluster_id >= 0
            assert cluster.document_count >= 2
            assert isinstance(cluster.keywords, list)
            assert isinstance(cluster.avg_scores, dict)
            assert isinstance(cluster.representative_questions, list)

    def test_cluster_topics_insufficient_data(self):
        """데이터가 부족하면 빈 리스트 반환."""
        from unittest.mock import MagicMock

        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        small_run = EvaluationRun(
            run_id="small-run",
            dataset_name="test",
            model_name="test",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="질문1",
                    answer="답변1",
                    metrics=[MetricScore(name="f", score=0.9, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["f"],
        )

        mock_llm = MagicMock()
        adapter = NLPAnalysisAdapter(llm_adapter=mock_llm, use_embeddings=True)

        result = adapter.cluster_topics(small_run, min_cluster_size=3)

        assert result == []

    def test_analyze_with_topic_clusters(self, clustering_run):
        """analyze 메서드에서 토픽 클러스터링 포함."""
        from unittest.mock import MagicMock

        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.return_value = [
            [0.1, 0.2, 0.3],
            [0.1, 0.2, 0.4],
            [0.1, 0.2, 0.35],
            [0.9, 0.8, 0.7],
            [0.9, 0.8, 0.6],
            [0.9, 0.8, 0.65],
        ]

        mock_llm = MagicMock()
        mock_llm.as_ragas_embeddings.return_value = mock_embeddings

        adapter = NLPAnalysisAdapter(llm_adapter=mock_llm, use_embeddings=True)

        result = adapter.analyze(clustering_run, include_topic_clusters=True, min_cluster_size=2)

        # 토픽 클러스터가 포함되어야 함
        assert len(result.topic_clusters) >= 1
        # 인사이트에 클러스터 정보가 포함되어야 함
        cluster_insight = [i for i in result.insights if "topic clusters" in i.lower()]
        assert len(cluster_insight) > 0

    def test_cluster_topics_graceful_fallback(self, clustering_run):
        """임베딩 에러 시 graceful 폴백."""
        from unittest.mock import MagicMock

        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.side_effect = Exception("Embedding failed")

        mock_llm = MagicMock()
        mock_llm.as_ragas_embeddings.return_value = mock_embeddings

        adapter = NLPAnalysisAdapter(llm_adapter=mock_llm, use_embeddings=True)

        result = adapter.cluster_topics(clustering_run)

        # 에러 시 빈 리스트 반환
        assert result == []


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestNLPAnalysisAdapterKorean:
    """한국어 형태소 분석 통합 테스트."""

    @pytest.fixture
    def korean_tokenizer(self):
        """한국어 토크나이저 인스턴스."""
        return KiwiTokenizer()

    @pytest.fixture
    def adapter_with_korean(self, korean_tokenizer):
        """한국어 토크나이저가 설정된 어댑터."""
        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        return NLPAnalysisAdapter(korean_tokenizer=korean_tokenizer)

    @pytest.fixture
    def korean_run(self) -> EvaluationRun:
        """한국어 데이터가 포함된 EvaluationRun."""
        return EvaluationRun(
            run_id="korean-run",
            dataset_name="korean-dataset",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="이 보험의 보장금액은 얼마인가요?",
                    answer="이 보험의 사망 보장금액은 1억원입니다.",
                    contexts=["해당 보험의 사망 보장금액은 1억원입니다."],
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-002",
                    question="보험료 납입 기간은 어떻게 되나요?",
                    answer="납입 기간은 10년, 15년, 20년 중 선택 가능합니다.",
                    contexts=["보험료 납입 기간은 다양하게 선택할 수 있습니다."],
                    metrics=[MetricScore(name="faithfulness", score=0.85, threshold=0.7)],
                ),
                TestCaseResult(
                    test_case_id="tc-003",
                    question="보험 해지시 환급금은 어떻게 되나요?",
                    answer="해지 환급금은 납입 보험료의 약 80%입니다.",
                    contexts=["중도 해지시 환급금이 지급됩니다."],
                    metrics=[MetricScore(name="faithfulness", score=0.8, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

    def test_adapter_init_with_korean_tokenizer(self, adapter_with_korean):
        """한국어 토크나이저로 어댑터 초기화."""
        assert adapter_with_korean._korean_tokenizer is not None

    def test_extract_keywords_with_korean_tokenizer(self, adapter_with_korean, korean_run):
        """한국어 형태소 분석을 사용한 키워드 추출."""
        keywords = adapter_with_korean.extract_keywords(korean_run)

        assert len(keywords) > 0
        # 보험 관련 키워드가 추출되어야 함
        keyword_texts = [k.keyword for k in keywords]
        keyword_str = " ".join(keyword_texts)
        assert any(term in keyword_str for term in ["보험", "보장", "납입", "환급"])

    def test_extract_keywords_removes_particles(self, adapter_with_korean, korean_run):
        """형태소 분석으로 조사가 제거됨."""
        keywords = adapter_with_korean.extract_keywords(korean_run)

        keyword_texts = [k.keyword for k in keywords]
        # 조사가 키워드로 추출되지 않아야 함
        particles = ["은", "는", "이", "가", "을", "를", "의"]
        for particle in particles:
            assert particle not in keyword_texts

    def test_text_stats_with_korean_tokenizer(self, adapter_with_korean, korean_run):
        """한국어 토크나이저를 사용한 텍스트 통계."""
        result = adapter_with_korean.analyze_text_statistics(korean_run)

        assert result.question_stats is not None
        assert result.question_stats.word_count > 0
        # 형태소 분석 사용 시 단어 수가 정규식보다 더 정확함
        assert result.question_stats.sentence_count >= 1

    def test_analyze_with_korean_tokenizer(self, adapter_with_korean, korean_run):
        """한국어 토크나이저를 사용한 전체 분석."""
        result = adapter_with_korean.analyze(korean_run)

        assert result.run_id == "korean-run"
        assert result.has_text_stats
        assert result.has_question_type_analysis
        assert result.has_keyword_analysis
        # 한국어 질문 유형 분류
        assert len(result.question_types) > 0

    def test_fallback_to_basic_when_no_korean_text(self, adapter_with_korean):
        """영어만 있을 경우 기본 추출 사용."""
        english_run = EvaluationRun(
            run_id="english-run",
            dataset_name="english-dataset",
            model_name="gpt-5-nano",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="What is the coverage amount?",
                    answer="The coverage amount is 100 million won.",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

        keywords = adapter_with_korean.extract_keywords(english_run)

        # 영어 키워드가 추출되어야 함
        assert len(keywords) > 0
        keyword_texts = [k.keyword for k in keywords]
        assert any(
            term.lower() in [k.lower() for k in keyword_texts]
            for term in ["coverage", "amount", "million"]
        )

    def test_korean_keyword_quality(self, adapter_with_korean):
        """한국어 키워드 추출 품질 테스트."""
        run = EvaluationRun(
            run_id="quality-run",
            dataset_name="test",
            model_name="test",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="종신보험의 사망보험금 지급 조건은 무엇인가요?",
                    answer="피보험자가 보험기간 중 사망하면 사망보험금을 지급합니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

        keywords = adapter_with_korean.extract_keywords(run, top_k=10)

        keyword_texts = [k.keyword for k in keywords]
        # 핵심 보험 용어가 추출되어야 함
        assert any(
            term in keyword_texts
            for term in ["종신보험", "사망보험금", "피보험자", "보험기간", "사망", "보험금", "지급"]
        )


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestNLPAnalysisAdapterKoreanFallback:
    """한국어 분석 폴백 테스트."""

    def test_adapter_without_korean_tokenizer_still_works(self):
        """한국어 토크나이저 없이도 동작."""
        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

        adapter = NLPAnalysisAdapter()  # 토크나이저 없음

        run = EvaluationRun(
            run_id="no-tokenizer-run",
            dataset_name="test",
            model_name="test",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="보험료가 얼마인가요?",
                    answer="월 5만원입니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

        # 기본 정규식 기반으로 동작
        keywords = adapter.extract_keywords(run)
        assert len(keywords) > 0

    def test_mixed_korean_english_text(self):
        """한국어-영어 혼합 텍스트 처리."""
        from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter
        from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer

        adapter = NLPAnalysisAdapter(korean_tokenizer=KiwiTokenizer())

        run = EvaluationRun(
            run_id="mixed-run",
            dataset_name="test",
            model_name="test",
            started_at=datetime.now(),
            results=[
                TestCaseResult(
                    test_case_id="tc-001",
                    question="CI보험의 coverage는 어떻게 되나요?",
                    answer="Critical Illness 발생시 보험금을 지급합니다.",
                    metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
                ),
            ],
            metrics_evaluated=["faithfulness"],
        )

        keywords = adapter.extract_keywords(run)
        assert len(keywords) > 0
