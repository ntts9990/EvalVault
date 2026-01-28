# 다음 개발 실행 계획 (P0→P3)

> 기준 문서: `docs/ROADMAP.md`, `docs/security_audit_worklog.md`
> 목적: 문서에 정의된 P0→P3를 **실행 순서/검증 게이트**로 정리

## 실행 원칙
- P0→P3 순차 진행
- 각 단계 완료 시 단위 테스트 + 작업 로그 기록
- 전체 테스트 통과 후 e2e 검증 수행
- e2e 통과 시 커밋/푸시/릴리즈
- CI 실패 시 원인 수정 후 재검증

## 실행 순서

### P0 (안정성/운영)
1) CI/테스트 안정성 강화
   - 목표: 플래키 제거, OS 차이 최소화
   - 검증: `uv run pytest tests -q` 2회 연속 통과

2) 설정/프로필 검증 및 오류 메시지 개선
   - 목표: 온보딩 실패율 감소
   - 검증: `tests/unit/test_settings.py`, `tests/integration/test_cli_integration.py`

### P1 (사용성)
1) Web UI 핵심 워크플로 완성도 향상
   - Run 상세 탭(Staging/Prompts/Gate/Debug)
   - AnalysisLab 연동 강화
   - 검증: `npm run build` (프론트는 코드로만 확인)

2) CLI/웹 공통 경로 규약 UX 노출
   - 문서/UI 일관성 확인

### P2 (관측성/표준)
1) Open RAG Trace 스펙/샘플 확장
2) Collector/보존/PII 마스킹 가이드 강화
3) Stage Events 최소 스키마 표준화 및 문서 동기화

### P3 (성능 개선)
1) KPI/평가 프로토콜/로드맵 정립
2) Retrieval/리랭킹/GraphRAG 지표 통합
3) 노이즈 저감/ordering_warning 운영 기준 정착

## 테스트 게이트
1) 단위 테스트: 변경 범위별 최소 단위 테스트 통과
2) 전체 테스트: `uv run pytest tests -q`
3) e2e 테스트: 백엔드 e2e 실행, 프론트는 코드로만 확인

## 릴리즈 게이트
1) 테스트 통과
2) e2e 통과
3) 커밋/푸시
4) CI 상태 확인 및 실패 시 수정 반복

## 추가 개선 작업 (2026-01)

### 1) CI Gate 종료코드 정책 정리
- 목적: CI 스크립트가 종료코드로 실패 원인을 구분 가능하도록 명문화
- 변경: `docs/guides/CI_REGRESSION_GATE.md`
- 기준: `ci-gate` 종료코드 0/1/2/3 정의 및 예외 케이스 명시

### 2) Analysis Report API 스펙 문서화
- 목적: Web UI/외부 도구에서 동일 파라미터로 호출 가능하도록 API 스펙 명시
- 변경: `docs/guides/USER_GUIDE.md`
- 포함 항목: `format`, `include_nlp`, `include_causal`, `use_cache`, `save`

### 3) Analysis Report 저장/캐싱 옵션 추가
- 목적: 보고서 생성 비용 절감 및 재사용 가능
- 변경 파일:
  - `src/evalvault/ports/outbound/storage_port.py`
  - `src/evalvault/adapters/outbound/storage/sqlite_adapter.py`
  - `src/evalvault/adapters/outbound/storage/postgres_adapter.py`
  - `src/evalvault/adapters/inbound/api/adapter.py`
  - `src/evalvault/adapters/inbound/api/routers/runs.py`
- 동작:
  - `use_cache=true`: DB에 동일 조건의 보고서가 있으면 재사용
  - `save=true`: 생성된 보고서를 DB에 저장

### 4) DashboardGenerator API 엔드포인트 추가
- 목적: Web UI가 CLI 없이 대시보드를 직접 렌더링 가능
- 변경 파일:
  - `src/evalvault/adapters/outbound/report/dashboard_generator.py`
  - `src/evalvault/adapters/inbound/api/adapter.py`
  - `src/evalvault/adapters/inbound/api/routers/runs.py`
- 엔드포인트: `GET /api/v1/runs/{run_id}/dashboard` (png/svg/pdf)

### 5) Deprecation 경고 정리
- 목적: 런타임 경고 최소화 및 차기 버전 호환성 확보
- 변경 파일:
  - `src/evalvault/domain/services/evaluator.py`
- 대응: `ragas.metrics.collections.Faithfulness` 우선 사용 (구버전 fallback)

## 작업 로그
- 작업 완료 시 `.sisyphus/notepads/*/worklog.md`에 기록
