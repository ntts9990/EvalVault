# Web UI E2E 시나리오 정의서

> 작성일: 2026-01-09
> 상태: v0.1 (초안)
> 목적: CLI 플로우와 일치하는 UI E2E 테스트 시나리오를 고정한다.

## 1) 기본 원칙

- 핵심 플로우는 **Evaluation → RunDetails → Compare → Analysis** 순서로 구성한다.
- 모든 E2E는 **Mock API 응답 기반**으로 안정성을 확보한다.
- 실패 원인을 쉽게 파악하도록 **명확한 가시성/검증 포인트**를 포함한다.

## 2) 공통 테스트 데이터

| 구분 | 위치 |
| --- | --- |
| 런 목록 | `frontend/e2e/mocks/runs.json` |
| 런 상세 | `frontend/e2e/mocks/run_details.json` |
| 분석 의도 | `frontend/e2e/mocks/intents.json` |

## 3) 시나리오 목록 (필수)

### S1. Evaluation Studio 기본 로드

- **목표**: 옵션 데이터셋/모델/메트릭 로딩 확인.
- **경로**: `/studio`
- **Mock**:
  - `GET /api/v1/runs/`
  - `GET /api/v1/runs/options/datasets`
  - `GET /api/v1/runs/options/models`
  - `GET /api/v1/runs/options/metrics`
  - `GET /api/v1/config/`
- **검증**:
  - “Evaluation Studio” 헤더 표시
  - Dataset/Model 항목 노출
  - “Start Evaluation” 버튼 활성

### S2. Evaluation 실행 → RunDetails 이동

- **목표**: 실행 요청 후 RunDetails 라우팅 확인.
- **경로**: `/studio` → `/runs/:id`
- **Mock**:
  - `POST /api/v1/runs/start` (streamed event)
- **검증**:
  - Start 클릭 후 `/runs/new-run-id` 이동
  - RunDetails 로딩 상태 표시

### S3. Dashboard 목록/필터/선택

- **목표**: 런 목록 표시 및 선택 동작 확인.
- **경로**: `/`
- **Mock**:
  - `GET /api/v1/runs/`
- **검증**:
  - 런 카드 2개 이상 표시
  - 데이터셋/모델 텍스트 노출

### S4. Dashboard → RunDetails 이동

- **목표**: 런 클릭 시 상세 화면 이동 확인.
- **경로**: `/` → `/runs/:id`
- **Mock**:
  - `GET /api/v1/runs/run-123`
- **검증**:
  - URL `/runs/run-123` 변경
  - 요약 정보 표시

### S5. Compare 활성화

- **목표**: 2개 런 선택 시 비교 버튼 활성화.
- **경로**: `/` → `/compare?base=...&target=...`
- **Mock**:
  - `GET /api/v1/runs/`
- **검증**:
  - Compare 버튼 활성화
  - URL 쿼리 파라미터 포함

### S6. RunDetails 기본 정보/케이스 확장

- **목표**: Summary/Case 상세 토글 동작 확인.
- **경로**: `/runs/run-123`
- **Mock**:
  - `GET /api/v1/runs/run-123`
  - `GET /api/v1/runs/run-123/improvement`
  - `GET /api/v1/runs/run-123/report`
- **검증**:
  - pass rate 표시
  - 케이스 확장 시 Ground Truth 노출

### S7. RunDetails 성능 탭 전환

- **목표**: Performance 탭 전환 동작 확인.
- **경로**: `/runs/run-123`
- **검증**:
  - Performance 탭 클릭 후 관련 지표 표시

### S8. Analysis Lab 쿼리 실행

- **목표**: 자연어 분석 쿼리 실행 흐름 확인.
- **경로**: `/analysis`
- **Mock**:
  - `GET /api/v1/pipeline/intents`
  - `GET /api/v1/pipeline/results?limit=20`
  - `GET /api/v1/runs/`
  - `POST /api/v1/pipeline/analyze`
- **검증**:
  - Intent 목록 로드
  - 결과 리포트/요약 노출
  - LLM 오류 배너/보고서 상태 배지 표시
  - 부분 노드 실패 경고 배너 표시
  - 대용량 보고서 토글 노출
  - 보고서 없음 배지 표시

### S9. Knowledge Base 업로드/빌드

- **목표**: 문서 업로드와 KG 빌드 플로우 확인.
- **경로**: `/knowledge`
- **Mock**:
  - `GET /api/v1/knowledge/stats`
  - `POST /api/v1/knowledge/upload`
  - `POST /api/v1/knowledge/build`
  - `GET /api/v1/knowledge/jobs/:id`
- **검증**:
  - KG 상태/엔티티/관계 수 표시
  - 파일 선택/업로드 동작
  - Build 진행 상태 표시 및 완료 후 상태 갱신

### S10. Domain Memory 탭 전환

- **목표**: Facts/Behaviors/Insights 탭 전환 및 데이터 표시.
- **경로**: `/domain`
- **Mock**:
  - `GET /api/v1/domain/facts`
  - `GET /api/v1/domain/behaviors`
- **검증**:
  - Facts 카드 렌더링
  - Behaviors 카드 렌더링
  - Insights 차트/요약 카드 노출

### S11. Compare Runs 기본/필터

- **목표**: 런 비교 화면 로드 및 회귀 필터 적용.
- **경로**: `/compare?base=...&target=...`
- **Mock**:
  - `GET /api/v1/runs/compare`
- **검증**:
  - 비교 헤더/요약 카드 표시
  - Regressions 필터 적용

### S12. Analysis Compare 결과 비교

- **목표**: 두 분석 결과 비교 화면 로드 및 차이 표시 확인.
- **경로**: `/analysis/compare?left=...&right=...`
- **Mock**:
  - `GET /api/v1/pipeline/results/:id`
- **검증**:
  - 좌/우 결과 헤더 표시
  - 주요 지표 차이 표시
  - 노드 상태 변화 표시

## 4) 확장 시나리오 (후순위)

- GraphRAG/KG 업로드 및 검증 플로우
- Phoenix 링크/드리프트 배지 표시
- 자동 분석 결과 다운로드

## 5) 테스트 실패 원인 체크

- API 경로 prefix 불일치(`/api/v1`)
- stream 응답 파싱 실패
- 버튼/레이블 텍스트 변경에 따른 locator 불일치

## 6) Playwright 파일 매핑

| 시나리오 | 파일 |
| --- | --- |
| S1-S2 | `frontend/e2e/evaluation-studio.spec.ts` |
| S3-S5 | `frontend/e2e/dashboard.spec.ts` |
| S6-S7 | `frontend/e2e/run-details.spec.ts` |
| S8 | 신규 파일 (`analysis-lab.spec.ts`) |
| S9 | 신규 파일 (`knowledge-base.spec.ts`) |
| S10 | 신규 파일 (`domain-memory.spec.ts`) |
| S11 | 신규 파일 (`compare-runs.spec.ts`) |
| S12 | 신규 파일 (`analysis-compare.spec.ts`) |
