# 부록: 문서/백서 분류(택소노미) + 중복/갭 감사

> 목적: 기존 문서 체계를 "교과서형 handbook"(본편+부록)과 충돌 없이 공존시키기 위한 분류/재사용 원칙을 고정한다.

---

## 1) 현재 문서 체계 지도 (What exists)

### 1.1 최상위 진입점
- `README.md`: 프로젝트 한 줄 정의 + Quickstart + 핵심 개념 + 주요 링크
- `docs/INDEX.md`: 문서 허브(문서 운영 원칙 포함)
- `docs/STATUS.md`: 1페이지 상태 요약(가능/제약)
- `docs/ROADMAP.md`: 공개 로드맵(우선순위)

### 1.2 사용자/운영 가이드 (How to)
- `docs/getting-started/INSTALLATION.md`: 설치/환경 구성
- `docs/guides/USER_GUIDE.md`: 사용자/운영 종합(명령/설정/흐름)
- `docs/guides/DEV_GUIDE.md`: 개발 루틴/테스트/품질
- `docs/guides/EVALVAULT_DIAGNOSTIC_PLAYBOOK.md`: 문제→분석→해석→액션 흐름

### 1.3 설계/운영/품질 기준(내부 SSoT 성격)
- `docs/new_whitepaper/INDEX.md`: 내부 개발자용 종합 백서 인덱스(읽는 순서/작성 규칙)
- `docs/new_whitepaper/*`: 아키텍처/데이터 흐름/구성요소/전문가 관점/구현/품질/성능/보안/운영/표준/로드맵

### 1.4 아키텍처/표준 스펙
- `docs/architecture/open-rag-trace-spec.md`: Open RAG Trace 스펙
- `docs/architecture/open-rag-trace-collector.md`: Collector 구성

### 1.5 API 레퍼런스
- `docs/api/*`: mkdocstrings 기반 API 레퍼런스(ports/adapters/domain 등)

### 1.6 템플릿/예시
- `docs/templates/*`: 데이터셋/리포트 템플릿
- `tests/fixtures/*`: 실행 가능한 데이터셋/케이스(문서 근거로 자주 인용 가능)

### 1.7 리포트/실행 산출물
- `reports/README.md`: reports 디렉터리의 성격(대부분 산출물) + git 추적 정책

### 1.8 에이전트(개발 자동화)
- `agent/README.md`: 개발 에이전트 구조/사용법(별도 "개발 전용" 폴더)

---

## 2) 문서 운영 원칙(기존 규칙)과 handbook의 합의

`docs/INDEX.md`의 핵심 원칙:
- "정답"은 문서가 아니라 `코드/테스트/CLI 도움말`이 최우선
- 문서가 코드와 어긋나면 문서를 최신화하거나 삭제
- 큰 변경(설계/운영/보안/품질 기준)은 `docs/new_whitepaper/`에 먼저 반영

handbook의 합의(이 프로젝트에서 추가로 고정):
- handbook은 "새로운 진실"이 아니라, **기존 SSoT를 묶어주는 교과서형 내비게이션/해설 레이어**
- handbook 본편은 내부 독자 기준으로 작성하되, `docs/handbook/EXTERNAL.md`에 외부 공개 요약을 분리
- 본문 복제 금지: 이미 `docs/`/`docs/new_whitepaper/`에 있는 내용은 **링크 + 요약(필요 최소)**로 처리

---

## 3) 중복 후보(문서가 많아져 생길 수 있는 충돌 지점)

아래 항목은 "중복 확정"이 아니라, Task 3(전수 정독)에서 정밀 판정이 필요한 후보군입니다.

### 3.1 계획/상태 문서 다중화
- 상태/계획/실행 보고 성격 문서가 `docs/guides/`에 다수 존재
  - 예: `docs/guides/NEXT_STEPS_EXECUTION_PLAN.md`, `docs/guides/PROJECT_STATUS_AND_PLAN.md`, `docs/guides/P0_P3_EXECUTION_REPORT.md`, `docs/guides/P1_P4_WORK_PLAN.md`
- `docs/INDEX.md`는 "과거 로그/계획/리포트 성격 문서는 삭제"를 원칙으로 하므로, 이들과의 정합성 점검 필요

### 3.2 Open RAG Trace 문서의 중복 가능성
- `docs/architecture/*`와 `docs/guides/OPEN_RAG_TRACE_*.md`의 역할 분리(스펙 vs 실사용 가이드)가 유지되는지 확인 필요

---

## 4) 갭(교과서형 총정리 관점에서 비어 있는 부분)

### 4.1 프로젝트 전체 파일/구성요소 커버리지 증거
- 기존 문서들은 개념/흐름/설계 기준이 풍부하지만, "모든 파일을 직접 확인했다"는 증거/매핑이 없음
- 이를 보완하기 위해 handbook 부록에 아래를 신설
  - `docs/handbook/appendix-file-inventory.md`
  - `docs/handbook/appendix-coverage-matrix.md`

### 4.2 중앙 집중 용어/정의(Glossary)
- 용어가 문서 곳곳에 분산(예: Run, Artifact, Profile, Stage 등)
- handbook 본편에서 용어 박스/정의 섹션을 통합(또는 별도 glossary 부록) 필요

### 4.3 외부 공개용 요약본의 경계 규칙
- 외부 공개 파트는 개념/사용 흐름 중심이어야 함
- 내부 경로/운영 절차/실데이터/수치/시크릿이 유입되지 않도록 "편집 규칙" 고정 필요

---

## 5) 재사용/참조 원칙(SSoT 유지 전략)

### 5.1 링크 우선(복제 금지)
- 동일 주제가 이미 존재하면:
  1) handbook에서 3~7줄로 요약
  2) 원문을 링크(파일 경로 기준)
  3) 원문이 SSoT(설계 기준/규칙)라면 `docs/new_whitepaper/`를 우선 링크

### 5.2 SSoT 우선순위
1) 코드/테스트/CLI 도움말
2) `docs/new_whitepaper/` (설계/운영/품질 기준)
3) `docs/guides/` (실사용 가이드)
4) handbook (교과서형 정리/내비게이션)

### 5.3 reports 취급
- `reports/README.md`의 정책을 존중: 대부분 산출물(기본 제외)
- handbook에는 "산출물 구조/해석 방법"만 설명하고, 개별 산출물 파일은 원칙적으로 상세 인용 금지

---

## 6) `docs/INDEX.md`에 handbook 링크 추가 계획

handbook이 안정화되면(최소: 목차 + 커버리지 매트릭스 완성) `docs/INDEX.md`의 "빠른 링크"에 아래 1줄을 추가합니다:
- `handbook: handbook/INDEX.md` (교과서형 총정리)

주의:
- `docs/INDEX.md`의 원칙(중복 제거/현재 동작 우선)을 어기지 않도록 handbook은 "링크/요약 레이어"로만 운영합니다.
