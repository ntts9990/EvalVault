# EvalVault — 리팩토링 진단 보고서

> **문서 성격**: 인수받는 사내 팀이 EvalVault의 누적된 부담(꼬임)을 **슬라이스 단위로 안전하게 풀어내기 위한 실행 계획**.
> 4명의 read-only architect 에이전트(Opus)가 영역별로 병렬 진단한 결과를 종합한 작업 문서.
>
> - 진단 기준 버전: **v1.77.0**, 커밋 `bc88726`
> - 진단 수행일: **2026-05-21**
> - 진단 영역: ① 도메인/서비스 비대화  ② 문서/디렉토리 적층  ③ 테스트/CI 비대화  ④ 어댑터 레이어 정합성
> - 짝 문서: [`docs/PROJECT_STATE.md`](./PROJECT_STATE.md) (현재 상태 SSoT)
> - 실행 원칙: **한 슬라이스 = 한 브랜치 = 한 `/ultrareview`**. 회귀 게이트를 baseline으로 사용해 매 슬라이스마다 검증.

---

## 0. Executive Summary

레포는 "코드가 못 만들어서" 꼬인 게 아니라, **성공한 흐름(Hexagonal + dual-tracker + 1,352 tests)의 흔적과 미완 작업의 잔해가 같은 디렉토리에 공존**해서 꼬여 있습니다. 4개 진단을 합쳐보면 단일 패턴이 보입니다:

1. **문서가 코드를 따라잡지 못함**.
   - `CLAUDE.md:310-316`이 가리키는 5개 문서가 실존하지 않음(404).
   - 문서가 `MultiTrackerAdapter` 존재를 명시하지만, **코드 grep 결과 해당 클래스가 없음** — dual-logging은 CLI/API 양쪽에서 손으로 합성 중.
   - `docs/PROJECT_STATE.md` §3.2도 동일 오류를 상속(필자 작성 직전 검증한 CLAUDE.md를 인용).

2. **God-class 2개**가 도메인 코드의 16% 이상을 흡수.
   - `RagasEvaluator`(`evaluator.py`, **1,951줄**)에 평가/한국어 프롬프트/Faithfulness fallback/비용계산이 동거.
   - `PipelineTemplateRegistry`(858줄)에 23개 `_create_*_template` 메서드 하드코딩.

3. **회귀 게이트가 둘**.
   - `.github/workflows/ci.yml`의 regression-gate 잡과 `.github/workflows/regression-gate.yml`이 의미적으로 다른 두 게이트인데 둘 다 PR마다 발화. 하나는 mocked, 다른 하나는 OpenAI 실호출.

4. **어댑터 정책이 어댑터마다 다름**.
   - LLM 5종 중 retry/timeout 표준은 0개. Ollama·vLLM만 timeout을 노출.
   - Tracker 3종에는 공통 base가 없고, 에러를 던지는 방식도 `ValueError`/`RuntimeError`로 갈림.

5. **운영 위험은 P1 회귀 게이트에 묶여 있다**.
   - 진단 영역 모두 "regression-gate 의존성을 흔드는 변경은 동결" 결론으로 수렴.
   - 즉, **회귀 게이트 baseline을 보존하면서** 슬라이스를 돌려야 함.

권장 실행 순서: **Pre-flight 2개 → Phase 1(저위험 6개) → Phase 2(구조 5개) → Phase 3(고위험 4개)**. 자세한 마스터 슬라이스 표는 §3 참조.

---

## 1. 영역 교차 발견 (Cross-area Findings)

### 1.1 문서 ↔ 코드 불일치 (가장 시급)

| 발견 | 근거 | 즉시 조치 |
|---|---|---|
| `CLAUDE.md:310-316`이 가리키는 5개 문서가 실존하지 않음 — `USER_GUIDE.md`, `ARCHITECTURE.md`, `COMPLETED.md`, `IMPROVEMENT_PLAN.md`, `KG_IMPROVEMENT_PLAN.md` | 진단 #2 (docs/architect) | Pre-flight A에서 `CLAUDE.md` 표를 PROJECT_STATE/handbook로 재맵 |
| 문서가 `MultiTrackerAdapter` 존재를 명시하지만 코드에는 없음 (`grep "class.*MultiTracker"` → 0건). 합성은 `cli/commands/run_helpers.py:339-377`와 `api/adapter.py:238-286`에서 수동. | 진단 #4 (adapter/architect) | Pre-flight B에서 PROJECT_STATE.md §3.2와 CLAUDE.md를 정정 |
| `docs/PROJECT_STATE.md` §3.2가 `MultiTracker Adapter (MLflow + Phoenix dual) ✅` 행을 갖고 있음 (이 문서 작성자도 동일 오류를 상속) | `docs/PROJECT_STATE.md:159` | Pre-flight B에서 정정 |
| `mkdocs.yml:113-147`이 deprecated된 `new_whitepaper/*` 14개를 여전히 nav 노출 | 진단 #2 | slice-docs-2 |

> **핵심**: 인수팀이 첫날 CLAUDE.md를 따라가다 깨진 링크/존재하지 않는 클래스에서 신뢰를 잃습니다. **이 문서 두 곳을 1개 PR로 먼저 고쳐야** 그 다음 모든 작업이 정상화됩니다.

### 1.2 슬라이스 의존 그래프

```
[Pre-flight A] CLAUDE.md 깨진 링크 + PROJECT_STATE §3.2 정정
   │
   ├──> [Phase 1] 저위험 슬라이스들이 안전한 진실 위에서 출발
   │
[Pre-flight B] MultiTrackerAdapter 코드/문서 정합화 결정
   │  (옵션 A: 코드 실제 구현 = adapter-S3, 옵션 B: 문서에서 제거)
   │
   ├──> 옵션 A → adapter-S3 → cli/api 합성 중복 자동 해소
   └──> 옵션 B → docs-S1 → 곧장 정합

[domain-S1] domain의 adapter import 제거 ─── 의존성 깨끗 ──┐
[adapter-S2] Tracker base 도입 ───────── 에러정책 통일 ─────┤
                                                          ▼
[domain-S2] evaluator에서 korean prompt 분리 ──── 안전한 분해 시작 ──> [domain-S5] god-class 본격 해체
                                                          ▲
[adapter-S1] LLM retry/timeout 표준화 ──────────────────────┘

[test-S2] slow 마커 부착 ─── PR wall-clock 단축 (선행 부담 없음)
[test-S4] regression-gate 잡 중복 제거 ─── 회귀 게이트 baseline 점검 후 진행
   │
[docs-S2] mkdocs nav 정리 ─── 외부 노출 정리
[docs-S5] INDEX/README.ko 갱신 ─── 진입 동선 정리
```

### 1.3 공통 Anti-targets (영역 전반)

이번 라운드에서 **건드리면 위험한 5곳**. 4명 architect 모두 명시:

1. `src/evalvault/domain/services/regression_gate_service.py` + `.github/workflows/regression-gate.yml` + `tests/fixtures/e2e/regression_baseline.json` — **P1 회귀 게이트 baseline 의존성 동결**.
2. `src/evalvault/adapters/outbound/storage/base_sql.py`의 SQL 빌더 — SQLite/Postgres 차이 흡수 중. 슬라이스 전 회귀 테스트 필수.
3. `src/evalvault/domain/metrics/*` + `registry.py` — evaluator가 직접 참조. 시그니처 변경 금지.
4. `.github/workflows/release.yml:75-87`의 version sed/푸시 — branch protection bypass와 결합.
5. `docs/handbook/CHAPTERS/00-09` 본편 + `docs/api/*`(mkdocstrings 자동 생성) — SSoT.

---

## 2. 영역별 헤드라인 통증 (Top 1 per area)

| 영역 | 가장 시급한 통증 | 근거 | 슬라이스 ID |
|---|---|---|---|
| **도메인** | `RagasEvaluator` 1,951줄에 평가/한국어/fallback/비용이 동거 → 단일 실패점 | `src/evalvault/domain/services/evaluator.py:176-1950` | domain-S2, S5 |
| **문서** | `CLAUDE.md:310-316`이 실존하지 않는 5개 문서 링크. 인수팀 day-1 충돌 | `CLAUDE.md` + `ls docs/` 404 검증 | docs-S1 (Pre-flight A) |
| **테스트/CI** | regression-gate가 두 워크플로에 중복 정의되어 PR마다 두 번 발화 | `.github/workflows/ci.yml:138` + `regression-gate.yml:10` | test-S4 |
| **어댑터** | 문서상 존재하는 `MultiTrackerAdapter`가 코드에 없음 | `grep "class.*MultiTracker"` 0건 + `run_helpers.py:339-377` 수동합성 | adapter-S3 (Pre-flight B) |

---

## 3. 마스터 슬라이스 표 (실행 순서 정렬)

> 한 줄 = 한 PR. 위에서 아래로 진행하면 종속성/회귀 위험이 최소화됨.
> Risk: L=low, M=medium, H=high. Wall=예상 작업 시간(휴리스틱).

### Pre-flight (먼저 1일 안에 끝낼 것)

| ID | 슬라이스 | 영역 | Risk | Wall | 영향 파일 | DoD |
|---|---|---|---|---|---|---|
| **P-A** | `CLAUDE.md` 깨진 5개 링크 수술 + 표를 PROJECT_STATE/handbook로 재맵 | docs | L | 30분 | 1 (`CLAUDE.md`) | `ls`로 검증된 경로만 남음 |
| **P-B** | `MultiTrackerAdapter` 코드/문서 정합 결정 → 결정 결과를 `PROJECT_STATE.md §3.2`·`CLAUDE.md`·`run_helpers.py`/`api/adapter.py`에 반영 | adapter+docs | L (문서만) / M (코드구현) | 1–4h | 2~5 | "표/코드/CLI/API"가 같은 진실 |

### Phase 1 — 저위험 정리 (1~2주, baseline 영향 ≤ 0)

| ID | 슬라이스 | 영역 | Risk | Wall | 영향 파일 | 의존 |
|---|---|---|---|---|---|---|
| **D-S1** | domain → adapters 직접 import 제거 (`domain_learning_hook.py:23`) + port 도입 | domain | L | 2h | `domain_learning_hook.py`, `ports/outbound/domain_memory_port.py`(신규), `adapters/outbound/domain_memory/__init__.py` | — |
| **D-S2** | `evaluator.py` 한국어 프롬프트 오버라이드 분리 → `services/ragas_korean_prompts.py` | domain | L | 3h | `evaluator.py:715-967`, `evaluator.py:1484-1488`, `ragas_prompt_overrides.py`, `test_evaluator_comprehensive.py` | — |
| **T-S2** | 누락된 `slow` 마커 부착 (`test_hybrid_cache`, `test_memory_cache`, `test_async_batch_executor`, `test_cli_progress`) | test | L | 1h | 4개 테스트 파일 | — |
| **DOC-S2** | `mkdocs.yml` nav에서 deprecated 6개 제거, PROJECT_STATE를 top-level로 승격 | docs | L | 1h | `mkdocs.yml` | P-A |
| **DOC-S5** | `docs/INDEX.md` + `docs/README.ko.md` + `docs/handbook/EXTERNAL.md:27` 진입 동선 갱신 | docs | L | 1h | 3개 | P-A |
| **A-S5** | LLM `factory.py` settings mutation 제거 + fallback model 설정화 | adapter | L | 2h | `llm/factory.py:34-103`, `config/settings.py` | — |

### Phase 2 — 구조 정리 (2~4주, 회귀 테스트 필수)

| ID | 슬라이스 | 영역 | Risk | Wall | 영향 파일 | 의존 |
|---|---|---|---|---|---|---|
| **A-S1** | `BaseLLMAdapter`에 `RetryPolicy` 주입 + Settings에 `*_retry_policy` 키 통일 | adapter | M | 1d | `llm/base.py`, 5개 LLM 어댑터, `config/settings.py` | — |
| **A-S2** | `BaseTrackerAdapter` 도입 + 3개 트래커의 에러 정책 통일 | adapter | M | 1.5d | `tracker/base.py`(신규), 3개 tracker 어댑터 | — |
| **T-S1** | CI 매트릭스 다운사이즈 (4셀 → 3셀, Windows nightly로 이동) | test | M | 2h | `.github/workflows/ci.yml:14-20` | — |
| **T-S5** | `ci.yml` lint/test 잡 풀-sync 슬림화 | test | L | 1h | `.github/workflows/ci.yml:44, 85` | — |
| **T-S3** | mocked-only `integration/test_*_flow.py` → unit으로 재분류 | test | M | 4h | `tests/integration/test_langfuse_flow.py`, `test_phoenix_flow.py`, `.github/workflows/ci.yml:177-205` | branch protection 재구성 필요 |
| **DOC-S4** | handbook으로 흡수: `CI_REGRESSION_GATE`, `MULTITURN_EVAL_GUIDE`, `EXPERIMENT_TRACKING_STACK`, `AGENTS_SYSTEM_GUIDE`, `EVALVAULT_DIAGNOSTIC_PLAYBOOK`, `PARALLEL_WORK_APPROVAL_RULES` | docs | M | 1d | 6 흡수 + 6 redirect 스텁 | P-A |
| **DOC-S3** | `docs/guides/`·`docs/refactor/`·고립된 worklog 일괄 git rm (≈32 파일) | docs | M | 2h | ≈32 삭제 | DOC-S4 |
| **D-S3** | Report 서비스 9개 → 3계층(Builder/Renderer/Composer) 재정렬 (**2 PR로 분할 권장**) | domain | M | 3d | 9개 report 서비스 + 단위 테스트 | — |
| **D-S4** | `PipelineTemplateRegistry` 분해 (templates/verify_*, compare_*, analyze_*, generate_*) | domain | M | 2d | `pipeline_template_registry.py` 분해 + `__init__` 등록 훅 | — |

### Phase 3 — 고위험 핵심 해체 (각각 별도 sprint)

| ID | 슬라이스 | 영역 | Risk | Wall | 영향 파일 | 의존 |
|---|---|---|---|---|---|---|
| **T-S4** | `ci.yml`의 regression-gate 잡 삭제 (regression-gate.yml과 중복) — **baseline 영향 ⚠** | test | M-H | 4h | `.github/workflows/ci.yml:138-174` | regression-gate baseline 점검 후 |
| **A-S3** | `MultiTrackerAdapter` 실제 구현 + CLI/API 합성 중복 제거 (open-circuit 정책 포함) | adapter | M-H | 1d | `tracker/multi_adapter.py`(신규), `run_helpers.py:339-377`, `api/adapter.py:238-286` | A-S2 |
| **A-S4** | `langfuse_trace_id` → `tracker_trace_ids: dict[str,str]` (도메인의 벤더 누수 제거) | adapter | H | 1d | `domain/entities/result.py`, `base_sql.py:52,148,667,1177` + DB 마이그레이션 1회 | A-S3 |
| **D-S5** | `RagasEvaluator` 핵심 좁히기 (cost/fallback/custom-metric scoring 분리) | domain | H | 1주 | `evaluator.py`, `multiturn_evaluator.py`, `memory_aware_evaluator.py`, `prompt_scoring_service.py`, `graph_rag_experiment.py`, 2개 신규 서비스 | D-S2 |

---

## 4. 인수팀이 결정해야 할 미해결 질문 (Phase 2 전까지 합의 필요)

진단 4명이 모두 "사람이 결정해야 풀린다"고 지목한 항목만 모음:

1. **`MultiTrackerAdapter` 의도** — git history에서 삭제됐는지, 아직 미구현인지 확인. 결정 후 P-B의 옵션 A/B 선택.
2. **`experiment_repository.py`(68줄) 위치** — 도메인 service인가, outbound port의 default 구현인가? D-S3·D-S4 전 결정.
3. **9개 report 서비스의 외부 노출 표면** — CLI/regression-gate 스냅샷 호환 범위. D-S3 시작 전.
4. **`intent_classifier.py`·`pipeline_template_registry`의 계층** — 진정한 도메인 로직인가, application 계층인가? D-S4 위험도 결정.
5. **mkdocs 사이트 실제 운영 여부** — 운영 중이면 DOC-S2 우선순위 최상단, 미운영이면 후순위.
6. **`docs/architecture/open-rag-trace-spec.md`** — Draft인지 정식 발행인지 (README.ko.md:340). handbook 흡수 여부.
7. **Storage `metric_scores.name` vs `metric_name` 컬럼 차이** — 마이그레이션할 가치인가, 영구히 `SQLQueries` 추상화로 유지인가?
8. **벤치마크 storage(`benchmark_storage_adapter.py`) 별도 base** — 의도된 분리인가, 통합 대상인가?
9. **`tests/fixtures/e2e/` 25개 JSON** 중 실제로 도는 것 — `regression_baseline.json`, `summary_eval_minimal.json` 외엔 명목상 자산?
10. **Frontend Playwright** — `.github/workflows/`에 npm/playwright step 없음. 로컬 전용인가, CI 누락인가?
11. **`docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`(246줄)** vs `rag_human_feedback_calibration_implementation_plan.md`(218줄) — 가이드만 유지하고 계획은 삭제 가능?
12. **`agent/` 자율 에이전트 시스템** — 인수팀이 유지할지 제거할지 (이미 `PROJECT_STATE.md §9.6`에서 제기).

---

## 5. 영역별 상세 진단 보고서 (Verbatim)

### 5.1 도메인/서비스 비대화 진단

**헤드라인**

- `RagasEvaluator`(`evaluator.py` 1,951L)와 `PipelineTemplateRegistry`(858L)가 도메인 서비스 코드의 16% 이상을 흡수하며 god-class로 굳어가고 있음.
- `evaluator.py` 안에 평가/한국어 프롬프트 오버라이드/커스텀 메트릭 스코어링/비용 계산이 동거 → 변경 한 번이 1,352개 회귀 전체를 흔드는 단일 실패점.
- 한 라운드에서 `evaluator`의 책임 4개 중 1개(한국어 프롬프트 오버라이드)를 먼저 떼어내는 저위험 슬라이스부터 시작 권장.

**Top 5 통증 지점**

1. **RagasEvaluator god-class** — `evaluator.py:176-1950`, 단일 클래스에 `_apply_*_korean_*` 4종(L827-967), `_evaluate_sequential/_evaluate_parallel/_score_single_sample`(L1148-1483), `_score_faithfulness_with_fallback`(L1700), `_calculate_cost`(L1935), `_build_ragas_config`(L561) 공존. 영향: `multiturn_evaluator`, `prompt_scoring_service`, `memory_aware_evaluator`, `graph_rag_experiment`가 직접 import.
2. **PipelineTemplateRegistry 858L 거대 팩토리** — `_create_*_template` 23개 메서드 하드코딩. 영향: `AnalysisPipelineService`(pipeline_orchestrator.py:462).
3. **experiment_* 6분할의 책임 블러** — `experiment_manager.py:6-12`, `compare_groups`(L92-104)가 단순 위임만. `experiment_repository.py`는 도메인 service에 있으나 이름·역할은 storage 어댑터에 가까움.
4. **Report/Summary 서비스 9중 중복 추상** — `benchmark_report_service`, `debug_report_service`, `difficulty_profile_reporter`, `experiment_reporter`, `ops_report_service`, `prompt_suggestion_reporter`, `run_comparison_service`, `stage_summary_service`, `unified_report_service` 공존. `debug_report_service.py:12-14`와 `ops_report_service.py:9-11`이 동일 3개를 결합.
5. **`dict[str, Any]` 반환 폭탄 + 도메인의 adapter 누수** — `evaluator.py`에 14건, `visual_space_service.py`에 21건. `domain/services/domain_learning_hook.py:23`에서 `from evalvault.adapters.outbound.domain_memory import ...` — **헥사고날 위반**.

**슬라이스**: S1(domain→adapter import 제거, L), S2(evaluator korean prompt 분리, L), S3(report 9개→3계층, M, 2 PR), S4(pipeline registry 분해, M), S5(RagasEvaluator 핵심 좁히기, H).

**만지지 말 것**: `regression_gate_service.py`, `domain/metrics/*`, `entities/benchmark.py`/`analysis_pipeline.py`, evaluator의 RAGAS Faithfulness 패치 흐름.

**미해결 질문**: `experiment_repository.py` 위치, 9개 report의 외부 노출 범위, `intent_classifier`/`pipeline_template_registry`의 계층.

> 전체 보고서는 [부록 A.1](#a1) 참조.

### 5.2 문서/디렉토리 적층 진단

**헤드라인**

- 새 SSoT(`docs/PROJECT_STATE.md`)와 handbook이 자리잡았지만, 주변에 **deprecated 스텁 7개 · 1회성 plan/worklog 50+ · 완전히 stale한 트랙(`new_whitepaper/`, `refactor/`, `CLAUDE.md` 문서표) 3개**가 적층되어 인수팀의 검색 진입을 오염.
- 가장 위험한 단일 결함은 `CLAUDE.md:310-316`이 존재하지 않는 5개 문서를 가리키는 점.
- `mkdocs.yml:131-147`이 deprecated `new_whitepaper/*` 14개를 여전히 nav에 노출.

**카테고리별 정리 후보**

- **즉시 삭제 가능** (Git 히스토리만 보존): `WORKLOG_LAST_2_DAYS.md`, `P0_P3_EXECUTION_REPORT`, `P1_P4_WORK_PLAN`, `EVALVAULT_WORK_PLAN`, `NEXT_STEPS_EXECUTION_PLAN`, `DI_EXTRACTION_NEXT_STEPS`, `DOCS_REFRESH_PLAN`, `PROJECT_STATUS_AND_PLAN`, `CLI_UX_REDESIGN`, `CHAINLIT_INTEGRATION_PLAN`, `LENA_MVP_IMPLEMENTATION_PLAN`, `LENA_RAGAS_CALIBRATION_DEV_PLAN`, `PRD_LENA`, `RAG_PGVECTOR_PREINDEX_PLAN`, `INSURANCE_SUMMARY_METRICS_PLAN`, `RAG_PERFORMANCE_IMPLEMENTATION_LOG`, `RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL`, `rag_human_feedback_calibration_implementation_plan`, `WEBUI_CLI_ROLLOUT_PLAN`, `CLI_MCP_PLAN`, `refactoring_strategy`, `Extension_2`, `repeat_query`, `cli_process`, `prompt_suggestions_design`, `docs/refactor/REFAC_*` + `logs/phase-*`, `docs/web_ui_analysis_migration_plan`, `docs/security_audit_worklog`, `docs/handbook/WORKLOG_DOCS_CLEANUP_2026-01-29`.
- **handbook으로 흡수 후 삭제**: `CI_REGRESSION_GATE`(→ ch06), `MULTITURN_EVAL_GUIDE`(→ ch02/03), `EXPERIMENT_TRACKING_STACK`(→ ch04), `AGENTS_SYSTEM_GUIDE`(→ `agent/README.md`), `EVALVAULT_DIAGNOSTIC_PLAYBOOK`(→ ch04 장애대응), `PARALLEL_WORK_APPROVAL_RULES`(→ `AGENTS.md`).
- **명시적 redirect 유지**: `STATUS.md`, `ROADMAP.md`, `getting-started/INSTALLATION.md`, `guides/USER_GUIDE.md`, `guides/DEV_GUIDE.md`, `new_whitepaper/INDEX.md`, `guides/_DEPRECATED_NOTICE.md` — **단, `mkdocs.yml`에서 nav 제거 필수**.
- **현행 유지 + 갱신**: 3개 README가 동시 존재(`README.md`, `README.en.md`, `docs/README.ko.md`); `docs/README.ko.md:182,304`가 deprecated `USER_GUIDE.md`를 권유. `CLAUDE.md:310-316`은 즉시 교정 대상. `docs/INDEX.md:34-62`에 PROJECT_STATE 누락. `docs/handbook/EXTERNAL.md:27`은 deprecated를 안내.

**SSoT 충돌** (8개): 아키텍처/Port-Adapter 매트릭스, 구현 현황/Phase 1-14, CLI 명령 일람, 환경변수, Threshold 정책, 릴리스/Conventional Commits, 로드맵/P0-P4, Open RAG Trace. 1차 SSoT 권장은 [부록 A.2](#a2)의 표.

**슬라이스**: slice-docs-1(CLAUDE.md 깨진 링크, L), slice-docs-2(mkdocs nav 정리, L), slice-docs-3(legacy 일괄 git rm, M), slice-docs-4(handbook 흡수, M), slice-docs-5(INDEX/README 갱신, L).

> 전체 보고서는 [부록 A.2](#a2) 참조.

### 5.3 테스트/CI 비대화 진단

**헤드라인**

- 비대화는 "테스트 수(1,352)"보다 **CI 매트릭스 × 풀세트 실행**과 **integration 디렉토리의 mocked-only 테스트 잔류**에서 발생.
- 마커 운영 불일치: `slow`는 8지점만, `sleep` 다발 테스트에 미부착.
- `regression-gate` 잡이 두 워크플로에 중복.

**Top 5 통증**: CI 매트릭스 4셀 풀세트, regression-gate 의미적 중복, mocked-only "integration", `slow` 마커 누락, e2e fixture와 integration 중복.

**CI 워크플로 분석**:

- `ci.yml`: lint+test+regression(CLI)+conditional integration. **lint와 test가 둘 다 풀-sync(`--extra dev --extra web --extra korean`)**. 슬라이스: matrix 4→3셀, Windows nightly로.
- `regression-gate.yml`: PR마다 baseline DB artifact fetch + `evalvault run` 실행. **건드리지 말 것**.
- `release.yml`: branch protection bypass(RELEASE_TOKEN)에 의존 — 범위 외.
- `stale.yml`: 무관.

**슬라이스**: T-S1(매트릭스 다운사이즈, L), T-S2(slow 마커, L), T-S3(integration 재분류, M), T-S4(ci.yml regression-gate 잡 삭제, M-H), T-S5(풀-sync 슬림화, L), T-S6(중복 fixture 통합, L).

**미해결**: `tests/fixtures/e2e/` 25개 중 실호출되는 건 2~3개로 추정; frontend Playwright는 CI에서 미실행; `integration-test` 잡은 PR에서 안 도는데 의도된 분업인가?

> 전체 보고서는 [부록 A.3](#a3) 참조.

### 5.4 어댑터 레이어 정합성 진단

**헤드라인**

- LLM 5종은 `BaseLLMAdapter`(`llm/base.py:83`)로 토큰/Thinking은 통일됐으나 **retry·timeout 정책은 어댑터마다 다름** (Ollama·vLLM만 timeout 노출).
- Storage는 `BaseSQLStorageAdapter`로 잘 추상화됐지만 **`metric_name` 컬럼이 SQLite/Postgres로 분기**(`postgres_adapter.py:38`) — 스키마 표류 위험.
- Tracker 3종에는 **공통 base 없음**. `MultiTrackerAdapter`는 **코드에 존재하지 않음** — dual-logging은 CLI/API에서 수동 합성 중.

**카테고리별 통증**

- **LLM**: 5개 모두 base 사용 + Anthropic만 `ThinkingTokenTrackingAsyncAnthropic` 별도 데코레이터(`anthropic_adapter.py:25`). retry/backoff/tenacity/max_retries grep 0건. `AzureOpenAIAdapter`(79L)가 가장 약함.
- **Storage**: `BaseSQLStorageAdapter` 활용 OK이나 `SQLQueries`가 placeholder/컬럼명/RETURNING 3축 분산. `_get_connection`은 retry 없음. `factory.py:18`의 `fallback_to_sqlite=True`가 silent fallback 야기. `benchmark_storage_adapter.py`는 별도 base.
- **Tracker**: 공통 base 없음. Phoenix(883L) 비대. 에러 정책 분기 — MLflow/Langfuse는 `ValueError`, Phoenix는 `RuntimeError`. dual-logging 시 한 트래커 실패가 전체 막을 위험. `MultiTrackerAdapter` 부재.

**Port 계약 누수 4건**: `StoragePort.save_run`의 `langfuse_trace_id` 필드(`base_sql.py:52,148,667,1177`), `LLMPort.as_ragas_llm()`의 Ragas 타입 노출(`llm_port.py:63`), `TrackerPort.log_evaluation_run`이 `EvaluationRun` 통째로 받음(`tracker_port.py:85`), `factory.py:34-63`의 settings mutation.

**슬라이스**: A-S1(LLM RetryPolicy, M), A-S2(Tracker Base + 에러 통일, M), A-S3(MultiTrackerAdapter 실구현, M-H), A-S4(`langfuse_trace_id` → `tracker_trace_ids`, H), A-S5(factory mutation 제거, L).

> 전체 보고서는 [부록 A.4](#a4) 참조.

---

## 6. 실행 운영 규칙

이 진단을 실제 PR로 옮길 때 지켜야 할 규칙. 4명 architect의 공통 권고를 합성.

### 6.1 각 슬라이스 PR 작성 절차

1. 새 브랜치: `refactor/<slice-id>-<short-name>` (예: `refactor/p-a-claude-md-broken-links`).
2. 슬라이스 표의 DoD를 PR 본문 첫 줄에 명시.
3. 슬라이스 표의 "영향 파일" 외에 다른 파일을 만지면 **별도 PR로 분리**.
4. 회귀 게이트 baseline에 영향이 있는 슬라이스(T-S4, A-S3, A-S4, D-S5)는 PR 본문에 `## ⚠️ baseline-impact` 섹션 명시.
5. PR 머지 전: `uv run pytest -v -m "not requires_openai and not requires_langfuse"` + `uv run ruff check` 통과 확인.
6. **각 PR에 `/ultrareview` 실행** — diff가 슬라이스 범위 안에 있는지 검증.

### 6.2 Phase 전환 게이트

- Pre-flight 완료 조건: P-A, P-B 둘 다 머지. `CLAUDE.md`/`PROJECT_STATE.md`의 모든 표가 실코드와 일치.
- Phase 1 완료 조건: 6개 슬라이스 머지 + 1,352 tests 그대로 통과 + 회귀 게이트 baseline 무변경.
- Phase 2 진입 조건: §4의 미해결 질문 1, 2, 3, 5 결정 완료.
- Phase 3 진입 조건: §4의 모든 미해결 질문 결정 완료 + 회귀 게이트 baseline 재실행으로 노이즈 측정.

### 6.3 위험 신호와 롤백 트리거

다음 중 하나라도 발생하면 해당 PR을 즉시 revert:

- 회귀 게이트가 새로운 회귀를 보고 (baseline 변화 의심).
- CI 매트릭스에서 새로운 OS/Python 조합 실패.
- 1,352 tests 중 새로운 실패가 5개 이상.
- `evalvault run` 명령의 출력 스키마(JSON) 변경.

---

## 부록 — 영역별 전체 진단 원본

### A.1 도메인/서비스 비대화 (전체) {#a1}

이 섹션은 도메인/서비스 architect 에이전트의 원본 보고서.

본문은 §5.1과 동일. 추가로:

**S1 상세**: `grep -r "from evalvault.adapters" src/evalvault/domain` 결과 0건이 되도록 `domain_learning_hook`을 포트 의존으로 전환. 신규 `ports/outbound/domain_memory_port.py`, `adapters/outbound/domain_memory/__init__.py`의 `build_domain_memory_adapter`는 그대로 유지하되 DI composition root에서 주입.

**S2 상세**: `_apply_korean_*` 4개 + 한국어 상수 블록을 `services/ragas_korean_prompts.py`로 추출. `evaluator.py`는 import만. `test_evaluator.py`, `test_evaluator_comprehensive.py`는 그대로 통과해야 함.

**S3 상세 (분할)**:
- S3a: 공통 `ReportDataclass` 도입 + Renderer 인터페이스 정의 (변경 없는 통과 가능 = 회귀 안전).
- S3b: 9개 service를 Builder/Renderer/Composer 책임으로 재배치 + `UnifiedReport`를 Composer로 위치.

**S5 상세 (최대 위험)**: D-S2 머지 후 baseline 측정 → cost/fallback/custom-metric scoring 3개를 각각 별도 PR로 추출 → 마지막에 `RagasEvaluator` 본체를 ≤700L로 좁힘.

### A.2 문서/디렉토리 적층 (전체) {#a2}

§5.2와 동일. 추가:

**SSoT 충돌 표 (1차 SSoT 권장)**:

| 주제 | 충돌 문서 | 1차 SSoT |
|---|---|---|
| 아키텍처/Port-Adapter | README, CLAUDE.md L22-71, AGENTS.md L3-4, PROJECT_STATE §2-3.2, handbook ch01, new_whitepaper/02(deprecated) | **PROJECT_STATE §3.2 + handbook ch01** |
| 구현 현황/Phase 1-14 | CLAUDE.md L285-307, PROJECT_STATE §3, appendix-coverage-matrix | **PROJECT_STATE §3** (메타 있음) |
| CLI 명령 | README.ko.md L32-42, CLAUDE.md L107-118, AGENTS.md L13-20, PROJECT_STATE §4.1 | **PROJECT_STATE §4.1 + `--help`** |
| 환경변수 | CLAUDE.md L170-191, README.ko.md L228-275, PROJECT_STATE §5.2 | **PROJECT_STATE §5.2** |
| Threshold | CLAUDE.md L265-272, README.ko.md L45-66, PROJECT_STATE §5.1 | **PROJECT_STATE §5.1** |
| Conventional Commits | CLAUDE.md L154-168, AGENTS.md L31-37, CONTRIBUTING.md L95-125, PROJECT_STATE §7.2 | **CONTRIBUTING.md** (외부) + PROJECT_STATE §7.2 (운영) |
| 로드맵 P0-P4 | STATUS/ROADMAP(stub), CLAUDE.md L309, PROJECT_STATE §8, handbook ch08, new_whitepaper/14 | **handbook ch08** + PROJECT_STATE §8 요약 |
| Open RAG Trace | architecture/open-rag-trace-spec.md, architecture/open-rag-trace-collector.md, guides/OPEN_RAG_TRACE_* (2개), guides/EXTERNAL_TRACE_API_SPEC.md | **architecture/open-rag-trace-spec.md** |

### A.3 테스트/CI 비대화 (전체) {#a3}

§5.3과 동일. 추가:

**구체 sleep 데이터 (T-S2 대상)**:
- `tests/unit/test_hybrid_cache.py:94,103,112` — `time.sleep(1.1) × 3`
- `tests/unit/test_memory_cache.py:90,99,108` — `time.sleep(1.1) × 3`
- `tests/unit/test_async_batch_executor.py:267,293` — `asyncio.sleep(1)`
- `tests/unit/test_cli_progress.py:43` — (확인 필요)

→ 매 CI 셀마다 최소 7초 직렬 sleep × 4 매트릭스 셀 = **28초+ 낭비**. `@pytest.mark.slow` 부착으로 즉시 해소.

**`integration-test` 잡 분업 의문**: `ci.yml:177-205`의 `if: github.ref == 'refs/heads/main' && github.event_name == 'push'` — PR에서 절대 안 돔. 실제 OpenAI 통합 신호는 `regression-gate.yml`에 의존. 의도된 분업인지 인수팀 확인 필요.

### A.4 어댑터 레이어 정합성 (전체) {#a4}

§5.4와 동일. 추가:

**Port 누수 4건 상세**:

1. `StoragePort.save_run`이 `langfuse_trace_id` 필드를 그대로 통과시킴 — `base_sql.py:52,148,389,667,1177`에서 SQL 컬럼으로 1:1 매핑. 도메인이 트래커 벤더를 알게 됨. **A-S4가 이걸 해소**.
2. `LLMPort.as_ragas_llm()`(`llm_port.py:63`)이 Ragas 타입을 도메인 포트에 박아둠 → `instructor_factory.py:99`가 어댑터 외부에서 wrapper를 만드는 우회로 발생.
3. `TrackerPort.log_evaluation_run`(`tracker_port.py:85`)이 `EvaluationRun` 도메인 엔티티 통째로 받음 → 트래커 어댑터가 도메인 스키마 전체에 결합.
4. `factory.py:34-63`이 provider별로 settings 객체를 mutate — factory가 부작용으로 상태 오염. **A-S5가 이걸 해소**.

**Anti-target 추가**: `tests/fixtures/e2e/regression_baseline.json` — `regression-gate.yml:50, 146`이 직접 참조.

---

## 부록 B — 진단 산출 메타데이터

| 항목 | 값 |
|---|---|
| 진단 도구 | `oh-my-claudecode:architect` 에이전트 4명 (Opus, read-only) |
| 병렬 실행 | 4명 동시 |
| 총 소요 wall-time | ~157초 (가장 느린 에이전트 기준) |
| 총 tool_uses | 28 + 25 + 36 + 27 = 116회 |
| 총 token usage | 약 302k |
| 진단 완료일 | 2026-05-21 |
| 다음 검증 트리거 | Pre-flight 완료 직후 + Phase 1 완료 직후 |
| 이 문서의 owner | **(TBD: 인수팀 리더)** |

---

## 부록 C — 추적 ID

원본 architect 에이전트 ID (필요 시 SendMessage로 추가 질문 가능):

- 도메인/서비스: `a74db4d86ef1a0c71`
- 문서/디렉토리: `abad6da5fe67de41c`
- 테스트/CI: `abef10d106a5959bb`
- 어댑터: `a9aca0e0239ff00d2`
