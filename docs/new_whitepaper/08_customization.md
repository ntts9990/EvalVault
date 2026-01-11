# 08. 커스터마이징(확장) 가이드

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: 내부 개발자가 “새 기능을 추가할 때 어디를 건드려야 하는지”를 빠르게 결정할 수 있게 한다.
- **독자**: 중급 내부 개발자
- **선행 지식**: Hexagonal 구조 이해(02장), 기본 실행/산출물 흐름 이해(03장)

---

## TL;DR

- 새로운 기능은 기본적으로 `domain`의 정책/오케스트레이션에서 시작한다.
- 외부 연동(LLM/DB/Tracker/Tracing)은 `ports` 계약을 확인하고 `adapters`에 구현을 추가한다.
- 분석 확장은 “레거시 분석 서비스(AnalysisService)”와 “DAG 파이프라인”이 공존한다.
  - 새 기능은 기본적으로 **DAG 파이프라인**(의도/템플릿/모듈 등록) 쪽을 우선한다.
- 변경을 넣었다면 “문서(Evidence) + 재현 명령 + 최소 회귀 테스트”까지 함께 고정한다.

---

## 0) 확장 전 체크(결정 트리)

1) **이 로직은 도메인 정책인가?** → `src/evalvault/domain/`에서 시작
- 예: 메트릭 계산/threshold 정책/실패 케이스 정의

2) **외부 시스템과의 통신인가?** → `src/evalvault/ports/` 계약을 먼저
- 예: LLM, DB, Tracer/Tracker, Retriever

3) **표현/입력 계층인가?** → `src/evalvault/adapters/inbound/`에서
- CLI 플래그, API 요청/응답 스키마

---

## 1) 새 메트릭 추가

### 1.1 어디를 읽고 어디를 고치나

- 메트릭 오케스트레이션 근거: `src/evalvault/domain/services/evaluator.py`
  - `RagasEvaluator.METRIC_MAP` (Ragas 기반)
  - `RagasEvaluator.CUSTOM_METRIC_MAP` (커스텀 메트릭)
  - `RagasEvaluator.REFERENCE_REQUIRED_METRICS` (ground_truth 요구)
  - `RagasEvaluator.EMBEDDING_REQUIRED_METRICS` (임베딩 요구)

### 1.2 권장 구현 흐름(체크리스트)

- [ ] 메트릭이 요구하는 입력(예: `ground_truth` 필요 여부, 임베딩 필요 여부)을 명확히 한다.
- [ ] “실행 가능한 최소 fixture”를 만든다(`tests/fixtures/` 또는 기존 fixture 재사용).
- [ ] 도메인별 기본 threshold가 필요한 경우 정책을 한 곳에 모은다.
- [ ] 실패/타임아웃/비용이 큰 메트릭은 “옵션 플래그”로 분리할지 판단한다.

### 1.3 문서 업데이트(이 백서)

- 메트릭이 사용자 표면에 노출되면 `docs/new_whitepaper/04_components.md`와
  `docs/new_whitepaper/09_quality.md`에 “추가된 메트릭/검증 루틴”을 갱신한다.

---

## 2) 새 분석 모듈/노드(DAG 파이프라인) 추가

### 2.1 현재 구조(핵심 근거)

- 포트(계약): `src/evalvault/ports/outbound/analysis_module_port.py`
  - `AnalysisModulePort.execute(...)`, `execute_async(...)`

- 엔티티(의도/노드/DAG): `src/evalvault/domain/entities/analysis_pipeline.py`
  - `AnalysisIntent`, `AnalysisNode`, `AnalysisPipeline`

- 템플릿(의도별 DAG): `src/evalvault/domain/services/pipeline_template_registry.py`
  - 예: `COMPARE_SEARCH_METHODS` 템플릿은 `bm25_searcher`/`embedding_searcher`/`hybrid_rrf`/`hybrid_weighted`를 연결한다.

- 등록(모듈 카탈로그/DI): `src/evalvault/adapters/outbound/analysis/pipeline_factory.py`
  - `build_analysis_pipeline_service(storage, llm_adapter)`에서 모듈을 `register_module`한다.

- CLI 진입점(사용자 표면): `src/evalvault/adapters/inbound/cli/commands/pipeline.py`
  - `evalvault pipeline analyze "<query>"`로 실행된다.

- 산출물(아티팩트 인덱스): `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
  - `write_pipeline_artifacts(...)`가 노드별 JSON과 `index.json`을 만든다.

### 2.2 새 분석 모듈 추가 절차(권장)

1) **모듈 구현**
- `AnalysisModulePort` 규약을 만족하는 모듈(보통 `BaseAnalysisModule` 계열)을 만든다.

2) **모듈 ID/메타데이터 고정**
- `module_id`는 템플릿/리포트/아티팩트 파일명에 영향을 준다.
- `metadata`는 `ModuleCatalog`로 등록되어 템플릿 점검/도구화에 쓰인다.

3) **등록**
- `src/evalvault/adapters/outbound/analysis/pipeline_factory.py`에 등록을 추가한다.
  - 등록 누락 시 `Module not found: <module_id>`로 실패한다(오케스트레이터 동작 근거: `src/evalvault/domain/services/pipeline_orchestrator.py`).

4) **템플릿 연결(선택)**
- 특정 의도에서 자동 실행되길 원하면 `src/evalvault/domain/services/pipeline_template_registry.py`에
  `AnalysisNode(module="<module_id>")`를 추가한다.

5) **아티팩트/리포트 스키마 고정**
- 출력은 `dict[str, Any]`를 기본으로 하고, 원본 결과는 `artifacts/<prefix>/<node_id>.json`로 저장될 수 있다.
- “요약(report) vs 원본(output)”을 분리하는 것이 유지보수에 유리하다.

### 2.3 최소 재현(개발자 UX)

```bash
uv run evalvault pipeline intents
uv run evalvault pipeline templates
uv run evalvault pipeline analyze "검색 방식 비교" --run <RUN_ID>
```

---

## 3) 레거시 분석 서비스(AnalysisService) 확장(주의)

- 레거시 분석 오케스트레이션: `src/evalvault/domain/services/analysis_service.py` (`AnalysisService`)
- 이 경로는 “통계/NLP/인과 분석을 묶는 서비스”로 유용하지만,
  **의도 기반 자동화/아티팩트 인덱싱**은 DAG 파이프라인 쪽이 더 강하다.

> **권장**: 신규 분석 기능은 DAG 파이프라인을 1순위로 고려하고,
> 레거시는 유지보수/호환성 목적이 있을 때만 확장한다.

---

## 4) Domain Memory 확장

### 4.1 어디를 읽고 어디를 고치나

- 포트(계약): `src/evalvault/ports/outbound/domain_memory_port.py`
  - `FactualMemoryPort`, `LearningMemoryPort`, `BehaviorMemoryPort`, `WorkingMemoryPort`
  - 동학 포트: `MemoryEvolutionPort`, `MemoryRetrievalPort`, `MemoryFormationPort` 등

- 엔티티: `src/evalvault/domain/entities/memory.py` (`FactualFact`, `LearningMemory`, `BehaviorEntry`, `DomainMemoryContext`)
- SQLite 구현: `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py`
- 스키마: `src/evalvault/adapters/outbound/domain_memory/domain_memory_schema.sql`

### 4.2 스키마/포트 변경 체크리스트

- [ ] 포트에 새 메서드/새 반환 구조를 추가했다면, SQLite 어댑터에 구현을 추가했는가
- [ ] 테이블/인덱스를 추가했다면, 스키마 SQL에 반영했는가
- [ ] FTS5 관련 변경이 있다면, `_rebuild_fts_indexes()` 동작과 충돌하지 않는가
- [ ] Formation/Evolution/Retrieval 중 어디가 변경 포인트인지 명확히 문서화했는가

---

## 5) Tracer/Tracker(관측성) 연동 추가

### 5.1 “표준 계측(Open RAG Trace)” 확장

- 스팬 생성/속성: `src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py`
- 속성 빌더: `src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py`

규칙:
- OTel 속성은 스칼라/스칼라 배열만 안전하므로, 복합 구조는 JSON 문자열로 보낸다.

### 5.2 Phoenix 연동(OTLP)

- Tracker 구현: `src/evalvault/adapters/outbound/tracker/phoenix_adapter.py` (`PhoenixAdapter`)
- 설정: `src/evalvault/config/settings.py` (phoenix_* 필드)
- CLI 계측 보조: `src/evalvault/config/phoenix_support.py` (`ensure_phoenix_instrumentation`)

---

## 6) CLI 옵션 추가

- 루트 앱: `src/evalvault/adapters/inbound/cli/app.py`
- 각 명령: `src/evalvault/adapters/inbound/cli/commands/` 하위

원칙:
- 옵션은 “도메인 정책”이 아니라 “도메인 정책을 선택/구성하는 입력”이어야 한다.
- 파라미터가 늘어나는 경우, 프리셋/모드(`--mode simple/full`) 같은 전략을 우선한다.

---

## 7) Web UI 확장

- 프론트엔드는 별도(`frontend/`)이며, 이 백서에서는 “경계/데이터 계약”만 다룬다.
- 화면/디자인 변경은 별도 가이드로 분리한다.

---

## Evidence

- 메트릭 오케스트레이션: `src/evalvault/domain/services/evaluator.py`
- DAG 파이프라인:
  - `src/evalvault/ports/outbound/analysis_module_port.py`
  - `src/evalvault/domain/entities/analysis_pipeline.py`
  - `src/evalvault/domain/services/pipeline_orchestrator.py`
  - `src/evalvault/domain/services/pipeline_template_registry.py`
  - `src/evalvault/adapters/outbound/analysis/pipeline_factory.py`
  - `src/evalvault/adapters/inbound/cli/commands/pipeline.py`
  - `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
- 레거시 분석: `src/evalvault/domain/services/analysis_service.py`
- Domain Memory:
  - `src/evalvault/ports/outbound/domain_memory_port.py`
  - `src/evalvault/domain/entities/memory.py`
  - `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py`
  - `src/evalvault/adapters/outbound/domain_memory/domain_memory_schema.sql`
- Tracing/Tracking:
  - `src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py`
  - `src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py`
  - `src/evalvault/adapters/outbound/tracker/phoenix_adapter.py`
  - `src/evalvault/config/settings.py`
  - `src/evalvault/config/phoenix_support.py`

---

## 전문가 관점 체크리스트

- [ ] 커스터마이징 절차가 도메인 경계를 침범하지 않는가
- [ ] 등록/템플릿/아티팩트까지 포함한 “끝단까지” 흐름이 문서에 존재하는가
- [ ] 최소 재현(스모크/테스트) 경로가 포함되는가
- [ ] 옵션/설정이 문서와 싱크되는가

---

## 향후 변경 시 업데이트 가이드

- 분석 파이프라인에 새 모듈을 추가했으면:
  - `src/evalvault/adapters/outbound/analysis/pipeline_factory.py` 등록 여부
  - `src/evalvault/domain/services/pipeline_template_registry.py` 템플릿 연결 여부
  - `src/evalvault/adapters/inbound/cli/commands/pipeline.py`에서 사용자 표면 필요 여부
  를 확인하고, 이 장의 **2장**을 업데이트한다.

- Domain Memory 스키마/포트가 바뀌었으면:
  - 이 장의 **4장** + `docs/new_whitepaper/07_advanced.md`의 “저장소/스키마” 절을 함께 갱신한다.

- CLI 옵션을 추가했으면:
  - 도움말(typer help)이 의미 있게 유지되는지 확인하고,
  - 사용자용 SSoT(`docs/guides/USER_GUIDE.md`)와 충돌하지 않도록 링크를 추가한다.
