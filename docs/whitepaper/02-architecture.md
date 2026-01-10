## 제2부: 아키텍처 설계

### 2.1 설계 방법론: Hexagonal + Clean + DDD

### 2.1.1 Hexagonal Architecture (육각형 아키텍처)

**원작자**: Alistair Cockburn

**핵심 개념**:
- **포트 (Port)**: 애플리케이션과 외부 세계 사이의 인터페이스
  - **Inbound Port**: 애플리케이션이 제공하는 기능 (사용 사례)
  - **Outbound Port**: 애플리케이션이 필요로 하는 외부 서비스
- **어댑터 (Adapter)**: 포트를 구현하는 구체적인 기술
  - **Inbound Adapter**: 외부 요청을 애플리케이션으로 변환 (예: CLI, REST API)
  - **Outbound Adapter**: 애플리케이션 요청을 외부 시스템으로 변환 (예: 데이터베이스, API 클라이언트)
- **도메인 (Domain)**: 핵심 비즈니스 로직이 위치하는 계층

**EvalVault 적용**:
```
                    ┌─────────────────────┐
                    │   External World    │
                    │ (Users, File, DB)  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │    ADAPTERS        │
                    │  (구현 계층)        │
                    └──────────┬───────────┘
                               │ depends on
                    ┌──────────▼───────────┐
                    │      PORTS         │
                    │ (인터페이스 계층)  │
                    └──────────┬───────────┘
                               │ depends on
                    ┌──────────▼───────────┐
                    │      DOMAIN        │
                    │ (비즈니스 로직)     │
                    └──────────────────────┘
```

**코드 예시**:
```python
# 포트 정의 (ports/outbound/llm_port.py)
from abc import ABC, abstractmethod

class LLMPort(ABC):
    """LLM adapter interface for Ragas metrics evaluation."""

    @abstractmethod
    def get_model_name(self) -> str:
        """모델 이름 반환"""
        pass

    @abstractmethod
    def as_ragas_llm(self):
        """Ragas 호환 LLM 인스턴스 반환"""
        pass

# 어댑터 구현 (adapters/outbound/llm/openai_adapter.py)
from langchain_openai import ChatOpenAI

class OpenAIAdapter(LLMPort):
    """OpenAI LLM adapter."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._ragas_llm = llm_factory(
            model=settings.openai_model,
            provider="openai",
            api_key=settings.openai_api_key,
        )

    def get_model_name(self) -> str:
        return self._settings.openai_model

    def as_ragas_llm(self):
        return self._ragas_llm

# 도메인 서비스 사용 (domain/services/evaluator.py)
class RagasEvaluator:
    async def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,  # 포트 인터페이스에 의존
    ) -> EvaluationRun:
        """평가 실행 - 핵심 비즈니스 로직"""
        ragas_llm = llm.as_ragas_llm()
        # 평가 로직...
```

### 2.1.2 Clean Architecture (클린 아키텍처)

**원작자**: Robert C. Martin (Uncle Bob)

**핵심 원칙**:

**의존성 규칙 (Dependency Rule)**:
```
의존성 방향: 외부 → 내부
┌─────────────────────────────────────────┐
│  Adapters (외부 계층)                   │
│  └─> Ports (인터페이스)                 │
│      └─> Domain (핵심 로직)             │
└─────────────────────────────────────────┘
```

**엔티티 규칙 (Entity Rule)**:
- 도메인 엔티티는 가장 안쪽 계층에 위치
- 비즈니스 규칙을 캡슐화
- 외부 의존성이 없음

**사용 사례 규칙 (Use Case Rule)**:
- 애플리케이션 특화 동작 (Use Case)는 도메인 서비스에 구현
- 어댑터는 Use Case를 호출하기만 함

**EvalVault 적용**:

```python
# 의존성 규칙 적용
# ✅ 올바른 예: 도메인이 포트 인터페이스에만 의존
from evalvault.ports.outbound.llm_port import LLMPort

class RagasEvaluator:
    def __init__(self, llm: LLMPort):  # 인터페이스에 의존
        self._llm = llm

# ❌ 잘못된 예: 도메인이 어댑터에 직접 의존
from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter

class RagasEvaluator:
    def __init__(self):
        self._llm = OpenAIAdapter()  # 구체적인 구현에 의존
```

### 2.1.3 Domain-Driven Design (도메인 주도 설계)

**원작자**: Eric Evans

**핵심 개념**:

**도메인 엔티티 (Domain Entity)**:
- 비즈니스 로직을 캡슐화한 불변 객체
- 도메인 전문가가 이해할 수 있는 언어로 작성

**도메인 서비스 (Domain Service)**:
- 여러 엔티티에 걸친 비즈니스 로직
- 상태가 없는 (stateless) 서비스

**집합 (Aggregate)**:
- 관련된 엔티티의 그룹
- 일관성 경계 정의

**값 객체 (Value Object)**:
- 식별자 없이 속성만으로 정의되는 객체
- 불변성 보장

**EvalVault 적용**:

```python
# 도메인 엔티티 (domain/entities/dataset.py)
@dataclass
class Dataset:
    """평가용 데이터셋."""
    name: str
    version: str
    test_cases: list[TestCase]
    thresholds: dict[str, float] = field(default_factory=dict)

    # 비즈니스 규칙 캡슐화
    def get_threshold(self, metric_name: str, default: float = 0.7) -> float:
        """비즈니스 규칙: 임계값 조회"""
        return self.thresholds.get(metric_name, default)

    # 불변성 보장
    def with_threshold(self, metric_name: str, value: float) -> 'Dataset':
        """새로운 thresholds를 가진 복사본 반환"""
        new_thresholds = {**self.thresholds, metric_name: value}
        return dataclasses.replace(self, thresholds=new_thresholds)

# 도메인 서비스 (domain/services/evaluator.py)
class RagasEvaluator:
    """Ragas 기반 RAG 평가 서비스."""

    def __init__(self):
        # 상태가 없는 서비스
        pass

    async def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
    ) -> EvaluationRun:
        """평가 실행 오케스트레이션"""
        # 1. 임계값 해석 (비즈니스 규칙)
        resolved_thresholds = self._resolve_thresholds(dataset, metrics)

        # 2. 평가 실행 (Ragas 메트릭)
        eval_results = await self._evaluate_with_ragas(dataset, metrics, llm)

        # 3. 결과 집계 (비즈니스 로직)
        run = self._aggregate_results(dataset, metrics, eval_results, resolved_thresholds)

        return run
```

### 2.2 전체 구조 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              EVALVAULT ARCHITECTURE                              │
│                        (Hexagonal Architecture / Ports & Adapters)                   │
│                                                                                      │
│  이 아키텍처는 Alistair Cockburn의 Hexagonal Architecture와 Robert C. Martin의      │
│  Clean Architecture 원칙을 결합하여, 도메인 로직을 외부 의존성으로부터 완전히  │
│  격리하고 테스트 가능하며 확장 가능한 시스템을 구축합니다.                           │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  ADAPTERS LAYER                               │
│                          (외부 세계와의 인터페이스 구현)                              │
│                                                                                      │
│  어댑터는 외부 시스템(CLI, 파일 시스템, LLM API, 데이터베이스 등)과 도메인       │
│  계층 사이의 변환 계층입니다. 어댑터는 포트 인터페이스를 구현하여 도메인과 통신합니다. │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────┐                    ┌───────────────────────────────────┐
│      INBOUND ADAPTERS            │                    │      OUTBOUND ADAPTERS            │
│   (입력 어댑터 - 사용자 입력)     │                    │   (출력 어댑터 - 외부 시스템)     │
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
│  ├── __init__.py                  │                    │  ├── __init__.py                  │
│  ├── cli.py                       │                    │  ├── dataset/                     │
│  │   └── Typer 기반 CLI            │                    │  │   ├── __init__.py              │
│  │       - run 명령                │                    │  │   ├── base.py                  │
│  │       - generate 명령           │                    │  │   ├── csv_loader.py             │
│  │       - history 명령             │                    │  │   ├── excel_loader.py           │
│  │       - compare 명령             │                    │  │   ├── json_loader.py            │
│  │       - pipeline 명령            │                    │  │   └── loader_factory.py        │
│  │       - benchmark 명령          │                    │  │                                 │
│  │       - domain 명령              │                    │  ├── llm/                          │
│  │       - agent.py                 │                    │  │   ├── __init__.py               │
│  │                                 │                    │  │   ├── anthropic_adapter.py      │
│  └── web/                         │                    │  │   ├── azure_adapter.py          │
│      ├── adapter.py                 │                    │  │   ├── ollama_adapter.py         │
│      ├── app.py                    │                    │  │   ├── openai_adapter.py         │
│      ├── components/                │                    │  │   └── vllm_adapter.py           │
│      │   ├── cards.py               │                    │  │                                 │
│      │   ├── charts.py              │                    │  ├── storage/                      │
│      │   ├── evaluate.py            │                    │  │   ├── __init__.py               │
│      │   ├── history.py             │                    │  │   ├── postgres_adapter.py       │
│      │   ├── reports.py             │                    │  │   ├── sqlite_adapter.py         │
│      │   └── upload.py              │                    │  │   ├── postgres_schema.sql       │
│      └── session.py                │                    │  │   └── schema.sql                   │
│                                   │                    │  │                                 │
│                                   │                    │  ├── tracker/                      │
│                                   │                    │  │   ├── __init__.py               │
│                                   │                    │  │   ├── langfuse_adapter.py       │
│                                   │                    │  │   ├── mlflow_adapter.py         │
│                                   │                    │  │   └── phoenix_adapter.py        │
│                                   │                    │  │                                 │
│                                   │                    │  ├── analysis/                     │
│                                   │                    │  │   ├── statistical_adapter.py    │
│                                   │                    │  │   ├── nlp_adapter.py            │
│                                   │                    │  │   ├── causal_adapter.py         │
│                                   │                    │  │   └── [분석 모듈들]              │
│                                   │                    │  │                                 │
│                                   │                    │  ├── cache/                        │
│                                   │                    │  │   └── memory_cache.py            │
│                                   │                    │  │                                 │
│                                   │                    │  ├── domain_memory/                │
│                                   │                    │  │   ├── sqlite_adapter.py         │
│                                   │                    │  │   └── domain_memory_schema.sql  │
│                                   │                    │  │                                 │
│                                   │                    │  ├── improvement/                  │
│                                   │                    │  │   ├── pattern_detector.py         │
│                                   │                    │  │   ├── insight_generator.py      │
│                                   │                    │  │   └── playbook_loader.py         │
│                                   │                    │  │                                 │
│                                   │                    │  ├── nlp/                           │
│                                   │                    │  │   └── korean/                    │
│                                   │                    │  │       ├── bm25_retriever.py     │
│                                   │                    │  │       ├── dense_retriever.py    │
│                                   │                    │  │       └── hybrid_retriever.py   │
│                                   │                    │  │                                 │
│                                   │                    │  └── report/                        │
│                                   │                    │      ├── llm_report_generator.py   │
│                                   │                    │      └── markdown_adapter.py      │
└───────────────────────────────────┘                    └───────────────────────────────────┘
         │                                                          │
         │                                                          │
         │  [의존성 방향: 어댑터 → 포트]                             │
         │                                                          │
         ▼                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    PORTS LAYER                               │
│                          (인터페이스 정의 - 계약)                                    │
│                                                                                      │
│  포트는 도메인과 외부 세계 사이의 계약(Contract)을 정의합니다. 포트는 인터페이스  │
│  또는 프로토콜로 정의되며, 도메인은 포트를 통해 외부 서비스를 사용합니다.           │
│                                                                                      │
│  핵심 원칙:                                                                          │
│  - 포트는 도메인 계층에 속함                                                         │
│  - 포트는 "무엇을" 정의하지만 "어떻게"는 정의하지 않음                               │
│  - 어댑터는 포트를 구현함                                                            │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────┐                    ┌───────────────────────────────────┐
│      INBOUND PORTS                 │                    │      OUTBOUND PORTS                 │
│   (입력 포트 - 사용 사례 정의)    │                    │   (출력 포트 - 외부 의존성 정의)    │
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
│  ├── __init__.py                  │                    │  ├── __init__.py                  │
│  ├── evaluator_port.py            │                    │  ├── dataset_port.py               │
│  │   └── EvaluatorPort            │                    │  │   └── DatasetPort               │
│  │       Protocol {                │                    │  │       Protocol {                │
│  │         evaluate()               │                    │  │         load()                  │
│  │       }                         │                    │  │         supports()             │
│  │                                 │                    │  │       }                          │
│  ├── analysis_pipeline_port.py    │                    │  │                                 │
│  │   └── AnalysisPipelinePort    │                    │  ├── llm_port.py                     │
│  │       Protocol {                │                    │  │   └── LLMPort                   │
│  │         build_pipeline()         │                    │  │       ABC {                     │
│  │         execute()                │                    │  │         get_model_name()        │
│  │       }                         │                    │  │         as_ragas_llm()          │
│  │                                 │                    │  │       }                          │
│  ├── learning_hook_port.py        │                    │  │                                 │
│  │   └── LearningHookPort         │                    │  ├── storage_port.py               │
│  │                                 │                    │  │   └── StoragePort               │
│  └── web_port.py                  │                    │  │       Protocol {                 │
│      └── WebUIPort                 │                    │  │         save_run()              │
│                                                           │  │         get_run()               │
│                                   │                    │  │         list_runs()              │
│                                   │                    │  │       }                          │
│                                   │                    │  │                                 │
│                                   │                    │  ├── tracker_port.py               │
│                                   │                    │  │   └── TrackerPort                │
│                                   │                    │  │       Protocol {                 │
│                                   │                    │  │         start_trace()           │
│                                   │                    │  │         log_evaluation_run()    │
│                                   │                    │  │       }                          │
│                                   │                    │  │                                 │
│                                   │                    │  ├── analysis_port.py              │
│                                   │                    │  │   └── AnalysisPort              │
│                                   │                    │  │                                 │
│                                   │                    │  ├── domain_memory_port.py         │
│                                   │                    │  │   └── DomainMemoryPort          │
│                                   │                    │  │       (Factual/Experiential/    │
│                                   │                    │  │        Behavior 레이어)         │
└───────────────────────────────────┘                    └───────────────────────────────────┘
         │                                                          │
         │                                                          │
         │  [의존성 방향: 도메인 → 포트]                             │
         │                                                          │
         └──────────────────┬───────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  DOMAIN LAYER                                 │
│                          (핵심 비즈니스 로직)                                    │
│                                                                                      │
│  도메인 계층은 시스템의 핵심 비즈니스 로직을 포함합니다. 이 계층은 외부 의존성에    │
│  대해 전혀 알지 못하며, 오직 포트 인터페이스를 통해서만 외부와 통신합니다.          │
│                                                                                      │
│  핵심 원칙:                                                                          │
│  - 순수한 비즈니스 로직만 포함                                                       │
│  - 외부 프레임워크나 라이브러리에 의존하지 않음                                      │
│  - 테스트 가능하며 독립적으로 실행 가능                                              │
│  - 도메인 전문가가 이해할 수 있는 언어로 작성                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  domain/                                                                            │
│  ├── entities/                          (도메인 엔티티 - Rich Domain Model)         │
│  │   ├── __init__.py                                                               │
│  │   ├── dataset.py                    ─ Dataset 엔티티                             │
│  │   │   └── TestCase, Dataset 클래스                                               │
│  │   │       - 비즈니스 규칙 포함                                                    │
│  │   │       - 불변성 보장                                                           │
│  │   │       - 도메인 이벤트 발생 가능                                                │
│  │   │                                                                              │
│  │   ├── result.py                     ─ Result 엔티티                              │
│  │   │   └── EvaluationRun, TestCaseResult, MetricScore                            │
│  │   │       - 평가 결과 집계                                                        │
│  │   │       - 통과/실패 판정                                                        │
│  │   │       - 메트릭 점수 관리                                                      │
│  │   │                                                                              │
│  │   ├── analysis.py                    ─ Analysis 엔티티                           │
│  │   │   └── AnalysisBundle, ComparisonResult, MetaAnalysisResult                   │
│  │   │       - 통계/NLP/인과 분석 결과                                               │
│  │   │       - 비교 및 메타 분석                                                     │
│  │   │                                                                              │
│  │   ├── analysis_pipeline.py           ─ Analysis Pipeline 엔티티                 │
│  │   │   └── AnalysisPipeline, AnalysisNode, AnalysisContext                        │
│  │   │       - DAG 기반 분석 파이프라인                                              │
│  │   │       - 의도 분류 및 템플릿 관리                                              │
│  │   │                                                                              │
│  │   ├── rag_trace.py                   ─ RAG Trace 엔티티                           │
│  │   │   └── RetrievalData, GenerationData, RAGTraceData                            │
│  │   │       - Phoenix/OpenTelemetry span 속성 매핑                                 │
│  │   │       - 검색/생성 단계 레이턴시 및 토큰 사용 분석                            │
│  │   │                                                                              │
│  │   └── memory.py                      ─ Domain Memory 엔티티                       │
│  │       └── FactualFact, LearningMemory, BehaviorEntry                             │
│  │           - 도메인 메모리 (Factual/Experiential/Behavior)                        │
│  │           - Formation/Evolution/Retrieval dynamics                               │
│  │                                                                                  │
│  ├── metrics/                            (평가 메트릭)                                │
│  │   ├── __init__.py                                                               │
│  │   ├── insurance.py                  ─ 보험 도메인 메트릭                          │
│  │   │   └── InsuranceTermAccuracy                                                    │
│  │   │       - 도메인 특화 메트릭                                                     │
│  │   │       - Ragas 외부 커스텀 메트릭                                              │
│  │   │                                                                              │
│  │   └── terms_dictionary.json        ─ 용어 사전                                  │
│  │       - 도메인 지식 표현                                                          │
│  │                                                                                  │
│  └── services/                          (도메인 서비스)                               │
│      ├── __init__.py                                                               │
│      │                                                                              │
│      ├── evaluator.py                  ─ 평가자 서비스                               │
│      │   └── RagasEvaluator                                                         │
│      │       - Ragas 메트릭 실행                                                     │
│      │       - 커스텀 메트릭 실행                                                    │
│      │       - 결과 집계 및 임계값 판정                                              │
│      │       - 토큰 사용량 및 비용 추적                                              │
│      │                                                                              │
│      ├── analysis_service.py           ─ 분석 서비스                               │
│      │   └── AnalysisService                                                       │
│      │       - 통계 분석 오케스트레이션                                              │
│      │       - NLP/인과 분석 통합                                                    │
│      │       - 메타 분석 및 비교                                                     │
│      │                                                                              │
│      ├── pipeline_orchestrator.py      ─ 파이프라인 오케스트레이터                 │
│      │   └── PipelineOrchestrator                                                  │
│      │       - DAG 기반 분석 파이프라인 실행                                        │
│      │       - 모듈 카탈로그 및 템플릿 관리                                          │
│      │       - 의도 분류 및 파이프라인 빌드                                         │
│      │                                                                              │
│      └── improvement_guide_service.py  ─ 개선 가이드 서비스                        │
│          └── ImprovementGuideService                                               │
│              - 규칙 기반 패턴 탐지                                                  │
│              - LLM 기반 인사이트 생성                                               │
│              - 하이브리드 분석 및 리포트 생성                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 의존성 관리

### 2.3.1 의존성 방향 규칙

**규칙**: 의존성은 항상 외부 → 내부 방향

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        의존성 방향 다이어그램                                │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │   External Systems   │
                    │  (File, API, DB)     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │    ADAPTERS          │
                    │  (구현 계층)          │
                    └──────────┬───────────┘
                               │ depends on
                    ┌──────────▼───────────┐
                    │      PORTS            │
                    │  (인터페이스 계층)      │
                    └──────────┬───────────┘
                               │ depends on
                    ┌──────────▼───────────┐
                    │      DOMAIN           │
                    │  (비즈니스 로직)       │
                    └──────────────────────┘

규칙: 의존성은 항상 외부 → 내부 방향
      도메인은 외부에 의존하지 않음
```

### 2.3.2 의존성 규칙 위반 방지

**잘못된 예**:
```python
# ❌ 도메인이 어댑터에 직접 의존
from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter

class RagasEvaluator:
    def __init__(self):
        self._llm = OpenAIAdapter()  # 구체적인 구현에 의존
```

**올바른 예**:
```python
# ✅ 도메인이 포트 인터페이스에만 의존
from evalvault.ports.outbound.llm_port import LLMPort

class RagasEvaluator:
    def __init__(self, llm: LLMPort):  # 인터페이스에 의존
        self._llm = llm
```

### 2.4 설계 패턴과 원칙

### 2.4.1 SOLID 원칙

#### 2.4.1.1 단일 책임 원칙 (Single Responsibility Principle - SRP)

**원칙**: 각 클래스는 하나의 책임만 가짐

**EvalVault 적용**:
- `RagasEvaluator`: 평가 실행만 담당
- `ExperimentManager`: 실험 관리만 담당
- `DocumentChunker`: 문서 청킹만 담당

**코드 예시**:
```python
# ✅ SRP 준수: 단일 책임
class RagasEvaluator:
    """Ragas 기반 평가 서비스."""

    async def evaluate(self, dataset, metrics, llm) -> EvaluationRun:
        """평가 실행만 담당"""
        # 평가 로직...

class ExperimentManager:
    """실험 관리 서비스."""

    def compare_groups(self, experiment_id) -> list[MetricComparison]:
        """그룹 비교만 담당"""
        # 비교 로직...

# ❌ SRP 위반: 다중 책임
class CombinedService:
    """평가와 실험 관리를 모두 담당"""

    async def evaluate(self, ...):
        # 평가 로직...

    def compare_groups(self, ...):
        # 비교 로직...
```

#### 2.4.1.2 개방/폐쇄 원칙 (Open/Closed Principle - OCP)

**원칙**: 확장에는 열려있고, 수정에는 닫혀있음

**EvalVault 적용**:
- 새로운 LLM 제공자 추가: `LLMPort`를 구현하는 새 어댑터만 추가
- 새로운 메트릭 추가: `RagasEvaluator` 수정 없이 메트릭만 추가

**코드 예시**:
```python
# ✅ OCP 준수: 확장에 열려있음
class LLMPort(ABC):
    @abstractmethod
    def get_model_name(self) -> str: ...

# 새로운 LLM 제공자 추가 시
class NewLLMAdapter(LLMPort):
    def get_model_name(self) -> str: return "new-model"
    def as_ragas_llm(self): return llm_factory("new-model", "new-provider")

# ❌ OCP 위반: 수정이 필요
class RagasEvaluator:
    def evaluate(self, dataset, metrics, provider):
        if provider == "openai":
            # OpenAI 로직
        elif provider == "anthropic":
            # Anthropic 로직
        # 새로운 제공자 추가 시마다 수정 필요...
```

#### 2.4.1.3 리스코프 치환 원칙 (Liskov Substitution Principle - LSP)

**원칙**: 서브타입은 베이스 타입을 대체할 수 있어야 함

**EvalVault 적용**:
- 모든 `LLMPort` 구현체는 서로 교체 가능
- 모든 `StoragePort` 구현체는 서로 교체 가능

**코드 예시**:
```python
# ✅ LSP 준수: 교체 가능
def run_evaluation(dataset: Dataset, llm: LLMPort):
    evaluator = RagasEvaluator()
    result = await evaluator.evaluate(dataset, metrics, llm)

# 어떤 LLMPort 구현체든 교체 가능
openai_llm = OpenAIAdapter(settings)
anthropic_llm = AnthropicAdapter(settings)

run_evaluation(dataset, metrics, openai_llm)  # 정상 작동
run_evaluation(dataset, metrics, anthropic_llm)  # 정상 작동
```

#### 2.4.1.4 인터페이스 분리 원칙 (Interface Segregation Principle - ISP)

**원칙**: 클라이언트는 사용하지 않는 메서드에 의존하지 않아야 함

**EvalVault 적용**:
- `LLMPort`: LLM 관련 메서드만 포함
- `StoragePort`: 저장소 관련 메서드만 포함
- `TrackerPort`: 추적 관련 메서드만 포함

**코드 예시**:
```python
# ✅ ISP 준수: 단일 책임 인터페이스
class LLMPort(ABC):
    @abstractmethod
    def get_model_name(self) -> str: ...

    @abstractmethod
    def as_ragas_llm(self): ...

# ❌ ISP 위반: 다중 책임 인터페이스
class MultiPort(ABC):
    # LLM 관련
    @abstractmethod
    def get_model_name(self) -> str: ...

    # 저장소 관련
    @abstractmethod
    def save_run(self, run: EvaluationRun) -> str: ...

    # 추적 관련
    @abstractmethod
    def start_trace(self, name: str) -> str: ...
```

#### 2.4.1.5 의존성 역전 원칙 (Dependency Inversion Principle - DIP)

**원칙**: 고수준 모듈은 저수준 모듈에 의존하지 않아야 함. 둘 다 추상화에 의존해야 함

**EvalVault 적용**:
- `RagasEvaluator`는 `LLMPort` 인터페이스에 의존 (구체적인 어댑터에 의존하지 않음)
- `ExperimentManager`는 `StoragePort` 인터페이스에 의존 (구체적인 저장소에 의존하지 않음)

**코드 예시**:
```python
# ✅ DIP 준수: 추상화에 의존
class RagasEvaluator:
    def __init__(self, llm: LLMPort):  # 인터페이스에 의존
        self._llm = llm

class ExperimentManager:
    def __init__(self, storage: StoragePort):  # 인터페이스에 의존
        self._storage = storage

# ❌ DIP 위반: 구체적인 구현에 의존
class RagasEvaluator:
    def __init__(self):
        self._llm = OpenAIAdapter()  # 구체적인 구현에 의존

class ExperimentManager:
    def __init__(self):
        self._storage = SQLiteStorageAdapter()  # 구체적인 구현에 의존
```

### 2.5 확장성과 테스트 가능성

### 2.5.1 확장성 (Extensibility)

#### 2.5.1.1 새로운 LLM 제공자 추가

**단계**:
1. `LLMPort` 인터페이스 구현
2. 어댑터 클래스 생성
3. Factory에 등록

**예시**:
```python
# 1. LLMPort 구현
class NewLLMAdapter(LLMPort):
    def get_model_name(self) -> str:
        return "new-model"

    def as_ragas_llm(self):
        return llm_factory(model="new-model", provider="new-provider")

# 2. Factory에 등록
def get_llm_adapter(settings: Settings) -> LLMPort:
    if settings.llm_provider == "new-provider":
        return NewLLMAdapter(settings)
    # ...
```

#### 2.5.1.2 새로운 메트릭 추가

**단계**:
1. 메트릭 클래스 생성
2. `RagasEvaluator.CUSTOM_METRIC_MAP`에 등록

**예시**:
```python
# 1. 메트릭 클래스
class NewMetric:
    def score(self, answer: str, contexts: list[str]) -> float:
        return 0.9

# 2. 등록
class RagasEvaluator:
    CUSTOM_METRIC_MAP = {
        "insurance_term_accuracy": InsuranceTermAccuracy,
        "new_metric": NewMetric,  # 새 메트릭 추가
    }
```

### 2.5.2 테스트 가능성 (Testability)

#### 2.5.2.1 포트 인터페이스를 통한 모킹

**도메인 서비스 테스트**:
```python
# 테스트용 모킹 어댑터
class MockLLMAdapter(LLMPort):
    def get_model_name(self) -> str:
        return "mock-model"

    def as_ragas_llm(self):
        return MockRagasLLM()

# 테스트
def test_evaluator():
    llm = MockLLMAdapter()
    evaluator = RagasEvaluator()
    result = await evaluator.evaluate(dataset, metrics, llm)
    assert result.pass_rate > 0.7
```

---

## 업데이트 이력

| 버전 | 날짜 | 변경 사항 | 담당 |
|------|------|----------|------|
| 1.0.0 | 2026-01-10 | 초기 작성 | EvalVault Team |

## 관련 섹션

- 섹션 1: 프로젝트 개요
- 섹션 3: 데이터 흐름 분석
- 섹션 4: 주요 컴포넌트 상세
