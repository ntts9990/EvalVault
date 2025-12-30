# EvalVault Development Log

> 개발 진행 상황을 기록하는 문서입니다.

---

## 2025-12-30: Phase 10-13 개발 시작

### 계획

| Phase | 작업 | 상태 |
|-------|------|------|
| Phase 12 | 웹 UI MVP (Streamlit) | 🔄 진행 중 |
| Phase 10 | 분석 데이터 저장 완성 | ⏳ 대기 |
| Phase 11 | 확장 가능한 보고서 시스템 | ⏳ 대기 |
| Phase 13 | 웹 UI 확장 | ⏳ 대기 |

### 개발 정책

- **TDD**: 테스트 먼저 작성
- **Hexagonal Architecture**: 포트/어댑터 패턴 준수
- **커밋 규칙**: Conventional Commits
- **PR 정책**: 테스트 통과 후 머지

---

## Phase 12: 웹 UI MVP (Streamlit)

### Phase 12.1: 기반 설정

**시작 시간**: 2025-12-30

**목표**:
- [x] 의존성 추가 (streamlit, plotly)
- [x] CLI 진입점 추가 (evalvault-web)
- [x] 기본 앱 구조 생성
- [x] WebUIPort 인터페이스 정의
- [x] 테스트 작성

**진행 상황**:

| 시간 | 작업 | 결과 |
|------|------|------|
| 12:00 | 의존성 추가 (streamlit, plotly, watchdog) | ✅ 완료 |
| 12:05 | WebUIPort 인터페이스 정의 | ✅ 완료 |
| 12:10 | 테스트 27개 작성 | ✅ 완료 |
| 12:20 | Streamlit 앱 구조 생성 | ✅ 완료 |
| 12:30 | 테스트 실행 (27/27 통과) | ✅ 완료 |

**생성된 파일**:
- `src/evalvault/ports/inbound/web_port.py` - WebUIPort 인터페이스
- `src/evalvault/adapters/inbound/web/` - 웹 UI 어댑터
  - `__init__.py`
  - `adapter.py` - WebUIAdapter 구현
  - `app.py` - Streamlit 메인 앱
  - `session.py` - 세션 관리
  - `pages/__init__.py`
  - `components/__init__.py`
  - `styles/__init__.py`
  - `styles/theme.py` - 테마/색상 정의
- `tests/unit/test_web_ui.py` - 웹 UI 테스트 (27개)

**수정된 파일**:
- `pyproject.toml` - web extra 의존성, evalvault-web 진입점 추가
- `src/evalvault/ports/inbound/__init__.py` - WebUIPort 내보내기 추가

**PR**: [#55](https://github.com/ntts9990/EvalVault/pull/55) ✅ 머지 완료

---

### Phase 12.2: Home 페이지 대시보드 위젯

**시작 시간**: 2025-12-30

**목표**:
- [x] Plotly 차트 컴포넌트 생성
- [x] MetricSummaryCard 컴포넌트 생성
- [x] RecentRunsList 컴포넌트 생성
- [x] Home 페이지 리팩토링
- [x] 테스트 작성

**진행 상황**:

| 시간 | 작업 | 결과 |
|------|------|------|
| 13:00 | 대시보드 테스트 24개 작성 | ✅ 완료 |
| 13:10 | Plotly 차트 컴포넌트 (charts.py) 구현 | ✅ 완료 |
| 13:15 | MetricSummaryCard 컴포넌트 (cards.py) 구현 | ✅ 완료 |
| 13:20 | RecentRunsList 컴포넌트 (lists.py) 구현 | ✅ 완료 |
| 13:25 | DashboardStats 컴포넌트 (stats.py) 구현 | ✅ 완료 |
| 13:30 | Home 페이지 리팩토링 | ✅ 완료 |
| 13:35 | 테스트 실행 (51/51 통과) | ✅ 완료 |

**생성된 파일**:
- `src/evalvault/adapters/inbound/web/components/charts.py` - Plotly 차트 (3종)
- `src/evalvault/adapters/inbound/web/components/cards.py` - MetricSummaryCard
- `src/evalvault/adapters/inbound/web/components/lists.py` - RecentRunsList
- `src/evalvault/adapters/inbound/web/components/stats.py` - DashboardStats
- `tests/unit/test_web_dashboard.py` - 대시보드 컴포넌트 테스트 (24개)

**수정된 파일**:
- `src/evalvault/adapters/inbound/web/components/__init__.py` - 컴포넌트 내보내기
- `src/evalvault/adapters/inbound/web/app.py` - Home 페이지 리팩토링

**PR**: [#56](https://github.com/ntts9990/EvalVault/pull/56) ✅ 머지 완료

---

### Phase 12.3: Evaluate 페이지 개선

**시작 시간**: 2025-12-30

**목표**:
- [x] 파일 업로드 컴포넌트 개선
- [x] 메트릭 선택 컴포넌트 개선
- [x] 진행률 표시 컴포넌트 생성
- [x] 평가 실행 로직 연결 (mock)
- [x] 테스트 작성

**진행 상황**:

| 시간 | 작업 | 결과 |
|------|------|------|
| 14:00 | Evaluate 페이지 테스트 26개 작성 | ✅ 완료 |
| 14:10 | FileUploadHandler 컴포넌트 구현 | ✅ 완료 |
| 14:15 | MetricSelector 컴포넌트 구현 | ✅ 완료 |
| 14:20 | EvaluationProgress 컴포넌트 구현 | ✅ 완료 |
| 14:25 | EvaluationConfig 컴포넌트 구현 | ✅ 완료 |
| 14:30 | Evaluate 페이지 리팩토링 | ✅ 완료 |
| 14:35 | 테스트 실행 (77/77 통과) | ✅ 완료 |

**생성된 파일**:
- `src/evalvault/adapters/inbound/web/components/upload.py` - FileUploadHandler
- `src/evalvault/adapters/inbound/web/components/metrics.py` - MetricSelector
- `src/evalvault/adapters/inbound/web/components/progress.py` - EvaluationProgress
- `src/evalvault/adapters/inbound/web/components/evaluate.py` - EvaluationConfig
- `tests/unit/test_web_evaluate.py` - Evaluate 컴포넌트 테스트 (26개)

**수정된 파일**:
- `src/evalvault/adapters/inbound/web/components/__init__.py` - 컴포넌트 내보내기
- `src/evalvault/adapters/inbound/web/app.py` - Evaluate 페이지 리팩토링
