"""Korean Retrieval 단위 테스트.

한국어 BM25, 청킹, 하이브리드 검색 테스트입니다.
"""

from __future__ import annotations

import pytest

from tests.optional_deps import kiwi_ready, rank_bm25_ready

# Check if kiwipiepy is available
try:
    from evalvault.adapters.outbound.nlp.korean import (
        Chunk,
        FusionMethod,
        HybridResult,
        KiwiTokenizer,
        KoreanBM25Retriever,
        KoreanDocumentChunker,
        KoreanHybridRetriever,
        ParagraphChunker,
        RetrievalResult,
    )

    HAS_KIWI, KIWI_SKIP_REASON = kiwi_ready()
    HAS_BM25, BM25_SKIP_REASON = rank_bm25_ready()
    KOREAN_READY = HAS_KIWI and HAS_BM25
    if not HAS_KIWI:
        KOREAN_SKIP_REASON = KIWI_SKIP_REASON or "kiwipiepy unavailable"
    else:
        KOREAN_SKIP_REASON = BM25_SKIP_REASON or "rank_bm25 unavailable"
except ImportError:
    HAS_KIWI = False
    HAS_BM25 = False
    KOREAN_READY = False
    KOREAN_SKIP_REASON = "korean deps not installed"


@pytest.mark.skipif(not KOREAN_READY, reason=KOREAN_SKIP_REASON)
class TestKoreanBM25Retriever:
    """KoreanBM25Retriever 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        """토크나이저 인스턴스."""
        return KiwiTokenizer()

    @pytest.fixture
    def retriever(self, tokenizer) -> KoreanBM25Retriever:
        """BM25 검색기 인스턴스."""
        return KoreanBM25Retriever(tokenizer)

    @pytest.fixture
    def sample_documents(self) -> list[str]:
        """테스트용 샘플 문서."""
        return [
            "이 보험의 보장금액은 1억원입니다. 사망 시 보험금이 지급됩니다.",
            "보험료 납입 기간은 20년입니다. 매월 10만원을 납입합니다.",
            "만기 환급금은 납입 보험료의 100%입니다.",
            "보험 가입 후 3년이 지나면 해지 환급금이 발생합니다.",
            "피보험자가 사망하면 보험수익자에게 보험금을 지급합니다.",
        ]

    def test_index_documents(self, retriever, sample_documents):
        """문서 인덱싱 테스트."""
        count = retriever.index(sample_documents)

        assert count == len(sample_documents)
        assert retriever.is_indexed
        assert retriever.document_count == len(sample_documents)

    def test_index_empty_documents(self, retriever):
        """빈 문서 리스트 인덱싱."""
        count = retriever.index([])

        assert count == 0
        assert not retriever.is_indexed

    def test_search_basic(self, retriever, sample_documents):
        """기본 검색 테스트."""
        retriever.index(sample_documents)

        results = retriever.search("보험료 납입", top_k=3)

        assert len(results) > 0
        assert all(isinstance(r, RetrievalResult) for r in results)
        # 보험료 납입 관련 문서가 상위에 있어야 함
        assert any("납입" in r.document for r in results[:2])

    def test_search_with_scores(self, retriever, sample_documents):
        """점수 포함 검색 테스트."""
        retriever.index(sample_documents)

        results = retriever.search_with_scores("보장금액", top_k=3)

        assert len(results) > 0
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
        # (문서, 점수) 형식
        doc, score = results[0]
        assert isinstance(doc, str)
        assert isinstance(score, float)
        assert score > 0

    def test_search_before_index(self, retriever):
        """인덱싱 전 검색 시 에러."""
        with pytest.raises(ValueError, match="인덱스가 구축되지 않았습니다"):
            retriever.search("테스트")

    def test_search_relevance(self, retriever, sample_documents):
        """검색 관련성 테스트."""
        retriever.index(sample_documents)

        # "사망 보험금" 쿼리
        results = retriever.search("사망 보험금", top_k=3)

        # 사망 관련 문서가 상위에 있어야 함
        top_docs = [r.document for r in results[:2]]
        assert any("사망" in doc for doc in top_docs)

    def test_search_include_tokens(self, retriever, sample_documents):
        """토큰 포함 검색."""
        retriever.index(sample_documents)

        results = retriever.search("보험료", top_k=1, include_tokens=True)

        assert len(results) > 0
        assert results[0].tokens is not None
        assert len(results[0].tokens) > 0

    def test_add_documents(self, retriever, sample_documents):
        """문서 추가 테스트."""
        retriever.index(sample_documents[:3])
        assert retriever.document_count == 3

        new_count = retriever.add_documents(sample_documents[3:])
        assert new_count == len(sample_documents)

    def test_clear_index(self, retriever, sample_documents):
        """인덱스 초기화 테스트."""
        retriever.index(sample_documents)
        assert retriever.is_indexed

        retriever.clear()

        assert not retriever.is_indexed
        assert retriever.document_count == 0


@pytest.mark.skipif(not KOREAN_READY, reason=KOREAN_SKIP_REASON)
class TestKoreanDocumentChunker:
    """KoreanDocumentChunker 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        """토크나이저 인스턴스."""
        return KiwiTokenizer()

    @pytest.fixture
    def chunker(self, tokenizer) -> KoreanDocumentChunker:
        """청커 인스턴스."""
        return KoreanDocumentChunker(tokenizer, chunk_size=50, overlap_tokens=10)

    @pytest.fixture
    def long_document(self) -> str:
        """긴 테스트 문서."""
        return """
        제1조 (보험금의 지급)
        회사는 피보험자가 보험기간 중 사망하였을 때 사망보험금으로 보험가입금액을 보험수익자에게 지급합니다.

        제2조 (보험료의 납입)
        보험료는 매월 납입하며, 납입기간은 계약시 정한 기간으로 합니다.
        보험료 납입이 연체된 경우 회사는 계약을 해지할 수 있습니다.

        제3조 (해지환급금)
        보험계약이 해지된 경우 회사는 해지환급금을 계약자에게 지급합니다.
        해지환급금은 납입보험료의 일정 비율로 계산됩니다.
        """

    def test_chunk_document(self, chunker, long_document):
        """문서 청킹 테스트."""
        chunks = chunker.chunk(long_document)

        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_chunk_properties(self, chunker, long_document):
        """청크 속성 테스트."""
        chunks = chunker.chunk(long_document)

        for chunk in chunks:
            assert chunk.text
            assert chunk.token_count > 0
            assert chunk.sentence_count > 0
            assert chunk.start_idx >= 0
            assert chunk.end_idx > chunk.start_idx

    def test_chunk_size_limit(self, tokenizer):
        """청크 크기 제한 테스트."""
        chunker = KoreanDocumentChunker(tokenizer, chunk_size=30, overlap_tokens=5)

        document = "첫 번째 문장입니다. 두 번째 문장입니다. 세 번째 문장입니다. 네 번째 문장입니다. 다섯 번째 문장입니다."
        chunks = chunker.chunk(document)

        # 각 청크의 토큰 수가 chunk_size를 크게 초과하지 않아야 함
        for chunk in chunks:
            # 문장 단위로 분리하므로 약간 초과할 수 있음
            assert chunk.token_count <= 60  # 여유 있는 상한

    def test_empty_document(self, chunker):
        """빈 문서 청킹."""
        chunks = chunker.chunk("")
        assert chunks == []

        chunks = chunker.chunk("   ")
        assert chunks == []

    def test_chunk_to_strings(self, chunker, long_document):
        """문자열 리스트로 청킹."""
        chunk_texts = chunker.chunk_to_strings(long_document)

        assert len(chunk_texts) > 0
        assert all(isinstance(t, str) for t in chunk_texts)

    def test_chunk_with_metadata(self, chunker, long_document):
        """메타데이터 포함 청킹."""
        chunks = chunker.chunk_with_metadata(
            long_document,
            doc_id="doc-001",
            source="insurance_policy.pdf",
        )

        for i, chunk in enumerate(chunks):
            assert chunk.metadata["chunk_index"] == i
            assert chunk.metadata["total_chunks"] == len(chunks)
            assert chunk.metadata["doc_id"] == "doc-001"
            assert chunk.metadata["source"] == "insurance_policy.pdf"

    def test_split_sentences(self, chunker):
        """문장 분리 테스트."""
        text = "첫 번째 문장입니다. 두 번째 문장입니다! 세 번째 문장인가요?"
        sentences = chunker.split_sentences(text)

        assert len(sentences) == 3


@pytest.mark.skipif(not KOREAN_READY, reason=KOREAN_SKIP_REASON)
class TestParagraphChunker:
    """ParagraphChunker 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        return KiwiTokenizer()

    @pytest.fixture
    def chunker(self, tokenizer) -> ParagraphChunker:
        return ParagraphChunker(tokenizer, chunk_size=100)

    def test_split_paragraphs(self, chunker):
        """단락 분리 테스트."""
        text = """첫 번째 단락입니다.
        이것은 같은 단락입니다.

        두 번째 단락입니다.

        세 번째 단락입니다."""

        paragraphs = chunker.split_paragraphs(text)

        assert len(paragraphs) == 3

    def test_paragraph_based_chunking(self, chunker):
        """단락 기반 청킹."""
        document = """제1조 보험금 지급
        보험금은 피보험자 사망시 지급됩니다.

        제2조 보험료 납입
        보험료는 매월 납입합니다.

        제3조 해지환급금
        계약 해지시 환급금을 지급합니다."""

        chunks = chunker.chunk(document)

        assert len(chunks) > 0


@pytest.mark.skipif(not KOREAN_READY, reason=KOREAN_SKIP_REASON)
class TestKoreanHybridRetriever:
    """KoreanHybridRetriever 테스트."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        return KiwiTokenizer()

    @pytest.fixture
    def sample_documents(self) -> list[str]:
        return [
            "이 보험의 보장금액은 1억원입니다.",
            "보험료 납입 기간은 20년입니다.",
            "만기 환급금은 납입 보험료의 100%입니다.",
            "피보험자가 사망하면 보험금을 지급합니다.",
        ]

    @pytest.fixture
    def mock_embedding_func(self):
        """간단한 임베딩 함수 Mock."""

        def embed(texts: list[str]) -> list[list[float]]:
            # 텍스트 길이 기반 간단한 임베딩
            return [[len(t) / 100, len(t.split()) / 10, 0.5] for t in texts]

        return embed

    def test_bm25_only_search(self, tokenizer, sample_documents):
        """BM25만 사용한 검색."""
        retriever = KoreanHybridRetriever(tokenizer)
        retriever.index(sample_documents)

        results = retriever.search_bm25_only("보험료 납입 기간", top_k=2)

        assert len(results) > 0
        assert all(isinstance(r, HybridResult) for r in results)
        # BM25 점수가 있어야 함 (0 이상)
        assert results[0].bm25_score >= 0
        # Dense를 사용하지 않았으므로 dense_score는 0
        assert results[0].dense_score == 0

    def test_hybrid_search_with_embeddings(self, tokenizer, sample_documents, mock_embedding_func):
        """하이브리드 검색."""
        retriever = KoreanHybridRetriever(
            tokenizer,
            embedding_func=mock_embedding_func,
            bm25_weight=0.5,
            dense_weight=0.5,
        )
        retriever.index(sample_documents)

        results = retriever.search("보험금 지급", top_k=3)

        assert len(results) > 0
        assert all(isinstance(r, HybridResult) for r in results)
        # 하이브리드 결과는 두 점수 모두 가질 수 있음
        for r in results:
            assert r.score >= 0

    def test_fusion_method_rrf(self, tokenizer, sample_documents, mock_embedding_func):
        """RRF 융합 방식 테스트."""
        retriever = KoreanHybridRetriever(
            tokenizer,
            embedding_func=mock_embedding_func,
            fusion_method=FusionMethod.RRF,
        )
        retriever.index(sample_documents)

        results = retriever.search("보장금액", top_k=3)

        assert len(results) > 0
        # RRF 점수는 작은 값
        assert all(r.score < 1 for r in results)

    def test_fusion_method_weighted(self, tokenizer, sample_documents, mock_embedding_func):
        """가중합 융합 방식 테스트."""
        retriever = KoreanHybridRetriever(
            tokenizer,
            embedding_func=mock_embedding_func,
            fusion_method=FusionMethod.WEIGHTED_SUM,
            bm25_weight=0.7,
            dense_weight=0.3,
        )
        retriever.index(sample_documents)

        results = retriever.search("환급금", top_k=3)

        assert len(results) > 0

    def test_search_without_index(self, tokenizer):
        """인덱싱 없이 검색 시 에러."""
        retriever = KoreanHybridRetriever(tokenizer)

        with pytest.raises(ValueError, match="인덱스가 구축되지 않았습니다"):
            retriever.search("테스트")

    def test_index_without_embeddings(self, tokenizer, sample_documents):
        """임베딩 없이 인덱싱."""
        retriever = KoreanHybridRetriever(tokenizer)
        retriever.index(sample_documents, compute_embeddings=True)

        assert retriever.is_indexed
        assert not retriever.has_embeddings  # 임베딩 함수가 없으므로

    def test_clear(self, tokenizer, sample_documents, mock_embedding_func):
        """인덱스 초기화."""
        retriever = KoreanHybridRetriever(tokenizer, embedding_func=mock_embedding_func)
        retriever.index(sample_documents)
        assert retriever.is_indexed

        retriever.clear()

        assert not retriever.is_indexed
        assert not retriever.has_embeddings


@pytest.mark.skipif(not KOREAN_READY, reason=KOREAN_SKIP_REASON)
class TestKoreanRetrievalIntegration:
    """통합 테스트: 청킹 + 검색."""

    @pytest.fixture
    def tokenizer(self) -> KiwiTokenizer:
        return KiwiTokenizer()

    @pytest.fixture
    def insurance_document(self) -> str:
        return """
        [보험 약관]

        제1장 보험금의 지급

        제1조 (사망보험금)
        회사는 피보험자가 보험기간 중 사망하였을 때 사망보험금으로
        보험가입금액 전액을 보험수익자에게 지급합니다.

        제2조 (재해사망보험금)
        피보험자가 재해로 인하여 사망한 경우 재해사망보험금을 추가로 지급합니다.
        재해사망보험금은 보험가입금액의 100%입니다.

        제2장 보험료의 납입

        제3조 (보험료 납입기간)
        보험료 납입기간은 계약 체결시 정한 기간으로 하며,
        매월 납입일에 보험료를 납입하여야 합니다.

        제4조 (보험료 납입 연체시)
        보험료가 연체된 경우 회사는 계약을 해지할 수 있습니다.
        다만, 보험료 미납 후 30일 이내에 납입하면 계약이 유지됩니다.
        """

    def test_chunk_then_search(self, tokenizer, insurance_document):
        """청킹 후 검색 테스트."""
        # 1. 문서 청킹
        chunker = KoreanDocumentChunker(tokenizer, chunk_size=50, overlap_tokens=10)
        chunks = chunker.chunk(insurance_document)

        # 2. 청크 인덱싱
        retriever = KoreanBM25Retriever(tokenizer)
        chunk_texts = [c.text for c in chunks]
        retriever.index(chunk_texts)

        # 3. 검색
        results = retriever.search("재해 사망 보험금", top_k=3)

        # 검증
        assert len(results) > 0
        # 재해사망 관련 청크가 상위에 있어야 함
        top_doc = results[0].document
        assert "재해" in top_doc or "사망" in top_doc

    def test_hybrid_chunk_search(self, tokenizer, insurance_document):
        """하이브리드 청킹 + 검색."""
        # 1. 청킹
        chunker = KoreanDocumentChunker(tokenizer, chunk_size=60)
        chunks = chunker.chunk(insurance_document)
        chunk_texts = [c.text for c in chunks]

        # 2. 간단한 임베딩 함수
        def simple_embed(texts):
            return [[len(t) / 100] * 3 for t in texts]

        # 3. 하이브리드 검색기
        retriever = KoreanHybridRetriever(
            tokenizer,
            embedding_func=simple_embed,
            bm25_weight=0.6,
            dense_weight=0.4,
        )
        retriever.index(chunk_texts)

        # 4. 검색
        results = retriever.search("보험료 연체 해지", top_k=3)

        assert len(results) > 0

    def test_morphological_advantage(self, tokenizer):
        """형태소 분석의 이점 테스트."""
        documents = [
            "보험료를 납입합니다.",
            "보험료가 인상되었습니다.",
            "보험료의 납입이 연체되었습니다.",
            "자동차 정비 비용입니다.",
        ]

        retriever = KoreanBM25Retriever(tokenizer)
        retriever.index(documents)

        # "보험료 납입" 검색 - 형태소 분석으로 조사 변형에도 매칭
        results = retriever.search("보험료 납입", top_k=3)

        # 보험료 관련 문서가 모두 상위에 있어야 함
        top_docs = [r.document for r in results[:3]]
        assert any("보험료" in doc for doc in top_docs)
        # 자동차 정비는 관련성이 낮아야 함
        assert "자동차" not in results[0].document
