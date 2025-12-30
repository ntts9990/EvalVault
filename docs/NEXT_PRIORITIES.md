# EvalVault Next Priorities

> Last Updated: 2025-12-30
> Status: Planning Phase
> Context: Phase 9 Korean RAG Optimization 완료 후 다음 단계

---

## Executive Summary

Phase 9 완료 후 EvalVault의 다음 우선순위는 **분석 데이터 저장 완성**, **확장 가능한 보고서 시스템**, 그리고 **Streamlit 기반 웹 UI MVP**입니다.

### 핵심 결정 사항

| 항목 | 결정 | 근거 |
|------|------|------|
| 웹 UI 프레임워크 | **Streamlit** | Python 기반, 빠른 프로토타이핑, 풍부한 컴포넌트 |
| MVP 범위 | **축소 (3개 핵심 기능)** | 빠른 검증, 과도한 범위 방지 |
| API 서버 | **Streamlit 내장 우선** | FastAPI는 필요 시 추가 |
| 배포 | **로컬 + Docker** | HF Spaces는 선택적 |

### 우선순위 요약

| 순위 | 작업 | 예상 규모 | 의존성 |
|------|------|-----------|--------|
| 🔴 P0 | 분석 데이터 저장 완성 | Medium | 없음 |
| 🔴 P0 | 확장 가능한 보고서 시스템 | Large | P0 저장 |
| 🔴 P0 | **웹 UI MVP (Streamlit)** | Medium | 없음 (병렬 가능) |
| 🟡 P1 | 웹 UI 확장 (분석, 트렌드) | Medium | P0 웹 UI |
| 🟡 P1 | API 서버 (FastAPI) | Medium | P0 보고서 |
| 🟢 P2 | 알림 시스템 | Small | P0 저장 |
| 🟢 P2 | PDF 내보내기 | Small | P0 보고서 |

---

## Part 1: 현재 상태 분석 (Gap Analysis)

### 1.1 코드베이스 현황

```
EvalVault 현재 상태:
┌─────────────────────────────────────────────────────────────────┐
│  코드 통계                                                       │
├─────────────────────────────────────────────────────────────────┤
│  테스트          │  976개 (Unit 950 + Integration 26)           │
│  CLI 코드        │  2,426줄                                     │
│  도메인/서비스    │  5,000줄+                                    │
│  Python 파일     │  85개+                                       │
│  CLI 명령어      │  21개                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 저장 시스템 현황

```
현재 구현:
┌─────────────────────────────────────────────────────────────────┐
│  SQLite Storage                                                  │
├─────────────────────────────────────────────────────────────────┤
│  ✅ evaluation_runs        - 평가 실행 메타데이터               │
│  ✅ test_case_results      - 테스트 케이스별 결과               │
│  ✅ metric_scores          - 메트릭 점수                        │
│  ✅ experiments            - 실험 관리                          │
│  ✅ analysis_results       - 분석 결과 (JSON blob)              │
│  ✅ save_analysis()        - StatisticalAnalysis 저장           │
│  ✅ save_nlp_analysis()    - NLPAnalysis 저장                   │
│  ❌ save_causal_analysis() - CausalAnalysis 저장 (미구현)       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Langfuse Tracker                                                │
├─────────────────────────────────────────────────────────────────┤
│  ✅ log_evaluation_run()   - 평가 실행 트레이스 저장            │
│  ✅ log_score()            - 메트릭 스코어 저장                 │
│  ✅ save_artifact()        - 아티팩트 메타데이터 저장           │
│  ❌ Analysis scores        - 분석 결과 스코어링 (미구현)        │
│  ❌ Analysis metadata      - 분석 메타데이터 저장 (미구현)      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 보고서 시스템 현황

```
현재 구현 (MarkdownReportAdapter):
┌─────────────────────────────────────────────────────────────────┐
│  하드코딩된 섹션 구조                                            │
├─────────────────────────────────────────────────────────────────┤
│  1. _generate_header()           - 헤더                         │
│  2. _generate_summary()          - 요약                         │
│  3. _generate_statistical_section() - 통계 분석                 │
│  4. _generate_nlp_section()      - NLP 분석                     │
│  5. _generate_causal_section()   - 인과 분석                    │
│  6. _generate_recommendations()  - 권장사항                     │
│  7. _generate_footer()           - 푸터                         │
└─────────────────────────────────────────────────────────────────┘

문제점:
- 새 섹션 추가 시 코드 수정 필요
- 섹션 순서/포함 여부 런타임 설정 불가
- 출력 포맷(MD/HTML)이 어댑터에 결합
- 플러그인 방식 확장 불가능
```

### 1.4 웹 UI 현황

```
현재: 없음

CLI 명령어 (웹 UI 대상):
├── 메인 명령어 (7개)
│   ├── run         - RAG 평가 실행
│   ├── analyze     - 통계/NLP/인과관계 분석
│   ├── generate    - 테스트셋 생성
│   ├── history     - 평가 이력
│   ├── compare     - 실행 비교
│   ├── export      - JSON 내보내기
│   └── metrics/config - 정보 표시
├── 실험 관리 (7개)
│   └── experiment-* 명령어들
└── 도메인 관리 (4개)
    └── domain init/list/show/terms

지원 메트릭 (7개):
faithfulness, answer_relevancy, context_precision, context_recall,
factual_correctness, semantic_similarity, insurance_term_accuracy
```

---

## Part 2: 웹 UI 기술 스택 분석

### 2.1 기술 스택 비교

| 옵션 | 장점 | 단점 | AI 오류 위험 | 개발 시간 |
|------|------|------|--------------|-----------|
| **Streamlit** | Python 기반, 풍부한 컴포넌트, 상태 관리 개선, 커뮤니티 큼 | 커스터마이징 제한 | 낮음 | 빠름 |
| Gradio | ML 데모 특화, HF 통합 | 복잡한 UI 제한, 상태 관리 미흡 | 중간 | 빠름 |
| NiceGUI | 현대적 UI, Vue 스타일 | 커뮤니티 작음 | 중간 | 중간 |
| FastAPI+React | 완전 커스텀 | 개발 시간 많이 필요 | 높음 | 느림 |

### 2.2 Streamlit 선택 이유

```
✅ Python 기반 - 기존 도메인 코드 그대로 재사용
✅ 풍부한 컴포넌트 - st.dataframe, st.plotly_chart, st.file_uploader
✅ 상태 관리 - st.session_state로 세션 상태 관리
✅ 레이아웃 - st.columns, st.tabs, st.sidebar 지원
✅ 파일 처리 - 업로드/다운로드 내장
✅ 실시간 갱신 - st.rerun, auto_refresh
✅ 차트 - Plotly, Altair, Matplotlib 통합
✅ 테마 - 다크모드/라이트모드 지원
✅ 배포 - Docker, Streamlit Cloud 지원
```

### 2.3 Gradio를 선택하지 않은 이유

```
❌ 용도 불일치 - ML 모델 데모용 설계, 관리 대시보드에 부적합
❌ 네비게이션 제한 - 탭 기반만 지원, 서브페이지/모달 구현 어려움
❌ 상태 관리 미흡 - 복잡한 폼 상태 관리 어려움
❌ 레이아웃 제약 - 복잡한 대시보드 레이아웃 구현 제한적
❌ 지식그래프 시각화 - 네트워크 그래프 라이브러리 통합 제한적
```

---

## Part 3: 웹 UI MVP 설계

### 3.1 MVP 범위 (축소)

```
┌─────────────────────────────────────────────────────────────────┐
│  MVP Phase 1 (핵심 3개 기능)                                     │
├─────────────────────────────────────────────────────────────────┤
│  📊 평가 실행 (Evaluation)                                       │
│     ├── 데이터셋 업로드 (CSV/JSON)                               │
│     ├── 메트릭 선택                                              │
│     ├── 실행 및 진행률 표시                                       │
│     └── 결과 요약                                                │
│                                                                  │
│  📋 이력 조회 (History)                                          │
│     ├── 평가 목록 (필터/정렬)                                     │
│     ├── 상세 결과 보기                                           │
│     └── 테스트 케이스별 점수                                      │
│                                                                  │
│  📄 보고서 다운로드 (Reports)                                     │
│     ├── Markdown/HTML 생성                                       │
│     └── 파일 다운로드                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Phase 2 확장 (MVP 검증 후)                                      │
├─────────────────────────────────────────────────────────────────┤
│  🔬 분석 (Analysis)      - NLP/인과관계 분석 시각화              │
│  📈 트렌드 (Trends)      - 메트릭 트렌드 차트                    │
│  🧪 실험 (Experiments)   - A/B 테스트 비교                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  제외 (CLI 유지)                                                 │
├─────────────────────────────────────────────────────────────────┤
│  ❌ 지식그래프 시각화    - 별도 도구 (Neo4j Browser) 권장        │
│  ❌ 도메인 메모리 관리   - CLI로 충분                            │
│  ❌ Langfuse 대시보드    - Langfuse 자체 UI 사용                 │
│  ❌ 테스트셋 생성        - 복잡한 설정 필요, CLI 유지            │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 아키텍처 설계

```
Hexagonal Architecture 유지:
┌─────────────────────────────────────────────────────────────────┐
│                        Inbound Adapters                          │
│  ┌─────────────┐  ┌─────────────────────────────────────────┐   │
│  │    CLI      │  │           Web UI (Streamlit)             │   │
│  │  (기존)     │  │              (NEW)                       │   │
│  └──────┬──────┘  └─────────────────┬───────────────────────┘   │
│         │                           │                            │
│         ▼                           ▼                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    WebUIPort (NEW)                       │    │
│  │  - run_evaluation()                                      │    │
│  │  - list_runs()                                           │    │
│  │  - get_run_details()                                     │    │
│  │  - generate_report()                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Domain Services                         │    │
│  │  RagasEvaluator, AnalysisService, ReportEngine (재사용)   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Outbound Adapters                       │    │
│  │  SQLiteStorage, LangfuseTracker, MarkdownReport (재사용)  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 파일 구조

```
src/evalvault/
├── ports/
│   └── inbound/
│       └── web_port.py              # WebUIPort 인터페이스 (NEW)
├── adapters/
│   └── inbound/
│       ├── cli.py                   # 기존 CLI (유지)
│       └── web/                     # 웹 UI 어댑터 (NEW)
│           ├── __init__.py
│           ├── app.py               # Streamlit 메인 앱
│           ├── session.py           # 세션/상태 관리
│           ├── runner.py            # 백그라운드 작업 관리
│           ├── pages/
│           │   ├── __init__.py
│           │   ├── home.py          # 홈/대시보드
│           │   ├── evaluation.py    # 평가 실행
│           │   ├── history.py       # 이력 조회
│           │   └── reports.py       # 보고서 생성
│           ├── components/
│           │   ├── __init__.py
│           │   ├── dataset_uploader.py
│           │   ├── metric_selector.py
│           │   ├── progress_display.py
│           │   ├── results_table.py
│           │   └── charts.py
│           └── styles/
│               └── theme.py         # 테마/색상 정의
└── config/
    └── web_config.py                # 웹 UI 설정
```

### 3.4 WebUIPort 인터페이스

```python
# src/evalvault/ports/inbound/web_port.py
from typing import Protocol, Callable, Literal
from dataclasses import dataclass

@dataclass
class EvalRequest:
    """평가 실행 요청."""
    dataset_path: str
    metrics: list[str]
    model_name: str = "gpt-5-nano"
    langfuse_enabled: bool = False

@dataclass
class EvalProgress:
    """평가 진행 상태."""
    current: int
    total: int
    current_metric: str
    percent: float

@dataclass
class RunSummary:
    """평가 실행 요약."""
    run_id: str
    dataset_name: str
    model_name: str
    pass_rate: float
    total_test_cases: int
    started_at: datetime
    metrics_evaluated: list[str]

class WebUIPort(Protocol):
    """웹 UI 인바운드 포트."""

    async def run_evaluation(
        self,
        request: EvalRequest,
        *,
        on_progress: Callable[[EvalProgress], None] | None = None,
    ) -> EvaluationRun:
        """평가 실행 (비동기, 진행률 콜백)."""
        ...

    def list_runs(
        self,
        limit: int = 50,
        dataset_name: str | None = None,
        model_name: str | None = None,
    ) -> list[RunSummary]:
        """평가 목록 조회."""
        ...

    def get_run_details(self, run_id: str) -> EvaluationRun:
        """평가 상세 조회."""
        ...

    def generate_report(
        self,
        run_id: str,
        format: Literal["markdown", "html"],
        *,
        include_nlp: bool = True,
        include_causal: bool = True,
    ) -> bytes:
        """보고서 생성."""
        ...
```

### 3.5 상태 관리 전략

```python
# src/evalvault/adapters/inbound/web/session.py
from dataclasses import dataclass, field
from datetime import datetime
import streamlit as st

@dataclass
class WebSession:
    """웹 세션 상태."""
    # 현재 작업 상태
    current_run_id: str | None = None
    is_evaluating: bool = False
    eval_progress: EvalProgress | None = None

    # 필터 상태
    selected_dataset: str | None = None
    selected_model: str | None = None
    selected_metrics: list[str] = field(default_factory=list)

    # 캐시
    runs_cache: list[RunSummary] | None = None
    cache_updated_at: datetime | None = None

    @classmethod
    def get(cls) -> "WebSession":
        """세션 상태 가져오기 (없으면 생성)."""
        if "web_session" not in st.session_state:
            st.session_state.web_session = cls()
        return st.session_state.web_session

    def invalidate_cache(self) -> None:
        """캐시 무효화."""
        self.runs_cache = None
        self.cache_updated_at = None
```

### 3.6 백그라운드 작업 처리

```python
# src/evalvault/adapters/inbound/web/runner.py
from concurrent.futures import ThreadPoolExecutor, Future
from uuid import uuid4
import threading

class EvaluationRunner:
    """평가 실행 관리자 (백그라운드 처리)."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._executor = ThreadPoolExecutor(max_workers=2)
                cls._instance._tasks: dict[str, Future] = {}
                cls._instance._progress: dict[str, EvalProgress] = {}
            return cls._instance

    def start_evaluation(self, request: EvalRequest) -> str:
        """평가 시작, task_id 반환."""
        task_id = str(uuid4())[:8]

        def run_with_progress():
            # 실제 평가 로직
            ...

        future = self._executor.submit(run_with_progress)
        self._tasks[task_id] = future
        return task_id

    def get_progress(self, task_id: str) -> EvalProgress | None:
        """진행률 조회."""
        return self._progress.get(task_id)

    def is_complete(self, task_id: str) -> bool:
        """완료 여부."""
        future = self._tasks.get(task_id)
        return future.done() if future else True

    def get_result(self, task_id: str) -> EvaluationRun | None:
        """결과 조회."""
        future = self._tasks.get(task_id)
        if future and future.done():
            return future.result()
        return None
```

### 3.7 UI 레이아웃 설계

```
┌─────────────────────────────────────────────────────────────────┐
│  EvalVault                                    [🌙] [Settings]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────────────────────────────────┐  │
│  │  Sidebar    │  │  Main Content                            │  │
│  │             │  │                                          │  │
│  │  🏠 Home    │  │  ┌──────────────────────────────────┐   │  │
│  │  📊 Evaluate│  │  │  Page Title                      │   │  │
│  │  📋 History │  │  │                                  │   │  │
│  │  📄 Reports │  │  │  [Content Area]                  │   │  │
│  │             │  │  │                                  │   │  │
│  │  ─────────  │  │  │  - Tables                        │   │  │
│  │             │  │  │  - Charts                        │   │  │
│  │  ⚙️ Settings│  │  │  - Forms                         │   │  │
│  │             │  │  │                                  │   │  │
│  └─────────────┘  └─────────────────────────────────────────┘  │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│  EvalVault v1.3.0 | Powered by Ragas + Langfuse                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.8 색상 팔레트

```python
# src/evalvault/adapters/inbound/web/styles/theme.py
COLORS = {
    "primary": "#3B82F6",      # Blue
    "success": "#10B981",      # Green
    "warning": "#F59E0B",      # Yellow
    "error": "#EF4444",        # Red
    "info": "#6366F1",         # Indigo
    "background": "#0F172A",   # Dark slate (dark mode)
    "surface": "#1E293B",      # Slate (dark mode)
    "text": "#F8FAFC",         # Light (dark mode)
}

PASS_RATE_COLORS = {
    "excellent": "#10B981",    # >= 90%
    "good": "#3B82F6",         # >= 70%
    "warning": "#F59E0B",      # >= 50%
    "critical": "#EF4444",     # < 50%
}
```

---

## Part 4: 구현 계획

### Phase 10: 분석 데이터 저장 완성 (P0)

#### 10.1 CausalAnalysis 저장 구현

**파일:** `src/evalvault/adapters/outbound/storage/sqlite_adapter.py`

```python
def save_causal_analysis(self, analysis: CausalAnalysis) -> str:
    """Causal 분석 결과를 저장합니다."""
    ...

def get_causal_analysis_by_run(self, run_id: str) -> CausalAnalysis | None:
    """특정 실행의 Causal 분석 결과를 조회합니다."""
    ...
```

#### 10.2 Langfuse 분석 스코어 연동

```python
def log_analysis_scores(self, trace_id: str, bundle: AnalysisBundle) -> None:
    """분석 결과를 Langfuse 스코어로 기록."""
    ...
```

#### 10.3 분석 조회 API 강화

```python
def get_analysis_trends(self, metric_name: str, limit: int = 30) -> list[TrendPoint]:
    """메트릭 트렌드 데이터 조회."""
    ...
```

---

### Phase 11: 확장 가능한 보고서 시스템 (P0)

#### 11.1 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│  ReportEngine                                                    │
├─────────────────────────────────────────────────────────────────┤
│  SectionRegistry → Section Interface → OutputRenderer            │
│                                                                  │
│  Built-in Sections:                                              │
│  - HeaderSection (0)                                             │
│  - SummarySection (10)                                           │
│  - StatisticalSection (20)                                       │
│  - NLPSection (30)                                               │
│  - CausalSection (40)                                            │
│  - KoreanRAGSection (50) (NEW)                                   │
│  - RecommendationsSection (90)                                   │
│  - FooterSection (100)                                           │
└─────────────────────────────────────────────────────────────────┘
```

#### 11.2 핵심 인터페이스

```python
class ReportSectionPort(Protocol):
    @property
    def section_id(self) -> str: ...
    @property
    def priority(self) -> int: ...
    def is_applicable(self, bundle: AnalysisBundle) -> bool: ...
    def render(self, bundle: AnalysisBundle) -> SectionContent: ...

class ReportEnginePort(Protocol):
    def register_section(self, section: ReportSectionPort) -> None: ...
    def generate(self, bundle: AnalysisBundle, *, output_format: str) -> str: ...
```

---

### Phase 12: 웹 UI MVP (P0) - Streamlit

#### 12.1 의존성 추가

```toml
# pyproject.toml
[project.optional-dependencies]
web = [
    "streamlit>=1.40.0",
    "plotly>=5.18.0",
    "watchdog>=3.0.0",  # hot reload
]
```

#### 12.2 CLI 진입점 추가

```toml
# pyproject.toml
[project.scripts]
evalvault = "evalvault.adapters.inbound.cli:app"
evalvault-web = "evalvault.adapters.inbound.web.app:main"
```

#### 12.3 구현 단계

```
Phase 12.1: 기반 설정
├── 의존성 추가 (streamlit, plotly)
├── CLI 진입점 추가 (evalvault-web)
├── 기본 앱 구조 생성
└── WebUIPort 인터페이스 정의

Phase 12.2: 홈 페이지
├── 사이드바 네비게이션
├── 대시보드 개요 (최근 평가, 통과율)
└── 빠른 액션 버튼

Phase 12.3: 평가 실행 페이지
├── 데이터셋 업로드 컴포넌트
├── 메트릭 선택 UI
├── 백그라운드 실행 및 진행률
└── 결과 요약 표시

Phase 12.4: 이력 조회 페이지
├── 평가 목록 테이블 (필터/정렬)
├── 상세 결과 페이지
└── 메트릭별 차트

Phase 12.5: 보고서 페이지
├── 보고서 생성 UI
├── 포맷 선택 (MD/HTML)
└── 다운로드 기능
```

---

### Phase 13: 웹 UI 확장 (P1)

#### 13.1 분석 시각화

```
├── NLP 분석 결과 시각화
│   ├── 키워드 워드클라우드
│   ├── 질문 유형 분포 파이차트
│   └── 토픽 클러스터 시각화
├── 인과 분석 결과 시각화
│   ├── 요인-메트릭 영향도 히트맵
│   ├── 인과 관계 다이어그램
│   └── 개선 제안 목록
```

#### 13.2 트렌드 페이지

```
├── 메트릭별 시계열 차트
├── 통과율 추이
└── 모델별 비교
```

#### 13.3 실험 비교 페이지

```
├── A/B 그룹 비교 테이블
├── 통계적 유의성 표시
└── 결론 및 권장사항
```

---

## Part 5: 구현 일정 및 테스트 계획

### 마일스톤

```
Phase 10: 분석 데이터 저장 완성
├── 10.1 CausalAnalysis 저장 구현
├── 10.2 Langfuse 분석 스코어 연동
└── 10.3 분석 조회 API 강화
    └── 테스트: +25 (Unit)

Phase 11: 확장 가능한 보고서 시스템
├── 11.1-11.4 ReportEngine 구현
├── 11.5 설정 파일 기반 구성
└── 11.6 KoreanRAGSection 추가
    └── 테스트: +40 (Unit + Integration)

Phase 12: 웹 UI MVP (Streamlit)
├── 12.1 기반 설정
├── 12.2 홈 페이지
├── 12.3 평가 실행 페이지
├── 12.4 이력 조회 페이지
└── 12.5 보고서 페이지
    └── 테스트: +30 (Unit + Integration + E2E)

Phase 13: 웹 UI 확장
├── 13.1 분석 시각화
├── 13.2 트렌드 페이지
└── 13.3 실험 비교 페이지
    └── 테스트: +20 (Integration)
```

### 예상 테스트 수

| Phase | 예상 테스트 수 | 테스트 유형 |
|-------|---------------|-------------|
| Phase 10 | +25 | Unit |
| Phase 11 | +40 | Unit + Integration |
| Phase 12 | +30 | Unit + Integration + E2E |
| Phase 13 | +20 | Integration |
| **Total** | **+115** | |

---

## Part 6: 설계 원칙

### 확장성 원칙

1. **Open/Closed Principle**
   - 새 섹션 추가 시 기존 코드 수정 없이 `register_section()` 호출만으로 가능
   - 새 페이지 추가 시 pages/ 폴더에 파일 추가만으로 가능 (Streamlit 자동 감지)

2. **Dependency Inversion**
   - 웹 UI가 WebUIPort 인터페이스에 의존
   - 도메인 서비스는 직접 접근하지 않음

3. **Single Responsibility**
   - 각 페이지는 하나의 기능만 담당
   - 컴포넌트는 재사용 가능하게 설계

### 설정 우선 원칙

1. **YAML 설정으로 제어:**
   - 포함할 보고서 섹션
   - 테마 색상
   - 기본 메트릭 선택

2. **코드 수정 필요:**
   - 새로운 페이지
   - 새로운 컴포넌트
   - 새로운 차트 유형

---

## Part 7: 리스크 및 대안

### 리스크 분석

| 리스크 | 영향 | 확률 | 대응 |
|--------|------|------|------|
| Streamlit 성능 한계 (대용량 데이터) | Medium | Medium | 페이지네이션, 캐싱 |
| 백그라운드 작업 상태 관리 복잡 | Medium | Medium | Redis 캐시 도입 |
| 동시 사용자 문제 | Low | Low | 세션 격리 강화 |
| PDF 변환 복잡 | Low | Medium | HTML to PDF 서비스 활용 |

### 대안 계획

1. **Streamlit 한계 시:**
   - Panel 또는 Dash 시도
   - 필요 시 FastAPI + React 마이그레이션

2. **복잡한 시각화 필요 시:**
   - D3.js 임베딩
   - Apache ECharts 사용

---

## Appendix: 참조 파일

### 현재 구현 파일

| 파일 | 설명 |
|------|------|
| `sqlite_adapter.py:523-898` | 분석 저장 메서드 |
| `langfuse_adapter.py:208-481` | `log_evaluation_run()` 구현 |
| `markdown_adapter.py:1-446` | 현재 보고서 어댑터 |
| `report_port.py:1-53` | 현재 ReportPort 인터페이스 |
| `analysis.py:1-520` | 분석 엔티티 정의 |
| `cli.py` | CLI 어댑터 (2,426줄) |

### 관련 문서

| 문서 | 설명 |
|------|------|
| `docs/ROADMAP.md` | 전체 개발 로드맵 |
| `docs/ARCHITECTURE.md` | Hexagonal Architecture 설명 |
| `docs/STRATEGIC_DIRECTION.md` | 전략적 방향 |

---

*Document generated: 2025-12-30*
*Updated: Web UI MVP plan integrated (Streamlit, reduced scope)*
