"""RAG trace data entities for observability.

이 모듈은 RAG 파이프라인의 검색(Retrieval)과 생성(Generation) 단계의
상세 데이터를 캡처하기 위한 엔티티들을 정의합니다.

Phoenix/OpenTelemetry와 연동하여 다음 분석을 가능하게 합니다:
- 검색 품질 분석 (Precision@K, NDCG, 점수 분포)
- 생성 파라미터 최적화 (프롬프트 A/B 테스트)
- 레이턴시 분해 (검색 vs 생성 병목 식별)

Example:
    >>> from evalvault.domain.entities.rag_trace import RetrievalData, RetrievedDocument
    >>> doc = RetrievedDocument(
    ...     content="보험 약관 내용...",
    ...     score=0.89,
    ...     rank=1,
    ...     source="insurance_policy.pdf",
    ... )
    >>> retrieval = RetrievalData(
    ...     retrieval_method="hybrid",
    ...     top_k=5,
    ...     retrieval_time_ms=45.3,
    ...     candidates=[doc],
    ... )
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RetrievalMethod(str, Enum):
    """검색 방법 유형."""

    BM25 = "bm25"
    DENSE = "dense"
    HYBRID = "hybrid"
    SPARSE = "sparse"
    RERANK = "rerank"


class RerankMethod(str, Enum):
    """리랭킹 방법 유형."""

    CROSS_ENCODER = "cross_encoder"
    COLBERT = "colbert"
    COHERE = "cohere"
    BGE = "bge"
    NONE = "none"


@dataclass
class RetrievedDocument:
    """검색된 개별 문서.

    검색 시스템에서 반환된 각 문서의 상세 정보를 캡처합니다.

    Attributes:
        content: 문서 내용 (또는 청크)
        score: 검색 점수 (0.0 ~ 1.0 정규화 권장)
        rank: 검색 순위 (1부터 시작)
        source: 원본 문서 식별자 (파일명, URL 등)
        metadata: 추가 메타데이터 (페이지 번호, 섹션 등)
        rerank_score: 리랭킹 후 점수 (리랭킹 적용 시)
        rerank_rank: 리랭킹 후 순위 (리랭킹 적용 시)
        chunk_id: 청크 식별자 (chunking 적용 시)
        embedding_vector: 임베딩 벡터 (시각화용, 선택적)
    """

    content: str
    score: float
    rank: int
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    rerank_score: float | None = None
    rerank_rank: int | None = None
    chunk_id: str | None = None
    embedding_vector: list[float] | None = None

    @property
    def was_reranked(self) -> bool:
        """리랭킹이 적용되었는지 여부."""
        return self.rerank_score is not None

    @property
    def rank_change(self) -> int | None:
        """리랭킹으로 인한 순위 변화 (양수: 상승, 음수: 하락)."""
        if self.rerank_rank is None:
            return None
        return self.rank - self.rerank_rank


@dataclass
class RetrievalData:
    """검색 단계 전체 데이터.

    RAG 파이프라인의 검색(Retrieval) 단계에서 발생하는
    모든 데이터를 캡처합니다.

    Attributes:
        query: 사용자 쿼리 (검색에 사용된 원본 또는 변환된 쿼리)
        retrieval_method: 검색 방법 (bm25, dense, hybrid 등)
        embedding_model: 임베딩 모델명 (dense 검색 시)
        top_k: 검색할 문서 수
        retrieval_time_ms: 검색 소요 시간 (밀리초)
        candidates: 검색된 문서 목록
        rerank_method: 리랭킹 방법 (적용 시)
        rerank_time_ms: 리랭킹 소요 시간 (밀리초)
        total_docs_searched: 전체 검색 대상 문서 수
        similarity_threshold: 유사도 임계값 (필터링 적용 시)
        metadata: 추가 메타데이터
        timestamp: 검색 수행 시각
    """

    query: str = ""
    retrieval_method: str = "dense"
    embedding_model: str | None = None
    top_k: int = 5
    retrieval_time_ms: float = 0.0
    candidates: list[RetrievedDocument] = field(default_factory=list)
    rerank_method: str | None = None
    rerank_time_ms: float | None = None
    total_docs_searched: int | None = None
    similarity_threshold: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def num_candidates(self) -> int:
        """검색된 문서 수."""
        return len(self.candidates)

    @property
    def avg_score(self) -> float | None:
        """검색 문서들의 평균 점수."""
        if not self.candidates:
            return None
        return sum(d.score for d in self.candidates) / len(self.candidates)

    @property
    def top_score(self) -> float | None:
        """최고 검색 점수."""
        if not self.candidates:
            return None
        return max(d.score for d in self.candidates)

    @property
    def score_gap(self) -> float | None:
        """최고 점수와 최저 점수의 차이.

        점수 갭이 크면 검색 결과가 명확히 구분됨을 의미합니다.
        """
        if len(self.candidates) < 2:
            return None
        scores = [d.score for d in self.candidates]
        return max(scores) - min(scores)

    def get_precision_at_k(self, k: int, relevant_sources: set[str]) -> float:
        """Precision@K 계산.

        Args:
            k: 상위 K개 문서
            relevant_sources: 관련 문서 source 집합

        Returns:
            Precision@K 값 (0.0 ~ 1.0)
        """
        if k <= 0 or not self.candidates:
            return 0.0
        top_k = self.candidates[:k]
        relevant_count = sum(1 for d in top_k if d.source in relevant_sources)
        return relevant_count / k

    def to_span_attributes(self) -> dict[str, Any]:
        """OpenTelemetry span attributes로 변환."""
        attrs = {
            "retrieval.method": self.retrieval_method,
            "retrieval.top_k": self.top_k,
            "retrieval.time_ms": self.retrieval_time_ms,
            "retrieval.num_candidates": self.num_candidates,
        }
        if self.embedding_model:
            attrs["retrieval.embedding_model"] = self.embedding_model
        if self.avg_score is not None:
            attrs["retrieval.avg_score"] = self.avg_score
        if self.top_score is not None:
            attrs["retrieval.top_score"] = self.top_score
        if self.score_gap is not None:
            attrs["retrieval.score_gap"] = self.score_gap
        if self.rerank_method:
            attrs["retrieval.rerank_method"] = self.rerank_method
        if self.rerank_time_ms:
            attrs["retrieval.rerank_time_ms"] = self.rerank_time_ms
        if self.total_docs_searched is not None:
            attrs["retrieval.total_docs_searched"] = self.total_docs_searched
        if self.similarity_threshold is not None:
            attrs["retrieval.similarity_threshold"] = self.similarity_threshold
        return attrs


@dataclass
class GenerationData:
    """생성 단계 데이터.

    RAG 파이프라인의 생성(Generation) 단계에서 발생하는
    모든 데이터를 캡처합니다.

    Attributes:
        model: 사용된 LLM 모델명
        prompt_template: 프롬프트 템플릿 (변수 치환 전)
        prompt: 실제 전송된 프롬프트
        response: LLM 응답
        temperature: 샘플링 온도
        max_tokens: 최대 토큰 수
        generation_time_ms: 생성 소요 시간 (밀리초)
        input_tokens: 입력 토큰 수
        output_tokens: 출력 토큰 수
        total_tokens: 총 토큰 수
        cost_usd: 비용 (USD)
        stop_reason: 생성 중단 이유 (stop, length, etc.)
        metadata: 추가 메타데이터 (top_p, frequency_penalty 등)
        timestamp: 생성 수행 시각
    """

    model: str = ""
    prompt_template: str | None = None
    prompt: str = ""
    response: str = ""
    temperature: float = 0.0
    max_tokens: int | None = None
    generation_time_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float | None = None
    stop_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def tokens_per_second(self) -> float | None:
        """초당 생성 토큰 수."""
        if self.generation_time_ms <= 0 or self.output_tokens <= 0:
            return None
        return self.output_tokens / (self.generation_time_ms / 1000)

    @property
    def cost_per_token(self) -> float | None:
        """토큰당 비용."""
        if self.total_tokens <= 0 or self.cost_usd is None:
            return None
        return self.cost_usd / self.total_tokens

    def to_span_attributes(self) -> dict[str, Any]:
        """OpenTelemetry span attributes로 변환."""
        attrs = {
            "generation.model": self.model,
            "generation.time_ms": self.generation_time_ms,
            "generation.input_tokens": self.input_tokens,
            "generation.output_tokens": self.output_tokens,
            "generation.total_tokens": self.total_tokens,
            "generation.temperature": self.temperature,
        }
        if self.max_tokens:
            attrs["generation.max_tokens"] = self.max_tokens
        if self.cost_usd is not None:
            attrs["generation.cost_usd"] = self.cost_usd
        if self.cost_per_token is not None:
            attrs["generation.cost_per_token"] = self.cost_per_token
        if self.stop_reason:
            attrs["generation.stop_reason"] = self.stop_reason
        if self.tokens_per_second:
            attrs["generation.tokens_per_second"] = self.tokens_per_second
        if self.metadata:
            for key, value in self.metadata.items():
                attrs[f"generation.meta.{key}"] = value
        return attrs


@dataclass
class RAGTraceData:
    """RAG 파이프라인 전체 추적 데이터.

    검색과 생성 단계의 데이터를 통합하여 전체 RAG 파이프라인의
    성능을 분석할 수 있게 합니다.

    Attributes:
        trace_id: 추적 ID (OpenTelemetry trace ID)
        query: 사용자 원본 쿼리
        retrieval: 검색 단계 데이터
        generation: 생성 단계 데이터
        final_answer: 최종 응답
        total_time_ms: 전체 소요 시간
        metadata: 추가 메타데이터
    """

    trace_id: str = ""
    query: str = ""
    retrieval: RetrievalData | None = None
    generation: GenerationData | None = None
    final_answer: str = ""
    total_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def retrieval_ratio(self) -> float | None:
        """전체 시간 중 검색 비율.

        검색이 병목인지 생성이 병목인지 식별하는 데 유용합니다.
        """
        if self.total_time_ms <= 0 or self.retrieval is None:
            return None
        return self.retrieval.retrieval_time_ms / self.total_time_ms

    @property
    def generation_ratio(self) -> float | None:
        """전체 시간 중 생성 비율."""
        if self.total_time_ms <= 0 or self.generation is None:
            return None
        return self.generation.generation_time_ms / self.total_time_ms

    def to_span_attributes(self) -> dict[str, Any]:
        """OpenTelemetry span attributes로 변환."""
        attrs = {
            "rag.total_time_ms": self.total_time_ms,
        }
        if self.retrieval:
            attrs.update(self.retrieval.to_span_attributes())
        if self.generation:
            attrs.update(self.generation.to_span_attributes())
        if self.retrieval_ratio is not None:
            attrs["rag.retrieval_ratio"] = self.retrieval_ratio
        if self.generation_ratio is not None:
            attrs["rag.generation_ratio"] = self.generation_ratio
        return attrs
