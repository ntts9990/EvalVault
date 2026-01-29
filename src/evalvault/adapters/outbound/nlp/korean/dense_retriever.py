"""Korean Dense Retriever with BGE-M3 and Qwen3-Embedding support.

한국어 Dense 임베딩 기반 검색을 제공합니다.
BGE-M3-Korean 모델을 기본으로 사용하며, Qwen3-Embedding (Ollama) 및 sentence-transformers를 지원합니다.

Qwen3-Embedding Features:
    - Matryoshka Representation Learning (MRL): 가변 차원 임베딩 지원
    - 0.6B 모델: 32~768 차원 (개발용, 권장: 256)
    - 8B 모델: 32~4096 차원 (운영용, 권장: 1024)

Example:
    >>> from evalvault.adapters.outbound.nlp.korean.dense_retriever import KoreanDenseRetriever
    >>> retriever = KoreanDenseRetriever()
    >>> retriever.index(["보험료 납입 기간은 20년입니다.", "보장금액은 1억원입니다."])
    >>> results = retriever.search("보험료 기간", top_k=1)

    # Qwen3-Embedding with Matryoshka (Ollama)
    >>> from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter
    >>> adapter = OllamaAdapter(settings)
    >>> retriever = KoreanDenseRetriever(
    ...     model_name="qwen3-embedding:0.6b",
    ...     ollama_adapter=adapter,
    ...     matryoshka_dim=256,
    ... )
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

import numpy as np

from evalvault.config.phoenix_support import instrumentation_span, set_span_attributes

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
        # ===== HuggingFace Models =====
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
        # ===== Ollama Qwen3-Embedding Models (Matryoshka 지원) =====
        # 폐쇄망 환경용 Qwen3-Embedding
        # Matryoshka Representation Learning으로 가변 차원 임베딩 지원
        "qwen3-embedding:0.6b": {  # 개발용 (경량)
            "dimension": 768,  # 기본 차원 (Matryoshka로 축소 가능)
            "max_length": 8192,
            "type": "ollama",
            "matryoshka": True,
            "matryoshka_range": (32, 768),
            "recommended_dim": 256,  # 개발용 권장 차원
        },
        "qwen3-embedding:8b": {  # 운영용 (고성능)
            "dimension": 4096,  # 기본 차원
            "max_length": 8192,
            "type": "ollama",
            "matryoshka": True,
            "matryoshka_range": (32, 4096),
            "recommended_dim": 1024,  # 운영용 권장 차원
        },
    }

    # 기본 모델: BAAI/bge-m3 (멀티링거시 기본)
    DEFAULT_MODEL = "BAAI/bge-m3"

    def __init__(
        self,
        model_name: str | None = None,
        use_fp16: bool = True,
        device: str | DeviceType = DeviceType.AUTO,
        batch_size: int = 32,
        ollama_adapter: Any = None,
        matryoshka_dim: int | None = None,
        profile: str | None = None,
        use_faiss: bool = False,
        faiss_use_gpu: bool | None = None,
        faiss_index_type: str = "flat",
        faiss_ivf_nlist: int = 128,
        faiss_ivf_nprobe: int = 16,
        faiss_hnsw_m: int = 32,
        faiss_hnsw_ef_search: int = 128,
        faiss_hnsw_ef_construction: int = 200,
        faiss_pq_m: int = 16,
        faiss_pq_nbits: int = 8,
        query_cache_size: int = 256,
        search_cache_size: int = 256,
        normalize_embeddings: bool = True,
    ) -> None:
        """KoreanDenseRetriever 초기화.

        Args:
            model_name: 사용할 모델 이름 (기본: dragonkue/BGE-m3-ko)
            use_fp16: FP16 양자화 사용 (메모리 절약)
            device: 디바이스 (auto, cpu, cuda, mps)
            batch_size: 인코딩 배치 크기
                - 0 이하로 설정하면 간단한 휴리스틱으로 자동 결정
        ollama_adapter: OpenAI 호환 임베딩 어댑터 (Ollama/vLLM)
            matryoshka_dim: Matryoshka 차원 (Qwen3-Embedding 전용)
                - None: 모델 권장 차원 사용
                - 256: 개발용 (속도 우선)
                - 1024: 운영용 (품질 우선)
            profile: 프로파일 이름 ('dev' 또는 'prod')
                - 'dev': qwen3-embedding:0.6b, dim=256
                - 'prod': qwen3-embedding:8b, dim=1024
            use_faiss: FAISS 인덱스 사용 여부 (선택)
            faiss_use_gpu: FAISS GPU 사용 여부 (None이면 CUDA 가능 시 자동 선택)
            faiss_index_type: FAISS 인덱스 타입 (flat, hnsw, ivf, ivf_pq)
            faiss_ivf_nlist: IVF 클러스터 수 (ivf/ivf_pq 전용)
            faiss_ivf_nprobe: IVF 검색 시 탐색할 클러스터 수
            faiss_hnsw_m: HNSW 그래프 차수
            faiss_hnsw_ef_search: HNSW 검색 효율 파라미터
            faiss_hnsw_ef_construction: HNSW 구축 효율 파라미터
            faiss_pq_m: PQ 서브벡터 수 (ivf_pq 전용)
            faiss_pq_nbits: PQ 비트 수 (ivf_pq 전용)
            query_cache_size: 쿼리 임베딩 캐시 크기
            search_cache_size: 검색 결과 캐시 크기
            normalize_embeddings: 코사인 유사도 계산을 위한 정규화 여부

        Example:
            >>> # HuggingFace 모델 사용 (기존 방식)
            >>> retriever = KoreanDenseRetriever()

            >>> # Ollama Qwen3-Embedding 사용 (profile 기반)
            >>> retriever = KoreanDenseRetriever(profile="dev", ollama_adapter=adapter)

            >>> # 직접 모델/차원 지정
            >>> retriever = KoreanDenseRetriever(
            ...     model_name="qwen3-embedding:8b",
            ...     matryoshka_dim=1024,
            ...     ollama_adapter=adapter,
            ... )
        """
        # Profile-based model selection
        if profile:
            model_name, matryoshka_dim = self._get_profile_config(profile)

        self._model_name = model_name or self.DEFAULT_MODEL
        self._use_fp16 = use_fp16
        self._device = self._resolve_device(device)
        self._batch_size = batch_size
        self._ollama_adapter = ollama_adapter
        self._matryoshka_dim = matryoshka_dim
        self._use_faiss = use_faiss
        self._faiss_use_gpu = faiss_use_gpu
        self._faiss_index_type = (faiss_index_type or "flat").lower()
        self._faiss_ivf_nlist = max(1, faiss_ivf_nlist)
        self._faiss_ivf_nprobe = max(1, faiss_ivf_nprobe)
        self._faiss_hnsw_m = max(4, faiss_hnsw_m)
        self._faiss_hnsw_ef_search = max(1, faiss_hnsw_ef_search)
        self._faiss_hnsw_ef_construction = max(1, faiss_hnsw_ef_construction)
        self._faiss_pq_m = max(1, faiss_pq_m)
        self._faiss_pq_nbits = max(1, faiss_pq_nbits)
        self._faiss_ivf_nlist_used: int | None = None
        self._faiss_ivf_nprobe_used: int | None = None
        self._normalize_embeddings = normalize_embeddings or use_faiss
        self._query_cache_size = max(query_cache_size, 0)
        self._search_cache_size = max(search_cache_size, 0)

        # Validate embedding adapter for OpenAI-compatible embedding models
        model_info = self.SUPPORTED_MODELS.get(self._model_name)
        if model_info and model_info.get("type") == "ollama" and not self._ollama_adapter:
            raise ValueError(
                f"embedding adapter is required for model '{self._model_name}'. "
                "Create one with: OllamaAdapter(settings) or VLLMAdapter(settings)"
            )

        # Auto-select matryoshka dimension if not specified
        if model_info and model_info.get("matryoshka") and self._matryoshka_dim is None:
            self._matryoshka_dim = model_info.get("recommended_dim")
            logger.info(
                f"Auto-selected Matryoshka dimension: {self._matryoshka_dim} for {self._model_name}"
            )

        if self._use_faiss and not normalize_embeddings:
            logger.info("FAISS uses cosine similarity; enabling embedding normalization.")

        self._model: Any = None
        self._model_type: str | None = None

        self._documents: list[str] = []
        self._embeddings: np.ndarray | None = None
        self._normalized_embeddings: np.ndarray | None = None
        self._faiss_index: Any | None = None
        self._faiss_gpu_active = False
        self._query_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._search_cache: OrderedDict[tuple[str, int], list[tuple[int, float]]] = OrderedDict()

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
        """임베딩 차원.

        Matryoshka 모델의 경우 설정된 matryoshka_dim을 반환합니다.
        """
        # Matryoshka dimension takes precedence
        if self._matryoshka_dim is not None:
            return self._matryoshka_dim

        model_info = self.SUPPORTED_MODELS.get(self._model_name)
        if model_info:
            return model_info["dimension"]
        return 1024  # 기본값

    @property
    def matryoshka_dim(self) -> int | None:
        """Matryoshka 차원 (설정된 경우)."""
        return self._matryoshka_dim

    @property
    def faiss_gpu_active(self) -> bool:
        """FAISS GPU 인덱스 사용 여부."""
        return bool(self._faiss_gpu_active)

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

    def _get_profile_config(self, profile: str) -> tuple[str, int]:
        """프로파일에 따른 모델/차원 설정을 반환합니다.

        Args:
            profile: 'dev' 또는 'prod'

        Returns:
            (model_name, matryoshka_dim) 튜플
        """
        profiles = {
            "dev": ("qwen3-embedding:0.6b", 256),
            "prod": ("qwen3-embedding:8b", 1024),
        }

        if profile not in profiles:
            raise ValueError(f"Unknown profile: {profile}. Use 'dev' or 'prod'.")

        return profiles[profile]

    def _load_model(self) -> None:
        """모델 로딩 (lazy loading).

        Ollama 모델의 경우 별도 로딩이 필요 없습니다 (어댑터 사용).
        """
        if self._model is not None:
            return

        model_info = self.SUPPORTED_MODELS.get(self._model_name)
        if model_info is None and self._ollama_adapter is not None:
            model_type = "ollama"
        else:
            model_type = model_info["type"] if model_info else "sentence-transformers"

        # Ollama models use adapter directly - no model loading needed
        if model_type == "ollama":
            self._model_type = "ollama"
            self._model = True  # Mark as loaded
            logger.info(
                f"Using Ollama adapter for: {self._model_name} "
                f"(matryoshka_dim: {self._matryoshka_dim})"
            )
            return

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

    def _clear_search_cache(self) -> None:
        """검색 결과 캐시를 초기화합니다."""
        self._search_cache.clear()

    def _clear_query_cache(self) -> None:
        """쿼리 임베딩 캐시를 초기화합니다."""
        self._query_cache.clear()

    def _resolve_batch_size(self, total: int, override: int | None) -> int:
        """배치 크기를 결정합니다."""
        if override is not None:
            return max(1, override)
        if self._batch_size > 0:
            return max(1, min(self._batch_size, total)) if total > 0 else max(1, self._batch_size)

        base = 64 if self._device != "cpu" else 32
        if self.dimension >= 2048:
            base = max(8, base // 2)
        if total > 0:
            return max(1, min(base, total))
        return base

    def _normalize_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """행 단위로 임베딩을 정규화합니다."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return embeddings / norms

    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """벡터를 정규화합니다."""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def _get_cached_query_embedding(self, query: str) -> np.ndarray:
        """쿼리 임베딩 캐시 조회 또는 생성."""
        if self._query_cache_size <= 0:
            embedding = self.encode([query])[0]
            return np.asarray(embedding, dtype=np.float32)

        cached = self._query_cache.get(query)
        if cached is not None:
            self._query_cache.move_to_end(query)
            return cached

        embedding = self.encode([query])[0]
        embedding = np.asarray(embedding, dtype=np.float32)
        self._query_cache[query] = embedding
        self._query_cache.move_to_end(query)

        if len(self._query_cache) > self._query_cache_size:
            self._query_cache.popitem(last=False)

        return embedding

    def _get_cached_search(self, query: str, top_k: int) -> list[tuple[int, float]] | None:
        """검색 결과 캐시 조회."""
        if self._search_cache_size <= 0:
            return None
        key = (query, top_k)
        cached = self._search_cache.get(key)
        if cached is not None:
            self._search_cache.move_to_end(key)
        return cached

    def _store_search_cache(
        self,
        query: str,
        top_k: int,
        results: list[tuple[int, float]],
    ) -> None:
        """검색 결과 캐시 저장."""
        if self._search_cache_size <= 0:
            return
        key = (query, top_k)
        self._search_cache[key] = results
        self._search_cache.move_to_end(key)
        if len(self._search_cache) > self._search_cache_size:
            self._search_cache.popitem(last=False)

    def _select_top_k(self, scores: np.ndarray, top_k: int) -> np.ndarray:
        """상위 k개 인덱스를 효율적으로 선택."""
        if top_k >= len(scores):
            return scores.argsort()[::-1]

        top_indices = np.argpartition(scores, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        return top_indices

    def _faiss_gpu_available(self, faiss: Any) -> bool:
        """FAISS GPU 사용 가능 여부 확인."""
        try:
            get_num_gpus = getattr(faiss, "get_num_gpus", None)
            if callable(get_num_gpus):
                return get_num_gpus() > 0
        except Exception:
            return False
        return False

    def _resolve_faiss_gpu(self, faiss: Any) -> bool:
        """GPU 사용 여부를 결정합니다."""
        available = self._faiss_gpu_available(faiss)
        if self._faiss_use_gpu is None:
            return available
        if self._faiss_use_gpu and not available:
            logger.warning("FAISS GPU requested but CUDA is unavailable. Falling back to CPU.")
            return False
        return bool(self._faiss_use_gpu)

    def _build_faiss_index(self, embeddings: np.ndarray) -> None:
        """FAISS 인덱스를 구축합니다."""
        try:
            import faiss  # type: ignore
        except ImportError:
            logger.warning("faiss not installed. Falling back to numpy search.")
            self._faiss_index = None
            self._faiss_gpu_active = False
            return

        embeddings = np.asarray(embeddings, dtype=np.float32)
        dimension = embeddings.shape[1]

        index_type = self._faiss_index_type
        metric = faiss.METRIC_INNER_PRODUCT
        index: Any
        ivf_nlist = min(self._faiss_ivf_nlist, max(1, embeddings.shape[0]))
        ivf_nprobe = min(self._faiss_ivf_nprobe, ivf_nlist)

        if index_type in {"ivf_pq", "pq"} and dimension % self._faiss_pq_m != 0:
            logger.warning(
                "FAISS PQ requires dimension divisible by m=%s. Falling back to IVF flat.",
                self._faiss_pq_m,
            )
            index_type = "ivf"

        if index_type == "flat":
            index = faiss.IndexFlatIP(dimension)
        elif index_type == "hnsw":
            try:
                index = faiss.IndexHNSWFlat(dimension, self._faiss_hnsw_m, metric)
            except TypeError:
                index = faiss.IndexHNSWFlat(dimension, self._faiss_hnsw_m)
                if hasattr(index, "metric_type"):
                    index.metric_type = metric
            if hasattr(index, "hnsw"):
                index.hnsw.efSearch = self._faiss_hnsw_ef_search
                index.hnsw.efConstruction = self._faiss_hnsw_ef_construction
        elif index_type in {"ivf", "ivf_flat"}:
            quantizer = faiss.IndexFlatIP(dimension)
            try:
                index = faiss.IndexIVFFlat(quantizer, dimension, ivf_nlist, metric)
            except TypeError:
                index = faiss.IndexIVFFlat(quantizer, dimension, ivf_nlist)
        elif index_type in {"ivf_pq", "pq"}:
            quantizer = faiss.IndexFlatIP(dimension)
            try:
                index = faiss.IndexIVFPQ(
                    quantizer,
                    dimension,
                    ivf_nlist,
                    self._faiss_pq_m,
                    self._faiss_pq_nbits,
                    metric,
                )
            except TypeError:
                index = faiss.IndexIVFPQ(
                    quantizer,
                    dimension,
                    ivf_nlist,
                    self._faiss_pq_m,
                    self._faiss_pq_nbits,
                )
        else:
            logger.warning("Unknown FAISS index type '%s'. Falling back to flat.", index_type)
            index = faiss.IndexFlatIP(dimension)

        if hasattr(index, "is_trained") and not index.is_trained:
            index.train(embeddings)

        use_gpu = self._resolve_faiss_gpu(faiss)
        self._faiss_gpu_active = False

        if use_gpu:
            try:
                resources = faiss.StandardGpuResources()
                index = faiss.index_cpu_to_gpu(resources, 0, index)
                self._faiss_gpu_active = True
            except Exception as exc:  # pragma: no cover - optional GPU path
                logger.warning("Failed to enable FAISS GPU: %s", exc)

        if hasattr(index, "nprobe"):
            index.nprobe = ivf_nprobe
            self._faiss_ivf_nlist_used = ivf_nlist
            self._faiss_ivf_nprobe_used = ivf_nprobe
        else:
            self._faiss_ivf_nlist_used = None
            self._faiss_ivf_nprobe_used = None

        index.add(embeddings)
        self._faiss_index = index
        logger.info("FAISS index ready: %s vectors", embeddings.shape[0])

    def _search_with_faiss(
        self,
        query_embedding: np.ndarray,
        top_k: int,
    ) -> list[tuple[int, float]]:
        """FAISS 인덱스로 검색합니다."""
        if self._faiss_index is None:
            return []

        query = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
        distances, indices = self._faiss_index.search(query, top_k)
        results: list[tuple[int, float]] = []
        for idx, score in zip(indices[0], distances[0], strict=False):
            if idx < 0:
                continue
            results.append((int(idx), float(score)))
        return results

    def _build_results(
        self,
        doc_scores: list[tuple[int, float]],
        include_embeddings: bool,
    ) -> list[DenseRetrievalResult]:
        """검색 결과 객체를 생성합니다."""
        results = []
        for doc_id, score in doc_scores:
            embedding = None
            if include_embeddings and self._embeddings is not None:
                embedding = self._embeddings[doc_id].tolist()

            results.append(
                DenseRetrievalResult(
                    document=self._documents[doc_id],
                    score=score,
                    doc_id=doc_id,
                    embedding=embedding,
                )
            )
        return results

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

        batch_size = self._resolve_batch_size(len(texts), batch_size)

        if self._model_type == "ollama":
            # Ollama Qwen3-Embedding with Matryoshka
            embeddings = self._encode_with_ollama(texts, show_progress=show_progress)
        elif self._model_type == "bge-m3":
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

        return np.asarray(embeddings, dtype=np.float32)

    def _encode_with_ollama(
        self,
        texts: list[str],
        show_progress: bool = False,
    ) -> np.ndarray:
        """Ollama adapter를 사용하여 임베딩 생성.

        Matryoshka 차원을 자동으로 적용합니다.

        Args:
            texts: 임베딩할 텍스트 리스트
            show_progress: 진행 상황 표시 (현재 미사용)

        Returns:
            임베딩 벡터 배열
        """
        if not self._ollama_adapter:
            raise ValueError("Ollama adapter is not configured")

        # Use sync version of embed
        embeddings = self._ollama_adapter.embed_sync(
            texts=texts,
            model=self._model_name,
            dimension=self._matryoshka_dim,
        )

        if show_progress:
            logger.info(f"Encoded {len(texts)} texts with Ollama (dim={self._matryoshka_dim})")

        return np.array(embeddings)

    def encode_query(self, query: str) -> list[float]:
        """단일 쿼리를 임베딩합니다.

        Args:
            query: 쿼리 텍스트

        Returns:
            임베딩 벡터
        """
        embedding = self._get_cached_query_embedding(query)
        return embedding.tolist()

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

        span_attrs = {
            "retriever.type": "dense",
            "retriever.documents": len(documents),
            "retriever.model": self._model_name,
        }
        batch_size = self._resolve_batch_size(len(documents), None)
        index_started_at = time.perf_counter()
        with instrumentation_span("retriever.dense.index", span_attrs) as span:
            self._documents = documents
            self._embeddings = self.encode(documents, show_progress=True)

            if self._embeddings is not None:
                if self._normalize_embeddings:
                    self._normalized_embeddings = self._normalize_matrix(self._embeddings)
                else:
                    self._normalized_embeddings = None

                if self._use_faiss:
                    embeddings_for_index = (
                        self._normalized_embeddings
                        if self._normalized_embeddings is not None
                        else self._embeddings
                    )
                    self._build_faiss_index(embeddings_for_index)
                else:
                    self._faiss_index = None

            self._clear_search_cache()

            index_build_time_ms = (time.perf_counter() - index_started_at) * 1000

            if span and self._embeddings is not None:
                faiss_attrs = {"retriever.faiss_index_type": self._faiss_index_type}
                if self._faiss_index_type in {"ivf", "ivf_flat", "ivf_pq", "pq"}:
                    faiss_attrs["retriever.faiss_nlist"] = (
                        self._faiss_ivf_nlist_used or self._faiss_ivf_nlist
                    )
                    faiss_attrs["retriever.faiss_nprobe"] = (
                        self._faiss_ivf_nprobe_used or self._faiss_ivf_nprobe
                    )
                if self._faiss_index_type == "hnsw":
                    faiss_attrs["retriever.faiss_hnsw_m"] = self._faiss_hnsw_m
                set_span_attributes(
                    span,
                    {
                        "retriever.embedding_dim": int(self._embeddings.shape[1]),
                        "retriever.device": self._device,
                        "retriever.index_size": len(documents),
                        "retriever.batch_size": batch_size,
                        "retriever.faiss_gpu_active": self._faiss_gpu_active,
                        "retriever.index_build_time_ms": index_build_time_ms,
                        **faiss_attrs,
                    },
                )

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

        if top_k <= 0:
            return []

        top_k = min(top_k, self.document_count)

        span_attrs = {
            "retriever.type": "dense",
            "retriever.top_k": top_k,
            "retriever.model": self._model_name,
        }
        with instrumentation_span("retriever.dense.search", span_attrs) as span:
            cached = self._get_cached_search(query, top_k)
            cache_hit = cached is not None
            if cache_hit:
                results = self._build_results(cached, include_embeddings)
            else:
                query_embedding = self._get_cached_query_embedding(query)
                if self._normalize_embeddings:
                    query_embedding = self._normalize_vector(query_embedding)

                if self._faiss_index is not None:
                    doc_scores = self._search_with_faiss(query_embedding, top_k)
                else:
                    embeddings = (
                        self._normalized_embeddings
                        if self._normalize_embeddings and self._normalized_embeddings is not None
                        else self._embeddings
                    )
                    if embeddings is None:
                        raise ValueError(
                            "임베딩이 초기화되지 않았습니다. index()를 다시 실행하세요."
                        )

                    if self._normalize_embeddings:
                        scores = np.dot(embeddings, query_embedding)
                    else:
                        scores = self._cosine_similarity(query_embedding, embeddings)
                    top_indices = self._select_top_k(scores, top_k)
                    doc_scores = [(int(idx), float(scores[idx])) for idx in top_indices]

                self._store_search_cache(query, top_k, doc_scores)
                results = self._build_results(doc_scores, include_embeddings)

            if span:
                set_span_attributes(
                    span,
                    {
                        "retriever.result_count": len(results),
                        "retriever.total_docs_searched": self.document_count,
                        "retriever.cache_hit": cache_hit,
                        "retriever.faiss_gpu_active": self._faiss_gpu_active,
                        "retriever.faiss_index_type": self._faiss_index_type,
                    },
                )

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
        self._normalized_embeddings = None
        self._faiss_index = None
        self._faiss_gpu_active = False
        self._documents = []
        self._clear_search_cache()
        self._clear_query_cache()
        logger.info("Dense 인덱스 초기화")
