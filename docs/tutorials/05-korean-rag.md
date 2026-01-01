# 한국어 RAG 최적화 가이드

> 한국어 RAG 시스템의 평가 품질을 높이는 최적화 기법을 배웁니다.

---

## 목차

1. [한국어 RAG의 특수성](#한국어-rag의-특수성)
2. [한국어 토크나이저 설정](#한국어-토크나이저-설정)
3. [BM25/Dense/Hybrid 검색 설정](#bm25densehybrid-검색-설정)
4. [성능 최적화 팁](#성능-최적화-팁)
5. [벤치마크 실행](#벤치마크-실행)

---

## 한국어 RAG의 특수성

### 왜 한국어 최적화가 필요한가?

한국어는 **교착어**로, 영어와 다른 언어적 특성을 가집니다.

| 특성 | 영어 | 한국어 |
|------|------|--------|
| 어순 | SVO (주어-동사-목적어) | SOV (주어-목적어-동사) |
| 조사 | 별도 단어 (전치사) | 단어에 붙음 (후치사) |
| 어미 변형 | 제한적 | 다양함 |
| 공백 | 단어 구분 | 어절 구분 |

### 문제 예시

```
질문: "보험료가 얼마인가요?"
컨텍스트: "보험료는 월 10만원입니다."

# 공백 기반 토큰화
질문 토큰: ["보험료가", "얼마인가요?"]
컨텍스트 토큰: ["보험료는", "월", "10만원입니다."]
→ "보험료가" != "보험료는" (매칭 실패)

# 형태소 분석 기반 토큰화
질문 토큰: ["보험료", "얼마"]
컨텍스트 토큰: ["보험료", "월", "10만원"]
→ "보험료" == "보험료" (매칭 성공)
```

### EvalVault 한국어 기능

EvalVault는 다음 한국어 최적화 기능을 제공합니다:

| 기능 | 설명 |
|------|------|
| KiwiTokenizer | Kiwi 기반 형태소 분석 |
| KoreanBM25Retriever | 형태소 분석 기반 BM25 검색 |
| KoreanDenseRetriever | BGE-m3-ko 임베딩 기반 검색 |
| KoreanHybridRetriever | BM25 + Dense 하이브리드 검색 |
| KoreanDocumentChunker | 의미 단위 문서 청킹 |

---

## 한국어 토크나이저 설정

### Step 1: 의존성 설치

```bash
# 한국어 NLP 기능 설치
uv sync --extra korean
```

또는:

```bash
pip install kiwipiepy rank-bm25
```

### Step 2: KiwiTokenizer 사용

```python
from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer

# 토크나이저 초기화
tokenizer = KiwiTokenizer(
    remove_particles=True,   # 조사 제거 (가, 이, 은, 는, ...)
    remove_endings=True,     # 어미 제거 (했다, 합니다, ...)
    use_lemma=True,          # 원형 사용 (했다 → 하다)
)

# 토큰화
text = "보험료가 얼마인가요?"
tokens = tokenizer.tokenize(text)
print(tokens)  # ['보험료', '얼마']
```

### 옵션 설명

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `remove_particles` | `True` | 조사 제거 (가, 이, 은, 는, 를, 을) |
| `remove_endings` | `True` | 어미 제거 (다, 니다, 요, 습니다) |
| `use_lemma` | `True` | 원형 사용 (했다 → 하다) |
| `user_dict_path` | `None` | 사용자 사전 경로 |

### 사용자 사전 추가

보험, 의료 등 도메인 특화 용어를 추가할 수 있습니다.

```python
# 사용자 사전 파일: user_dict.txt
# 형식: 단어 \t 품사 \t 점수
보장금액	NNG	10
실손보험	NNG	10
해지환급금	NNG	10

# 토크나이저에 사전 적용
tokenizer = KiwiTokenizer(user_dict_path="user_dict.txt")
```

### 명사 추출

```python
# 명사만 추출
text = "이 보험의 보장금액은 1억원입니다."
nouns = tokenizer.extract_nouns(text)
print(nouns)  # ['보험', '보장금액', '1억원']
```

### 키워드 추출

```python
# 명사, 동사, 형용사 추출
text = "보험료가 비싸서 해지했습니다."
keywords = tokenizer.extract_keywords(text, pos_tags=['NNG', 'NNP', 'VV', 'VA'])
print(keywords)  # ['보험료', '비싸다', '해지하다']
```

---

## BM25/Dense/Hybrid 검색 설정

### BM25 검색 (형태소 분석 기반)

```python
from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer, KoreanBM25Retriever

# 초기화
tokenizer = KiwiTokenizer()
retriever = KoreanBM25Retriever(tokenizer)

# 문서 인덱싱
documents = [
    "이 보험의 사망 보장금액은 1억원입니다.",
    "보험료 납입기간은 20년입니다.",
    "해지환급금은 납입 보험료의 80%입니다.",
]
retriever.index(documents)

# 검색
query = "보장금액이 얼마인가요?"
results = retriever.search(query, top_k=2)

for doc, score in results:
    print(f"[{score:.3f}] {doc}")
# [0.982] 이 보험의 사망 보장금액은 1억원입니다.
# [0.124] 해지환급금은 납입 보험료의 80%입니다.
```

### Dense 검색 (임베딩 기반)

```python
from evalvault.adapters.outbound.nlp.korean import KoreanDenseRetriever

# BGE-m3-ko 모델 사용 (권장)
retriever = KoreanDenseRetriever(model_name="dragonkue/BGE-m3-ko")

# 문서 인덱싱
documents = [
    "이 보험의 사망 보장금액은 1억원입니다.",
    "보험료 납입기간은 20년입니다.",
    "해지환급금은 납입 보험료의 80%입니다.",
]
retriever.index(documents)

# 검색
query = "보장금액이 얼마인가요?"
results = retriever.search(query, top_k=2)

for doc, score in results:
    print(f"[{score:.3f}] {doc}")
```

### Hybrid 검색 (BM25 + Dense)

```python
from evalvault.adapters.outbound.nlp.korean import (
    KiwiTokenizer,
    KoreanHybridRetriever,
)

# 초기화
tokenizer = KiwiTokenizer()
retriever = KoreanHybridRetriever(
    tokenizer=tokenizer,
    dense_model="dragonkue/BGE-m3-ko",
    bm25_weight=0.4,   # BM25 가중치
    dense_weight=0.6,  # Dense 가중치
)

# 문서 인덱싱
retriever.index(documents)

# 검색
results = retriever.search(query, top_k=3)
```

### 검색 방식 비교

| 방식 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| BM25 | 정확한 키워드 매칭 | 동의어 처리 약함 | 보험 용어 검색 |
| Dense | 의미적 유사도 | 키워드 매칭 약함 | 일반 질문 |
| Hybrid | 두 장점 결합 | 설정 복잡 | 프로덕션 환경 |

---

## 성능 최적화 팁

### 1. 문서 청킹 최적화

한국어 문서는 문장 경계를 존중하는 청킹이 중요합니다.

```python
from evalvault.adapters.outbound.nlp.korean import KoreanDocumentChunker

tokenizer = KiwiTokenizer()
chunker = KoreanDocumentChunker(
    tokenizer=tokenizer,
    chunk_size=500,       # 토큰 수 기준
    overlap_tokens=50,    # 토큰 오버랩
    split_by='sentence',  # sentence | paragraph
)

# 문서 청킹
document = """
이 보험은 피보험자가 보험기간 중 사망한 경우 사망보험금을 지급합니다.
보장금액은 가입금액의 100%입니다.
보험료 납입기간은 10년, 15년, 20년 중 선택 가능합니다.
해지환급금은 납입한 보험료에서 경과기간에 따른 해지공제액을 차감한 금액입니다.
"""

chunks = chunker.chunk(document)
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1}: {chunk[:50]}...")
```

### 2. 임베딩 모델 선택

| 모델 | 차원 | Max Tokens | 성능 | 권장 |
|------|------|------------|------|------|
| dragonkue/BGE-m3-ko | 1024 | 8192 | 최고 | 프로덕션 |
| upskyy/bge-m3-korean | 1024 | 8192 | 좋음 | 대안 |
| BAAI/bge-m3 | 1024 | 8192 | 좋음 | 다국어 |
| jhgan/ko-sroberta-multitask | 768 | 512 | 보통 | 경량 |

```python
# 최적 모델 사용
retriever = KoreanDenseRetriever(model_name="dragonkue/BGE-m3-ko")
```

### 3. 캐싱 활용

```python
from functools import lru_cache

# 토큰화 결과 캐싱
@lru_cache(maxsize=10000)
def cached_tokenize(text: str) -> tuple[str, ...]:
    return tuple(tokenizer.tokenize(text))

# 임베딩 결과 캐싱
@lru_cache(maxsize=1000)
def cached_embed(text: str) -> tuple[float, ...]:
    embedding = retriever.embed(text)
    return tuple(embedding.tolist())
```

### 4. 배치 처리

```python
# 대량 문서 처리 시 배치 사용
documents = [...]  # 1000개 문서

# 배치 임베딩
embeddings = retriever.embed_batch(documents, batch_size=32)
```

### 5. 불용어 커스터마이징

```python
from evalvault.adapters.outbound.nlp.korean import KOREAN_STOPWORDS

# 기본 불용어 확인
print(KOREAN_STOPWORDS[:10])
# ['이', '그', '저', '것', '수', '등', '더', '또', '또한', '및']

# 커스텀 불용어 추가
custom_stopwords = KOREAN_STOPWORDS + ['보험', '계약']
tokenizer = KiwiTokenizer(stopwords=custom_stopwords)
```

---

## 벤치마크 실행

### 벤치마크 데이터셋

EvalVault에 포함된 한국어 RAG 벤치마크:

```
examples/benchmarks/korean_rag/
├── insurance_qa_100.json      # 보험 QA 100개
├── faithfulness_test.json     # Faithfulness 테스트
├── keyword_extraction_test.json  # 키워드 추출 테스트
└── retrieval_test.json        # 검색 품질 테스트
```

### CLI로 벤치마크 실행

```bash
# 한국어 보험 QA 벤치마크
uv run evalvault benchmark korean-insurance --metrics faithfulness,context_precision

# 형태소 분석 vs 공백 기반 비교
uv run evalvault benchmark korean-insurance --compare-tokenizer
```

### Python으로 벤치마크 실행

```python
from evalvault.domain.services.benchmark_runner import KoreanRAGBenchmarkRunner

# 벤치마크 러너 초기화
runner = KoreanRAGBenchmarkRunner()

# 벤치마크 실행
results = runner.run(
    dataset_path="examples/benchmarks/korean_rag/insurance_qa_100.json",
    metrics=["faithfulness", "context_precision"],
)

# 결과 출력
print(f"평균 Faithfulness: {results['faithfulness']:.3f}")
print(f"평균 Context Precision: {results['context_precision']:.3f}")

# 결과 저장 (MTEB 형식)
runner.save_results(results, format="mteb", output_path="results.json")
```

### 벤치마크 결과 비교

```python
# 형태소 분석 vs 공백 기반 비교
baseline = runner.run(
    dataset_path="...",
    tokenizer="whitespace",
)

optimized = runner.run(
    dataset_path="...",
    tokenizer="kiwi",
)

print(f"공백 기반 Faithfulness: {baseline['faithfulness']:.3f}")
print(f"형태소 기반 Faithfulness: {optimized['faithfulness']:.3f}")
print(f"개선율: {(optimized['faithfulness'] - baseline['faithfulness']) / baseline['faithfulness'] * 100:.1f}%")
```

### 예상 개선 효과

| 메트릭 | 공백 기반 | 형태소 기반 | 개선율 |
|--------|-----------|-------------|--------|
| 키워드 정확도 | 60% | 85%+ | +42% |
| 검색 정밀도 | 70% | 85%+ | +21% |
| Faithfulness | 75% | 88%+ | +17% |

---

## 문제 해결

### Kiwi 설치 오류

```
Error: No module named 'kiwipiepy'
```

**해결**:
```bash
uv sync --extra korean
# 또는
pip install kiwipiepy
```

### 메모리 부족

대량 문서 처리 시 메모리 부족:

```python
# 스트리밍 처리
for batch in chunked(documents, batch_size=100):
    embeddings = retriever.embed_batch(batch)
    # 처리 후 메모리 해제
    del embeddings
    gc.collect()
```

### 느린 토큰화

```python
# 멀티프로세싱 활용
from multiprocessing import Pool

def tokenize_batch(texts):
    tokenizer = KiwiTokenizer()  # 프로세스별 인스턴스
    return [tokenizer.tokenize(t) for t in texts]

with Pool(4) as p:
    results = p.map(tokenize_batch, chunked(texts, 1000))
```

---

## 다음 단계

| 주제 | 튜토리얼 |
|------|----------|
| 프로덕션 배포 가이드 | [06-production-tips.md](06-production-tips.md) |

---

<div align="center">

[이전: Phoenix 통합](04-phoenix-integration.md) | [다음: 프로덕션 가이드](06-production-tips.md)

</div>
