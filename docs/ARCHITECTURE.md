# EvalVault 아키텍처 가이드

> **Hexagonal Architecture (Ports & Adapters) + Clean Architecture + Domain-Driven Design 기반**

이 문서는 EvalVault의 아키텍처를 매우 상세하게 설명하는 학습 교과서입니다. 소프트웨어 아키텍처 방법론, 설계 원칙, 데이터 흐름, 각 컴포넌트의 역할과 책임을 다룹니다.

---

## 목차

1. [아키텍처 개요](#1-아키텍처-개요)
2. [방법론 기반: Hexagonal Architecture](#2-방법론-기반-hexagonal-architecture)
3. [계층별 상세 분석](#3-계층별-상세-분석)
4. [데이터 흐름 분석](#4-데이터-흐름-분석)
5. [설계 패턴과 원칙](#5-설계-패턴과-원칙)
6. [의존성 관리](#6-의존성-관리)
7. [확장성과 테스트 가능성](#7-확장성과-테스트-가능성)

---

## 1. 아키텍처 개요

### 1.1 전체 구조 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              EVALVAULT ARCHITECTURE                                  │
│                        (Hexagonal Architecture / Ports & Adapters)                   │
│                                                                                      │
│  이 아키텍처는 Alistair Cockburn의 Hexagonal Architecture와 Robert C. Martin의      │
│  Clean Architecture 원칙을 결합하여, 도메인 로직을 외부 의존성으로부터 완전히        │
│  격리하고 테스트 가능하며 확장 가능한 시스템을 구축합니다.                           │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  ADAPTERS LAYER                                      │
│                          (외부 세계와의 인터페이스 구현)                              │
│                                                                                      │
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
│  ├── __init__.py                  │                    │  ├── __init__.py                  │
│  └── cli.py                       │                    │  ├── dataset/                     │
│      └── Typer 기반 CLI            │                    │  │   ├── __init__.py              │
│          - run 명령                │                    │  │   ├── base.py                  │
│          - generate 명령           │                    │  │   ├── csv_loader.py             │
│          - history 명령             │                    │  │   ├── excel_loader.py           │
│          - compare 명령             │                    │  │   ├── json_loader.py            │
│          - experiment 명령들        │                    │  │   └── loader_factory.py        │
│                                   │                    │  │                                 │
│                                   │                    │  ├── llm/                          │
│                                   │                    │  │   ├── __init__.py               │
│                                   │                    │  │   ├── anthropic_adapter.py      │
│                                   │                    │  │   ├── azure_adapter.py          │
│                                   │                    │  │   ├── ollama_adapter.py         │
│                                   │                    │  │   └── openai_adapter.py         │
│                                   │                    │  │                                 │
│                                   │                    │  ├── storage/                      │
│                                   │                    │  │   ├── __init__.py               │
│                                   │                    │  │   ├── postgres_adapter.py       │
│                                   │                    │  │   ├── sqlite_adapter.py         │
│                                   │                    │  │   ├── postgres_schema.sql       │
│                                   │      │   │   │   │   └── schema.sql                   │
│                                   │                    │  │                                 │
│                                   │                    │  └── tracker/                      │
│                                   │                    │      ├── __init__.py               │
│                                   │                    │      ├── langfuse_adapter.py       │
│                                   │                    │      └── mlflow_adapter.py         │
└───────────────────────────────────┘                    └───────────────────────────────────┘
         │                                                          │
         │                                                          │
         │  [의존성 방향: 어댑터 → 포트]                             │
         │                                                          │
         ▼                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    PORTS LAYER                                       │
│                          (인터페이스 정의 - 계약)                                     │
│                                                                                      │
│  포트는 도메인과 외부 세계 사이의 계약(Contract)을 정의합니다. 포트는 인터페이스     │
│  또는 프로토콜로 정의되며, 도메인은 포트를 통해 외부 서비스를 사용합니다.           │
│                                                                                      │
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
│  ├── __init__.py                  │                    │  ├── __init__.py                  │
│  └── evaluator_port.py            │                    │  ├── dataset_port.py               │
│      └── EvaluatorPort            │                    │  │   └── DatasetPort               │
│          Protocol {                │                    │  │       Protocol {                │
│            evaluate()               │                    │  │         load()                  │
│          }                         │                    │  │         supports()             │
│                                   │                    │  │       }                          │
│                                   │                    │  │                                 │
│                                   │                    │  ├── llm_port.py                     │
│                                   │                    │  │   └── LLMPort                   │
│                                   │                    │  │       ABC {                     │
│                                   │                    │  │         get_model_name()        │
│                                   │                    │  │         as_ragas_llm()          │
│                                   │                    │  │       }                          │
│                                   │                    │  │                                 │
│                                   │                    │  ├── storage_port.py               │
│                                   │                    │  │   └── StoragePort               │
│                                   │                    │  │       Protocol {                 │
│                                   │                    │  │         save_run()              │
│                                   │                    │  │         get_run()               │
│                                   │                    │  │         list_runs()              │
│                                   │                    │  │       }                          │
│                                   │                    │  │                                 │
│                                   │                    │  └── tracker_port.py               │
│                                   │                    │      └── TrackerPort                │
│                                   │                    │          Protocol {                 │
│                                   │                    │            start_trace()           │
│                                   │                    │            add_span()               │
│                                   │                    │            log_score()              │
│                                   │                    │            log_evaluation_run()    │
│                                   │                    │          }                          │
└───────────────────────────────────┘                    └───────────────────────────────────┘
         │                                                          │
         │                                                          │
         │  [의존성 방향: 도메인 → 포트]                             │
         │                                                          │
         └──────────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  DOMAIN LAYER                                        │
│                          (핵심 비즈니스 로직)                                        │
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
│  ├── __init__.py                                                                    │
│  │                                                                                  │
│  ├── entities/                          (도메인 엔티티 - Rich Domain Model)         │
│  │   ├── __init__.py                                                               │
│  │   ├── dataset.py                    ─ Dataset 엔티티                             │
│  │   │   └── TestCase, Dataset 클래스                                               │
│  │   │       - 비즈니스 규칙 포함                                                    │
│  │   │       - 불변성 보장                                                           │
│  │   │       - 도메인 이벤트 발생 가능                                                │
│  │   │                                                                              │
│  │   ├── experiment.py                 ─ Experiment 엔티티                          │
│  │   │   └── Experiment, ExperimentGroup                                             │
│  │   │       - A/B 테스트 관리                                                       │
│  │   │       - 그룹별 메트릭 비교                                                    │
│  │   │                                                                              │
│  │   └── result.py                     ─ Result 엔티티                              │
│  │       └── EvaluationRun, TestCaseResult, MetricScore                            │
│  │           - 평가 결과 집계                                                        │
│  │           - 통과/실패 판정                                                        │
│  │           - 메트릭 점수 관리                                                      │
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
│      ├── entity_extractor.py           ─ 엔티티 추출 서비스                         │
│      │   └── EntityExtractor                                                       │
│      │       - 문서에서 엔티티 추출                                                  │
│      │       - 관계 추출                                                             │
│      │       - 지식 그래프 구축 지원                                                 │
│      │                                                                              │
│      ├── kg_generator.py               ─ 지식 그래프 생성 서비스                     │
│      │   └── KnowledgeGraphGenerator                                                │
│      │       - 문서에서 지식 그래프 생성                                             │
│      │       - 엔티티-관계 추출                                                      │
│      │       - 테스트셋 생성에 활용                                                 │
│      │                                                                              │
│      ├── testset_generator.py          ─ 테스트셋 생성 서비스                       │
│      │   ├── BasicTestsetGenerator                                                  │
│      │   └── KnowledgeGraphTestsetGenerator                                        │
│      │       - 문서에서 평가용 테스트셋 생성                                         │
│      │       - Strategy 패턴으로 생성 방법 선택                                      │
│      │                                                                              │
│      ├── document_chunker.py           ─ 문서 청킹 서비스                           │
│      │   └── DocumentChunker                                                       │
│      │       - 문서를 청크로 분할                                                   │
│      │       - 오버랩 처리                                                           │
│      │                                                                              │
│      └── experiment_manager.py         ─ 실험 관리 서비스                          │
│          └── ExperimentManager                                                     │
│              - A/B 테스트 관리                                                       │
│              - 그룹별 메트릭 비교                                                    │
│              - 실험 결론 기록                                                        │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              CONFIG LAYER                                            │
│                          (설정 관리)                                                 │
│                                                                                      │
│  이 계층은 애플리케이션 설정을 제공합니다. 도메인 로직과는 분리되어 있지만,          │
│  도메인 서비스가 필요시 사용할 수 있습니다.                                          │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────┐
│      CONFIG                       │
│   (설정 관리)                      │
├───────────────────────────────────┤
│                                   │
│  config/                          │
│  ├── __init__.py                  │
│  │                                 │
│  ├── settings.py                  │
│  │   └── Settings (Pydantic)      │
│  │       - 환경변수 기반 설정      │
│  │       - 프로필 지원             │
│  │       - 타입 검증               │
│  │                                 │
│  └── model_config.py              │
│      └── ModelConfig              │
│          - YAML 기반 모델 설정     │
│          - 프로필 관리             │
│          - Pydantic 검증           │
└───────────────────────────────────┘
```

---

## 2. 방법론 기반: Hexagonal Architecture

### 2.1 Hexagonal Architecture란?

**Hexagonal Architecture** (또는 **Ports & Adapters Architecture**)는 Alistair Cockburn이 제안한 아키텍처 패턴으로, 애플리케이션의 핵심 비즈니스 로직을 외부 의존성으로부터 격리하는 것을 목표로 합니다.

#### 핵심 개념

1. **포트 (Port)**: 애플리케이션과 외부 세계 사이의 인터페이스
   - **Inbound Port**: 애플리케이션이 제공하는 기능 (사용 사례)
   - **Outbound Port**: 애플리케이션이 필요로 하는 외부 서비스

2. **어댑터 (Adapter)**: 포트를 구현하는 구체적인 기술
   - **Inbound Adapter**: 외부 요청을 애플리케이션으로 변환 (예: CLI, REST API)
   - **Outbound Adapter**: 애플리케이션 요청을 외부 시스템으로 변환 (예: 데이터베이스, API 클라이언트)

3. **도메인 (Domain)**: 핵심 비즈니스 로직이 위치하는 계층

### 2.2 EvalVault에서의 적용

```
                    ┌─────────────────────────────┐
                    │   External World            │
                    │   (Users, File System,      │
                    │    LLM APIs, Databases)     │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │      ADAPTERS               │
                    │  ┌────────┐  ┌──────────┐  │
                    │  │  CLI   │  │  File    │  │
                    │  │Adapter │  │  Loader  │  │
                    │  └───┬────┘  └────┬─────┘  │
                    │      │            │        │
                    └──────┼────────────┼────────┘
                           │            │
                    ┌──────▼────────────▼──────┐
                    │         PORTS            │
                    │  ┌────────┐  ┌─────────┐ │
                    │  │Evaluator│ │ Dataset │ │
                    │  │  Port  │ │  Port   │ │
                    │  └───┬────┘ └────┬─────┘ │
                    └──────┼──────────┼───────┘
                           │          │
                    ┌──────▼──────────▼──────┐
                    │      DOMAIN            │
                    │  ┌──────────────────┐  │
                    │  │  RagasEvaluator  │  │
                    │  │  (Business Logic)│  │
                    │  └──────────────────┘  │
                    └────────────────────────┘
```

### 2.3 의존성 규칙 (Dependency Rule)

**Clean Architecture**의 의존성 규칙을 따릅니다:

```
의존성 방향: 외부 → 내부
┌─────────────────────────────────────────┐
│  Adapters (외부 계층)                   │
│  └─> Ports (인터페이스)                 │
│      └─> Domain (핵심 로직)             │
└─────────────────────────────────────────┘
```

**규칙:**
- 어댑터는 포트에 의존
- 포트는 도메인에 속하지만 도메인 서비스에 의존하지 않음
- 도메인은 포트에만 의존 (어댑터에 직접 의존하지 않음)

---

## 3. 계층별 상세 분석

### 3.1 Domain Layer (도메인 계층)

도메인 계층은 시스템의 핵심입니다. 이 계층은 **완전히 독립적**이며 외부 프레임워크나 라이브러리에 의존하지 않습니다.

#### 3.1.1 Entities (엔티티)

엔티티는 도메인의 핵심 개념을 표현하는 불변 객체입니다.

**Dataset 엔티티**

```python
@dataclass
class Dataset:
    """평가용 데이터셋."""
    name: str
    version: str
    test_cases: list[TestCase]
    thresholds: dict[str, float] = field(default_factory=dict)

    def get_threshold(self, metric_name: str, default: float = 0.7) -> float:
        """비즈니스 규칙: 임계값 조회"""
        return self.thresholds.get(metric_name, default)
```

**책임:**
- 데이터셋의 불변성 보장
- 비즈니스 규칙 캡슐화 (임계값 관리)
- Ragas 형식으로 변환하는 메서드 제공

**EvaluationRun 엔티티**

```python
@dataclass
class EvaluationRun:
    """전체 평가 실행 결과."""
    run_id: str
    dataset_name: str
    model_name: str
    results: list[TestCaseResult]
    metrics_evaluated: list[str]
    thresholds: dict[str, float]

    @property
    def pass_rate(self) -> float:
        """비즈니스 규칙: 통과율 계산"""
        if not self.results:
            return 0.0
        return self.passed_test_cases / self.total_test_cases

    def get_avg_score(self, metric_name: str) -> float | None:
        """비즈니스 규칙: 메트릭 평균 점수 계산"""
        scores = [r.get_metric(metric_name).score
                  for r in self.results
                  if r.get_metric(metric_name)]
        return sum(scores) / len(scores) if scores else None
```

**책임:**
- 평가 결과의 집계 및 통계 계산
- 통과/실패 판정 로직
- 도메인 이벤트 발생 가능 (향후 확장)

#### 3.1.2 Services (도메인 서비스)

도메인 서비스는 여러 엔티티에 걸친 비즈니스 로직을 구현합니다.

**RagasEvaluator 서비스**

```python
class RagasEvaluator:
    """Ragas 기반 RAG 평가 서비스."""

    async def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,  # 포트 인터페이스에 의존
        thresholds: dict[str, float] | None = None,
    ) -> EvaluationRun:
        """평가 실행 - 핵심 비즈니스 로직"""
        # 1. 임계값 해석 (비즈니스 규칙)
        resolved_thresholds = self._resolve_thresholds(
            dataset, metrics, thresholds
        )

        # 2. 평가 실행 (Ragas 메트릭)
        eval_results = await self._evaluate_with_ragas(
            dataset, metrics, llm
        )

        # 3. 결과 집계 (비즈니스 로직)
        run = self._aggregate_results(
            dataset, metrics, eval_results, resolved_thresholds
        )

        return run
```

**책임:**
- 평가 실행 오케스트레이션
- 메트릭별 평가 로직
- 결과 집계 및 임계값 판정
- 토큰 사용량 및 비용 추적

**의존성:**
- `LLMPort` (포트 인터페이스) - 구체적인 LLM 구현에 의존하지 않음
- `Dataset`, `EvaluationRun` (도메인 엔티티)

**ExperimentManager 서비스**

```python
class ExperimentManager:
    """실험 관리 서비스."""

    def __init__(self, storage: StoragePort):  # 포트에 의존
        self._storage = storage
        self._experiments: dict[str, Experiment] = {}

    def compare_groups(self, experiment_id: str) -> list[MetricComparison]:
        """그룹 간 메트릭 비교 - 비즈니스 로직"""
        experiment = self.get_experiment(experiment_id)

        # 각 그룹의 run 데이터 수집
        group_runs = self._collect_group_runs(experiment)

        # 메트릭별 비교 (비즈니스 규칙)
        comparisons = []
        for metric in experiment.metrics_to_compare:
            group_scores = self._calculate_group_scores(
                group_runs, metric
            )
            best_group = max(group_scores, key=group_scores.get)
            improvement = self._calculate_improvement(group_scores)

            comparisons.append(MetricComparison(
                metric_name=metric,
                group_scores=group_scores,
                best_group=best_group,
                improvement=improvement,
            ))

        return comparisons
```

**책임:**
- A/B 테스트 실험 관리
- 그룹별 메트릭 비교 및 분석
- 실험 결론 기록

**의존성:**
- `StoragePort` (포트 인터페이스) - 구체적인 저장소에 의존하지 않음

#### 3.1.3 Metrics (메트릭)

도메인 특화 메트릭을 정의합니다.

**InsuranceTermAccuracy 메트릭**

```python
class InsuranceTermAccuracy:
    """보험 용어 정확도 메트릭."""

    def score(self, answer: str, contexts: list[str]) -> float:
        """비즈니스 규칙: 보험 용어가 컨텍스트에 기반하는지 검증"""
        # 도메인 지식 활용
        terms = self._extract_insurance_terms(answer)
        grounded_terms = self._check_grounding(terms, contexts)

        return len(grounded_terms) / len(terms) if terms else 0.0
```

**책임:**
- 도메인 특화 평가 로직
- 도메인 지식 활용 (용어 사전)

### 3.2 Ports Layer (포트 계층)

포트는 도메인과 외부 세계 사이의 계약을 정의합니다.

#### 3.2.1 Inbound Ports (입력 포트)

도메인이 제공하는 기능을 정의합니다.

**EvaluatorPort**

```python
class EvaluatorPort(Protocol):
    """평가 실행을 위한 포트 인터페이스."""

    def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        model: str,
    ) -> EvaluationRun:
        """데이터셋에 대해 평가를 실행합니다."""
        ...
```

**특징:**
- `Protocol` 기반 (Python의 구조적 서브타이핑)
- 도메인 서비스(`RagasEvaluator`)가 구현
- 어댑터(`CLI`)가 호출

#### 3.2.2 Outbound Ports (출력 포트)

도메인이 필요로 하는 외부 서비스를 정의합니다.

**LLMPort**

```python
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
```

**특징:**
- `ABC` (Abstract Base Class) 기반
- 어댑터(`OpenAIAdapter`, `AnthropicAdapter` 등)가 구현
- 도메인 서비스(`RagasEvaluator`)가 사용

**DatasetPort**

```python
class DatasetPort(Protocol):
    """데이터셋 로드를 위한 포트 인터페이스."""

    def load(self, file_path: str | Path) -> Dataset:
        """파일에서 데이터셋을 로드합니다."""
        ...

    def supports(self, file_path: str | Path) -> bool:
        """해당 파일 형식을 지원하는지 확인합니다."""
        ...
```

**StoragePort**

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

**TrackerPort**

```python
class TrackerPort(Protocol):
    """평가 실행 추적을 위한 포트 인터페이스."""

    def start_trace(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        """새로운 trace를 시작합니다."""
        ...

    def log_evaluation_run(self, run: EvaluationRun) -> str:
        """평가 실행을 trace로 기록합니다."""
        ...
```

### 3.3 Adapters Layer (어댑터 계층)

어댑터는 포트 인터페이스를 구현하여 외부 시스템과 통신합니다.

#### 3.3.1 Inbound Adapters (입력 어댑터)

**CLI Adapter**

```python
@app.command()
def run(
    dataset: Path,
    metrics: str,
    model: str | None = None,
    ...
):
    """Run RAG evaluation on a dataset."""
    # 1. 입력 검증 및 파싱
    metric_list = [m.strip() for m in metrics.split(",")]

    # 2. 설정 로드
    settings = Settings()

    # 3. 어댑터 생성 (Factory 패턴)
    loader = get_loader(dataset)  # DatasetPort 구현
    llm = get_llm_adapter(settings)  # LLMPort 구현

    # 4. 도메인 서비스 호출
    evaluator = RagasEvaluator()
    result = asyncio.run(
        evaluator.evaluate(
            dataset=ds,
            metrics=metric_list,
            llm=llm,  # 포트 인터페이스 전달
        )
    )

    # 5. 결과 포맷팅 및 출력
    _display_results(result)
```

**책임:**
- CLI 명령 파싱 (Typer 사용)
- 사용자 입력 검증
- 도메인 서비스 호출
- 결과 포맷팅 및 출력

**의존성:**
- `EvaluatorPort` (포트 인터페이스)
- `DatasetPort`, `LLMPort` (포트 인터페이스)

#### 3.3.2 Outbound Adapters (출력 어댑터)

**Dataset Loaders (CSV, Excel, JSON)**

```python
class CSVDatasetLoader(BaseDatasetLoader):
    """CSV 파일 로더."""

    def load(self, file_path: str | Path) -> Dataset:
        """CSV 파일을 Dataset으로 변환"""
        df = pd.read_csv(file_path)
        test_cases = [
            TestCase(
                id=f"tc-{i+1:03d}",
                question=row["question"],
                answer=row["answer"],
                contexts=row["contexts"].split("|"),
                ground_truth=row.get("ground_truth"),
            )
            for i, row in df.iterrows()
        ]
        return Dataset(
            name=Path(file_path).stem,
            version="1.0.0",
            test_cases=test_cases,
        )

    def supports(self, file_path: str | Path) -> bool:
        """CSV 파일 지원 여부"""
        return Path(file_path).suffix.lower() == ".csv"
```

**책임:**
- 파일 형식별 데이터 로드
- Dataset 엔티티로 변환
- 파일 형식 지원 여부 확인

**LLM Adapters**

```python
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
        """Ragas 호환 LLM 반환"""
        return self._ragas_llm
```

**책임:**
- LLM API 클라이언트 초기화
- Ragas 호환 형식으로 변환
- 토큰 사용량 추적

**Storage Adapters**

```python
class SQLiteStorageAdapter(StoragePort):
    """SQLite 저장소 어댑터."""

    def save_run(self, run: EvaluationRun) -> str:
        """EvaluationRun을 SQLite에 저장"""
        # EvaluationRun → DB 스키마 변환
        # SQL 쿼리 실행
        ...

    def get_run(self, run_id: str) -> EvaluationRun:
        """DB에서 EvaluationRun 조회"""
        # DB 쿼리 실행
        # DB 스키마 → EvaluationRun 변환
        ...
```

**책임:**
- 데이터베이스 쿼리 실행
- 도메인 엔티티 ↔ DB 스키마 변환

**Tracker Adapters**

```python
class LangfuseAdapter(TrackerPort):
    """Langfuse 추적 어댑터."""

    def log_evaluation_run(self, run: EvaluationRun) -> str:
        """EvaluationRun을 Langfuse trace로 기록"""
        trace = self._client.trace(
            name=f"evaluation-{run.run_id}",
            metadata={
                "dataset": run.dataset_name,
                "model": run.model_name,
            }
        )

        # 각 테스트 케이스를 span으로 기록
        for result in run.results:
            span = trace.span(
                name=result.test_case_id,
                input={"question": result.question},
                output={"answer": result.answer},
            )

            # 메트릭 점수 기록
            for metric in result.metrics:
                span.score(
                    name=metric.name,
                    value=metric.score,
                )

        return trace.id
```

**책임:**
- 추적 시스템 API 호출
- 도메인 엔티티 → 추적 형식 변환

---

## 4. 데이터 흐름 분석

### 4.1 평가 실행 흐름 (Evaluation Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        평가 실행 전체 흐름                                    │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 사용자 입력
    │
    ▼
[2] CLI Adapter (adapters/inbound/cli.py)
    │  - 명령 파싱 및 검증
    │  - 설정 로드
    │
    ├─> [3] Dataset Loader Factory
    │      │  - 파일 형식 감지
    │      │  - 적절한 로더 선택 (Strategy 패턴)
    │      │
    │      ▼
    │  [4] CSV/Excel/JSON Loader (adapters/outbound/dataset/)
    │      │  - 파일 읽기
    │      │  - Dataset 엔티티로 변환
    │      │
    │      └─> [5] Dataset 엔티티 (domain/entities/dataset.py)
    │
    ├─> [6] LLM Adapter Factory
    │      │  - 프로바이더 설정 확인
    │      │  - 적절한 어댑터 생성
    │      │
    │      ▼
    │  [7] OpenAI/Anthropic/Ollama Adapter (adapters/outbound/llm/)
    │      │  - LLM 클라이언트 초기화
    │      │  - LLMPort 구현
    │      │
    │      └─> [8] LLMPort 인터페이스 (ports/outbound/llm_port.py)
    │
    └─> [9] RagasEvaluator (domain/services/evaluator.py)
            │  - 평가 실행 오케스트레이션
            │
            ├─> [10] Ragas 메트릭 실행
            │       │  - LLMPort.as_ragas_llm() 호출
            │       │  - 각 테스트 케이스 평가
            │       │
            │       └─> [11] LLM Adapter
            │               - 실제 LLM API 호출
            │               - 토큰 사용량 추적
            │
            ├─> [12] 커스텀 메트릭 실행
            │       │  - InsuranceTermAccuracy 등
            │       │
            │       └─> [13] 도메인 메트릭 (domain/metrics/)
            │
            └─> [14] 결과 집계
                    │  - TestCaseResult 생성
                    │  - EvaluationRun 생성
                    │  - 통과/실패 판정
                    │
                    └─> [15] EvaluationRun 엔티티 (domain/entities/result.py)

[16] 결과 출력
    │  - CLI Adapter가 결과 포맷팅
    │  - 사용자에게 표시
    │
    ├─> [17] Storage Adapter (선택적)
    │       │  - EvaluationRun 저장
    │       │
    │       └─> [18] SQLite/PostgreSQL
    │
    └─> [19] Tracker Adapter (선택적)
            │  - Langfuse/MLflow에 기록
            │
            └─> [20] 추적 시스템
```

### 4.2 실험 관리 흐름 (Experiment Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        A/B 테스트 실험 흐름                                   │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 실험 생성
    │
    ▼
[2] ExperimentManager.create_experiment()
    │  - Experiment 엔티티 생성
    │
    └─> [3] Experiment 엔티티 (domain/entities/experiment.py)

[4] 그룹 추가
    │
    ▼
[5] Experiment.add_group()
    │  - ExperimentGroup 생성
    │
    └─> [6] ExperimentGroup 엔티티

[7] 평가 실행 추가
    │
    ▼
[8] Experiment.add_run_to_group()
    │  - 그룹에 run_id 추가
    │
    └─> [9] Storage Adapter
            │  - EvaluationRun 저장
            │
            └─> [10] 데이터베이스

[11] 그룹 비교
     │
     ▼
[12] ExperimentManager.compare_groups()
     │  - 각 그룹의 EvaluationRun 조회
     │  - 메트릭별 평균 점수 계산
     │  - 최고 그룹 및 개선율 계산
     │
     ├─> [13] Storage Adapter
     │       │  - StoragePort.get_run() 호출
     │       │
     │       └─> [14] 데이터베이스
     │
     └─> [15] MetricComparison 결과
             │  - 그룹별 점수
             │  - 최고 그룹
             │  - 개선율
```

### 4.3 테스트셋 생성 흐름 (Testset Generation Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        테스트셋 생성 흐름                                     │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 문서 입력
    │
    ▼
[2] CLI Adapter
    │  - 문서 파일 읽기
    │
    └─> [3] 문서 텍스트

[4] 생성 방법 선택
    │
    ├─> [5] Basic Method
    │       │
    │       ▼
    │   [6] BasicTestsetGenerator
    │       │  - DocumentChunker 사용
    │       │  - 청크에서 질문 생성
    │       │
    │       └─> [7] Dataset 엔티티
    │
    └─> [8] Knowledge Graph Method
            │
            ▼
        [9] KnowledgeGraphGenerator
            │  - EntityExtractor 사용
            │  - 지식 그래프 구축
            │  - 그래프에서 질문 생성
            │
            └─> [10] Dataset 엔티티

[11] 결과 저장
     │  - JSON 파일로 저장
```

### 4.4 의존성 주입 흐름 (Dependency Injection Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        의존성 주입 패턴                                      │
└─────────────────────────────────────────────────────────────────────────────┘

[1] Factory 함수들 (adapters/outbound/__init__.py)
    │
    ├─> get_loader(file_path) -> DatasetPort
    │      │  - 파일 형식에 따라 적절한 로더 반환
    │      │
    │      ├─> CSVDatasetLoader
    │      ├─> ExcelDatasetLoader
    │      └─> JSONDatasetLoader
    │
    ├─> get_llm_adapter(settings) -> LLMPort
    │      │  - 프로바이더 설정에 따라 적절한 어댑터 반환
    │      │
    │      ├─> OpenAIAdapter
    │      ├─> AnthropicAdapter
    │      ├─> AzureOpenAIAdapter
    │      └─> OllamaAdapter
    │
    └─> get_storage_adapter(settings) -> StoragePort
           │  - 저장소 설정에 따라 적절한 어댑터 반환
           │
           ├─> SQLiteStorageAdapter
           └─> PostgreSQLStorageAdapter

[2] CLI Adapter에서 의존성 주입
    │
    ▼
[3] 도메인 서비스 생성
    │  evaluator = RagasEvaluator()
    │  llm = get_llm_adapter(settings)  # LLMPort 구현
    │
    └─> [4] 도메인 서비스에 포트 전달
            evaluator.evaluate(
                dataset=ds,
                metrics=metric_list,
                llm=llm,  # 의존성 주입
            )
```

---

## 5. 설계 패턴과 원칙

### 5.1 적용된 설계 패턴

#### 5.1.1 Adapter Pattern (어댑터 패턴)

**목적:** 호환되지 않는 인터페이스를 호환 가능하게 만들기

**적용:**
- `LLMPort` 인터페이스와 다양한 LLM 제공자 (OpenAI, Anthropic, Azure, Ollama)
- `StoragePort` 인터페이스와 다양한 데이터베이스 (SQLite, PostgreSQL)

**예시:**
```python
# 포트 인터페이스
class LLMPort(ABC):
    @abstractmethod
    def as_ragas_llm(self): ...

# 어댑터 구현
class OpenAIAdapter(LLMPort):
    def as_ragas_llm(self):
        return llm_factory(model="gpt-4", provider="openai")

class AnthropicAdapter(LLMPort):
    def as_ragas_llm(self):
        return llm_factory(model="claude-3", provider="anthropic")
```

#### 5.1.2 Factory Pattern (팩토리 패턴)

**목적:** 객체 생성 로직을 캡슐화

**적용:**
- `get_loader()`: 파일 형식에 따라 적절한 로더 생성
- `get_llm_adapter()`: 프로바이더 설정에 따라 적절한 LLM 어댑터 생성

**예시:**
```python
def get_loader(file_path: str | Path) -> BaseDatasetLoader:
    """Factory: 파일 형식에 따라 로더 선택"""
    path = Path(file_path)
    for loader_class in _LOADERS:
        loader = loader_class()
        if loader.supports(path):
            return loader
    raise ValueError(f"Unsupported file format: {path.suffix}")
```

#### 5.1.3 Strategy Pattern (전략 패턴)

**목적:** 알고리즘을 캡슐화하고 런타임에 선택

**적용:**
- 테스트셋 생성 방법: `BasicTestsetGenerator` vs `KnowledgeGraphGenerator`
- 프롬프트 언어: `KoreanPrompt`, `EnglishPrompt`, `JapanesePrompt`, `ChinesePrompt`

**예시:**
```python
# Strategy 인터페이스
class PromptTemplate(ABC):
    @abstractmethod
    def format(self, **kwargs) -> str: ...

# 전략 구현
class KoreanPrompt(PromptTemplate):
    def format(self, **kwargs) -> str:
        return f"질문: {kwargs['question']}"

class EnglishPrompt(PromptTemplate):
    def format(self, **kwargs) -> str:
        return f"Question: {kwargs['question']}"
```

#### 5.1.4 Repository Pattern (저장소 패턴)

**목적:** 데이터 접근 로직을 캡슐화

**적용:**
- `StoragePort`: 데이터베이스 접근을 추상화
- `SQLiteStorageAdapter`, `PostgreSQLStorageAdapter`: 구체적인 저장소 구현

**예시:**
```python
# Repository 인터페이스
class StoragePort(Protocol):
    def save_run(self, run: EvaluationRun) -> str: ...
    def get_run(self, run_id: str) -> EvaluationRun: ...

# Repository 구현
class SQLiteStorageAdapter(StoragePort):
    def save_run(self, run: EvaluationRun) -> str:
        # SQLite 특화 구현
        ...
```

### 5.2 SOLID 원칙

#### 5.2.1 Single Responsibility Principle (단일 책임 원칙)

각 클래스는 하나의 책임만 가집니다.

**예시:**
- `RagasEvaluator`: 평가 실행만 담당
- `ExperimentManager`: 실험 관리만 담당
- `DocumentChunker`: 문서 청킹만 담당

#### 5.2.2 Open/Closed Principle (개방/폐쇄 원칙)

확장에는 열려있고 수정에는 닫혀있습니다.

**예시:**
- 새로운 LLM 제공자 추가: `LLMPort`를 구현하는 새 어댑터만 추가
- 새로운 메트릭 추가: `RagasEvaluator` 수정 없이 메트릭만 추가

#### 5.2.3 Liskov Substitution Principle (리스코프 치환 원칙)

서브타입은 베이스 타입을 대체할 수 있어야 합니다.

**예시:**
- 모든 `LLMPort` 구현체는 서로 교체 가능
- 모든 `StoragePort` 구현체는 서로 교체 가능

#### 5.2.4 Interface Segregation Principle (인터페이스 분리 원칙)

클라이언트는 사용하지 않는 메서드에 의존하지 않아야 합니다.

**예시:**
- `LLMPort`: LLM 관련 메서드만 포함
- `StoragePort`: 저장소 관련 메서드만 포함
- `TrackerPort`: 추적 관련 메서드만 포함

#### 5.2.5 Dependency Inversion Principle (의존성 역전 원칙)

고수준 모듈은 저수준 모듈에 의존하지 않아야 합니다. 둘 다 추상화에 의존해야 합니다.

**예시:**
- `RagasEvaluator`는 `LLMPort` 인터페이스에 의존 (구체적인 어댑터에 의존하지 않음)
- `ExperimentManager`는 `StoragePort` 인터페이스에 의존 (구체적인 저장소에 의존하지 않음)

---

## 6. 의존성 관리

### 6.1 의존성 방향

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

### 6.2 의존성 규칙 위반 방지

**잘못된 예:**
```python
# ❌ 도메인이 어댑터에 직접 의존
from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter

class RagasEvaluator:
    def __init__(self):
        self.llm = OpenAIAdapter()  # 구체적인 구현에 의존
```

**올바른 예:**
```python
# ✅ 도메인이 포트 인터페이스에만 의존
from evalvault.ports.outbound.llm_port import LLMPort

class RagasEvaluator:
    def __init__(self, llm: LLMPort):  # 인터페이스에 의존
        self.llm = llm
```

### 6.3 의존성 주입 (Dependency Injection)

**생성자 주입 (Constructor Injection)**

```python
# 도메인 서비스
class ExperimentManager:
    def __init__(self, storage: StoragePort):  # 의존성 주입
        self._storage = storage

# 어댑터에서 주입
storage = SQLiteStorageAdapter(db_path="evalvault.db")
manager = ExperimentManager(storage=storage)  # 의존성 주입
```

**메서드 주입 (Method Injection)**

```python
# 도메인 서비스
class RagasEvaluator:
    async def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,  # 메서드 파라미터로 주입
    ) -> EvaluationRun:
        ...

# 어댑터에서 주입
llm = get_llm_adapter(settings)
result = await evaluator.evaluate(dataset=ds, metrics=metrics, llm=llm)
```

---

## 7. 확장성과 테스트 가능성

### 7.1 확장성 (Extensibility)

#### 7.1.1 새로운 LLM 제공자 추가

**단계:**
1. `LLMPort` 인터페이스 구현
2. 어댑터 클래스 생성
3. Factory에 등록

**예시:**
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

#### 7.1.2 새로운 메트릭 추가

**단계:**
1. 메트릭 클래스 생성
2. `RagasEvaluator.CUSTOM_METRIC_MAP`에 등록

**예시:**
```python
# 1. 메트릭 클래스
class NewMetric:
    def score(self, answer: str, contexts: list[str]) -> float:
        # 평가 로직
        return 0.9

# 2. 등록
class RagasEvaluator:
    CUSTOM_METRIC_MAP = {
        "insurance_term_accuracy": InsuranceTermAccuracy,
        "new_metric": NewMetric,  # 새 메트릭 추가
    }
```

#### 7.1.3 새로운 데이터 형식 추가

**단계:**
1. `BaseDatasetLoader` 상속
2. `supports()` 및 `load()` 메서드 구현
3. Factory에 등록

**예시:**
```python
# 1. 로더 구현
class XMLDatasetLoader(BaseDatasetLoader):
    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() == ".xml"

    def load(self, file_path: str | Path) -> Dataset:
        # XML 파싱 및 Dataset 변환
        ...

# 2. Factory에 등록
_LOADERS.append(XMLDatasetLoader)
```

### 7.2 테스트 가능성 (Testability)

#### 7.2.1 포트 인터페이스를 통한 모킹

**도메인 서비스 테스트:**

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

#### 7.2.2 의존성 주입을 통한 테스트

**실험 관리 서비스 테스트:**

```python
# 테스트용 모킹 저장소
class MockStorageAdapter(StoragePort):
    def get_run(self, run_id: str) -> EvaluationRun:
        return create_mock_run(run_id)

# 테스트
def test_experiment_comparison():
    storage = MockStorageAdapter()
    manager = ExperimentManager(storage)
    comparisons = manager.compare_groups("exp-1")
    assert len(comparisons) > 0
```

---

## 8. 결론

EvalVault는 **Hexagonal Architecture**, **Clean Architecture**, **Domain-Driven Design** 원칙을 결합하여 다음과 같은 이점을 제공합니다:

### 8.1 주요 장점

1. **테스트 가능성**: 도메인 로직이 외부 의존성과 격리되어 단위 테스트가 용이
2. **확장성**: 새로운 어댑터 추가가 간단 (포트 인터페이스만 구현)
3. **유지보수성**: 각 계층의 책임이 명확하여 코드 이해 및 수정이 용이
4. **독립성**: 도메인 로직이 외부 프레임워크나 라이브러리에 의존하지 않음
5. **유연성**: 다양한 LLM 제공자, 저장소, 추적 시스템을 쉽게 교체 가능

### 8.2 아키텍처 원칙 요약

- **의존성 규칙**: 의존성은 항상 외부 → 내부 방향
- **포트와 어댑터**: 도메인은 포트를 통해 외부와 통신
- **도메인 중심**: 핵심 비즈니스 로직은 도메인 계층에 집중
- **인터페이스 분리**: 각 포트는 단일 책임을 가짐
- **의존성 주입**: 구체적인 구현이 아닌 인터페이스에 의존

이 아키텍처는 소프트웨어의 복잡성을 관리하고, 변경에 유연하게 대응하며, 장기적인 유지보수를 용이하게 합니다.

---

## 부록: 참고 자료

### 아키텍처 방법론
- **Hexagonal Architecture**: Alistair Cockburn
- **Clean Architecture**: Robert C. Martin
- **Domain-Driven Design**: Eric Evans

### 설계 패턴
- **Design Patterns**: Gang of Four
- **Enterprise Integration Patterns**: Gregor Hohpe

### Python 특화
- **Protocol**: Python typing 모듈
- **ABC**: Python abc 모듈
- **Dependency Injection**: Python의 타입 힌트 활용
