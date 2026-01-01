"""Unit tests for RAG trace entities."""

import pytest

from evalvault.domain.entities.rag_trace import (
    GenerationData,
    RAGTraceData,
    RerankMethod,
    RetrievalData,
    RetrievalMethod,
    RetrievedDocument,
)


class TestRetrievedDocument:
    """RetrievedDocument 엔티티 테스트."""

    def test_basic_creation(self):
        """기본 생성 테스트."""
        doc = RetrievedDocument(
            content="보험 약관 내용입니다.",
            score=0.89,
            rank=1,
            source="insurance_policy.pdf",
        )

        assert doc.content == "보험 약관 내용입니다."
        assert doc.score == 0.89
        assert doc.rank == 1
        assert doc.source == "insurance_policy.pdf"
        assert doc.was_reranked is False

    def test_with_rerank(self):
        """리랭킹 적용 문서 테스트."""
        doc = RetrievedDocument(
            content="내용",
            score=0.7,
            rank=3,
            source="doc.pdf",
            rerank_score=0.95,
            rerank_rank=1,
        )

        assert doc.was_reranked is True
        assert doc.rank_change == 2  # 3 - 1 = 2 (상승)

    def test_rank_change_negative(self):
        """순위 하락 테스트."""
        doc = RetrievedDocument(
            content="내용",
            score=0.9,
            rank=1,
            source="doc.pdf",
            rerank_score=0.5,
            rerank_rank=5,
        )

        assert doc.rank_change == -4  # 1 - 5 = -4 (하락)

    def test_metadata(self):
        """메타데이터 테스트."""
        doc = RetrievedDocument(
            content="내용",
            score=0.8,
            rank=1,
            source="doc.pdf",
            metadata={"page": 5, "section": "coverage"},
            chunk_id="chunk_001",
        )

        assert doc.metadata["page"] == 5
        assert doc.chunk_id == "chunk_001"


class TestRetrievalData:
    """RetrievalData 엔티티 테스트."""

    @pytest.fixture
    def sample_candidates(self):
        """샘플 검색 후보 문서."""
        return [
            RetrievedDocument(content="doc1", score=0.9, rank=1, source="a.pdf"),
            RetrievedDocument(content="doc2", score=0.7, rank=2, source="b.pdf"),
            RetrievedDocument(content="doc3", score=0.5, rank=3, source="c.pdf"),
        ]

    def test_basic_creation(self, sample_candidates):
        """기본 생성 테스트."""
        data = RetrievalData(
            query="보험 보장금액은?",
            retrieval_method="hybrid",
            embedding_model="text-embedding-3-small",
            top_k=5,
            retrieval_time_ms=45.3,
            candidates=sample_candidates,
        )

        assert data.query == "보험 보장금액은?"
        assert data.retrieval_method == "hybrid"
        assert data.num_candidates == 3

    def test_avg_score(self, sample_candidates):
        """평균 점수 계산 테스트."""
        data = RetrievalData(candidates=sample_candidates)

        expected = (0.9 + 0.7 + 0.5) / 3
        assert data.avg_score == pytest.approx(expected)

    def test_top_score(self, sample_candidates):
        """최고 점수 테스트."""
        data = RetrievalData(candidates=sample_candidates)

        assert data.top_score == 0.9

    def test_score_gap(self, sample_candidates):
        """점수 갭 테스트."""
        data = RetrievalData(candidates=sample_candidates)

        assert data.score_gap == pytest.approx(0.4)  # 0.9 - 0.5

    def test_empty_candidates(self):
        """빈 후보 테스트."""
        data = RetrievalData(candidates=[])

        assert data.num_candidates == 0
        assert data.avg_score is None
        assert data.top_score is None
        assert data.score_gap is None

    def test_precision_at_k(self, sample_candidates):
        """Precision@K 계산 테스트."""
        data = RetrievalData(candidates=sample_candidates)

        relevant = {"a.pdf", "c.pdf"}  # 2 relevant docs

        # P@1: a.pdf is relevant
        assert data.get_precision_at_k(1, relevant) == 1.0

        # P@2: a.pdf relevant, b.pdf not
        assert data.get_precision_at_k(2, relevant) == 0.5

        # P@3: 2 out of 3 relevant
        assert data.get_precision_at_k(3, relevant) == pytest.approx(2 / 3)

    def test_to_span_attributes(self, sample_candidates):
        """OpenTelemetry span 변환 테스트."""
        data = RetrievalData(
            retrieval_method="dense",
            embedding_model="text-embedding-3-small",
            top_k=5,
            retrieval_time_ms=45.3,
            candidates=sample_candidates,
            rerank_method="cross_encoder",
            rerank_time_ms=12.5,
        )

        attrs = data.to_span_attributes()

        assert attrs["retrieval.method"] == "dense"
        assert attrs["retrieval.top_k"] == 5
        assert attrs["retrieval.time_ms"] == 45.3
        assert attrs["retrieval.num_candidates"] == 3
        assert attrs["retrieval.embedding_model"] == "text-embedding-3-small"
        assert attrs["retrieval.rerank_method"] == "cross_encoder"
        assert attrs["retrieval.rerank_time_ms"] == 12.5


class TestGenerationData:
    """GenerationData 엔티티 테스트."""

    def test_basic_creation(self):
        """기본 생성 테스트."""
        data = GenerationData(
            model="gpt-5-nano",
            prompt="질문: 보험 보장금액은?",
            response="보장금액은 1억원입니다.",
            temperature=0.0,
            generation_time_ms=500.0,
            input_tokens=150,
            output_tokens=20,
            total_tokens=170,
        )

        assert data.model == "gpt-5-nano"
        assert data.input_tokens == 150
        assert data.output_tokens == 20
        assert data.total_tokens == 170

    def test_tokens_per_second(self):
        """초당 토큰 계산 테스트."""
        data = GenerationData(
            model="gpt-5-nano",
            generation_time_ms=1000.0,  # 1 second
            output_tokens=50,
        )

        assert data.tokens_per_second == 50.0

    def test_tokens_per_second_zero_time(self):
        """시간이 0일 때 테스트."""
        data = GenerationData(
            model="gpt-5-nano",
            generation_time_ms=0.0,
            output_tokens=50,
        )

        assert data.tokens_per_second is None

    def test_cost_per_token(self):
        """토큰당 비용 계산 테스트."""
        data = GenerationData(
            model="gpt-5-nano",
            total_tokens=1000,
            cost_usd=0.01,
        )

        assert data.cost_per_token == pytest.approx(0.00001)

    def test_to_span_attributes(self):
        """OpenTelemetry span 변환 테스트."""
        data = GenerationData(
            model="gpt-5-nano",
            generation_time_ms=500.0,
            input_tokens=150,
            output_tokens=20,
            total_tokens=170,
            temperature=0.7,
            max_tokens=1000,
            cost_usd=0.005,
            stop_reason="stop",
        )

        attrs = data.to_span_attributes()

        assert attrs["generation.model"] == "gpt-5-nano"
        assert attrs["generation.time_ms"] == 500.0
        assert attrs["generation.input_tokens"] == 150
        assert attrs["generation.output_tokens"] == 20
        assert attrs["generation.total_tokens"] == 170
        assert attrs["generation.temperature"] == 0.7
        assert attrs["generation.max_tokens"] == 1000
        assert attrs["generation.cost_usd"] == 0.005
        assert attrs["generation.stop_reason"] == "stop"


class TestRAGTraceData:
    """RAGTraceData 엔티티 테스트."""

    def test_basic_creation(self):
        """기본 생성 테스트."""
        retrieval = RetrievalData(retrieval_time_ms=50.0)
        generation = GenerationData(generation_time_ms=450.0)

        data = RAGTraceData(
            trace_id="abc123",
            query="질문",
            retrieval=retrieval,
            generation=generation,
            final_answer="답변",
            total_time_ms=500.0,
        )

        assert data.trace_id == "abc123"
        assert data.total_time_ms == 500.0

    def test_retrieval_ratio(self):
        """검색 비율 테스트."""
        retrieval = RetrievalData(retrieval_time_ms=100.0)
        generation = GenerationData(generation_time_ms=400.0)

        data = RAGTraceData(
            retrieval=retrieval,
            generation=generation,
            total_time_ms=500.0,
        )

        assert data.retrieval_ratio == pytest.approx(0.2)  # 100/500
        assert data.generation_ratio == pytest.approx(0.8)  # 400/500

    def test_ratios_without_data(self):
        """데이터 없을 때 비율 테스트."""
        data = RAGTraceData(total_time_ms=500.0)

        assert data.retrieval_ratio is None
        assert data.generation_ratio is None

    def test_to_span_attributes(self):
        """OpenTelemetry span 변환 테스트."""
        retrieval = RetrievalData(
            retrieval_method="hybrid",
            retrieval_time_ms=50.0,
            top_k=5,
        )
        generation = GenerationData(
            model="gpt-5-nano",
            generation_time_ms=450.0,
        )

        data = RAGTraceData(
            retrieval=retrieval,
            generation=generation,
            total_time_ms=500.0,
        )

        attrs = data.to_span_attributes()

        assert attrs["rag.total_time_ms"] == 500.0
        assert attrs["retrieval.method"] == "hybrid"
        assert attrs["generation.model"] == "gpt-5-nano"
        assert "rag.retrieval_ratio" in attrs
        assert "rag.generation_ratio" in attrs


class TestEnums:
    """Enum 테스트."""

    def test_retrieval_method(self):
        """RetrievalMethod enum 테스트."""
        assert RetrievalMethod.BM25.value == "bm25"
        assert RetrievalMethod.DENSE.value == "dense"
        assert RetrievalMethod.HYBRID.value == "hybrid"

    def test_rerank_method(self):
        """RerankMethod enum 테스트."""
        assert RerankMethod.CROSS_ENCODER.value == "cross_encoder"
        assert RerankMethod.COLBERT.value == "colbert"
        assert RerankMethod.NONE.value == "none"


class TestEntityExports:
    """엔티티 export 테스트."""

    def test_entities_exported_from_package(self):
        """패키지에서 export되는지 테스트."""
        from evalvault.domain.entities import (
            GenerationData,
            RAGTraceData,
            RerankMethod,
            RetrievalData,
            RetrievalMethod,
            RetrievedDocument,
        )

        assert RetrievedDocument is not None
        assert RetrievalData is not None
        assert GenerationData is not None
        assert RAGTraceData is not None
        assert RetrievalMethod is not None
        assert RerankMethod is not None
