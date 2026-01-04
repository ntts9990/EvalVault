"""Korean RAG Evaluation unit tests.

Tests for KoreanFaithfulnessChecker and KoreanSemanticSimilarity.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from tests.optional_deps import kiwi_ready

# Check if kiwipiepy is available
try:
    from evalvault.adapters.outbound.nlp.korean import (
        ClaimVerification,
        FaithfulnessResult,
        KiwiTokenizer,
        KoreanFaithfulnessChecker,
        KoreanSemanticSimilarity,
        SemanticSimilarityResult,
    )

    HAS_KIWI, KIWI_SKIP_REASON = kiwi_ready()
    KIWI_SKIP_REASON = KIWI_SKIP_REASON or "kiwipiepy unavailable"
except ImportError:
    HAS_KIWI = False
    KIWI_SKIP_REASON = "kiwipiepy not installed"
    # Define placeholders for type hints
    from dataclasses import dataclass, field

    @dataclass
    class ClaimVerification:  # type: ignore[no-redef]
        claim: str
        is_faithful: bool
        coverage: float
        matched_keywords: list[str] = field(default_factory=list)

    @dataclass
    class FaithfulnessResult:  # type: ignore[no-redef]
        is_faithful: bool
        score: float
        claim_results: list = field(default_factory=list)
        total_claims: int = 0
        faithful_claims: int = 0

    @dataclass
    class SemanticSimilarityResult:  # type: ignore[no-redef]
        similarity: float
        text1_keywords: list[str] = field(default_factory=list)
        text2_keywords: list[str] = field(default_factory=list)
        preprocessed: bool = False

    KiwiTokenizer = None  # type: ignore[misc,assignment]
    KoreanFaithfulnessChecker = None  # type: ignore[misc,assignment]
    KoreanSemanticSimilarity = None  # type: ignore[misc,assignment]


class TestClaimVerification:
    """ClaimVerification 데이터클래스 테스트."""

    def test_create_verification(self):
        """기본 검증 결과 생성."""
        result = ClaimVerification(
            claim="보험료 납입",
            is_faithful=True,
            coverage=0.8,
            matched_keywords=["보험료", "납입"],
        )

        assert result.claim == "보험료 납입"
        assert result.is_faithful is True
        assert result.coverage == 0.8
        assert result.matched_keywords == ["보험료", "납입"]

    def test_create_verification_default_keywords(self):
        """기본값으로 빈 키워드 리스트."""
        result = ClaimVerification(
            claim="테스트",
            is_faithful=False,
            coverage=0.2,
        )

        assert result.matched_keywords == []


class TestFaithfulnessResult:
    """FaithfulnessResult 데이터클래스 테스트."""

    def test_create_result(self):
        """기본 결과 생성."""
        result = FaithfulnessResult(
            is_faithful=True,
            score=0.9,
            claim_results=[],
            total_claims=5,
            faithful_claims=4,
        )

        assert result.is_faithful is True
        assert result.score == 0.9
        assert result.total_claims == 5
        assert result.faithful_claims == 4

    def test_create_result_defaults(self):
        """기본값 확인."""
        result = FaithfulnessResult(
            is_faithful=False,
            score=0.3,
        )

        assert result.claim_results == []
        assert result.total_claims == 0
        assert result.faithful_claims == 0


class TestSemanticSimilarityResult:
    """SemanticSimilarityResult 데이터클래스 테스트."""

    def test_create_result(self):
        """기본 결과 생성."""
        result = SemanticSimilarityResult(
            similarity=0.85,
            text1_keywords=["보험료", "납입"],
            text2_keywords=["보험료", "기간"],
            preprocessed=True,
        )

        assert result.similarity == 0.85
        assert result.text1_keywords == ["보험료", "납입"]
        assert result.preprocessed is True


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKoreanFaithfulnessChecker:
    """KoreanFaithfulnessChecker 테스트."""

    @pytest.fixture
    def tokenizer(self):
        """KiwiTokenizer 인스턴스."""
        return KiwiTokenizer()

    @pytest.fixture
    def checker(self, tokenizer):
        """FaithfulnessChecker 인스턴스."""
        return KoreanFaithfulnessChecker(tokenizer)

    def test_init_default(self, tokenizer):
        """기본 초기화."""
        checker = KoreanFaithfulnessChecker(tokenizer)

        assert checker._min_coverage == 0.5
        assert "NNG" in checker._claim_pos_tags
        assert "VV" in checker._claim_pos_tags

    def test_init_custom(self, tokenizer):
        """커스텀 초기화."""
        checker = KoreanFaithfulnessChecker(
            tokenizer,
            min_coverage=0.7,
            claim_pos_tags=["NNG", "NNP"],
        )

        assert checker._min_coverage == 0.7
        assert checker._claim_pos_tags == ["NNG", "NNP"]

    def test_extract_claims(self, checker):
        """주장 추출 테스트."""
        text = "보험료 납입 기간은 20년입니다. 보장금액은 1억원입니다."

        claims = checker.extract_claims(text)

        # 각 문장에서 키워드 추출됨
        assert len(claims) >= 1
        # 주장에 핵심 키워드가 포함되어야 함
        all_claims = " ".join(claims)
        assert "보험료" in all_claims or "납입" in all_claims

    def test_extract_claims_single_sentence(self, checker):
        """단일 문장 주장 추출."""
        text = "보험료는 월 10만원입니다"

        claims = checker.extract_claims(text)

        assert len(claims) >= 1

    def test_extract_claims_empty(self, checker):
        """빈 텍스트 주장 추출."""
        claims = checker.extract_claims("")

        assert claims == []

    def test_verify_claim_faithful(self, checker):
        """충실한 주장 검증."""
        claim = "보험료 납입"
        context_keywords = {"보험료", "납입", "기간", "20년"}

        result = checker.verify_claim(claim, context_keywords)

        assert result.is_faithful is True
        assert result.coverage >= 0.5
        assert len(result.matched_keywords) > 0

    def test_verify_claim_not_faithful(self, checker):
        """충실하지 않은 주장 검증."""
        claim = "사망보험금 지급"
        context_keywords = {"보험료", "납입", "기간"}

        result = checker.verify_claim(claim, context_keywords)

        # 겹치는 키워드가 없으므로 충실하지 않음
        assert result.is_faithful is False
        assert result.coverage < 0.5

    def test_verify_claim_empty(self, checker):
        """빈 주장 검증."""
        claim = ""
        context_keywords = {"보험료", "납입"}

        result = checker.verify_claim(claim, context_keywords)

        # 키워드가 없으면 충실함으로 간주
        assert result.is_faithful is True
        assert result.coverage == 1.0

    def test_check_faithfulness_fully_faithful(self, checker):
        """완전히 충실한 답변 검증."""
        answer = "보험료 납입 기간은 20년입니다."
        contexts = ["이 보험의 보험료 납입 기간은 20년이며, 보장금액은 1억원입니다."]

        result = checker.check_faithfulness(answer, contexts)

        assert result.is_faithful is True
        assert result.score >= 0.5
        assert result.total_claims >= 1

    def test_check_faithfulness_partially_faithful(self, checker):
        """부분적으로 충실한 답변 검증."""
        answer = "보험료는 월 10만원이고, 해약환급금은 80%입니다."
        contexts = ["이 보험의 보험료는 월 10만원입니다."]

        result = checker.check_faithfulness(answer, contexts)

        # 일부만 컨텍스트에 있으므로 부분 충실
        assert result.total_claims >= 1
        # 점수는 0~1 사이
        assert 0.0 <= result.score <= 1.0

    def test_check_faithfulness_empty_answer(self, checker):
        """빈 답변 검증."""
        result = checker.check_faithfulness("", ["컨텍스트"])

        assert result.is_faithful is True
        assert result.score == 1.0
        assert result.total_claims == 0

    def test_check_faithfulness_empty_context(self, checker):
        """빈 컨텍스트 검증."""
        result = checker.check_faithfulness("답변", [])

        assert result.is_faithful is True
        assert result.score == 1.0

    def test_calculate_keyword_overlap(self, checker):
        """키워드 겹침 계산."""
        question = "보험료 납입 기간은 얼마인가요?"
        contexts = ["보험료 납입 기간은 20년입니다. 보장금액은 1억원입니다."]

        overlap = checker.calculate_keyword_overlap(question, contexts)

        # 겹침 비율이 0보다 커야 함
        assert overlap > 0.0
        assert overlap <= 1.0

    def test_calculate_keyword_overlap_no_context(self, checker):
        """컨텍스트 없는 경우 겹침 계산."""
        overlap = checker.calculate_keyword_overlap("질문", None)

        assert overlap == 0.0

    def test_calculate_keyword_overlap_empty_context(self, checker):
        """빈 컨텍스트 리스트."""
        overlap = checker.calculate_keyword_overlap("질문", [])

        assert overlap == 0.0

    def test_morphological_normalization(self, checker):
        """형태소 분석을 통한 정규화 확인."""
        # 조사 변형이 있어도 같은 키워드로 인식되어야 함
        answer1 = "보험료가 있습니다"
        answer2 = "보험료를 확인합니다"

        claims1 = checker.extract_claims(answer1)
        claims2 = checker.extract_claims(answer2)

        # 둘 다 '보험료'를 추출해야 함
        all_claims1 = " ".join(claims1)
        all_claims2 = " ".join(claims2)

        # 형태소 분석으로 조사가 제거됨
        assert "보험료" in all_claims1 or len(claims1) > 0
        assert "보험료" in all_claims2 or len(claims2) > 0


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKoreanSemanticSimilarity:
    """KoreanSemanticSimilarity 테스트."""

    @pytest.fixture
    def tokenizer(self):
        """KiwiTokenizer 인스턴스."""
        return KiwiTokenizer()

    @pytest.fixture
    def similarity_calculator(self, tokenizer):
        """SemanticSimilarity 인스턴스 (임베딩 없이)."""
        return KoreanSemanticSimilarity(tokenizer)

    @pytest.fixture
    def similarity_with_embedding(self, tokenizer):
        """임베딩 함수를 가진 SemanticSimilarity 인스턴스."""

        def mock_embedding_func(texts: list[str]) -> list[list[float]]:
            # 간단한 모킹: 텍스트 길이 기반 임베딩
            return [[len(t) * 0.1, len(t) * 0.2, 0.5] for t in texts]

        return KoreanSemanticSimilarity(tokenizer, embedding_func=mock_embedding_func)

    def test_init_default(self, tokenizer):
        """기본 초기화."""
        calc = KoreanSemanticSimilarity(tokenizer)

        assert calc._use_preprocessing is True
        assert calc._embedding_func is None

    def test_init_custom(self, tokenizer):
        """커스텀 초기화."""
        mock_func = MagicMock()
        calc = KoreanSemanticSimilarity(
            tokenizer,
            embedding_func=mock_func,
            use_preprocessing=False,
            keyword_pos_tags=["NNG"],
        )

        assert calc._use_preprocessing is False
        assert calc._embedding_func is mock_func
        assert calc._keyword_pos_tags == ["NNG"]

    def test_preprocess(self, similarity_calculator):
        """전처리 테스트."""
        text = "보험료가 얼마인가요?"

        preprocessed, keywords = similarity_calculator.preprocess(text)

        # 조사/어미가 제거된 키워드만 남음
        assert len(keywords) > 0
        # 전처리된 텍스트는 키워드의 연결
        assert preprocessed == " ".join(keywords)

    def test_preprocess_empty(self, similarity_calculator):
        """빈 텍스트 전처리."""
        preprocessed, keywords = similarity_calculator.preprocess("")

        assert preprocessed == ""
        assert keywords == []

    def test_calculate_jaccard_similar(self, similarity_calculator):
        """Jaccard 유사도 - 유사한 텍스트."""
        text1 = "보험료 납입 기간"
        text2 = "보험료 납입 방법"

        result = similarity_calculator.calculate(text1, text2)

        # 공통 키워드가 있으므로 유사도 > 0
        assert result.similarity > 0.0
        assert result.preprocessed is True
        assert len(result.text1_keywords) > 0
        assert len(result.text2_keywords) > 0

    def test_calculate_jaccard_different(self, similarity_calculator):
        """Jaccard 유사도 - 다른 텍스트."""
        text1 = "보험료 납입"
        text2 = "해약환급금 지급"

        result = similarity_calculator.calculate(text1, text2)

        # 공통 키워드가 적으므로 유사도 낮음
        assert result.similarity < 0.5

    def test_calculate_jaccard_identical(self, similarity_calculator):
        """Jaccard 유사도 - 동일 텍스트."""
        text = "보험료 납입 기간"

        result = similarity_calculator.calculate(text, text)

        assert result.similarity == 1.0

    def test_calculate_without_preprocessing(self, similarity_calculator):
        """전처리 없이 계산."""
        text1 = "보험료가"
        text2 = "보험료를"

        result = similarity_calculator.calculate(text1, text2, use_preprocessing=False)

        assert result.preprocessed is False
        # 전처리 없이는 키워드가 비어있음
        assert result.text1_keywords == []
        assert result.text2_keywords == []

    def test_calculate_with_embedding(self, similarity_with_embedding):
        """임베딩 기반 유사도 계산."""
        text1 = "보험료 납입"
        text2 = "보험료 납입"

        result = similarity_with_embedding.calculate(text1, text2)

        # 코사인 유사도는 -1 ~ 1 범위 (부동소수점 오차 허용)
        assert -1.0 - 1e-9 <= result.similarity <= 1.0 + 1e-9
        assert result.preprocessed is True

    def test_calculate_batch(self, similarity_calculator):
        """배치 유사도 계산."""
        texts1 = ["보험료 납입", "보장금액 확인"]
        texts2 = ["보험료 기간", "보장금액 조회"]

        results = similarity_calculator.calculate_batch(texts1, texts2)

        assert len(results) == 2
        assert all(isinstance(r, SemanticSimilarityResult) for r in results)

    def test_calculate_batch_length_mismatch(self, similarity_calculator):
        """배치 길이 불일치 에러."""
        texts1 = ["텍스트1", "텍스트2"]
        texts2 = ["텍스트1"]

        with pytest.raises(ValueError, match="same length"):
            similarity_calculator.calculate_batch(texts1, texts2)

    def test_jaccard_similarity_empty(self, similarity_calculator):
        """빈 리스트 Jaccard 유사도."""
        # 둘 다 빈 경우
        result = similarity_calculator._jaccard_similarity([], [])
        assert result == 1.0

        # 하나만 빈 경우
        result = similarity_calculator._jaccard_similarity(["a"], [])
        assert result == 0.0

    def test_cosine_similarity(self, similarity_calculator):
        """코사인 유사도 계산."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        result = similarity_calculator._cosine_similarity(vec1, vec2)

        assert np.isclose(result, 1.0)

    def test_cosine_similarity_orthogonal(self, similarity_calculator):
        """직교 벡터 코사인 유사도."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])

        result = similarity_calculator._cosine_similarity(vec1, vec2)

        assert np.isclose(result, 0.0)

    def test_cosine_similarity_zero_vector(self, similarity_calculator):
        """영벡터 코사인 유사도."""
        vec1 = np.array([0.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        result = similarity_calculator._cosine_similarity(vec1, vec2)

        assert result == 0.0


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestIntegration:
    """통합 테스트."""

    @pytest.fixture
    def tokenizer(self):
        """KiwiTokenizer 인스턴스."""
        return KiwiTokenizer()

    def test_faithfulness_with_similarity(self, tokenizer):
        """Faithfulness와 Similarity 통합 테스트."""
        checker = KoreanFaithfulnessChecker(tokenizer)
        similarity = KoreanSemanticSimilarity(tokenizer)

        answer = "보험료 납입 기간은 20년입니다."
        context = "이 보험의 보험료 납입 기간은 20년이며, 보장금액은 1억원입니다."
        ground_truth = "납입 기간 20년"

        # Faithfulness 검증
        faithfulness_result = checker.check_faithfulness(answer, [context])
        assert faithfulness_result.is_faithful is True

        # 의미 유사도 검증 (answer vs ground_truth)
        similarity_result = similarity.calculate(answer, ground_truth)
        assert similarity_result.similarity > 0.0

    def test_keyword_overlap_improvement(self, tokenizer):
        """형태소 분석 기반 키워드 겹침 개선 테스트."""
        checker = KoreanFaithfulnessChecker(tokenizer)

        # 조사가 다르지만 같은 의미
        question = "보험료가 얼마인가요?"
        contexts = ["보험료는 월 10만원입니다."]

        overlap = checker.calculate_keyword_overlap(question, contexts)

        # 형태소 분석으로 조사 제거 후 '보험료' 매칭
        assert overlap > 0.0

    def test_particle_variation_handling(self, tokenizer):
        """조사 변형 처리 테스트."""
        similarity = KoreanSemanticSimilarity(tokenizer)

        # 조사만 다른 문장들
        text1 = "보험료가 납입됩니다"
        text2 = "보험료를 납입합니다"
        text3 = "보험료는 납입되었습니다"

        # 조사/어미 제거 후 유사도가 높아야 함
        result1_2 = similarity.calculate(text1, text2)
        result1_3 = similarity.calculate(text1, text3)

        # 핵심 키워드(보험료, 납입)가 같으므로 유사도 높음
        assert result1_2.similarity > 0.3
        assert result1_3.similarity > 0.3
