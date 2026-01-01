"""Korean NLP adapters.

한국어 자연어 처리를 위한 어댑터 모듈입니다.
Kiwi 형태소 분석기를 기반으로 토큰화, 키워드 추출, 검색 등을 제공합니다.

Modules:
    kiwi_tokenizer: Kiwi 기반 토크나이저
    korean_stopwords: 한국어 불용어 사전
    bm25_retriever: BM25 기반 검색기
    document_chunker: 문서 청킹
    hybrid_retriever: 하이브리드 검색 (BM25 + Dense)
    dense_retriever: Dense 임베딩 검색 (BGE-M3)
    korean_evaluation: 한국어 RAG 평가 유틸리티
"""

from evalvault.adapters.outbound.nlp.korean.bm25_retriever import (
    KoreanBM25Retriever,
    RetrievalResult,
)
from evalvault.adapters.outbound.nlp.korean.dense_retriever import (
    DenseRetrievalResult,
    DeviceType,
    KoreanDenseRetriever,
)
from evalvault.adapters.outbound.nlp.korean.document_chunker import (
    Chunk,
    KoreanDocumentChunker,
    ParagraphChunker,
)
from evalvault.adapters.outbound.nlp.korean.hybrid_retriever import (
    FusionMethod,
    HybridResult,
    KoreanHybridRetriever,
)
from evalvault.adapters.outbound.nlp.korean.kiwi_tokenizer import KiwiTokenizer
from evalvault.adapters.outbound.nlp.korean.korean_evaluation import (
    ClaimVerification,
    FaithfulnessResult,
    KoreanFaithfulnessChecker,
    KoreanSemanticSimilarity,
    SemanticSimilarityResult,
)
from evalvault.adapters.outbound.nlp.korean.korean_stopwords import (
    KOREAN_STOPWORDS,
    STOPWORD_POS_TAGS,
    is_stopword,
)
from evalvault.adapters.outbound.nlp.korean.toolkit import KoreanNLPToolkit

__all__ = [
    # Tokenizer
    "KiwiTokenizer",
    # Stopwords
    "KOREAN_STOPWORDS",
    "STOPWORD_POS_TAGS",
    "is_stopword",
    # BM25 Retriever
    "KoreanBM25Retriever",
    "RetrievalResult",
    # Document Chunker
    "KoreanDocumentChunker",
    "ParagraphChunker",
    "Chunk",
    # Hybrid Retriever
    "KoreanHybridRetriever",
    "HybridResult",
    "FusionMethod",
    # Dense Retriever
    "KoreanDenseRetriever",
    "DenseRetrievalResult",
    "DeviceType",
    # Korean Evaluation
    "KoreanFaithfulnessChecker",
    "KoreanSemanticSimilarity",
    "FaithfulnessResult",
    "ClaimVerification",
    "SemanticSimilarityResult",
    # Toolkit
    "KoreanNLPToolkit",
]
