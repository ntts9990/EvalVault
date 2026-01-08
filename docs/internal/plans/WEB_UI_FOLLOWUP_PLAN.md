# Web UI 후속 개발 계획 (FastAPI + React)

> 작성일: 2026-01-07
> 목적: ARCHITECTURE_C4/PROJECT_MAP/CLASS_CATALOG 기준으로 웹 UI 커버리지를 점검하고,
> 후속 개발을 병렬로 진행할 수 있도록 작업 단위를 분리한다.

---

## 1) 현재 UI 커버리지 점검 (요약)

- 평가 실행: `frontend/src/pages/EvaluationStudio.tsx`
  (메트릭 선택, threshold profile, 배치, retriever, memory, tracker)
- 실행 히스토리/지표: `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/CustomerReport.tsx`
- Run 상세: `frontend/src/pages/RunDetails.tsx`
  (Summary Safety + threshold profile 표기)
- 비교: `frontend/src/pages/CompareRuns.tsx`
- 분석/파이프라인: `frontend/src/pages/AnalysisLab.tsx`, `frontend/src/pages/AnalysisResultView.tsx`
- Domain Memory: `frontend/src/pages/DomainMemory.tsx`
- Knowledge Base/KG: `frontend/src/pages/KnowledgeBase.tsx`

---

## 2) UX 관점 점검 (인지 부하/누락 포인트)

- 고급 옵션이 한 화면에 집중되어 초보자에게 과부하 가능
  → 프리셋/추천값/툴팁/사전검증 플로우 필요
- Run 리스트에서 평가 태스크/도메인/threshold 기준이 한눈에 부족
  → 메타 배지, 필터, 요약 경고 기준 노출 보강 필요
- 요약 메트릭 기본 임계값은 상세 화면 중심으로 노출
  → 대시보드/리포트에 요약 경고 기준 안내가 있으면 안전
- Domain Memory는 조회 중심이라 실행 플로우와 연결성이 약함
  → 평가 실행 시 메모리 사용 여부, 도메인 매핑을 명확히 보여줄 필요
- Experiment/Benchmark/Experiment 비교 UI는 부재
  → 프로젝트 맵 상 핵심 흐름 대비 UI 공백 존재

---

## 3) 후속 개발 백로그 (병렬화 가능)

### Track A — Run 메타/필터 UX

- Dashboard/CustomerReport에 evaluation_task/도메인/threshold 배지 및 필터 추가
- RunDetails에 dataset thresholds vs profile thresholds 비교 패널 추가
- RunSummary에 domain/evaluation_task 노출 확장 (API/adapter)

### Track B — Evaluation Studio 개선

- Dataset Inspector: 타입(qa/summary) 자동 감지, 추천 메트릭/프로필 제안
- Threshold editor: dataset thresholds 미리보기 + 오버라이드 UX
- Memory/Tracker 설정 도움말 + 사전 검증 메시지

### Track C — 분석/리포트 강화

- AnalysisLab 결과 요약 카드/중요도 정렬/다운로드
- Improvement Guide 결과를 RunDetails/AnalysisResultView에 통합
- Report Export: Markdown/PDF 내보내기 (고객 리포트용)

### Track D — 실험/벤치마크 UI

- Experiment manager UI (그룹 생성/비교/추적)
- Benchmark runner 전용 페이지 (실행 + 히스토리)
- FastAPI 신규 router 필요 (experiments/benchmarks)

---

## 4) 병렬 작업 분리 (충돌 최소화 가이드)

| Track | React 수정 범위 | FastAPI/Backend 범위 | 충돌 주의 |
| --- | --- | --- | --- |
| A | `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/CustomerReport.tsx`, `frontend/src/pages/RunDetails.tsx` | `src/evalvault/adapters/inbound/api/routers/runs.py`, `src/evalvault/adapters/inbound/api/adapter.py`, `src/evalvault/ports/inbound/web_port.py` | RunSummary 스키마 충돌 주의 |
| B | `frontend/src/pages/EvaluationStudio.tsx`, `frontend/src/components/` | `src/evalvault/adapters/inbound/api/routers/config.py`, `src/evalvault/config/` | 모델/데이터셋 API 변경 시 동기화 필요 |
| C | `frontend/src/pages/AnalysisLab.tsx`, `frontend/src/pages/AnalysisResultView.tsx`, `frontend/src/components/` | `src/evalvault/adapters/inbound/api/routers/pipeline.py` | Analysis 결과 스키마 변경 주의 |
| D | `frontend/src/pages/` 신규 화면 | `src/evalvault/adapters/inbound/api/routers/` 신규 | router 등록 충돌 가능 |

---

## 5) 공통 체크리스트

- RunSummary/RunDetails 스키마 변경 시 API/React 타입 동시 수정
- 요약 메트릭 기본 임계값(0.90/0.85/0.90) 문구는 UI/리포트에 명시
- 고급 옵션은 기본 접힘 + 툴팁/예시 제공 (인지 부하 최소화)
- UX 변경은 모바일 레이아웃 확인 필수
