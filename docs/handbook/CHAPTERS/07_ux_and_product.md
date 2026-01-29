# 07. UX & Product (사용자 여정, 정보 구조, 문서/UX 일관성)

이 챕터는 EvalVault를 “제품”으로 보고, 사용자가 실제로 성공하도록 UX를 정의한다.
핵심은 기능 목록이 아니라 ‘사용자 여정’을 기준으로 CLI와 Web UI를 하나의 경험으로 만드는 것이다.

이 장은 “디자인 철학”을 말하기보다, 레포에 이미 존재하는 UX 메커니즘(에러 패널, 스킵 정책, 다운로드 규약, UI 제약)을 근거로 문서/제품을 정렬하는 것을 목표로 한다.

## TL;DR

- EvalVault의 UX 중심축은 `run_id`다. 사용자는 run을 만들고(run), 이해하고(analyze), 비교하고(compare), 개선한다.
- UI는 “조회/탐색/공유”에 강하고, CLI는 “정밀 제어/자동화”에 강하다. 둘은 역할이 다르다.
- 좋은 UX는 (1) 명확한 다음 행동 제안 (2) 실패 원인과 해결책 제시 (3) 결과의 근거로 이어지는 링크(아티팩트)로 정의된다.

## 목표

- 제품 관점의 핵심 사용자/목표/성공지표를 정의한다.
- CLI와 Web UI의 책임 분리를 명확히 한다.
- 페이지/명령이 “같은 개념”을 같은 언어로 말하도록 정렬한다.

---

## 0) 현실 체크(문서 vs 제품)

Web UI는 CLI의 모든 플래그/옵션을 1:1로 노출하지 않는다.

- 근거(구현): UI에서 CLI로 조건을 복사/이동하는 탈출구가 존재한다: `frontend/src/utils/cliCommandBuilder.ts`

이 제약을 인정하지 않으면 UX가 망가진다.
"UI에서 못 하는 것"을 숨기기보다, CLI로의 안전한 탈출구(예: Copy as CLI, run_id/DB 공유, 다운로드)를 제공하는 것이 팀 비용을 줄인다.

---

## 사용자(페르소나)와 성공 정의

### 1) RAG 운영 엔지니어

- 목표: 변경이 안전한지 빠르게 판단하고 롤백/수정 결정을 내린다.
- 성공: 회귀 원인을 30분 내 1~2개 후보로 좁힌다.

### 2) QA/PM

- 목표: 모델/프롬프트 변경이 사용자 경험에 미치는 영향을 확인한다.
- 성공: “왜 점수가 변했는지”를 이해 가능한 형태(리포트)로 공유한다.

### 3) PoC/솔루션 팀

- 목표: 고객 데이터/도메인에서 재현 가능한 성능을 입증한다.
- 성공: 데이터셋 버전과 run_id를 함께 제시하며 결과를 반복 재현한다.

---

## 핵심 사용자 여정(Primary Journeys)

### 여정 A: 한 번 돌려보고 결과를 이해한다

1) 실행 생성(run)
2) 분석/리포트 생성(auto analyze)
3) Run Details에서 핵심 요약 확인
4) 아티팩트로 근거 확인

### 여정 B: 변경 전/후를 비교해 결정을 내린다

1) baseline run과 current run을 확보
2) 비교(compare)
3) 통계 기반 비교(필요 시)
4) 회귀 원인을 특정(데이터/메트릭/모듈)

### 여정 C: 회귀 게이트로 자동 차단한다

1) PR에서 기준 run 확보
2) current run 생성
3) 게이트 판단(통과/실패)
4) 실패 시 PR 코멘트로 근거 공유

---

## CLI와 Web UI의 역할 분담

### CLI가 잘하는 것

- 자동화(스크립트/CI)
- 상세 옵션(프로필, 메트릭, 분석 모듈, 리트리버)
- 대량 실행/파이프라인

### Web UI가 잘하는 것

- 탐색/필터/비교 시각화
- 리포트 공유(비개발자 포함)
- 아티팩트/근거의 빠른 탐색

### 매핑(개념 중심)

- 실행 목록: CLI `history` ↔ UI Run List
- 실행 상세: CLI 출력/리포트 ↔ UI Run Details
- 분석: CLI `analyze`, `pipeline` ↔ UI Analysis/Report
- 비교: CLI `compare`, `analyze-compare` ↔ UI Compare

---

## 정보 구조(IA): 화면/명령이 가르쳐야 하는 것

사용자는 “다음에 뭘 해야 하는지”를 알고 싶어한다.
따라서 모든 화면/명령은 아래 3가지를 명시적으로 제공해야 한다.

1) 현재 상태: 무엇을 보고 있는가(어떤 run_id, 어떤 데이터셋/프로필)
2) 해석: 무엇이 중요하게 변했는가(메트릭/통과율/원인 후보)
3) 다음 행동: 무엇을 하면 원인이 좁혀지는가(추천 액션)

---

## UX 원칙(팀 규약)

### 인지 부하 최소화

- 한 화면/한 섹션에서 전달할 핵심은 3~5개를 넘기지 않는다.
- 표/그래프는 “결정에 필요한 축”만 보여준다.

### 점진적 공개(Progressive Disclosure)

- 초보자에게는 요약/추천 행동을 먼저 보여준다.
- 고급 사용자는 아티팩트/원본 JSON/세부 로그로 내려갈 수 있어야 한다.

### 실패 메시지의 품질

- 증상 + 원인 후보 + 바로 가능한 조치(명령어/버튼)를 함께 제공한다.
- “무엇이 틀렸는지”만 말하지 말고 “어떻게 고치는지”까지 말한다.

---

## 제품 품질 지표(UX KPI)

- 성공 시간: 새 run_id를 만들고 리포트를 확인하기까지 걸리는 시간
- 문제 해결 시간: 회귀 원인을 1~2개 후보로 좁히기까지의 시간
- 재현율: 같은 조건에서 실행했을 때 결과가 일관되게 재현되는 비율

---

## 체크리스트(UX 리뷰)

- [ ] UI/CLI가 같은 개념을 같은 이름으로 부르는가(run_id, artifacts 등)?
- [ ] 사용자가 다음 행동을 1분 내 선택할 수 있는가?
- [ ] 실패 메시지가 조치 가능(actionable)한가?
- [ ] 근거(아티팩트)로 이동하는 경로가 존재하는가?

## 자기 점검 질문

1) EvalVault UX의 ‘단일 중심축’은 무엇이며, 왜 그렇게 설계되어야 하나?
2) UI가 CLI를 그대로 복제하면 어떤 문제가 생기나?
3) 실패 메시지에 반드시 포함되어야 하는 3요소는 무엇인가?

---

## 1) UX의 단일 중심축: `run_id` + "같은 DB"

EvalVault에서 사용자가 “같은 결과를 보고 있다”는 의미는 DB를 공유한다는 뜻이다.

- Settings 기본 DB: `src/evalvault/config/settings.py#Settings.evalvault_db_path`
- Web API는 settings를 읽어 동작한다: `src/evalvault/adapters/inbound/api/main.py#create_app`

실무 규칙(UX 규약으로 고정):

- UI에서 결과가 안 보이면 “기능이 없어서”가 아니라 “DB가 달라서”인 경우가 가장 많다.
- 따라서 UI/CLI는 화면/콘솔 어디서든 DB 경로를 확인할 수 있어야 한다.

근거(코드):

- Settings 기본 DB 필드: `src/evalvault/config/settings.py#Settings.evalvault_db_path`
- API 서버가 settings를 읽어 동작: `src/evalvault/adapters/inbound/api/main.py#create_app`
- (참고) CLI는 여러 커맨드에서 Settings를 fallback으로 사용: `src/evalvault/adapters/inbound/cli/commands/history.py`, `src/evalvault/adapters/inbound/cli/commands/compare.py`

---

## 2) CLI UX 패턴(코드로 강제되는 사용자 경험)

### 2.1 조치 가능한 에러 메시지(Actionable Errors)

CLI는 단순히 에러를 던지지 않고 “How to fix”/“Tips”를 포함한 패널을 출력한다.

- 공통 렌더러: `src/evalvault/adapters/inbound/cli/utils/console.py#print_cli_error`, `print_cli_warning`

실무 포인트:

- 도메인/어댑터가 실패해도, 사용자가 다음 행동을 고를 수 있어야 한다.

### 2.2 실패 패턴별 가이드(실전형)

대표적인 실패 패턴(키 없음/레이트리밋/타임아웃/데이터셋 오류)에 대해 고정된 해결책 템플릿을 제공한다.

- 구현: `src/evalvault/adapters/inbound/cli/utils/errors.py`
  - `handle_missing_api_key`
  - `handle_invalid_dataset`
  - `handle_evaluation_error`
  - `handle_storage_error`

특히 레이트리밋 대응 UX는 “재시도/배치 크기/병렬 옵션”으로 이어져야 한다.

- 에러 가이드(배치 크기/병렬 힌트): `src/evalvault/adapters/inbound/cli/utils/errors.py#handle_evaluation_error`
- 실행기 레이트리밋 감지(429 문자열 기반) + 배치 크기 감소: `src/evalvault/domain/services/async_batch_executor.py#AsyncBatchExecutor._is_rate_limit_error`

### 2.3 선택지 검증(초기 실패, 빠른 피드백)

CLI는 사용자가 잘못된 선택지를 넣으면 즉시 실패시킨다.

- 구현: `src/evalvault/adapters/inbound/cli/utils/validators.py` (`validate_choice`, `validate_choices`)

이 패턴이 중요한 이유:

- 잘못된 입력을 “조용히 무시”하면, run 결과가 해석 불가능해진다.

### 2.4 진행 표시(Spinner)

장시간 작업은 사용자에게 “멈춘 게 아니라 진행 중”임을 보여준다.

- 구현: `src/evalvault/adapters/inbound/cli/utils/console.py#progress_spinner`

---

## 3) Web UI UX 패턴(문서/코드/페이지 구조)

### 3.1 Web UI 페이지/기능의 “현재 범위”를 문서로 고정

Web UI의 범위와 설계 원칙(워크플로 중심/다운로드 중심/CLI↔UI 매핑)은 문서로 관리된다.

근거(현재 페이지/라우팅): `frontend/src/App.tsx` (Routes)

핵심 원칙 중 UX에 직접적인 것:

- "워크플로 중심": 화면이 실행/조회/분석/비교의 흐름으로 분리돼 있다.
  - 근거: `frontend/src/App.tsx`, `frontend/src/pages/EvaluationStudio.tsx`, `frontend/src/pages/RunDetails.tsx`, `frontend/src/pages/AnalysisLab.tsx`, `frontend/src/pages/CompareRuns.tsx`
- "다운로드 중심": UI는 요약/탐색에 강하고, 근거는 보고서/아티팩트/엔드포인트로 내려가게 설계돼 있다.
  - 근거: `/report`, `/analysis-report`, `/dashboard` 엔드포인트: `src/evalvault/adapters/inbound/api/routers/runs.py`

### 3.2 Web API는 UI의 UX 계약이다

React UI가 무엇을 할 수 있는지는 FastAPI 라우트가 사실상 계약이다.

- runs API 요약: `docs/api/adapters/inbound.md`
- 실제 라우트 구현: `src/evalvault/adapters/inbound/api/routers/runs.py`

추가로, Analysis Lab의 “분석 카탈로그(메뉴)”는 파이프라인 API가 제공하는 intent 목록이 사실상 계약이다.

- intent 카탈로그(서버): `src/evalvault/adapters/inbound/api/routers/pipeline.py` (`INTENT_CATALOG`)
- intent 카탈로그(클라이언트): `frontend/src/services/api.ts#fetchAnalysisIntents`
- UI에서 카탈로그를 로드/표시: `frontend/src/pages/AnalysisLab.tsx`

예: 데이터셋 특성 분석(intent=`analyze_dataset_features`)

- 템플릿: `src/evalvault/domain/services/pipeline_template_registry.py#_create_analyze_dataset_features_template`
- 모듈: `src/evalvault/adapters/outbound/analysis/dataset_feature_analyzer_module.py#DatasetFeatureAnalyzerModule`

UI 관점의 의미:

- 사용자는 Analysis Lab에서 “데이터셋 특성 분석”을 선택해 실행할 수 있다.
- 상세 파라미터는 UI에 아직 1:1로 모두 노출되지 않을 수 있다(원칙적으로 UI는 CLI를 완전 복제하지 않음).

주의(구현 현실):

- 파이프라인 API는 `params`를 받고 `__context__.additional_params`로 전달하지만,
  모든 모듈이 이를 읽도록 연결된 것은 아니다.
- `dataset_feature_analyzer`는 현재 `node.params`만 읽는다(기본값으로 동작).

근거:

- API params 계약: `frontend/src/services/api.ts#runAnalysis`, `src/evalvault/adapters/inbound/api/routers/pipeline.py` (`AnalyzeRequest.params`)
- additional_params 전달: `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator._prepare_inputs`
- dataset_feature_analyzer의 파라미터 해석: `src/evalvault/adapters/outbound/analysis/dataset_feature_analyzer_module.py#DatasetFeatureAnalyzerModule.execute`

예: 보고서 언어 옵션

- `GET /api/v1/runs/{run_id}/report?language=en` (기본 ko)
  - 근거(코드): `src/evalvault/adapters/inbound/api/routers/runs.py#generate_llm_report`

예: 분석 보고서/대시보드

- 분석 보고서: `src/evalvault/adapters/inbound/api/routers/runs.py#get_analysis_report`
- 대시보드: `src/evalvault/adapters/inbound/api/routers/runs.py#get_dashboard` (matplotlib 의존 오류는 ImportError로 반환)

### 3.3 로컬 개발 UX: 프론트/백엔드 연결

- Vite 프록시/직접 호출 환경변수:
  - `frontend/vite.config.ts` (`VITE_API_PROXY_TARGET`)
  - `frontend/src/config.ts` (`VITE_API_BASE_URL`)
  - `frontend/.env.example` (예시)

### 3.4 UI에서 CLI로 안전하게 “탈출”하기: Copy as CLI

UI는 모든 옵션을 노출하지 않는다. 대신 “지금 화면에서 보고 있는 조건”을 CLI 명령으로 복제할 수 있게 하면,
파워 유저/CI 자동화/재현(공유)이 쉬워진다.

- CLI 커맨드 문자열 빌더: `frontend/src/utils/cliCommandBuilder.ts`
- 클립보드 복사 유틸: `frontend/src/utils/clipboard.ts`
- 사용 페이지(예: Copy 버튼):
  - `frontend/src/pages/EvaluationStudio.tsx`
  - `frontend/src/pages/RunDetails.tsx`
  - `frontend/src/pages/AnalysisLab.tsx`
  - `frontend/src/pages/CompareRuns.tsx`

---

## 4) “근거로 내려가는 UX”: 아티팩트(index.json)와 다운로드

EvalVault의 의사결정 UX는 보고서(요약)에서 끝나지 않는다.
정답은 보통 “왜?”이고, 그 답은 아티팩트에서 찾는다.

- 아티팩트 인덱스 작성: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`
- node_id 파일명 sanitize(안전한 파일명): `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#_safe_artifact_name`

UX 규칙(권장):

- UI/CLI 어디서든 `index.json`으로 점프할 수 있어야 한다.
- 팀 커뮤니케이션에서는 `run_id`만 남기지 말고, 최소한 보고서 경로 + index.json 경로를 함께 남긴다.

---

## 5) 온보딩 UX: "첫 성공"을 5분 안에 정의하기

온보딩 UX는 “설치했다”가 아니라 “루프가 닫혔다(run_id 생성→조회→리포트)”로 정의해야 한다.

- 설치/실행(요약): `README.md`
- 로컬 운영 루틴(상세): `docs/handbook/CHAPTERS/04_operations.md`
- handbook 최소 실행: `docs/handbook/CHAPTERS/00_overview.md`

---

## 6) UX 리뷰 체크리스트(실전)

- [ ] UI/CLI가 같은 개념을 같은 이름으로 부르는가? (예: run_id, artifacts)
- [ ] “UI에서 안 됨”이 있을 때 CLI로의 탈출구가 있는가(명령/Copy as CLI/다운로드)?
- [ ] 실패 메시지가 조치 가능(actionable)한가(원인 후보 + 다음 행동)?
- [ ] 보고서에서 아티팩트(index.json)로 내려가는 경로가 존재하는가?

---

## 7) 향후 변경 시 업데이트 가이드

- CLI 에러 UX 템플릿 변경: `src/evalvault/adapters/inbound/cli/utils/console.py`, `src/evalvault/adapters/inbound/cli/utils/errors.py`
- Web UI 범위/매핑 변경(구현 근거):
  - 페이지: `frontend/src/pages/EvaluationStudio.tsx`, `frontend/src/pages/RunDetails.tsx`, `frontend/src/pages/AnalysisLab.tsx`, `frontend/src/pages/CompareRuns.tsx`
  - API 라우트(계약): `src/evalvault/adapters/inbound/api/routers/runs.py`, `src/evalvault/adapters/inbound/api/routers/pipeline.py`
- Runs API(보고서/대시보드/디버그) 변경: `src/evalvault/adapters/inbound/api/routers/runs.py`, `docs/api/adapters/inbound.md`
