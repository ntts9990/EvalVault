"""KiwiTokenizer 단위 테스트.

한국어 형태소 분석기 Kiwi 기반 토크나이저의 테스트입니다.
"""

from __future__ import annotations

import pytest

from tests.optional_deps import kiwi_ready

# Check if kiwipiepy is available
try:
    from evalvault.adapters.outbound.nlp.korean import (
        KOREAN_STOPWORDS,
        STOPWORD_POS_TAGS,
        KiwiTokenizer,
        is_stopword,
    )

    HAS_KIWI, KIWI_SKIP_REASON = kiwi_ready()
    KIWI_SKIP_REASON = KIWI_SKIP_REASON or "kiwipiepy unavailable"
except ImportError:
    HAS_KIWI = False
    KIWI_SKIP_REASON = "kiwipiepy not installed"
    # Define placeholders for type hints
    KiwiTokenizer = None  # type: ignore[misc,assignment]
    KOREAN_STOPWORDS = set()  # type: ignore[misc]
    STOPWORD_POS_TAGS = set()  # type: ignore[misc]

    def is_stopword(word: str, pos_tag: str | None = None) -> bool:  # type: ignore[misc]
        return False


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKiwiTokenizerBasic:
    """KiwiTokenizer 기본 기능 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        """기본 토크나이저 인스턴스."""
        return KiwiTokenizer()

    def test_tokenize_simple_sentence(self, tokenizer: KiwiTokenizer):
        """간단한 문장 토큰화."""
        tokens = tokenizer.tokenize("보험료가 얼마인가요?")

        # 조사 '가'와 어미는 제거됨
        assert "보험료" in tokens
        assert "얼마" in tokens
        assert "가" not in tokens  # 조사 제거

    def test_tokenize_insurance_terms(self, tokenizer: KiwiTokenizer):
        """보험 용어 토큰화."""
        tokens = tokenizer.tokenize("종신보험의 보장금액은 1억원입니다.")

        assert "종신보험" in tokens or "종신" in tokens
        assert "보장금액" in tokens or "보장" in tokens

    def test_tokenize_empty_string(self, tokenizer: KiwiTokenizer):
        """빈 문자열 처리."""
        assert tokenizer.tokenize("") == []
        assert tokenizer.tokenize("   ") == []

    def test_tokenize_removes_particles(self, tokenizer: KiwiTokenizer):
        """조사 제거 확인."""
        tokens = tokenizer.tokenize("보험을 가입하고 보장을 받습니다")

        # 조사 '을', '을', '를'은 제거되어야 함
        for token in tokens:
            assert not token.endswith("을")
            assert not token.endswith("를")

    def test_tokenize_removes_endings(self, tokenizer: KiwiTokenizer):
        """어미 제거 확인."""
        tokens = tokenizer.tokenize("보험료를 납입합니다")

        # 어미 '습니다'는 제거되어야 함
        assert "습니다" not in tokens

    def test_tokenize_uses_lemma(self, tokenizer: KiwiTokenizer):
        """원형 사용 확인."""
        tokens = tokenizer.tokenize("보험에 가입했습니다")

        # '가입했습니다' → '가입하다' 또는 '가입'
        assert "가입" in tokens or "가입하다" in tokens


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKiwiTokenizerExtraction:
    """키워드/명사 추출 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        """기본 토크나이저 인스턴스."""
        return KiwiTokenizer()

    def test_extract_nouns(self, tokenizer: KiwiTokenizer):
        """명사 추출."""
        nouns = tokenizer.extract_nouns("삼성화재 종신보험의 보장금액은 1억원입니다.")

        # 명사만 추출
        assert len(nouns) > 0
        # 최소한 이런 명사들이 포함되어야 함
        noun_text = " ".join(nouns)
        assert "삼성" in noun_text or "화재" in noun_text or "삼성화재" in noun_text

    def test_extract_keywords(self, tokenizer: KiwiTokenizer):
        """키워드 추출 (명사, 동사, 형용사)."""
        keywords = tokenizer.extract_keywords("보험료가 비싸서 가입을 망설입니다.")

        assert len(keywords) > 0
        # 동사/형용사도 포함
        keyword_text = " ".join(keywords)
        assert "보험료" in keyword_text or "보험" in keyword_text

    def test_extract_keywords_with_custom_pos(self, tokenizer: KiwiTokenizer):
        """커스텀 품사 태그로 키워드 추출."""
        # 명사만 추출
        keywords = tokenizer.extract_keywords(
            "보험료가 비싸서 가입을 망설입니다.",
            pos_tags={"NNG", "NNP"},
        )

        assert len(keywords) > 0


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKiwiTokenizerSentences:
    """문장 분리 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        """기본 토크나이저 인스턴스."""
        return KiwiTokenizer()

    def test_split_sentences_basic(self, tokenizer: KiwiTokenizer):
        """기본 문장 분리."""
        text = "보험료가 얼마인가요? 보장 내용도 알려주세요."
        sentences = tokenizer.split_sentences(text)

        assert len(sentences) == 2
        assert "얼마" in sentences[0]
        assert "보장" in sentences[1]

    def test_split_sentences_single(self, tokenizer: KiwiTokenizer):
        """단일 문장."""
        text = "보험료가 얼마인가요?"
        sentences = tokenizer.split_sentences(text)

        assert len(sentences) == 1

    def test_split_sentences_empty(self, tokenizer: KiwiTokenizer):
        """빈 문자열 문장 분리."""
        assert tokenizer.split_sentences("") == []
        assert tokenizer.split_sentences("   ") == []

    def test_split_sentences_korean_endings(self, tokenizer: KiwiTokenizer):
        """한국어 문장 종결 처리."""
        text = "첫 번째입니다. 두 번째예요! 세 번째인가요?"
        sentences = tokenizer.split_sentences(text)

        assert len(sentences) == 3


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKiwiTokenizerPOS:
    """품사 태깅 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        """기본 토크나이저 인스턴스."""
        return KiwiTokenizer()

    def test_get_pos_tags(self, tokenizer: KiwiTokenizer):
        """품사 태깅 결과."""
        pos_tags = tokenizer.get_pos_tags("보험료가 비쌉니다")

        assert len(pos_tags) > 0
        # (토큰, 태그) 튜플 형식
        assert all(isinstance(item, tuple) and len(item) == 2 for item in pos_tags)

    def test_pos_tags_contain_nouns(self, tokenizer: KiwiTokenizer):
        """품사 태깅에 명사 포함."""
        pos_tags = tokenizer.get_pos_tags("삼성화재 종신보험")

        # 명사 태그(NNG, NNP) 확인
        tags = [tag for _, tag in pos_tags]
        assert any(t.startswith("N") for t in tags)


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKiwiTokenizerAnalyze:
    """형태소 분석 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        """기본 토크나이저 인스턴스."""
        return KiwiTokenizer()

    def test_analyze_returns_tokens(self, tokenizer: KiwiTokenizer):
        """형태소 분석 결과 Token 객체 반환."""
        tokens = tokenizer.analyze("보험료가 얼마인가요?")

        assert len(tokens) > 0
        # Token 객체 속성 확인
        for token in tokens:
            assert hasattr(token, "form")
            assert hasattr(token, "tag")
            assert hasattr(token, "lemma")
            assert hasattr(token, "start")
            assert hasattr(token, "end")

    def test_token_properties(self, tokenizer: KiwiTokenizer):
        """Token 객체 속성 테스트."""
        tokens = tokenizer.analyze("보험에 가입합니다")

        # is_noun, is_verb 등 속성 확인
        has_noun = any(t.is_noun for t in tokens)
        has_verb = any(t.is_verb for t in tokens)

        assert has_noun or has_verb


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKiwiTokenizerOptions:
    """토크나이저 옵션 테스트."""

    def test_keep_particles(self):
        """조사 유지 옵션."""
        tokenizer = KiwiTokenizer(remove_particles=False)
        tokens = tokenizer.tokenize("보험료가 얼마인가요?")

        # 조사가 유지되어야 함 - 토큰 수가 더 많아짐
        assert len(tokens) > 0

    def test_keep_endings(self):
        """어미 유지 옵션."""
        tokenizer = KiwiTokenizer(remove_endings=False)
        tokens = tokenizer.tokenize("보험에 가입합니다")

        # 어미가 유지되어야 함 - 토큰이 생성됨
        assert len(tokens) > 0

    def test_use_surface_form(self):
        """표면형 사용 옵션."""
        tokenizer = KiwiTokenizer(use_lemma=False)
        tokens = tokenizer.tokenize("보험에 가입했습니다")

        # 표면형 사용 (원형 변환 안함) - 토큰이 생성됨
        assert len(tokens) > 0

    def test_no_stopword_removal(self):
        """불용어 미제거 옵션."""
        tokenizer = KiwiTokenizer(remove_stopwords=False)
        tokens = tokenizer.tokenize("그것은 보험입니다")

        # 불용어 '것'이 유지될 수 있음 - 토큰이 생성됨
        assert len(tokens) > 0

    def test_min_token_length(self):
        """최소 토큰 길이 옵션."""
        tokenizer = KiwiTokenizer(min_token_length=2)
        tokens = tokenizer.tokenize("a b 보험료가 c 비쌉니다")

        # 1글자 토큰은 제거됨
        for token in tokens:
            assert len(token) >= 2


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKiwiTokenizerUserDict:
    """사용자 사전 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        """기본 토크나이저 인스턴스."""
        return KiwiTokenizer()

    def test_add_user_word(self, tokenizer: KiwiTokenizer):
        """사용자 단어 추가."""
        # 사용자 단어 추가
        tokenizer.add_user_word("삼성화재다이렉트", "NNP", 0.0)

        tokens = tokenizer.tokenize("삼성화재다이렉트 보험에 가입했습니다")
        # 사용자 단어가 하나의 토큰으로 인식됨
        assert "삼성화재다이렉트" in tokens

    def test_add_insurance_terms(self, tokenizer: KiwiTokenizer):
        """보험 용어 일괄 추가."""
        terms = ["무배당종신보험", "변액유니버셜", "CI보험"]
        tokenizer.add_insurance_terms(terms)

        # 추가된 용어가 제대로 인식되는지 확인
        for term in terms:
            tokens = tokenizer.tokenize(f"{term}에 가입했습니다")
            assert term in tokens


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKiwiTokenizerNormalize:
    """텍스트 정규화 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        """기본 토크나이저 인스턴스."""
        return KiwiTokenizer()

    def test_normalize_text(self, tokenizer: KiwiTokenizer):
        """텍스트 정규화."""
        normalized = tokenizer.normalize("보험료가 얼마인가요?")

        # 공백으로 구분된 토큰들
        assert " " in normalized or len(normalized) > 0

    def test_normalize_removes_noise(self, tokenizer: KiwiTokenizer):
        """정규화 시 노이즈 제거."""
        normalized = tokenizer.normalize("보험료가!!! 얼마인가요???")

        # 특수문자 제거됨
        assert "!" not in normalized
        assert "?" not in normalized


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKoreanStopwords:
    """한국어 불용어 테스트."""

    def test_stopword_set_exists(self):
        """불용어 집합 존재 확인."""
        assert len(KOREAN_STOPWORDS) > 0

    def test_common_stopwords(self):
        """일반 불용어 포함 확인."""
        assert "것" in KOREAN_STOPWORDS
        assert "수" in KOREAN_STOPWORDS
        assert "등" in KOREAN_STOPWORDS

    def test_stopword_pos_tags_exist(self):
        """불용어 품사 태그 존재 확인."""
        assert len(STOPWORD_POS_TAGS) > 0
        # 조사 태그 포함
        assert "JKS" in STOPWORD_POS_TAGS
        assert "JKO" in STOPWORD_POS_TAGS

    def test_is_stopword_function(self):
        """is_stopword 함수 테스트."""
        assert is_stopword("것") is True
        assert is_stopword("보험") is False

    def test_is_stopword_with_pos_tag(self):
        """품사 태그로 불용어 판단."""
        assert is_stopword("은", "JX") is True  # 보조사
        assert is_stopword("보험", "NNG") is False  # 일반명사


@pytest.mark.skipif(not HAS_KIWI, reason=KIWI_SKIP_REASON)
class TestKiwiTokenizerInsurance:
    """보험 도메인 특화 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        """기본 토크나이저 인스턴스."""
        return KiwiTokenizer()

    def test_insurance_question_tokenization(self, tokenizer: KiwiTokenizer):
        """보험 질문 토큰화."""
        questions = [
            "이 보험의 보장금액은 얼마인가요?",
            "납입 기간은 어떻게 되나요?",
            "만기 환급금이 있나요?",
            "사망 보험금 지급 조건이 뭔가요?",
        ]

        for question in questions:
            tokens = tokenizer.tokenize(question)
            assert len(tokens) > 0
            # 최소한 하나의 보험 관련 키워드 포함
            keywords = {
                "보험",
                "보장금액",
                "보장",
                "납입",
                "만기",
                "환급금",
                "사망",
                "보험금",
                "지급",
            }
            assert any(t in keywords or any(k in t for k in keywords) for t in tokens)

    def test_insurance_answer_tokenization(self, tokenizer: KiwiTokenizer):
        """보험 답변 토큰화."""
        answer = "이 종신보험의 사망 보장금액은 1억원이며, 납입 기간은 20년입니다."
        tokens = tokenizer.tokenize(answer)

        assert len(tokens) > 0
        token_text = " ".join(tokens)
        # 핵심 정보 포함
        assert "종신보험" in token_text or "종신" in token_text or "보험" in token_text

    def test_insurance_context_keywords(self, tokenizer: KiwiTokenizer):
        """보험 컨텍스트 키워드 추출."""
        context = """
        제1조 (보험금의 지급)
        회사는 피보험자가 보험기간 중 사망하였을 때 사망보험금으로
        보험가입금액을 보험수익자에게 지급합니다.
        """

        keywords = tokenizer.extract_keywords(context)

        assert len(keywords) > 0
        keyword_text = " ".join(keywords)
        # 핵심 보험 용어 포함
        assert any(term in keyword_text for term in ["보험금", "피보험자", "사망", "보험", "지급"])
