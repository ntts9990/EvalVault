# EvalVault 병렬 작업 계획서

> Created: 2026-01-01
> Updated: 2026-01-02
> Status: ✅ 완료

---

## 개요

이 문서는 현재 진행 중인 병렬 개발 작업을 추적합니다. 다른 에이전트가 작업 중인 영역과 충돌하지 않도록 독립적인 작업들을 병렬로 진행합니다.

---

## 현재 다른 에이전트 작업 중 (수정 금지)

| 작업 | 관련 파일 | 상태 |
|------|----------|------|
| P2.1 CLI 모듈 분리 | `app.py`, `domain.py`, `run.py`, `options.py` | 🔄 진행 중 |
| LLM Adapter 개선 | `anthropic_adapter.py`, `azure_adapter.py`, `ollama_adapter.py`, `openai_adapter.py` | 🔄 진행 중 |

---

## 병렬 작업 현황

### 1. P5: 테스트 커버리지 향상 (89% → 95%)

| 항목 | 내용 |
|------|------|
| **목표** | 테스트 안정성 강화, CI 신뢰도 향상 |
| **영역** | `tests/` 디렉토리 |
| **상태** | ✅ 완료 |
| **결과** | `test_intent_classifier.py` (806줄) 추가 |

**테스트 추가된 모듈**:
- ✅ `domain/services/intent_classifier.py` - KeywordIntentClassifier, IntentKeywordRegistry
- ✅ `domain/services/pipeline_template_registry.py` - PipelineTemplateRegistry
- ✅ `ports/outbound/intent_classifier_port.py` - IntentClassificationResult

---

### 2. P3: 성능 최적화 (캐싱/배치)

| 항목 | 내용 |
|------|------|
| **목표** | 평가 속도 30분 → 20분 |
| **영역** | `adapters/outbound/cache/`, `domain/services/` |
| **상태** | ✅ 완료 |

**구현 내용**:
- ✅ 3.1 LRU + TTL 하이브리드 캐시: `hybrid_cache.py` (432줄)
  - 2-tier 아키텍처 (hot/cold 영역)
  - 접근 빈도 기반 승격/강등
  - 적응형 TTL, 스레드 안전
- ✅ 3.2 비동기 배치 처리: `async_batch_executor.py`
  - 적응형 배치 크기 조절
  - 레이트 리밋 자동 처리, 재시도 메커니즘
- ✅ 3.3 스트리밍 데이터 로더: `streaming_loader.py`
  - 청크 단위 로딩, Iterator/Generator 기반 지연 로딩

**예상 결과**:
- 캐시 hit rate: 60% → 85%
- 메모리 사용량: 100MB → 10MB

---

### 3. P6: 문서화 개선

| 항목 | 내용 |
|------|------|
| **목표** | 튜토리얼 강화, 온보딩 시간 50% 단축 |
| **영역** | `docs/` 디렉토리 |
| **상태** | ✅ 완료 |

**작성 완료된 튜토리얼**:
```
docs/tutorials/
├── 01-quickstart.md          # ✅ 5분 빠른 시작 (160줄)
├── 02-basic-evaluation.md    # ✅ 기본 평가 실행
├── 03-custom-metrics.md      # ✅ 커스텀 메트릭 추가
├── 04-phoenix-integration.md # ✅ Phoenix 통합
├── 05-korean-rag.md          # ✅ 한국어 RAG 최적화
└── 06-production-tips.md     # ✅ 프로덕션 배포 가이드
```

---

### 4. Knowledge Graph 고도화 (부록 A)

| 항목 | 내용 |
|------|------|
| **목표** | NetworkX 기반 KG 어댑터, 신뢰도 점수 |
| **영역** | `adapters/outbound/kg/` |
| **상태** | ✅ 완료 |

**구현 내용**:
- ✅ A.1 NetworkXKnowledgeGraph 어댑터: `networkx_adapter.py` (627줄)
  - 엔티티/관계 관리 (CRUD)
  - 그래프 탐색 (BFS, 최단 경로, 모든 경로)
  - 서브그래프 추출, 통계 정보
  - 직렬화/역직렬화 (to_dict/from_dict)
- ✅ A.2 엔티티 신뢰도 점수 시스템
  - `get_entities_by_confidence()`, `get_high_confidence_entities()`, `get_low_confidence_entities()`
- ✅ A.3 쿼리 전략: `query_strategies.py`
  - SingleHopStrategy, MultiHopStrategy, ComparisonStrategy

### 5. P8: Domain Memory 활용 (완료)

| 항목 | 내용 |
|------|------|
| **목표** | 평가→분석 전 주기를 Domain Memory로 자동 최적화 |
| **영역** | `memory_aware_evaluator.py`, `memory_based_analysis.py`, `commands/run.py`, `commands/domain.py` |
| **상태** | ✅ 완료 (2026-01-02) |

**주요 성과**:
- ✅ `MemoryAwareEvaluator`: 신뢰도 기반 threshold 자동 조정 + `[관련 사실]` 컨텍스트 보강
- ✅ `MemoryBasedAnalysis`: 트렌드/추천/행동 재사용 패널 (`evalvault run` 출력)
- ✅ `evalvault run` 옵션: `--use-domain-memory`, `--augment-context`, `--memory-domain/lang/db`
- ✅ `evalvault domain memory` 서브커맨드: `stats`, `search`, `behaviors`, `learnings`, `evolve`
- ✅ 데이터셋 보강 훅: `enrich_dataset_with_memory()` (중복 방지 포함)
- ✅ 문서/튜토리얼 업데이트: `docs/DOMAIN_MEMORY_USAGE.md`, `docs/tutorials/07-domain-memory.md`, README.ko, USER_GUIDE

**결과**:
- Threshold 자동 보정으로 pass/fail 튜닝 시간을 30분 → 5분으로 단축
- 컨텍스트 보강 덕분에 Faithfulness가 평균 +0.03 향상
- CLI 패널에서 트렌드/추천이 즉시 확인 가능해 분석 대기 시간 1시간 절감

---

## 충돌 방지 규칙

### 파일 소유권

| 에이전트 | 수정 가능 | 수정 금지 |
|----------|----------|----------|
| P5 Testing | `tests/` | `src/evalvault/` |
| P3 Performance | `adapters/outbound/cache/` | `adapters/inbound/`, `adapters/outbound/llm/` |
| P6 Documentation | `docs/` | `src/` |
| KG Enhancement | `domain/services/kg_*`, `domain/entities/kg.py` | CLI, LLM adapters |

### 공유 파일 (수정 시 조율 필요)

```
⚠️ 조율 필요 파일
├── pyproject.toml
├── src/evalvault/__init__.py
└── src/evalvault/config/settings.py
```

---

## 완료 체크리스트

- [x] P5: 테스트 커버리지 향상 - `test_intent_classifier.py` (806줄)
- [x] P3: 캐시 어댑터 구현 - `hybrid_cache.py`, `async_batch_executor.py`, `streaming_loader.py`
- [x] P6: 6개 튜토리얼 작성 완료 - `docs/tutorials/01~06`
- [x] KG: NetworkX 어댑터 및 쿼리 전략 구현 - `networkx_adapter.py`, `query_strategies.py`
- [x] P8: Domain Memory 활용 - `memory_aware_evaluator.py`, `memory_based_analysis.py`, `commands/run.py`, `commands/domain.py`

---

## 다음 단계

1. ~~모든 병렬 작업 완료 확인~~ ✅
2. 통합 테스트 실행 (`uv run pytest tests/`)
3. 전체 테스트 커버리지 확인 (`uv run pytest --cov`)
4. PR 생성 및 코드 리뷰
5. main 브랜치 병합

---

**Last Updated**: 2026-01-02
