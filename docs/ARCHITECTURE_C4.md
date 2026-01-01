# EvalVault 아키텍처 (C4 Model)

> **C4 Model 기반 아키텍처 문서**
>
> C4 Model은 시스템 아키텍처를 4단계로 점진적으로 상세화하여 표현하는 방법론입니다.
> - **Level 1: System Context** - 시스템과 외부 세계의 관계
> - **Level 2: Container** - 애플리케이션의 주요 구성 요소
> - **Level 3: Component** - 컨테이너 내부의 주요 컴포넌트
> - **Level 4: Code** - 컴포넌트 내부의 상세 구현 (선택적)

이 문서는 EvalVault의 아키텍처를 C4 Model 방법론에 따라 계층적으로 설명합니다.

---

## 목차

1. [Level 1: System Context](#level-1-system-context)
2. [Level 2: Container Diagram](#level-2-container-diagram)
3. [Level 3: Component Diagram](#level-3-component-diagram)
4. [Level 4: Code Structure](#level-4-code-structure)
5. [주요 시나리오](#주요-시나리오)

---

## Level 1: System Context

**시스템 컨텍스트 다이어그램**은 EvalVault가 어떤 사용자와 외부 시스템과 상호작용하는지 보여줍니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EVALVAULT SYSTEM CONTEXT                           │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   개발자      │
                    │ (Developer)  │
                    └──────┬───────┘
                           │
                           │ CLI 명령 실행
                           │ 평가 결과 확인
                           │
                    ┌──────▼──────────────────────────────────────┐
                    │                                             │
                    │            EVALVAULT                        │
                    │    (RAG Evaluation System)                 │
                    │                                             │
                    │  - RAG 시스템 평가                          │
                    │  - 평가 결과 분석                           │
                    │  - 개선 가이드 생성                         │
                    │  - 도메인 메모리 관리                       │
                    │                                             │
                    └──────┬──────────────────────────────────────┘
                           │
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        │                  │                  │
┌───────▼──────┐  ┌────────▼────────┐  ┌──────▼──────┐
│              │  │                 │  │              │
│   데이터     │  │   LLM API       │  │   추적 시스템│
│   과학자     │  │                 │  │              │
│              │  │  - OpenAI       │  │  - Langfuse  │
│  - 평가 실행 │  │  - Anthropic    │  │  - MLflow    │
│  - 결과 분석 │  │  - Azure OpenAI  │  │              │
│  - 리포트    │  │  - Ollama        │  │              │
│              │  │                 │  │              │
└──────────────┘  └─────────────────┘  └──────────────┘
        │                  │                  │
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────────────────────┐
                    │                             │
                    │      파일 시스템             │
                    │                             │
                    │  - 데이터셋 (JSON/CSV/Excel) │
                    │  - 평가 결과 저장            │
                    │  - 리포트 생성               │
                    │                             │
                    └─────────────────────────────┘
```

### 주요 액터 (Actors)

1. **개발자 (Developer)**
   - CLI를 통한 평가 실행
   - 평가 결과 확인 및 분석
   - 실험 관리 및 비교

2. **데이터 과학자 (Data Scientist)**
   - Web UI를 통한 평가 실행
   - 결과 시각화 및 분석
   - 리포트 생성 및 공유

### 외부 시스템 (External Systems)

1. **LLM API 제공자**
   - OpenAI: GPT 모델 평가
   - Anthropic: Claude 모델 평가
   - Azure OpenAI: Azure 호스팅 모델
   - Ollama: 로컬 모델 실행

2. **추적 시스템 (Tracing Systems)**
   - Langfuse: 평가 실행 추적 및 시각화
   - MLflow: 실험 관리 및 모델 추적

3. **파일 시스템**
   - 데이터셋 파일 (JSON, CSV, Excel)
   - 평가 결과 저장
   - 리포트 파일 생성

---

## Level 2: Container Diagram

**컨테이너 다이어그램**은 EvalVault의 주요 기술 구성 요소와 그들 간의 상호작용을 보여줍니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EVALVAULT CONTAINER DIAGRAM                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              사용자 인터페이스                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐              ┌──────────────────────┐
│                      │              │                      │
│   CLI Application    │              │    Web UI            │
│   (Typer)            │              │    (Streamlit)       │
│                      │              │                      │
│  - run 명령          │              │  - 평가 실행         │
│  - generate 명령     │              │  - 결과 시각화       │
│  - compare 명령      │              │  - 리포트 생성       │
│  - pipeline 명령     │              │  - 히스토리 조회     │
│                      │              │                      │
└──────────┬───────────┘              └──────────┬───────────┘
           │                                    │
           │                                    │
           └──────────────┬─────────────────────┘
                          │
                          │
┌─────────────────────────▼──────────────────────────────────────────────────┐
│                         EVALVAULT CORE APPLICATION                          │
│                    (Hexagonal Architecture / Ports & Adapters)              │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                      DOMAIN LAYER                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │  Entities   │  │  │  Services   │  │   Metrics    │           │   │
│  │  │             │  │  │             │  │              │           │   │
│  │  │ - Dataset   │  │  │ - Evaluator │  │ - Ragas      │           │   │
│  │  │ - Result    │  │  │ - Analysis  │  │ - Custom     │           │   │
│  │  │ - Pipeline  │  │  │ - Pipeline │  │              │           │   │
│  │  │ - Memory    │  │  │ - KG        │  │              │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                      PORTS LAYER                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │  Inbound     │  │  Outbound    │  │  Outbound    │           │   │
│  │  │  Ports       │  │  Ports       │  │  Ports       │           │   │
│  │  │              │  │              │  │              │           │   │
│  │  │ - Evaluator  │  │ - LLM        │  │ - Storage    │           │   │
│  │  │ - Pipeline   │  │ - Dataset    │  │ - Tracker    │           │   │
│  │  │ - Web        │  │ - Analysis   │  │ - Memory     │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    ADAPTERS LAYER                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │  Inbound    │  │  Outbound     │  │  Outbound     │          │   │
│  │  │  Adapters   │  │  Adapters     │  │  Adapters     │          │   │
│  │  │             │  │               │  │               │          │   │
│  │  │ - CLI       │  │ - LLM         │  │ - Storage    │          │   │
│  │  │ - Web       │  │ - Dataset     │  │ - Tracker     │          │   │
│  │  └──────────────┘  │ - Analysis   │  │ - Memory     │          │   │
│  │                    │ - NLP       │  │ - Cache      │          │   │
│  │                    │ - Report    │  │               │          │   │
│  │                    └──────────────┘  └──────────────┘          │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                          │                    │                    │
                          │                    │                    │
        ┌─────────────────┼────────────────────┼────────────────────┼─────────┐
        │                 │                    │                    │         │
        │                 │                    │                    │         │
┌───────▼──────┐  ┌───────▼──────┐  ┌─────────▼──────┐  ┌─────────▼──────┐
│              │  │              │  │                 │  │                 │
│  SQLite/     │  │  Domain      │  │  LLM API        │  │  Langfuse/     │
│  PostgreSQL  │  │  Memory DB   │  │  (OpenAI, etc.) │  │  MLflow        │
│              │  │              │  │                 │  │                 │
│  - 평가 결과 │  │  - 사실      │  │  - 평가 실행    │  │  - 추적 데이터 │
│  - 실행 히스토리│  │  - 패턴     │  │  - 메트릭 계산 │  │  - 시각화      │
│              │  │  - 행동      │  │                 │  │                 │
└──────────────┘  └──────────────┘  └─────────────────┘  └─────────────────┘
```

### 주요 컨테이너 (Containers)

1. **CLI Application (Typer)**
   - **기술**: Python Typer
   - **책임**: 명령줄 인터페이스 제공
   - **포트**: 표준 입출력

2. **Web UI (Streamlit)**
   - **기술**: Streamlit
   - **책임**: 웹 기반 사용자 인터페이스
   - **포트**: HTTP (기본 8501)

3. **EvalVault Core Application**
   - **기술**: Python 3.12+
   - **책임**: 핵심 비즈니스 로직
   - **아키텍처**: Hexagonal Architecture

4. **SQLite/PostgreSQL Database**
   - **기술**: SQLite (기본) 또는 PostgreSQL
   - **책임**: 평가 결과 및 실행 히스토리 저장
   - **포트**: SQLite (파일) 또는 PostgreSQL (5432)

5. **Domain Memory Database**
   - **기술**: SQLite
   - **책임**: 도메인 메모리 (Factual/Experiential/Behavior) 저장
   - **포트**: SQLite (파일)

### 컨테이너 간 통신

- **CLI/Web UI → Core**: 함수 호출 (동기)
- **Core → LLM API**: HTTP/HTTPS (비동기)
- **Core → Database**: SQL (동기)
- **Core → Tracker**: HTTP/HTTPS (비동기)

---

## Level 3: Component Diagram

**컴포넌트 다이어그램**은 EvalVault Core Application 내부의 주요 컴포넌트와 그들 간의 관계를 보여줍니다.

### 3.1 평가 실행 컴포넌트

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EVALUATION EXECUTION COMPONENTS                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          INBOUND ADAPTERS                                   │
│                                                                              │
│  ┌──────────────────┐              ┌──────────────────┐                   │
│  │   CLI Adapter    │              │   Web Adapter    │                   │
│  │                  │              │                  │                   │
│  │  - 명령 파싱      │              │  - 요청 처리     │                   │
│  │  - 입력 검증      │              │  - 세션 관리     │                   │
│  │  - 결과 포맷팅    │              │  - 진행률 표시    │                   │
│  └────────┬─────────┘              └────────┬─────────┘                   │
│           │                                  │                             │
└───────────┼──────────────────────────────────┼─────────────────────────────┘
            │                                  │
            └──────────────┬───────────────────┘
                           │
                           │ EvaluatorPort
                           │
            ┌──────────────▼───────────────────┐
            │                                   │
            │      RagasEvaluator               │
            │      (Domain Service)             │
            │                                   │
            │  - 평가 오케스트레이션            │
            │  - 메트릭 실행                    │
            │  - 결과 집계                      │
            │                                   │
            └──────────────┬───────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        │                  │                  │
┌───────▼──────┐  ┌────────▼────────┐  ┌─────▼──────┐
│              │  │                 │  │             │
│  Dataset     │  │  LLM Adapter    │  │  Metrics    │
│  Entity      │  │  (Outbound)     │  │  (Domain)   │
│              │  │                 │  │             │
│  - TestCase  │  │  - OpenAI       │  │  - Ragas    │
│  - Dataset   │  │  - Anthropic    │  │  - Custom   │
│              │  │  - Ollama       │  │             │
└──────────────┘  └────────────────┘  └─────────────┘
```

### 3.2 분석 파이프라인 컴포넌트

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ANALYSIS PIPELINE COMPONENTS                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          PipelineOrchestrator                                │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │  Intent          │  │  Template        │  │  Module           │        │
│  │  Classifier       │  │  Registry        │  │  Catalog          │        │
│  │                  │  │                  │  │                  │        │
│  │  - 키워드 분석    │  │  - 템플릿 조회    │  │  - 모듈 메타데이터│        │
│  │  - 의도 추출      │  │  - 템플릿 검증    │  │  - 의존성 그래프  │        │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘        │
│           │                     │                      │                   │
│           └──────────┬───────────┴──────────────────────┘                  │
│                      │                                                      │
│                      │ build_pipeline()                                     │
│                      │                                                      │
│           ┌──────────▼──────────────────────────────────────┐              │
│           │                                                  │              │
│           │          AnalysisPipeline                        │              │
│           │          (Domain Entity)                          │              │
│           │                                                  │              │
│           │  - DAG 구조 (nodes, edges)                      │              │
│           │  - 실행 컨텍스트                                │              │
│           └──────────┬──────────────────────────────────────┘              │
│                      │                                                      │
│                      │ execute_pipeline()                                   │
│                      │                                                      │
└──────────────────────┼──────────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐  ┌────▼────┐  ┌─────▼──────┐
│              │  │         │  │             │
│ Statistical  │  │  NLP    │  │  Causal    │
│ Analysis     │  │ Analysis│  │  Analysis  │
│ Module       │  │ Module  │  │  Module    │
│              │  │         │  │             │
│ - 통계 계산  │  │ - 감성  │  │ - 인과관계 │
│ - 분포 분석  │  │ - 주제  │  │ - 원인 분석│
└──────────────┘  └─────────┘  └─────────────┘
```

### 3.3 도메인 메모리 컴포넌트

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DOMAIN MEMORY COMPONENTS                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      DomainLearningHook                                      │
│                      (Domain Service)                                       │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │  Fact Extraction│  │  Pattern         │  │  Behavior         │        │
│  │                  │  │  Extraction      │  │  Extraction       │        │
│  │  - SPO 트리플    │  │  - 성공/실패 패턴│  │  - 재사용 행동    │        │
│  │  - 신뢰도 계산   │  │  - 메트릭 분포   │  │  - 성공률 계산    │        │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘        │
│           │                     │                      │                   │
│           └──────────┬───────────┴──────────────────────┘                  │
│                      │                                                      │
│                      │ DomainMemoryPort                                    │
│                      │                                                      │
│           ┌──────────▼──────────────────────────────────────┐              │
│           │                                                  │              │
│           │      SQLiteDomainMemoryAdapter                  │              │
│           │      (Outbound Adapter)                          │              │
│           │                                                  │              │
│           │  ┌──────────────┐  ┌──────────────┐           │              │
│           │  │  Factual     │  │  Experiential │           │              │
│           │  │  Layer       │  │  Layer       │           │              │
│           │  │              │  │              │           │              │
│           │  │  - FactualFact│ │  - Learning  │           │              │
│           │  │  - SPO 저장  │  │    Memory    │           │              │
│           │  └──────────────┘  └──────────────┘           │              │
│           │                                                  │              │
│           │  ┌──────────────┐                              │              │
│           │  │  Behavior    │                              │              │
│           │  │  Layer       │                              │              │
│           │  │              │                              │              │
│           │  │  - BehaviorEntry                             │              │
│           │  │  - Handbook   │                              │              │
│           │  └──────────────┘                              │              │
│           └─────────────────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 개선 가이드 컴포넌트

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IMPROVEMENT GUIDE COMPONENTS                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    ImprovementGuideService                                   │
│                    (Domain Service)                                          │
│                                                                              │
│  ┌──────────────────┐              ┌──────────────────┐                   │
│  │  Pattern         │              │  Insight         │                   │
│  │  Detector        │              │  Generator       │                   │
│  │  (Rule-based)    │              │  (LLM-based)      │                   │
│  │                  │              │                  │                   │
│  │  - 플레이북 규칙 │              │  - LLM 분석       │                   │
│  │  - 패턴 탐지     │              │  - 인사이트 생성 │                   │
│  └────────┬─────────┘              └────────┬─────────┘                   │
│           │                                  │                             │
│           └──────────────┬───────────────────┘                             │
│                          │                                                   │
│                          │ Hybrid Analysis                                   │
│                          │                                                   │
│           ┌──────────────▼───────────────────┐                             │
│           │                                   │                             │
│           │    ImprovementReport              │                             │
│           │    (Domain Entity)                 │                             │
│           │                                   │                             │
│           │  - 패턴 탐지 결과                 │                             │
│           │  - LLM 인사이트                   │                             │
│           │  - 우선순위 액션                   │                             │
│           └───────────────────────────────────┘                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 주요 컴포넌트 요약

| 컴포넌트 | 계층 | 책임 |
|---------|------|------|
| **RagasEvaluator** | Domain Service | 평가 실행 오케스트레이션 |
| **AnalysisService** | Domain Service | 통계/NLP/인과 분석 통합 |
| **PipelineOrchestrator** | Domain Service | DAG 파이프라인 실행 |
| **DomainLearningHook** | Domain Service | 도메인 메모리 형성 |
| **ImprovementGuideService** | Domain Service | 개선 가이드 생성 |
| **CLI Adapter** | Inbound Adapter | CLI 인터페이스 |
| **Web Adapter** | Inbound Adapter | Web UI 인터페이스 |
| **LLM Adapters** | Outbound Adapter | LLM API 통신 |
| **Storage Adapters** | Outbound Adapter | 데이터베이스 저장 |
| **Analysis Adapters** | Outbound Adapter | 분석 모듈 실행 |

---

## Level 4: Code Structure

**코드 구조**는 주요 컴포넌트의 내부 클래스 및 함수 구조를 보여줍니다.

### 4.1 RagasEvaluator 구조

```python
# domain/services/evaluator.py

class RagasEvaluator:
    """Ragas 기반 RAG 평가 서비스."""

    # 메트릭 매핑
    METRIC_MAP: dict[str, type]
    CUSTOM_METRIC_MAP: dict[str, type]

    async def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
        thresholds: dict[str, float] | None = None,
    ) -> EvaluationRun:
        """평가 실행"""
        # 1. 임계값 해석
        # 2. Ragas 메트릭 실행
        # 3. 커스텀 메트릭 실행
        # 4. 결과 집계
        ...

    async def _evaluate_with_ragas(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
    ) -> list[TestCaseEvalResult]:
        """Ragas 메트릭 실행"""
        ...

    def _aggregate_results(
        self,
        dataset: Dataset,
        metrics: list[str],
        eval_results: list[TestCaseEvalResult],
        thresholds: dict[str, float],
    ) -> EvaluationRun:
        """결과 집계"""
        ...
```

### 4.2 PipelineOrchestrator 구조

```python
# domain/services/pipeline_orchestrator.py

@dataclass
class PipelineOrchestrator:
    """파이프라인 오케스트레이터."""

    module_catalog: ModuleCatalog
    template_registry: PipelineTemplateRegistry
    intent_classifier: KeywordIntentClassifier
    _modules: dict[str, AnalysisModulePort]

    def register_module(self, module: AnalysisModulePort) -> None:
        """모듈 등록"""
        ...

    def build_pipeline(
        self,
        intent: AnalysisIntent,
        context: AnalysisContext,
    ) -> AnalysisPipeline:
        """파이프라인 빌드"""
        # 1. 템플릿 조회
        # 2. 컨텍스트 주입
        # 3. 파이프라인 생성
        ...

    async def execute_pipeline(
        self,
        pipeline: AnalysisPipeline,
        context: AnalysisContext,
    ) -> PipelineResult:
        """파이프라인 실행"""
        # 1. DAG 토폴로지 정렬
        # 2. 의존성 순서대로 실행
        # 3. 결과 집계
        ...
```

### 4.3 DomainLearningHook 구조

```python
# domain/services/domain_learning_hook.py

class DomainLearningHook:
    """도메인 학습 훅 서비스."""

    def __init__(self, memory_port: DomainMemoryPort):
        self.memory_port = memory_port

    async def on_evaluation_complete(
        self,
        evaluation_run: EvaluationRun,
        domain: str,
        language: str = "ko",
        auto_save: bool = True,
    ) -> dict[str, list | LearningMemory]:
        """평가 완료 후 메모리 형성"""
        # 1. 사실 추출
        # 2. 패턴 추출
        # 3. 행동 추출
        ...

    def extract_and_save_facts(...) -> list[FactualFact]:
        """사실 추출 및 저장"""
        ...

    def extract_and_save_patterns(...) -> LearningMemory:
        """패턴 추출 및 저장"""
        ...

    def extract_and_save_behaviors(...) -> list[BehaviorEntry]:
        """행동 추출 및 저장"""
        ...
```

### 4.4 포트 인터페이스 구조

```python
# ports/outbound/llm_port.py

class LLMPort(ABC):
    """LLM 어댑터 인터페이스."""

    @abstractmethod
    def get_model_name(self) -> str:
        """모델 이름 반환"""
        ...

    @abstractmethod
    def as_ragas_llm(self):
        """Ragas 호환 LLM 반환"""
        ...

# ports/outbound/storage_port.py

class StoragePort(Protocol):
    """저장소 인터페이스."""

    def save_run(self, run: EvaluationRun) -> str:
        """평가 실행 저장"""
        ...

    def get_run(self, run_id: str) -> EvaluationRun:
        """평가 실행 조회"""
        ...

    def list_runs(...) -> list[EvaluationRun]:
        """평가 실행 목록 조회"""
        ...
```

---

## 주요 시나리오

### 시나리오 1: 평가 실행 (Evaluation Execution)

```
1. 사용자가 CLI에서 평가 명령 실행
   └─> CLI Adapter가 명령 파싱

2. CLI Adapter가 Dataset Loader 호출
   └─> CSV/JSON/Excel 파일을 Dataset 엔티티로 변환

3. CLI Adapter가 LLM Adapter 생성
   └─> 설정에 따라 OpenAI/Anthropic/Ollama 선택

4. CLI Adapter가 RagasEvaluator.evaluate() 호출
   └─> 도메인 서비스가 평가 실행

5. RagasEvaluator가 LLMPort를 통해 LLM 호출
   └─> 실제 LLM API 통신

6. RagasEvaluator가 결과 집계
   └─> EvaluationRun 엔티티 생성

7. CLI Adapter가 결과 출력
   └─> 사용자에게 결과 표시

8. (선택) Storage Adapter가 결과 저장
   └─> SQLite/PostgreSQL에 저장

9. (선택) Tracker Adapter가 추적 데이터 전송
   └─> Langfuse/MLflow에 기록
```

### 시나리오 2: 분석 파이프라인 실행 (Analysis Pipeline)

```
1. 사용자가 "요약해줘" 쿼리 입력
   └─> CLI/Web Adapter가 쿼리 수신

2. PipelineOrchestrator가 IntentClassifier 호출
   └─> "요약해줘" → GENERATE_SUMMARY 의도 추출

3. PipelineOrchestrator가 TemplateRegistry에서 템플릿 조회
   └─> GENERATE_SUMMARY 템플릿 반환

4. PipelineOrchestrator가 AnalysisPipeline 빌드
   └─> 노드 및 엣지 구성

5. PipelineOrchestrator가 파이프라인 실행
   └─> DAG 순서대로 모듈 실행

6. 각 AnalysisModule이 실행
   └─> Statistical → NLP → Report 순서

7. PipelineResult 반환
   └─> 최종 리포트 생성
```

### 시나리오 3: 도메인 메모리 형성 (Domain Memory Formation)

```
1. 평가 완료 후 DomainLearningHook 호출
   └─> on_evaluation_complete() 실행

2. Fact Extraction
   └─> 높은 신뢰도 평가 결과에서 SPO 트리플 추출
   └─> DomainMemoryPort.save_fact() 호출

3. Pattern Extraction
   └─> 성공/실패 패턴 분석
   └─> DomainMemoryPort.save_learning() 호출

4. Behavior Extraction
   └─> 재사용 가능한 행동 패턴 추출
   └─> DomainMemoryPort.save_behavior() 호출

5. 향후 평가에서 메모리 활용
   └─> hybrid_search()로 관련 메모리 검색
   └─> 평가 컨텍스트에 적용
```

### 시나리오 4: 개선 가이드 생성 (Improvement Guide)

```
1. ImprovementGuideService.generate_report() 호출
   └─> EvaluationRun 입력

2. PatternDetector가 규칙 기반 탐지
   └─> 플레이북 규칙으로 패턴 탐지
   └─> PatternEvidence 생성

3. InsightGenerator가 LLM 기반 분석
   └─> 실패 샘플 일괄 분석
   └─> ClaimImprovementProtocol 생성

4. 두 결과를 하이브리드로 통합
   └─> ImprovementReport 생성
   └─> 우선순위 액션 결정

5. 리포트 반환
   └─> 사용자에게 개선 가이드 제공
```

---

## 아키텍처 원칙

### 1. 의존성 규칙 (Dependency Rule)

```
의존성 방향: 외부 → 내부
Adapters → Ports → Domain
```

- 어댑터는 포트에 의존
- 도메인은 포트에만 의존 (어댑터에 직접 의존하지 않음)
- 포트는 도메인에 속하지만 도메인 서비스에 의존하지 않음

### 2. 단일 책임 원칙 (Single Responsibility)

- 각 컴포넌트는 하나의 명확한 책임만 가짐
- 예: `RagasEvaluator`는 평가 실행만, `AnalysisService`는 분석만

### 3. 개방/폐쇄 원칙 (Open/Closed)

- 확장에는 열려있고 수정에는 닫혀있음
- 새로운 LLM 제공자 추가: 어댑터만 추가
- 새로운 분석 모듈 추가: 모듈만 등록

### 4. 의존성 역전 원칙 (Dependency Inversion)

- 고수준 모듈은 저수준 모듈에 의존하지 않음
- 둘 다 추상화(포트)에 의존
- 예: `RagasEvaluator`는 `LLMPort` 인터페이스에 의존

---

## 기술 스택 요약

| 계층 | 기술 |
|------|------|
| **언어** | Python 3.12+ |
| **CLI 프레임워크** | Typer |
| **Web UI** | Streamlit |
| **평가 프레임워크** | Ragas v1.0 |
| **데이터베이스** | SQLite (기본), PostgreSQL (선택) |
| **추적 시스템** | Langfuse, MLflow |
| **LLM API** | OpenAI, Anthropic, Azure OpenAI, Ollama |
| **설정 관리** | Pydantic Settings |
| **타입 검증** | Python typing, Protocol |

---

## 참고 자료

- **C4 Model**: https://c4model.com/
- **Hexagonal Architecture**: Alistair Cockburn
- **Clean Architecture**: Robert C. Martin
- **Domain-Driven Design**: Eric Evans

---

**문서 버전**: 1.0
**최종 업데이트**: 2026년
**작성자**: EvalVault Team
