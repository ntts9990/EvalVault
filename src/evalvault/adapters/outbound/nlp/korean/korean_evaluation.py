"""Korean RAG Evaluation utilities.

한국어 RAG 평가를 위한 유틸리티 클래스들을 제공합니다:
- KoreanFaithfulnessChecker: 한국어 Faithfulness 검증
- KoreanSemanticSimilarity: 한국어 의미 유사도 계산

Example:
    >>> from evalvault.adapters.outbound.nlp.korean import (
    ...     KoreanFaithfulnessChecker,
    ...     KoreanSemanticSimilarity,
    ...     KiwiTokenizer,
    ... )
    >>> tokenizer = KiwiTokenizer()
    >>> checker = KoreanFaithfulnessChecker(tokenizer)
    >>> result = checker.check_faithfulness(
    ...     answer="보험료는 월 10만원입니다.",
    ...     contexts=["이 보험의 보험료는 월 10만원이며, 납입 기간은 20년입니다."]
    ... )
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable

    from evalvault.adapters.outbound.nlp.korean.kiwi_tokenizer import KiwiTokenizer

logger = logging.getLogger(__name__)

# 숫자 패턴 (금액, 기간, 비율 등)
NUMBER_PATTERNS = [
    # 금액 패턴
    r"(\d+(?:,\d{3})*)\s*(?:만원|천원|백원|원|억원)",
    r"(\d+)\s*(?:만|천|백|억)\s*원",
    # 기간 패턴
    r"(\d+)\s*(?:년|개월|월|일|세)",
    # 비율 패턴
    r"(\d+(?:\.\d+)?)\s*%",
    # 일반 숫자
    r"(\d+(?:,\d{3})*(?:\.\d+)?)",
]


@dataclass
class NumberWithUnit:
    """숫자와 단위 정보."""

    value: float
    unit: str
    original: str  # 원본 텍스트


@dataclass
class ClaimVerification:
    """단일 주장(claim) 검증 결과.

    Attributes:
        claim: 검증된 주장 텍스트
        is_faithful: 컨텍스트에 충실한지 여부
        coverage: 키워드 겹침 비율 (0.0 ~ 1.0)
        matched_keywords: 겹친 키워드 목록
        number_mismatch: 숫자 불일치 여부
    """

    claim: str
    is_faithful: bool
    coverage: float
    matched_keywords: list[str] = field(default_factory=list)
    number_mismatch: bool = False


@dataclass
class FaithfulnessResult:
    """Faithfulness 검증 결과.

    Attributes:
        is_faithful: 전체 답변이 충실한지 여부
        score: Faithfulness 점수 (0.0 ~ 1.0)
        claim_results: 각 주장별 검증 결과
        total_claims: 총 주장 수
        faithful_claims: 충실한 주장 수
    """

    is_faithful: bool
    score: float
    claim_results: list[ClaimVerification] = field(default_factory=list)
    total_claims: int = 0
    faithful_claims: int = 0


@dataclass
class SemanticSimilarityResult:
    """의미 유사도 계산 결과.

    Attributes:
        similarity: 코사인 유사도 점수 (-1.0 ~ 1.0)
        text1_keywords: 텍스트1에서 추출된 키워드
        text2_keywords: 텍스트2에서 추출된 키워드
        preprocessed: 전처리 사용 여부
    """

    similarity: float
    text1_keywords: list[str] = field(default_factory=list)
    text2_keywords: list[str] = field(default_factory=list)
    preprocessed: bool = True


class KoreanFaithfulnessChecker:
    """한국어 Faithfulness 검증기.

    한국어의 교착어 특성을 고려하여 faithfulness를 검증합니다:
    - 조사 변형 무시 (보험료가/보험료를/보험료는 → 보험료)
    - 어미 변형 무시 (지급됩니다/지급되며/지급하고 → 지급)
    - 형태소 분석 기반 키워드 매칭

    Example:
        >>> tokenizer = KiwiTokenizer()
        >>> checker = KoreanFaithfulnessChecker(tokenizer)
        >>> result = checker.check_faithfulness(
        ...     answer="보험료는 월 10만원입니다.",
        ...     contexts=["이 보험의 보험료는 월 10만원입니다."]
        ... )
        >>> print(result.score)  # 1.0 (완전히 충실)
    """

    def __init__(
        self,
        tokenizer: KiwiTokenizer,
        *,
        min_coverage: float = 0.5,
        claim_pos_tags: list[str] | None = None,
        check_numbers: bool = True,
    ) -> None:
        """KoreanFaithfulnessChecker 초기화.

        Args:
            tokenizer: KiwiTokenizer 인스턴스
            min_coverage: 충실함 판정을 위한 최소 키워드 겹침 비율 (기본: 0.5)
            claim_pos_tags: 주장 추출에 사용할 품사 태그 (기본: 명사, 동사, 형용사)
            check_numbers: 숫자 값 비교 여부 (기본: True)
        """
        self._tokenizer = tokenizer
        self._min_coverage = min_coverage
        self._claim_pos_tags = claim_pos_tags or ["NNG", "NNP", "VV", "VA", "NNB"]
        self._check_numbers = check_numbers
        # 숫자+단위 패턴 컴파일
        self._number_pattern = re.compile(
            r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(만원|천원|백원|원|억원|만|천|백|억|년|개월|월|일|세|%)?",
            re.UNICODE,
        )

    def extract_claims(self, text: str) -> list[str]:
        """텍스트에서 주장(claim)을 추출합니다.

        형태소 분석을 통해 문장 단위로 핵심 명사구/동사구를 추출합니다.

        Args:
            text: 분석할 텍스트

        Returns:
            추출된 주장 리스트 (각 문장의 핵심 키워드)
        """
        claims = []

        # 문장 분리
        sentences = self._tokenizer.split_sentences(text)
        if not sentences:
            sentences = [text]

        for sentence in sentences:
            if not sentence.strip():
                continue

            # 각 문장에서 핵심 키워드 추출
            keywords = self._tokenizer.extract_keywords(sentence, pos_tags=self._claim_pos_tags)

            if keywords:
                # 키워드를 공백으로 연결하여 주장으로 변환
                claim = " ".join(keywords)
                claims.append(claim)

        return claims

    def extract_numbers(self, text: str) -> list[NumberWithUnit]:
        """텍스트에서 숫자와 단위를 추출합니다.

        Args:
            text: 분석할 텍스트

        Returns:
            NumberWithUnit 리스트
        """
        numbers = []
        for match in self._number_pattern.finditer(text):
            value_str = match.group(1).replace(",", "")
            unit = match.group(2) or ""
            try:
                value = float(value_str)
                numbers.append(NumberWithUnit(value=value, unit=unit, original=match.group(0)))
            except ValueError:
                continue
        return numbers

    def check_number_mismatch(
        self,
        answer_text: str,
        context_text: str,
    ) -> tuple[bool, list[str]]:
        """답변과 컨텍스트의 숫자 불일치를 확인합니다.

        Args:
            answer_text: 답변 텍스트
            context_text: 컨텍스트 텍스트

        Returns:
            (불일치 여부, 불일치 상세 리스트)
        """
        answer_numbers = self.extract_numbers(answer_text)
        context_numbers = self.extract_numbers(context_text)

        if not answer_numbers:
            return False, []

        # 컨텍스트에서 동일 단위의 숫자들을 수집
        context_by_unit: dict[str, set[float]] = {}
        for num in context_numbers:
            if num.unit not in context_by_unit:
                context_by_unit[num.unit] = set()
            context_by_unit[num.unit].add(num.value)

        mismatches = []
        for ans_num in answer_numbers:
            # 같은 단위의 숫자가 컨텍스트에 있는지 확인
            if (
                ans_num.unit in context_by_unit
                and ans_num.value not in context_by_unit[ans_num.unit]
            ):
                # 컨텍스트에 다른 값이 있음 = 불일치
                ctx_values = context_by_unit[ans_num.unit]
                mismatches.append(
                    f"{ans_num.original} (context has: {', '.join(str(v) + ans_num.unit for v in ctx_values)})"
                )

        return len(mismatches) > 0, mismatches

    def verify_claim(
        self,
        claim: str,
        context_keywords: set[str],
        context_text: str = "",
        original_claim_text: str = "",
    ) -> ClaimVerification:
        """단일 주장을 컨텍스트 대비 검증합니다.

        Args:
            claim: 검증할 주장 (키워드 형태)
            context_keywords: 컨텍스트에서 추출된 키워드 집합
            context_text: 원본 컨텍스트 텍스트 (숫자 비교용)
            original_claim_text: 원본 주장 텍스트 (숫자 비교용)

        Returns:
            ClaimVerification 결과
        """
        # 주장의 키워드 추출
        claim_keywords = set(self._tokenizer.extract_keywords(claim))

        if not claim_keywords:
            # 키워드가 없으면 충실함으로 간주
            return ClaimVerification(
                claim=claim,
                is_faithful=True,
                coverage=1.0,
                matched_keywords=[],
            )

        # 키워드 겹침 계산
        matched = claim_keywords & context_keywords
        coverage = len(matched) / len(claim_keywords)

        is_faithful = coverage >= self._min_coverage
        number_mismatch = False

        # 숫자 비교 (활성화된 경우)
        if self._check_numbers and context_text and original_claim_text:
            has_mismatch, _ = self.check_number_mismatch(original_claim_text, context_text)
            if has_mismatch:
                number_mismatch = True
                is_faithful = False  # 숫자 불일치 시 불충실

        return ClaimVerification(
            claim=claim,
            is_faithful=is_faithful,
            coverage=coverage,
            matched_keywords=list(matched),
            number_mismatch=number_mismatch,
        )

    def check_faithfulness(
        self,
        answer: str,
        contexts: list[str],
    ) -> FaithfulnessResult:
        """답변의 faithfulness를 컨텍스트 대비 검증합니다.

        Args:
            answer: 검증할 답변
            contexts: 참조 컨텍스트 리스트

        Returns:
            FaithfulnessResult 결과
        """
        if not answer or not contexts:
            return FaithfulnessResult(
                is_faithful=True,
                score=1.0,
                claim_results=[],
                total_claims=0,
                faithful_claims=0,
            )

        # 컨텍스트에서 키워드 추출
        context_text = " ".join(contexts)
        context_keywords = set(
            self._tokenizer.extract_keywords(context_text, pos_tags=self._claim_pos_tags)
        )

        # 전체 답변에서 숫자 불일치 먼저 확인
        if self._check_numbers:
            has_number_mismatch, mismatch_details = self.check_number_mismatch(answer, context_text)
            if has_number_mismatch:
                # 숫자 불일치가 있으면 불충실로 판정
                return FaithfulnessResult(
                    is_faithful=False,
                    score=0.0,
                    claim_results=[
                        ClaimVerification(
                            claim=answer,
                            is_faithful=False,
                            coverage=0.0,
                            matched_keywords=[],
                            number_mismatch=True,
                        )
                    ],
                    total_claims=1,
                    faithful_claims=0,
                )

        # 답변에서 주장 추출
        claims = self.extract_claims(answer)
        # 원본 문장도 보존 (숫자 비교용)
        sentences = self._tokenizer.split_sentences(answer)
        if not sentences:
            sentences = [answer]

        if not claims:
            return FaithfulnessResult(
                is_faithful=True,
                score=1.0,
                claim_results=[],
                total_claims=0,
                faithful_claims=0,
            )

        # 각 주장 검증
        claim_results = []
        faithful_count = 0

        for i, claim in enumerate(claims):
            original_text = sentences[i] if i < len(sentences) else ""
            result = self.verify_claim(
                claim,
                context_keywords,
                context_text=context_text,
                original_claim_text=original_text,
            )
            claim_results.append(result)
            if result.is_faithful:
                faithful_count += 1

        # 전체 점수 계산
        score = faithful_count / len(claims) if claims else 1.0
        is_faithful = score >= self._min_coverage

        return FaithfulnessResult(
            is_faithful=is_faithful,
            score=score,
            claim_results=claim_results,
            total_claims=len(claims),
            faithful_claims=faithful_count,
        )

    def calculate_keyword_overlap(
        self,
        question: str,
        contexts: list[str] | None,
    ) -> float:
        """질문과 컨텍스트 간 형태소 기반 키워드 겹침 비율을 계산합니다.

        CausalAnalysisAdapter의 keyword_overlap 계산을 개선합니다.

        Args:
            question: 질문 텍스트
            contexts: 컨텍스트 리스트

        Returns:
            키워드 겹침 비율 (0.0 ~ 1.0)
        """
        if not contexts:
            return 0.0

        # 형태소 분석으로 키워드 추출
        question_keywords = set(
            self._tokenizer.extract_keywords(question, pos_tags=self._claim_pos_tags)
        )

        if not question_keywords:
            return 0.0

        context_text = " ".join(contexts)
        context_keywords = set(
            self._tokenizer.extract_keywords(context_text, pos_tags=self._claim_pos_tags)
        )

        overlap = len(question_keywords & context_keywords)
        return overlap / len(question_keywords)


class KoreanSemanticSimilarity:
    """한국어 의미 유사도 계산기.

    형태소 기반 전처리 + Dense 임베딩으로 의미 유사도를 계산합니다.

    Example:
        >>> from evalvault.adapters.outbound.nlp.korean import (
        ...     KoreanSemanticSimilarity,
        ...     KiwiTokenizer,
        ...     KoreanDenseRetriever,
        ... )
        >>> tokenizer = KiwiTokenizer()
        >>> retriever = KoreanDenseRetriever()
        >>> similarity = KoreanSemanticSimilarity(
        ...     tokenizer=tokenizer,
        ...     embedding_func=retriever.get_embedding_func(),
        ... )
        >>> result = similarity.calculate("보험료가 얼마인가요?", "보험료는 얼마입니까?")
        >>> print(result.similarity)  # 높은 유사도
    """

    def __init__(
        self,
        tokenizer: KiwiTokenizer,
        embedding_func: Callable[[list[str]], list[list[float]]] | None = None,
        *,
        use_preprocessing: bool = True,
        keyword_pos_tags: list[str] | None = None,
    ) -> None:
        """KoreanSemanticSimilarity 초기화.

        Args:
            tokenizer: KiwiTokenizer 인스턴스
            embedding_func: 임베딩 함수 (texts -> embeddings)
            use_preprocessing: 형태소 분석 전처리 사용 여부 (기본: True)
            keyword_pos_tags: 전처리에 사용할 품사 태그
        """
        self._tokenizer = tokenizer
        self._embedding_func = embedding_func
        self._use_preprocessing = use_preprocessing
        self._keyword_pos_tags = keyword_pos_tags or ["NNG", "NNP", "VV", "VA"]

    def preprocess(self, text: str) -> tuple[str, list[str]]:
        """형태소 분석으로 전처리합니다.

        조사/어미를 제거하여 핵심 의미만 추출합니다.

        Args:
            text: 전처리할 텍스트

        Returns:
            (전처리된 텍스트, 추출된 키워드 리스트)
        """
        keywords = self._tokenizer.extract_keywords(text, pos_tags=self._keyword_pos_tags)
        preprocessed = " ".join(keywords)
        return preprocessed, keywords

    def calculate(
        self,
        text1: str,
        text2: str,
        *,
        use_preprocessing: bool | None = None,
    ) -> SemanticSimilarityResult:
        """두 텍스트의 의미 유사도를 계산합니다.

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            use_preprocessing: 전처리 사용 여부 (None이면 인스턴스 설정 사용)

        Returns:
            SemanticSimilarityResult 결과
        """
        if use_preprocessing is None:
            use_preprocessing = self._use_preprocessing

        text1_keywords: list[str] = []
        text2_keywords: list[str] = []

        if use_preprocessing:
            text1, text1_keywords = self.preprocess(text1)
            text2, text2_keywords = self.preprocess(text2)

        # 임베딩 함수가 없으면 키워드 기반 Jaccard 유사도 사용
        if self._embedding_func is None:
            similarity = self._jaccard_similarity(text1_keywords, text2_keywords)
            return SemanticSimilarityResult(
                similarity=similarity,
                text1_keywords=text1_keywords,
                text2_keywords=text2_keywords,
                preprocessed=use_preprocessing,
            )

        # 임베딩 기반 코사인 유사도
        try:
            embeddings = self._embedding_func([text1, text2])
            emb1 = np.array(embeddings[0])
            emb2 = np.array(embeddings[1])

            similarity = self._cosine_similarity(emb1, emb2)

            return SemanticSimilarityResult(
                similarity=similarity,
                text1_keywords=text1_keywords,
                text2_keywords=text2_keywords,
                preprocessed=use_preprocessing,
            )

        except Exception as e:
            logger.warning(f"Embedding-based similarity failed: {e}, falling back to Jaccard")
            similarity = self._jaccard_similarity(text1_keywords, text2_keywords)
            return SemanticSimilarityResult(
                similarity=similarity,
                text1_keywords=text1_keywords,
                text2_keywords=text2_keywords,
                preprocessed=use_preprocessing,
            )

    def calculate_batch(
        self,
        texts1: list[str],
        texts2: list[str],
        *,
        use_preprocessing: bool | None = None,
    ) -> list[SemanticSimilarityResult]:
        """여러 텍스트 쌍의 의미 유사도를 배치로 계산합니다.

        Args:
            texts1: 첫 번째 텍스트 리스트
            texts2: 두 번째 텍스트 리스트
            use_preprocessing: 전처리 사용 여부

        Returns:
            SemanticSimilarityResult 리스트
        """
        if len(texts1) != len(texts2):
            raise ValueError("texts1 and texts2 must have the same length")

        results = []
        for t1, t2 in zip(texts1, texts2, strict=True):
            result = self.calculate(t1, t2, use_preprocessing=use_preprocessing)
            results.append(result)

        return results

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도 계산."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def _jaccard_similarity(self, keywords1: list[str], keywords2: list[str]) -> float:
        """Jaccard 유사도 계산 (임베딩 없는 경우 fallback)."""
        set1 = set(keywords1)
        set2 = set(keywords2)

        if not set1 and not set2:
            return 1.0  # 둘 다 빈 경우

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0
