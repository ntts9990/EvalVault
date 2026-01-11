# EvalVault 개발 백서

> **버전**: 1.1.0 (개발중)
> **작성일**: 2026-01-11
> **목적**: EvalVault 프로젝트의 아키텍처, 구현, 사용법을 정리한 기술 문서

---

**개발 상태 메모**:
- **초안 완료**: 2026-01-11
- **최근 변경**:
  - gpt-4o-mini → gpt-5-mini로 기본 모델 업데이트
  - VisualSpace/InsightSpace 기능 상세 추가 (개발 진행 중)
  - 개발 중인 기능: VisualSpace, InsightSpace
  - 완성된 기능: 평가, Domain Memory, Analysis Pipeline, Benchmark, Phoenix 연동
- **문제 해결 보류**: 일부 코드 타입 에러 (evaluator.py) 확인 필요

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [아키텍처 설계](#2-아키텍처-설계)
3. [주요 컴포넌트 상세](#3-주요-컴포넌트-상세)
4. [전문가 관점 통합 설계](#4-전문가-관점-통합-설계)
5. [구현 상세](#5-구현-상세)

---

## 1. 프로젝트 개요

### 1.1 EvalVault란 무엇인가?

EvalVault는 **RAG(Retrieval-Augmented Generation) 시스템의 품질 측정·관측·개선**을 한 번에 처리하는 평가 플랫폼입니다.

**핵심 목표**:
- **평가(Evaluation)**: 데이터셋 기반으로 다양한 LLM/리트리버/프롬프트 조합을 실험하고 점수/threshold 관리
- **관측(Observability)**: Stage 단위 이벤트와 메트릭, Langfuse/Phoenix 트레이스를 한 Run ID로 연결
- **학습(Domain Memory)**: 과거 실행으로부터 도메인 지식/패턴을 축적해 threshold, 컨텍스트, 리포트를 자동 보정
- **분석(Analysis Pipelines)**: 통계·NLP·인과 모듈이 포함된 DAG 파이프라인으로 결과를 다각도로 해석

### 1.2 왜 EvalVault인가?

**해결하는 문제**:
1. **"모델/프롬프트/리트리버를 바꿨을 때 정말 좋아진 건지 수치로 설명하기 어렵다."**
   - 점수만 봐서는 개선의 원인을 파악하기 어렵고, 실험 간 비교가 일관되지 않습니다.
2. **"LLM 로그, 검색 로그, 트레이스가 여러 곳에 흩어져 있고 한 눈에 병목·품질 이슈를 잡기 힘들다."**
   - 각 단계별 데이터가 분산되어 있어 전체 파이프라인을 통합적으로 분석하기 어렵습니다.
3. **"팀/프로젝트마다 ad-hoc 스크립트가 늘어나 재현성과 회귀 테스트가 깨지기 쉽다."**
   - 표준화된 평가 워크플로가 없어 실험 결과의 재현성과 비교가 어렵습니다.

### 1.3 5대 핵심 축

| 축 | 설명 | 구현 |
|------|------|------|
| **평가** | Ragas 0.4.x 메트릭과 커스텀 메트릭을 조합한 평가 | `RagasEvaluator` |
| **관측** | Langfuse·Phoenix 트레이서와 연동된 Stage-level 트레이싱 | `TracerPort` |
| **표준 연동** | OpenTelemetry + OpenInference 기반 Open RAG Trace 표준 | `OpenRagTraceAdapter` |
| **학습** | Domain Memory로 과거 결과를 학습하여 threshold 자동 조정 | `DomainLearningHook` |
| **분석** | 통계·NLP·인과 분석 모듈이 포함된 DAG 파이프라인 | `AnalysisService` |

---

## 2. 아키텍처 설계

### 2.1 Hexagonal Architecture

EvalVault는 **Hexagonal Architecture (Ports & Adapters)** 패턴을 사용하여 핵심 비즈니스 로직과 외부 기술 구현을 완전히 분리합니다.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              EVALVAULT ARCHITECTURE                                  │
│                        (Hexagonal Architecture / Ports & Adapters)                   │
│                                                                              │
│  이 아키텍처는 Alistair Cockburn의 Hexagonal Architecture와 Robert C. Martin의      │
│  Clean Architecture 원칙을 결합하여, 도메인 로직을 외부 의존성으로부터    │
│  완전히 격리하고 테스트 가능하며 확장 가능한 시스템을 구축합니다.         │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  ADAPTERS LAYER                                  │
│                          (외부 세계와의 인터페이스 구현)                              │
│                                                                              │
│  어댑터는 외부 시스템(CLI, 파일 시스템, LLM API, 데이터베이스 등)과 도메인         │
│  계층 사이의 변환 계층입니다. 어댑터는 포트 인터페이스를 구현하여 도메인과 통신합니다. │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────┐                    ┌───────────────────────────────────┐
│      INBOUND ADAPTERS             │                    │      OUTBOUND ADAPTERS            │
│   (입력 어댑터 - 사용자 입력)      │                    │   (출력 어댑터 - 외부 시스템)      │
│                                                                                              │
│  목적: 외부에서 들어오는 요청을    │                    │  목적: 도메인이 필요로 하는       │
│        도메인 서비스로 변환         │                    │        외부 서비스를 제공          │
│                                                                                              │
│  책임:                              │                    │  책임:                             │
│  - CLI 명령 파싱                    │                    │  - 파일 시스템 접근                │
│  - 사용자 입력 검증                 │                    │  - LLM API 호출                    │
│  - 도메인 서비스 호출               │                    │  - 데이터베이스 쿼리              │
│  - 결과 포맷팅 및 출력              │                    │  - 추적 시스템 연동                │
│                                                                                              │
├───────────────────────────────────┤                    ├───────────────────────────────────┤
│                                   │                    │                                   │
│  adapters/inbound/                │                    │  adapters/outbound/               │
│  ├── cli.py                       │                    │  ├── dataset/                     │
│  │   └── Typer 기반 CLI            │                    │  │   ├── base.py                  │
│  │                               │                    │  │   ├── csv_loader.py             │
│  │                               │                    │  │   ├── excel_loader.py           │
│  │                               │                    │  │   ├── json_loader.py            │
│  │                               │                    │  │   └── loader_factory.py        │
│  │                               │                    │  │                                 │
│  │  └── web/                       │                    │  ├── llm/                          │
│  │      ├── adapter.py             │                    │  │   ├── __init__.py               │
│  │      ├── app.py                │                    │  │   ├── anthropic_adapter.py      │
│  │      ├── components/           │                    │  │   ├── ollama_adapter.py         │
│  │      ├── ...                   │                    │  │   ├── openai_adapter.py         │
│  │                               │                    │  │   └── vllm_adapter.py           │
│  │                               │                    │  │                                 │
│  │                               │                    │  ├── storage/                      │
│  │                               │                    │  │   ├── sqlite_adapter.py         │
│  │                               │                    │  │   └── postgres_adapter.py       │
│  │                               │                    │  │                                 │
│  │                               │                    │  ├── tracker/                      │
│  │                               │                    │  │   ├── langfuse_adapter.py       │
│  │                               │                    │  │   └── phoenix_adapter.py        │
│  │                               │                    │  │                                 │
│  │                               │                    │  ├── cache/                        │
│  │                               │                    │  │   └── memory_cache.py            │
│  │                               │                    │  │                                 │
│  │                               │                    │  ├── domain_memory/                │
│  │                               │                    │  │   └── sqlite_adapter.py         │
│  │                               │                    │  │                                 │
│  │                               │                    │  └── report/                        │
│  │                               │                    │      └── markdown_adapter.py      │
└───────────────────────────────────┘                    └───────────────────────────────────┘
         │                                                          │
         │  [의존성 방향: 어댑터 → 포트]                             │
         │                                                          │
         ▼                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    PORTS LAYER                                       │
│                          (인터페이스 정의 - 계약)                                     │
│                                                                              │
│  포트는 도메인과 외부 세계 사이의 계약(Contract)을 정의합니다. 포트는 인터페이스     │
│  또는 프로토콜로 정의되며, 도메인은 포트를 통해 외부 서비스를 사용합니다.           │
│                                                                              │
│  핵심 원칙:                                                                          │
│  - 포트는 도메인 계층에 속함                                                         │
│  - 포트는 "무엇을" 정의하지만 "어떻게"는 정의하지 않음                               │
│  - 어댑터는 포트를 구현함                                                            │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────┐                    ┌───────────────────────────────────┐
│      INBOUND PORTS                 │                    │      OUTBOUND PORTS                 │
│   (입력 포트 - 사용 사례 정의)      │                    │   (출력 포트 - 외부 의존성 정의)    │
│                                                                                              │
│  목적: 도메인이 제공하는 기능을     │                    │  목적: 도메인이 필요로 하는         │
│        외부에 노출하는 인터페이스   │                    │        외부 서비스를 정의           │
│                                                                                              │
│  특징:                              │                    │  특징:                              │
│  - Protocol 기반 (Python typing)    │                    │  - ABC 또는 Protocol 기반          │
│  - 도메인 서비스가 구현              │                    │  - 어댑터가 구현                   │
│  - 어댑터가 호출                     │                    │  - 도메인 서비스가 사용            │
│                                                                                              │
├───────────────────────────────────┤                    ├───────────────────────────────────┤
│                                   │                    │                                   │
│  ports/inbound/                   │                    │  ports/outbound/                 │
│  ├── evaluator_port.py            │                    │  ├── dataset_port.py               │
│  ├── analysis_pipeline_port.py    │                    │  ├── llm_port.py                     │
│  ├── learning_hook_port.py        │                    │  ├── storage_port.py               │
│  └── web_port.py                  │                    │  ├── tracker_port.py                │
│                                   │                    │  ├── analysis_port.py              │
│                                   │                    │  └── domain_memory_port.py          │
│                                   │                    │                                   │
└───────────────────────────────────┘                    └───────────────────────────────────┘
         │                                                          │
         │  [의존성 방향: 도메인 → 포트]                             │
         │                                                          │
         └──────────────────┬───────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  DOMAIN LAYER                                        │
│                          (핵심 비즈니스 로직)                                        │
│                                                                              │
│  도메인 계층은 시스템의 핵심 비즈니스 로직을 포함합니다. 이 계층은 외부 의존성에    │
│  대해 전혀 알지 못하며, 오직 포트 인터페이스를 통해서만 외부와 통신합니다.          │
│                                                                              │
│  핵심 원칙:                                                                          │
│  - 순수한 비즈니스 로직만 포함                                                       │
│  - 외부 프레임워크나 라이브러리에 의존하지 않음                                      │
│  - 테스트 가능하며 독립적으로 실행 가능                                              │
│  - 도메인 전문가가 이해할 수 있는 언어로 작성                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  domain/                                                                            │
│  ├── entities/                          (도메인 엔티티)         │
│  │   ├── dataset.py                    ─ TestCase, Dataset          │
│  │   ├── result.py                     ─ EvaluationRun, Result     │
│  │   ├── experiment.py                 ─ Experiment, Group            │
│  │   ├── analysis.py                    ─ AnalysisBundle            │
│  │   └── ...                           │
│  │                                                                              │
│  ├── metrics/                            (평가 메트릭)        │
│  │   ├── insurance.py                  ─ 보험 도메인 메트릭           │
│  │   └── ...                           │
│  │                                                                              │
│  └── services/                          (도메인 서비스)       │
│      ├── evaluator.py                  ─ RagasEvaluator              │
│      ├── analysis_service.py           ─ AnalysisService              │
│      ├── experiment_manager.py         ─ ExperimentManager            │
│      └── ...                           │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 설계 원칙

| 원칙 | 설명 | 적용 |
|------|------|------|
| **단일 책임 (Single Responsibility)** | 각 클래스는 하나의 책임만 가져야 함 | 엔티티, 서비스, 포트 분리 |
| **개방-폐쇄 (Open/Closed)** | 확장에는 열려 있되, 수정에는 닫혀 있음 | 포트 인터페이스, 플러그인 시스템 |
| **리스코프 치환 (Liskov Substitution)** | 하위 타입은 상위 타입으로 치환 가능 | 포트, 어댑터 계층 |
| **인터페이스 분리 (Interface Segregation)** | 클라이언트는 사용하지 않는 인터페이스 의존하지 않음 | 세부 포트 정의 |
| **의존성 역전 (Dependency Inversion)** | 도메인이 추상(포트)에 의존, 구현체에 의존하지 않음 | 도메인 → 포트 ← 어댑터 |

---

## 3. 주요 컴포넌트 상세

### 3.1 도메인 엔티티

#### Dataset 엔티티

```python
@dataclass
class TestCase:
    """단일 평가 케이스 (Ragas SingleTurnSample과 매핑)."""

    id: str
    question: str      # user_input
    answer: str        # response
    contexts: list[str] # retrieved_contexts
    ground_truth: str | None = None  # reference
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_ragas_dict(self) -> dict[str, Any]:
        """Ragas EvaluationDataset 형식으로 변환."""
        result = {
            "user_input": self.question,
            "response": self.answer,
            "retrieved_contexts": self.contexts,
        }
        if self.ground_truth:
            result["reference"] = self.ground_truth
        return result


@dataclass
class Dataset:
    """평가용 데이터셋."""

    name: str
    version: str
    test_cases: list[TestCase]
    metadata: dict[str, Any] = field(default_factory=dict)
    source_file: str | None = None  # CSV/Excel 원본 파일 경로
    thresholds: dict[str, float] = field(default_factory=dict)  # 메트릭별 임계값

    def get_threshold(self, metric_name: str, default: float = 0.7) -> float:
        """특정 메트릭의 임계값 반환."""
        return self.thresholds.get(metric_name, default)
```

#### EvaluationRun 엔티티

```python
@dataclass
class EvaluationRun:
    """전체 평가 실행 결과."""

    run_id: str = field(default_factory=lambda: str(uuid4()))
    dataset_name: str = ""
    dataset_version: str = ""
    model_name: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None

    # 개별 결과
    results: list[TestCaseResult] = field(default_factory=list)

    # 메타데이터
    metrics_evaluated: list[str] = field(default_factory=list)
    thresholds: dict[str, float] = field(default_factory=dict)

    # 리소스 사용량
    total_tokens: int = 0
    total_cost_usd: float | None = None

    # Langfuse 연동
    langfuse_trace_id: str | None = None
    tracker_metadata: dict[str, Any] = field(default_factory=dict)
    retrieval_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def total_test_cases(self) -> int:
        return len(self.results)

    @property
    def passed_test_cases(self) -> int:
        """모든 메트릭을 통과한 테스트 케이스 수."""
        return sum(1 for r in self.results if r.all_passed)

    @property
    def pass_rate(self) -> float:
        """테스트 케이스 통과율."""
        if not self.results:
            return 0.0
        return self.passed_test_cases / self.total_test_cases
```

### 3.2 도메인 서비스

#### RagasEvaluator

```python
class RagasEvaluator:
    """Ragas 기반 평가자 서비스."""

    def __init__(
        self,
        llm_port: LLMPort,
        metrics: list[str],
        threshold_profile: str | None = None,
    ):
        self.llm_port = llm_port
        self.metrics = metrics
        self.threshold_profile = threshold_profile

    def evaluate(self, dataset: Dataset) -> EvaluationRun:
        """데이터셋을 평가하여 EvaluationRun 반환."""
        # 1. Ragas로 변환
        ragas_dataset = dataset.to_ragas_list()

        # 2. Ragas 메트릭으로 평가
        results = self._run_ragas_evaluation(ragas_dataset)

        # 3. 결과를 EvaluationRun으로 변환
        return self._build_evaluation_run(results, dataset)
```

#### AnalysisService

```python
class AnalysisService:
    """분석 서비스 - 통계/NLP/인과 분석 오케스트레이션."""

    def __init__(
        self,
        analysis_port: AnalysisPort,
        nlp_port: NLPAnalysisPort,
        causal_port: CausalAnalysisPort,
    ):
        self.analysis_port = analysis_port
        self.nlp_port = nlp_port
        self.causal_port = causal_port

    def analyze_run(self, run: EvaluationRun) -> AnalysisBundle:
        """평가 실행 결과를 다각도로 분석."""
        # 1. 통계 분석
        stats = self.analysis_port.statistical_analysis(run)

        # 2. NLP 분석
        nlp_results = self.nlp_port.analyze(run)

        # 3. 인과 분석
        causal_results = self.causal_port.analyze(run)

        # 4. 결과 통합
        return AnalysisBundle(
            statistics=stats,
            nlp=nlp_results,
            causal=causal_results,
        )
```

### 3.3 포트 인터페이스

#### LLMPort

```python
class LLMPort(ABC):
    """LLM adapter interface for Ragas metrics evaluation."""

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name being used."""
        pass

    @abstractmethod
    def as_ragas_llm(self) -> Any:
        """Return a LLM instance compatible with Ragas."""
        pass

    def get_thinking_config(self) -> ThinkingConfig:
        """Get thinking/reasoning configuration for this adapter."""
        return ThinkingConfig(enabled=False)

    def supports_thinking(self) -> bool:
        """Check if this adapter supports thinking/reasoning mode."""
        return self.get_thinking_config().enabled
```

#### StoragePort

```python
class StoragePort(Protocol):
    """평가 결과 저장을 위한 포트 인터페이스."""

    def save_run(self, run: EvaluationRun) -> str:
        """평가 실행 결과를 저장합니다."""
        ...

    def get_run(self, run_id: str) -> EvaluationRun:
        """저장된 평가 실행 결과를 조회합니다."""
        ...

    def list_runs(
        self,
        limit: int = 100,
        dataset_name: str | None = None,
        model_name: str | None = None,
    ) -> list[EvaluationRun]:
        """저장된 평가 실행 결과 목록을 조회합니다."""
        ...
```

### 3.4 어댑터 구현

#### LLM Adapters

```python
class OpenAIAdapter(LLMPort):
    """OpenAI LLM adapter."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def get_model_name(self) -> str:
        return self.model

    def as_ragas_llm(self) -> Any:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=self.api_key, model=self.model)


class OllamaAdapter(LLMPort):
    """Ollama LLM adapter."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    def get_model_name(self) -> str:
        return self.model

    def as_ragas_llm(self) -> Any:
        from langchain_community import ChatOllama
        return ChatOllama(base_url=self.base_url, model=self.model)
```

#### Storage Adapters

```python
class SQLiteAdapter:
    """SQLite 저장소 어댑터."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_schema()

    def save_run(self, run: EvaluationRun) -> str:
        """평가 실행 결과를 SQLite에 저장."""
        # 1. INSERT INTO evaluation_runs
        # 2. INSERT INTO test_case_results
        # 3. INSERT INTO metric_scores
        return run.run_id

    def get_run(self, run_id: str) -> EvaluationRun:
        """저장된 평가 실행 결과를 조회."""
        # SELECT * FROM evaluation_runs WHERE run_id = ?
        # SELECT * FROM test_case_results WHERE run_id = ?
        # SELECT * FROM metric_scores WHERE run_id = ?
        pass
```

---

## 4. 전문가 관점 통합 설계

### 4.1 인지심리학자 관점

**핵심 원칙**:
- **인지 부하 최소화**: 한 화면에 7±2개 정보 청크 유지
- **패턴 인식 촉진**: 유사한 패턴을 시각적으로 그룹화
- **주의 집중 유도**: 중요한 정보를 시각적 계층으로 강조
- **작업 기억 보조**: 컨텍스트 전환 최소화 (모달/탭 최소화)

**구체적 적용**:
1. **점진적 정보 공개 (Progressive Disclosure)**
   - 기본: 요약 메트릭 + 핵심 인사이트
   - 확장: 클릭/호버로 상세 정보 표시
   - 심화: Phoenix 링크로 전문 분석

2. **시각적 그룹핑**
   - 성공/실패 케이스를 색상으로 즉시 구분
   - 클러스터별로 공간적으로 그룹화
   - 단계별로 시각적 구분 (Retrieval → Rerank → Generation)

3. **인지 부하 관리**
   - 복잡한 차트는 Phoenix로 위임
   - Frontend는 핵심 인사이트만 표시
   - 필터/검색으로 정보 범위 제한

### 4.2 UI/UX 전문가 관점

**핵심 원칙**:
- **사용자 워크플로우 최적화**: 자주 하는 작업을 빠르게
- **피드백 제공**: 모든 액션에 즉각적 피드백
- **에러 방지**: 잘못된 입력 사전 차단
- **접근성**: 키보드 네비게이션, 스크린 리더 지원

**구체적 적용**:
1. **워크플로우 최적화**
   - 평가 실행 → 결과 확인 → Phoenix 분석 → 개선 가이드
   - 각 단계에서 다음 액션을 명확히 제시
   - Phoenix 링크를 적절한 시점에 표시

2. **인터랙션 디자인**
   - 호버: 상세 정보 미리보기
   - 클릭: 상세 페이지/모달
   - 드래그: 비교할 Run 선택

3. **피드백 메커니즘**
   - 로딩 상태: 스켈레톤 UI
   - 성공/실패: 토스트 알림
   - 진행 상황: 프로그레스 바

### 4.3 시각 정보 전문가 관점

**핵심 원칙**:
- **정보 계층 구조**: 중요도에 따른 시각적 강조
- **시각적 인코딩 일관성**: 색상/크기/형태의 의미 일관성
- **공간 활용**: 2D/3D 공간을 의미 있게 활용
- **비교 용이성**: 비교해야 할 항목을 인접 배치

**구체적 적용**:
1. **색상 인코딩 체계**
   - 성공: 녹색 계열 (Green 500-600)
   - 경고: 노란색 계열 (Yellow 400-500)
   - 실패: 빨간색 계열 (Red 500-600)
   - 정보: 파란색 계열 (Blue 500-600)
   - 중립: 회색 계열 (Gray 400-500)

2. **크기 인코딩**
   - 메트릭 점수 → 점 크기 (높을수록 큰 점)
   - 중요도 → 폰트 크기/두께

3. **공간 배치**
   - 시간 축: 왼쪽 → 오른쪽
   - 계층 구조: 위 → 아래
   - 비교: 나란히 배치

### 4.4 정보공학 전문가 관점

**핵심 원칙**:
- **정보 아키텍처**: 논리적 그룹핑과 계층 구조
- **데이터 구조화**: 일관된 데이터 모델
- **확장성**: 새로운 메트릭/단계 추가 용이
- **재사용성**: 컴포넌트 기반 설계

**구체적 적용**:
1. **정보 구조**
   - Run → Test Case → Stage → Metric 계층
   - 각 레벨에서 적절한 집계/상세 정보 제공

2. **데이터 모델**
   - StageMetric, EvaluationResult 등 일관된 엔티티
   - API 응답 구조 표준화

3. **확장성**
   - 새로운 메트릭 타입 추가 시 최소 변경
   - 플러그인 방식의 시각화 컴포넌트

### 4.5 교육공학 전문가 관점

**핵심 원칙**:
- **학습 효과 극대화**: 정보를 이해하기 쉽게 전달
- **점진적 학습**: 기본 → 고급 순서로 정보 제공
- **피드백 루프**: 즉각적 피드백으로 학습 촉진

**구체적 적용**:
1. **점진적 정보 제공**
   - 초보자: 요약 + 간단한 설명
   - 중급자: 상세 메트릭 + 비교
   - 고급자: Phoenix 링크 + 원시 데이터

2. **학습 지원**
   - 툴팁으로 용어 설명
   - 예시 케이스 제공
   - 개선 가이드 연결

### 4.6 색채 전문가 관점

**핵심 원칙**:
- **색상 의미론**: 문화적/보편적 색상 의미 활용
- **색맹 접근성**: 색상만으로 정보 전달하지 않음
- **색상 조화**: 조화로운 색상 팔레트 사용

**구체적 적용**:
1. **색상 의미**
   - 성공: 녹색 (Green)
   - 경고: 노란색 (Yellow/Amber)
   - 실패: 빨간색 (Red)
   - 정보: 파란색 (Blue)
   - 중립: 회색 (Gray)

2. **접근성**
   - 색상 + 아이콘/패턴으로 정보 전달
   - WCAG 2.1 AA 기준 준수 (대비율 4.5:1 이상)

3. **색상 팔레트**
   - Tailwind CSS 기본 팔레트 활용
   - 다크 모드 지원

### 4.7 컴퓨터 공학 전문가 관점

**핵심 원칙**:
- **성능**: 렌더링 최적화, 가상화, 지연 로딩
- **확장성**: 대용량 데이터 처리
- **유지보수성**: 모듈화, 테스트 가능성
- **표준 준수**: 웹 표준, 접근성 표준

**구체적 적용**:
1. **성능 최적화**
   - 대용량 데이터셋: 가상 스크롤
   - 복잡한 차트: Web Workers 활용
   - 이미지/차트: 지연 로딩

2. **확장성**
   - 컴포넌트 기반 아키텍처
   - 플러그인 시스템

3. **유지보수성**
   - 단일 책임 원칙
   - 의존성 주입
   - 테스트 가능성

---

## 5. 구현 상세

### 5.1 환경 설정

#### Pydantic Settings

```python
class Settings(BaseSettings):
    """Application configuration settings."""

    # Profile Configuration (YAML 기반 모델 프로필)
    evalvault_profile: str | None = Field(
        default=None,
        description="Model profile name (dev, prod, openai). Overrides individual settings.",
    )

    # Database Paths
    evalvault_db_path: str = Field(
        default="data/db/evalvault.db",
        description="SQLite database path for API/CLI storage.",
    )
    evalvault_memory_db_path: str = Field(
        default="data/db/evalvault_memory.db",
        description="SQLite database path for Domain Memory storage.",
    )

    # LLM Provider Selection
    llm_provider: str = Field(
        default="ollama",
        description="LLM provider: 'openai', 'ollama', or 'vllm'",
    )

    # OpenAI Configuration
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    openai_base_url: str | None = Field(
        default=None, description="Custom OpenAI API base URL (optional)"
    )
    openai_model: str = Field(
        default="gpt-5-mini",
        description="OpenAI model to use for evaluation",
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model"
    )

    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL",
    )
    ollama_model: str = Field(
        default="gemma3:1b",
        description="Ollama model name for evaluation",
    )
```

#### models.yaml 구조

```yaml
profiles:
  dev:
    llm:
      provider: ollama
      model: gemma3:1b
    embedding:
      provider: ollama
      model: qwen3-embedding:0.6b

  prod:
    llm:
      provider: openai
      model: gpt-4o-mini
    embedding:
      provider: openai
      model: text-embedding-3-small

  vllm:
    llm:
      provider: vllm
      model: gpt-oss-120b
    embedding:
      provider: vllm
      model: qwen3-embedding:0.6b
```

### 5.2 CLI 사용법

```bash
# 평가 실행
evalvault run dataset.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db

# 히스토리 확인
evalvault history --db data/db/evalvault.db

# 결과 분석
evalvault analyze <RUN_ID> --db data/db/evalvault.db

# 비교 분석
evalvault analyze-compare <RUN_A> <RUN_B> --db data/db/evalvault.db
```

### 5.3 Web API 사용법

```python
# FastAPI 서버 실행
evalvault serve-api --reload

# React 프론트엔드 실행
cd frontend
npm install
npm run dev
```

**API 엔드포인트**:
- `POST /runs/` - 평가 실행
- `GET /runs/` - 평가 결과 목록
- `GET /runs/{run_id}` - 특정 실행 결과
- `POST /analysis/` - 분석 실행
- `GET /analysis/{result_id}` - 분석 결과

### 5.4 확장 가이드

#### 새 메트릭 추가

```python
from evalvault.domain.metrics import BaseMetric

class MyCustomMetric(BaseMetric):
    name = "my_custom_metric"
    description = "My custom evaluation metric"

    def score(self, test_case: TestCase) -> float:
        # 커스텀 로직
        return 0.85
```

#### 새 LLM 추가

```python
from evalvault.ports.outbound.llm_port import LLMPort

class MyLLMAdapter(LLMPort):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def get_model_name(self) -> str:
        return self.model

    def as_ragas_llm(self) -> Any:
        # LangChain LLM 래퍼 반환
        pass
```

---

## 6. 결론

EvalVault는 **Hexagonal Architecture**를 기반으로 설계된 RAG 평가/분석 플랫폼으로, 다음 특징을 가집니다:

1. **도메인 로직 격리**: 포트/어댑터 패턴으로 외부 의존성으로부터 완전히 독립
2. **확장 가능한 아키텍처**: 플러그인 방식의 메트릭, LLM, 저장소 추가 가능
3. **전문가 관점 통합**: 인지심리학, UI/UX, 시각화, 정보공학, 교육공학, 색채, 컴퓨터공학 관점 통합
4. **실용적인 도구**: CLI와 Web UI가 동일한 DB/트레이스 위에서 동작
5. **지속적 개선 루프**: Domain Memory와 Analysis Pipeline을 통해 자동 개선

이 백서는 EvalVault를 개발하고 사용하는 데 필요한 모든 기술 정보를 제공합니다.

---

**작성일**: 2026-01-11
**버전**: 1.0.0
