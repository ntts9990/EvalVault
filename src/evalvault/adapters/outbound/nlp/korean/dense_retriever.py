"""Korean Dense Retriever with BGE-M3 support.

한국어 Dense 임베딩 기반 검색을 제공합니다.
BGE-M3-Korean 모델을 기본으로 사용하며, sentence-transformers로 fallback합니다.

Example:
    >>> from evalvault.adapters.outbound.nlp.korean.dense_retriever import KoreanDenseRetriever
    >>> retriever = KoreanDenseRetriever()
    >>> retriever.index(["보험료 납입 기간은 20년입니다.", "보장금액은 1억원입니다."])
    >>> results = retriever.search("보험료 기간", top_k=1)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """디바이스 타입."""

    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Silicon


@dataclass
class DenseRetrievalResult:
    """Dense 검색 결과.

    Attributes:
        document: 검색된 문서 텍스트
        score: 코사인 유사도 점수 (0.0 ~ 1.0)
        doc_id: 문서 인덱스
        embedding: 문서 임베딩 벡터 (선택)
    """

    document: str
    score: float
    doc_id: int
    embedding: list[float] | None = None


class KoreanDenseRetriever:
    """한국어 Dense 임베딩 기반 검색기.

    BGE-M3-Korean 모델을 사용하여 의미 기반 검색을 제공합니다.
    FP16 양자화 및 다양한 디바이스(CPU, CUDA, MPS)를 지원합니다.

    Attributes:
        model_name: 사용 모델 이름
        use_fp16: FP16 양자화 사용 여부
        device: 디바이스 타입

    Example:
        >>> retriever = KoreanDenseRetriever(use_fp16=True)
        >>> retriever.index(documents)
        >>> results = retriever.search("보험료 납입", top_k=5)
    """

    # 지원 모델 목록
    # 벤치마크 참고: https://huggingface.co/dragonkue/BGE-m3-ko
    # dragonkue/BGE-m3-ko가 AutoRAG 벤치마크에서 upskyy/bge-m3-korean보다
    # +39.4% 높은 성능 (0.7456 vs 0.5351)
    SUPPORTED_MODELS = {
        "dragonkue/BGE-m3-ko": {  # 1순위: 한국어 최고 성능
            "dimension": 1024,
            "max_length": 8192,
            "type": "sentence-transformers",  # SentenceTransformer 호환
            "benchmark": {"autorag_topk1": 0.7456, "miracl_ndcg10": 0.6833},
        },
        "upskyy/bge-m3-korean": {  # 2순위
            "dimension": 1024,
            "max_length": 8192,
            "type": "bge-m3",
            "benchmark": {"autorag_topk1": 0.5351},
        },
        "BAAI/bge-m3": {  # Multilingual fallback
            "dimension": 1024,
            "max_length": 8192,
            "type": "bge-m3",
        },
        "jhgan/ko-sroberta-multitask": {  # 경량 모델
            "dimension": 768,
            "max_length": 512,
            "type": "sentence-transformers",
        },
        "intfloat/multilingual-e5-large": {  # 다국어
            "dimension": 1024,
            "max_length": 512,
            "type": "sentence-transformers",
        },
    }

    # 기본 모델: dragonkue/BGE-m3-ko (AutoRAG 벤치마크 1위)
    DEFAULT_MODEL = "dragonkue/BGE-m3-ko"

    def __init__(
        self,
        model_name: str | None = None,
        use_fp16: bool = True,
        device: str | DeviceType = DeviceType.AUTO,
        batch_size: int = 32,
    ) -> None:
        """KoreanDenseRetriever 초기화.

        Args:
            model_name: 사용할 모델 이름 (기본: upskyy/bge-m3-korean)
            use_fp16: FP16 양자화 사용 (메모리 절약)
            device: 디바이스 (auto, cpu, cuda, mps)
            batch_size: 인코딩 배치 크기
        """
        self._model_name = model_name or self.DEFAULT_MODEL
        self._use_fp16 = use_fp16
        self._device = self._resolve_device(device)
        self._batch_size = batch_size

        self._model: Any = None
        self._model_type: str | None = None

        self._documents: list[str] = []
        self._embeddings: np.ndarray | None = None

    @property
    def is_indexed(self) -> bool:
        """인덱스가 구축되었는지 확인."""
        return self._embeddings is not None and len(self._embeddings) > 0

    @property
    def document_count(self) -> int:
        """인덱싱된 문서 수."""
        return len(self._documents)

    @property
    def dimension(self) -> int:
        """임베딩 차원."""
        model_info = self.SUPPORTED_MODELS.get(self._model_name)
        if model_info:
            return model_info["dimension"]
        return 1024  # 기본값

    @property
    def model_name(self) -> str:
        """모델 이름."""
        return self._model_name

    @property
    def max_length(self) -> int:
        """최대 입력 토큰 수."""
        model_info = self.SUPPORTED_MODELS.get(self._model_name)
        if model_info:
            return model_info["max_length"]
        return 512  # 기본값

    def _resolve_device(self, device: str | DeviceType) -> str:
        """디바이스 자동 감지."""
        if isinstance(device, DeviceType):
            device = device.value

        if device == "auto":
            try:
                import torch

                if torch.cuda.is_available():
                    return "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    return "mps"
                else:
                    return "cpu"
            except ImportError:
                return "cpu"

        return device

    def _load_model(self) -> None:
        """모델 로딩 (lazy loading)."""
        if self._model is not None:
            return

        model_info = self.SUPPORTED_MODELS.get(self._model_name)
        model_type = model_info["type"] if model_info else "sentence-transformers"

        logger.info(
            f"Loading model: {self._model_name} (type: {model_type}, device: {self._device})"
        )

        if model_type == "bge-m3":
            self._load_bge_m3_model()
        else:
            self._load_sentence_transformer_model()

        self._model_type = model_type

    def _load_bge_m3_model(self) -> None:
        """BGE-M3 모델 로딩."""
        try:
            from FlagEmbedding import BGEM3FlagModel

            self._model = BGEM3FlagModel(
                self._model_name,
                use_fp16=self._use_fp16,
                device=self._device,
            )
            logger.info(f"Loaded BGE-M3 model: {self._model_name}")
        except ImportError:
            logger.warning(
                "FlagEmbedding not installed. Falling back to sentence-transformers. "
                "Install with: uv add FlagEmbedding"
            )
            self._load_sentence_transformer_model()

    def _load_sentence_transformer_model(self) -> None:
        """sentence-transformers 모델 로딩."""
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name, device=self._device)

            if self._use_fp16 and self._device != "cpu":
                self._model = self._model.half()

            logger.info(f"Loaded sentence-transformers model: {self._model_name}")
        except ImportError as e:
            raise ImportError(
                "sentence-transformers not installed. Install with: uv add sentence-transformers"
            ) from e

    def encode(
        self,
        texts: list[str],
        *,
        batch_size: int | None = None,
        show_progress: bool = False,
    ) -> np.ndarray:
        """텍스트를 임베딩 벡터로 변환합니다.

        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기 (기본: 인스턴스 설정)
            show_progress: 진행 상황 표시 여부

        Returns:
            임베딩 벡터 배열 (shape: [len(texts), dimension])

        Raises:
            ImportError: 필요한 패키지가 설치되지 않은 경우
        """
        self._load_model()

        batch_size = batch_size or self._batch_size

        if self._model_type == "bge-m3":
            # BGE-M3 모델
            result = self._model.encode(
                texts,
                batch_size=batch_size,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )
            # BGE-M3는 dict 반환
            embeddings = result["dense_vecs"] if isinstance(result, dict) else result
        else:
            # sentence-transformers
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
            )

        return np.array(embeddings)

    def encode_query(self, query: str) -> list[float]:
        """단일 쿼리를 임베딩합니다.

        Args:
            query: 쿼리 텍스트

        Returns:
            임베딩 벡터
        """
        embeddings = self.encode([query])
        return embeddings[0].tolist()

    def index(self, documents: list[str]) -> int:
        """문서를 인덱싱합니다.

        Dense 임베딩을 계산하여 인덱스를 구축합니다.

        Args:
            documents: 인덱싱할 문서 리스트

        Returns:
            인덱싱된 문서 수

        Raises:
            ImportError: 필요한 패키지가 설치되지 않은 경우
        """
        if not documents:
            logger.warning("빈 문서 리스트로 인덱싱 시도")
            return 0

        self._documents = documents
        self._embeddings = self.encode(documents, show_progress=True)

        logger.info(f"Dense 인덱스 구축 완료: {len(documents)}개 문서")
        return len(documents)

    def search(
        self,
        query: str,
        top_k: int = 5,
        include_embeddings: bool = False,
    ) -> list[DenseRetrievalResult]:
        """쿼리로 문서를 검색합니다.

        코사인 유사도 기반으로 가장 유사한 문서를 반환합니다.

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            include_embeddings: 결과에 임베딩 포함 여부

        Returns:
            검색 결과 리스트 (점수 내림차순)

        Raises:
            ValueError: 인덱스가 구축되지 않은 경우
        """
        if not self.is_indexed:
            raise ValueError("인덱스가 구축되지 않았습니다. index()를 먼저 호출하세요.")

        # 쿼리 임베딩
        query_embedding = self.encode([query])[0]

        # 코사인 유사도 계산
        scores = self._cosine_similarity(query_embedding, self._embeddings)

        # 상위 k개 인덱스
        top_indices = scores.argsort()[::-1][:top_k]

        results = []
        for idx in top_indices:
            idx = int(idx)
            score = float(scores[idx])

            result = DenseRetrievalResult(
                document=self._documents[idx],
                score=score,
                doc_id=idx,
                embedding=self._embeddings[idx].tolist() if include_embeddings else None,
            )
            results.append(result)

        return results

    def _cosine_similarity(
        self,
        query_embedding: np.ndarray,
        doc_embeddings: np.ndarray,
    ) -> np.ndarray:
        """코사인 유사도 계산."""
        # 정규화
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)

        # 내적 = 코사인 유사도 (정규화된 벡터)
        return np.dot(doc_norms, query_norm)

    def get_embedding_func(self) -> Callable[[list[str]], list[list[float]]]:
        """KoreanHybridRetriever에 주입할 임베딩 함수 반환.

        Returns:
            임베딩 함수 (texts -> embeddings)

        Example:
            >>> retriever = KoreanDenseRetriever()
            >>> embedding_func = retriever.get_embedding_func()
            >>> hybrid = KoreanHybridRetriever(tokenizer, embedding_func=embedding_func)
        """

        def embedding_func(texts: list[str]) -> list[list[float]]:
            embeddings = self.encode(texts)
            return embeddings.tolist()

        return embedding_func

    def add_documents(self, documents: list[str]) -> int:
        """문서를 추가하고 인덱스를 재구축합니다.

        Args:
            documents: 추가할 문서 리스트

        Returns:
            전체 인덱싱된 문서 수
        """
        all_docs = self._documents + documents
        return self.index(all_docs)

    def clear(self) -> None:
        """인덱스를 초기화합니다."""
        self._embeddings = None
        self._documents = []
        logger.info("Dense 인덱스 초기화")
