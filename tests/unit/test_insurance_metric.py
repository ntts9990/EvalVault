"""Unit tests for InsuranceTermAccuracy metric."""

import pytest

from evalvault.domain.metrics.insurance import InsuranceTermAccuracy


class TestInsuranceTermAccuracy:
    """Test suite for InsuranceTermAccuracy metric."""

    @pytest.fixture
    def metric(self):
        """Create InsuranceTermAccuracy metric instance."""
        return InsuranceTermAccuracy()

    def test_initialization_loads_dictionary(self, metric):
        """Test that initialization loads the terms dictionary."""
        assert len(metric.terms_dict) > 0
        assert "보험금" in metric.terms_dict
        assert "보험료" in metric.terms_dict

    def test_exact_match_korean_term(self, metric):
        """Test exact match of Korean insurance term."""
        text = "보험금은 1억원입니다."
        matches = metric._find_term_matches(text)
        assert "보험금" in matches

    def test_variant_match_korean_term(self, metric):
        """Test matching variant of Korean insurance term."""
        text = "보상금은 1억원입니다."
        matches = metric._find_term_matches(text)
        assert "보험금" in matches  # 보상금 is a variant of 보험금

    def test_english_term_match(self, metric):
        """Test matching English insurance term."""
        text = "The insurance premium is 50,000 won."
        matches = metric._find_term_matches(text)
        assert "보험료" in matches

    def test_multiple_terms_in_text(self, metric):
        """Test finding multiple insurance terms in text."""
        text = "피보험자는 보험금을 받으며, 보험료는 월 5만원입니다."
        matches = metric._find_term_matches(text)
        assert "피보험자" in matches
        assert "보험금" in matches
        assert "보험료" in matches

    def test_no_terms_in_text(self, metric):
        """Test text with no insurance terms."""
        text = "This is a simple sentence without insurance terminology."
        matches = metric._find_term_matches(text)
        assert len(matches) == 0

    def test_calculate_accuracy_perfect_match(self, metric):
        """Test accuracy calculation with perfect term matching."""
        answer = "보험금은 1억원이고, 보험료는 5만원입니다."
        contexts = ["보험금 지급액은 1억원이며, 월 보험료는 50,000원입니다."]

        accuracy = metric._calculate_accuracy(answer, contexts)
        assert accuracy == 1.0  # All terms in answer are in contexts

    def test_calculate_accuracy_partial_match(self, metric):
        """Test accuracy calculation with partial term matching."""
        answer = "보험금은 1억원이고, 보험료는 5만원이며, 특약은 3개입니다."
        contexts = ["보험금은 1억원입니다."]  # Only 보험금 matches

        accuracy = metric._calculate_accuracy(answer, contexts)
        assert 0 < accuracy < 1.0

    def test_calculate_accuracy_no_terms_in_answer(self, metric):
        """Test accuracy calculation when answer has no insurance terms."""
        answer = "The weather is nice today."
        contexts = ["It's a sunny day."]

        accuracy = metric._calculate_accuracy(answer, contexts)
        assert accuracy == 1.0  # No terms to check, perfect score

    def test_calculate_accuracy_case_insensitive(self, metric):
        """Test that accuracy calculation is case insensitive for English."""
        answer = "The INSURANCE PREMIUM is 50,000 won."
        contexts = ["The insurance premium is 50000 won."]

        accuracy = metric._calculate_accuracy(answer, contexts)
        assert accuracy == 1.0

    def test_score_returns_value_between_0_and_1(self, metric):
        """Test that score method returns value in [0, 1] range."""
        answer = "보험금은 1억원입니다."
        contexts = ["보험금 지급액은 1억원입니다."]

        score = metric.score(answer, contexts)
        assert 0.0 <= score <= 1.0

    def test_score_with_empty_answer(self, metric):
        """Test scoring with empty answer."""
        score = metric.score("", ["보험금은 1억원입니다."])
        assert score == 1.0  # No terms to check

    def test_score_with_empty_contexts(self, metric):
        """Test scoring with empty contexts."""
        score = metric.score("보험금은 1억원입니다.", [])
        assert score == 0.0  # No context to verify against

    def test_multiple_contexts_aggregation(self, metric):
        """Test that metric aggregates terms from multiple contexts."""
        answer = "보험금은 1억원이고, 보험료는 5만원입니다."
        contexts = ["보험금은 1억원입니다.", "보험료는 50,000원입니다."]

        accuracy = metric._calculate_accuracy(answer, contexts)
        assert accuracy == 1.0  # Both terms found across contexts

    def test_normalized_term_matching(self, metric):
        """Test that terms are normalized (whitespace removal)."""
        answer = "월 보험료는 5만원입니다."
        contexts = ["월보험료는 50,000원입니다."]

        accuracy = metric._calculate_accuracy(answer, contexts)
        assert accuracy == 1.0

    def test_common_insurance_terms_in_dictionary(self, metric):
        """Test that common insurance terms are in dictionary."""
        expected_terms = [
            "보험금",
            "보험료",
            "피보험자",
            "보험계약자",
            "면책기간",
            "보장내용",
            "해지환급금",
            "특약",
        ]

        for term in expected_terms:
            assert term in metric.terms_dict

    def test_term_has_canonical_and_variants(self, metric):
        """Test that each term has canonical form and variants."""
        term_data = metric.terms_dict["보험금"]
        assert "canonical" in term_data
        assert "variants" in term_data
        assert isinstance(term_data["variants"], list)
        assert len(term_data["variants"]) > 0

    def test_metric_name_constant(self, metric):
        """Test that metric has a name constant."""
        assert hasattr(metric, "name")
        assert metric.name == "insurance_term_accuracy"
