"""Korean Dense Retriever unit tests.

Tests for KoreanDenseRetriever with mocked embedding models.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from evalvault.adapters.outbound.nlp.korean import (
    DenseRetrievalResult,
    DeviceType,
    KoreanDenseRetriever,
)
from evalvault.ports.outbound import EmbeddingResult
from tests.optional_deps import kiwi_ready, rank_bm25_ready

# Check if kiwipiepy is available (needed for hybrid retriever tests)
try:
    from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer  # noqa: F401

    HAS_KIWI, KIWI_SKIP_REASON = kiwi_ready()
except ImportError:
    HAS_KIWI = False
    KIWI_SKIP_REASON = "kiwipiepy not installed"

HAS_BM25, BM25_SKIP_REASON = rank_bm25_ready()
KOREAN_READY = HAS_KIWI and HAS_BM25
if not HAS_KIWI:
    KOREAN_SKIP_REASON = KIWI_SKIP_REASON or "kiwipiepy unavailable"
else:
    KOREAN_SKIP_REASON = BM25_SKIP_REASON or "rank_bm25 unavailable"


class TestDeviceType:
    """DeviceType 열거형 테스트."""

    def test_device_types_exist(self):
        """디바이스 타입이 정의되어 있는지 확인."""
        assert DeviceType.AUTO.value == "auto"
        assert DeviceType.CPU.value == "cpu"
        assert DeviceType.CUDA.value == "cuda"
        assert DeviceType.MPS.value == "mps"


class TestDenseRetrievalResult:
    """DenseRetrievalResult 데이터클래스 테스트."""

    def test_create_result(self):
        """결과 객체 생성."""
        result = DenseRetrievalResult(
            document="테스트 문서",
            score=0.95,
            doc_id=0,
        )

        assert result.document == "테스트 문서"
        assert result.score == 0.95
        assert result.doc_id == 0
        assert result.embedding is None

    def test_create_result_with_embedding(self):
        """임베딩 포함 결과 객체 생성."""
        embedding = [0.1, 0.2, 0.3]
        result = DenseRetrievalResult(
            document="테스트 문서",
            score=0.95,
            doc_id=0,
            embedding=embedding,
        )

        assert result.embedding == embedding


class TestEmbeddingPort:
    """EmbeddingPort 인터페이스 테스트."""

    def test_embedding_result(self):
        """EmbeddingResult 데이터클래스 테스트."""
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        result = EmbeddingResult(
            embeddings=embeddings,
            dimension=2,
            model_name="test-model",
        )

        assert result.embeddings == embeddings
        assert result.dimension == 2
        assert result.model_name == "test-model"


class TestKoreanDenseRetrieverInit:
    """KoreanDenseRetriever 초기화 테스트."""

    def test_default_init(self):
        """기본 초기화."""
        retriever = KoreanDenseRetriever()

        # 기본 모델: BAAI/bge-m3 (다국어 기본 모델)
        assert retriever.model_name == "BAAI/bge-m3"
        assert retriever.dimension == 1024
        assert retriever.max_length == 8192
        assert not retriever.is_indexed
        assert retriever.document_count == 0

    def test_custom_model_init(self):
        """커스텀 모델 초기화."""
        retriever = KoreanDenseRetriever(
            model_name="jhgan/ko-sroberta-multitask",
            use_fp16=False,
            device=DeviceType.CPU,
        )

        assert retriever.model_name == "jhgan/ko-sroberta-multitask"
        assert retriever.dimension == 768
        assert retriever.max_length == 512

    def test_device_type_string(self):
        """문자열 디바이스 타입."""
        retriever = KoreanDenseRetriever(device="cpu")
        assert retriever._device == "cpu"

    def test_device_type_enum(self):
        """열거형 디바이스 타입."""
        retriever = KoreanDenseRetriever(device=DeviceType.CPU)
        assert retriever._device == "cpu"


class TestKoreanDenseRetrieverWithMock:
    """모킹을 사용한 KoreanDenseRetriever 테스트."""

    @pytest.fixture
    def mock_retriever(self):
        """모킹된 모델을 사용하는 retriever."""
        retriever = KoreanDenseRetriever(device="cpu")

        # 모델 모킹
        mock_model = MagicMock()

        # encode 결과 설정 (3개 문서, 4차원)
        mock_embeddings = np.array(
            [
                [0.1, 0.2, 0.3, 0.4],
                [0.5, 0.6, 0.7, 0.8],
                [0.9, 1.0, 1.1, 1.2],
            ]
        )
        mock_model.encode.return_value = mock_embeddings

        retriever._model = mock_model
        retriever._model_type = "sentence-transformers"

        return retriever

    def test_encode_with_mock(self, mock_retriever):
        """인코딩 테스트 (모킹)."""
        texts = ["문서1", "문서2", "문서3"]
        embeddings = mock_retriever.encode(texts)

        assert embeddings.shape == (3, 4)
        mock_retriever._model.encode.assert_called_once()

    def test_encode_query_with_mock(self, mock_retriever):
        """쿼리 인코딩 테스트 (모킹)."""
        # 단일 쿼리 인코딩
        mock_retriever._model.encode.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])

        embedding = mock_retriever.encode_query("테스트 쿼리")

        assert len(embedding) == 4
        assert embedding == pytest.approx([0.1, 0.2, 0.3, 0.4])

    def test_index_with_mock(self, mock_retriever):
        """인덱싱 테스트 (모킹)."""
        documents = [
            "보험료 납입 기간은 20년입니다.",
            "보장금액은 1억원입니다.",
            "사망보험금이 지급됩니다.",
        ]

        count = mock_retriever.index(documents)

        assert count == 3
        assert mock_retriever.is_indexed
        assert mock_retriever.document_count == 3

    def test_search_with_mock(self, mock_retriever):
        """검색 테스트 (모킹)."""
        documents = [
            "보험료 납입 기간은 20년입니다.",
            "보장금액은 1억원입니다.",
            "사망보험금이 지급됩니다.",
        ]

        # 인덱싱
        mock_retriever.index(documents)

        # 검색 시 쿼리 임베딩
        mock_retriever._model.encode.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])

        results = mock_retriever.search("보험료", top_k=2)

        assert len(results) == 2
        assert all(isinstance(r, DenseRetrievalResult) for r in results)
        # 점수 내림차순 정렬 확인
        assert results[0].score >= results[1].score

    def test_search_uses_cache(self, mock_retriever):
        """검색 캐시가 동일 쿼리에서 재사용되는지 확인."""
        documents = [
            "보험료 납입 기간은 20년입니다.",
            "보장금액은 1억원입니다.",
        ]

        mock_retriever._model.encode.return_value = np.array(
            [
                [0.1, 0.2, 0.3, 0.4],
                [0.5, 0.6, 0.7, 0.8],
            ]
        )
        mock_retriever.index(documents)

        mock_retriever._model.encode.reset_mock()
        mock_retriever._model.encode.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])

        mock_retriever.search("보험료", top_k=1)
        mock_retriever.search("보험료", top_k=1)

        assert mock_retriever._model.encode.call_count == 1

    def test_search_before_index(self, mock_retriever):
        """인덱스 없이 검색 시 에러."""
        with pytest.raises(ValueError, match="인덱스가 구축되지 않았습니다"):
            mock_retriever.search("테스트")

    def test_search_include_embeddings(self, mock_retriever):
        """임베딩 포함 검색."""
        documents = ["문서1", "문서2"]
        mock_retriever.index(documents)

        mock_retriever._model.encode.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])

        results = mock_retriever.search("쿼리", top_k=2, include_embeddings=True)

        assert results[0].embedding is not None
        assert len(results[0].embedding) == 4

    def test_add_documents(self, mock_retriever):
        """문서 추가 테스트."""
        # 초기 인덱싱
        mock_retriever._model.encode.return_value = np.array(
            [
                [0.1, 0.2, 0.3, 0.4],
                [0.5, 0.6, 0.7, 0.8],
            ]
        )
        mock_retriever.index(["문서1", "문서2"])

        # 추가 문서
        mock_retriever._model.encode.return_value = np.array(
            [
                [0.1, 0.2, 0.3, 0.4],
                [0.5, 0.6, 0.7, 0.8],
                [0.9, 1.0, 1.1, 1.2],
            ]
        )
        count = mock_retriever.add_documents(["문서3"])

        assert count == 3
        assert mock_retriever.document_count == 3

    def test_clear(self, mock_retriever):
        """인덱스 초기화 테스트."""
        mock_retriever.index(["문서1", "문서2", "문서3"])

        mock_retriever.clear()

        assert not mock_retriever.is_indexed
        assert mock_retriever.document_count == 0

    def test_index_empty_documents(self, mock_retriever):
        """빈 문서 리스트 인덱싱."""
        count = mock_retriever.index([])

        assert count == 0
        assert not mock_retriever.is_indexed

    def test_get_embedding_func(self, mock_retriever):
        """임베딩 함수 반환 테스트."""
        mock_retriever._model.encode.return_value = np.array(
            [
                [0.1, 0.2, 0.3, 0.4],
                [0.5, 0.6, 0.7, 0.8],
            ]
        )

        embedding_func = mock_retriever.get_embedding_func()

        assert callable(embedding_func)

        result = embedding_func(["텍스트1", "텍스트2"])

        assert len(result) == 2
        assert len(result[0]) == 4


class TestCosineSimilarity:
    """코사인 유사도 계산 테스트."""

    @pytest.fixture
    def retriever(self):
        """테스트용 retriever."""
        return KoreanDenseRetriever(device="cpu")

    def test_identical_vectors(self, retriever):
        """동일 벡터 유사도 = 1."""
        query = np.array([1.0, 0.0, 0.0])
        docs = np.array([[1.0, 0.0, 0.0]])

        scores = retriever._cosine_similarity(query, docs)

        assert np.isclose(scores[0], 1.0)

    def test_orthogonal_vectors(self, retriever):
        """직교 벡터 유사도 = 0."""
        query = np.array([1.0, 0.0, 0.0])
        docs = np.array([[0.0, 1.0, 0.0]])

        scores = retriever._cosine_similarity(query, docs)

        assert np.isclose(scores[0], 0.0)

    def test_opposite_vectors(self, retriever):
        """반대 벡터 유사도 = -1."""
        query = np.array([1.0, 0.0, 0.0])
        docs = np.array([[-1.0, 0.0, 0.0]])

        scores = retriever._cosine_similarity(query, docs)

        assert np.isclose(scores[0], -1.0)

    def test_multiple_documents(self, retriever):
        """여러 문서 유사도 계산."""
        query = np.array([1.0, 0.0, 0.0])
        docs = np.array(
            [
                [1.0, 0.0, 0.0],  # 동일
                [0.707, 0.707, 0.0],  # 45도
                [0.0, 1.0, 0.0],  # 직교
            ]
        )

        scores = retriever._cosine_similarity(query, docs)

        assert len(scores) == 3
        assert np.isclose(scores[0], 1.0)
        assert np.isclose(scores[1], 0.707, atol=0.01)
        assert np.isclose(scores[2], 0.0)


class TestKoreanDenseRetrieverIntegration:
    """KoreanDenseRetriever 통합 테스트 (실제 모델 사용)."""

    @pytest.fixture
    def retriever_with_model(self):
        """실제 모델을 사용하는 retriever (설치된 경우만)."""
        try:
            from sentence_transformers import SentenceTransformer  # noqa: F401

            # 경량 모델 사용
            retriever = KoreanDenseRetriever(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                use_fp16=False,
                device="cpu",
            )
            return retriever
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    @pytest.mark.slow
    def test_real_encoding(self, retriever_with_model):
        """실제 인코딩 테스트."""
        texts = ["안녕하세요", "감사합니다"]
        embeddings = retriever_with_model.encode(texts)

        assert embeddings.shape[0] == 2
        assert embeddings.shape[1] > 0  # 차원 > 0

    @pytest.mark.slow
    def test_real_search(self, retriever_with_model):
        """실제 검색 테스트."""
        documents = [
            "보험료 납입 기간은 20년입니다.",
            "보장금액은 1억원입니다.",
            "사망보험금이 지급됩니다.",
        ]

        retriever_with_model.index(documents)
        results = retriever_with_model.search("보험료", top_k=2)

        assert len(results) == 2
        # 검색 결과가 문서 중 하나여야 함 (경량 모델은 정확한 순위 보장 안함)
        assert results[0].document in documents
        # 점수가 유효한 범위인지 확인
        assert -1.0 <= results[0].score <= 1.0


class TestKoreanDenseRetrieverFaiss:
    """FAISS 인덱스 경로 테스트 (설치된 경우만)."""

    def test_faiss_search_optional(self):
        """FAISS가 설치된 경우 검색 경로가 동작하는지 확인."""
        pytest.importorskip("faiss")

        retriever = KoreanDenseRetriever(use_faiss=True, device="cpu")
        retriever._model = MagicMock()
        retriever._model_type = "sentence-transformers"
        retriever._model.encode.side_effect = [
            np.array(
                [
                    [0.1, 0.2, 0.3, 0.4],
                    [0.5, 0.6, 0.7, 0.8],
                    [0.9, 1.0, 1.1, 1.2],
                ]
            ),
            np.array([[0.1, 0.2, 0.3, 0.4]]),
        ]

        retriever.index(["문서1", "문서2", "문서3"])
        results = retriever.search("보험료", top_k=1)

        assert len(results) == 1


@pytest.mark.skipif(not KOREAN_READY, reason=KOREAN_SKIP_REASON)
class TestHybridRetrieverDenseIntegration:
    """KoreanHybridRetriever와 Dense 통합 테스트."""

    @pytest.fixture
    def mock_embedding_func(self):
        """모킹된 임베딩 함수."""

        def embedding_func(texts: list[str]) -> list[list[float]]:
            # 간단한 모킹: 텍스트 길이 기반 임베딩
            return [[len(t) * 0.1, len(t) * 0.2] for t in texts]

        return embedding_func

    def test_hybrid_with_dense_mock(self, mock_embedding_func):
        """Dense 함수를 주입한 하이브리드 검색 테스트."""
        from evalvault.adapters.outbound.nlp.korean import (
            KiwiTokenizer,
            KoreanHybridRetriever,
        )

        tokenizer = KiwiTokenizer()
        hybrid = KoreanHybridRetriever(
            tokenizer=tokenizer,
            embedding_func=mock_embedding_func,
            bm25_weight=0.5,
            dense_weight=0.5,
        )

        documents = [
            "보험료 납입 기간은 20년입니다.",
            "보장금액은 1억원입니다.",
        ]

        hybrid.index(documents, compute_embeddings=True)
        assert hybrid.has_embeddings
        assert hybrid._embeddings is not None

        results = hybrid.search("보험료", top_k=2, use_dense=True)
        assert len(results) == 2

    def test_dense_retriever_as_embedding_func(self):
        """KoreanDenseRetriever를 임베딩 함수로 사용."""
        from evalvault.adapters.outbound.nlp.korean import (
            KiwiTokenizer,
            KoreanHybridRetriever,
        )

        # 모킹된 dense retriever
        dense_retriever = KoreanDenseRetriever(device="cpu")
        dense_retriever._model = MagicMock()
        dense_retriever._model.encode.return_value = np.array(
            [
                [0.1, 0.2],
                [0.3, 0.4],
            ]
        )
        dense_retriever._model_type = "sentence-transformers"

        embedding_func = dense_retriever.get_embedding_func()

        tokenizer = KiwiTokenizer()
        hybrid = KoreanHybridRetriever(
            tokenizer=tokenizer,
            embedding_func=embedding_func,
        )

        documents = ["문서1", "문서2"]
        hybrid.index(documents, compute_embeddings=True)

        assert hybrid.has_embeddings
        assert hybrid._embeddings is not None
        assert len(hybrid._embeddings) == 2


class TestQwen3EmbeddingSupport:
    """Qwen3-Embedding 및 Matryoshka 지원 테스트."""

    def test_qwen3_models_in_supported_models(self):
        """Qwen3-Embedding 모델이 SUPPORTED_MODELS에 등록되어 있는지 확인."""
        assert "qwen3-embedding:0.6b" in KoreanDenseRetriever.SUPPORTED_MODELS
        assert "qwen3-embedding:8b" in KoreanDenseRetriever.SUPPORTED_MODELS

    def test_qwen3_model_config(self):
        """Qwen3-Embedding 모델 설정 확인."""
        config_06b = KoreanDenseRetriever.SUPPORTED_MODELS["qwen3-embedding:0.6b"]
        assert config_06b["type"] == "ollama"
        assert config_06b["matryoshka"] is True
        assert config_06b["matryoshka_range"] == (32, 768)
        assert config_06b["recommended_dim"] == 256

        config_8b = KoreanDenseRetriever.SUPPORTED_MODELS["qwen3-embedding:8b"]
        assert config_8b["type"] == "ollama"
        assert config_8b["matryoshka"] is True
        assert config_8b["matryoshka_range"] == (32, 4096)
        assert config_8b["recommended_dim"] == 1024

    def test_profile_config_dev(self):
        """dev 프로파일 설정 확인."""
        retriever = KoreanDenseRetriever()
        model, dim = retriever._get_profile_config("dev")

        assert model == "qwen3-embedding:0.6b"
        assert dim == 256

    def test_profile_config_prod(self):
        """prod 프로파일 설정 확인."""
        retriever = KoreanDenseRetriever()
        model, dim = retriever._get_profile_config("prod")

        assert model == "qwen3-embedding:8b"
        assert dim == 1024

    def test_profile_config_invalid(self):
        """잘못된 프로파일 오류 확인."""
        retriever = KoreanDenseRetriever()

        with pytest.raises(ValueError, match="Unknown profile"):
            retriever._get_profile_config("invalid")

    def test_qwen3_requires_ollama_adapter(self):
        """Ollama 어댑터 없이 Qwen3 모델 초기화 시 오류 확인."""
        with pytest.raises(ValueError, match="embedding adapter is required"):
            KoreanDenseRetriever(model_name="qwen3-embedding:0.6b")

    def test_qwen3_with_mock_adapter(self):
        """모킹된 Ollama 어댑터로 Qwen3 모델 초기화."""
        mock_adapter = MagicMock()
        mock_adapter.embed_sync.return_value = [[0.1, 0.2, 0.3] * 85 + [0.1]]  # 256 dim

        retriever = KoreanDenseRetriever(
            model_name="qwen3-embedding:0.6b",
            ollama_adapter=mock_adapter,
            matryoshka_dim=256,
        )

        assert retriever.model_name == "qwen3-embedding:0.6b"
        assert retriever.matryoshka_dim == 256
        assert retriever.dimension == 256

    def test_qwen3_auto_dimension_selection(self):
        """Matryoshka 차원 자동 선택 확인."""
        mock_adapter = MagicMock()

        retriever = KoreanDenseRetriever(
            model_name="qwen3-embedding:0.6b",
            ollama_adapter=mock_adapter,
            # matryoshka_dim not specified - should auto-select
        )

        # Should auto-select recommended_dim
        assert retriever._matryoshka_dim == 256

    def test_profile_based_init(self):
        """프로파일 기반 초기화 확인."""
        mock_adapter = MagicMock()

        retriever = KoreanDenseRetriever(
            profile="dev",
            ollama_adapter=mock_adapter,
        )

        assert retriever.model_name == "qwen3-embedding:0.6b"
        assert retriever.matryoshka_dim == 256
        assert retriever.dimension == 256

    def test_encode_with_ollama_mock(self):
        """Ollama 어댑터로 인코딩 테스트."""
        mock_adapter = MagicMock()
        mock_embeddings = [[0.1] * 256, [0.2] * 256]
        mock_adapter.embed_sync.return_value = mock_embeddings

        retriever = KoreanDenseRetriever(
            model_name="qwen3-embedding:0.6b",
            ollama_adapter=mock_adapter,
            matryoshka_dim=256,
        )

        texts = ["보험료 납입", "보장금액"]
        embeddings = retriever.encode(texts)

        mock_adapter.embed_sync.assert_called_once_with(
            texts=texts,
            model="qwen3-embedding:0.6b",
            dimension=256,
        )

        assert embeddings.shape == (2, 256)

    def test_matryoshka_dim_property(self):
        """matryoshka_dim 프로퍼티 확인."""
        mock_adapter = MagicMock()

        retriever = KoreanDenseRetriever(
            model_name="qwen3-embedding:8b",
            ollama_adapter=mock_adapter,
            matryoshka_dim=1024,
        )

        assert retriever.matryoshka_dim == 1024

    def test_default_model_no_matryoshka(self):
        """기본 HuggingFace 모델은 Matryoshka 없음 확인."""
        retriever = KoreanDenseRetriever()

        assert retriever.matryoshka_dim is None
        assert retriever._ollama_adapter is None
