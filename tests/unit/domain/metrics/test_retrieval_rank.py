"""Tests for retrieval ranking metrics (MRR, NDCG, HitRate)."""

import math

import pytest

from evalvault.domain.metrics.retrieval_rank import (
    MRR,
    NDCG,
    HitRate,
    _calculate_relevance,
    _normalize_text,
    _tokenize,
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
        assert _normalize_text(None) == ""

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
        assert _tokenize(None) == set()

    def test_calculate_relevance_exact_match(self):
        relevance = _calculate_relevance("1억원", "1억원")
        assert relevance == 1.0

    def test_calculate_relevance_partial(self):
        relevance = _calculate_relevance(
            "보장금액은 1억원입니다. 기타 정보도 있습니다.",
            "1억원",
        )
        # "1억원" token is present in context (after stripping Korean endings)
        assert relevance == 1.0

    def test_calculate_relevance_multiple_tokens(self):
        relevance = _calculate_relevance(
            "보장금액은 1억원, 보험료는 10만원입니다",
            "보장금액 1억원 보험료",
        )
        # All ground truth tokens present (after stripping Korean endings)
        assert relevance == 1.0

    def test_calculate_relevance_partial_overlap(self):
        relevance = _calculate_relevance(
            "사망 시 보장금액은 1억원이 지급됩니다.",
            "사망보험금 1억원",
        )
        # Only "1억원" matches (사망 != 사망보험금)
        assert 0 < relevance < 1.0

    def test_calculate_relevance_no_overlap(self):
        relevance = _calculate_relevance(
            "관련없는 내용입니다",
            "1억원",
        )
        assert relevance == 0.0

    def test_calculate_relevance_empty(self):
        assert _calculate_relevance("", "1억원") == 0.0
        assert _calculate_relevance("context", "") == 0.0
        assert _calculate_relevance("", "") == 0.0


class TestMRR:
    """Tests for MRR metric."""

    @pytest.fixture
    def metric(self):
        return MRR()

    def test_mrr_first_relevant(self, metric):
        # First context is relevant -> RR = 1/1 = 1.0
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["보장금액 1억원", "관련없음", "기타"],
        )
        assert score == 1.0

    def test_mrr_second_relevant(self, metric):
        # Second context is first relevant -> RR = 1/2 = 0.5
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "보장금액 1억원", "기타"],
        )
        assert score == 0.5

    def test_mrr_third_relevant(self, metric):
        # Third context is first relevant -> RR = 1/3
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "다른내용", "보장금액 1억원"],
        )
        assert abs(score - 1 / 3) < 0.001

    def test_mrr_no_relevant(self, metric):
        # No relevant context -> RR = 0
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "다른내용", "기타정보"],
        )
        assert score == 0.0

    def test_mrr_empty_contexts(self, metric):
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=[],
        )
        assert score == 0.0

    def test_mrr_none_contexts(self, metric):
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=None,
        )
        assert score == 0.0

    def test_mrr_no_ground_truth(self, metric):
        score = metric.score(
            answer="답변",
            ground_truth="",
            contexts=["context1", "context2"],
        )
        assert score == 0.0

    def test_mrr_with_k(self):
        # MRR@2: only look at top 2
        metric = MRR(k=2)
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "다른내용", "보장금액 1억원"],  # 3rd is relevant
        )
        # Only top 2 considered, no relevant in top 2
        assert score == 0.0

    def test_mrr_custom_threshold(self):
        # Higher threshold requires more overlap
        metric = MRR(relevance_threshold=0.8)
        score = metric.score(
            answer="답변",
            ground_truth="보장금액 보험료",  # 2 tokens
            contexts=["보장금액입니다"],  # Only 1/2 tokens = 0.5 relevance
        )
        # 0.5 < 0.8 threshold, so not relevant
        assert score == 0.0

    def test_mrr_detailed(self, metric):
        result = metric.score_detailed(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "보장금액 1억원", "기타"],
        )
        assert result["mrr"] == 0.5
        assert result["first_relevant_rank"] == 2
        assert result["num_relevant"] == 1
        assert len(result["relevance_scores"]) == 3

    def test_mrr_detailed_no_relevant(self, metric):
        result = metric.score_detailed(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "다른내용"],
        )
        assert result["mrr"] == 0.0
        assert result["first_relevant_rank"] is None
        assert result["num_relevant"] == 0


class TestNDCG:
    """Tests for NDCG metric."""

    @pytest.fixture
    def metric(self):
        return NDCG(k=10)

    def test_ndcg_perfect_ranking(self, metric):
        # All relevant at top -> NDCG = 1.0
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["보장금액 1억원", "1억원 지급", "관련없음"],
        )
        assert score == 1.0

    def test_ndcg_single_relevant_first(self, metric):
        # Single relevant at position 1 -> NDCG = 1.0
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["보장금액 1억원", "관련없음", "기타"],
        )
        assert score == 1.0

    def test_ndcg_single_relevant_last(self, metric):
        # Single relevant at position 3
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "다른내용", "보장금액 1억원"],
        )
        # DCG = rel/log2(4) = 1/2
        # IDCG = 1/log2(2) = 1
        # NDCG = 0.5
        assert abs(score - 0.5) < 0.01

    def test_ndcg_no_relevant(self, metric):
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "다른내용"],
        )
        assert score == 0.0

    def test_ndcg_empty_contexts(self, metric):
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=[],
        )
        assert score == 0.0

    def test_ndcg_with_k(self):
        # NDCG@2
        metric = NDCG(k=2)
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "다른내용", "보장금액 1억원"],
        )
        # Only top 2 considered, no relevant
        assert score == 0.0

    def test_ndcg_binary_relevance(self):
        metric = NDCG(k=10, use_graded=False)
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["보장금액 1억원", "관련없음"],
        )
        # Binary relevance mode
        assert score == 1.0

    def test_ndcg_detailed(self, metric):
        result = metric.score_detailed(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "보장금액 1억원"],
        )
        assert "ndcg" in result
        assert "dcg" in result
        assert "idcg" in result
        assert "relevances" in result
        assert result["k"] == 10

    def test_ndcg_dcg_calculation(self):
        metric = NDCG(k=3)
        # Manual DCG calculation verification
        # DCG = sum(rel_i / log2(i+1))
        result = metric.score_detailed(
            answer="답변",
            ground_truth="1억원",
            contexts=["보장금액 1억원", "관련없음", "1억원 추가"],
        )
        # Position 1: rel=1.0, DCG contribution = 1.0/log2(2) = 1.0
        # Position 2: rel=0.0, DCG contribution = 0
        # Position 3: rel=1.0, DCG contribution = 1.0/log2(4) = 0.5
        expected_dcg = 1.0 / math.log2(2) + 1.0 / math.log2(4)
        assert abs(result["dcg"] - expected_dcg) < 0.01


class TestHitRate:
    """Tests for HitRate metric."""

    @pytest.fixture
    def metric(self):
        return HitRate(k=3)

    def test_hit_rate_hit_found(self, metric):
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "보장금액 1억원", "기타"],
        )
        assert score == 1.0

    def test_hit_rate_no_hit(self, metric):
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "다른내용", "기타"],
        )
        assert score == 0.0

    def test_hit_rate_hit_beyond_k(self):
        metric = HitRate(k=2)
        score = metric.score(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "다른내용", "보장금액 1억원"],
        )
        # Relevant is at position 3, but k=2
        assert score == 0.0

    def test_hit_rate_empty(self, metric):
        assert metric.score("답변", "1억원", []) == 0.0
        assert metric.score("답변", "1억원", None) == 0.0

    def test_hit_rate_detailed(self, metric):
        result = metric.score_detailed(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "보장금액 1억원", "기타"],
        )
        assert result["hit_rate"] == 1.0
        assert result["hit_position"] == 2
        assert result["k"] == 3
        assert len(result["relevance_scores"]) == 3

    def test_hit_rate_detailed_no_hit(self, metric):
        result = metric.score_detailed(
            answer="답변",
            ground_truth="1억원",
            contexts=["관련없음", "다른내용"],
        )
        assert result["hit_rate"] == 0.0
        assert result["hit_position"] is None


class TestEvaluatorRegistration:
    """Test evaluator registration for retrieval metrics."""

    def test_metrics_registered_in_evaluator(self):
        """Test that MRR, NDCG, HitRate are registered in RagasEvaluator."""
        from evalvault.domain.services.evaluator import RagasEvaluator

        evaluator = RagasEvaluator()
        assert "mrr" in evaluator.CUSTOM_METRIC_MAP
        assert "ndcg" in evaluator.CUSTOM_METRIC_MAP
        assert "hit_rate" in evaluator.CUSTOM_METRIC_MAP

    def test_metrics_in_reference_required(self):
        """Test that retrieval metrics require ground_truth."""
        from evalvault.domain.services.evaluator import RagasEvaluator

        evaluator = RagasEvaluator()
        assert "mrr" in evaluator.REFERENCE_REQUIRED_METRICS
        assert "ndcg" in evaluator.REFERENCE_REQUIRED_METRICS
        assert "hit_rate" in evaluator.REFERENCE_REQUIRED_METRICS


class TestIntegration:
    """Integration tests for retrieval metrics."""

    def test_all_metrics_same_input(self):
        """Test all metrics with the same input for consistency."""
        contexts = [
            "보장금액은 1억원입니다",  # Relevant (contains "1억원")
            "관련 없는 내용",
            "보험료는 10만원",
        ]
        ground_truth = "1억원"

        mrr = MRR()
        ndcg = NDCG(k=10)
        hit_rate = HitRate(k=3)

        mrr_score = mrr.score("", ground_truth, contexts)
        ndcg_score = ndcg.score("", ground_truth, contexts)
        hit_rate_score = hit_rate.score("", ground_truth, contexts)

        # First context is relevant (after Korean ending stripping)
        assert mrr_score == 1.0  # 1/1
        assert ndcg_score == 1.0  # Perfect ranking
        assert hit_rate_score == 1.0  # Hit found

    def test_korean_insurance_scenario(self):
        """Test with realistic Korean insurance Q&A scenario."""
        ground_truth = "1억원"  # Simpler ground truth
        contexts = [
            "해당 보험 상품의 월 보험료는 5만원입니다.",
            "사망 시 보장금액은 1억원이 지급됩니다.",  # Contains "1억원"
            "가입 연령은 만 19세부터 65세까지입니다.",
        ]

        mrr = MRR()
        ndcg = NDCG()
        hit_rate = HitRate()

        # Second context contains "1억원"
        mrr_score = mrr.score("", ground_truth, contexts)
        assert mrr_score == 0.5  # 1/2

        ndcg_score = ndcg.score("", ground_truth, contexts)
        assert ndcg_score < 1.0  # Not perfect ranking

        hit_rate_score = hit_rate.score("", ground_truth, contexts)
        assert hit_rate_score == 1.0  # Hit found in top 3

    def test_english_scenario(self):
        """Test with English content."""
        ground_truth = "premium $100"  # Simplified
        contexts = [
            "The coverage amount is $1 million",
            "Monthly premium is $100 per month",  # Contains "premium" and "$100"
            "Policy term is 20 years",
        ]

        mrr = MRR()
        mrr_score = mrr.score("", ground_truth, contexts)
        # Second context matches "premium" and "100"
        assert mrr_score == 0.5

    def test_multiple_relevant_contexts(self):
        """Test with multiple relevant contexts."""
        ground_truth = "1억원"
        contexts = [
            "보장금액 1억원",  # Relevant
            "관련없음",
            "1억원 지급",  # Also relevant
            "기타",
        ]

        mrr = MRR()
        ndcg = NDCG(k=4)

        # MRR only cares about first relevant
        mrr_score = mrr.score("", ground_truth, contexts)
        assert mrr_score == 1.0

        # NDCG considers all relevant - not perfectly optimal due to position 2 being irrelevant
        ndcg_score = ndcg.score("", ground_truth, contexts)
        assert ndcg_score > 0.9  # High but not perfect

        # Check detailed MRR
        mrr_detailed = mrr.score_detailed("", ground_truth, contexts)
        assert mrr_detailed["num_relevant"] == 2
