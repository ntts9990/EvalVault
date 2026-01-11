"""Tests for Contextual Relevancy metric."""

import pytest

from evalvault.domain.metrics.contextual_relevancy import (
    ContextualRelevancy,
    _calculate_relevancy,
    _normalize_text,
    _strip_korean_endings,
    _tokenize,
    _tokenize_content_words,
    _tokenize_with_stripping,
)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_normalize_text_basic(self):
        assert _normalize_text("Hello World") == "hello world"
        assert _normalize_text("  Multiple   Spaces  ") == "multiple spaces"

    def test_normalize_text_korean(self):
        assert _normalize_text("안녕하세요") == "안녕하세요"
        assert _normalize_text("보험료는  1억원입니다") == "보험료는 1억원입니다"

    def test_normalize_text_empty(self):
        assert _normalize_text("") == ""

    def test_tokenize_basic(self):
        tokens = _tokenize("hello world")
        assert "hello" in tokens
        assert "world" in tokens

    def test_tokenize_korean(self):
        tokens = _tokenize("보험료 1억원")
        assert "보험료" in tokens
        assert "1억원" in tokens

    def test_tokenize_empty(self):
        assert _tokenize("") == set()

    def test_strip_korean_endings_basic(self):
        assert _strip_korean_endings("1억원입니다") == "1억원"
        assert _strip_korean_endings("보험료는") == "보험료"
        assert _strip_korean_endings("금액이") == "금액"

    def test_strip_korean_endings_no_match(self):
        assert _strip_korean_endings("보험") == "보험"
        assert _strip_korean_endings("test") == "test"

    def test_strip_korean_endings_short_token(self):
        # Should not strip if result would be empty
        assert _strip_korean_endings("은") == "은"
        assert _strip_korean_endings("입니다") == "입니다"

    def test_tokenize_with_stripping(self):
        tokens = _tokenize_with_stripping("보험료는 1억원입니다")
        assert "보험료" in tokens
        assert "1억원" in tokens

    def test_tokenize_with_stripping_empty(self):
        assert _tokenize_with_stripping("") == set()

    def test_tokenize_content_words_filters_stopwords(self):
        """Test that stopwords are filtered out."""
        tokens = _tokenize_content_words("the quick brown fox")
        assert "the" not in tokens
        assert "quick" in tokens
        assert "brown" in tokens
        assert "fox" in tokens

    def test_tokenize_content_words_korean(self):
        """Test Korean content word extraction."""
        tokens = _tokenize_content_words("보험료는 1억원입니다")
        assert "보험료" in tokens
        assert "1억원" in tokens


class TestCalculateRelevancy:
    """Tests for relevancy calculation."""

    def test_full_match(self):
        """Question terms fully appear in context."""
        relevancy = _calculate_relevancy(
            question="보장금액",
            context="보장금액은 1억원입니다",
        )
        assert relevancy == 1.0

    def test_partial_match(self):
        """Some question terms appear in context."""
        relevancy = _calculate_relevancy(
            question="보장금액 보험료 얼마",
            context="보장금액은 1억원입니다",
        )
        # Only "보장금액" matches (1/3 content words after filtering)
        assert 0.0 < relevancy < 1.0

    def test_no_match(self):
        """No question terms appear in context."""
        relevancy = _calculate_relevancy(
            question="보장금액 얼마",
            context="회사 소개 페이지입니다",
        )
        assert relevancy == 0.0

    def test_empty_question(self):
        """Empty question."""
        assert _calculate_relevancy("", "context") == 0.0

    def test_empty_context(self):
        """Empty context."""
        assert _calculate_relevancy("question", "") == 0.0

    def test_english_relevancy(self):
        """Test with English content."""
        relevancy = _calculate_relevancy(
            question="What is the coverage amount?",
            context="The coverage amount is $1 million.",
        )
        # "coverage" and "amount" should match
        assert relevancy > 0.0


class TestContextualRelevancy:
    """Tests for ContextualRelevancy metric."""

    @pytest.fixture
    def metric(self):
        return ContextualRelevancy()

    def test_all_relevant_contexts(self, metric):
        """All contexts are relevant to the question."""
        score = metric.score(
            question="보장금액",
            contexts=[
                "보장금액은 1억원입니다",
                "사망시 보장금액이 지급됩니다",
            ],
        )
        # Both contexts contain "보장금액"
        assert score == 1.0

    def test_mixed_relevancy(self, metric):
        """Mix of relevant and irrelevant contexts."""
        score = metric.score(
            question="보장금액",
            contexts=[
                "보장금액은 1억원입니다",  # Relevant (1.0)
                "회사 소개 페이지입니다",  # Irrelevant (0.0)
            ],
        )
        # Average of relevant (1.0) and irrelevant (0.0) = 0.5
        assert score == 0.5

    def test_no_relevant_contexts(self, metric):
        """No contexts are relevant."""
        score = metric.score(
            question="이 보험의 보장금액은 얼마인가요?",
            contexts=[
                "회사 소개 페이지입니다",
                "연락처 정보입니다",
            ],
        )
        assert score < 0.3

    def test_empty_contexts(self, metric):
        """Empty context list."""
        score = metric.score(
            question="이 보험의 보장금액은 얼마인가요?",
            contexts=[],
        )
        assert score == 0.0

    def test_none_contexts(self, metric):
        """None contexts."""
        score = metric.score(
            question="이 보험의 보장금액은 얼마인가요?",
            contexts=None,
        )
        assert score == 0.0

    def test_empty_question(self, metric):
        """Empty question."""
        score = metric.score(
            question="",
            contexts=["보장금액은 1억원입니다"],
        )
        assert score == 0.0

    def test_with_k_limit(self):
        """Test with k limit."""
        metric = ContextualRelevancy(k=2)
        # Only first 2 contexts considered
        detailed = metric.score_detailed(
            question="보장금액",
            contexts=[
                "보장금액 1억원",
                "회사 소개",
                "보장금액 추가 정보",
            ],
        )
        assert detailed["total_contexts"] == 2

    def test_reference_free(self, metric):
        """Metric works without ground_truth."""
        score = metric.score(
            question="보장금액 얼마",
            answer="1억원입니다",  # Not used
            ground_truth="1억원",  # Not used
            contexts=["보장금액은 1억원입니다"],
        )
        # Should still work, ignoring answer and ground_truth
        assert score > 0.0


class TestContextualRelevancyDetailed:
    """Tests for detailed score output."""

    @pytest.fixture
    def metric(self):
        return ContextualRelevancy()

    def test_detailed_output_structure(self, metric):
        """Test detailed output contains all fields."""
        result = metric.score_detailed(
            question="보장금액 얼마",
            contexts=["보장금액 1억원", "관련없음"],
        )
        assert "contextual_relevancy" in result
        assert "relevancy_scores" in result
        assert "relevant_count" in result
        assert "total_contexts" in result
        assert "k" in result
        assert "precision" in result

    def test_detailed_output_values(self, metric):
        """Test detailed output has reasonable values."""
        result = metric.score_detailed(
            question="보장금액 보험료",
            contexts=[
                "보장금액은 1억원입니다",  # Relevant
                "회사 소개",  # Irrelevant
                "보험료는 월 10만원",  # Relevant
            ],
        )
        assert 0.0 <= result["contextual_relevancy"] <= 1.0
        assert len(result["relevancy_scores"]) == 3
        assert result["total_contexts"] == 3
        assert 0 <= result["relevant_count"] <= 3
        assert 0.0 <= result["precision"] <= 1.0

    def test_detailed_empty_contexts(self, metric):
        """Test detailed output for empty contexts."""
        result = metric.score_detailed(
            question="보장금액",
            contexts=[],
        )
        assert result["contextual_relevancy"] == 0.0
        assert result["relevancy_scores"] == []
        assert result["relevant_count"] == 0
        assert result["total_contexts"] == 0


class TestGetRelevantContexts:
    """Tests for get_relevant_contexts method."""

    @pytest.fixture
    def metric(self):
        return ContextualRelevancy()

    def test_returns_relevant_contexts(self, metric):
        """Test that relevant contexts are returned."""
        contexts = [
            "보장금액은 1억원입니다",  # Relevant
            "회사 소개입니다",  # Irrelevant
            "보장금액 관련 추가 정보",  # Relevant
        ]
        results = metric.get_relevant_contexts(
            question="보장금액",
            contexts=contexts,
        )
        # Should return relevant contexts with indices and scores
        assert len(results) >= 1
        for idx, _ctx, score in results:
            assert idx in [0, 2]  # First and third are relevant
            assert score >= 0.3

    def test_sorted_by_score(self, metric):
        """Test results are sorted by score descending."""
        contexts = [
            "관련없음",
            "보장금액 1억원",  # More relevant
            "보장금액",  # Less relevant (shorter)
        ]
        results = metric.get_relevant_contexts(
            question="보장금액 1억원",
            contexts=contexts,
        )
        if len(results) >= 2:
            scores = [r[2] for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_custom_threshold(self, metric):
        """Test custom threshold."""
        contexts = [
            "보장금액 1억원",
            "약간 관련",
        ]
        # High threshold
        high_results = metric.get_relevant_contexts(
            question="보장금액",
            contexts=contexts,
            threshold=0.9,
        )
        # Low threshold
        low_results = metric.get_relevant_contexts(
            question="보장금액",
            contexts=contexts,
            threshold=0.1,
        )
        # Low threshold should return more (or equal) results
        assert len(low_results) >= len(high_results)

    def test_empty_contexts(self, metric):
        """Test with empty contexts."""
        results = metric.get_relevant_contexts(
            question="보장금액",
            contexts=[],
        )
        assert results == []


class TestEvaluatorRegistration:
    """Test evaluator registration."""

    def test_metric_registered_in_evaluator(self):
        """Test that ContextualRelevancy is registered in RagasEvaluator."""
        from evalvault.domain.services.evaluator import RagasEvaluator

        evaluator = RagasEvaluator()
        assert "contextual_relevancy" in evaluator.CUSTOM_METRIC_MAP

    def test_metric_not_in_reference_required(self):
        """Test that contextual_relevancy is NOT in REFERENCE_REQUIRED_METRICS."""
        from evalvault.domain.services.evaluator import RagasEvaluator

        evaluator = RagasEvaluator()
        # This metric is reference-free
        assert "contextual_relevancy" not in evaluator.REFERENCE_REQUIRED_METRICS


class TestEvaluatorIntegration:
    """Evaluator integration for contextual relevancy."""

    @pytest.mark.asyncio
    async def test_contextual_relevancy_uses_question(self):
        """Evaluator should pass question to contextual relevancy metric."""
        from evalvault.domain.entities import Dataset, TestCase
        from evalvault.domain.services.evaluator import RagasEvaluator

        dataset = Dataset(
            name="contextual-relevancy",
            version="v1",
            test_cases=[
                TestCase(
                    id="tc-001",
                    question="보장금액",
                    answer="1억원입니다.",
                    contexts=["보장금액은 1억원입니다."],
                    ground_truth=None,
                )
            ],
        )

        evaluator = RagasEvaluator()
        results = await evaluator._evaluate_with_custom_metrics(
            dataset=dataset,
            metrics=["contextual_relevancy"],
        )

        score = results["tc-001"].scores.get("contextual_relevancy")
        assert score is not None
        assert score > 0.0


class TestIntegration:
    """Integration tests for contextual relevancy metric."""

    def test_korean_insurance_scenario(self):
        """Test with realistic Korean insurance Q&A scenario."""
        metric = ContextualRelevancy()

        # Question about coverage amount
        score = metric.score(
            question="이 보험의 사망 보장금액은 얼마인가요?",
            contexts=[
                "해당 보험의 사망 보장금액은 1억원입니다.",  # Very relevant
                "보험 가입 연령은 만 19세부터 65세까지입니다.",  # Less relevant
                "월 보험료는 5만원입니다.",  # Somewhat relevant (insurance context)
            ],
        )
        # First context should be most relevant
        assert score > 0.3

    def test_english_scenario(self):
        """Test with English content."""
        metric = ContextualRelevancy()

        score = metric.score(
            question="What is the death benefit coverage amount?",
            contexts=[
                "The death benefit coverage is $1 million.",  # Relevant
                "Contact us at support@example.com.",  # Irrelevant
            ],
        )
        assert score > 0.3

    def test_comparison_with_context_precision(self):
        """Test difference from context precision (reference-free vs reference-required)."""
        metric = ContextualRelevancy()

        # This metric only looks at question-context alignment
        # Context Precision would look at ground_truth-context alignment
        score = metric.score(
            question="보장금액 얼마",
            ground_truth="1억원",  # Not used
            contexts=["보장금액은 1억원입니다"],
        )
        # Should work without relying on ground_truth
        assert score > 0.0

    def test_rag_triad_use_case(self):
        """Test as part of RAG Triad evaluation."""
        metric = ContextualRelevancy()

        # RAG Triad:
        # 1. Answer Relevancy: answer vs question
        # 2. Faithfulness: answer vs contexts
        # 3. Contextual Relevancy: contexts vs question (this metric)

        question = "이 보험의 보장금액은 얼마인가요?"
        contexts = [
            "해당 보험의 사망 보장금액은 1억원입니다.",
            "보험 약관 설명서입니다.",
        ]

        # Evaluate context quality before looking at the answer
        score = metric.score(question=question, contexts=contexts)

        # High score means retrieval was good
        # Low score means retrieval needs improvement
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
