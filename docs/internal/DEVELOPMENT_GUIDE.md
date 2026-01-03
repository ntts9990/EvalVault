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

---

## 1. 개발 환경 설정

### 1.1 필수 요구사항

- Python 3.12+
- `uv` 패키지 매니저

### 1.2 설치

```bash
# 기본 개발 환경
uv sync --extra dev

# 전체 기능 포함
uv sync --extra dev --extra analysis --extra korean --extra web --extra phoenix
```

### 1.3 Optional Dependencies

| Extra | 패키지 | 용도 |
|-------|--------|------|
| `dev` | pytest, ruff, mypy | 개발 도구 |
| `analysis` | scikit-learn | 통계/NLP 분석 |
| `korean` | kiwipiepy, rank-bm25, sentence-transformers | 한국어 NLP |
| `web` | streamlit, plotly | Web UI |
| `postgres` | psycopg | PostgreSQL 지원 |
| `mlflow` | mlflow | MLflow 트래커 |
| `phoenix` | arize-phoenix, opentelemetry | Phoenix 트레이싱 |

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

상세 범위와 일정은 `docs/internal/PARALLEL_WORK_PLAN.md`에서 관리합니다.

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
| 1.4.0 | 2025-12-30 | Phase 10-13 - Streamlit Web UI |
| 1.3.0 | 2025-12-30 | Phase 9 - Korean RAG Optimization |
| 1.2.0 | 2025-12-29 | Phase 8 - Domain Memory |
| 1.1.0 | 2025-12-29 | Phase 2 NLP + Phase 3 Causal |
| 1.0.0 | 2025-12-28 | OSS Release |

---

## 부록 A: 아키텍처 감사 결과

> 2026-01-01 기준 감사 결과

### A.1 준수 사항

- ✅ Domain 서비스는 Port 인터페이스만 의존
- ✅ 15+ Outbound Port가 `typing.Protocol`로 정의
- ✅ LLM/Storage 어댑터 공통화 완료
- ✅ 분석 파이프라인 경계 명확

### A.2 검증 방법

```bash
# 의존성 방향 검증
rg "from evalvault.adapters" src/evalvault/domain  # 결과: 0

# import cycle 검증
uv run python -c "import evalvault"  # 정상 실행
```

### A.3 남은 과제

- 아키텍처 감사 기준의 미완료 항목 없음
- 개선 작업은 `docs/internal/PARALLEL_WORK_PLAN.md`와 `docs/ROADMAP.md`에서 관리

---

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

## 참고 문서

- [ARCHITECTURE.md](../ARCHITECTURE.md): 전체 아키텍처
- [ROADMAP.md](../ROADMAP.md): 개발 로드맵
- [USER_GUIDE.md](../USER_GUIDE.md): 사용자 가이드
- [tutorials/](../tutorials/): 튜토리얼

---

**문서 끝**
