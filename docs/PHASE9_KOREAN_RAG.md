# Phase 9: Korean RAG Optimization

> **Status**: Planning
> **Priority**: 🔥 High
> **Goal**: 한국어 RAG 시스템 성능을 실질적으로 향상시키는 도구와 가이드 제공

---

## 목표

1. **한국어 형태소 분석 통합**: Kiwi 기반 토큰화
2. **한국어 특화 키워드 추출**: 조사/어미 제거, 의미 단위 추출
3. **한국어 검색 최적화**: BM25 + 형태소 분석
4. **한국어 RAG 평가 개선**: 한국어 특성 반영 메트릭
5. **벤치마크 및 가이드**: 성능 비교 데이터 및 최적화 가이드

---

## 기술 스택 선정

### 형태소 분석기 비교

| 분석기 | 언어 | 설치 용이성 | 성능 | 선택 |
|--------|------|-------------|------|------|
| **Kiwi** | Pure Python | ✅ pip install | 빠름, 정확 | ✅ **선택** |
| Mecab-ko | C++ (Python wrapper) | ❌ 별도 설치 필요 | 매우 빠름 | ❌ |
| Komoran | Java | ❌ JVM 필요 | 보통 | ❌ |
| Okt (KoNLPy) | Java | ❌ JVM 필요 | 보통 | ❌ |
| soynlp | Pure Python | ✅ pip install | 비지도학습 | 🔄 보조 |

**결정**: **Kiwi** (kiwipiepy)
- Pure Python, pip install만으로 설치
- 빠른 속도 (100만 문자/초)
- 높은 정확도 (세종 코퍼스 기준 97%+)
- 사용자 사전 지원

---

### 한국어 임베딩 모델 비교 (2024-2025)

> 참고: [BGE-M3 Korean](https://huggingface.co/upskyy/bge-m3-korean), [dragonkue/BGE-m3-ko](https://huggingface.co/dragonkue/BGE-m3-ko)

| 모델 | 차원 | Max Tokens | 특징 | 선택 |
|------|------|------------|------|------|
| **upskyy/bge-m3-korean** | 1024 | 8192 | BGE-M3 한국어 파인튜닝, Dense+Sparse+ColBERT | ✅ **1순위** |
| **dragonkue/BGE-m3-ko** | 1024 | 8192 | 568M params, 한국어 벤치마크 우수 | ✅ **2순위** |
| BAAI/bge-m3 | 1024 | 8192 | 100+ 언어, Dense+Sparse+Multi-vec | 🔄 Fallback |
| intfloat/multilingual-e5-large | 1024 | 512 | 다국어, 안정적 | 🔄 대안 |
| jhgan/ko-sroberta-multitask | 768 | 512 | 한국어 특화, 작은 크기 | 🔄 경량 |

**결정**: **upskyy/bge-m3-korean** (1순위)
- 한국어에 특화된 파인튜닝
- 8192 토큰 지원 (긴 문서 처리 가능)
- Dense + Sparse + ColBERT 3가지 검색 모드 지원
- 영어-한국어 유사도 0.78-0.94 달성

---

### SPLADE for Korean: 효과 분석

> 참고: [Naver SPLADE GitHub](https://github.com/naver/splade), [Korean SPLADE 연구](https://arxiv.org/html/2511.22263v1)

#### SPLADE 한국어 적용 가능성

| 항목 | 평가 | 상세 |
|------|------|------|
| **효과** | ✅ 높음 | 2.6억 한국어 query-document 페어로 검증됨 |
| **BM25 대비** | ✅ 우수 | 복잡한 쿼리에서 특히 좋은 성능 |
| **핵심 조건** | ⚠️ 어휘 선택 | 한국어 vocab이 잘 맞는 모델 필수 |

#### 한국어 SPLADE 권장 백본

```
✅ 권장 (한국어 vocab 우수):
- klue/roberta-base
- skt/A.X-Encoder-base
- monologg/koelectra-base-v3

❌ 비권장 (vocab 불일치):
- jhu-clsp/mmBERT-base → 한국어 표현 붕괴 (all-zero)
- 영어 중심 모델 → 토큰 과분절화
```

#### 핵심 인사이트

> "Before asking 'Which backbone should I use?', ask 'Can this model's vocabulary properly express the language in my data?'"
> — [HuggingFace Blog: Vocabulary in Sparse Retrieval](https://huggingface.co/blog/yjoonjang/vocabulary-is-the-most-important-element-in-splade)

한국어에서 어휘가 맞지 않는 토크나이저는:
- 토큰 과분절화 (보험 → ▁보, ##험)
- 희귀 서브워드 매핑
- 희소성 압력 하에서 all-zero 출력 학습

---

### 하이브리드 검색 전략 (권장)

BGE-M3 모델은 **Dense + Sparse + ColBERT**를 동시 지원하므로, 하이브리드 검색이 최적:

```python
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel('upskyy/bge-m3-korean', use_fp16=True)

# Dense, Sparse, ColBERT 임베딩 동시 생성
embeddings = model.encode(
    sentences,
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=True
)

# 하이브리드 스코어 계산
dense_score = dense_similarity(query_embed, doc_embed)
sparse_score = sparse_dot_product(query_sparse, doc_sparse)  # SPLADE 스타일
colbert_score = colbert_score(query_vecs, doc_vecs)

# 가중치 조합 (Reciprocal Rank Fusion)
final_score = rrf(dense_rank, sparse_rank, colbert_rank)
```

#### 검색 모드별 특성

| 모드 | 장점 | 단점 | 보험 도메인 적합성 |
|------|------|------|------------------|
| Dense | 의미 유사도 | 정확한 용어 매칭 약함 | 🔄 보통 |
| Sparse (SPLADE) | 정확한 용어 매칭 | 의미 확장 한계 | ✅ 높음 (보험 용어) |
| ColBERT | 토큰 레벨 매칭 | 계산 비용 | ✅ 높음 |
| **Hybrid** | 모든 장점 통합 | 복잡도 | ✅✅ 최적 |

---

## 구현 계획

### Phase 9.1: Korean NLP Foundation (Week 1)

> **목표**: Kiwi 형태소 분석기 통합 및 기본 한국어 처리 인프라

#### 새 파일 구조

```
src/evalvault/
├── adapters/outbound/nlp/
│   └── korean/
│       ├── __init__.py
│       ├── kiwi_tokenizer.py      # Kiwi 기반 토크나이저
│       ├── korean_stopwords.py    # 한국어 불용어 사전
│       └── korean_utils.py        # 유틸리티 함수
├── ports/outbound/
│   └── korean_nlp_port.py         # 한국어 NLP 포트
```

#### KiwiTokenizer 설계

```python
from kiwipiepy import Kiwi

class KiwiTokenizer:
    """Kiwi 기반 한국어 토크나이저.

    형태소 분석을 통해 의미있는 토큰을 추출합니다.
    """

    def __init__(
        self,
        remove_particles: bool = True,      # 조사 제거
        remove_endings: bool = True,        # 어미 제거
        use_lemma: bool = True,             # 원형 사용
        user_dict_path: str | None = None,  # 사용자 사전
    ):
        self.kiwi = Kiwi()
        self.remove_particles = remove_particles
        self.remove_endings = remove_endings
        self.use_lemma = use_lemma

        if user_dict_path:
            self._load_user_dict(user_dict_path)

    def tokenize(self, text: str) -> list[str]:
        """텍스트를 형태소 분석하여 토큰 리스트 반환.

        Args:
            text: 입력 텍스트

        Returns:
            토큰 리스트 (불용어/조사/어미 제거됨)
        """
        tokens = []
        for token in self.kiwi.tokenize(text):
            # 조사(J*), 어미(E*), 기호(S*) 제외
            if self.remove_particles and token.tag.startswith('J'):
                continue
            if self.remove_endings and token.tag.startswith('E'):
                continue
            if token.tag.startswith('S'):
                continue

            # 원형 사용 또는 표면형 사용
            form = token.lemma if self.use_lemma else token.form
            tokens.append(form)

        return tokens

    def extract_nouns(self, text: str) -> list[str]:
        """명사만 추출."""
        nouns = []
        for token in self.kiwi.tokenize(text):
            if token.tag.startswith('N'):  # NNG, NNP, NNB, ...
                nouns.append(token.lemma)
        return nouns

    def extract_keywords(
        self,
        text: str,
        pos_tags: list[str] = ['NNG', 'NNP', 'VV', 'VA']
    ) -> list[str]:
        """키워드 품사만 추출 (명사, 동사, 형용사)."""
        keywords = []
        for token in self.kiwi.tokenize(text):
            if token.tag in pos_tags:
                keywords.append(token.lemma)
        return keywords
```

#### 한국어 불용어 사전

```python
# korean_stopwords.py

KOREAN_STOPWORDS = {
    # 일반 불용어
    '것', '수', '등', '및', '또', '때', '더', '이', '그', '저',
    '있다', '하다', '되다', '않다', '없다', '같다',

    # 보험 도메인 불용어 (맥락에 따라 조정)
    '경우', '해당', '관련', '대한', '위한', '통해', '따라',

    # 접속사/부사
    '그리고', '그러나', '또한', '따라서', '그래서', '하지만',
}

# 품사 기반 불용어 태그
STOPWORD_POS_TAGS = {
    'JKS', 'JKC', 'JKG', 'JKO', 'JKB', 'JKV', 'JKQ',  # 격조사
    'JX', 'JC',  # 보조사, 접속조사
    'EP', 'EF', 'EC', 'ETN', 'ETM',  # 어미
    'SF', 'SP', 'SS', 'SE', 'SO',  # 기호
}
```

#### 테스트 목표

- [ ] Kiwi 설치 및 기본 동작 확인
- [ ] 토큰화 정확도 테스트 (보험 도메인 텍스트)
- [ ] 사용자 사전 로드 테스트
- [ ] 성능 벤치마크 (처리 속도)

---

### Phase 9.2: Korean Keyword Extraction (Week 1-2)

> **목표**: 형태소 분석 기반 키워드 추출로 NLP 분석 품질 향상

#### NLPAnalysisAdapter 개선

```python
# nlp_adapter.py 수정

class NLPAnalysisAdapter:
    def __init__(
        self,
        llm: LLMPort | None = None,
        korean_tokenizer: KiwiTokenizer | None = None,  # 추가
    ):
        self.llm = llm
        self.korean_tokenizer = korean_tokenizer or KiwiTokenizer()

    def _extract_keywords_korean(
        self,
        texts: list[str],
        top_n: int = 20
    ) -> list[KeywordInfo]:
        """한국어 형태소 분석 기반 키워드 추출."""
        # 1. 형태소 분석으로 토큰 추출
        all_tokens = []
        for text in texts:
            tokens = self.korean_tokenizer.extract_keywords(text)
            all_tokens.extend(tokens)

        # 2. TF-IDF 계산 (형태소 기반)
        from sklearn.feature_extraction.text import TfidfVectorizer

        # 각 문서를 형태소 분석 후 공백 연결
        tokenized_docs = [
            ' '.join(self.korean_tokenizer.extract_keywords(text))
            for text in texts
        ]

        vectorizer = TfidfVectorizer(max_features=100)
        tfidf_matrix = vectorizer.fit_transform(tokenized_docs)

        # 3. 키워드 점수 계산
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.sum(axis=0).A1

        keywords = []
        for idx in scores.argsort()[::-1][:top_n]:
            keyword = feature_names[idx]
            tfidf_score = scores[idx]
            frequency = all_tokens.count(keyword)

            keywords.append(KeywordInfo(
                keyword=keyword,
                tfidf_score=tfidf_score,
                frequency=frequency,
            ))

        return keywords
```

#### 개선 효과 예시

```
Before (공백 기반):
  키워드: ['보험료가', '얼마인가요', '무엇인가요', '가능합니다', '있습니다']

After (형태소 분석):
  키워드: ['보험료', '보장', '가입', '보험', '납입', '사망', '만기', '연금']
```

---

### Phase 9.3: Korean Chunking & Retrieval (Week 2)

> **목표**: 의미 단위 청킹 및 한국어 검색 최적화

#### KoreanDocumentChunker

```python
class KoreanDocumentChunker:
    """한국어 특화 문서 청킹.

    형태소 분석을 활용하여 의미 단위로 청킹합니다.
    """

    def __init__(
        self,
        tokenizer: KiwiTokenizer,
        chunk_size: int = 500,       # 토큰 수 기준
        overlap_tokens: int = 50,    # 토큰 오버랩
        split_by: str = 'sentence',  # sentence | paragraph
    ):
        self.tokenizer = tokenizer
        self.kiwi = tokenizer.kiwi
        self.chunk_size = chunk_size
        self.overlap_tokens = overlap_tokens
        self.split_by = split_by

    def _split_sentences(self, text: str) -> list[str]:
        """Kiwi의 문장 분리 사용."""
        return [sent.text for sent in self.kiwi.split_into_sents(text)]

    def chunk(self, document: str) -> list[str]:
        """의미 단위로 문서 청킹."""
        sentences = self._split_sentences(document)

        chunks = []
        current_chunk = []
        current_token_count = 0

        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.tokenize(sentence))

            if current_token_count + sentence_tokens <= self.chunk_size:
                current_chunk.append(sentence)
                current_token_count += sentence_tokens
            else:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append(' '.join(current_chunk))

                # 오버랩 처리
                overlap_sents = self._get_overlap_sentences(
                    current_chunk, self.overlap_tokens
                )
                current_chunk = overlap_sents + [sentence]
                current_token_count = sum(
                    len(self.tokenizer.tokenize(s)) for s in current_chunk
                )

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks
```

#### Korean BM25 Retriever

```python
class KoreanBM25Retriever:
    """형태소 분석 기반 BM25 검색.

    한국어 텍스트에 최적화된 BM25 검색을 제공합니다.
    """

    def __init__(self, tokenizer: KiwiTokenizer):
        self.tokenizer = tokenizer
        self.bm25 = None
        self.documents = []

    def index(self, documents: list[str]) -> None:
        """문서 인덱싱."""
        from rank_bm25 import BM25Okapi

        self.documents = documents
        tokenized_docs = [
            self.tokenizer.tokenize(doc) for doc in documents
        ]
        self.bm25 = BM25Okapi(tokenized_docs)

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """쿼리로 검색."""
        tokenized_query = self.tokenizer.tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        # 상위 k개 반환
        top_indices = scores.argsort()[::-1][:top_k]
        return [
            (self.documents[i], scores[i])
            for i in top_indices
        ]
```

---

### Phase 9.4: Korean RAG Evaluation (Week 3)

> **목표**: 한국어 특성을 반영한 평가 메트릭 개선

#### 한국어 Faithfulness 개선

```python
class KoreanFaithfulnessChecker:
    """한국어 Faithfulness 검증.

    한국어의 교착어 특성을 고려하여 faithfulness를 검증합니다.
    - 조사 변형 무시 (보험료가/보험료를/보험료는 → 보험료)
    - 어미 변형 무시 (지급됩니다/지급되며/지급하고 → 지급)
    - 동의어/유의어 처리
    """

    def __init__(self, tokenizer: KiwiTokenizer):
        self.tokenizer = tokenizer

    def extract_claims(self, text: str) -> list[str]:
        """답변에서 주장(claim) 추출.

        형태소 분석으로 핵심 명사구/동사구 추출.
        """
        claims = []
        # Kiwi의 명사구 추출 활용
        for sent in self.tokenizer.kiwi.split_into_sents(text):
            nouns = self.tokenizer.extract_nouns(sent.text)
            if nouns:
                claims.append(' '.join(nouns))
        return claims

    def verify_against_context(
        self,
        claims: list[str],
        context: str
    ) -> list[tuple[str, bool, float]]:
        """컨텍스트 대비 주장 검증."""
        context_tokens = set(self.tokenizer.tokenize(context))

        results = []
        for claim in claims:
            claim_tokens = set(self.tokenizer.tokenize(claim))

            # 토큰 겹침 계산
            overlap = len(claim_tokens & context_tokens)
            coverage = overlap / len(claim_tokens) if claim_tokens else 0

            is_faithful = coverage >= 0.5  # 50% 이상 겹침
            results.append((claim, is_faithful, coverage))

        return results
```

#### 한국어 Semantic Similarity 개선

```python
class KoreanSemanticSimilarity:
    """한국어 의미 유사도 계산.

    형태소 기반 전처리 + 임베딩으로 유사도 계산.
    """

    def __init__(
        self,
        tokenizer: KiwiTokenizer,
        embedding_model: str = 'text-embedding-3-small'
    ):
        self.tokenizer = tokenizer
        self.embedding_model = embedding_model

    def preprocess(self, text: str) -> str:
        """형태소 분석으로 전처리.

        조사/어미 제거하여 핵심 의미만 추출.
        """
        tokens = self.tokenizer.extract_keywords(text)
        return ' '.join(tokens)

    def calculate_similarity(
        self,
        text1: str,
        text2: str,
        use_preprocessing: bool = True
    ) -> float:
        """두 텍스트의 의미 유사도 계산."""
        if use_preprocessing:
            text1 = self.preprocess(text1)
            text2 = self.preprocess(text2)

        # 임베딩 계산 및 코사인 유사도
        # (실제 구현에서는 LLMPort 활용)
        ...
```

---

### Phase 9.5: Benchmarks & Guidelines (Week 3-4)

> **목표**: 한국어 RAG 최적화 효과 측정 및 가이드 문서화

#### 벤치마크 데이터셋

```
examples/benchmarks/korean_rag/
├── insurance_qa_100.json     # 보험 QA 100개
├── retrieval_test.json       # 검색 성능 테스트
├── chunking_test.json        # 청킹 품질 테스트
└── faithfulness_test.json    # Faithfulness 테스트
```

#### 성능 비교 메트릭

| 항목 | Before (공백 기반) | After (형태소 기반) | 개선율 |
|------|-------------------|-------------------|-------|
| 키워드 정확도 | 측정 예정 | 측정 예정 | - |
| 검색 Recall@5 | 측정 예정 | 측정 예정 | - |
| Faithfulness | 측정 예정 | 측정 예정 | - |
| 처리 속도 | baseline | 측정 예정 | - |

#### 가이드 문서

```markdown
# 한국어 RAG 최적화 가이드

## 1. 형태소 분석 활용
- Kiwi 토크나이저 설정 방법
- 사용자 사전 추가 (보험 용어)

## 2. 청킹 전략
- 토큰 기반 vs 문자 기반
- 오버랩 설정 권장값

## 3. 검색 최적화
- BM25 vs Dense Retrieval
- 하이브리드 검색 설정

## 4. 평가 시 주의사항
- 조사/어미 변형 처리
- 동의어 처리
```

---

## 의존성 추가

```toml
# pyproject.toml
[project.optional-dependencies]
korean = [
    # 형태소 분석
    "kiwipiepy>=0.18.0",              # 한국어 형태소 분석 (Pure Python)

    # 임베딩 & 검색
    "FlagEmbedding>=1.2.0",           # BGE-M3 모델 (Dense+Sparse+ColBERT)
    "rank-bm25>=0.2.2",               # BM25 검색

    # Hugging Face
    "transformers>=4.40.0",           # 모델 로딩
    "sentence-transformers>=2.7.0",   # 임베딩 유틸리티
]

korean-full = [
    # korean + 추가 모델
    "evalvault[korean]",
    "torch>=2.0.0",                   # GPU 가속
    "faiss-cpu>=1.7.4",               # 벡터 검색 (CPU)
    # "faiss-gpu>=1.7.4",             # GPU 버전 (선택)
]
```

### 설치 방법

```bash
# 기본 한국어 지원
uv add evalvault[korean]

# 전체 한국어 기능 (GPU 포함)
uv add evalvault[korean-full]

# 또는 개별 설치
uv add kiwipiepy FlagEmbedding rank-bm25
```

### 모델 다운로드

```python
# 첫 사용 시 자동 다운로드 (~2GB)
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel(
    'upskyy/bge-m3-korean',
    use_fp16=True,  # GPU 메모리 절약
    device='cuda'   # 또는 'cpu'
)
```

---

## 타임라인

| Week | Phase | 주요 작업 |
|------|-------|----------|
| 1 | 9.1 | Kiwi 통합, KiwiTokenizer 구현 |
| 1-2 | 9.2 | 키워드 추출 개선, NLP 어댑터 수정 |
| 2 | 9.3 | 한국어 청킹, BM25 검색 |
| 3 | 9.4 | 한국어 평가 메트릭 |
| 3-4 | 9.5 | 벤치마크, 가이드 문서화 |

---

## 성공 지표

| 지표 | 현재 | 목표 |
|------|------|------|
| 키워드 추출 정확도 | ~60% (추정) | 85%+ |
| 검색 Recall@5 | 측정 필요 | +15% 개선 |
| Faithfulness 정확도 | 측정 필요 | +10% 개선 |
| 사용자 설정 용이성 | 수동 | CLI 자동화 |

---

## 참고 자료

- [Kiwi 공식 문서](https://github.com/bab2min/kiwipiepy)
- [한국어 형태소 분석기 비교](https://konlpy.org/ko/latest/morph/)
- [BM25 알고리즘](https://en.wikipedia.org/wiki/Okapi_BM25)
