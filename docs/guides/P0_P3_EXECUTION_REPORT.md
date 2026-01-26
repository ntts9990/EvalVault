# P0-P3 작업 보고서

> 기간: 2026-01-26
> 범위: P0 안정성/운영, P1 사용성, P2 관측성/표준, P3 성능 개선

## P0 (안정성/운영)

### 목표
- 설정/프로필 검증 강화
- 온보딩 실패율 감소(명확한 오류 메시지)

### 작업 내역
- 프로필 적용 시 오류 메시지 강화(없는 프로필/설정 파일 누락)
- 프로덕션 프로필 필수 항목 검증 테스트 추가

### 성과
- 프로필 검증 실패가 조용히 무시되지 않음
- prod 환경 필수 조건이 테스트로 고정됨

### 변경 파일
- `src/evalvault/config/settings.py`
- `tests/unit/test_settings.py`
- `tests/integration/test_cli_integration.py`

### 검증
- `uv run pytest tests/unit/test_settings.py -q`
- `uv run pytest tests -q`

---

## P1 (사용성)

### 목표
- Web UI 핵심 워크플로 완성도 향상
- Run 상세/AnalysisLab/Settings 연동 강화

### 작업 내역
- RunDetails 탭: Stages/Prompts/Gate/Debug UI 존재 확인
- AnalysisLab Prompt Diff 링크 존재 확인
- Settings Metrics Catalog 존재 확인

### 성과
- 설계 문서(웹 UI 확장 계획)에 명시된 핵심 UI가 이미 반영되어 있음 확인

### 변경 파일
- 변경 없음(현행 구현 확인)

### 검증
- `npm run build`

---

## P2 (관측성/표준)

### 목표
- Stage Events 최소 스키마 표준화
- 문서 동기화

### 작업 내역
- StageEvent 최소 필수 필드 검증 및 stage_type 소문자 정규화
- Stage Events 최소 스키마 문서 반영

### 성과
- StageEvent 입력 데이터 정합성 강화
- 문서와 코드 기준 일치

### 변경 파일
- `src/evalvault/domain/entities/stage.py`
- `tests/unit/test_stage_event_schema.py`
- `docs/new_whitepaper/03_data_flow.md`
- `docs/new_whitepaper/12_operations.md`

### 검증
- `uv run pytest tests/unit/test_stage_event_schema.py -q`

---

## P3 (성능 개선)

### 목표
- 요약 메트릭용 데이터셋 메타데이터 흐름 보강
- CSV/Excel 로더에서 summary_tags/summary_intent 지원

### 작업 내역
- CSV/Excel 로더에 summary_tags/summary_intent/metadata 컬럼 파싱 추가
- 데이터셋 스키마 문서에 컬럼 안내 추가

### 성과
- 요약 메트릭(리스크 커버리지/팔로업) 활용 시 데이터셋 태그 누락 감소 기대

### 변경 파일
- `src/evalvault/adapters/outbound/dataset/base.py`
- `src/evalvault/adapters/outbound/dataset/csv_loader.py`
- `src/evalvault/adapters/outbound/dataset/excel_loader.py`
- `tests/unit/test_data_loaders.py`
- `docs/guides/USER_GUIDE.md`

### 검증
- `uv run pytest tests/unit/test_data_loaders.py -q`

---

## 종합 테스트 결과
- `uv run pytest tests -q` : 2119 passed, 2 skipped

## 주의사항
- LSP 진단은 로컬 LSP 서버 설정 미비로 실행 불가
- 프론트 빌드 경고(번들 크기) 존재하나 기존 경고와 동일
