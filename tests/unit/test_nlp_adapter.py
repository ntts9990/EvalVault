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
