# 06. 구현 상세(어디를 보면 되는지)

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: 실제로 기능을 수정/추가할 때, “코드 위치”와 “검증 방법”을 빠르게 찾을 수 있게 한다.
- **독자**: 내부 개발자(기능 개발/버그 수정)
- **선행 지식**: Python, 테스트 실행(uv/pytest) 경험

---

## TL;DR

- 진입점: CLI는 `src/evalvault/adapters/inbound/cli/commands/run.py`, API는 `src/evalvault/adapters/inbound/api/main.py`가 중심이다.
- 평가/분석/학습/관측의 근거 파일이 명확히 존재한다(아래 매핑 표).
- 변경 시에는 “도메인 정책 → 포트 계약 → 어댑터 연결” 순서를 기본으로 한다.

---

## 1) 핵심 근거 매핑 (실무용)

| 주제 | 근거 파일 | 메모 |
|---|---|---|
| CLI 진입(평가) | `src/evalvault/adapters/inbound/cli/commands/run.py` | 실행/저장/추적/자동 분석 오케스트레이션 |
| 실행 모드 프리셋 | `src/evalvault/adapters/inbound/cli/commands/run_helpers.py` | `RUN_MODE_PRESETS` 정의 |
| API 진입 | `src/evalvault/adapters/inbound/api/main.py` | `create_app()` 라우터 연결 |
| Runs API | `src/evalvault/adapters/inbound/api/routers/runs.py` | 평가 실행/조회 관련 API |
| 평가 엔진 | `src/evalvault/domain/services/evaluator.py` | `RagasEvaluator.evaluate` (threshold 우선순위, retriever 적용) |
| 분석(DAG) 엔진 | `src/evalvault/domain/services/pipeline_orchestrator.py` | `PipelineOrchestrator.execute/execute_async` |
| 분석 모듈 등록 | `src/evalvault/adapters/outbound/analysis/pipeline_factory.py` | `build_analysis_pipeline_service` |
| 아티팩트 저장 규칙 | `src/evalvault/adapters/inbound/cli/utils/analysis_io.py` | `write_pipeline_artifacts`, `index.json` |
| Domain Memory | `src/evalvault/domain/services/memory_aware_evaluator.py` | threshold 조정 + 컨텍스트 보강 |
| 학습 훅 | `src/evalvault/domain/services/domain_learning_hook.py` | 평가 후 메모리 형성/진화 |
| Stage Events | `src/evalvault/domain/services/stage_event_builder.py` | input/retrieval/output 이벤트 생성 |

> **NOTE**: 이 장은 “파일을 여는 위치”와 “실수 방지 절차”가 목적이다. 구현 세부는 근거를 확인한 뒤 업데이트한다.

---

## 2) 변경 작업의 기본 루트(권장)

### 2.1 메트릭/평가 로직 변경

1. 도메인에서 정책/규칙을 정의한다.
   - 근거: `src/evalvault/domain/services/evaluator.py`
2. 필요하면 포트 계약을 보강한다.
3. 어댑터는 ‘연결/변환’만 수행하도록 유지한다.

실수 방지 체크:
- threshold 우선순위(“CLI > dataset > default”)가 바뀌면, 문서(03장)와 UI/CLI 설명도 함께 바뀐다.

### 2.2 분석 파이프라인(DAG) 변경

> 분석 파이프라인은 “의도(AnalysisIntent) 기반 DAG 실행”을 전제로 한다.

권장 루트:
1. (새 모듈) `AnalysisModulePort` 구현 추가
2. `build_analysis_pipeline_service()`에 등록
3. 템플릿/의도 분류에서 해당 모듈이 호출되도록 연결
4. 산출물 스키마(artifacts/index.json + 노드별 JSON)가 안정적인지 확인

근거:
- 모듈 포트: `src/evalvault/ports/outbound/analysis_module_port.py`
- 모듈 등록: `src/evalvault/adapters/outbound/analysis/pipeline_factory.py`
- 실행 엔진: `src/evalvault/domain/services/pipeline_orchestrator.py`

### 2.3 Domain Memory 변경

권장 루트:
1. 엔티티/스키마 변경 → 어댑터(SQLite)에서 마이그레이션/호환 처리
2. 평가 적용 변경 → `MemoryAwareEvaluator`에서 반영
3. 학습/진화 변경 → `DomainLearningHook`에서 반영

근거:
- 엔티티: `src/evalvault/domain/entities/memory.py`
- 포트: `src/evalvault/ports/outbound/domain_memory_port.py`
- SQLite 어댑터: `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py`
- 스키마: `src/evalvault/adapters/outbound/domain_memory/domain_memory_schema.sql`

---

## 3) 검증(Validation) 루틴

### 3.1 테스트

```bash
uv run pytest tests -v
```

> **NOTE**: 외부 API가 필요한 통합 테스트는 환경 설정에 따라 스킵될 수 있다.

### 3.2 린트/포맷

```bash
uv run ruff check src/ tests/ && uv run ruff format src/ tests/
```

---

## 4) 디버깅 레시피(자주 쓰는 것)

- `--auto-analyze` 결과/아티팩트가 이상함
  - `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`에서 `index.json` 생성 규칙 확인
  - `src/evalvault/domain/services/pipeline_orchestrator.py`에서 노드 실행/스킵 규칙 확인
- Domain Memory가 기대대로 threshold를 바꾸지 않음
  - `src/evalvault/domain/services/memory_aware_evaluator.py`의 `_adjust_by_reliability` 확인
  - 메모리 포트가 반환하는 `get_aggregated_reliability` 결과 확인
- Stage 이벤트가 누락됨
  - `src/evalvault/domain/services/stage_event_builder.py`의 `build_for_run` 확인

---

## 5) 문서-코드 싱크를 유지하는 방법

- 이 장의 표는 변경이 발생할 때마다 함께 갱신한다.
- “코드 경로”가 바뀌는 리팩토링은, 해당 장(또는 INDEX)의 링크도 함께 갱신한다.
- 기능이 추가될 때는 각 장의 “향후 변경 시 업데이트 가이드” 체크리스트를 함께 업데이트한다.

---

## 6) 향후 변경 시 업데이트 가이드

- `run.py`에서 CLI 옵션이 늘어나면: 06장(근거 매핑) + 03장(실행 흐름) + 12장(운영)을 같이 갱신한다.
- 분석 노드가 늘어나면: 06장에는 “등록/연결/산출물 안정화” 절차만 유지하고, 상세는 07/08장으로 보낸다.
- Domain Memory 스키마가 바뀌면: 06장에는 경로/원칙만 유지하고, 상세 운영은 07/12장에 반영한다.

---

## Evidence

- `docs/new_whitepaper/STYLE_GUIDE.md` (근거 기반 서술 규칙)
- `docs/guides/USER_GUIDE.md` (실행/옵션/운영 관점 SSoT)

---

## 전문가 관점 체크리스트

- [ ] 개발자가 ‘수정 위치’를 1~2분 내 찾을 수 있는가
- [ ] 테스트/린트 명령이 실제 작업 흐름과 연결되는가
- [ ] 단정적 서술로 코드와 문서가 어긋날 위험을 줄였는가
