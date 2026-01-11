# 07. 고급 기능 및 확장(Advanced)

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: EvalVault의 차별점(학습/관측/표준 연동/고급 검색/벤치마크)을 “기능 카탈로그 + 안전한 사용법”으로 정리한다.
- **독자**: 중급~고급 내부 개발자
- **선행 지식**: 기본 실행/산출물(run_id) 흐름 이해(03장), Hexagonal 경계(02장)

---

## TL;DR

- Domain Memory는 “평가 결과 → 지식(사실/패턴/행동) 축적 → 다음 실행에서 재사용”을 구현한다.
- 관측성은 `run_id`를 중심으로 **StageEvent/StageMetric/Trace**를 연결해 “왜(원인) + 어디(단계) + 얼마나(성능)”를 남긴다.
- Open RAG Trace는 OpenTelemetry를 사용할 때도/안 쓸 때도 안전하게 동작하는 **표준 계측 어댑터**를 제공한다.
- 검색기 변화(Hybrid/RRF/Embedding 비교)는 분석 DAG의 의도/템플릿으로 자동화되어 있어 “느낌”이 아니라 “벤치마크/비교”로 검증한다.

---

## 1) Domain Memory (학습)

### 1.1 무엇을 해결하나

- 평가 결과가 휘발되는 문제(“이번엔 왜 좋았지?”)를 줄이고, 다음 실행에서 **threshold/컨텍스트/행동 레시피**로 재사용한다.
- “정답률이 떨어졌다” 수준이 아니라, 도메인별로 **어떤 메트릭이 신뢰할 만한지(신뢰도)**를 축적하여 평가 기준을 보정한다.

### 1.2 핵심 개념(레이어/동학)

Domain Memory는 다음을 분리한다.

- **레이어(Functions)**
  - Factual: 사실(SPO 트리플) 축적
  - Experiential: 학습된 패턴/신뢰도(예: 타입별 신뢰도)
  - Behavior: 재사용 가능한 행동(action sequence)
  - Working: 현재 세션 컨텍스트
- **동학(Dynamics)**
  - Formation: 평가 결과에서 추출하여 저장
  - Evolution: 통합/망각/감쇠(메모리 유지보수)
  - Retrieval: 키워드/FTS/하이브리드로 재사용

> **NOTE**: Domain Memory의 “포트 인터페이스”는 Phase별로 확장될 수 있으므로, 실제 구현 가능 범위는 어댑터(예: SQLite) 구현을 기준으로 판단한다.

### 1.3 최소 사용 예제(운영 관점)

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --use-domain-memory \
  --memory-domain insurance \
  --memory-language ko
```

- 위 플래그의 의미는 “도메인 메모리를 켠다”가 아니라,
  - **저장소**: `Settings.evalvault_memory_db_path` (기본: `data/db/evalvault_memory.db`)
  - **도메인 분리**: `domain=insurance`, `language=ko`로 네임스페이스 분리
  - **재사용 경로**: threshold 조정 / fact 기반 컨텍스트 보강 / 행동 추천
  로 이어지는 것을 의미한다.

### 1.4 내부 동작(코드 기반)

#### A) Formation: 평가 결과 → 메모리 형성

- 평가 완료 후 훅 진입점: `src/evalvault/domain/services/domain_learning_hook.py`
  - `DomainLearningHook.on_evaluation_complete(...)`
  - 내부에서
    - `extract_and_save_facts(...)`
    - `extract_and_save_patterns(...)`
    - `extract_and_save_behaviors(...)`
    를 순서대로 호출한다.

- Evolution 실행(메모리 정리) 진입점: 같은 파일의
  - `DomainLearningHook.run_evolution(domain, language)`
  - `consolidate_facts`, `forget_obsolete`, `decay_verification_scores`를 호출한다.

#### B) Retrieval/재사용: 다음 실행에서 무엇이 바뀌나

- threshold 보정(신뢰도 기반): `src/evalvault/domain/services/memory_aware_evaluator.py`
  - `MemoryAwareEvaluator.evaluate_with_memory(...)`
  - `MemoryInsightPort.get_aggregated_reliability(domain, language)` 결과를 이용해
    `_adjust_by_reliability(...)`에서 메트릭별 threshold를 상향/하향한다.

- 컨텍스트 보강(facts 주입): 같은 파일의
  - `MemoryAwareEvaluator.augment_context_with_facts(...)`
  - 내부에서 `MemoryInsightPort.search_facts(query, domain, language, limit)` 호출 후,
    `[관련 사실]` 헤더와 `- subject predicate object` 리스트를 기존 컨텍스트에 덧붙인다.

- 행동 재사용(action sequence): `src/evalvault/domain/services/memory_based_analysis.py`
  - `MemoryBasedAnalysis.apply_successful_behaviors(...)`
  - `MemoryInsightPort.search_behaviors(context, domain, language)` 결과 중 `success_rate`로 필터링한다.

#### C) 저장소/스키마: 무엇을 어떻게 저장하나

- 저장 어댑터(로컬 기본): `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py`
  - `SQLiteDomainMemoryAdapter(db_path="data/db/evalvault_memory.db")`
  - 초기화 시 스키마 실행: `domain_memory_schema.sql`
  - FTS5 동기화 안정화: `_rebuild_fts_indexes()`가 트리거/테이블을 드롭 후 재구축한다.
    - “INSERT OR REPLACE로 rowid 동기화가 깨질 수 있음”을 코드 주석으로 명시한다.

- 스키마 근거: `src/evalvault/adapters/outbound/domain_memory/domain_memory_schema.sql`
  - `factual_facts`, `learning_memories`, `behavior_entries`, `memory_contexts`
  - FTS5: `facts_fts`, `behaviors_fts` (트리거 기반 동기화 정의)
  - Phase 5 확장: `fact_kg_bindings`, `fact_hierarchy`

- 엔티티 정의 근거: `src/evalvault/domain/entities/memory.py`
  - `FactualFact`는 KG 연결(`kg_entity_id`, `kg_relation_type`)과 계층(`parent_fact_id`, `abstraction_level`)을 지원한다.

### 1.5 설계 근거 / 트레이드오프

- “지식을 구조화”하면서도, 완전한 지식 그래프를 강제하지 않는다.
  - 최소 단위는 `FactualFact(SPO)`이며, KG/Hierarchy는 Phase 5 확장으로 둔다.
- FTS5는 빠르지만 “정합성 유지”가 어렵다.
  - 스키마는 트리거 기반 동기화를 제공하나, 실제 구현은 `_rebuild_fts_indexes()` 같은 방어 로직이 필요하다.

### 1.6 운영/테스트/디버깅 팁

- “검색 결과가 이상하다(예: 저장은 됐는데 검색이 안 된다)” → FTS 인덱스 재빌드가 필요할 수 있다.
  - 근거: `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py`의 `rebuild_fts_indexes()`
- “threshold가 왜 바뀌었지?” → 신뢰도 집계/보정 로직을 확인한다.
  - 근거: `src/evalvault/domain/services/memory_aware_evaluator.py`의 `_adjust_by_reliability(...)`

---

## 2) 관측성(Observability) & Phoenix

### 2.1 목적

- “점수”만 남기지 않고, **단계별(Stage) 이벤트/메트릭/트레이스**를 남겨 원인 분석(디버깅)과 성능 튜닝을 가능하게 한다.

### 2.2 내부 동작(코드 기반)

- StageEvent 생성: `src/evalvault/domain/services/stage_event_builder.py`
  - `StageEventBuilder.build_for_run(run, prompt_metadata, retrieval_metadata)`
  - test-case 단위로
    - `stage_type="input"` (query)
    - `stage_type="retrieval"` (doc_ids/top_k/scores + `retrieval_time_ms` 등)
    - `stage_type="output"` (answer/citations/tokens_used + duration)
    를 만든다.
  - 성능 속성(옵션): `index_build_time_ms`, `cache_hit`, `batch_size`, `total_docs_searched`, `index_size`,
    `faiss_gpu_active`, `graph_nodes`, `graph_edges`, `subgraph_size` 등은 `retrieval_metadata`에 있을 때만 주입된다.

- StageMetric 계산: `src/evalvault/domain/services/stage_metric_service.py`
  - `StageMetricService.build_metrics(events, relevance_map, thresholds)`
  - 기본 임계값: `DEFAULT_STAGE_THRESHOLDS`에 정의(예: `retrieval.latency_ms=500`, `output.latency_ms=3000`).

- Phoenix 전송(Tracker): `src/evalvault/adapters/outbound/tracker/phoenix_adapter.py`
  - `PhoenixAdapter`는 OTLP HTTP exporter를 사용하여 Phoenix endpoint로 span을 보낸다.
  - OpenTelemetry 의존성은 optional이며, 없으면 `uv sync --extra phoenix`를 요구한다.

- Phoenix 계측(자동):
  - 설정/토글: `src/evalvault/config/settings.py` (`phoenix_enabled`, `phoenix_endpoint`, `phoenix_sample_rate`, `phoenix_api_token`)
  - CLI 통합: `src/evalvault/config/phoenix_support.py`의 `ensure_phoenix_instrumentation(settings, force=...)`
  - OTEL SDK 설정: `src/evalvault/config/instrumentation.py`

### 2.3 로컬 실행(Compose)

- Phoenix + OTel Collector: `docker-compose.phoenix.yaml`
  - Phoenix UI/ingest: `6006`
  - Collector OTLP: `4317`(gRPC), `4318`(HTTP)
- Collector 파이프라인: `scripts/dev/otel-collector-config.yaml`
  - `spec.version=0.1` attribute를 traces pipeline에 삽입한다.

---

## 3) Open RAG Trace (표준 연동)

### 3.1 목적

- EvalVault 내부뿐 아니라 “외부 RAG 시스템”도 동일한 스키마로 계측하여 비교/분석 가능한 상태로 만든다.

### 3.2 구현 포인트(코드 기반)

- 안전한 표준 어댑터(OTel 없어도 동작): `src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py`
  - `OpenRagTraceAdapter`는 OTel이 없으면 `_NoOpSpan`으로 동작한다.
  - 표준 속성: `spec.version`, `rag.module` (config: `OpenRagTraceConfig`)

- 속성 빌더(OTel-safe serialization): `src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py`
  - `build_retrieval_attributes(...)`, `build_llm_attributes(...)`, `build_eval_attributes(...)`
  - OTel 속성 제한(스칼라/스칼라 배열)을 넘는 값은 JSON 문자열로 직렬화한다.

---

## 4) 고급 검색기/분석: Hybrid / 비교 / 벤치마크

### 4.1 “검색기 변경”을 어떻게 검증할까

- “좋아진 것 같다”를 금지하고, 아래 두 레이어에서 검증한다.
  1) **StageMetric**: `retrieval.*` (정확도/레이턴시/결과 수)
  2) **분석 DAG**: 검색 방식 비교/벤치마크 의도 템플릿

### 4.2 분석 DAG 근거(코드 기반)

- 의도/엔티티: `src/evalvault/domain/entities/analysis_pipeline.py`
  - `AnalysisIntent`에 `COMPARE_SEARCH_METHODS`, `BENCHMARK_RETRIEVAL` 등이 정의된다.

- 템플릿 레지스트리: `src/evalvault/domain/services/pipeline_template_registry.py`
  - 비교 템플릿은 `bm25_searcher`, `embedding_searcher`, `hybrid_rrf`, `hybrid_weighted`, `search_comparator` 등을 연결한다.

- 모듈 등록(중앙 허브): `src/evalvault/adapters/outbound/analysis/pipeline_factory.py`
  - `RetrievalBenchmarkModule`, `SearchComparatorModule`, `HybridRRFModule`, `HybridWeightedModule` 등이 등록되어야 실제 실행된다.

- 아티팩트 저장(재현성): `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
  - 노드별 JSON + `artifacts/<prefix>/index.json`을 생성한다(`write_pipeline_artifacts`).

---

## 5) 성능 벤치마크(스크립트 기반)

- Dense retriever R3 스모크(퍼센타일 포함): `scripts/perf/r3_dense_smoke.py`
  - 출력: JSONL 이벤트(`r3.smoke.index`, `r3.smoke.search`, `r3.smoke.summary`)
  - p50/p95/p99: `search_ms_p50`, `search_ms_p95`, `search_ms_p99`

```bash
python scripts/perf/r3_dense_smoke.py --documents 1000 --queries 200 --top-k 5 --mock-embeddings
```

> **NOTE**: 이 스크립트는 EvalVault “운영 CLI”와 별개로, 성능 실험을 빠르게 반복하기 위한 개발자 도구다.

---

## Evidence

- Domain Memory(형성/재사용)
  - `src/evalvault/domain/services/domain_learning_hook.py`
  - `src/evalvault/domain/services/memory_aware_evaluator.py`
  - `src/evalvault/domain/services/memory_based_analysis.py`
  - `src/evalvault/ports/outbound/domain_memory_port.py`
  - `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py`
  - `src/evalvault/adapters/outbound/domain_memory/domain_memory_schema.sql`
  - `src/evalvault/domain/entities/memory.py`

- 관측성(Stage)
  - `src/evalvault/domain/services/stage_event_builder.py`
  - `src/evalvault/domain/services/stage_metric_service.py`

- Phoenix/OTel
  - `src/evalvault/adapters/outbound/tracker/phoenix_adapter.py`
  - `src/evalvault/config/settings.py`
  - `src/evalvault/config/phoenix_support.py`
  - `src/evalvault/config/instrumentation.py`
  - `docker-compose.phoenix.yaml`
  - `scripts/dev/otel-collector-config.yaml`

- Open RAG Trace
  - `src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py`
  - `src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py`

- 분석 DAG/검색 비교
  - `src/evalvault/domain/entities/analysis_pipeline.py`
  - `src/evalvault/domain/services/pipeline_template_registry.py`
  - `src/evalvault/adapters/outbound/analysis/pipeline_factory.py`
  - `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`

- 성능 스모크
  - `scripts/perf/r3_dense_smoke.py`

---

## 전문가 관점 체크리스트

- [ ] 고급 기능 설명이 “실행 가능”한 최소 예제/근거 경로를 제공하는가
- [ ] 재사용/학습 기능이 “어디서 저장되고 어디서 읽히는지”가 명확한가
- [ ] 관측성 지표가 점수/트레이스/아티팩트와 연결되는가
- [ ] OTel 속성 제약(스칼라/배열)과 직렬화 방식을 문서가 숨기지 않는가

---

## 향후 변경 시 업데이트 가이드

- Domain Memory 포트/스키마를 확장했다면:
  - `src/evalvault/ports/outbound/domain_memory_port.py`에 인터페이스 추가 여부
  - `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py` 구현/마이그레이션 추가 여부
  - `src/evalvault/adapters/outbound/domain_memory/domain_memory_schema.sql` 테이블/인덱스/FTS 갱신 여부
  를 확인하고, 이 장의 **1.4(C 저장소/스키마)**에 근거를 갱신한다.

- 새로운 Stage 타입/지표를 추가했다면:
  - `src/evalvault/domain/services/stage_event_builder.py` (attributes/duration_ms)
  - `src/evalvault/domain/services/stage_metric_service.py` (metric_name, DEFAULT_STAGE_THRESHOLDS)
  를 근거로, 이 장의 **2.2(내부 동작)**에 추가한다.

- Open RAG Trace의 스펙 버전/필드가 바뀌었다면:
  - `src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py` (`spec.version`, `rag.module`)
  - `scripts/dev/otel-collector-config.yaml` (spec.version 삽입)
  을 함께 업데이트하고, 이 장의 **3장**을 수정한다.

- 분석 DAG에 새 의도/템플릿/모듈을 추가했다면:
  - `src/evalvault/domain/entities/analysis_pipeline.py` (AnalysisIntent)
  - `src/evalvault/domain/services/pipeline_template_registry.py` (템플릿)
  - `src/evalvault/adapters/outbound/analysis/pipeline_factory.py` (모듈 등록)
  을 근거로 이 장의 **4장**을 업데이트한다.
