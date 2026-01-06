# Test Coverage Improvement Plan

> **현재 상태**: 68% (23,105 lines 중 15,705 lines 커버)
> **목표**: 85%+ 커버리지 달성
> **작성일**: 2026-01-06

## 1. Executive Summary

현재 EvalVault 프로젝트의 테스트 커버리지는 **68%**로, 특히 신규 개발된 Web UI 관련 코드와 일부 도메인 서비스의 커버리지가 낮은 상태입니다. 본 문서는 커버리지를 85% 이상으로 높이기 위한 단계별 계획을 제시합니다.

### 우선순위 분류

| 우선순위 | 영역 | 현재 커버리지 | 목표 |
|---------|------|--------------|------|
| **P0 (Critical)** | 핵심 도메인 서비스 | 41~61% | 85%+ |
| **P1 (High)** | Web UI 컴포넌트 | 0~15% | 70%+ |
| **P2 (Medium)** | 트래커/설정 | 21~45% | 70%+ |
| **P3 (Low)** | 디버그/스크립트 | 0% | 제외 가능 |

---

## 2. 영역별 상세 분석

### 2.1 P0: 핵심 도메인 서비스 (Critical)

비즈니스 로직의 핵심이므로 최우선 커버리지 확보가 필요합니다.

#### 2.1.1 `domain/services/evaluator.py` (41% → 85%)

**현재 상태**: 387 lines, 230 lines 미커버
**누락된 테스트 영역**:
- Ragas 메트릭 실제 실행 경로
- 병렬 처리 (`parallel=True`) 로직
- 에러 핸들링 및 fallback 로직
- 진행률 콜백 (`on_progress`) 동작
- 배치 처리 로직

**필요한 테스트**:
```python
# tests/unit/domain/services/test_evaluator_comprehensive.py

class TestRagasEvaluatorParallel:
    """병렬 처리 테스트."""

    async def test_evaluate_parallel_batch_processing(self):
        """병렬 배치 처리가 올바르게 동작하는지 확인."""
        pass

    async def test_evaluate_parallel_with_failures(self):
        """병렬 처리 중 일부 실패 시 나머지 계속 처리."""
        pass

class TestRagasEvaluatorProgress:
    """진행률 콜백 테스트."""

    async def test_progress_callback_called_correctly(self):
        """진행률 콜백이 올바른 순서로 호출되는지 확인."""
        pass

class TestRagasEvaluatorErrorHandling:
    """에러 처리 테스트."""

    async def test_api_timeout_handling(self):
        """API 타임아웃 시 적절한 에러 처리."""
        pass

    async def test_invalid_metric_handling(self):
        """잘못된 메트릭 지정 시 처리."""
        pass
```

**예상 작업량**: 3-4시간

#### 2.1.2 `domain/services/benchmark_runner.py` (61% → 85%)

**현재 상태**: 306 lines, 120 lines 미커버
**누락된 테스트 영역**:
- 벤치마크 실행 전체 플로우
- 결과 집계 로직
- 비교 분석 로직

**필요한 테스트**:
```python
# tests/unit/domain/services/test_benchmark_runner_comprehensive.py

class TestBenchmarkRunnerExecution:
    """벤치마크 실행 테스트."""

    def test_run_benchmark_full_flow(self):
        """전체 벤치마크 실행 플로우."""
        pass

    def test_benchmark_result_aggregation(self):
        """결과 집계 로직."""
        pass

class TestBenchmarkComparison:
    """벤치마크 비교 테스트."""

    def test_compare_multiple_runs(self):
        """여러 실행 비교."""
        pass
```

**예상 작업량**: 2-3시간

#### 2.1.3 `domain/services/improvement_guide_service.py` (60% → 85%)

**현재 상태**: 181 lines, 73 lines 미커버
**누락된 테스트 영역**:
- LLM 분석 경로
- Stage 메트릭 기반 가이드 생성
- 마크다운 렌더링

**예상 작업량**: 2시간

---

### 2.2 P1: Web UI 컴포넌트 (High Priority)

새로 개발된 Web UI의 테스트 커버리지 확보가 필요합니다.

#### 2.2.1 `adapters/inbound/web/adapter.py` (현재 일부 테스트됨)

**총 라인 수**: 1,285 lines
**누락된 테스트 영역**:
- `run_evaluation()` 의 retriever 설정 경로
- `_build_retriever()` 로직
- `_load_retriever_documents()` 다양한 포맷
- `list_models()` Ollama/vLLM 연동
- `generate_llm_report()` 전체 플로우
- Phoenix resolver 관련 로직

**필요한 테스트**:
```python
# tests/unit/adapters/inbound/web/test_adapter_retriever.py

class TestWebUIAdapterRetriever:
    """리트리버 관련 테스트."""

    def test_build_retriever_bm25_mode(self):
        """BM25 리트리버 빌드."""
        pass

    def test_build_retriever_hybrid_mode(self):
        """Hybrid 리트리버 빌드."""
        pass

    def test_load_retriever_documents_jsonl(self):
        """JSONL 포맷 문서 로드."""
        pass

    def test_load_retriever_documents_json(self):
        """JSON 포맷 문서 로드."""
        pass

class TestWebUIAdapterModels:
    """모델 목록 관련 테스트."""

    def test_list_ollama_models(self):
        """Ollama 모델 목록 조회."""
        pass

    def test_list_vllm_models(self):
        """vLLM 모델 목록 조회."""
        pass

    def test_list_models_fallback(self):
        """모델 조회 실패 시 fallback."""
        pass
```

**예상 작업량**: 4-5시간

#### 2.2.2 `adapters/inbound/web/app.py` (0% → 50%)

**총 라인 수**: 890 lines
**특이사항**: Streamlit 의존성으로 인해 직접 테스트 어려움

**테스트 전략**:
1. **렌더링 함수 분리 테스트**: 데이터 처리 로직을 별도 함수로 분리하여 테스트
2. **Mock Streamlit**: `unittest.mock`으로 st 객체 모킹
3. **컴포넌트 단위 테스트**: 각 페이지 렌더링 함수의 핵심 로직만 테스트

**필요한 테스트**:
```python
# tests/unit/adapters/inbound/web/test_app_pages.py

class TestHomePageLogic:
    """홈 페이지 로직 테스트."""

    def test_dashboard_stats_calculation(self):
        """대시보드 통계 계산."""
        pass

    def test_quality_gate_display_logic(self):
        """품질 게이트 표시 로직."""
        pass

class TestEvaluatePageLogic:
    """평가 페이지 로직 테스트."""

    def test_metric_selection_logic(self):
        """메트릭 선택 로직."""
        pass

    def test_run_mode_switching(self):
        """실행 모드 전환."""
        pass

class TestImprovementPageLogic:
    """개선 가이드 페이지 로직 테스트."""

    def test_analysis_type_selection(self):
        """분석 유형 선택."""
        pass
```

**예상 작업량**: 3-4시간

#### 2.2.3 Web Components (70% 목표)

| 파일 | 라인 수 | 현재 테스트 | 필요한 추가 테스트 |
|------|---------|------------|------------------|
| `charts.py` | 226 | 없음 | 차트 데이터 생성 로직 |
| `reports.py` | 535 | 일부 | 리포트 생성/다운로드 |
| `model_selector.py` | 149 | 없음 | 모델 선택 로직 |
| `prompt_panel.py` | 56 | 없음 | 프롬프트 패널 로직 |

**필요한 테스트**:
```python
# tests/unit/adapters/inbound/web/test_components_charts.py

class TestChartCreation:
    """차트 생성 테스트."""

    def test_create_pass_rate_chart_data(self):
        """통과율 차트 데이터 생성."""
        pass

    def test_create_trend_chart_data(self):
        """트렌드 차트 데이터 생성."""
        pass

    def test_create_metric_breakdown_chart_data(self):
        """메트릭 분석 차트 데이터 생성."""
        pass

# tests/unit/adapters/inbound/web/test_components_model_selector.py

class TestModelSelector:
    """모델 선택기 테스트."""

    def test_get_available_models(self):
        """사용 가능한 모델 목록."""
        pass

    def test_get_model_by_id(self):
        """ID로 모델 조회."""
        pass

    def test_model_option_structure(self):
        """ModelOption 구조 확인."""
        pass
```

**예상 작업량**: 4-5시간

#### 2.2.4 Web Pages (50% 목표)

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `pages/history.py` | 199 | 히스토리 페이지 |
| `pages/reports.py` | 357 | 리포트 페이지 |

**테스트 전략**: 페이지 렌더링은 Streamlit 의존성으로 직접 테스트 어려움. 데이터 처리 로직 위주로 테스트.

**예상 작업량**: 2-3시간

---

### 2.3 P2: 트래커 및 설정 (Medium Priority)

#### 2.3.1 `adapters/outbound/tracker/phoenix_adapter.py` (37% → 70%)

**현재 상태**: 213 lines, 135 lines 미커버
**누락된 테스트 영역**:
- Phoenix 연결 및 트레이스 로깅
- 실험 결과 기록
- 에러 핸들링

**필요한 테스트**:
```python
# tests/unit/adapters/outbound/tracker/test_phoenix_adapter.py

class TestPhoenixAdapter:
    """Phoenix 어댑터 테스트."""

    def test_log_evaluation_run(self):
        """평가 실행 로깅."""
        pass

    def test_connection_error_handling(self):
        """연결 에러 처리."""
        pass

    def test_trace_creation(self):
        """트레이스 생성."""
        pass
```

**예상 작업량**: 2-3시간

#### 2.3.2 `config/instrumentation.py` (45% → 70%)

**현재 상태**: 60 lines, 33 lines 미커버

**예상 작업량**: 1시간

#### 2.3.3 `config/langfuse_support.py` (21% → 70%)

**현재 상태**: 14 lines, 11 lines 미커버

**예상 작업량**: 30분

#### 2.3.4 `config/phoenix_support.py` (65% → 80%)

**현재 상태**: 244 lines, 86 lines 미커버

**예상 작업량**: 1-2시간

---

### 2.4 P3: 디버그 및 스크립트 (Low Priority)

| 파일 | 상태 | 권장 조치 |
|------|------|----------|
| `debug_ragas.py` | 0% | 커버리지 제외 권장 |
| `debug_ragas_real.py` | 0% | 커버리지 제외 권장 |
| `mkdocs_helpers.py` | 0% | 커버리지 제외 권장 |

이 파일들은 개발/디버깅 목적이므로 `.coveragerc`에서 제외하는 것을 권장합니다.

```ini
# .coveragerc 또는 pyproject.toml [tool.coverage]
[run]
omit =
    src/evalvault/debug_*.py
    src/evalvault/mkdocs_helpers.py
```

---

## 3. 구현 계획

### Phase 1: P0 핵심 도메인 서비스 (Week 1)

| 작업 | 대상 파일 | 예상 시간 | 담당 |
|------|----------|----------|------|
| 1.1 | evaluator.py 테스트 확장 | 4h | - |
| 1.2 | benchmark_runner.py 테스트 | 3h | - |
| 1.3 | improvement_guide_service.py 테스트 | 2h | - |

**예상 결과**: 커버리지 68% → 73%

### Phase 2: P1 Web UI 컴포넌트 (Week 2)

| 작업 | 대상 파일 | 예상 시간 | 담당 |
|------|----------|----------|------|
| 2.1 | adapter.py 테스트 확장 | 5h | - |
| 2.2 | app.py 로직 테스트 | 4h | - |
| 2.3 | charts.py 테스트 | 2h | - |
| 2.4 | model_selector.py 테스트 | 2h | - |
| 2.5 | reports.py 테스트 확장 | 3h | - |

**예상 결과**: 커버리지 73% → 80%

### Phase 3: P2 트래커 및 설정 (Week 3)

| 작업 | 대상 파일 | 예상 시간 | 담당 |
|------|----------|----------|------|
| 3.1 | phoenix_adapter.py 테스트 | 3h | - |
| 3.2 | config 모듈 테스트 | 3h | - |
| 3.3 | 커버리지 제외 설정 | 30m | - |

**예상 결과**: 커버리지 80% → 85%

---

## 4. 테스트 작성 가이드라인

### 4.1 Mock 사용 원칙

```python
# 외부 서비스(API, DB)는 항상 Mock
from unittest.mock import MagicMock, AsyncMock, patch

@patch('evalvault.adapters.outbound.llm.openai_adapter.OpenAI')
def test_with_mocked_api(mock_openai):
    mock_openai.return_value.chat.completions.create.return_value = ...
```

### 4.2 Streamlit 테스트 패턴

```python
# Streamlit 컴포넌트 테스트 시 st 객체 모킹
from unittest.mock import MagicMock

def test_with_mocked_streamlit():
    import sys
    mock_st = MagicMock()
    sys.modules['streamlit'] = mock_st

    # 테스트 코드
    from evalvault.adapters.inbound.web.app import render_home_page
    ...
```

### 4.3 비동기 테스트 패턴

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### 4.4 Fixture 활용

```python
@pytest.fixture
def sample_evaluation_run():
    """테스트용 EvaluationRun 생성."""
    from evalvault.domain.entities import EvaluationRun
    return EvaluationRun(
        run_id="test-run-001",
        dataset_name="test-dataset",
        ...
    )
```

---

## 5. 성공 지표

| 지표 | 현재 | 목표 | 측정 방법 |
|------|------|------|----------|
| 전체 커버리지 | 68% | 85% | `pytest --cov` |
| 핵심 도메인 커버리지 | 50% | 85% | evaluator, benchmark 등 |
| Web UI 커버리지 | 15% | 70% | web 패키지 |
| 테스트 실행 시간 | 3분 | 4분 이내 | CI 파이프라인 |

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| Streamlit 의존성 테스트 어려움 | 중 | 로직 분리, Mock 활용 |
| 외부 API 테스트 불안정 | 중 | Mock 우선, 통합 테스트 분리 |
| 테스트 실행 시간 증가 | 낮 | 병렬 실행, 마커 분리 |

---

## 7. 부록

### A. 현재 커버리지가 낮은 파일 전체 목록

```
src/evalvault/adapters/inbound/web/adapter.py          - 부분 테스트됨
src/evalvault/adapters/inbound/web/app.py              - 0%
src/evalvault/adapters/inbound/web/components/charts.py - 0%
src/evalvault/adapters/inbound/web/components/model_selector.py - 0%
src/evalvault/adapters/inbound/web/components/prompt_panel.py - 0%
src/evalvault/adapters/inbound/web/pages/history.py    - 0%
src/evalvault/adapters/inbound/web/pages/reports.py    - 0%
src/evalvault/adapters/outbound/tracker/phoenix_adapter.py - 37%
src/evalvault/config/instrumentation.py                - 45%
src/evalvault/config/langfuse_support.py               - 21%
src/evalvault/domain/services/evaluator.py             - 41%
src/evalvault/domain/services/benchmark_runner.py      - 61%
src/evalvault/domain/services/improvement_guide_service.py - 60%
src/evalvault/domain/services/debug_report_service.py  - 29%
src/evalvault/domain/services/method_runner.py         - 33%
```

### B. 추천 테스트 파일 구조

```
tests/
├── unit/
│   ├── adapters/
│   │   └── inbound/
│   │       └── web/
│   │           ├── test_adapter_retriever.py      # NEW
│   │           ├── test_adapter_models.py         # NEW
│   │           ├── test_app_pages.py              # NEW
│   │           ├── test_components_charts.py      # NEW
│   │           └── test_components_model_selector.py # NEW
│   └── domain/
│       └── services/
│           ├── test_evaluator_comprehensive.py    # NEW
│           └── test_benchmark_runner_comprehensive.py # NEW
└── integration/
    └── web/
        └── test_web_e2e.py                        # NEW (선택적)
```

### C. 참고 문서

- [pytest 공식 문서](https://docs.pytest.org/)
- [pytest-cov 사용법](https://pytest-cov.readthedocs.io/)
- [Streamlit 테스트 가이드](https://docs.streamlit.io/library/advanced-features/testing)
