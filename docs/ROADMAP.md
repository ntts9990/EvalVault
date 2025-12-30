# EvalVault Development Roadmap

> Last Updated: 2025-12-30
> Current Version: 1.3.0
> Status: Phase 9 Korean RAG Optimization Complete ✅

---

## Overview

EvalVault의 개발 로드맵입니다. Phase 1-7 Core System, Analysis 기능(Phase 2 NLP, Phase 3 Causal), Domain Memory Layering(Phase 8), 그리고 Korean RAG Optimization(Phase 9)이 완료되었습니다.

### Progress Summary

| Phase | Description | Status | Tests |
|-------|-------------|--------|-------|
| Phase 1-3 | Core System | ✅ Complete | 118 |
| Phase 4 | Foundation Enhancement | ✅ Complete | +60 |
| Phase 5 | Storage & Domain | ✅ Complete | +42 |
| Phase 6 | Advanced Features | ✅ Complete | +160 |
| Phase 7 | Production Ready | ✅ Complete | +10 |
| **Phase 2 NLP** | NLP Analysis | ✅ Complete | +97 |
| **Phase 3 Causal** | Causal Analysis | ✅ Complete | +27 |
| **Phase 8** | Domain Memory Layering | ✅ Complete | +113 |
| **Phase 9** | Korean RAG Optimization | ✅ Complete (9.1-9.5) | +24 |
| **Total** | | | **915** |

### Test Coverage Summary

> **Status Update (2025-12-28)**: 테스트 커버리지 개선 계획 완료
> - 전체 커버리지: 53% → **89%** 달성
> - CLI 커버리지: 46% → **89%** (목표 80% 초과 달성)
> - 총 테스트 수: **457개** (Unit 431 + Integration 26)

---

## Phase 2: NLP Analysis ✅

> **Status**: Complete (2025-12-29)
> **Tests**: +97

평가 결과에 대한 자연어 처리 분석 기능입니다.

### 구현된 기능

| Sub-Phase | Description | Status |
|-----------|-------------|--------|
| Phase 2.3 | NLP Adapter (Hybrid: Rule + ML + LLM) | ✅ Complete |
| Phase 2.4 | AnalysisService Integration | ✅ Complete |
| Phase 2.5 | CLI Integration (`--nlp`, `--profile`) | ✅ Complete |
| Phase 2.6 | Database Storage for NLP Analysis | ✅ Complete |
| Phase 2.7 | Topic Clustering (K-Means + Embeddings) | ✅ Complete |
| Phase 2.8 | Report Generation (Markdown/HTML) | ✅ Complete |

### 주요 파일

```
src/evalvault/
├── adapters/outbound/analysis/
│   └── nlp_adapter.py          # NLP 분석 어댑터
├── adapters/outbound/report/
│   └── markdown_adapter.py     # Markdown/HTML 보고서 생성
├── ports/outbound/
│   ├── nlp_analysis_port.py    # NLP 분석 포트
│   └── report_port.py          # 보고서 생성 포트
└── domain/entities/
    └── analysis.py             # NLPAnalysis, TextStats, TopicCluster 등
```

### CLI 사용법

```bash
# NLP 분석 실행
evalvault analyze <run_id> --nlp --profile dev

# 보고서 생성
evalvault analyze <run_id> --nlp --report report.md
evalvault analyze <run_id> --nlp --report report.html
```

---

## Phase 3: Causal Analysis ✅

> **Status**: Complete (2025-12-29)
> **Tests**: +27

평가 결과에서 인과 관계를 분석하여 근본 원인을 파악하고 개선 제안을 생성합니다.

### 구현된 기능

| Feature | Description |
|---------|-------------|
| Factor Extraction | 질문 길이, 컨텍스트 수, 키워드 겹침 등 인과 요인 추출 |
| Factor-Metric Impact | 각 요인이 메트릭에 미치는 영향 분석 (상관분석) |
| Causal Relationships | 유의미한 인과 관계 식별 |
| Root Cause Analysis | 메트릭별 근본 원인 분석 |
| Intervention Suggestions | 개선 제안 생성 |
| Stratified Analysis | 요인값별 계층화 분석 (low/medium/high) |

### 주요 파일

```
src/evalvault/
├── adapters/outbound/analysis/
│   └── causal_adapter.py       # 인과 분석 어댑터
├── ports/outbound/
│   └── causal_analysis_port.py # 인과 분석 포트
└── domain/entities/
    └── analysis.py             # CausalAnalysis, FactorImpact, RootCause 등
```

### CLI 사용법

```bash
# 인과 분석 실행
evalvault analyze <run_id> --causal

# NLP + 인과 분석 함께 실행
evalvault analyze <run_id> --nlp --causal --report report.html
```

### 인과 요인 (Causal Factors)

| Factor | Description |
|--------|-------------|
| `question_length` | 질문 길이 (단어 수) |
| `answer_length` | 답변 길이 (단어 수) |
| `context_count` | 컨텍스트 수 |
| `context_length` | 컨텍스트 총 길이 |
| `question_complexity` | 질문 복잡도 |
| `has_ground_truth` | ground_truth 존재 여부 |
| `keyword_overlap` | 질문-컨텍스트 키워드 겹침 |

---

## Phase 8: Domain Memory Layering ✅

> **Status**: Complete (2025-12-29)
> **Tests**: +113
> **Priority**: 🔥 High

EvalVault의 현재 아키텍처(순차적 평가 파이프라인)에 맞는 실질적인 개선 사항입니다.

### 목표

평가 결과에서 학습하여 엔티티 추출과 지식 그래프 생성의 정확도를 향상시킵니다.

**중요한 설명:**
- **Ragas 평가 자체는 매번 동일한 프롬프트를 사용합니다** (Ragas 메트릭의 고정된 프롬프트)
- **학습 피드백 루프는 평가가 아닌 다른 컴포넌트에서 작동합니다:**
  1. **KG 생성 및 테스트셋 생성**: EntityExtractor가 학습된 패턴을 사용하여 더 정확한 엔티티 추출
  2. **도메인 지식 축적**: 평가 결과에서 검증된 사실(FactualFact)을 추출하여 도메인 지식베이스 구축
  3. **패턴 학습**: 엔티티 타입별 신뢰도, 실패 패턴 등을 학습하여 다음 KG 생성에 반영

**실제 작동 방식:**
```
평가 #1: Dataset → RagasEvaluator → EvaluationRun
    └─> DomainLearningHook.on_evaluation_complete()
            ├─> 엔티티 타입별 신뢰도 계산 (예: "organization" 타입 = 0.92)
            └─> LearningMemory 저장

평가 #2 (KG 기반 테스트셋 생성 시):
    └─> KnowledgeGraphGenerator.build_graph(documents)
            └─> EntityExtractor.extract_entities()
                    └─> DomainMemoryAdapter.get_aggregated_reliability()
                            └─> 학습된 신뢰도 점수를 가중치로 적용
                                    └─> 더 정확한 엔티티 추출 → 더 나은 KG → 더 나은 테스트셋
```

### 핵심 개념

Agent Memory Survey의 Forms×Functions 가이드라인을 도입해 도메인 지식을 세 계층으로 구성합니다:

| 계층 | 목적 | 예시 |
|------|------|------|
| **Factual** | 검증된 정적 사실 | 용어 사전, 규정 문서 |
| **Experiential** | 평가에서 학습한 패턴 | 엔티티 타입별 신뢰도, 실패 패턴 |
| **Working** | 현재 실행 컨텍스트 | 세션 캐시, 활성 KG 바인딩 |

### 구현된 기능

| Sub-Phase | Description | Status | Tests |
|-----------|-------------|--------|-------|
| Phase 8.1 | Factual Memory Store | ✅ Complete | +40 |
| Phase 8.2 | Dynamics: Evolution & Retrieval | ✅ Complete | +14 |
| Phase 8.3 | Dynamics: Formation | ✅ Complete | +9 |
| Phase 8.4 | Config & Multi-language | ✅ Complete | +33 |
| Phase 8.5 | Forms: Planar/Hierarchical | ✅ Complete | +17 |
| **Total** | | | **+113** |

### 주요 파일

```
src/evalvault/
├── domain/entities/
│   └── memory.py                    # FactualFact, LearningMemory, BehaviorEntry
├── domain/services/
│   └── domain_learning_hook.py      # DomainLearningHook 서비스
├── ports/outbound/
│   ├── domain_memory_port.py        # DomainMemoryPort 인터페이스
│   └── learning_hook_port.py         # DomainLearningHookPort 인터페이스
├── adapters/outbound/domain_memory/
│   ├── sqlite_adapter.py            # SQLiteDomainMemoryAdapter
│   └── domain_memory_schema.sql     # 스키마 (FTS5 포함)
└── config/
    └── domain_config.py             # DomainMemoryConfig

config/domains/insurance/
├── memory.yaml                       # 도메인 메모리 설정
├── terms_dictionary_ko.json          # 한국어 용어사전
└── terms_dictionary_en.json          # 영어 용어사전
```

### CLI 사용법

```bash
# 도메인 초기화
evalvault domain init insurance --languages ko,en

# 도메인 목록 조회
evalvault domain list

# 도메인 설정 조회
evalvault domain show insurance

# 용어사전 조회
evalvault domain terms insurance --language ko --limit 10
```

### 구현 계획 (참고용 - 완료됨)

#### Phase 8.1: Factual Memory Store (Week 1-2) ✅

```
src/evalvault/domain/entities/memory.py
├── FactualFact (검증된 사실 엔티티)
├── LearningMemory (학습된 패턴)
└── DomainMemoryContext (워킹 메모리)

src/evalvault/ports/outbound/domain_memory_port.py
└── DomainMemoryPort (store_fact, query_facts, record_learning)

src/evalvault/adapters/outbound/domain_memory/
└── sqlite_adapter.py (SQLite 기반 메모리 저장소)
```

#### Phase 8.2: Config Extension (Week 2-3) ✅

```yaml
# config/domains/insurance/memory.yaml
factual:
  glossary: terms_dictionary.json
  regulatory_rules: rules.md
  languages: ["ko", "en"]  # 다국어 지원
experiential:
  reliability_scores: reliability.json
  failure_modes: failures.json
working:
  run_cache: ${RUN_DIR}/memory.db
  kg_binding: kg://insurance
```

**CLI 확장:**
```bash
evalvault domain init <domain>      # 도메인 설정 초기화
evalvault domain list               # 등록된 도메인 목록
evalvault run ... --memory-layer working  # 특정 계층만 로드
```

#### Phase 8.3: Learning Integration (Week 3-4) ✅

**DomainLearningHook 프로토콜** (결합도 최소화):
```python
class DomainLearningHook(Protocol):
    """평가 결과에서 학습하는 훅 인터페이스"""
    def on_evaluation_complete(self, run: EvaluationRun) -> LearningMemory:
        """평가 완료 시 패턴 학습"""
        ...

    def apply_learning(self, extractor: EntityExtractor) -> None:
        """학습된 패턴을 추출기에 적용"""
        ...
```

### 성공 지표

| 지표 | Baseline | 목표 |
|------|----------|------|
| Entity Extraction Accuracy | 현재 측정 필요 | +10% |
| 도메인 온보딩 시간 | 수동 설정 | CLI 자동화 |
| 반복 실수율 | 측정 필요 | -30% |

---

## Phase 9: Korean RAG Optimization ✅

> **Status**: Complete (9.1-9.5)
> **Priority**: ✅ Complete
> **Goal**: 한국어 RAG 시스템 성능을 실질적으로 향상시키는 도구와 가이드 제공
> **Tests**: +24

### 구현된 기능

| Sub-Phase | Description | Status |
|-----------|-------------|--------|
| Phase 9.1 | Korean NLP Foundation (KiwiTokenizer) | ✅ Complete |
| Phase 9.2 | Korean Keyword Extraction + Hybrid Search | ✅ Complete |
| Phase 9.3 | Dense Embedding (BGE-m3-ko) | ✅ Complete |
| Phase 9.4 | Korean RAG Evaluation (Faithfulness) | ✅ Complete |
| Phase 9.5 | Benchmarks & Guidelines | ✅ Complete |

### 주요 파일

```
src/evalvault/
├── adapters/outbound/nlp/
│   └── korean/
│       ├── kiwi_tokenizer.py           # Kiwi 기반 토크나이저
│       ├── korean_stopwords.py         # 한국어 불용어 사전
│       ├── korean_bm25_retriever.py    # 형태소 분석 BM25 검색
│       ├── korean_hybrid_retriever.py  # BM25 + Dense 하이브리드
│       ├── korean_dense_retriever.py   # Dense 임베딩 검색
│       └── korean_faithfulness.py      # Faithfulness 검증 도구
├── domain/entities/
│   └── benchmark.py                    # RAGTestCase, BenchmarkResult
├── domain/services/
│   └── benchmark_runner.py             # KoreanRAGBenchmarkRunner
├── ports/outbound/
│   └── korean_nlp_port.py              # 한국어 NLP 포트

examples/benchmarks/
├── run_korean_benchmark.py             # 벤치마크 실행 스크립트
├── README.md                           # 벤치마크 가이드
└── korean_rag/                         # 벤치마크 데이터셋

tests/unit/
└── test_benchmark_runner.py            # 24개 벤치마크 테스트
```

### 기술 스택

- **형태소 분석**: Kiwi (kiwipiepy) - Pure Python, 빠른 속도, 높은 정확도
- **임베딩 모델**: dragonkue/BGE-m3-ko - AutoRAG 벤치마크 1위 (+39.4% 성능 향상)
- **검색**: BM25 + Dense 하이브리드 (Reciprocal Rank Fusion)

### 통합 포인트

1. **테스트셋 생성**: KoreanDocumentChunker로 의미 단위 청킹
2. **NLP Analysis**: 형태소 분석 기반 키워드 추출 (정확도 60% → 85%+)
3. **KG 생성**: 형태소 분석 기반 엔티티 추출 (정확도 70% → 90%+)
4. **Domain Memory**: 사실 정규화로 중복 제거
5. **평가 품질**: Faithfulness 검증 보조 (+5-10% 향상)

### 예상 효과

| 기능 | 개선율 |
|------|--------|
| 테스트셋 품질 | +15-20% |
| 키워드 추출 정확도 | +25% (60% → 85%+) |
| 엔티티 추출 정확도 | +20% (70% → 90%+) |
| KG 품질 | +20-30% |
| Domain Memory 정확도 | +10-15% |

### CLI 사용법

```bash
# 한국어 최적화 옵션 사용
evalvault generate documents.md --method knowledge_graph --korean

# 한국어 토크나이저로 NLP 분석
evalvault analyze <run_id> --nlp --korean

# 한국어 청킹으로 테스트셋 생성
evalvault generate documents.md --korean-chunker
```

### 상세 문서

- `docs/PHASE9_KOREAN_RAG.md`: 전체 구현 계획 및 통합 전략

---

## Future: Agent System Integration

> **Status**: Research / Deferred
> **Prerequisite**: 멀티에이전트 아키텍처 도입

현재 EvalVault는 **순차적 평가 파이프라인**입니다. 아래 기능들은 **진정한 멀티에이전트 시스템** 도입 후에 의미가 있습니다.

### 전제 조건: Agent Architecture

```
현재 구조 (에이전트 없음):
  Dataset → RagasEvaluator → Results

미래 구조 (에이전트 시스템):
  Dataset → [Planner Agent] → [Metric Agents] → [Insight Agent] → Results
                  ↑                    ↑                ↑
                  └────────────────────┴────────────────┘
                           Agent Coordination
```

### Coordination Profiler & Policy Guard

**전제**: 프로파일링할 에이전트 간 조율이 존재해야 함

- **목표**: Scaling Agent Systems 논문 기반, 멀티에이전트 오버헤드 정량화
- **CLI 스펙** (미래):
  ```bash
  evalvault profile <dataset_path> \
    --agents single|centralized|decentralized \
    --max-calls 1000 \
    --emit-policy
  ```
- **baseline_score 정의**: 동일 데이터셋에 대해 단일 에이전트 재실행 결과
- **우선순위**: Agent Architecture 도입 후 1.5 스프린트

### Latent Evidence Bus

**전제**: 에이전트 간 hidden state 공유가 필요해야 함

- **목표**: LatentMAS 스타일 KV cache / hidden state 공유
- **API 제약**:
  - OpenAI/Anthropic/Azure API: hidden state 미노출 → **불가능**
  - HuggingFace/vLLM 로컬 모델: **가능** (별도 어댑터 필요)
- **현실적 범위**:
  - Q1: Anthropic Extended Thinking 캡처만 (API 기반)
  - 이후: HuggingFace/vLLM 직접 통합 연구
- **우선순위**: Agent Architecture + 로컬 모델 인프라 확보 후

### 로드맵

```
2026 Q1: Domain Memory Layering (현재 시스템에 적용)
2026 Q2: Agent Architecture 설계 및 프로토타입
2026 Q3: Coordination Profiler (에이전트 시스템에 적용)
2026 Q4: Latent Evidence Bus 연구 (로컬 모델 기반)
```

---

## Completed Phases

### Phase 1-3: Core System ✅

**Status**: Complete (2024-12-24)

| Component | Status | Description |
|-----------|--------|-------------|
| Domain Entities | ✅ | TestCase, Dataset, EvaluationRun, MetricScore |
| Port Interfaces | ✅ | LLMPort, DatasetPort, StoragePort, TrackerPort, EvaluatorPort |
| Data Loaders | ✅ | CSV, Excel, JSON loaders |
| RagasEvaluator | ✅ | Async evaluation with 4 core metrics |
| OpenAI Adapter | ✅ | LangChain integration with token tracking |
| Langfuse Adapter | ✅ | Trace/score logging, SDK v3 support |
| CLI Interface | ✅ | run, metrics, config commands |

---

### Phase 4: Foundation Enhancement ✅

**Status**: Complete (2024-12-24)

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| TASK-4.3 | FactualCorrectness Metric | ✅ DONE | `evaluator.py`, `settings.py` |
| TASK-4.4 | SemanticSimilarity Metric | ✅ DONE | `evaluator.py`, `settings.py` |
| TASK-4.5a | Azure OpenAI Adapter | ✅ DONE | `src/evalvault/adapters/outbound/llm/azure_adapter.py` |
| TASK-4.5b | Anthropic Claude Adapter | ✅ DONE | `src/evalvault/adapters/outbound/llm/anthropic_adapter.py` |

#### Implemented Features

**New Metrics**:
- `factual_correctness` - ground_truth 대비 사실적 정확성
- `semantic_similarity` - 답변과 ground_truth 간 의미적 유사도

---

### Phase 5: Storage & Domain ✅

**Status**: Complete (2024-12-24)

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| TASK-5.1 | SQLite Storage Adapter | ✅ DONE | `sqlite_adapter.py`, `schema.sql` |
| TASK-5.2 | History CLI Commands | ✅ DONE | `cli.py` (history, compare, export) |
| TASK-5.3 | InsuranceTermAccuracy Metric | ✅ DONE | `src/evalvault/domain/metrics/insurance.py` |
| TASK-5.4 | Basic Testset Generation | ✅ DONE | `testset_generator.py`, `document_chunker.py` |

#### Implemented Features

**SQLite Storage** (`src/evalvault/adapters/outbound/storage/sqlite_adapter.py`):
- `save_run(run)` - 평가 결과 저장
- `get_run(run_id)` - 단일 결과 조회
- `list_runs(limit, dataset_name, model_name)` - 필터링된 목록 조회
- `delete_run(run_id)` - 결과 삭제

**CLI Commands**:
- `evalvault history` - 평가 히스토리 조회
- `evalvault compare <run_id1> <run_id2>` - 두 평가 결과 비교
- `evalvault export <run_id> -o <file>` - 결과 JSON 내보내기
- `evalvault generate <documents> -n <num>` - 테스트셋 생성

**InsuranceTermAccuracy** (`src/evalvault/domain/metrics/insurance.py`):
- 보험 도메인 특화 용어 정확도 평가
- 용어 사전 기반 매칭 (`terms_dictionary.json`)
- Ragas Metric 인터페이스 호환

**Testset Generation** (`src/evalvault/domain/services/testset_generator.py`):
- `BasicTestsetGenerator` - LLM 없이 기본 테스트셋 생성
- `DocumentChunker` - 문서 청킹 유틸리티
- factual/reasoning 질문 유형 지원

---

### Phase 6: Advanced Features ✅

**Status**: Complete (2025-12-24)

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| TASK-6.1 | Knowledge Graph Testset Generation | ✅ DONE | `kg_generator.py`, `entity_extractor.py` |
| TASK-6.2 | Experiment Management System | ✅ DONE | `experiment.py`, `experiment_manager.py` |
| TASK-6.4 | PostgreSQL Storage Adapter | ✅ DONE | `postgres_adapter.py` |
| TASK-6.5 | MLflow Tracker Adapter | ✅ DONE | `mlflow_adapter.py` |
| TASK-6.6 | Azure OpenAI Adapter | ✅ DONE | `azure_adapter.py` |
| TASK-6.7 | Anthropic Claude Adapter | ✅ DONE | `anthropic_adapter.py` |

---

#### Implemented Features

**Knowledge Graph Generator** (`src/evalvault/domain/services/kg_generator.py`):
- `KnowledgeGraph` - 지식 그래프 데이터 구조
- `KnowledgeGraphGenerator` - 문서 기반 그래프 생성
- Multi-hop 질문 생성 지원
- Entity 타입별 질문 생성

**Entity Extractor** (`src/evalvault/domain/services/entity_extractor.py`):
- 보험 도메인 엔티티 추출 (회사, 상품, 금액, 기간, 보장)
- 관계 추출 (PROVIDES, COVERS, HAS_AMOUNT 등)

**Experiment Management** (`src/evalvault/domain/services/experiment_manager.py`):
- `Experiment`, `ExperimentGroup` 엔티티
- A/B 테스트 그룹 비교
- 메트릭 통계 분석 및 결과 요약

**PostgreSQL Adapter** (`src/evalvault/adapters/outbound/storage/postgres_adapter.py`):
- asyncpg 기반 비동기 PostgreSQL 지원
- StoragePort 인터페이스 호환

**MLflow Adapter** (`src/evalvault/adapters/outbound/tracker/mlflow_adapter.py`):
- MLflow 실험 추적 연동
- TrackerPort 인터페이스 호환

**Azure OpenAI Adapter** (`src/evalvault/adapters/outbound/llm/azure_adapter.py`):
- Azure OpenAI Service 연동
- LLMPort 인터페이스 호환

**Anthropic Adapter** (`src/evalvault/adapters/outbound/llm/anthropic_adapter.py`):
- Anthropic Claude API 연동
- OpenAI embeddings fallback 지원
- LLMPort 인터페이스 호환

---

### Phase 7: Production Ready ✅

**Status**: Complete (2025-12-28)

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| TASK-7.1 | Performance Optimization | ✅ DONE | `evaluator.py` (parallel, batch_size) |
| TASK-7.2 | Docker Containerization | ✅ DONE | `Dockerfile`, `docker-compose.yml` |

#### Implemented Features

**Performance Optimization**:
- `--parallel` CLI 옵션으로 병렬 평가 활성화
- `--batch-size` 옵션으로 배치 크기 조절
- 대규모 데이터셋 평가 성능 향상

**Docker Support**:
- Multi-stage build로 최적화된 이미지
- `docker-compose.yml`로 PostgreSQL + EvalVault 스택 구성
- 비root 사용자로 보안 강화

---

## Future Enhancements

> YAGNI 원칙에 따라, 아래 기능은 실제 사용자 요구가 있을 때 구현합니다.
> 현재는 CLI + Langfuse/MLflow UI 조합으로 대부분의 사용 사례를 충족합니다.

| Feature | Description | Status |
|---------|-------------|--------|
| API Server (FastAPI) | HTTP API 노출 | ⏸️ Deferred (Langfuse/MLflow UI 활용) |
| Dashboard Web UI | 평가 결과 시각화 | ⏸️ Deferred (Langfuse/MLflow UI 활용) |
| Kubernetes Deployment | K8s 배포 지원 | ⏸️ Deferred (Docker로 충분) |

---

## Supported Metrics (Current)

| Metric | Type | Ground Truth | Embeddings | Status |
|--------|------|--------------|------------|--------|
| `faithfulness` | Ragas | No | No | ✅ |
| `answer_relevancy` | Ragas | No | Yes | ✅ |
| `context_precision` | Ragas | Yes | No | ✅ |
| `context_recall` | Ragas | Yes | No | ✅ |
| `factual_correctness` | Ragas | Yes | No | ✅ |
| `semantic_similarity` | Ragas | Yes | Yes | ✅ |
| `insurance_term_accuracy` | Custom | Yes | No | ✅ |

---

## CLI Commands (Current)

```bash
# Core Commands
evalvault run <dataset> --metrics <metrics> [--langfuse]
evalvault metrics
evalvault config

# History Commands
evalvault history [--limit N] [--dataset NAME] [--model NAME]
evalvault compare <run_id1> <run_id2>
evalvault export <run_id> -o <file>

# Generation Commands
evalvault generate <documents> -n <num> -o <output>
```

---

## Test Summary

| Category | Count | Description |
|----------|-------|-------------|
| Unit Tests | 776 | Domain, ports, adapters, services, analysis |
| Integration Tests | 26 | End-to-end flows |
| **Total** | **802** | All passing |

### Test Files
```
tests/
├── unit/
│   ├── test_entities.py          # 19 tests
│   ├── test_data_loaders.py      # 21 tests
│   ├── test_evaluator.py         # 13 tests (including parallel)
│   ├── test_langfuse_tracker.py  # 18 tests
│   ├── test_openai_adapter.py    # 4 tests
│   ├── test_ports.py             # 24 tests
│   ├── test_cli.py               # 58 tests
│   ├── test_insurance_metric.py  # 18 tests
│   ├── test_sqlite_storage.py    # 18 tests
│   ├── test_testset_generator.py # 16 tests
│   ├── test_kg_generator.py      # 27 tests (Phase 6)
│   ├── test_entity_extractor.py  # 20 tests (Phase 6)
│   ├── test_experiment.py        # 21 tests (Phase 6)
│   ├── test_postgres_storage.py  # 19 tests (Phase 6)
│   ├── test_mlflow_tracker.py    # 17 tests (Phase 6)
│   ├── test_azure_adapter.py     # 18 tests (Phase 6)
│   ├── test_anthropic_adapter.py # 19 tests (Phase 6)
│   ├── test_nlp_adapter.py       # 97 tests (Phase 2 NLP)
│   ├── test_causal_adapter.py    # 27 tests (Phase 3 Causal)
│   ├── test_domain_memory.py     # 80 tests (Phase 8)
│   └── test_benchmark_runner.py  # 24 tests (Phase 9.5)
└── integration/
    ├── test_evaluation_flow.py   # 6 tests
    ├── test_data_flow.py         # 8 tests
    ├── test_langfuse_flow.py     # 5 tests
    └── test_storage_flow.py      # 7 tests
```

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2024-12-24 | Phase 3 Complete - Core System |
| 0.2.0 | 2024-12-24 | Phase 5 Complete - Storage & Domain |
| 0.3.0 | 2025-12-24 | Phase 6 Complete - Advanced Features |
| 1.0.0 | 2025-12-28 | OSS Release - PyPI 배포, CI/CD 자동화 |
| 1.1.0 | 2025-12-29 | Phase 2 NLP + Phase 3 Causal Analysis |
| 1.2.0 | 2025-12-29 | Phase 8 Domain Memory Layering |
| 1.3.0 | 2025-12-30 | Phase 9 Korean RAG Optimization Complete |

---

## CI/CD & Release

### Cross-Platform CI

| Platform | Python | Status |
|----------|--------|--------|
| Ubuntu | 3.12, 3.13 | ✅ |
| macOS | 3.12 | ✅ |
| Windows | 3.12 | ✅ |

### Automatic Versioning (python-semantic-release)

main 브랜치에 머지되면 Conventional Commits 규칙에 따라 자동으로 버전이 결정되고 PyPI에 배포됩니다:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat:` | Minor (0.x.0) | `feat: Add new metric` |
| `fix:`, `perf:` | Patch (0.0.x) | `fix: Correct calculation` |
| Other | No release | `docs:`, `chore:`, `ci:`, etc. |

### Release Workflow

1. PR 생성 → CI 테스트 (Ubuntu, macOS, Windows)
2. PR 머지 → main 브랜치 푸시
3. Release 워크플로우 실행:
   - Conventional Commits 분석
   - 버전 태그 생성 (예: v1.0.1)
   - PyPI 배포
   - GitHub Release 생성

---

## Architecture

```
src/evalvault/
├── domain/
│   ├── entities/         # TestCase, Dataset, EvaluationRun, MetricScore, Experiment
│   ├── services/         # RagasEvaluator, TestsetGenerator, KGGenerator, ExperimentManager
│   └── metrics/          # InsuranceTermAccuracy (custom metrics)
├── ports/
│   ├── inbound/          # EvaluatorPort
│   └── outbound/         # LLMPort, DatasetPort, StoragePort, TrackerPort
├── adapters/
│   ├── inbound/          # CLI (Typer)
│   └── outbound/
│       ├── dataset/      # CSV, Excel, JSON loaders
│       ├── llm/          # OpenAI, Azure OpenAI, Anthropic adapters
│       ├── storage/      # SQLite, PostgreSQL adapters
│       └── tracker/      # Langfuse, MLflow adapters
└── config/               # Settings (pydantic-settings)
```

### Port/Adapter Implementation Status

| Port | Adapter | Status |
|------|---------|--------|
| LLMPort | OpenAIAdapter | ✅ Complete |
| LLMPort | AzureOpenAIAdapter | ✅ Complete |
| LLMPort | AnthropicAdapter | ✅ Complete |
| DatasetPort | CSV/Excel/JSON Loaders | ✅ Complete |
| TrackerPort | LangfuseAdapter | ✅ Complete |
| TrackerPort | MLflowAdapter | ✅ Complete |
| StoragePort | SQLiteAdapter | ✅ Complete |
| StoragePort | PostgreSQLAdapter | ✅ Complete |
| EvaluatorPort | RagasEvaluator | ✅ Complete |
| NLPAnalysisPort | NLPAnalysisAdapter | ✅ Complete |
| CausalAnalysisPort | CausalAnalysisAdapter | ✅ Complete |
| ReportPort | MarkdownReportAdapter | ✅ Complete |
| DomainMemoryPort | SQLiteDomainMemoryAdapter | ✅ Complete |

---

## Quality Standards (SLA)

### Metric Thresholds

| Metric | Minimum | Target | Excellent |
|--------|---------|--------|-----------|
| Faithfulness | 0.60 | 0.80 | 0.90 |
| Answer Relevancy | 0.65 | 0.80 | 0.90 |
| Context Precision | 0.60 | 0.75 | 0.85 |
| Context Recall | 0.60 | 0.80 | 0.90 |
| Factual Correctness | 0.70 | 0.85 | 0.95 |
| Semantic Similarity | 0.70 | 0.85 | 0.95 |

### System Requirements

- **Throughput**: 100 test cases / 5 minutes
- **Result Storage**: Dual storage (SQLite + Langfuse)
- **Reproducibility**: Deterministic results (temperature=0)

---

## References

- [Ragas Documentation](https://docs.ragas.io/)
- [Langfuse Documentation](https://langfuse.com/docs)
