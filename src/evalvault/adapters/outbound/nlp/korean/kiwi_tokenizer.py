"""Kiwi 기반 한국어 토크나이저.

Kiwi 형태소 분석기를 활용한 한국어 토큰화, 키워드 추출, 문장 분리를 제공합니다.

Example:
    >>> from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer
    >>> tokenizer = KiwiTokenizer()
    >>> tokens = tokenizer.tokenize("보험료가 얼마인가요?")
    >>> print(tokens)
    ['보험료', '얼마']
"""

from __future__ import annotations

import contextlib
import logging
import os
import platform
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from evalvault.adapters.outbound.nlp.korean.korean_stopwords import (
    KEYWORD_POS_TAGS,
    STOPWORD_POS_TAGS,
    is_stopword,
)

if TYPE_CHECKING:
    from kiwipiepy import Kiwi

logger = logging.getLogger(__name__)

_KIWI_NEON_QUANT_WARNING = "Quantization is not supported for ArchType::neon"


def _should_suppress_kiwi_quant_warning(model_type: str | None) -> bool:
    machine = platform.machine().lower()
    if "arm" not in machine and "aarch" not in machine:
        return False
    return model_type not in {"knlm", "sbg"}


@contextlib.contextmanager
def _suppress_kiwi_quant_warning(model_type: str | None) -> Iterator[None]:
    if not _should_suppress_kiwi_quant_warning(model_type):
        yield
        return
    try:
        stderr_fd = sys.stderr.fileno()
    except (AttributeError, OSError):
        yield
        return
    saved_fd = os.dup(stderr_fd)
    with tempfile.TemporaryFile(mode="w+t") as temp:
        os.dup2(temp.fileno(), stderr_fd)
        try:
            yield
        finally:
            os.dup2(saved_fd, stderr_fd)
            os.close(saved_fd)
            temp.seek(0)
            output = temp.read()
    if output:
        filtered = [line for line in output.splitlines() if _KIWI_NEON_QUANT_WARNING not in line]
        if filtered:
            sys.stderr.write("\n".join(filtered) + "\n")
            sys.stderr.flush()


@dataclass
class Token:
    """형태소 분석 결과 토큰."""

    form: str
    """표면형 (원본 텍스트)"""

    tag: str
    """품사 태그 (Kiwi 태그셋)"""

    lemma: str
    """원형 (기본형)"""

    start: int
    """시작 위치"""

    end: int
    """끝 위치"""

    @property
    def is_noun(self) -> bool:
        """명사인지 확인."""
        return self.tag.startswith("N")

    @property
    def is_verb(self) -> bool:
        """동사인지 확인."""
        return self.tag == "VV"

    @property
    def is_adjective(self) -> bool:
        """형용사인지 확인."""
        return self.tag == "VA"

    @property
    def is_keyword_pos(self) -> bool:
        """키워드 추출에 유용한 품사인지 확인."""
        return self.tag in KEYWORD_POS_TAGS

    @property
    def is_stopword_pos(self) -> bool:
        """불용어 품사인지 확인."""
        return self.tag in STOPWORD_POS_TAGS


class KiwiTokenizer:
    """Kiwi 기반 한국어 토크나이저.

    형태소 분석을 통해 의미있는 토큰을 추출합니다.
    조사/어미 제거, 원형 변환, 불용어 필터링을 지원합니다.

    Attributes:
        remove_particles: 조사(J*) 제거 여부
        remove_endings: 어미(E*) 제거 여부
        remove_symbols: 기호(S*) 제거 여부
        use_lemma: 원형(기본형) 사용 여부
        remove_stopwords: 불용어 제거 여부
        min_token_length: 최소 토큰 길이

    Example:
        >>> tokenizer = KiwiTokenizer()
        >>> tokenizer.tokenize("종신보험의 보장금액은 1억원입니다.")
        ['종신보험', '보장금액', '1억원']
    """

    def __init__(
        self,
        remove_particles: bool = True,
        remove_endings: bool = True,
        remove_symbols: bool = True,
        use_lemma: bool = True,
        remove_stopwords: bool = True,
        min_token_length: int = 1,
        user_dict_path: str | Path | None = None,
        num_workers: int = 0,
        model_type: str | None = None,
    ):
        """KiwiTokenizer 초기화.

        Args:
            remove_particles: 조사 제거 (이/가/을/를/의 등)
            remove_endings: 어미 제거 (다/요/습니다 등)
            remove_symbols: 기호 제거 (마침표, 쉼표 등)
            use_lemma: 원형 사용 (먹었다 → 먹다)
            remove_stopwords: 불용어 제거
            min_token_length: 최소 토큰 길이
            user_dict_path: 사용자 사전 경로 (TSV 형식)
            num_workers: 병렬 처리 워커 수 (0=자동)
            model_type: Kiwi 모델 타입 (cong, cong-global 등)
        """
        self.remove_particles = remove_particles
        self.remove_endings = remove_endings
        self.remove_symbols = remove_symbols
        self.use_lemma = use_lemma
        self.remove_stopwords = remove_stopwords
        self.min_token_length = min_token_length

        self._kiwi: Kiwi | None = None
        self._user_dict_path = Path(user_dict_path) if user_dict_path else None
        # num_workers: -1=single thread, 0=auto (deprecated), >0=specific count
        self._num_workers = num_workers if num_workers != 0 else -1
        self._model_type = model_type

    @property
    def kiwi(self) -> Kiwi:
        """Kiwi 인스턴스를 lazy loading으로 반환."""
        if self._kiwi is None:
            self._kiwi = self._create_kiwi()
        return self._kiwi

    def _create_kiwi(self) -> Kiwi:
        """Kiwi 인스턴스 생성."""
        try:
            from kiwipiepy import Kiwi
        except ImportError as e:
            raise ImportError(
                "kiwipiepy가 설치되지 않았습니다. "
                "'uv add kiwipiepy' 또는 'pip install kiwipiepy'로 설치하세요."
            ) from e

        with _suppress_kiwi_quant_warning(self._model_type):
            kiwi = Kiwi(num_workers=self._num_workers, model_type=self._model_type)

        # 사용자 사전 로드
        if self._user_dict_path and self._user_dict_path.exists():
            self._load_user_dict(kiwi, self._user_dict_path)
            logger.info(f"사용자 사전 로드: {self._user_dict_path}")

        return kiwi

    def _load_user_dict(self, kiwi: Kiwi, dict_path: Path) -> None:
        """사용자 사전을 로드합니다.

        TSV 형식: 단어\t품사\t점수
        예: 삼성화재\tNNP\t0.0

        Args:
            kiwi: Kiwi 인스턴스
            dict_path: 사용자 사전 경로
        """
        with open(dict_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split("\t")
                if len(parts) >= 2:
                    word = parts[0]
                    tag = parts[1]
                    score = float(parts[2]) if len(parts) >= 3 else 0.0
                    kiwi.add_user_word(word, tag, score)

    def _should_filter(self, tag: str) -> bool:
        """품사 태그로 필터링 여부를 결정합니다."""
        if self.remove_particles and tag.startswith("J"):
            return True
        if self.remove_endings and tag.startswith("E"):
            return True
        return bool(self.remove_symbols and tag.startswith("S"))

    def analyze(self, text: str) -> list[Token]:
        """텍스트를 형태소 분석합니다.

        Args:
            text: 분석할 텍스트

        Returns:
            Token 리스트 (필터링 전)
        """
        if not text or not text.strip():
            return []

        tokens = []
        for token in self.kiwi.tokenize(text):
            tokens.append(
                Token(
                    form=token.form,
                    tag=token.tag,
                    lemma=token.lemma if hasattr(token, "lemma") else token.form,
                    start=token.start,
                    end=token.end,
                )
            )
        return tokens

    def tokenize(self, text: str) -> list[str]:
        """텍스트를 토큰화합니다.

        조사/어미/기호를 제거하고 원형으로 변환합니다.

        Args:
            text: 토큰화할 텍스트

        Returns:
            토큰 리스트 (문자열)
        """
        tokens = self.analyze(text)
        result = []

        for token in tokens:
            # 품사 기반 필터링
            if self._should_filter(token.tag):
                continue

            # 토큰 값 결정 (원형 또는 표면형)
            value = token.lemma if self.use_lemma else token.form

            # 불용어 필터링
            if self.remove_stopwords and is_stopword(value, token.tag):
                continue

            # 최소 길이 필터링
            if len(value) < self.min_token_length:
                continue

            result.append(value)

        return result

    def extract_nouns(self, text: str) -> list[str]:
        """명사만 추출합니다.

        Args:
            text: 입력 텍스트

        Returns:
            명사 리스트
        """
        tokens = self.analyze(text)
        nouns = []

        for token in tokens:
            if token.is_noun:
                value = token.lemma if self.use_lemma else token.form
                if not self.remove_stopwords or not is_stopword(value, token.tag):
                    nouns.append(value)

        return nouns

    def extract_keywords(
        self,
        text: str,
        pos_tags: set[str] | None = None,
    ) -> list[str]:
        """키워드 품사만 추출합니다 (명사, 동사, 형용사).

        Args:
            text: 입력 텍스트
            pos_tags: 추출할 품사 태그 집합 (기본: KEYWORD_POS_TAGS)

        Returns:
            키워드 리스트
        """
        if pos_tags is None:
            pos_tags = KEYWORD_POS_TAGS

        tokens = self.analyze(text)
        keywords = []

        for token in tokens:
            if token.tag in pos_tags:
                value = token.lemma if self.use_lemma else token.form
                if not self.remove_stopwords or not is_stopword(value, token.tag):
                    keywords.append(value)

        return keywords

    def split_sentences(self, text: str) -> list[str]:
        """텍스트를 문장으로 분리합니다.

        Kiwi의 문장 분리 기능을 사용합니다.

        Args:
            text: 입력 텍스트

        Returns:
            문장 리스트
        """
        if not text or not text.strip():
            return []

        return [sent.text for sent in self.kiwi.split_into_sents(text)]

    def get_pos_tags(self, text: str) -> list[tuple[str, str]]:
        """품사 태깅 결과를 반환합니다.

        Args:
            text: 입력 텍스트

        Returns:
            (토큰, 품사) 튜플 리스트
        """
        tokens = self.analyze(text)
        return [(token.form, token.tag) for token in tokens]

    def normalize(self, text: str) -> str:
        """텍스트를 정규화합니다.

        형태소 분석 후 원형으로 재구성합니다.

        Args:
            text: 입력 텍스트

        Returns:
            정규화된 텍스트
        """
        tokens = self.tokenize(text)
        return " ".join(tokens)

    def add_user_word(
        self,
        word: str,
        tag: str = "NNP",
        score: float = 0.0,
    ) -> None:
        """사용자 단어를 추가합니다.

        Args:
            word: 추가할 단어
            tag: 품사 태그 (기본: 고유명사)
            score: 단어 점수 (기본: 0.0)
        """
        self.kiwi.add_user_word(word, tag, score)

    def add_insurance_terms(self, terms: list[str]) -> None:
        """보험 용어를 일괄 추가합니다.

        Args:
            terms: 보험 용어 리스트
        """
        for term in terms:
            self.add_user_word(term, "NNP", 0.0)
        logger.info(f"보험 용어 {len(terms)}개 추가")
