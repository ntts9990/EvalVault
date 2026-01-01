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

**코드 구조**는 EvalVault의 모든 클래스를 계층별로 분류하여 보여줍니다.

> **총 클래스 수**: 200+ 클래스
> - Domain Layer: 96 클래스 (Entities 75, Services 20, Metrics 1)
> - Ports Layer: 40 클래스 (Inbound 8, Outbound 32)
> - Adapters Layer: 85 클래스 (Inbound 20, Outbound 65)
> - Config Layer: 14 클래스

---

### 4.1 Domain Layer - Entities (75 클래스)

#### 4.1.1 Core Entities

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `TestCase` | dataset.py | 개별 평가 테스트 케이스 |
| `Dataset` | dataset.py | 테스트 케이스 컬렉션 |
| `MetricScore` | result.py | 개별 메트릭 점수 |
| `TestCaseResult` | result.py | 테스트 케이스 평가 결과 |
| `EvaluationRun` | result.py | 전체 평가 실행 결과 |
| `MetricType` | result.py | 메트릭 타입 Enum |

#### 4.1.2 Experiment Entities

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `ExperimentGroup` | experiment.py | 실험 그룹 정의 |
| `Experiment` | experiment.py | A/B 실험 정의 |

#### 4.1.3 Knowledge Graph Entities

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `EntityModel` | kg.py | 지식 그래프 엔티티 |
| `RelationModel` | kg.py | 지식 그래프 관계 |

#### 4.1.4 Analysis Pipeline Entities (10 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `AnalysisIntent` | analysis_pipeline.py | 분석 의도 Enum (19개 의도) |
| `AnalysisIntentCategory` | analysis_pipeline.py | 의도 카테고리 Enum |
| `NodeExecutionStatus` | analysis_pipeline.py | 노드 실행 상태 |
| `AnalysisNode` | analysis_pipeline.py | DAG 파이프라인 노드 |
| `AnalysisContext` | analysis_pipeline.py | 분석 실행 컨텍스트 |
| `AnalysisPipeline` | analysis_pipeline.py | DAG 파이프라인 정의 |
| `NodeResult` | analysis_pipeline.py | 노드 실행 결과 |
| `PipelineResult` | analysis_pipeline.py | 파이프라인 실행 결과 |
| `ModuleMetadata` | analysis_pipeline.py | 모듈 메타데이터 |
| `ModuleCatalog` | analysis_pipeline.py | 모듈 카탈로그 |

#### 4.1.5 Domain Memory Entities (5 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `FactualFact` | memory.py | 사실적 기억 (SPO 트리플) |
| `LearningMemory` | memory.py | 학습 기억 (패턴) |
| `DomainMemoryContext` | memory.py | 메모리 검색 컨텍스트 |
| `BehaviorEntry` | memory.py | 행동 기억 엔트리 |
| `BehaviorHandbook` | memory.py | 행동 핸드북 |

#### 4.1.6 Improvement Entities (11 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `RAGComponent` | improvement.py | RAG 컴포넌트 Enum |
| `ImprovementPriority` | improvement.py | 개선 우선순위 Enum |
| `PatternType` | improvement.py | 패턴 타입 Enum |
| `EffortLevel` | improvement.py | 노력 수준 Enum |
| `EvidenceSource` | improvement.py | 증거 소스 Enum |
| `FailureSample` | improvement.py | 실패 샘플 |
| `PatternEvidence` | improvement.py | 패턴 탐지 증거 |
| `ImprovementEvidence` | improvement.py | 개선 증거 |
| `ImprovementAction` | improvement.py | 개선 액션 |
| `RAGImprovementGuide` | improvement.py | RAG 개선 가이드 |
| `ImprovementReport` | improvement.py | 개선 리포트 |

#### 4.1.7 RAG Trace Entities (6 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `RetrievalMethod` | rag_trace.py | 검색 방법 Enum |
| `RerankMethod` | rag_trace.py | 재순위 방법 Enum |
| `RetrievedDocument` | rag_trace.py | 검색된 문서 |
| `RetrievalData` | rag_trace.py | 검색 단계 데이터 |
| `GenerationData` | rag_trace.py | 생성 단계 데이터 |
| `RAGTraceData` | rag_trace.py | RAG 파이프라인 추적 데이터 |

#### 4.1.8 Benchmark Entities (8 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `TaskType` | benchmark.py | 벤치마크 태스크 타입 |
| `MetricType` | benchmark.py | 벤치마크 메트릭 타입 |
| `RAGTestCase` | benchmark.py | 벤치마크 테스트 케이스 |
| `RAGTestCaseResult` | benchmark.py | 테스트 케이스 결과 |
| `SplitScores` | benchmark.py | 분할 점수 |
| `BenchmarkResult` | benchmark.py | 벤치마크 결과 |
| `BenchmarkSuite` | benchmark.py | 벤치마크 스위트 |
| `BenchmarkConfig` | benchmark.py | 벤치마크 설정 |

#### 4.1.9 Statistical Analysis Entities (27 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `AnalysisType` | analysis.py | 분석 타입 Enum |
| `QuestionType` | analysis.py | 질문 타입 Enum |
| `EffectSizeLevel` | analysis.py | 효과 크기 수준 |
| `MetricStats` | analysis.py | 메트릭 통계 |
| `CorrelationInsight` | analysis.py | 상관관계 인사이트 |
| `LowPerformerInfo` | analysis.py | 저성과 정보 |
| `ComparisonResult` | analysis.py | 비교 결과 |
| `AnalysisResult` | analysis.py | 분석 결과 기본 클래스 |
| `StatisticalAnalysis` | analysis.py | 통계 분석 결과 |
| `MetaAnalysisResult` | analysis.py | 메타 분석 결과 |
| `AnalysisBundle` | analysis.py | 분석 번들 |
| `TextStats` | analysis.py | 텍스트 통계 |
| `QuestionTypeStats` | analysis.py | 질문 타입 통계 |
| `KeywordInfo` | analysis.py | 키워드 정보 |
| `TopicCluster` | analysis.py | 토픽 클러스터 |
| `NLPAnalysis` | analysis.py | NLP 분석 결과 |
| `CausalFactorType` | analysis.py | 인과 요인 타입 |
| `ImpactDirection` | analysis.py | 영향 방향 |
| `ImpactStrength` | analysis.py | 영향 강도 |
| `FactorStats` | analysis.py | 요인 통계 |
| `StratifiedGroup` | analysis.py | 계층화 그룹 |
| `FactorImpact` | analysis.py | 요인 영향 |
| `CausalRelationship` | analysis.py | 인과 관계 |
| `RootCause` | analysis.py | 근본 원인 |
| `InterventionSuggestion` | analysis.py | 개입 제안 |
| `CausalAnalysis` | analysis.py | 인과 분석 결과 |

---

### 4.2 Domain Layer - Services (20 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `RagasEvaluator` | evaluator.py | Ragas 기반 평가 서비스 |
| `TestCaseEvalResult` | evaluator.py | 테스트 케이스 평가 결과 |
| `ExperimentManager` | experiment_manager.py | 실험 관리 서비스 |
| `MetricComparison` | experiment_manager.py | 메트릭 비교 결과 |
| `PipelineOrchestrator` | pipeline_orchestrator.py | 파이프라인 오케스트레이터 |
| `AnalysisPipelineService` | pipeline_orchestrator.py | 분석 파이프라인 서비스 |
| `PipelineTemplateRegistry` | pipeline_template_registry.py | 파이프라인 템플릿 레지스트리 |
| `IntentKeywordRegistry` | intent_classifier.py | 의도 키워드 레지스트리 |
| `KeywordIntentClassifier` | intent_classifier.py | 키워드 기반 의도 분류기 |
| `AnalysisService` | analysis_service.py | 통합 분석 서비스 |
| `DomainLearningHook` | domain_learning_hook.py | 도메인 학습 훅 |
| `ImprovementGuideService` | improvement_guide_service.py | 개선 가이드 서비스 |
| `KnowledgeGraph` | kg_generator.py | 지식 그래프 |
| `KnowledgeGraphGenerator` | kg_generator.py | 지식 그래프 생성기 |
| `Entity` | entity_extractor.py | 추출된 엔티티 |
| `Relation` | entity_extractor.py | 추출된 관계 |
| `EntityExtractor` | entity_extractor.py | 엔티티 추출기 |
| `GenerationConfig` | testset_generator.py | 테스트셋 생성 설정 |
| `BasicTestsetGenerator` | testset_generator.py | 기본 테스트셋 생성기 |
| `DocumentChunker` | document_chunker.py | 문서 청킹 서비스 |
| `BenchmarkComparison` | benchmark_runner.py | 벤치마크 비교 |
| `KoreanRAGBenchmarkRunner` | benchmark_runner.py | 한국어 RAG 벤치마크 러너 |

---

### 4.3 Domain Layer - Metrics (1 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `InsuranceTermAccuracy` | insurance.py | 보험 용어 정확도 메트릭 |

---

### 4.4 Ports Layer - Inbound (8 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `EvaluatorPort` | evaluator_port.py | 평가 실행 포트 |
| `AnalysisPipelinePort` | analysis_pipeline_port.py | 분석 파이프라인 포트 |
| `DomainLearningHookPort` | learning_hook_port.py | 도메인 학습 훅 포트 |
| `EvalRequest` | web_port.py | 평가 요청 DTO |
| `EvalProgress` | web_port.py | 평가 진행률 DTO |
| `RunSummary` | web_port.py | 실행 요약 DTO |
| `RunFilters` | web_port.py | 실행 필터 DTO |
| `WebUIPort` | web_port.py | 웹 UI 포트 |

---

### 4.5 Ports Layer - Outbound (32 클래스)

#### 4.5.1 LLM & Embedding Ports

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `ThinkingConfig` | llm_port.py | Thinking 모드 설정 |
| `LLMPort` | llm_port.py | LLM 어댑터 인터페이스 |
| `EmbeddingResult` | embedding_port.py | 임베딩 결과 |
| `EmbeddingPort` | embedding_port.py | 임베딩 포트 |

#### 4.5.2 Data & Storage Ports

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `DatasetPort` | dataset_port.py | 데이터셋 로더 포트 |
| `StoragePort` | storage_port.py | 저장소 포트 |
| `DomainMemoryPort` | domain_memory_port.py | 도메인 메모리 포트 |
| `AnalysisCachePort` | analysis_cache_port.py | 분석 캐시 포트 |

#### 4.5.3 Analysis Ports

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `AnalysisPort` | analysis_port.py | 통계 분석 포트 |
| `NLPAnalysisPort` | nlp_analysis_port.py | NLP 분석 포트 |
| `CausalAnalysisPort` | causal_analysis_port.py | 인과 분석 포트 |
| `AnalysisModulePort` | analysis_module_port.py | 분석 모듈 포트 |
| `IntentClassificationResult` | intent_classifier_port.py | 의도 분류 결과 |
| `IntentClassifierPort` | intent_classifier_port.py | 의도 분류기 포트 |

#### 4.5.4 Tracking & Report Ports

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `TrackerPort` | tracker_port.py | 추적기 포트 |
| `ReportPort` | report_port.py | 리포트 포트 |

#### 4.5.5 Korean NLP Ports

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `FaithfulnessClaimResultProtocol` | korean_nlp_port.py | 충실도 클레임 결과 |
| `FaithfulnessResultProtocol` | korean_nlp_port.py | 충실도 결과 |
| `RetrieverResultProtocol` | korean_nlp_port.py | 검색기 결과 |
| `RetrieverPort` | korean_nlp_port.py | 검색기 포트 |
| `KoreanNLPToolkitPort` | korean_nlp_port.py | 한국어 NLP 툴킷 포트 |

#### 4.5.6 Improvement Ports

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `ActionDefinitionProtocol` | improvement_port.py | 액션 정의 프로토콜 |
| `PatternDefinitionProtocol` | improvement_port.py | 패턴 정의 프로토콜 |
| `MetricPlaybookProtocol` | improvement_port.py | 메트릭 플레이북 프로토콜 |
| `PlaybookPort` | improvement_port.py | 플레이북 포트 |
| `PatternDetectorPort` | improvement_port.py | 패턴 탐지기 포트 |
| `ClaimImprovementProtocol` | improvement_port.py | 클레임 개선 프로토콜 |
| `InsightGeneratorPort` | improvement_port.py | 인사이트 생성기 포트 |

#### 4.5.7 Other Ports

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `RelationAugmenterPort` | relation_augmenter_port.py | 관계 증강기 포트 |

---

### 4.6 Adapters Layer - Inbound (20 클래스)

#### 4.6.1 Web UI Adapters

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `WebUIAdapter` | adapter.py | 웹 UI 어댑터 메인 |
| `GateResult` | adapter.py | 품질 게이트 결과 |
| `GateReport` | adapter.py | 품질 게이트 리포트 |
| `WebSession` | session.py | 웹 세션 관리 |

#### 4.6.2 Web Components - Upload & Cards

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `ValidationResult` | upload.py | 파일 검증 결과 |
| `FileUploadHandler` | upload.py | 파일 업로드 핸들러 |
| `MetricSummaryCard` | cards.py | 메트릭 요약 카드 |
| `StatCard` | cards.py | 통계 카드 |

#### 4.6.3 Web Components - History

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `RunFilter` | history.py | 실행 필터 컴포넌트 |
| `RunTable` | history.py | 실행 테이블 컴포넌트 |
| `RunDetailPanel` | history.py | 실행 상세 패널 |
| `HistoryExporter` | history.py | 히스토리 내보내기 |
| `RunSearch` | history.py | 실행 검색 컴포넌트 |

#### 4.6.4 Web Components - Other

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `RecentRunsList` | lists.py | 최근 실행 목록 |
| `MetricSelector` | metrics.py | 메트릭 선택기 |
| `EvaluationProgress` | progress.py | 평가 진행률 표시 |
| `ProgressStep` | progress.py | 진행 단계 |
| `DashboardStats` | stats.py | 대시보드 통계 |
| `EvaluationConfig` | evaluate.py | 평가 설정 |
| `EvaluationResult` | evaluate.py | 평가 결과 표시 |

#### 4.6.5 Web Components - Reports

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `ReportConfig` | reports.py | 리포트 설정 |
| `ReportResult` | reports.py | 리포트 결과 |
| `ReportTemplate` | reports.py | 리포트 템플릿 |
| `ReportGenerator` | reports.py | 리포트 생성기 |
| `ReportDownloader` | reports.py | 리포트 다운로더 |
| `RunSelector` | reports.py | 실행 선택기 |
| `ReportPreview` | reports.py | 리포트 미리보기 |

---

### 4.7 Adapters Layer - Outbound LLM (10 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `BaseLLMAdapter` | base.py | LLM 어댑터 기본 클래스 |
| `LLMConfigurationError` | base.py | LLM 설정 오류 |
| `TokenUsage` | base.py | 토큰 사용량 |
| `OpenAIAdapter` | openai_adapter.py | OpenAI 어댑터 |
| `TokenTrackingAsyncOpenAI` | openai_adapter.py | 토큰 추적 AsyncOpenAI |
| `OpenAIEmbeddingsWithLegacy` | openai_adapter.py | 레거시 임베딩 지원 |
| `AzureOpenAIAdapter` | azure_adapter.py | Azure OpenAI 어댑터 |
| `AnthropicAdapter` | anthropic_adapter.py | Anthropic 어댑터 |
| `ThinkingTokenTrackingAsyncAnthropic` | anthropic_adapter.py | Thinking 토큰 추적 |
| `OllamaAdapter` | ollama_adapter.py | Ollama 어댑터 |
| `ThinkingTokenTrackingAsyncOpenAI` | ollama_adapter.py | Thinking 토큰 추적 (Ollama) |
| `LLMRelationAugmenter` | llm_relation_augmenter.py | LLM 기반 관계 증강 |

---

### 4.8 Adapters Layer - Outbound Storage (4 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `BaseSQLStorageAdapter` | base_sql.py | SQL 저장소 기본 클래스 |
| `SQLQueries` | base_sql.py | SQL 쿼리 정의 |
| `SQLiteStorageAdapter` | sqlite_adapter.py | SQLite 저장소 어댑터 |
| `PostgreSQLStorageAdapter` | postgres_adapter.py | PostgreSQL 저장소 어댑터 |

---

### 4.9 Adapters Layer - Outbound Tracker (3 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `LangfuseAdapter` | langfuse_adapter.py | Langfuse 추적 어댑터 |
| `MLflowAdapter` | mlflow_adapter.py | MLflow 추적 어댑터 |
| `PhoenixAdapter` | phoenix_adapter.py | Phoenix/OpenTelemetry 어댑터 |

---

### 4.10 Adapters Layer - Outbound Dataset (4 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `BaseDatasetLoader` | base.py | 데이터셋 로더 기본 클래스 |
| `CSVDatasetLoader` | csv_loader.py | CSV 로더 |
| `ExcelDatasetLoader` | excel_loader.py | Excel 로더 |
| `JSONDatasetLoader` | json_loader.py | JSON 로더 |

---

### 4.11 Adapters Layer - Outbound Korean NLP (18 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `KiwiTokenizer` | kiwi_tokenizer.py | Kiwi 한국어 토크나이저 |
| `Token` | kiwi_tokenizer.py | 토큰 |
| `KoreanBM25Retriever` | bm25_retriever.py | BM25 검색기 |
| `RetrievalResult` | bm25_retriever.py | 검색 결과 |
| `KoreanDenseRetriever` | dense_retriever.py | Dense 검색기 |
| `DenseRetrievalResult` | dense_retriever.py | Dense 검색 결과 |
| `DeviceType` | dense_retriever.py | 디바이스 타입 |
| `KoreanHybridRetriever` | hybrid_retriever.py | 하이브리드 검색기 |
| `HybridResult` | hybrid_retriever.py | 하이브리드 검색 결과 |
| `FusionMethod` | hybrid_retriever.py | 퓨전 방법 |
| `KoreanDocumentChunker` | document_chunker.py | 문서 청커 |
| `ParagraphChunker` | document_chunker.py | 단락 청커 |
| `Chunk` | document_chunker.py | 청크 |
| `KoreanFaithfulnessChecker` | korean_evaluation.py | 한국어 충실도 검사기 |
| `KoreanSemanticSimilarity` | korean_evaluation.py | 한국어 의미 유사도 |
| `FaithfulnessResult` | korean_evaluation.py | 충실도 결과 |
| `ClaimVerification` | korean_evaluation.py | 클레임 검증 |
| `NumberWithUnit` | korean_evaluation.py | 단위 숫자 |
| `SemanticSimilarityResult` | korean_evaluation.py | 의미 유사도 결과 |
| `KoreanNLPToolkit` | toolkit.py | 한국어 NLP 툴킷 |
| `_RetrieverWrapper` | toolkit.py | 검색기 래퍼 |

---

### 4.12 Adapters Layer - Outbound Analysis (13 클래스)

#### 4.12.1 Analysis Adapters

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `BaseAnalysisAdapter` | common.py | 분석 어댑터 기본 클래스 |
| `AnalysisDataProcessor` | common.py | 분석 데이터 처리기 |
| `StatisticalAnalysisAdapter` | statistical_adapter.py | 통계 분석 어댑터 |
| `NLPAnalysisAdapter` | nlp_adapter.py | NLP 분석 어댑터 |
| `CausalAnalysisAdapter` | causal_adapter.py | 인과 분석 어댑터 |

#### 4.12.2 Analysis Modules

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `BaseAnalysisModule` | base_module.py | 분석 모듈 기본 클래스 |
| `DataLoaderModule` | data_loader_module.py | 데이터 로더 모듈 |
| `StatisticalAnalyzerModule` | statistical_analyzer_module.py | 통계 분석 모듈 |
| `NLPAnalyzerModule` | nlp_analyzer_module.py | NLP 분석 모듈 |
| `CausalAnalyzerModule` | causal_analyzer_module.py | 인과 분석 모듈 |
| `SummaryReportModule` | summary_report_module.py | 요약 리포트 모듈 |
| `AnalysisReportModule` | analysis_report_module.py | 분석 리포트 모듈 |
| `ComparisonReportModule` | comparison_report_module.py | 비교 리포트 모듈 |
| `VerificationReportModule` | verification_report_module.py | 검증 리포트 모듈 |

---

### 4.13 Adapters Layer - Outbound Improvement (10 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `PatternDetector` | pattern_detector.py | 패턴 탐지기 |
| `FeatureVector` | pattern_detector.py | 특징 벡터 |
| `PlaybookLoader` | playbook_loader.py | 플레이북 로더 |
| `Playbook` | playbook_loader.py | 플레이북 |
| `MetricPlaybook` | playbook_loader.py | 메트릭 플레이북 |
| `PatternDefinition` | playbook_loader.py | 패턴 정의 |
| `ActionDefinition` | playbook_loader.py | 액션 정의 |
| `DetectionRule` | playbook_loader.py | 탐지 규칙 |
| `InsightGenerator` | insight_generator.py | 인사이트 생성기 |
| `LLMInsight` | insight_generator.py | LLM 인사이트 |
| `BatchPatternInsight` | insight_generator.py | 배치 패턴 인사이트 |

---

### 4.14 Adapters Layer - Outbound Report (4 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `LLMReportGenerator` | llm_report_generator.py | LLM 리포트 생성기 |
| `LLMReport` | llm_report_generator.py | LLM 리포트 |
| `LLMReportSection` | llm_report_generator.py | LLM 리포트 섹션 |
| `MarkdownReportAdapter` | markdown_adapter.py | 마크다운 리포트 어댑터 |

---

### 4.15 Adapters Layer - Outbound Other (2 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `SQLiteDomainMemoryAdapter` | sqlite_adapter.py | SQLite 도메인 메모리 어댑터 |
| `MemoryCacheAdapter` | memory_cache.py | 메모리 캐시 어댑터 |

---

### 4.16 Config Layer (14 클래스)

| 클래스 | 파일 | 설명 |
|--------|------|------|
| `Settings` | settings.py | 환경 설정 (pydantic-settings) |
| `LLMConfig` | model_config.py | LLM 설정 |
| `EmbeddingConfig` | model_config.py | 임베딩 설정 |
| `ProfileConfig` | model_config.py | 프로필 설정 |
| `ModelConfig` | model_config.py | 모델 설정 |
| `LanguageConfig` | domain_config.py | 언어 설정 |
| `FactualConfig` | domain_config.py | 사실 기억 설정 |
| `ExperientialConfig` | domain_config.py | 경험 기억 설정 |
| `WorkingConfig` | domain_config.py | 작업 기억 설정 |
| `LearningConfig` | domain_config.py | 학습 설정 |
| `DomainMetadata` | domain_config.py | 도메인 메타데이터 |
| `DomainMemoryConfig` | domain_config.py | 도메인 메모리 설정 |
| `AgentMode` | agent_types.py | 에이전트 모드 Enum |
| `AgentType` | agent_types.py | 에이전트 타입 Enum |
| `AgentConfig` | agent_types.py | 에이전트 설정 |

---

### 4.17 주요 서비스 상세 구조

#### RagasEvaluator (domain/services/evaluator.py)

```python
class RagasEvaluator:
    """Ragas 기반 RAG 평가 서비스."""

    METRIC_MAP: dict[str, type]       # Ragas 메트릭 매핑
    CUSTOM_METRIC_MAP: dict[str, type] # 커스텀 메트릭 매핑

    async def evaluate(dataset, metrics, llm, thresholds) -> EvaluationRun:
        """평가 실행: 임계값 해석 → Ragas 실행 → 결과 집계"""

    async def _evaluate_with_ragas(...) -> list[TestCaseEvalResult]:
        """Ragas 메트릭 실행"""

    def _aggregate_results(...) -> EvaluationRun:
        """결과 집계 및 EvaluationRun 생성"""
```

#### PipelineOrchestrator (domain/services/pipeline_orchestrator.py)

```python
class PipelineOrchestrator:
    """DAG 기반 분석 파이프라인 오케스트레이터."""

    module_catalog: ModuleCatalog
    template_registry: PipelineTemplateRegistry
    intent_classifier: KeywordIntentClassifier

    def register_module(module: AnalysisModulePort) -> None:
        """모듈 등록"""

    def build_pipeline(intent, context) -> AnalysisPipeline:
        """템플릿 기반 파이프라인 빌드"""

    async def execute_pipeline(pipeline, context) -> PipelineResult:
        """DAG 토폴로지 정렬 → 의존성 순서 실행 → 결과 집계"""
```

#### DomainLearningHook (domain/services/domain_learning_hook.py)

```python
class DomainLearningHook:
    """도메인 학습 훅 - 3계층 메모리 형성."""

    async def on_evaluation_complete(evaluation_run, domain, language) -> dict:
        """평가 완료 후 Factual/Experiential/Behavior 메모리 형성"""

    def extract_and_save_facts(...) -> list[FactualFact]:
        """SPO 트리플 추출 및 저장"""

    def extract_and_save_patterns(...) -> LearningMemory:
        """성공/실패 패턴 추출 및 저장"""

    def extract_and_save_behaviors(...) -> list[BehaviorEntry]:
        """재사용 행동 패턴 추출 및 저장"""
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

**문서 버전**: 2.0
**최종 업데이트**: 2026-01-02
**작성자**: EvalVault Team

### 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2026-01 | 초기 C4 문서 작성 |
| 2.0 | 2026-01-02 | Level 4 클래스 카탈로그 전면 현행화 (200+ 클래스 문서화) |
