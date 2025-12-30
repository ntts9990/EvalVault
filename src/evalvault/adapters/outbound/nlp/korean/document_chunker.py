"""Korean document chunker with semantic awareness.

한국어 문서를 의미 단위로 청킹합니다.

Example:
    >>> from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer
    >>> from evalvault.adapters.outbound.nlp.korean.document_chunker import KoreanDocumentChunker
    >>> tokenizer = KiwiTokenizer()
    >>> chunker = KoreanDocumentChunker(tokenizer, chunk_size=200)
    >>> chunks = chunker.chunk(long_document)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """청크 정보.

    Attributes:
        text: 청크 텍스트
        start_idx: 원본 문서에서 시작 위치
        end_idx: 원본 문서에서 끝 위치
        token_count: 토큰 수
        sentence_count: 문장 수
        metadata: 추가 메타데이터
    """

    text: str
    start_idx: int
    end_idx: int
    token_count: int
    sentence_count: int
    metadata: dict = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        """문자 수."""
        return len(self.text)


class KoreanDocumentChunker:
    """한국어 문서 청커.

    Kiwi 형태소 분석기를 활용하여 의미 단위로 문서를 청킹합니다.
    문장 경계를 존중하며, 토큰 수 기준으로 청크 크기를 조절합니다.

    Attributes:
        tokenizer: KiwiTokenizer 인스턴스
        chunk_size: 청크당 최대 토큰 수
        overlap_tokens: 청크 간 오버랩 토큰 수
        min_chunk_size: 최소 청크 토큰 수

    Example:
        >>> chunker = KoreanDocumentChunker(tokenizer, chunk_size=200)
        >>> chunks = chunker.chunk("긴 보험 약관 문서...")
        >>> for chunk in chunks:
        ...     print(f"[{chunk.token_count} tokens] {chunk.text[:50]}...")
    """

    def __init__(
        self,
        tokenizer: KiwiTokenizer,
        chunk_size: int = 500,
        overlap_tokens: int = 50,
        min_chunk_size: int = 50,
    ) -> None:
        """KoreanDocumentChunker 초기화.

        Args:
            tokenizer: 한국어 토크나이저
            chunk_size: 청크당 최대 토큰 수
            overlap_tokens: 청크 간 오버랩 토큰 수
            min_chunk_size: 최소 청크 토큰 수 (이보다 작으면 이전 청크에 병합)
        """
        self._tokenizer = tokenizer
        self._chunk_size = chunk_size
        self._overlap_tokens = overlap_tokens
        self._min_chunk_size = min_chunk_size

    @property
    def chunk_size(self) -> int:
        """청크 크기 (토큰 수)."""
        return self._chunk_size

    @property
    def overlap_tokens(self) -> int:
        """오버랩 토큰 수."""
        return self._overlap_tokens

    def split_sentences(self, text: str) -> list[str]:
        """텍스트를 문장으로 분리합니다.

        Kiwi의 문장 분리 기능을 사용합니다.

        Args:
            text: 입력 텍스트

        Returns:
            문장 리스트
        """
        return self._tokenizer.split_sentences(text)

    def count_tokens(self, text: str) -> int:
        """텍스트의 토큰 수를 계산합니다.

        Args:
            text: 입력 텍스트

        Returns:
            토큰 수
        """
        return len(self._tokenizer.tokenize(text))

    def chunk(self, document: str) -> list[Chunk]:
        """문서를 청크로 분할합니다.

        문장 경계를 존중하며 토큰 수 기준으로 청킹합니다.

        Args:
            document: 입력 문서

        Returns:
            Chunk 리스트
        """
        if not document or not document.strip():
            return []

        sentences = self.split_sentences(document)
        if not sentences:
            # 문장 분리 실패 시 전체를 하나의 청크로
            return [
                Chunk(
                    text=document,
                    start_idx=0,
                    end_idx=len(document),
                    token_count=self.count_tokens(document),
                    sentence_count=1,
                )
            ]

        chunks = []
        current_sentences: list[str] = []
        current_token_count = 0
        current_start_idx = 0
        doc_position = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # 현재 청크에 문장 추가 가능 여부 확인
            if current_token_count + sentence_tokens <= self._chunk_size:
                current_sentences.append(sentence)
                current_token_count += sentence_tokens
            else:
                # 현재 청크 저장
                if current_sentences:
                    chunk_text = " ".join(current_sentences)
                    chunk_end_idx = doc_position

                    chunks.append(
                        Chunk(
                            text=chunk_text,
                            start_idx=current_start_idx,
                            end_idx=chunk_end_idx,
                            token_count=current_token_count,
                            sentence_count=len(current_sentences),
                        )
                    )

                # 오버랩 처리: 이전 청크의 마지막 문장들을 새 청크에 포함
                overlap_sentences = self._get_overlap_sentences(
                    current_sentences, self._overlap_tokens
                )

                # 새 청크 시작
                current_sentences = overlap_sentences + [sentence]
                current_token_count = sum(self.count_tokens(s) for s in current_sentences)
                current_start_idx = doc_position

            # 문서 위치 업데이트
            doc_position += len(sentence) + 1  # +1 for space

        # 마지막 청크 저장
        if current_sentences:
            chunk_text = " ".join(current_sentences)

            # 최소 크기 미달 시 이전 청크와 병합
            if current_token_count < self._min_chunk_size and chunks:
                last_chunk = chunks.pop()
                merged_text = last_chunk.text + " " + chunk_text
                chunks.append(
                    Chunk(
                        text=merged_text,
                        start_idx=last_chunk.start_idx,
                        end_idx=len(document),
                        token_count=last_chunk.token_count + current_token_count,
                        sentence_count=last_chunk.sentence_count + len(current_sentences),
                    )
                )
            else:
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        start_idx=current_start_idx,
                        end_idx=len(document),
                        token_count=current_token_count,
                        sentence_count=len(current_sentences),
                    )
                )

        return chunks

    def _get_overlap_sentences(
        self,
        sentences: list[str],
        target_tokens: int,
    ) -> list[str]:
        """오버랩에 사용할 문장들을 선택합니다.

        뒤에서부터 target_tokens에 도달할 때까지 문장을 선택합니다.

        Args:
            sentences: 문장 리스트
            target_tokens: 목표 토큰 수

        Returns:
            오버랩 문장 리스트
        """
        if not sentences or target_tokens <= 0:
            return []

        overlap = []
        token_count = 0

        for sentence in reversed(sentences):
            sentence_tokens = self.count_tokens(sentence)
            if token_count + sentence_tokens <= target_tokens:
                overlap.insert(0, sentence)
                token_count += sentence_tokens
            else:
                break

        return overlap

    def chunk_to_strings(self, document: str) -> list[str]:
        """문서를 청크 문자열 리스트로 분할합니다.

        간단한 사용을 위한 편의 메서드.

        Args:
            document: 입력 문서

        Returns:
            청크 텍스트 리스트
        """
        chunks = self.chunk(document)
        return [c.text for c in chunks]

    def chunk_with_metadata(
        self,
        document: str,
        doc_id: str | None = None,
        source: str | None = None,
    ) -> list[Chunk]:
        """메타데이터와 함께 청킹합니다.

        Args:
            document: 입력 문서
            doc_id: 문서 ID
            source: 출처 정보

        Returns:
            메타데이터가 포함된 Chunk 리스트
        """
        chunks = self.chunk(document)

        for i, chunk in enumerate(chunks):
            chunk.metadata = {
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            if doc_id:
                chunk.metadata["doc_id"] = doc_id
            if source:
                chunk.metadata["source"] = source

        return chunks


class ParagraphChunker(KoreanDocumentChunker):
    """단락 기반 청커.

    빈 줄로 구분된 단락을 기준으로 청킹합니다.
    """

    def split_paragraphs(self, text: str) -> list[str]:
        """텍스트를 단락으로 분리합니다.

        Args:
            text: 입력 텍스트

        Returns:
            단락 리스트
        """
        # 빈 줄(연속된 줄바꿈)로 분리
        paragraphs = []
        current = []

        for line in text.split("\n"):
            if line.strip():
                current.append(line.strip())
            elif current:
                paragraphs.append(" ".join(current))
                current = []

        if current:
            paragraphs.append(" ".join(current))

        return paragraphs

    def chunk(self, document: str) -> list[Chunk]:
        """단락 기반으로 청킹합니다.

        단락을 우선 분리하고, 큰 단락은 문장 단위로 추가 분할합니다.
        """
        if not document or not document.strip():
            return []

        paragraphs = self.split_paragraphs(document)
        if not paragraphs:
            return []

        chunks = []
        current_paragraphs: list[str] = []
        current_token_count = 0
        current_start_idx = 0

        for para in paragraphs:
            para_tokens = self.count_tokens(para)

            # 단락이 chunk_size보다 크면 문장 단위로 분할
            if para_tokens > self._chunk_size:
                # 현재까지 청크 저장
                if current_paragraphs:
                    chunk_text = "\n\n".join(current_paragraphs)
                    chunks.append(
                        Chunk(
                            text=chunk_text,
                            start_idx=current_start_idx,
                            end_idx=current_start_idx + len(chunk_text),
                            token_count=current_token_count,
                            sentence_count=len(current_paragraphs),
                        )
                    )
                    current_start_idx += len(chunk_text) + 2  # +2 for \n\n
                    current_paragraphs = []
                    current_token_count = 0

                # 큰 단락을 문장 단위로 분할
                sub_chunks = super().chunk(para)
                for sub_chunk in sub_chunks:
                    sub_chunk.start_idx += current_start_idx
                    sub_chunk.end_idx += current_start_idx
                    chunks.append(sub_chunk)
                current_start_idx += len(para) + 2

            elif current_token_count + para_tokens <= self._chunk_size:
                current_paragraphs.append(para)
                current_token_count += para_tokens
            else:
                # 현재 청크 저장
                if current_paragraphs:
                    chunk_text = "\n\n".join(current_paragraphs)
                    chunks.append(
                        Chunk(
                            text=chunk_text,
                            start_idx=current_start_idx,
                            end_idx=current_start_idx + len(chunk_text),
                            token_count=current_token_count,
                            sentence_count=len(current_paragraphs),
                        )
                    )
                    current_start_idx += len(chunk_text) + 2

                current_paragraphs = [para]
                current_token_count = para_tokens

        # 마지막 청크
        if current_paragraphs:
            chunk_text = "\n\n".join(current_paragraphs)
            chunks.append(
                Chunk(
                    text=chunk_text,
                    start_idx=current_start_idx,
                    end_idx=current_start_idx + len(chunk_text),
                    token_count=current_token_count,
                    sentence_count=len(current_paragraphs),
                )
            )

        return chunks
