"""Tests for claim-level faithfulness functionality."""

import pytest

from evalvault.domain.entities import ClaimLevelResult, ClaimVerdict, MetricScore


class TestClaimVerdict:
    """Tests for ClaimVerdict dataclass."""

    def test_to_dict_returns_all_fields(self):
        """Verify to_dict includes all relevant fields."""
        verdict = ClaimVerdict(
            claim_id="tc-001-claim-0",
            claim_text="보험료 월 10만원",
            verdict="supported",
            confidence=0.95,
            reason="컨텍스트에 명시됨",
            source_context_indices=[0, 1],
        )

        result = verdict.to_dict()

        assert result["claim_id"] == "tc-001-claim-0"
        assert result["claim_text"] == "보험료 월 10만원"
        assert result["verdict"] == "supported"
        assert result["confidence"] == 0.95
        assert result["reason"] == "컨텍스트에 명시됨"
        assert result["source_context_indices"] == [0, 1]

    def test_to_dict_handles_none_values(self):
        """Verify to_dict handles None values correctly."""
        verdict = ClaimVerdict(
            claim_id="tc-001-claim-0",
            claim_text="테스트 claim",
            verdict="not_supported",
        )

        result = verdict.to_dict()

        assert result["confidence"] == 0.0
        assert result["reason"] is None
        assert result["source_context_indices"] is None


class TestClaimLevelResult:
    """Tests for ClaimLevelResult dataclass."""

    def test_support_rate_calculation(self):
        """Verify support_rate is calculated correctly."""
        claims = [
            ClaimVerdict("c1", "claim1", "supported"),
            ClaimVerdict("c2", "claim2", "supported"),
            ClaimVerdict("c3", "claim3", "not_supported"),
            ClaimVerdict("c4", "claim4", "partially_supported"),
        ]
        result = ClaimLevelResult(
            total_claims=4,
            supported_claims=2,
            not_supported_claims=1,
            partially_supported_claims=1,
            claims=claims,
        )

        assert result.support_rate == 0.5  # 2/4

    def test_support_rate_zero_claims(self):
        """Verify support_rate is 1.0 when no claims exist."""
        result = ClaimLevelResult(total_claims=0)

        assert result.support_rate == 1.0

    def test_to_dict_includes_all_fields(self):
        """Verify to_dict includes all fields."""
        claims = [
            ClaimVerdict("c1", "claim1", "supported", 0.9),
            ClaimVerdict("c2", "claim2", "not_supported", 0.1),
        ]
        result = ClaimLevelResult(
            total_claims=2,
            supported_claims=1,
            not_supported_claims=1,
            partially_supported_claims=0,
            claims=claims,
            extraction_method="korean_nlp",
        )

        d = result.to_dict()

        assert d["total_claims"] == 2
        assert d["supported_claims"] == 1
        assert d["not_supported_claims"] == 1
        assert d["partially_supported_claims"] == 0
        assert d["support_rate"] == 0.5
        assert d["extraction_method"] == "korean_nlp"
        assert len(d["claims"]) == 2


class TestMetricScoreWithClaimDetails:
    """Tests for MetricScore with claim_details."""

    def test_metric_score_without_claim_details(self):
        """Verify MetricScore works without claim_details."""
        score = MetricScore(name="faithfulness", score=0.8, threshold=0.7)

        assert score.passed is True
        assert score.claim_details is None

    def test_metric_score_with_claim_details(self):
        """Verify MetricScore includes claim_details in to_dict."""
        claim_details = ClaimLevelResult(
            total_claims=3,
            supported_claims=2,
            not_supported_claims=1,
            partially_supported_claims=0,
            claims=[
                ClaimVerdict("c1", "claim1", "supported", 0.9),
                ClaimVerdict("c2", "claim2", "supported", 0.85),
                ClaimVerdict("c3", "claim3", "not_supported", 0.2),
            ],
        )
        score = MetricScore(
            name="faithfulness",
            score=0.67,
            threshold=0.7,
            claim_details=claim_details,
        )

        result = score.to_dict()

        assert result["name"] == "faithfulness"
        assert result["score"] == 0.67
        assert result["passed"] is False
        assert "claim_details" in result
        assert result["claim_details"]["total_claims"] == 3
        assert result["claim_details"]["support_rate"] == pytest.approx(0.667, rel=0.01)


class TestEvaluatorConvertToClaimLevelResult:
    """Tests for evaluator claim conversion."""

    def test_convert_faithfulness_result(self):
        """Verify conversion from FaithfulnessResult to ClaimLevelResult."""
        from evalvault.domain.services.evaluator import RagasEvaluator

        # Mock FaithfulnessResult-like object
        class MockClaimVerification:
            def __init__(self, claim, is_faithful, coverage, matched_keywords=None):
                self.claim = claim
                self.is_faithful = is_faithful
                self.coverage = coverage
                self.matched_keywords = matched_keywords or []
                self.number_mismatch = False

        class MockFaithfulnessResult:
            def __init__(self):
                self.total_claims = 3
                self.faithful_claims = 2
                self.claim_results = [
                    MockClaimVerification("claim1", True, 0.9, ["키워드1"]),
                    MockClaimVerification("claim2", True, 0.8, ["키워드2"]),
                    MockClaimVerification("claim3", False, 0.2, []),
                ]

        evaluator = RagasEvaluator()
        mock_result = MockFaithfulnessResult()

        claim_level = evaluator._convert_to_claim_level_result(mock_result, test_case_id="tc-001")

        assert claim_level.total_claims == 3
        assert claim_level.supported_claims == 2
        assert claim_level.not_supported_claims == 1
        assert len(claim_level.claims) == 3

        # Check first supported claim
        assert claim_level.claims[0].verdict == "supported"
        assert claim_level.claims[0].claim_id == "tc-001-claim-0"

        # Check not supported claim
        assert claim_level.claims[2].verdict == "not_supported"

    def test_convert_handles_number_mismatch(self):
        """Verify conversion handles number_mismatch flag."""
        from evalvault.domain.services.evaluator import RagasEvaluator

        class MockClaimVerification:
            def __init__(self):
                self.claim = "보험료 100만원"
                self.is_faithful = False
                self.coverage = 0.5
                self.matched_keywords = []
                self.number_mismatch = True

        class MockFaithfulnessResult:
            def __init__(self):
                self.total_claims = 1
                self.faithful_claims = 0
                self.claim_results = [MockClaimVerification()]

        evaluator = RagasEvaluator()
        mock_result = MockFaithfulnessResult()

        claim_level = evaluator._convert_to_claim_level_result(mock_result, test_case_id="tc-002")

        assert claim_level.claims[0].verdict == "not_supported"
        assert "숫자 불일치" in (claim_level.claims[0].reason or "")


class TestEvaluatorFallbackKoreanFaithfulness:
    """Tests for Korean faithfulness fallback."""

    def test_fallback_returns_none_for_empty_response(self):
        """Verify fallback returns None for empty response."""
        from ragas import SingleTurnSample

        from evalvault.domain.services.evaluator import RagasEvaluator

        evaluator = RagasEvaluator()
        sample = SingleTurnSample(
            user_input="테스트 질문",
            response="",
            retrieved_contexts=["컨텍스트"],
        )

        result = evaluator._fallback_korean_faithfulness(sample)

        assert result is None

    def test_fallback_returns_none_for_empty_contexts(self):
        """Verify fallback returns None for empty contexts."""
        from ragas import SingleTurnSample

        from evalvault.domain.services.evaluator import RagasEvaluator

        evaluator = RagasEvaluator()
        sample = SingleTurnSample(
            user_input="테스트 질문",
            response="테스트 답변",
            retrieved_contexts=[],
        )

        result = evaluator._fallback_korean_faithfulness(sample)

        assert result is None
