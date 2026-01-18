# EvalVault 현재 개발 상황 및 실행 계획

## 목적
- 현재 개발 현황을 한눈에 요약하고, 목표/골/에픽/작업을 일관된 구조로 정리한다.
- 진행 상태를 시각적으로 표현해 팀 내 공유/점검을 쉽게 한다.

---

## 1) 현재 개발 상황 요약

### 1.1 최근 커밋 흐름(요약)
- docs(cli): add parallel features spec
- docs(rag): document noise reduction plan
- feat(metrics): flag unordered stage inputs
- feat(cli): add parallel command suite
- feat(rag): harden noise reduction pipeline
- docs(rag): align noise reduction guidance
- feat(ui): surface ordering warnings
- feat(ui): add ordering warning guidance
- test(cli): fix compare pipeline mock

### 1.2 핵심 완료 사항
- **CLI 병렬 명령군 완료**: compare/calibrate-judge/profile-difficulty/regress/artifacts lint/ops snapshot
- **노이즈 저감 파이프라인 강화**: dataset_preprocessor/evaluator/stage_metric_service 개선
- **ordering_warning 도입**: 순서 복원/경고 메트릭 + 런북/strict 기준 문서화
- **WebUI 반영**: RunDetails/CompareRuns/AnalysisLab에 경고 표시 및 런북 링크 추가

### 1.3 품질/검증 상태
- Python unit smoke:
  - dataset_preprocessor: PASS
  - evaluator_comprehensive: PASS
  - stage_metric_service: PASS
- Frontend lint/build:
  - eslint: PASS
  - vite build: PASS (bundle size warning only)

---

## 2) 프로젝트 목표 정의

### 2.1 미션
- **RAG 성능 개선을 반복 가능하게 만든다**.

### 2.2 핵심 목표(Goals)
1. **측정 가능성 확보**: run_id 기준 KPI로 변화가 추적됨
2. **원인 규명 가능성**: 점수 변동의 원인을 stage/metric 단위로 추적
3. **재현 가능성**: 동일 입력/설정/아티팩트로 재검증
4. **운영 가능성**: 비용/지연/안정성을 함께 관리

---

## 3) 골(Goals) 설정

| Goal | 설명 | 완료 조건 |
|---|---|---|
| G1 | KPI baseline 확정 | 기준 run + 비교 리포트 생성 |
| G2 | 노이즈 저감 운영화 | ordering_warning 비율/런북 운영 |
| G3 | 병렬 CLI 체계화 | compare/calibrate/… 명령 일괄 적용 |
| G4 | 관측/리포팅 통합 | report + artifacts + run_id 연동 |
| G5 | WebUI 전달 | warning/런북/strict 체크리스트 노출 |

---

## 4) 에픽(Epics) 및 상세 작업

### EPIC-0 기준선/범위 고정
- EV-RAG-001 KPI baseline 정의 및 threshold 확정
- EV-RAG-002 표준 데이터셋 버전 고정
- EV-RAG-003 run 비교 리포트 템플릿 확정
- EV-RAG-004 Stage Events 스키마 점검

### EPIC-1 Retrieval 개선 체계화
- EV-RAG-101 rerank ON/OFF 메트릭 정리
- EV-RAG-102 GraphRAG stage/아티팩트 반영
- EV-RAG-103 retrieval benchmark 확장

### EPIC-2 Grounding/환각 대응
- EV-RAG-201 grounding stage metric 정의
- EV-RAG-202 improvement guide 레버 매핑
- EV-RAG-203 고위험 정책 플래그/워크플로

### EPIC-3 Observability/운영 게이트
- EV-RAG-301 운영 KPI 표준화
- EV-RAG-302 tracker metadata 주입
- EV-RAG-303 CI gate baseline 비교

### EPIC-4 Judge/난이도 프로파일링
- EV-RAG-401 난이도 v0 휴리스틱
- EV-RAG-402 judge 캐스케이드 v0
- EV-RAG-403 calibration 리포트 자동화

### EPIC-5 병렬 CLI 명령군
- EV-CLI-001 compare
- EV-CLI-002 calibrate-judge
- EV-CLI-003 profile-difficulty
- EV-CLI-004 regress
- EV-CLI-005 artifacts lint
- EV-CLI-006 ops snapshot

### EPIC-6 WebUI 노이즈 경고 전달
- EV-UI-001 RunDetails ordering_warning 표시
- EV-UI-002 CompareRuns ordering_warning 비교
- EV-UI-003 AnalysisLab 런북 링크
- EV-UI-004 Strict 체크리스트 노출

---

## 5) 진행 현황(시각화)

### 5.1 에픽 진행률
```
EPIC-0  [====>--------------] 20%
EPIC-1  [===>---------------] 15%
EPIC-2  [=>-----------------] 10%
EPIC-3  [==>----------------] 12%
EPIC-4  [=>-----------------] 10%
EPIC-5  [==================>] 95%
EPIC-6  [===============>---] 80%
```

### 5.2 완료/진행/대기
- 완료: EPIC-5(대부분), EPIC-6(대부분), ordering_warning 도입
- 진행: EPIC-0/1/2/3/4 기초 정의
- 대기: strict 전환 구현, GraphRAG 운영화, CI gate 자동화

---

## 6) 병렬 작업 가이드(필수 항목)

아래 항목을 각 병렬 작업 단위(에픽/티켓)마다 반드시 채운다.

### 6.1 병렬 작업 필수 메타데이터
- 작업 ID: 예) EV-RAG-101
- 오너: 담당자 1명 (문서 오너 포함)
- 범위 파일: 수정/생성 파일 목록(경로 기준)
- 금지 파일: 접근 금지 파일 목록(충돌 방지)
- 공유 스키마/출력 포맷: 변경 시 사전 합의 필요 목록
- 의존 작업: 선행/후행 작업
- 검증 계획: pytest/lint/build 명령
- 산출물: 리포트/아티팩트 경로
- 리스크: 실패 가능성 및 완화책

### 6.2 병렬 작업 템플릿(복사해서 사용)
```
[WORK ITEM]
- ID:
- Owner:
- Scope Files:
- Blocked Files:
- Shared Schemas/Formats:
- Dependencies:
- Validation:
- Outputs:
- Risks:

[NOTES]
- 진행 로그:
- 테스트 결과:
- 이슈/결정:
```

### 6.3 병렬 작업 규칙(핵심)
- 서로 다른 파일에서 작업
- 공유 스키마/출력 포맷 변경은 사전 합의
- 문서 오너 1명 지정(동시 편집 금지)
- 변경 산출물은 run_id 또는 작업 ID에 연결
- 작업 종료 시 검증 결과 기록

### 6.4 병렬 작업 검증 체크리스트
- [ ] 변경 파일 범위 일치
- [ ] 금지 파일 미접근
- [ ] 의존 작업 충족
- [ ] pytest/lint/build 통과
- [ ] 아티팩트/리포트 경로 기록

---

## 7) 다음 액션(추천)
1. EPIC-0 KPI baseline 확정 및 run 비교 리포트 생성
2. ordering_warning 런북 운영 자동화(비율 집계/경고)
3. CI gate(regress)와 baseline 연동
4. GraphRAG stage/아티팩트 정합성 강화

---

## 8) 참고 문서
- `docs/guides/RAG_NOISE_REDUCTION_GUIDE.md`
- `docs/guides/CLI_PARALLEL_FEATURES_SPEC.md`
- `docs/guides/RAG_PERFORMANCE_IMPLEMENTATION_LOG.md`
