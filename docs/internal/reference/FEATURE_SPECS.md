# EvalVault 기능 상세 스펙

> **Last Updated**: 2026-01-07
> **Status**: 기술 참조 문서

이 문서는 EvalVault의 주요 기능에 대한 상세 기술 스펙을 정리합니다.

## 관련 문서

| 문서 | 역할 |
|------|------|
| [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) | 개발 환경, 아키텍처 감사, 성능 최적화, RAG 단계별 평가 설계 |
| [PROJECT_MAP.md](./PROJECT_MAP.md) | 프로젝트 구조, 클래스 맵, Mermaid 데이터 흐름도 |
| [ARCHITECTURE_C4.md](./ARCHITECTURE_C4.md) | C4 Model 기반 아키텍처 다이어그램 |
| [CLASS_CATALOG.md](./CLASS_CATALOG.md) | 전체 클래스 카탈로그 |

---

## 목차

1. [한국어 RAG 최적화](#1-한국어-rag-최적화)
2. [DAG Analysis Pipeline](#2-dag-analysis-pipeline)
3. [임베딩 모델 통합](#3-임베딩-모델-통합)
4. [Phoenix Observability](#4-phoenix-observability)
5. [Domain Memory System](#5-domain-memory-system)

---

## 1. 한국어 RAG 최적화

### 1.1 기술 스택

| 구성요소 | 선택 | 이유 |
|----------|------|------|
| 형태소 분석 | Kiwi (kiwipiepy) | Pure Python, pip 설치, 97%+ 정확도 |
| BM25 검색 | rank-bm25 | 가벼운 키워드 검색 |
| Dense Embedding | dragonkue/BGE-m3-ko | AutoRAG Top-k 1위 (0.7456) |
| Hybrid | RRF (Reciprocal Rank Fusion) | BM25 + Dense 장점 통합 |

### 1.2 구현 클래스

```
src/evalvault/adapters/outbound/nlp/korean/
├── kiwi_tokenizer.py         # 형태소 분석기
├── korean_stopwords.py       # 불용어 사전
├── korean_bm25_retriever.py  # BM25 검색
├── korean_dense_retriever.py # Dense 검색
├── korean_hybrid_retriever.py # 하이브리드 검색
└── korean_faithfulness.py    # Faithfulness 검증
```

### 1.3 KiwiTokenizer API

```python
class KiwiTokenizer:
    def __init__(
        self,
        remove_particles: bool = True,   # 조사 제거
        remove_endings: bool = True,     # 어미 제거
        use_lemma: bool = True,          # 원형 사용
        user_dict_path: str | None = None,
    ): ...

    def tokenize(self, text: str) -> list[str]: ...
    def extract_nouns(self, text: str) -> list[str]: ...
    def extract_keywords(
        self, text: str,
        pos_tags: list[str] = ['NNG', 'NNP', 'VV', 'VA']
    ) -> list[str]: ...
```

### 1.4 성능 지표

| 지표 | Before | After | 개선 |
|------|--------|-------|------|
| 키워드 추출 정확도 | ~60% | 85%+ | +25% |
| 검색 Recall@5 | Baseline | +15-20% | - |
| Faithfulness 정확도 | Baseline | +10-25% | - |

### 1.5 통합 포인트

1. **테스트셋 생성**: `KoreanDocumentChunker` → 의미 단위 청킹
2. **NLP Analysis**: `NLPAnalysisAdapter` → 형태소 기반 키워드 추출
3. **KG 생성**: `EntityExtractor` → 형태소 기반 엔티티 추출
4. **Domain Memory**: 사실 정규화 (조사/어미 제거)

---

## 2. DAG Analysis Pipeline

### 2.1 아키텍처

```
User Query → Intent Classifier → Pipeline Builder → Executor → Report
                    ↓                    ↓
            Intent Keywords       Template Registry
```

### 2.2 분석 의도 (12가지)

```python
class AnalysisIntent(StrEnum):
    # 검증 (Verification)
    VERIFY_MORPHEME = "verify_morpheme"
    VERIFY_EMBEDDING = "verify_embedding"
    VERIFY_RETRIEVAL = "verify_retrieval"

    # 비교 (Comparison)
    COMPARE_SEARCH_METHODS = "compare_search"
    COMPARE_MODELS = "compare_models"
    COMPARE_RUNS = "compare_runs"

    # 분석 (Analysis)
    ANALYZE_LOW_METRICS = "analyze_low_metrics"
    ANALYZE_PATTERNS = "analyze_patterns"
    ANALYZE_TRENDS = "analyze_trends"

    # 보고서 (Report)
    GENERATE_SUMMARY = "generate_summary"
    GENERATE_DETAILED = "generate_detailed"
    GENERATE_COMPARISON = "generate_comparison"
```

### 2.3 분석 모듈 카탈로그

| 모듈 ID | 설명 | 의존성 |
|---------|------|--------|
| `data_loader` | StoragePort로 데이터 로드 | storage |
| `statistical_analyzer` | 통계 분석 | data_loader |
| `morpheme` | 형태소 분석 | korean extra |
| `bm25` | BM25 검색 | korean extra |
| `hybrid_rrf` | RRF 하이브리드 | morpheme, bm25 |
| `diagnostic` | 진단 플레이북 | ragas_eval |
| `causal` | 인과 분석 | ragas_eval |
| `report` | 보고서 생성 | * |

### 2.4 파이프라인 예시

**쿼리**: "형태소 분석이 제대로 되고 있는지 확인"

```yaml
intent: VERIFY_MORPHEME
pipeline:
  nodes:
    - id: data_loader
      module: data_loader
    - id: morpheme_analysis
      module: morpheme
      depends_on: [data_loader]
    - id: quality_check
      module: morpheme_quality_checker
      depends_on: [morpheme_analysis]
    - id: report
      module: verification_report
      depends_on: [quality_check]
```

### 2.5 CLI 사용

```bash
evalvault pipeline analyze "요약해줘" --profile dev

# 템플릿 조회
python scripts/pipeline_template_inspect.py --intent analyze_low_metrics
```

---

## 3. 임베딩 모델 통합

### 3.1 지원 모델

| 모델 | 차원 | Matryoshka | 환경 |
|------|------|------------|------|
| dragonkue/BGE-m3-ko | 1024 (고정) | ❌ | 운영 (최고 성능) |
| qwen3-embedding:0.6b | 32-768 | ✅ | 개발 (경량) |
| qwen3-embedding:8b | 32-4096 | ✅ | 운영 (폐쇄망) |

### 3.2 Matryoshka 차원 가이드

| 차원 | 정확도 | 속도 | 권장 환경 |
|------|--------|------|----------|
| 128 | 보통 | 빠름 | 개발 |
| 256 | 좋음 | 보통 | **개발 (권장)** |
| 512 | 매우 좋음 | 보통 | 중간 |
| 1024 | 우수 | 느림 | **운영 (권장)** |
| 2048+ | 최고 | 매우 느림 | 고정밀 |

### 3.3 프로필 설정

```yaml
# config/models.yaml
profiles:
  dev:
    embedding:
      provider: ollama
      model: qwen3-embedding:0.6b
      matryoshka_dim: 256

  prod:
    embedding:
      provider: ollama
      model: qwen3-embedding:8b
      matryoshka_dim: 1024
```

### 3.4 KoreanDenseRetriever API

```python
class KoreanDenseRetriever:
    SUPPORTED_MODELS = {
        "dragonkue/BGE-m3-ko": {"dimension": 1024, "matryoshka": False},
        "qwen3-embedding:0.6b": {"dimension": 768, "matryoshka": True},
        "qwen3-embedding:8b": {"dimension": 4096, "matryoshka": True},
    }

    def __init__(
        self,
        model_name: str | None = None,  # None이면 프로필에서 자동 선택
        matryoshka_dim: int | None = None,
    ): ...

    def encode(
        self,
        texts: list[str],
        dimension: int | None = None,  # Matryoshka 차원 오버라이드
    ) -> np.ndarray: ...
```

---

## 4. Phoenix Observability

### 4.1 아키텍처

```
EvalVault
    └─> OpenTelemetry Instrumentation
            └─> OTLP
                    ├─> Phoenix (주 추적)
                    └─> LangFuse (프롬프트 관리, 선택)
```

### 4.2 데이터 엔티티

```python
@dataclass
class RetrievalData:
    retrieval_method: str      # "bm25", "dense", "hybrid"
    embedding_model: str | None
    top_k: int
    retrieval_time_ms: float
    candidates: list[RetrievedDocument]

@dataclass
class GenerationData:
    prompt_data: PromptData
    metadata: GenerationMetadata

@dataclass
class LatencyBreakdown:
    total_time_ms: float
    query_processing_ms: float
    retrieval_ms: float
    reranking_ms: float | None
    generation_ms: float
```

### 4.3 CLI 옵션

```bash
evalvault run data.json \
  --tracker phoenix \
  --phoenix-dataset insurance-qa \
  --phoenix-experiment baseline-v1 \
  --phoenix-max-traces 100
```

### 4.4 Prompt Manifest Loop

1. **Manifest에 Prompt ID 기록**:
   ```bash
   evalvault phoenix prompt-link agent/prompts/baseline.txt \
     --prompt-id pr-428 --experiment-id exp-20250115
   ```

2. **Diff 확인**:
   ```bash
   evalvault phoenix prompt-diff \
     agent/prompts/baseline.txt agent/prompts/system.txt
   ```

3. **평가 시 주입**:
   ```bash
   evalvault run data.json \
     --prompt-files agent/prompts/baseline.txt \
     --prompt-manifest agent/prompts/prompt_manifest.json
   ```

### 4.5 Drift Watcher

```bash
uv run python scripts/ops/phoenix_watch.py \
  --endpoint http://localhost:6006 \
  --dataset-id ds_12345 \
  --interval 120 \
  --drift-threshold 0.2 \
  --slack-webhook https://hooks.slack.com/... \
  --gate-command "evalvault gate ..."
```

---

## 5. Domain Memory System

### 5.1 3계층 구조

| 계층 | 용도 | 저장소 |
|------|------|--------|
| **Factual** | 검증된 정적 사실 | SQLite FTS5 |
| **Experiential** | 학습된 패턴 | SQLite |
| **Working** | 세션 컨텍스트 | 메모리 |

### 5.2 핵심 클래스

```python
# 저장 (Formation)
class DomainLearningHook:
    async def on_evaluation_complete(
        self, run: EvaluationRun, domain: str, language: str
    ) -> LearningMemory: ...

    def run_evolution(self, domain: str) -> dict: ...
        # consolidate_facts, forget_obsolete, decay_verification_scores

# 검색 (Retrieval)
class SQLiteDomainMemoryAdapter:
    def search_facts(self, query: str, domain: str, limit: int) -> list[FactualFact]: ...
    def search_behaviors(self, context: str, domain: str) -> list[BehaviorEntry]: ...
    def hybrid_search(self, query: str, domain: str) -> dict: ...

# 활용 (Usage)
class MemoryAwareEvaluator:
    async def evaluate_with_memory(
        self, dataset: Dataset, metrics: list[str], domain: str
    ) -> EvaluationRun: ...
    # reliability 기반 threshold 자동 조정

    def augment_context_with_facts(
        self, question: str, original_context: str, domain: str
    ) -> str: ...
    # 관련 사실을 컨텍스트에 추가

class MemoryBasedAnalysis:
    def generate_insights(
        self, evaluation_run: EvaluationRun, domain: str
    ) -> dict: ...
    # trends, related_facts, recommendations

    def apply_successful_behaviors(
        self, test_case: TestCase, domain: str
    ) -> list[str]: ...
```

### 5.3 CLI 명령어

```bash
# 평가 시 Domain Memory 활용
evalvault run dataset.json \
  --use-domain-memory \
  --memory-domain insurance \
  --augment-context

# 메모리 조회
evalvault domain memory stats --domain insurance
evalvault domain memory search "청약 철회" --domain insurance
evalvault domain memory behaviors --min-success 0.8
evalvault domain memory learnings --limit 10

# Evolution 실행
evalvault domain memory evolve --domain insurance --yes
```

### 5.4 효과

| 기능 | 효과 |
|------|------|
| Threshold 자동 조정 | 튜닝 시간 30분 → 5분 |
| 컨텍스트 보강 | Faithfulness +0.03 |
| 트렌드 분석 | 분석 대기 시간 1시간 절감 |

---

## 부록: 데이터 스키마

### A. RetrievedDocument

```python
@dataclass
class RetrievedDocument:
    content: str
    score: float
    rank: int
    source: str
    metadata: dict[str, Any]
    rerank_score: float | None = None
    rerank_rank: int | None = None
```

### B. FactualFact

```python
@dataclass
class FactualFact:
    fact_id: str
    subject: str
    predicate: str
    object: str
    domain: str
    language: str
    verification_score: float
    verified_count: int
    created_at: datetime
    updated_at: datetime
```

### C. BenchmarkResult

```python
@dataclass
class BenchmarkResult:
    suite_name: str
    results: dict[str, dict]  # retriever_name -> metrics
    timestamp: datetime

    def to_mteb_format(self) -> dict: ...
    def to_leaderboard(self) -> list[dict]: ...
```

---

**문서 끝**
