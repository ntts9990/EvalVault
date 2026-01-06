# EvalVault 개발 가이드

> **Last Updated**: 2026-01-07
> **Version**: 2.0
> **Status**: 활성 개발 중

이 문서는 EvalVault 개발에 필요한 모든 정보를 통합한 내부 개발 가이드입니다.

---

## 목차

1. [개발 환경 설정](#1-개발-환경-설정)
2. [아키텍처 원칙](#2-아키텍처-원칙)
3. [코드 품질 개선 현황](#3-코드-품질-개선-현황)
4. [AI 에이전트 기반 개발](#4-ai-에이전트-기반-개발)
5. [기능별 구현 가이드](#5-기능별-구현-가이드)
6. [테스트 가이드](#6-테스트-가이드)
7. [CI/CD 및 릴리스](#7-cicd-및-릴리스)
8. [부록 A: 아키텍처 감사 상세](#부록-a-아키텍처-감사-상세)
9. [부록 B: 성능 최적화 구현](#부록-b-성능-최적화-구현)
10. [부록 C: RAG 단계별 성능 평가 설계](#부록-c-rag-단계별-성능-평가-설계)

---

## 1. 개발 환경 설정

### 1.1 필수 요구사항

- Python 3.12+
- `uv` 패키지 매니저

### 1.2 설치

```bash
# 기본 개발 환경
uv sync --extra dev

# dev는 모든 extras를 포함합니다. 경량 설치가 필요하면 개별 extras만 선택하세요.
```

### 1.3 Optional Dependencies

| Extra | 패키지 | 용도 |
|-------|--------|------|
| `dev` | pytest, ruff, pydeps | 개발 도구 + 전체 기능 |
| `analysis` | scikit-learn | 통계/NLP 분석 |
| `korean` | kiwipiepy, rank-bm25, sentence-transformers | 한국어 NLP |
| `postgres` | psycopg | PostgreSQL 지원 |
| `mlflow` | mlflow | MLflow 트래커 |
| `docs` | mkdocs, mkdocs-material, mkdocstrings | 문서 빌드 |
| `phoenix` | arize-phoenix, opentelemetry | Phoenix 트레이싱 |
| `anthropic` | anthropic | Anthropic LLM 어댑터 |
| `web` | streamlit, plotly, watchdog | Streamlit Web UI |
| `perf` | faiss-cpu, ijson | 대용량 데이터셋 성능 보조 |

### 1.4 환경 변수

```bash
cp .env.example .env
# 필수: OPENAI_API_KEY 또는 OLLAMA_BASE_URL
# 선택: LANGFUSE_*, PHOENIX_*, ANTHROPIC_API_KEY
```

---

## 2. 아키텍처 원칙

### 2.1 핵심 원칙

1. **Hexagonal Architecture**: Port/Adapter 패턴으로 외부 의존성 분리
2. **Clean Architecture**: 의존성 방향 외부→내부
3. **DDD**: 도메인 중심 설계
4. **SOLID**: 단일 책임, 개방-폐쇄, 의존성 역전
5. **YAGNI**: 필요한 기능만 구현
6. **TDD**: 테스트 주도 개발

### 2.2 디렉토리 구조

```
src/evalvault/
├── domain/           # 비즈니스 로직 (프레임워크 독립)
│   ├── entities/     # 도메인 엔티티
│   ├── services/     # 도메인 서비스
│   └── metrics/      # 커스텀 메트릭
├── ports/            # 인터페이스 정의
│   ├── inbound/      # 진입점 포트
│   └── outbound/     # 외부 의존성 포트
├── adapters/         # 포트 구현
│   ├── inbound/      # CLI, Web UI
│   └── outbound/     # LLM, Storage, Tracker 등
└── config/           # 설정
```

### 2.3 의존성 규칙

```
❌ Domain → Adapters (금지)
✅ Domain → Ports (허용)
✅ Adapters → Ports (허용)
✅ Adapters → Domain (허용)
```

검증 명령:
```bash
rg "from evalvault.adapters" src/evalvault/domain  # 결과 0이어야 함
```

---

## 3. 코드 품질 개선 현황

### 3.1 완료된 작업 (Phase 0-2)

| Phase | 작업 | 상태 |
|-------|------|------|
| P0 | 아키텍처 안전망 (의존성 역전, extras 재구성) | ✅ 완료 |
| P1.1 | LLM Adapter 통합 (`BaseLLMAdapter`) | ✅ 완료 |
| P1.2 | Storage Adapter 통합 (`BaseSQLStorageAdapter`) | ✅ 완료 |
| P1.3 | Analysis Adapter 통합 | ✅ 완료 |
| P2 | CLI 모듈 분리 (3k LOC → 모듈화) | ✅ 완료 |

### 3.2 진행 중인 개선 작업 (P2.2~P6)

| Phase | 작업 | 상태 | 담당 |
|-------|------|------|------|
| P2.2 | Web UI 재구조화 | 🚧 진행 중 | - |
| P3 | 성능 최적화 (캐시, 배치, 스트리밍) | 🚧 진행 중 | performance |
| P4.1 | CLI UX 개선 | 🚧 진행 중 | - |
| P5 | 테스트 커버리지 향상 (89% → 95%) | 🚧 진행 중 | testing |
| P6 | 문서화 개선 (API/튜토리얼) | 🚧 진행 중 | documentation |

상세 범위와 일정은 `docs/internal/plans/PARALLEL_WORK_PLAN.md`에서 관리합니다.

### 3.2.1 완료된 개선 작업

| Phase | 작업 | 상태 | 담당 |
|-------|------|------|------|
| P7 | Phoenix Observability | ✅ 완료 | observability |
| P8 | Domain Memory 활용 | ✅ 완료 | - |

### 3.3 성공 지표

| 지표 | 현재 | 목표 |
|------|------|------|
| 테스트 커버리지 | 89% | 95% |
| 중복 코드 | < 5% | < 3% |
| 평가 실행 시간 (1000 TC) | 15분 | 10분 |
| 캐시 적중률 | 85% | 90% |

---

## 4. AI 에이전트 기반 개발

### 4.1 에이전트 시스템 개요

EvalVault는 AI 에이전트를 활용한 병렬 개발 워크플로우를 지원합니다.

```bash
# 에이전트 실행
cd agent/
uv run python main.py --project-dir .. --agent-type architecture
```

### 4.2 에이전트 타입

| 타입 | 역할 | Phase |
|------|------|-------|
| `architecture` | 코드 구조, 의존성 역전 | P0-P2 |
| `performance` | 캐싱, 배치 처리, 최적화 | P3 |
| `testing` | 테스트 커버리지 향상 | P5 |
| `documentation` | 문서화, 튜토리얼 | P6 |
| `observability` | Phoenix 통합, 트레이싱 | P7 |
| `rag-data` | RAG 데이터 분석 | P7 (blocked) |
| `coordinator` | 전체 조율, 충돌 방지 | All |

### 4.3 병렬 실행 그룹

```
Group A (독립): performance, testing, documentation
Group B (순차): observability → rag-data
Group C (순차): architecture (P0→P1→P2)
```

### 4.4 충돌 방지 규칙

| 에이전트 | 수정 가능 | 수정 금지 |
|----------|----------|----------|
| testing | `tests/` | `src/evalvault/` |
| performance | `adapters/outbound/cache/` | `adapters/inbound/`, LLM adapters |
| documentation | `docs/` | `src/` |

**공유 파일 (조율 필요)**:
- `pyproject.toml`
- `src/evalvault/__init__.py`
- `src/evalvault/config/settings.py`

### 4.5 에이전트 메모리 시스템

```
agent/memory/
├── shared/
│   ├── decisions.md      # 공유 의사결정 기록
│   └── dependencies.md   # 모듈 간 의존성
└── agents/
    ├── architecture/     # 에이전트별 작업 로그
    ├── performance/
    └── ...
```

---

## 5. 기능별 구현 가이드

### 5.1 한국어 RAG 최적화 (Phase 9)

**구현 완료**:
- ✅ KiwiTokenizer (형태소 분석)
- ✅ KoreanBM25Retriever
- ✅ KoreanDenseRetriever (BGE-m3-ko)
- ✅ KoreanHybridRetriever (BM25 + Dense)
- ✅ KoreanFaithfulnessChecker

**파일 위치**:
```
src/evalvault/adapters/outbound/nlp/korean/
├── kiwi_tokenizer.py
├── korean_bm25_retriever.py
├── korean_dense_retriever.py
├── korean_hybrid_retriever.py
└── korean_faithfulness.py
```

### 5.2 Domain Memory (Phase 8)

**3계층 구조**:
1. **Factual Memory**: 검증된 사실 (FTS5 검색)
2. **Experiential Memory**: 학습된 패턴
3. **Working Memory**: 세션 컨텍스트

**주요 클래스**:
- `DomainLearningHook`: 평가 결과에서 학습
- `MemoryAwareEvaluator`: 메모리 기반 threshold 조정
- `MemoryBasedAnalysis`: 트렌드/추천 생성

### 5.3 DAG Analysis Pipeline (Phase 14)

**의도 분류**:
```python
class AnalysisIntent(StrEnum):
    VERIFY_MORPHEME = "verify_morpheme"
    COMPARE_SEARCH_METHODS = "compare_search"
    ANALYZE_LOW_METRICS = "analyze_low_metrics"
    GENERATE_SUMMARY = "generate_summary"
    # ... 12가지 의도
```

**파이프라인 실행**:
```bash
evalvault pipeline analyze "형태소 분석이 제대로 되는지 확인해줘"
```

### 5.4 Phoenix Observability (Phase 7)

**기능**:
- OpenInference 스팬 전송
- Phoenix Dataset/Experiment 업로드
- 임베딩 시각화
- Prompt Manifest 동기화
- Drift Watch (`scripts/ops/phoenix_watch.py`)

**CLI 옵션**:
```bash
evalvault run data.json \
  --tracker phoenix \
  --phoenix-dataset insurance-qa \
  --phoenix-experiment baseline-v1
```

### 5.5 Qwen3-Embedding 통합

**Matryoshka 지원**:
- 개발 환경: `qwen3-embedding:0.6b` (256 dim)
- 운영 환경: `qwen3-embedding:8b` (1024 dim)

**프로필 설정** (`config/models.yaml`):
```yaml
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

---

## 6. 테스트 가이드

### 6.1 테스트 구조

```
tests/
├── unit/           # 1,261개 단위 테스트
├── integration/    # 91개 통합 테스트
├── fixtures/       # 테스트 데이터
└── e2e_data/       # E2E 데이터셋
```

### 6.2 테스트 실행

```bash
# 전체 테스트
uv run pytest tests -v

# 커버리지 포함
uv run pytest --cov=src --cov-report=term

# 특정 모듈
uv run pytest tests/unit/test_evaluator.py -v

# 마킹된 테스트
uv run pytest -m "not slow" tests/
```

### 6.3 테스트 작성 규칙

1. `test_<behavior>` 네이밍
2. 비동기 코드는 `pytest.mark.asyncio`
3. 외부 API 의존성은 docstring에 명시
4. fixtures는 `tests/fixtures/` 사용

---

## 7. CI/CD 및 릴리스

### 7.1 CI 파이프라인

```yaml
# .github/workflows/ci.yml
- Ubuntu, macOS, Windows
- Python 3.12, 3.13
- pytest, ruff check, ruff format
```

### 7.2 자동 버전 관리

**python-semantic-release** 사용:

| Commit Type | Version Bump |
|-------------|--------------|
| `feat:` | Minor (0.x.0) |
| `fix:`, `perf:` | Patch (0.0.x) |
| `docs:`, `chore:` | No release |

### 7.3 릴리스 워크플로우

1. PR 생성 → CI 테스트
2. PR 머지 → main 브랜치
3. Release 워크플로우:
   - Conventional Commits 분석
   - 버전 태그 생성
   - PyPI 배포
   - GitHub Release 생성

### 7.4 버전 히스토리

| Version | Date | Description |
|---------|------|-------------|
| 1.5.0 | 2025-12-30 | Phase 14 - DAG Analysis Pipeline |
| 1.4.0 | 2025-12-30 | Phase 10-13 - React + FastAPI Web UI |
| 1.3.0 | 2025-12-30 | Phase 9 - Korean RAG Optimization |
| 1.2.0 | 2025-12-29 | Phase 8 - Domain Memory |
| 1.1.0 | 2025-12-29 | Phase 2 NLP + Phase 3 Causal |
| 1.0.0 | 2025-12-28 | OSS Release |

---

## 부록 A: 아키텍처 감사 상세

> **Audit Date**: 2026-01-03
> **Auditor**: Claude Code
> **Scope**: Full codebase architecture review
> **Total Files Analyzed**: 190 Python source files

---

## Executive Summary

EvalVault 코드베이스를 Hexagonal Architecture, Clean Architecture, SOLID, TDD, YAGNI 원칙 준수 관점에서 전수 검사하였습니다.

### Overall Compliance Score

| Principle | Score | Status |
|-----------|-------|--------|
| **Hexagonal Architecture** | 88/100 | GOOD |
| **Clean Architecture** | 85/100 | GOOD |
| **SOLID Principles** | 82/100 | GOOD |
| **TDD Compliance** | 82/100 | GOOD |
| **YAGNI** | 80/100 | GOOD |
| **Overall** | **83/100** | **GOOD** |

### Key Findings Summary

| Priority | Issue | Location | Impact |
|----------|-------|----------|--------|
| **P0** | DomainMemoryPort fat interface (38 methods) | `ports/outbound/domain_memory_port.py` | High |
| **P0** | run.py command 1,784 lines | `adapters/inbound/cli/commands/run.py` | High |
| **P0** | settings.py 테스트 누락 | `tests/unit/test_settings.py` | High |
| **P1** | Phoenix config import in domain | `domain/services/memory_aware_evaluator.py:7` | Medium |
| **P1** | LLMRelationAugmenter domain import | `adapters/outbound/llm/llm_relation_augmenter.py:8` | Medium |
| **P1** | CLI 직접 adapter 생성 | `history.py, gate.py, analyze.py` | Medium |
| **P2** | LLMPort ABC에 concrete method | `ports/outbound/llm_port.py:65-82` | Low |
| **P2** | HybridCache over-engineering | `adapters/outbound/cache/hybrid_cache.py` | Low |

---

## 1. Domain Layer Analysis

### 1.1 Compliance Score: 93/100

**Classes Analyzed**: 78 entity/service classes across 47 files

### 1.2 Strengths

- **Excellent entity design**: Pure dataclasses with no infrastructure dependencies
- **Strong port dependency pattern**: Services depend on abstractions
- **Rich type system**: Comprehensive use of enums and type hints
- **Good separation**: Entities vs Services clearly separated

### 1.3 Critical Violations

#### V1: Phoenix Config Import in Domain (CRITICAL)
```
File: src/evalvault/domain/services/memory_aware_evaluator.py:7
Code: from evalvault.config.phoenix_support import instrumentation_span, set_span_attributes
```
- **Issue**: Domain imports from config layer (infrastructure concern)
- **Principle Violated**: Hexagonal Architecture, Clean Architecture
- **Recommendation**: Create `TracerPort` abstraction in `ports/outbound/`

#### V2: Ragas Framework Dependency (INTENTIONAL)
```
File: src/evalvault/domain/services/evaluator.py:10-29
Code: from ragas import SingleTurnSample, ...
```
- **Issue**: Direct framework dependency in domain
- **Status**: May be intentional design choice (Ragas is core to EvalVault)
- **Recommendation**: Document in architecture decision record

#### V3: Pydantic in KG Entities (MODERATE)
```
File: src/evalvault/domain/entities/kg.py:7, 23, 29-30
Code: @field_validator, @model_validator from Pydantic
```
- **Issue**: Framework coupling in domain entities
- **Recommendation**: Convert to pure dataclasses with `__post_init__` validation

### 1.4 SRP Violations (Minor)

| Class | Issue | Location |
|-------|-------|----------|
| AnalysisService | 4 adapters in constructor | `analysis_service.py:34-52` |
| BenchmarkResult | Multiple format converters | `benchmark.py:332-420` |
| ImprovementReport | Data + markdown generation | `improvement.py:410-507` |
| EvaluationRun | Data + calculation logic | `result.py:98-192` |

---

## 2. Ports Layer Analysis

### 2.1 Compliance Score: 70/100

**Ports Analyzed**: 24 ports (4 inbound, 20 outbound)

### 2.2 Critical Violations

#### V1: DomainMemoryPort Fat Interface (CRITICAL)
```
File: src/evalvault/ports/outbound/domain_memory_port.py
Size: 755 lines, 38 methods
```

**9 distinct responsibilities mixed**:
1. Fact persistence (7 methods)
2. Learning memory (3 methods)
3. Behavior tracking (4 methods)
4. Working memory (5 methods)
5. Evolution dynamics (4 methods)
6. Memory retrieval (3 methods)
7. Memory formation (3 methods)
8. KG integration (4 methods)
9. Hierarchical memory (4 methods)

**Recommendation**: Split into segregated interfaces:
```python
class FactualMemoryPort(Protocol): ...      # 7 methods
class BehaviorMemoryPort(Protocol): ...     # 4 methods
class MemoryEvolutionPort(Protocol): ...    # 4 methods
class MemoryRetrievalPort(Protocol): ...    # 3 methods
class KGIntegrationPort(Protocol): ...      # 4 methods
```

#### V2: LLMPort Concrete Methods in ABC
```
File: src/evalvault/ports/outbound/llm_port.py:65-82
Code: def get_thinking_config(self) -> ThinkingConfig: return ThinkingConfig(enabled=False)
```
- **Issue**: Concrete implementation in port interface
- **Recommendation**: Move to `BaseLLMAdapter` in adapters layer

### 2.3 ISP Violations

| Port | Methods | Issue |
|------|---------|-------|
| WebUIPort | 6 | Evaluation + Query + Report mixed |
| StoragePort | 7 | Run + Experiment entities mixed |
| AnalysisPipelinePort | 3 | Build + Execute mixed |

### 2.4 Missing Exports

```python
# outbound/__init__.py missing:
- IntentClassifierPort
- AnalysisModulePort

# inbound/__init__.py missing:
- AnalysisPipelinePort
```

---

## 3. Outbound Adapters Analysis

### 3.1 Compliance Score: 82/100

**Adapters Analyzed**: 18 adapter classes across 9 subsystems

### 3.2 Critical Violations

#### V1: LLMRelationAugmenter Domain Import
```
File: src/evalvault/adapters/outbound/llm/llm_relation_augmenter.py:8
Code: from evalvault.domain.services.entity_extractor import Entity, Relation
```
- **Issue**: Adapter imports from domain services
- **Principle Violated**: Hexagonal Architecture (backwards dependency)
- **Recommendation**: Accept pre-constructed objects as parameters

#### V2: HybridCache Over-Engineering (YAGNI)
```
File: src/evalvault/adapters/outbound/cache/hybrid_cache.py
Lines: 450+
Features: Hot/Cold tiers, Prefetch callback, LRU eviction, TTL extension, Promotion/demotion
```
- **Issue**: Potentially unused features
- **Recommendation**: Audit actual usage, simplify if not needed

### 3.3 Port Conformance Issues

| Adapter | Port | Issue |
|---------|------|-------|
| BaseLLMAdapter | LLMPort | Token tracking methods not in port |
| HybridCache | AnalysisCachePort | Does not implement port |
| Multiple LLM adapters | LLMPort | `agenerate_text()` raises NotImplementedError |

---

## 4. Inbound Adapters Analysis

### 4.1 Compliance Score: 77/100

**Components Analyzed**: 14 CLI commands, 13 Web components

### 4.2 Critical Violations

#### V1: Run Command Size (CRITICAL)
```
File: src/evalvault/adapters/inbound/cli/commands/run.py
Lines: 1,784
```

**Mixed responsibilities**:
- Dataset loading & validation
- Streaming configuration
- Phoenix integration
- Domain Memory integration
- Evaluation orchestration
- Output formatting
- Result tracking

**Recommendation**: Split into 5+ smaller modules:
```
cli/commands/run/
├── evaluation_runner.py    # Orchestration
├── dataset_loader.py       # Loading
├── output_formatter.py     # Formatting
├── tracker_integration.py  # Phoenix/Langfuse
└── __init__.py            # Command registration
```

#### V2: CLI Direct Adapter Creation (DIP Violation)
```
Files: history.py:61, gate.py:52, analyze.py:61, pipeline.py:60
Code: storage = SQLiteStorageAdapter(db_path=db_path)
```
- **Issue**: CLI creates concrete adapters instead of using DI
- **Recommendation**: Use factory pattern or DI container

#### V3: Web Adapter Business Logic Mixing
```
File: src/evalvault/adapters/inbound/web/adapter.py:559-638
Code: ImprovementGuideService creation in adapter
```
- **Issue**: Domain service creation in presentation layer
- **Recommendation**: Move to domain service factory

### 4.3 File Size Analysis

| File | Lines | Status |
|------|-------|--------|
| run.py | 1,784 | CRITICAL |
| web/app.py | 887 | HIGH |
| web/adapter.py | 791 | HIGH |
| analyze.py | 680 | MODERATE |

---

## 5. Config Layer Analysis

### 5.1 Compliance Score: 90/100

**Files Analyzed**: 7 configuration files

### 5.2 Separation of Concerns

| File | SoC Score | Status |
|------|-----------|--------|
| settings.py | 9/10 | Excellent |
| model_config.py | 10/10 | Perfect |
| domain_config.py | 9.5/10 | Excellent |
| instrumentation.py | 8.5/10 | Good |
| phoenix_support.py | 7/10 | Needs Refactoring |
| agent_types.py | 10/10 | Perfect |

### 5.3 Violations

#### V1: PhoenixExperimentResolver in Config Layer
```
File: src/evalvault/config/phoenix_support.py
Issue: Data extraction logic and adapter coupling
```
- **Recommendation**: Move to `domain/services/phoenix_service.py`

---

## 6. TDD Compliance Analysis

### 6.1 Compliance Score: 82/100

**Test Statistics**:
- Total Test Files: 84 (74 unit, 10 integration)
- Total Test Lines: 30,906
- Estimated Test Cases: 1,352
- Coverage: 89%

### 6.2 Critical Gap

#### Missing Test Suite: settings.py
```
File: src/evalvault/config/settings.py (205 lines)
Tests: NONE
Coverage: ~0%
```

**Required Tests**:
- Environment variable loading
- Profile application
- Provider selection
- Connection string handling
- Global singleton behavior

### 6.3 Coverage by Layer

| Layer | Test Files | Coverage |
|-------|------------|----------|
| Domain Entities | 5+ | ~95% |
| Domain Services | 10+ | ~85% |
| Config | 5 | ~62% |
| Outbound Adapters | 15+ | ~90% |
| Inbound Adapters | 10+ | ~80% |

### 6.4 Test Pattern Quality

| Aspect | Score |
|--------|-------|
| Test Organization | 9/10 |
| Fixture Usage | 9/10 |
| Test Doubles | 8.5/10 |
| Edge Case Testing | 8/10 |
| Integration Testing | 8/10 |

---

## 7. YAGNI Compliance

### 7.1 Compliance Score: 80/100

### 7.2 Over-Engineering Concerns

| Component | Issue | Severity |
|-----------|-------|----------|
| HybridCache | Unused tier features | HIGH |
| DomainMemoryPort Phase 2 methods | Not implemented | MEDIUM |
| Analysis Pipeline 17 intent types | Verify usage | LOW |
| Stage entities | Check if used | LOW |

### 7.3 Well-Balanced Areas

- Metric selector flexibility
- Component composition pattern
- Port-based architecture extensibility
- Analysis pipeline architecture

---

## 8. Recommendations by Priority

### P0 - Critical (Address Immediately)

| # | Issue | Fix | Effort |
|---|-------|-----|--------|
| 1 | DomainMemoryPort fat interface | Split into 5-7 focused ports | 8h |
| 2 | run.py 1,784 lines | Refactor into modules | 16h |
| 3 | settings.py 테스트 누락 | Create comprehensive test suite | 4h |

### P1 - High (This Sprint)

| # | Issue | Fix | Effort |
|---|-------|-----|--------|
| 4 | Phoenix import in domain | Create TracerPort abstraction | 3h |
| 5 | LLMRelationAugmenter domain import | Accept objects as parameters | 2h |
| 6 | CLI direct adapter creation | Implement factory pattern | 4h |
| 7 | PhoenixExperimentResolver in config | Move to domain service | 3h |

### P2 - Medium (Next Sprint)

| # | Issue | Fix | Effort |
|---|-------|-----|--------|
| 8 | LLMPort concrete methods | Move to BaseLLMAdapter | 2h |
| 9 | ISP violations in ports | Split WebUIPort, StoragePort | 4h |
| 10 | Web adapter business logic | Extract to domain services | 4h |
| 11 | Expand phoenix_support tests | Add 9 more test cases | 3h |

### P3 - Low (Backlog)

| # | Issue | Fix | Effort |
|---|-------|-----|--------|
| 12 | HybridCache over-engineering | Audit and simplify | 4h |
| 13 | Pydantic in KG entities | Convert to dataclasses | 2h |
| 14 | Missing port exports | Update __init__.py files | 1h |
| 15 | SRP violations in entities | Extract calculators | 3h |

---

## 9. Architecture Strengths

### 9.1 Excellent Patterns

1. **Hexagonal Architecture Foundation**
   - Clear separation: Domain → Ports → Adapters
   - Port interfaces well-defined
   - Multiple adapter implementations

2. **Type Safety**
   - Comprehensive type hints
   - Enum-based type safety
   - Dataclass field validation

3. **Test Infrastructure**
   - 1,352 tests, 89% coverage
   - Good fixture patterns
   - Appropriate use of mocks

4. **Extensibility**
   - Multi-LLM support (4 providers)
   - Multi-DB support (SQLite, PostgreSQL)
   - Multi-Tracker support (Langfuse, MLflow, Phoenix)

### 9.2 Documentation Quality

- Comprehensive CLAUDE.md
- Clear ROADMAP.md
- Good inline documentation

---

## 10. Compliance Matrix

### 10.1 By Layer

| Layer | Hexagonal | Clean | SOLID | TDD | YAGNI | Overall |
|-------|-----------|-------|-------|-----|-------|---------|
| Domain | 93% | 96% | 95% | 95% | 89% | **93%** |
| Ports | 85% | 80% | 70% | - | 85% | **80%** |
| Outbound Adapters | 92% | 88% | 82% | 90% | 75% | **85%** |
| Inbound Adapters | 85% | 80% | 70% | 80% | 82% | **79%** |
| Config | 95% | 90% | 90% | 62% | 90% | **85%** |
| **Overall** | **90%** | **87%** | **81%** | **82%** | **84%** | **85%** |

### 10.2 SOLID Breakdown

| Principle | Score | Key Issues |
|-----------|-------|------------|
| **S**ingle Responsibility | 78% | run.py, DomainMemoryPort |
| **O**pen/Closed | 85% | Hard-coded metric lists |
| **L**iskov Substitution | 95% | Good inheritance patterns |
| **I**nterface Segregation | 75% | DomainMemoryPort, WebUIPort |
| **D**ependency Inversion | 85% | CLI adapter creation |

---

## 11. Action Plan Timeline

### Week 1
- [ ] P0: Create test_settings.py (4h)
- [ ] P1: Create TracerPort abstraction (3h)
- [ ] P1: Fix LLMRelationAugmenter (2h)

### Week 2
- [ ] P0: Split DomainMemoryPort (8h)
- [ ] P1: Implement CLI adapter factory (4h)

### Week 3-4
- [ ] P0: Refactor run.py (16h)
- [ ] P1: Move PhoenixExperimentResolver (3h)

### Ongoing
- [ ] P2/P3 items as capacity allows

---

## 12. Conclusion

EvalVault 코드베이스는 전반적으로 **양호한 아키텍처 준수 상태(83/100)**를 보여주고 있습니다.

**주요 강점**:
- Hexagonal Architecture 기반 설계
- 포괄적인 테스트 커버리지 (89%)
- 확장 가능한 멀티-어댑터 시스템
- 강력한 타입 시스템

**즉시 개선 필요**:
- DomainMemoryPort 인터페이스 분리
- run.py 명령어 모듈화
- settings.py 테스트 추가

P0 이슈 해결 시 전체 점수가 **88-90점**으로 상승할 것으로 예상됩니다.

---

**Report Generated**: 2026-01-03
**Analysis Method**: Parallel agent exploration with deep code inspection
**Files Reviewed**: 190 source files, 84 test files

## 부록 B: 성능 최적화 구현

### B.1 HybridCache

**파일**: `src/evalvault/adapters/outbound/cache/hybrid_cache.py`

**특징**:
- 2-tier 아키텍처 (hot/cold 영역)
- 접근 빈도 기반 승격/강등
- 적응형 TTL
- 스레드 안전

### B.2 AsyncBatchExecutor

**파일**: `src/evalvault/domain/services/async_batch_executor.py`

**특징**:
- 적응형 배치 크기 조절
- 레이트 리밋 자동 처리
- 재시도 메커니즘

### B.3 StreamingDatasetLoader

**파일**: `src/evalvault/adapters/outbound/dataset/streaming_loader.py`

**특징**:
- 청크 단위 로딩
- Iterator/Generator 기반 지연 로딩
- CSV/JSON/Excel 지원

---

## 부록 C: RAG 단계별 성능 평가 설계

> **Last Updated**: 2026-01-03
> **Status**: 내부 설계 초안 (Dev/Analyst 우선)

이 문서는 RAG 파이프라인의 단계별 실행 데이터를 표준화해 수집·저장하고, 단계별/종합
성능 평가와 개선 가이드 생성에 활용하기 위한 설계안을 정리합니다. 엔터프라이즈용
멀티테넌시/대규모 관측 스택은 범위 밖으로 두고, 개발자·데이터 분석가가 로컬에서
빠르게 활용할 수 있는 구성을 우선합니다.

---

## 목차

1. [목표와 범위](#1-목표와-범위)
2. [단계 모델 정의](#2-단계-모델-정의)
3. [단계별 데이터 스키마](#3-단계별-데이터-스키마)
4. [단계별 평가 지표](#4-단계별-평가-지표)
5. [EvalVault 저장 구조 제안](#5-evalvault-저장-구조-제안)
6. [수집·분석 운영 흐름](#6-수집·분석-운영-흐름)
7. [MVP 구현 순서](#7-mvp-구현-순서)

---

## 1. 목표와 범위

### 1.1 목표

- **단계별 실행 데이터 수집**: `system_prompt` → `input` → `retrieval` → `output`을
  필수 4단계로 정의하고, 나머지는 선택적으로 확장.
- **단계별 성능 평가**: 단계별 품질/레이턴시/비용을 측정해 병목을 분리.
- **E2E 평가와 연결**: 단계 결과를 E2E 결과와 같은 `run_id`로 연결.
- **개선 가이드 근거 확보**: 개선 플레이북/LLM 인사이트에 사용할 정량 근거 제공.

### 1.2 범위 (비범위 포함)

- 범위: 로컬/팀 단위 사용, SQLite 중심 저장, Phoenix/Langfuse 연동 가능.
- 비범위: 멀티테넌시, 장기 보관 정책, PII 규정 대응, 실시간 대시보드 SLA.

### 1.3 데이터셋 존재 여부 대응

- **데이터셋 있음**: 정답/관련 문서 기반의 정밀 지표 계산.
- **데이터셋 없음**: 약지도/LLM Judge/휴리스틱 기반의 대체 지표 사용.

---

## 2. 단계 모델 정의

### 2.1 필수 단계 (최소 공통 단계)

| stage_type | 설명 | 비고 |
|------------|------|------|
| `system_prompt` | 시스템 프롬프트 구성/확정 | 필수 |
| `input` | 사용자 쿼리 수집 | 필수 |
| `retrieval` | DB/인덱스 조회 | 필수 |
| `output` | 최종 결과/답변 | 필수 |

> 필수 단계가 미수집된 실행은 E2E는 평가하되, 단계별 분석에는 `completeness` 경고를 남김.

### 2.2 선택 단계 (확장 가능)

아래 항목은 모두 선택 단계이며, 파이프라인 특성에 맞게 자유롭게 추가/축소한다.

| stage_type | 용도 |
|------------|------|
| `intent` | 의도 분석 |
| `language_detection` | 언어 감지 |
| `clarification` | 사용자 추가 질문/모호성 해소 |
| `routing` | 기능/모델/검색 전략 라우팅 |
| `retrieval_decision` | 검색 필요 여부 판단/검색 전략 선택 |
| `source_selection` | 멀티 소스/리트리버 선택 |
| `rewrite` | 쿼리 리라이트 |
| `expansion` | 쿼리 확장(멀티쿼리, 키워드 확장) |
| `multi_query_generation` | Multi-Query/RAG-Fusion용 쿼리 생성 |
| `decomposition` | 질문 분해/서브쿼리 생성 |
| `self_query` | 메타데이터 필터/구조화 쿼리 생성 |
| `hypothetical_doc` | HyDE 등 가상 문서 생성 |
| `query_translation` | 다국어 질의 번역 |
| `planning` | 플래닝/툴 계획 |
| `memory` | 세션/개인화 메모리 조회 |
| `cache` | 캐시 조회/재사용 |
| `query_embedding` | 쿼리 임베딩/벡터화 |
| `metadata_filter` | 메타데이터 기반 필터링 |
| `iterative_retrieval` | 다단계/멀티홉 검색 반복 |
| `hybrid_retrieval` | sparse+dense 등 복수 리트리버 병렬 실행 |
| `fusion` | 다중 검색 결과 결합(RRF, weighted 등) |
| `rerank` | 리랭킹 |
| `filter` | 컨텍스트 필터링/중복 제거 |
| `compression` | 컨텍스트 압축/요약 |
| `contextualization` | 컨텍스트 주입/문서 보강 |
| `context_assembly` | 컨텍스트 묶음/프롬프트 구성 |
| `entity_linking` | KG 엔티티 매핑/링킹 |
| `knowledge_graph` | KG 기반 조회/증강 |
| `tool` | 도구 호출/함수 실행 |
| `candidate_generation` | 다중 후보 답변 생성(self-consistency) |
| `answer_synthesis` | 다중 컨텍스트 합성 초안 |
| `grounding_check` | 근거/사실성 검증 |
| `answer_validation` | 응답 검증/일관성 체크 |
| `reflection` | Self-RAG/자기 검증/비평 |
| `consensus` | 후보 답변 합의/선택 |
| `answer_refinement` | 답변 재작성/개선 |
| `citation` | 근거 추출/정규화 |
| `safety_check` | 정책/보안/PII 필터 |
| `postprocess` | 결과 후처리/가드레일 |
| `feedback` | 사용자 피드백 수집 |
| `fallback` | 예외 처리/대체 응답 |
| `document_ingestion` | 문서 수집/정규화 |
| `chunking` | 문서 분할 |
| `document_embedding` | 문서 임베딩 생성 |
| `indexing` | 인덱스 구축/업데이트 |

> `document_ingestion` ~ `indexing` 단계는 오프라인/배치 파이프라인에서도 기록 가능.

### 2.3 DAG/스팬 모델

- **stage_event**는 스팬 단위로 기록하며 `parent_stage_id`로 DAG를 구성.
- 동일 단계가 여러 번 발생할 수 있으므로 `stage_id`/`attempt`로 구분.
- `trace_id`(Phoenix/Langfuse)와 연동해 외부 트레이싱과 연결 가능.

---

## 3. 단계별 데이터 스키마

### 3.1 공통 스키마 (필수 필드)

```json
{
  "run_id": "run_20260103_001",
  "stage_id": "stg_system_prompt_01",
  "parent_stage_id": null,
  "stage_type": "system_prompt",
  "stage_name": "system_prompt_v1",
  "status": "success",
  "attempt": 1,
  "started_at": "2026-01-03T10:15:30.120Z",
  "finished_at": "2026-01-03T10:15:30.420Z",
  "duration_ms": 300,
  "input_ref": {
    "store": "payload",
    "id": "pl_abc123",
    "type": "json"
  },
  "output_ref": {
    "store": "payload",
    "id": "pl_def456",
    "type": "json"
  },
  "trace": {
    "trace_id": "phoenix_trace_id",
    "span_id": "span_system_prompt_01"
  },
  "attributes": {},
  "metadata": {
    "dataset_name": "insurance_qa_korean",
    "test_case_id": "tc_0001",
    "session_id": "sess_42"
  }
}
```

### 3.2 공통 규칙

- `stage_type`은 공통 enum을 따르되, `stage_name`으로 상세 구현을 표현.
- 대용량 텍스트/리스트는 `input_ref`/`output_ref`로 분리 저장.
- 데이터셋 기반 실행 시 `test_case_id`를 반드시 `metadata`에 포함.
- `duration_ms`는 가능한 한 기록하고, `started_at`/`finished_at`만 있는 경우 자동 계산 가능.
- `output.citation_count` 계산을 위해 근거 목록은 `output.attributes.citations`에 기록
  (리스트 또는 `{"doc_ids": [...]}` 형태 권장).

### 3.3 단계별 권장 필드 (attributes)

#### system_prompt

| 키 | 설명 |
|----|------|
| `prompt_id` | 시스템 프롬프트 식별자 |
| `template` | 시스템 프롬프트 템플릿 |
| `checksum` | 프롬프트 해시 |
| `model` | 적용 대상 모델 |

#### input

| 키 | 설명 |
|----|------|
| `query` | 사용자 원문 쿼리 |
| `language` | 언어 코드 (`ko`, `en`) |
| `channel` | 요청 채널 (cli, web, api) |

#### intent

| 키 | 설명 |
|----|------|
| `intent_label` | 예측 의도 |
| `confidence` | 신뢰도 |
| `candidates` | 후보 의도/점수 |

#### retrieval

| 키 | 설명 |
|----|------|
| `query` | 검색 쿼리 (rewrite 반영) |
| `index` | 사용 인덱스/컬렉션 |
| `method` | bm25/dense/hybrid |
| `top_k` | 조회 k |
| `doc_ids` | 조회 문서 ID 목록 |
| `scores` | 문서 점수 목록 |
| `latency_ms` | 조회 지연 |

#### rerank

| 키 | 설명 |
|----|------|
| `model` | 리랭커 모델 |
| `input_count` | 입력 문서 수 |
| `output_count` | 출력 문서 수 |
| `scores` | 리랭킹 점수 |
| `latency_ms` | 리랭킹 지연 |

#### output

| 키 | 설명 |
|----|------|
| `answer` | 최종 답변 |
| `citations` | 사용 문서/근거 |
| `tokens_in` | 입력 토큰 |
| `tokens_out` | 출력 토큰 |
| `latency_ms` | 생성 지연 |

- `citations` 미기록 시 `output.citation_count`는 0으로 계산됨.
- 인용을 사용하지 않는 시스템은 `output.citation_count` 임계값을 0으로 낮추거나 제거 권장.
#### Retriever 기반 컨텍스트 자동 생성

- `--retriever`가 활성화되면 contexts가 비어있는 테스트 케이스에 한해 자동으로 컨텍스트를 채웁니다.
- `--retriever-docs`는 `.json/.jsonl/.txt`를 지원하며 `documents` 배열 또는 줄 단위 텍스트를 허용합니다.
- 검색 결과는 `StageEvent(stage_type=retrieval)`의 `doc_ids/scores/top_k`로 기록됩니다.
- `doc_ids`는 문서의 `doc_id`를 우선 사용하고, 없으면 `doc_<index>`로 대체합니다.
- `scores`가 없다면 `retrieval.avg_score`/`retrieval.score_gap` 계산은 건너뜁니다.
- `retrieval_time_ms`는 선택 필드이며 R2/R3에서 채우는 것을 기본으로 합니다.

### 3.4 단계 예시 (필수 4단계)

```json
{
  "run_id": "run_20260103_001",
  "stage_events": [
    {
      "stage_id": "stg_system_prompt_01",
      "stage_type": "system_prompt",
      "stage_name": "system_prompt_v1",
      "attributes": {"prompt_id": "sys-01", "checksum": "abc123"}
    },
    {
      "stage_id": "stg_input_01",
      "parent_stage_id": "stg_system_prompt_01",
      "stage_type": "input",
      "stage_name": "user_query",
      "attributes": {"query": "보험 약관 요약해줘", "language": "ko"}
    },
    {
      "stage_id": "stg_retrieval_01",
      "parent_stage_id": "stg_input_01",
      "stage_type": "retrieval",
      "stage_name": "hybrid_retriever",
      "attributes": {"top_k": 8, "doc_ids": ["doc-1", "doc-7"], "latency_ms": 42}
    },
    {
      "stage_id": "stg_output_01",
      "parent_stage_id": "stg_retrieval_01",
      "stage_type": "output",
      "stage_name": "final_answer",
      "attributes": {"answer": "...", "tokens_in": 900, "tokens_out": 210}
    }
  ]
}
```

### 3.5 stage_events.jsonl 샘플

```jsonl
{"run_id":"run_20260103_001","stage_id":"stg_sys_01","stage_type":"system_prompt","stage_name":"system_prompt_v1","attributes":{"prompt_id":"sys-01","checksum":"abc123"}}
{"run_id":"run_20260103_001","stage_id":"stg_input_01","parent_stage_id":"stg_sys_01","stage_type":"input","stage_name":"user_query","attributes":{"query":"보험 약관 요약해줘","language":"ko"}}
{"run_id":"run_20260103_001","stage_id":"stg_retrieval_01","parent_stage_id":"stg_input_01","stage_type":"retrieval","stage_name":"hybrid_retriever","attributes":{"top_k":5,"doc_ids":["doc-1","doc-7"],"scores":[0.91,0.72]}}
{"run_id":"run_20260103_001","stage_id":"stg_output_01","parent_stage_id":"stg_retrieval_01","stage_type":"output","stage_name":"final_answer","attributes":{"answer":"...","citations":["doc-1","doc-7"],"tokens_in":900,"tokens_out":210}}
```

---

## 4. 단계별 평가 지표

### 4.1 데이터셋 있음 (정답/관련 문서 존재)

| 단계 | 주요 지표 | 요구 조건 |
|------|----------|-----------|
| system_prompt | Prompt coverage, checksum drift, policy compliance | prompt_id/checksum |
| input | Language accuracy, query length/dup ratio | 라벨/로그 |
| retrieval | Recall@K, MRR, Hit@K | 관련 문서 |
| output | Faithfulness, Answer Correctness | 정답/근거 |
| E2E | Pass Rate, 평균 점수 | 테스트셋 |

> 선택 단계는 4.3 템플릿에 따라 필요한 항목만 평가합니다.

### 4.2 데이터셋 없음 (로그 기반)

| 단계 | 대체 지표 | 설명 |
|------|----------|------|
| system_prompt | Prompt drift/변경률 | 프롬프트 일관성 |
| input | 길이 분포, 중복 비율 | 입력 이상치 탐지 |
| retrieval | Empty/Low-score 비율, Score 분산 | 품질 이상 징후 |
| output | LLM Judge (faithfulness/answerability) | 약지도 평가 |
| E2E | 사용자 피드백, 응답 길이/지연 | 운영 로그 |

> 선택 단계는 로그 기반 품질 지표를 중심으로 점검합니다.

### 4.3 StageMetric 템플릿 (권장)

| stage_type | metric_name 예시 | 필요 입력 |
|------------|------------------|----------|
| system_prompt | `system_prompt.drift_rate`, `system_prompt.policy_violation_rate` | prompt_id/checksum |
| input | `input.query_length`, `input.dup_ratio` | query 로그 |
| language_detection | `language_detection.accuracy`, `language_detection.confidence` | label/confidence |
| intent | `intent.accuracy`, `intent.confidence` | label/confidence |
| rewrite | `rewrite.delta_ratio`, `rewrite.term_coverage` | 원문/리라이트 |
| expansion | `expansion.query_count`, `expansion.coverage_gain` | 확장 쿼리 |
| decomposition | `decomposition.subquery_count`, `decomposition.coverage_gain` | 서브쿼리 |
| self_query | `self_query.parse_success`, `self_query.filter_coverage` | 필터 표현식/라벨 |
| hypothetical_doc | `hypo.similarity`, `hypo.coverage_gain` | HyDE 결과 |
| query_translation | `query_translation.consistency`, `query_translation.language_match` | 원문/번역 |
| retrieval | `retrieval.recall_at_k`, `retrieval.precision_at_k`, `retrieval.result_count`, `retrieval.avg_score`, `retrieval.score_gap`, `retrieval.latency_ms` | doc_ids/scores |
| metadata_filter | `metadata_filter.reduction_ratio`, `metadata_filter.hit_rate` | before/after 카운트 |
| iterative_retrieval | `iterative.hops`, `iterative.recall_gain` | hop 데이터 |
| fusion | `fusion.overlap_ratio`, `fusion.score_gain` | 결합 결과 |
| rerank | `rerank.ndcg_at_k`, `rerank.score_gap`, `rerank.keep_rate`, `rerank.avg_score`, `rerank.latency_ms` | scores/ranks |
| filter | `filter.filtered_ratio` | before/after 카운트 |
| compression | `compression.ratio`, `compression.retained_evidence` | token/citation |
| contextualization | `contextualization.added_tokens`, `contextualization.citation_hit_rate` | added context |
| context_assembly | `context.size`, `context.token_budget_util` | assembled context |
| knowledge_graph | `kg.hit_rate`, `kg.coverage` | entity/edge hits |
| answer_synthesis | `answer_synthesis.merge_count`, `answer_synthesis.consistency` | partial outputs |
| grounding_check | `grounding.grounded_ratio` | citation 매칭 |
| answer_validation | `answer_validation.pass_rate` | 검증 결과 |
| output | `output.faithfulness`, `output.token_ratio`, `output.citation_count`, `output.latency_ms` | answer/tokens |
| safety_check | `safety_check.violation_rate`, `safety_check.block_rate` | safety 결과 |
| postprocess | `postprocess.violation_rate` | safety 결과 |
| feedback | `feedback.user_score`, `feedback.followup_rate` | 피드백 로그 |
| document_ingestion | `document_ingestion.doc_count`, `document_ingestion.error_rate` | ingest 로그 |
| chunking | `chunking.avg_chunk_size`, `chunking.overlap_ratio` | chunk metadata |
| document_embedding | `document_embedding.throughput`, `document_embedding.error_rate` | embedding 로그 |
| indexing | `indexing.upsert_rate`, `indexing.latency_ms` | index 로그 |

**임계값/패스 규칙**
- 기본 규칙: `score >= threshold` 이면 pass
- `*.latency_ms`는 `score <= threshold` 기준으로 판정
- 기본 임계값(권장):
  - `retrieval.precision_at_k` ≥ 0.20
  - `retrieval.recall_at_k` ≥ 0.60
  - `retrieval.result_count` ≥ 1
  - `retrieval.latency_ms` ≤ 500
  - `rerank.keep_rate` ≥ 0.25
  - `rerank.score_gap` ≥ 0.10
  - `rerank.latency_ms` ≤ 800
  - `output.citation_count` ≥ 1
  - `output.latency_ms` ≤ 3000
- 서비스/프로젝트별로 JSON 매핑을 통해 덮어쓰기 권장
  - 템플릿: `config/stage_metric_thresholds.json`
  - `default` + `profiles.{profile}` 구조로 프로필 오버라이드 지원

**StageMetric 액션 플레이북**
- StageMetric 기반 개선 액션은 YAML로 외부화하여 정책 조정 가능
  - 템플릿: `config/stage_metric_playbook.yaml`
  - 커버리지: `retrieval.avg_score/score_gap/latency_ms`, `rerank.avg_score/latency_ms`,
    `output.token_ratio/output.citation_count` 등 로그 기반 지표 포함

### 4.4 단계별 개선 가이드 연결 (예시)

| 관측 패턴 | 원인 추정 | 권장 액션 |
|-----------|----------|-----------|
| Recall@K 급락 | 쿼리/임베딩 품질 | rewrite/embedding 재학습 |
| rerank score gap 낮음 | 리랭커 약함 | 리랭커 교체/튜닝 |
| output faithfulness 낮음 | 근거 부정합 | context slicing, citation 강제 |

---

## 5. EvalVault 저장 구조 제안

### 5.1 Domain Entities (신규)

```
domain/entities/
└── stage.py              # StageEvent, StageMetric, StagePayloadRef, StageSummary
```

- `StageEvent`: 단계별 실행 데이터 (공통 스키마)
- `StageMetric`: 단계별 평가 결과 (metric_name, score, evidence)
- `StageSummary`: 필수 단계 누락/집계 요약

> 기존 `RAGTraceData`는 retrieval/generation 단계 데이터로 유지하고, StageEvent로
> 확장해 Phoenix trace 또는 로컬 저장에 동시 활용하는 방식 권장.

### 5.2 Ports

```
ports/outbound/
└── stage_storage_port.py   # StageEvent/StageMetric 저장/조회
```

- `StageStoragePort.save_stage_event()` / `list_stage_events(run_id)`
- `StageStoragePort.save_stage_metrics()` / `list_stage_metrics(run_id)`

> payload 분리는 향후 필요 시 별도 포트로 분리하는 것을 권장합니다.

### 5.3 Adapters

```
adapters/outbound/storage/
├── sqlite_stage_adapter.py   # SQLite 저장
└── postgres_stage_adapter.py # (옵션) PostgreSQL

adapters/outbound/payload/
├── file_payload_store.py     # 로컬 파일 기반
└── sqlite_payload_store.py   # SQLite blob
```

### 5.4 Storage Schema (SQLite)

```sql
CREATE TABLE stage_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  stage_id TEXT NOT NULL,
  parent_stage_id TEXT,
  stage_type TEXT NOT NULL,
  stage_name TEXT,
  status TEXT,
  attempt INTEGER DEFAULT 1,
  started_at TIMESTAMP,
  finished_at TIMESTAMP,
  duration_ms REAL,
  input_ref TEXT,
  output_ref TEXT,
  attributes TEXT,
  metadata TEXT,
  trace_id TEXT,
  span_id TEXT
);

CREATE TABLE stage_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  stage_id TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  score REAL NOT NULL,
  threshold REAL,
  evidence TEXT
);
```

### 5.5 EvaluationRun과의 연결

- `EvaluationRun.run_id` → `stage_events.run_id`로 1:N 매핑.
- `TestCaseResult.test_case_id`를 stage `metadata`에 저장해 세밀한 매핑 가능.
- StageMetrics는 ImprovementGuideService의 패턴 탐지 입력으로 활용 가능.

---

## 6. 수집·분석 운영 흐름 {#6-수집·분석-운영-흐름}

1. **수집**: 각 단계에서 `StageEvent`를 기록하고, 대용량 데이터는 payload store로 분리.
   - CLI(JSONL): `evalvault run <dataset> --stage-events stage_events.jsonl`
   - CLI(SQLite): `evalvault run <dataset> --db data/db/evalvault.db --stage-store`
2. **저장**: JSONL로 수집한 경우 `StageStoragePort`를 통해 SQLite에 적재.
   - CLI: `evalvault stage ingest stage_events.jsonl --db data/db/evalvault.db`
3. **계산**: StageMetric 계산 로직으로 메트릭 생성
   - CLI: `evalvault stage compute-metrics <run_id> --thresholds-json config/stage_metric_thresholds.json`
   - `--thresholds-json` 미지정 시 템플릿 파일이 존재하면 자동 적용
   - `--thresholds-profile` 미지정 시 `Settings.evalvault_profile` 사용
4. **분석/리포트**: `run_id` 기준 StageEvent/Metric을 로드하여 단계별 진단 실행.
   - CLI: `evalvault stage report <run_id> --db data/db/evalvault.db`
   - `--playbook`으로 개선 액션 템플릿 교체 가능
5. **개선 가이드**: ImprovementGuideService에 `stage_metrics`를 전달해 규칙 기반 가이드 생성.
   - 액션 템플릿: `config/stage_metric_playbook.yaml`
6. **리포트**: E2E 메트릭 + 단계별 메트릭을 합산해 개선 리포트 생성.

> 오프라인 인덱싱(ingestion/chunking/embedding/indexing)은 별도 `run_id`로 기록하고,
> `metadata.pipeline_type=ingestion`처럼 구분 태그를 두는 것을 권장합니다.

**R1 스모크 스크립트**
- `scripts/tests/run_retriever_stage_report_smoke.sh`: retriever → stage report까지 단일 흐름을 점검하는 스모크 스크립트

**R1 완료 보고서**
- `docs/internal/reports/R1_COMPLETION_REPORT.md`: R1 구현/검증 결과 요약

---

## 7. MVP 구현 순서

1. **StageEvent 스키마 확정 + JSONL ingest**
   - CLI 또는 SDK에서 stage_events.jsonl 저장
2. **SQLite stage_events 테이블 추가**
   - 조회 기반 단계별 통계 리포트 제공
3. **StageMetric 계산기 추가**
   - retrieval/rerank/output 중심으로 시작 (기본 제공)
4. **Improvement Guide 연계**
   - StageMetric 기반 룰 확장

## 참고 문서

- [ARCHITECTURE.md](../../architecture/ARCHITECTURE.md): 전체 아키텍처
- [ROADMAP.md](../../status/ROADMAP.md): 개발 로드맵
- [USER_GUIDE.md](../../guides/USER_GUIDE.md): 사용자 가이드
- [tutorials/01-quickstart.md](../../tutorials/01-quickstart.md): 튜토리얼

---

**문서 끝**
