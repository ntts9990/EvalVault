"""Tests for NoAnswerAccuracy metric."""

import pytest

from evalvault.domain.metrics.no_answer import (
    NoAnswerAccuracy,
    is_no_answer,
)


class TestIsNoAnswer:
    """Tests for is_no_answer utility function."""

    def test_empty_string(self):
        assert is_no_answer("") is True

    def test_whitespace_only(self):
        assert is_no_answer("   ") is True

    def test_none_like(self):
        assert is_no_answer("없음") is True
        assert is_no_answer("None") is True
        assert is_no_answer("N/A") is True
        assert is_no_answer("n/a") is True

    def test_korean_no_answer_patterns(self):
        """Test Korean no-answer patterns."""
        patterns = [
            "정보 없음",
            "정보없음",
            "답변 불가",
            "답변불가",
            "알 수 없습니다",
            "확인 불가",
            "찾을 수 없습니다",
            "문서에 없습니다",
            "해당 정보가 없습니다",
            "관련 정보 없음",
            "언급되어 있지 않습니다",
            "명시되어 있지 않습니다",
            "존재하지 않습니다",
            "나와 있지 않습니다",
            "확인되지 않았습니다",
            "답변 드리기 어렵습니다",
        ]
        for pattern in patterns:
            assert is_no_answer(pattern) is True, f"Failed for: {pattern}"

    def test_english_no_answer_patterns(self):
        """Test English no-answer patterns."""
        patterns = [
            "No answer",
            "No information available",
            "Not found",
            "Cannot answer",
            "Unable to answer",
            "I don't know",
            "I do not know",
            "Not mentioned in the document",
            "Not specified",
            "Insufficient information",
            "Cannot determine",
            "Unknown",
        ]
        for pattern in patterns:
            assert is_no_answer(pattern) is True, f"Failed for: {pattern}"

    def test_valid_answers(self):
        """Test that valid answers are not detected as no-answer."""
        valid_answers = [
            "1억원입니다",
            "보험료는 월 5만원입니다",
            "The premium is $100",
            "보장기간은 20년입니다",
            "Yes, it covers hospitalization",
            "사망보험금 1억원",
            "This insurance covers fire damage",
        ]
        for answer in valid_answers:
            assert is_no_answer(answer) is False, f"False positive for: {answer}"

    def test_numbers_not_no_answer(self):
        """Numbers should not be considered no-answer."""
        assert is_no_answer("1억원") is False
        assert is_no_answer("100") is False
        assert is_no_answer("5만원") is False


class TestNoAnswerAccuracy:
    """Tests for NoAnswerAccuracy metric."""

    @pytest.fixture
    def metric(self):
        return NoAnswerAccuracy()

    def test_both_no_answer_korean(self, metric):
        """Both indicate no answer (Korean) - correct abstention."""
        score = metric.score(answer="정보 없음", ground_truth="정보 없음")
        assert score == 1.0

    def test_both_no_answer_english(self, metric):
        """Both indicate no answer (English) - correct abstention."""
        score = metric.score(answer="No information available", ground_truth="N/A")
        assert score == 1.0

    def test_both_have_answer(self, metric):
        """Both provide answers - correct behavior."""
        score = metric.score(answer="1억원입니다", ground_truth="1억원")
        assert score == 1.0

    def test_hallucination_korean(self, metric):
        """Model answers when should abstain - hallucination."""
        score = metric.score(answer="1억원입니다", ground_truth="정보 없음")
        assert score == 0.0

    def test_hallucination_english(self, metric):
        """Model answers when should abstain - hallucination (English)."""
        score = metric.score(answer="The coverage is $100,000", ground_truth="N/A")
        assert score == 0.0

    def test_false_abstention_korean(self, metric):
        """Model abstains when answer exists - false abstention."""
        score = metric.score(answer="정보 없음", ground_truth="1억원")
        assert score == 0.0

    def test_false_abstention_english(self, metric):
        """Model abstains when answer exists - false abstention (English)."""
        score = metric.score(answer="Cannot determine", ground_truth="$100,000")
        assert score == 0.0

    def test_empty_answer_as_no_answer(self, metric):
        """Empty answer treated as no-answer."""
        score = metric.score(answer="", ground_truth="정보 없음")
        assert score == 1.0

        score = metric.score(answer="", ground_truth="1억원")
        assert score == 0.0

    def test_contexts_unused(self, metric):
        """Contexts parameter should be accepted but unused."""
        score = metric.score(
            answer="정보 없음",
            ground_truth="정보 없음",
            contexts=["some context"],
        )
        assert score == 1.0


class TestNoAnswerAccuracyDetailed:
    """Tests for detailed scoring."""

    @pytest.fixture
    def metric(self):
        return NoAnswerAccuracy()

    def test_true_abstention(self, metric):
        """Test true abstention classification."""
        result = metric.score_detailed(
            answer="정보 없음",
            ground_truth="정보 없음",
        )
        assert result["score"] == 1.0
        assert result["classification"] == "true_abstention"
        assert result["answer_is_no_answer"] is True
        assert result["ground_truth_is_no_answer"] is True

    def test_hallucination(self, metric):
        """Test hallucination classification."""
        result = metric.score_detailed(
            answer="보험금은 1억원입니다",
            ground_truth="정보 없음",
        )
        assert result["score"] == 0.0
        assert result["classification"] == "hallucination"
        assert result["answer_is_no_answer"] is False
        assert result["ground_truth_is_no_answer"] is True

    def test_false_abstention(self, metric):
        """Test false abstention classification."""
        result = metric.score_detailed(
            answer="답변 불가",
            ground_truth="1억원",
        )
        assert result["score"] == 0.0
        assert result["classification"] == "false_abstention"
        assert result["answer_is_no_answer"] is True
        assert result["ground_truth_is_no_answer"] is False

    def test_true_answer(self, metric):
        """Test true answer classification."""
        result = metric.score_detailed(
            answer="보험금은 1억원입니다",
            ground_truth="1억원",
        )
        assert result["score"] == 1.0
        assert result["classification"] == "true_answer"
        assert result["answer_is_no_answer"] is False
        assert result["ground_truth_is_no_answer"] is False


class TestNoAnswerAccuracyCustomPatterns:
    """Tests for custom pattern support."""

    def test_custom_patterns(self):
        """Test adding custom no-answer patterns."""
        custom_patterns = [r"모르겠어요", r"잘\s*모르겠"]
        metric = NoAnswerAccuracy(custom_patterns=custom_patterns)

        # Custom pattern should be detected
        assert metric._check_no_answer("모르겠어요") is True
        assert metric._check_no_answer("잘 모르겠습니다") is True

    def test_strict_mode(self):
        """Test strict mode behavior."""
        metric_strict = NoAnswerAccuracy(strict_mode=True)
        metric_normal = NoAnswerAccuracy(strict_mode=False)

        # Short response without explicit marker
        short_response = "없음"

        # Both should detect this as no-answer (it's in the patterns)
        assert metric_strict._check_no_answer(short_response) is True
        assert metric_normal._check_no_answer(short_response) is True


class TestMetricIntegration:
    """Integration tests for metric with evaluator."""

    def test_metric_has_name(self):
        metric = NoAnswerAccuracy()
        assert metric.name == "no_answer_accuracy"

    def test_metric_in_custom_map(self):
        """Verify metric is registered in evaluator."""
        from evalvault.domain.services.evaluator import RagasEvaluator

        evaluator = RagasEvaluator()
        assert "no_answer_accuracy" in evaluator.CUSTOM_METRIC_MAP

    def test_metric_requires_reference(self):
        """Verify metric is marked as requiring reference."""
        from evalvault.domain.services.evaluator import RagasEvaluator

        evaluator = RagasEvaluator()
        assert "no_answer_accuracy" in evaluator.REFERENCE_REQUIRED_METRICS


class TestInsuranceDomainCases:
    """Test cases specific to insurance domain."""

    @pytest.fixture
    def metric(self):
        return NoAnswerAccuracy()

    def test_insurance_no_coverage_info(self, metric):
        """보장 정보 없음 케이스."""
        score = metric.score(
            answer="해당 보장에 대한 정보가 문서에 없습니다.",
            ground_truth="정보 없음",
        )
        assert score == 1.0

    def test_insurance_premium_not_specified(self, metric):
        """보험료 미명시 케이스."""
        score = metric.score(
            answer="보험료에 대한 내용이 확인되지 않았습니다.",
            ground_truth="정보 없음",
        )
        assert score == 1.0

    def test_insurance_hallucinated_premium(self, metric):
        """보험료 환각 케이스 - 문서에 없는데 답변함."""
        score = metric.score(
            answer="월 보험료는 10만원입니다.",
            ground_truth="정보 없음",
        )
        assert score == 0.0

    def test_insurance_missed_info(self, metric):
        """정보가 있는데 없다고 답변한 케이스."""
        score = metric.score(
            answer="해당 정보를 찾을 수 없습니다.",
            ground_truth="월 5만원",
        )
        assert score == 0.0

    def test_insurance_correct_answer(self, metric):
        """올바르게 답변한 케이스."""
        score = metric.score(
            answer="이 보험의 사망보험금은 1억원입니다.",
            ground_truth="사망보험금 1억원",
        )
        assert score == 1.0

    def test_mixed_language_response(self, metric):
        """한영 혼합 응답."""
        score = metric.score(
            answer="Sorry, 해당 정보 없음",
            ground_truth="N/A",
        )
        assert score == 1.0
