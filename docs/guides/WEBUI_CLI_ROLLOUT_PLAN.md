# Web UI 확장 설계서 (CLI 전 기능 반영)

## 목적
- CLI 확장 기능을 Web UI에 전부 반영한다.
- 평가를 잘 모르는 사용자도 따라갈 수 있는 워크플로 중심 UX를 제공한다.
- 고객 보고 페이지는 B2B 대시보드 스타일을 유지한다.
- 나머지 화면은 툴 내비게이터 스타일을 유지한다.
- 결과물은 웹에서 핵심 요약만 보여주고, 상세는 다운로드 중심으로 제공한다.

## 범위
- 대상 CLI: `run`, `run-simple`, `run-full`, `history`, `compare`, `export`, `analyze`, `analyze-compare`, `pipeline`, `benchmark`, `domain`, `kg`, `generate`, `stage`, `prompts`, `experiment-*`, `gate`, `method`, `agent`, `debug`, `config`, `metrics`, `phoenix`, `langfuse`, `serve-api`.
- Web UI 현재 페이지: `Dashboard`, `EvaluationStudio`, `RunDetails`, `AnalysisLab`, `Settings`, `DomainMemory`, `KnowledgeBase`, `Visualization`, `Customer Report`.

## 사용자 유형
- 초보 사용자: 최소 옵션과 가이드 중심, 기본 워크플로 선호.
- 평가 실행자/엔지니어: CLI 옵션과 동일한 명칭/구조, 세밀한 옵션 제어.
- 분석가/PM: 요약 중심, 비교/리포트 다운로드 선호.
- 운영/품질 담당: 게이트/회귀/디버그 리포트 필요.

## 핵심 원칙
- 워크플로 중심: 준비 → 실행 → 분석 → 비교 → 리포트.
- 툴 내비게이터: 기능 탐색과 실행이 빠른 구조.
- CLI ↔ UI 1:1 매핑: UI 옵션이 CLI 플래그/서브커맨드로 역직렬화 가능.
- 다운로드 중심: 웹은 핵심 요약, 상세는 다운로드.

## 롤아웃 전략
### 1단계 (최소 변경)
- 기존 메뉴 유지.
- Run 상세 탭 확장으로 핵심 기능 우선 반영.
- AnalysisLab/Settings 확장.

### 2단계 (구조 확장)
- 신규 메뉴 추가.
- 실험/운영 도구 분리로 탐색성 개선.
- 카탈로그형 도구 UI 정착.

---

## 1단계 상세 설계

### 1. 평가 스튜디오 (CLI: `run`, `run-simple`, `run-full`)
- 기본 입력: dataset, model/profile, metrics, threshold profile.
- 고급 옵션: retriever, memory, tracker, prompt overrides.
- 실행 결과: 완료 시 `Run 상세`로 이동.
- 추가: `Copy as CLI` 버튼 제공.

### 2. Run 상세 탭 확장 (핵심)
- 기존 탭: `Overview`, `Performance`, `Feedback` 유지.
- 신규 탭:
  - `Stages`: `stage list/summary/compute-metrics/report` 대응.
  - `Prompts`: `prompts show/diff` 대응.
  - `Gate`: `gate` 대응.
  - `Debug`: `debug report` 대응.

### 3. 분석 실험실 (CLI: `analyze`, `analyze-compare`, `pipeline`)
- 인텐트 카탈로그 확장.
- Run 선택 기반 분석.
- 결과 요약 + 다운로드.
- 비교 선택 시 Prompt Diff 링크 제공.

### 4. 도메인 메모리 (CLI: `domain`, `domain memory`)
- `ingest-embeddings`, `stats` 기능 탭 추가.

### 5. 지식 베이스 (CLI: `kg`, `generate`)
- KG build/stats 유지.
- 테스트셋 생성 기능 통합.

### 6. 설정 (CLI: `config`, `metrics`, `phoenix`, `langfuse`)
- Integrations 상태 체크.
- Metrics Catalog 노출.

---

## 2단계 상세 설계

### 1. 신규 메뉴 추가
- **실험(Experiments)**: `experiment create/add-group/add-run/list/compare/conclude/summary`.
- **운영 도구(Ops Tools)**: `gate`, `debug`, `stage ingest`, `method`, `agent`, `benchmark`.

### 2. 기존 메뉴 재정리
- AnalysisLab는 분석/리포트 중심으로 축소.
- Run 상세 탭은 유지하되 Ops 기능은 일부 이동.

---

## 메뉴/탭 상세 트리 (2단계 기준)
- 대시보드
  - 실행 리스트, 비교 선택, 게이트 빠른 실행
- 평가 스튜디오
  - 기본, 고급, 실행 로그, 데이터셋 유틸
- 시각화
  - 클러스터 맵, 내보내기
- 분석 실험실
  - 인텐트 카탈로그, 실행, 결과 비교
- 도메인 메모리
  - Facts, Behaviors, Insights, Ingest, Stats
- 지식 베이스
  - KG Build, KG Stats, Dataset Generate
- 실험(신규)
  - 목록, 상세, 그룹 관리, 비교, 결론 요약
- 운영 도구(신규)
  - Gate, Debug, Stage Ingest, Method Runner, Agents, Benchmark
- 고객 리포트(B2B)
  - KPI 요약, 리스크, 트렌드, 공유/다운로드
- 설정
  - 모델/프로필, Integrations, Metrics Catalog

---

## CLI → UI 매핑 요약
- `run` → 평가 스튜디오 실행 폼
- `history` → 대시보드 실행 리스트
- `analyze` → 분석 실험실
- `analyze-compare` → 비교 화면
- `pipeline` → 분석 실험실 (인텐트 카탈로그)
- `benchmark` → 운영 도구 > Benchmark
- `experiment-*` → 실험 메뉴
- `domain/memory` → 도메인 메모리
- `kg` → 지식 베이스
- `generate` → 지식 베이스/평가 스튜디오 유틸
- `stage` → Run 상세 > Stages + 운영 도구 > Ingest
- `prompts` → Run 상세 > Prompts
- `gate` → Run 상세 > Gate + 대시보드 빠른 실행
- `debug` → Run 상세 > Debug
- `method` → 운영 도구 > Method Runner
- `agent` → 운영 도구 > Agents
- `config/metrics` → 설정
- `phoenix/langfuse` → 설정 > Integrations

---

## 워크플로 UX 가이드
- 상단 흐름: 준비 → 실행 → 분석 → 비교 → 리포트.
- 각 단계는 도구 카드/탭으로 연결.
- 초보자는 프리셋 + 최소 옵션으로 실행 가능해야 한다.

---

## 다운로드 정책
- 웹: 핵심 요약 카드(Top 3~5)만 표시.
- 상세: PDF/CSV/JSON 다운로드.
- 파일명 규칙: `run_id` 또는 `date_range` 포함.

예시:
- `run_<RUN_ID>_summary.json`
- `analysis_<RUN_ID>.md`
- `stage_events_<RUN_ID>.jsonl`

---

## 구현 체크리스트
### 1단계
- Run 상세 탭 확장 (Stages/Prompts/Gate/Debug).
- 분석 실험실 인텐트 카탈로그 확장.
- 분석 결과 비교/Prompt Diff 연결 (AnalysisLab/CompareRuns/AnalysisCompareView).
- 고객 리포트 Prompt Diff 요약 + 비교 링크 제공.
- 설정 > Integrations 상태 체크.
- Metrics Catalog UI 노출.
- 다운로드 파일명/포맷 규칙 통일.

#### 1단계 구현 파일
- `frontend/src/pages/RunDetails.tsx` (Stages/Prompts/Gate/Debug 탭, Prompt Diff)
- `frontend/src/pages/CompareRuns.tsx` (Prompt Diff 요약/상세)
- `frontend/src/pages/AnalysisCompareView.tsx` (Prompt Diff 요약/상세)
- `frontend/src/pages/AnalysisLab.tsx` (Prompt Diff 링크)
- `frontend/src/pages/Settings.tsx` (Metrics Catalog)
- `frontend/src/pages/CustomerReport.tsx` (Prompt Diff 요약/비교 링크)
- `frontend/src/services/api.ts` (QualityGate/Debug/PromptDiff API)
- `src/evalvault/adapters/inbound/api/adapter.py` (Prompt Diff/Debug Report)
- `src/evalvault/adapters/inbound/api/routers/runs.py` (Prompt Diff/Debug Report API)

### 2단계
- 실험 메뉴 추가.
- 운영 도구 메뉴 추가.
- 카탈로그형 도구 UI 패턴 통합.
- 장시간 작업 상태/로그/취소 UI 통합.
- Copy as CLI 전면 적용.

---

## 검증 계획
- CLI 옵션 ↔ UI 필드 매핑 검증.
- API 요청/응답 모델 일치 확인.
- 다운로드 생성/링크 동작 확인.
- 초보 사용자 워크플로 시나리오 테스트.
