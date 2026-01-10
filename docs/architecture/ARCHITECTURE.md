# EvalVault 아키텍처 가이드

> **Hexagonal Architecture (Ports & Adapters) + Clean Architecture + Domain-Driven Design 기반**

이 문서는 EvalVault의 아키텍처를 매우 상세하게 설명하는 학습 교과서입니다. 소프트웨어 아키텍처 방법론, 설계 원칙, 데이터 흐름, 각 컴포넌트의 역할과 책임을 다룹니다.

## 📚 관련 문서

| 문서 | 역할 | 설명 |
|------|------|------|
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** (이 문서) | 메인 아키텍처 가이드 | 상세한 아키텍처 설명, 설계 원칙, 데이터 흐름 |
| [internal/reference/ARCHITECTURE_C4.md](../internal/reference/ARCHITECTURE_C4.md) | C4 다이어그램 | C4 Model 기반 계층적 아키텍처 다이어그램 |
| [internal/reference/CLASS_CATALOG.md](../internal/reference/CLASS_CATALOG.md) | 클래스 카탈로그 | 모든 클래스의 역할별/프로세스별 분류 |
| [internal/reference/DEVELOPMENT_GUIDE.md](../internal/reference/DEVELOPMENT_GUIDE.md) | 개발 가이드 | 개발 환경, 코드 품질, 에이전트 시스템 |
| [internal/reference/FEATURE_SPECS.md](../internal/reference/FEATURE_SPECS.md) | 기능 스펙 | 한국어 RAG, Phoenix, Domain Memory 등 상세 |

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

### 1.0 프로젝트 미션 및 핵심 기능

EvalVault는 RAG 시스템의 품질을 일관되게 평가하고 비교할 수 있는 표준 워크플로를 제공하는 것을 목표로 합니다. CLI와 FastAPI + React Web UI를 함께 제공해 평가 실행부터 결과 공유까지의 진입 장벽을 낮춥니다. 평가 결과는 SQLite/PostgreSQL에 저장되고 Langfuse·Phoenix·MLflow 같은 추적기와 연결됩니다. 도메인 메모리와 분석 파이프라인을 통해 과거 평가 결과를 재사용하고 개선 방향을 제시하는 데 초점을 둡니다.

**핵심 기능군**:
- **평가 실행**: Ragas 기반 메트릭과 커스텀 메트릭을 조합해 질문/답변/컨텍스트 품질을 정량화
- **결과 저장/비교**: 평가 결과를 데이터베이스에 저장하고 실행 간 비교 분석
- **추적 연동**: Langfuse/Phoenix/MLflow와 연동하여 Stage-level 트레이싱
- **분석/리포팅**: DAG 분석 파이프라인으로 통계/NLP/인과 분석 수행
- **Domain Memory**: 사실/행동/학습 레이어를 통해 평가 결과를 축적하고 다음 평가에 반영
- **한국어 RAG 최적화**: Kiwi 형태소 분석, BM25, Dense, Hybrid 검색기와 한국어 faithfulness 검증

**주요 사용자**:
- **개발자**: CLI로 평가를 실행하고 history/compare/export로 실행 결과를 분석
- **평가 담당자**: Web UI에서 평가 실행, 업로드, 히스토리 탐색, 기본 보고서 생성
- **운영팀**: Phoenix 기반 드리프트 감시와 Gate 실행을 통해 품질 변화를 상시 모니터링

### 1.1 소스 구조 요약

EvalVault의 핵심 패키지는 `src/evalvault/` 아래에 위치하며 domain/ports/adapters/config로 계층이 분리되어 있습니다.

```
src/evalvault/
├── domain/          # 핵심 도메인 로직 (엔티티, 서비스, 메트릭)
├── ports/           # 계약(인터페이스) - inbound/outbound
├── adapters/        # 외부 통합 (CLI/Web/LLM/스토리지/트레이싱)
└── config/          # 런타임 설정 (Settings, ModelConfig, DomainConfig)
```

**의존성 방향**: 어댑터 → 포트 → 도메인 (외부 → 내부)

### 1.2 전체 구조 다이어그램

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
│  ├── cli.py                       │                    │  ├── dataset/                     │
│  │   └── Typer 기반 CLI            │                    │  │   ├── __init__.py              │
│  │       - run 명령                │                    │  │   ├── base.py                  │
│  │       - generate 명령           │                    │  │   ├── csv_loader.py             │
│  │       - history 명령             │                    │  │   ├── excel_loader.py           │
│  │       - compare 명령             │                    │  │   ├── json_loader.py            │
│  │       - experiment 명령들        │                    │  │   └── loader_factory.py        │
│  │       - pipeline 명령            │                    │  │                                 │
│  │       - benchmark 명령          │                    │  ├── llm/                          │
│  │       - domain 명령              │                    │  │   ├── __init__.py               │
│  │                                 │                    │  │   ├── anthropic_adapter.py      │
│  │  └── web/                       │                    │  │   ├── azure_adapter.py          │
│  │      ├── adapter.py             │                    │  │   ├── ollama_adapter.py         │
│  │      ├── app.py                │                    │  │   ├── openai_adapter.py         │
│  │      ├── components/           │                    │  │   ├── vllm_adapter.py           │
│  │      │   ├── cards.py          │                    │  │   └── llm_relation_augmenter.py │
│  │      │   ├── cards.py          │                    │  │                                 │
│  │      │   ├── charts.py         │                    │  ├── storage/                      │
│  │      │   ├── evaluate.py       │                    │  │   ├── __init__.py               │
│  │      │   ├── history.py        │                    │  │   ├── postgres_adapter.py       │
│  │      │   ├── reports.py        │                    │  │   ├── sqlite_adapter.py         │
│  │      │   └── upload.py         │                    │  │   ├── postgres_schema.sql       │
│  │      └── session.py            │                    │  │   └── schema.sql                   │
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
│                                   │                    │  ├── analysis_module_port.py       │
│                                   │                    │  │   └── AnalysisModulePort        │
│                                   │                    │  │                                 │
│                                   │                    │  ├── analysis_cache_port.py         │
│                                   │                    │  │   └── AnalysisCachePort         │
│                                   │                    │  │                                 │
│                                   │                    │  ├── nlp_analysis_port.py          │
│                                   │                    │  │   └── NLPAnalysisPort           │
│                                   │                    │  │                                 │
│                                   │                    │  ├── causal_analysis_port.py       │
│                                   │                    │  │   └── CausalAnalysisPort       │
│                                   │                    │  │                                 │
│                                   │                    │  ├── domain_memory_port.py         │
│                                   │                    │  │   └── DomainMemoryPort          │
│                                   │                    │  │       (Factual/Experiential/    │
│                                   │                    │  │        Behavior 레이어)         │
│                                   │                    │  │                                 │
│                                   │                    │  ├── improvement_port.py           │
│                                   │                    │  │   └── PatternDetectorPort       │
│                                   │                    │  │   └── InsightGeneratorPort      │
│                                   │                    │  │   └── PlaybookPort              │
│                                   │                    │  │                                 │
│                                   │                    │  ├── korean_nlp_port.py            │
│                                   │                    │  │   └── KoreanNLPPort            │
│                                   │                    │  │                                 │
│                                   │                    │  ├── embedding_port.py             │
│                                   │                    │  │   └── EmbeddingPort            │
│                                   │                    │  │                                 │
│                                   │                    │  ├── relation_augmenter_port.py   │
│                                   │                    │  │   └── RelationAugmenterPort    │
│                                   │                    │  │                                 │
│                                   │                    │  ├── intent_classifier_port.py     │
│                                   │                    │  │   └── IntentClassifierPort      │
│                                   │                    │  │                                 │
│                                   │                    │  └── report_port.py                │
│                                   │                    │      └── ReportPort                │
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
│  │   ├── benchmark.py                  ─ Benchmark 엔티티                         │
│  │   │   └── BenchmarkRun, BenchmarkResult                                          │
│  │   │       - 벤치마크 실행 및 결과                                                 │
│  │   │                                                                              │
│  │   ├── improvement.py                 ─ Improvement 엔티티                        │
│  │   │   └── ImprovementReport, ImprovementAction, PatternEvidence                 │
│  │   │       - 개선 가이드 및 액션                                                  │
│  │   │       - 패턴 탐지 결과                                                        │
│  │   │                                                                              │
│  │   ├── kg.py                          ─ Knowledge Graph 엔티티                     │
│  │   │   └── KnowledgeGraph, Entity, Relation                                       │
│  │   │       - 지식 그래프 구조                                                     │
│  │   │       - 엔티티 및 관계 표현                                                   │
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
│      ├── experiment_manager.py         ─ 실험 관리 서비스                          │
│      │   └── ExperimentManager                                                     │
│      │       - A/B 테스트 관리                                                       │
│      │       - 그룹별 메트릭 비교                                                    │
│      │       - 실험 결론 기록                                                        │
│      │                                                                              │
│      ├── domain_learning_hook.py       ─ 도메인 학습 훅 서비스                     │
│      │   └── DomainLearningHook                                                    │
│      │       - 평가 결과에서 메모리 형성 (Formation)                                │
│      │       - 사실, 패턴, 행동 추출                                                 │
│      │       - 메모리 진화 관리 (Evolution)                                         │
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
│      ├── pipeline_template_registry.py  ─ 파이프라인 템플릿 레지스트리             │
│      │   └── PipelineTemplateRegistry                                             │
│      │       - 분석 의도별 템플릿 관리                                              │
│      │       - 템플릿 검증 및 등록                                                  │
│      │                                                                              │
│      ├── intent_classifier.py           ─ 의도 분류 서비스                         │
│      │   └── KeywordIntentClassifier                                               │
│      │       - 사용자 쿼리에서 분석 의도 추출                                       │
│      │       - 키워드 기반 분류                                                     │
│      │                                                                              │
│      ├── improvement_guide_service.py  ─ 개선 가이드 서비스                        │
│      │   └── ImprovementGuideService                                               │
│      │       - 규칙 기반 패턴 탐지                                                  │
│      │       - LLM 기반 인사이트 생성                                               │
│      │       - 하이브리드 분석 및 리포트 생성                                       │
│      │                                                                              │
│      └── benchmark_runner.py           ─ 벤치마크 러너 서비스                      │
│          └── BenchmarkRunner                                                       │
│              - 한국어 RAG 벤치마크 실행                                             │
│              - 메트릭 비교 및 리더보드 생성                                         │
│                                                                                     │
│      ├── memory_aware_evaluator.py     ─ 도메인 메모리 기반 평가                    │
│      │   └── MemoryAwareEvaluator                                                   │
│      │       - DomainMemoryPort 신뢰도로 threshold 자동 조정                        │
│      │       - Phoenix span으로 검색/컨텍스트 보강                                    │
│      │                                                                              │
│      ├── memory_based_analysis.py      ─ 메모리 기반 분석                           │
│      │   └── MemoryBasedAnalysis                                                   │
│      │       - 과거 LearningMemory와 현재 EvaluationRun 비교                        │
│      │       - 행동 패턴 재사용, 추천문 생성                                        │
│      │                                                                              │
│      ├── domain_learning_hook.py       ─ Formation dynamics 엔트리                  │
│      │   └── DomainLearningHook                                                    │
│      │       - 평가 종료 후 Facts/Learnings/Behaviors 추출 및 저장                  │
│      │       - 중복 fact 갱신·망각 정책 적용                                       │
│      │                                                                              │
│      ├── async_batch_executor.py / batch_executor.py ─ 배치 실행기                   │
│      │       - 적응형 배치 크기, 재시도, 진행 콜백                                  │
│      │       - Ragas 평가 및 대량 API 호출의 신뢰성 향상                            │
│      │                                                                              │
│      ├── embedding_overlay.py          ─ Phoenix 임베딩 → Domain Memory             │
│      │       - Phoenix 클러스터 export를 Fact triple로 변환                         │
│      │                                                                              │
│      ├── prompt_manifest.py            ─ 프롬프트 거버넌스                          │
│      │       - PromptDiffSummary, manifest I/O                                      │
│      │       - Langfuse/Phoenix prompt 메타데이터 추적                              │
│      │                                                                              │
│      └── experiment_*.*                ─ 실험 저장/통계/리포팅 서비스               │
│              - ExperimentRepository, ExperimentComparator, ExperimentReportGenerator │
│              - MetricComparison, 히스토리 요약                                      │
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

- `domain_config.py`: 도메인 메모리 학습/언어 리소스 경로를 정의하는 Pydantic 모델 (`domains/<name>/memory.yaml` 로딩).
- `agent_types.py`: CLI와 개발용 `agent/` 폴더가 공유하는 `AgentType`, `AgentConfig`, 운영/개발 모드 정의.
- `phoenix_support.py` & `instrumentation.py`: Phoenix/OpenTelemetry 설정, CLI에서 `instrumentation_span` 컨텍스트, 링크 포맷터(`extract_phoenix_links`) 제공.
- `playbooks/`: 개선 패턴 탐지 규칙 템플릿 (`improvement/playbook_loader.py`가 로딩).

---

### 1.2 전체 코드 맵 (디렉터리 → 책임)

| 경로 | 역할 | 주요 구성요소 |
|------|------|---------------|
| `src/evalvault/domain` | 핵심 도메인 엔티티·서비스 | Dataset/Result/Analysis/Memory/Improvement 엔티티, `RagasEvaluator`, `MemoryAwareEvaluator`, `MemoryBasedAnalysis`, `DomainLearningHook`, `PipelineOrchestrator`, `ImprovementGuideService`, `ExperimentManager`, `BenchmarkRunner`, `PromptManifest` 등 |
| `src/evalvault/ports` | 도메인이 외부와 통신하기 위해 정의한 계약 | Inbound 포트(평가, 파이프라인, 웹), Outbound 포트(LLM, Dataset, Storage, Tracker, DomainMemory, Analysis*, Embedding, Korean NLP, Report, Relation Augmenter 등) |
| `src/evalvault/adapters/inbound` | 사용자 인터페이스 계층 | Typer CLI(`commands/run.py`, `commands/gate.py`, `commands/pipeline.py`, `commands/agent.py` 등), FastAPI Web API(`api/routers/*`, `api/adapter.py`) |
| `src/evalvault/adapters/outbound` | 외부 시스템 구현체 | Dataset 로더(정적+스트리밍), LLM/Token-aware Chat, Storage(SQLite/Postgres), Domain Memory(SQLite+FTS5), Tracker(Langfuse/MLflow/Phoenix), Analysis 모듈, Korean NLP, Cache, KG, Report, Improvement, Phoenix Sync |
| `src/evalvault/config` | 실행 설정/계측/에이전트 정의 | `settings.py`, `model_config.py`, `domain_config.py`, `agent_types.py`, `phoenix_support.py`, `instrumentation.py`, `playbooks/` |
| `src/evalvault/reports` | CLI/PR 보고서 템플릿 | `release_notes.py` |
| `src/evalvault/scripts` | 자동화 도구 | `regression_runner.py` (회귀 시나리오 오케스트레이션) |
| `agent/` | 개발자용 하이브리드 에이전트 | `main.py`, `agent.py`, `config.py`, `prompts/`, `memory/`, `security.py` 등 – `evalvault agent …` CLI와 연동 |
| `frontend/` | React Web UI | Vite 기반 프론트엔드(Evaluation Studio/Analysis Lab) |
| `config/` | 모델/도메인 프로필 | `.env`, `models.yaml`, `domains/<name>/memory.yaml`, `playbooks/*.yaml` |
| `data/`, `tests/fixtures/` | 샘플/고정 데이터셋 | e2e JSON, fixture |
| `tests/` | 단위/통합/e2e 테스트 | `tests/unit`, `tests/integration`, `tests/e2e_data` |
| `docs/` | 설계/운영 문서 | ARCHITECTURE, C4, IMPROVEMENT_PLAN 등 |

이 표는 Hexagonal 아키텍처의 각 면이 실제 어디에 놓여 있는지 빠르게 파악할 수 있도록 돕습니다. 아래 섹션에서 세부 내용을 다시 설명합니다.

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

**RAGTraceData 엔티티 (`domain/entities/rag_trace.py`)**

```python
@dataclass
class RAGTraceData:
    trace_id: str = ""
    query: str = ""
    retrieval: RetrievalData | None = None
    generation: GenerationData | None = None
    final_answer: str = ""
    total_time_ms: float = 0.0

    def to_span_attributes(self) -> dict[str, Any]:
        attrs = {"rag.total_time_ms": self.total_time_ms}
        if self.retrieval:
            attrs.update(self.retrieval.to_span_attributes())
        if self.generation:
            attrs.update(self.generation.to_span_attributes())
        return attrs
```

**책임:**
- Phoenix/OpenTelemetry span 속성으로 직렬화하여 검색·생성 단계의 병목을 드러냅니다.
- `RetrievalData`는 Precision@K, 점수 분포, 리랭킹 정보를, `GenerationData`는 토큰/비용, 프롬프트 템플릿, stop reason 등을 추적합니다.
- `config/phoenix_support.instrumentation_span` 또는 tracker 어댑터가 `RAGTraceData`를 이용해 Langfuse/Phoenix에 공통 메타데이터를 남깁니다.

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

**AnalysisService 서비스**

```python
class AnalysisService:
    """분석 서비스.

    여러 분석 어댑터를 조합하여 종합 분석을 제공합니다.
    """

    def __init__(
        self,
        analysis_adapter: AnalysisPort,
        nlp_adapter: NLPAnalysisPort | None = None,
        causal_adapter: CausalAnalysisPort | None = None,
        cache_adapter: AnalysisCachePort | None = None,
    ):
        ...

    def analyze_run(
        self,
        run: EvaluationRun,
        *,
        include_nlp: bool = False,
        include_causal: bool = False,
        use_cache: bool = True,
    ) -> AnalysisBundle:
        """평가 실행에 대한 종합 분석을 수행합니다."""
        ...
```

**책임:**
- 통계 분석 오케스트레이션
- NLP 분석 통합 (선택적)
- 인과 분석 통합 (선택적)
- 분석 결과 캐싱

**의존성:**
- `AnalysisPort`, `NLPAnalysisPort`, `CausalAnalysisPort` (포트 인터페이스)
- `AnalysisCachePort` (캐시 포트)

**PipelineOrchestrator 서비스**

```python
@dataclass
class PipelineOrchestrator:
    """파이프라인 오케스트레이터.

    DAG 기반 분석 파이프라인을 빌드하고 실행합니다.
    """

    module_catalog: ModuleCatalog
    template_registry: PipelineTemplateRegistry
    intent_classifier: KeywordIntentClassifier
    _modules: dict[str, AnalysisModulePort]

    def build_pipeline(
        self,
        intent: AnalysisIntent,
        context: AnalysisContext,
    ) -> AnalysisPipeline:
        """의도와 컨텍스트에 따라 파이프라인 빌드"""
        ...

    async def execute_pipeline(
        self,
        pipeline: AnalysisPipeline,
        context: AnalysisContext,
    ) -> PipelineResult:
        """파이프라인 실행"""
        ...
```

**책임:**
- DAG 기반 분석 파이프라인 구성
- 모듈 카탈로그 관리
- 템플릿 레지스트리 관리
- 의도 분류 및 파이프라인 빌드
- 비동기 파이프라인 실행

**의존성:**
- `AnalysisModulePort` (포트 인터페이스)
- `AnalysisPipeline`, `AnalysisNode` (도메인 엔티티)

**ImprovementGuideService 서비스**

```python
class ImprovementGuideService:
    """개선 가이드 서비스.

    Rule-based Pattern Detector와 LLM-based Insight Generator를
    결합하여 하이브리드 분석을 수행합니다.
    """

    def __init__(
        self,
        pattern_detector: PatternDetectorPort,
        insight_generator: InsightGeneratorPort | None = None,
        playbook: PlaybookPort | None = None,
    ):
        ...

    def generate_report(
        self,
        run: EvaluationRun,
        metrics: list[str] | None = None,
    ) -> ImprovementReport:
        """개선 리포트 생성"""
        ...
```

**책임:**
- 규칙 기반 패턴 탐지
- LLM 기반 인사이트 생성
- 플레이북 기반 액션 제안
- 하이브리드 분석 및 리포트 생성

**의존성:**
- `PatternDetectorPort`, `InsightGeneratorPort`, `PlaybookPort` (포트 인터페이스)

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

**MemoryAwareEvaluator & MemoryBasedAnalysis**

```python
class MemoryAwareEvaluator:
    async def evaluate_with_memory(...):
        reliability = self._memory_port.get_aggregated_reliability(domain=domain, language=language)
        base_thresholds = dict(dataset.thresholds)
        if thresholds:
            base_thresholds.update(thresholds)
        adjusted = self._adjust_by_reliability(metrics, base_thresholds, reliability)
        return await self._evaluator.evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=llm,
            thresholds=adjusted,
            parallel=parallel,
            batch_size=batch_size,
        )
```

- DomainMemory의 신뢰도를 이용해 SLA 임계값을 상향/하향 조정하고, `augment_context_with_facts()`로 질문별 factual context를 주입합니다.
- Phoenix instrumentation(`instrumentation_span`)을 통해 도메인 메모리 검색 비용/레이턴시를 추적합니다.

```python
class MemoryBasedAnalysis:
    def generate_insights(...):
        historical = self.memory_port.list_learnings(...)
        current_metrics = self._extract_metrics(evaluation_run)
        trends = self._analyze_trends(current_metrics, historical)
        related = self.memory_port.hybrid_search(...)
        recommendations = self._generate_recommendations(trends, related.get("facts", []))
        return {"trends": trends, "related_facts": related.get("facts", []), "recommendations": recommendations}
```

- 평가 결과를 메모리 학습치와 비교하여 delta, 추천 작업, 재사용 가능한 행동(Action sequence)을 산출합니다.

**DomainLearningHook**
- Formation 단계에서 Facts/Learnings/Behaviors를 추출하여 중복 제거·망각 지표·신뢰도 갱신 정책을 적용합니다.
- DomainMemoryPort를 통해 저장소를 추상화하므로 SQLite 외 다른 구현으로 쉽게 확장할 수 있습니다.

**AsyncBatchExecutor / BatchExecutor**
- `AsyncBatchExecutor`는 적응형 배치 크기, Rate-limit 대응, 진행 콜백을 제공하여 Ragas 평가, Phoenix 데이터 동기화 등 대규모 API 호출을 안정화합니다.
- Sync 버전(`BatchExecutor`)은 CLI가 멀티스레드 없이 사용할 때 동일한 정책을 제공합니다.

**PromptManifest 유틸리티**

```python
def summarize_prompt_entry(...):
    record = manifest.get("prompts", {}).get(normalized_path)
    current_checksum = _checksum(content)
    if record is None:
        return PromptDiffSummary(path=normalized_path, status="untracked", current_checksum=current_checksum)
    ...
```

- Phoenix prompt manifest를 로딩하고 프롬프트 파일의 변경 사항, Langfuse/실험 ID, 체크섬을 기록합니다.
- CLI `run` 명령은 prompt metadata를 Phoenix/Tracker에 첨부하기 전에 이 유틸리티로 변화 내역을 요약합니다.

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

**AnalysisPipelinePort**

```python
class AnalysisPipelinePort(Protocol):
    """분석 파이프라인 포트 인터페이스."""

    def build_pipeline(
        self,
        intent: AnalysisIntent,
        context: AnalysisContext,
    ) -> AnalysisPipeline:
        """의도와 컨텍스트에 따라 분석 파이프라인을 구성합니다."""
        ...

    async def execute_async(
        self,
        pipeline: AnalysisPipeline,
        context: AnalysisContext,
    ) -> PipelineResult:
        """분석 파이프라인을 비동기로 실행합니다."""
        ...
```

**DomainMemoryPort**

```python
class DomainMemoryPort(Protocol):
    """도메인 메모리 저장소 인터페이스.

    세 가지 메모리 레이어를 관리합니다:
    - Factual Layer: 검증된 도메인 사실 (SPO 트리플)
    - Experiential Layer: 평가에서 학습된 패턴
    - Working Layer: 현재 세션의 활성 컨텍스트
    """

    def save_fact(self, fact: FactualFact) -> str: ...
    def save_learning(self, learning: LearningMemory) -> str: ...
    def save_behavior(self, behavior: BehaviorEntry) -> str: ...
    def hybrid_search(...) -> dict[str, list]: ...
```

**특징:**
- Factual/Experiential/Behavior 레이어 관리
- Formation/Evolution/Retrieval dynamics 지원
- Knowledge Graph 통합 (Phase 5)

**추가 Outbound 포트 요약**

| 포트 | 역할 | 대표 구현 |
|------|------|-----------|
| `AnalysisModulePort` | DAG 노드에 주입되는 분석 모듈 계약 (입력 검증 + sync/async 실행) | `adapters/outbound/analysis/*_module.py` |
| `AnalysisCachePort` | 분석 결과 캐싱 (LRU/TTL, 통계 제공) | `cache/memory_cache.py`, `cache/hybrid_cache.py` |
| `NLPAnalysisPort` / `CausalAnalysisPort` / `AnalysisPort` | 통계·언어·인과 분석 엔진 추상화 | `analysis/statistical_adapter.py`, `analysis/nlp_adapter.py`, `analysis/causal_adapter.py` |
| `KoreanNLPPort` | 한국어 토크나이저/검색기/평가기를 주입 | `nlp/korean/*.py` |
| `EmbeddingPort` | Dense 임베딩 생성 (encode/encode_query) | SentenceTransformers/BGE 어댑터 (향후) |
| `RelationAugmenterPort` | 컨텍스트 내 엔티티 관계 보강 | `llm/llm_relation_augmenter.py` |
| `ReportPort` | Markdown/LLM 기반 리포트 생성 | `report/markdown_adapter.py`, `report/llm_report_generator.py` |
| `IntentClassifierPort` | 분석 의도 분류기 (Keyword, LLM 등) | `domain/services/intent_classifier.KeywordIntentClassifier` |

**ImprovementPort (패턴 탐지 및 인사이트 생성)**

```python
class PatternDetectorPort(Protocol):
    """패턴 탐지 인터페이스."""

    def detect_patterns(
        self,
        run: EvaluationRun,
        metrics: Sequence[str] | None = None,
    ) -> Mapping[str, list[PatternEvidence]]: ...

class InsightGeneratorPort(Protocol):
    """LLM 인사이트 생성 인터페이스."""

    def analyze_batch_failures(
        self,
        failures: Sequence[FailureSample],
        metric_name: str,
        avg_score: float,
        threshold: float,
    ) -> ClaimImprovementProtocol: ...
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

**확장 CLI 명령**
- `commands/run.py`: `RunModePreset(simple/full)`과 Domain Memory/Prompt Manifest/Phoenix dataset sync 옵션을 노출, `StreamingDatasetLoader`를 통한 대규모 데이터셋 처리, Tracker 선택(`langfuse`, `mlflow`, `phoenix`), Phoenix experiment metadata (`build_experiment_metadata`) 삽입.
- `commands/gate.py`, `agent.py`, `domain.py`, `benchmark.py`, `kg.py`, `pipeline.py`, `analyze.py`, `config.py`, `langfuse.py`, `phoenix.py`, `api.py`: 각각 게이트 테스트, 운영/개발 에이전트, 도메인 메모리 bootstrap, Langfuse/phoenix 설정 확인, FastAPI 서버 실행 등을 담당합니다.
- `commands/history.py`, `experiment.py`: StoragePort를 조회하여 run/실험 히스토리를 표 형태로 노출합니다.

**Web API Adapter**
- `api/main.py`와 `api/routers/*`가 FastAPI 엔드포인트를 구성해 React UI와 통신합니다.
- `api/adapter.py`는 Web UI용 WebUIPort 구현체로 평가 실행/저장 흐름을 캡슐화합니다.

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

**StreamingDatasetLoader**

대용량 CSV/JSON/Excel 파일은 `StreamingDatasetLoader`(+`StreamingConfig`)와 `StreamingTestCaseIterator`를 통해 청크 단위로 처리합니다. Iterator는 청크 진행 상황을 외부 콜백으로 내보내고, CLI는 메모리 사용량을 10분의 1 수준으로 유지할 수 있습니다.

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

추가 구현체:
- `token_aware_chat.py`: 토큰 사용량을 기반으로 동적으로 max_tokens를 조절하는 래퍼.
- `instructor_factory.py`: Instructor(OpenAI function calling 호환) 프롬프트를 생성.
- `llm_relation_augmenter.py`: LLM을 이용해 Retrieved context에 관계 설명을 삽입해 Domain Memory와의 결합도를 높입니다.

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

`postgres_adapter.py`는 동일한 `BaseSQLStorageAdapter` 추상화를 공유하며 `postgres_schema.sql`을 로드하여 다중 실행 환경(CI)에서도 동일한 스키마를 유지합니다.

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

Langfuse 외에 `mlflow_adapter.py`(실험/파라미터 기록), `phoenix_adapter.py`(OpenInference 이벤트 전송)도 동일한 `TrackerPort`를 구현하여 CLI 옵션 하나로 추적 대상을 교체할 수 있습니다.

**Web Adapter (FastAPI)**

```python
class WebUIAdapter:
    """웹 UI 어댑터.

    FastAPI 기반 Web API를 제공합니다.
    """

    def run_evaluation(
        self,
        request: EvalRequest,
        *,
        on_progress: Callable[[EvalProgress], None] | None = None,
    ) -> EvaluationRun:
        """웹 UI에서 평가 실행"""
        ...

    def get_run_history(...) -> list[EvaluationRun]: ...
    def generate_llm_report(...) -> str: ...
```

**책임:**
- FastAPI Web API 제공
- 평가 실행 및 진행률 스트리밍
- 결과 조회/리포트 생성 API 제공
- 파일 업로드 및 검증

**Analysis Adapters (통계/NLP/인과 분석)**

```python
class StatisticalAnalysisAdapter(AnalysisPort):
    """통계 분석 어댑터."""

    def analyze_statistics(self, run: EvaluationRun) -> StatisticalResult:
        """통계 분석 수행"""
        ...

class NLPAnalysisAdapter(NLPAnalysisPort):
    """NLP 분석 어댑터."""

    def analyze(self, run: EvaluationRun) -> NLPResult:
        """NLP 분석 수행"""
        ...

class CausalAnalysisAdapter(CausalAnalysisPort):
    """인과 분석 어댑터."""

    def analyze_causality(self, run: EvaluationRun) -> CausalResult:
        """인과 분석 수행"""
        ...
```

**책임:**
- 통계 분석 (평균, 분산, 분포 등)
- NLP 분석 (감성, 주제, 키워드 등)
- 인과 분석 (인과 관계 추론)

**Domain Memory Adapter**

```python
class SQLiteDomainMemoryAdapter(DomainMemoryPort):
    """SQLite 기반 도메인 메모리 어댑터."""

    def save_fact(self, fact: FactualFact) -> str: ...
    def save_learning(self, learning: LearningMemory) -> str: ...
    def save_behavior(self, behavior: BehaviorEntry) -> str: ...
    def hybrid_search(...) -> dict[str, list]: ...
```

**책임:**
- Factual/Experiential/Behavior 레이어 저장
- 메모리 검색 및 통합
- Knowledge Graph 연동

**Improvement Adapters**

```python
class PatternDetector(PatternDetectorPort):
    """규칙 기반 패턴 탐지기."""

    def detect_patterns(
        self,
        run: EvaluationRun,
        metrics: Sequence[str] | None = None,
    ) -> Mapping[str, list[PatternEvidence]]: ...

class InsightGenerator(InsightGeneratorPort):
    """LLM 기반 인사이트 생성기."""

    def analyze_batch_failures(...) -> ClaimImprovementProtocol: ...
```

**책임:**
- 플레이북 기반 패턴 탐지
- LLM 기반 인사이트 생성
- 개선 액션 제안

**Analysis Modules & Cache**
- `adapters/outbound/analysis/*_module.py`는 `AnalysisModulePort`를 구현하여 PipelineOrchestrator가 동적으로 DAG를 구성할 수 있게 합니다. `statistical_analyzer_module.py`, `nlp_analyzer_module.py`, `causal_analyzer_module.py`, `analysis_report_module.py`, `summary_report_module.py`, `comparison_report_module.py`, `verification_report_module.py`, `data_loader_module.py` 등이 존재하며 메타데이터는 `ModuleCatalog`에 등록됩니다.
- `cache/memory_cache.py`는 단순 LRU, `cache/hybrid_cache.py`는 Hot/Cold 2-tier 캐시, Prefetch, TTL 확장, 통계 수집을 제공하여 `AnalysisCachePort` 구현으로 사용됩니다.

**NLP · Retrieval · KG 어댑터**
- `nlp/korean`은 kiwipiepy 기반 토크나이저, BM25/Dense/Hybrid retriever, 평가 툴킷(`korean_evaluation.py`), Document chunker를 제공하며 `KoreanNLPPort`와 `DocumentChunker` 서비스가 사용하는 자원입니다.
- `adapters/outbound/kg`는 `networkx_adapter.py`, `query_strategies.py`로 지식 그래프 생성·탐색을 지원합니다.

**Domain Memory Adapter 심화**
- `domain_memory/sqlite_adapter.py`는 FTS5 인덱스 동기화(`_rebuild_fts_indexes`)와 abstraction level, KG binding, behavior 검색, formation/evolution util을 구현합니다. `DomainLearningHook`과 CLI history 명령이 이 기능을 활용합니다.

**Report & Phoenix**
- `report/llm_report_generator.py`는 메트릭별 전문가 프롬프트 템플릿, 토큰 비용 계산, 비동기 LLM 호출을 제공하여 `ReportPort` 구현체로 사용됩니다. `markdown_adapter.py`는 CLI/README용 요약 텍스트를 생성합니다.
- `adapters/outbound/phoenix/sync_service.py`는 Phoenix dataset/experiment API를 감싸고, CLI `--phoenix-dataset/--phoenix-experiment` 옵션과 `config/phoenix_support.py`가 이 클래스를 호출합니다.

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
    ├─> [6a] Domain Memory 초기화 (--use-domain-memory 옵션)
    │      │  - SQLiteDomainMemoryAdapter 생성
    │      │  - MemoryAwareEvaluator 생성
    │      │  - 신뢰도 점수 조회 및 threshold 자동 조정
    │      │
    │      └─> [6b] MemoryAwareEvaluator (domain/services/memory_aware_evaluator.py)
    │              │  - RagasEvaluator 래핑
    │              │  - DomainMemoryPort 주입
    │              │
    │              └─> [6c] 컨텍스트 보강 (--augment-context 옵션)
    │                      │  - 각 테스트 케이스 질문으로 관련 사실 검색
    │                      │  - 컨텍스트에 사실 추가
    │
    └─> [9] RagasEvaluator 또는 MemoryAwareEvaluator (domain/services/evaluator.py)
            │  - 평가 실행 오케스트레이션
            │  - 메모리 활용 시: 조정된 threshold로 평가
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

### 4.4 분석 파이프라인 흐름 (Analysis Pipeline Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        분석 파이프라인 실행 흐름                                │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 사용자 쿼리 입력
    │  예: "요약해줘", "비교해줘", "검증해줘"
    │
    ▼
[2] CLI/Web Adapter
    │  - 쿼리 파싱
    │
    └─> [3] PipelineOrchestrator
            │
            ├─> [4] IntentClassifier
            │       │  - 키워드 기반 의도 분류
            │       │  - AnalysisIntent 추출
            │       │
            │       └─> [5] AnalysisIntent
            │               (VERIFY, COMPARE, ANALYZE, GENERATE 등)
            │
            ├─> [6] TemplateRegistry
            │       │  - 의도별 템플릿 조회
            │       │
            │       └─> [7] AnalysisPipeline 템플릿
            │               - 노드 및 엣지 정의
            │
            └─> [8] Pipeline 빌드
                    │  - 템플릿 복사
                    │  - 컨텍스트 주입
                    │
                    └─> [9] AnalysisPipeline 엔티티

[10] 파이프라인 실행
     │
     ▼
[11] PipelineOrchestrator.execute_pipeline()
     │  - DAG 토폴로지 정렬
     │  - 의존성 순서대로 실행
     │
     ├─> [12] AnalysisModule 실행
     │       │  - StatisticalAnalysisModule
     │       │  - NLPAnalysisModule
     │       │  - CausalAnalysisModule
     │       │  - ReportModule
     │       │
     │       └─> [13] NodeResult
     │
     └─> [14] PipelineResult
             │  - 모든 노드 결과 집계
             │  - 최종 리포트 생성
```

### 4.5 도메인 메모리 형성 흐름 (Domain Memory Formation Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        도메인 메모리 형성 흐름                                 │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 평가 완료
    │
    ▼
[2] DomainLearningHook.on_evaluation_complete()
    │
    ├─> [3] Factual Layer 형성
    │       │  - 평가 결과에서 SPO 트리플 추출
    │       │  - 높은 신뢰도 사실만 저장
    │       │
    │       └─> [4] DomainMemoryPort.save_fact()
    │               └─> [5] SQLiteDomainMemoryAdapter
    │                       └─> [6] 도메인 메모리 DB
    │
    ├─> [7] Experiential Layer 형성
    │       │  - 성공/실패 패턴 추출
    │       │  - 메트릭별 점수 분포 학습
    │       │
    │       └─> [8] DomainMemoryPort.save_learning()
    │
    └─> [9] Behavior Layer 형성
            │  - 재사용 가능한 행동 패턴 추출
            │  - 성공률 기반 필터링
            │
            └─> [10] DomainMemoryPort.save_behavior()

[11] 메모리 활용
     │  - 향후 평가에서 메모리 검색
     │  - Knowledge Graph 연동
```

### 4.6 도메인 메모리 활용 흐름 (Domain Memory Usage Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        도메인 메모리 활용 흐름                                 │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 평가 시작 (CLI: --use-domain-memory)
    │
    ▼
[2] MemoryAwareEvaluator 초기화
    │  - RagasEvaluator 래핑
    │  - DomainMemoryPort 주입
    │
    ├─> [3] 평가 전: 신뢰도 점수 조회
    │       │
    │       └─> DomainMemoryPort.get_aggregated_reliability()
    │               │  - 과거 평가에서 학습한 메트릭별 신뢰도
    │               │  - 예: {"faithfulness": 0.85, "answer_relevancy": 0.78}
    │               │
    │               └─> [4] Threshold 자동 조정
    │                       │  - 신뢰도 < 0.6: threshold - 0.1 (최소 0.5)
    │                       │  - 신뢰도 > 0.85: threshold + 0.05 (최대 0.95)
    │
    ├─> [5] 컨텍스트 보강 (CLI: --augment-context)
    │       │
    │       └─> MemoryAwareEvaluator.augment_context_with_facts()
    │               │  - 질문으로 관련 사실 검색
    │               │  - DomainMemoryPort.search_facts()
    │               │
    │               └─> [6] 컨텍스트에 사실 추가
    │                       │  - "[관련 사실]\n- 주체 관계 객체"
    │
    └─> [7] 평가 실행
            │
            └─> RagasEvaluator.evaluate()
                    │  - 조정된 threshold로 평가
                    │  - 보강된 컨텍스트 사용
                    │
                    └─> [8] EvaluationRun 결과

[9] 분석 단계 (선택적)
    │
    ▼
[10] MemoryBasedAnalysis.generate_insights()
     │  - 과거 학습 메모리와 현재 결과 비교
     │  - DomainMemoryPort.list_learnings()
     │
     ├─> [11] 트렌드 분석
     │       │  - baseline vs current 비교
     │       │  - delta 계산
     │
     └─> [12] 인사이트 생성
             │  - 관련 사실 검색
             │  - 추천 사항 생성
             │
             └─> [13] Insights 딕셔너리
                     - trends: {"metric": {"current": 0.85, "baseline": 0.82, "delta": 0.03}}
                     - related_facts: [...]
                     - recommendations: ["faithfulness 개선 중: 현재 전략을 유지하거나 확장하세요."]

[14] 행동 패턴 재사용 (선택적)
     │
     └─> MemoryBasedAnalysis.apply_successful_behaviors()
             │  - 질문 컨텍스트로 행동 검색
             │  - DomainMemoryPort.search_behaviors()
             │  - 성공률 >= 0.8인 행동만 필터링
             │
             └─> [15] 재사용 가능한 액션 시퀀스
                     - ["retrieve_contexts", "extract_monetary_value", "generate_response"]
```

### 4.8 개선 가이드 생성 흐름 (Improvement Guide Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        개선 가이드 생성 흐름                                   │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 평가 실행 결과
    │
    ▼
[2] ImprovementGuideService.generate_report()
    │
    ├─> [3] PatternDetector.detect_patterns()
    │       │  - 플레이북 규칙 기반 탐지
    │       │  - 낮은 메트릭 점수 패턴 분석
    │       │
    │       └─> [4] PatternEvidence 리스트
    │
    ├─> [5] InsightGenerator.analyze_batch_failures()
    │       │  - LLM 기반 심층 분석
    │       │  - 실패 샘플 일괄 분석
    │       │
    │       └─> [6] ClaimImprovementProtocol
    │               - 전체 평가
    │               - 우선순위 개선 사항
    │
    └─> [7] ImprovementReport 생성
            │  - 패턴 탐지 결과 통합
            │  - LLM 인사이트 통합
            │  - 액션 우선순위 결정
            │
            └─> [8] ImprovementReport 엔티티
                    - 개선 액션 목록
                    - 예상 개선 효과
                    - 구현 힌트
```

### 4.9 의존성 주입 흐름 (Dependency Injection Flow)

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

### 4.10 관측성 · 추적 흐름 (Observability & Tracing Flow)

EvalVault는 내부 실행뿐 아니라 **외부 RAG 시스템**도 동일한 스키마로 추적할 수 있도록
OpenTelemetry + OpenInference 기반의 **Open RAG Trace 표준**을 제공합니다.
외부 시스템은 `rag.module`을 중심으로 스팬을 생성하고,
`custom.*` 네임스페이스로 표준 외 메타데이터를 보존하며,
로그는 span event로 흡수합니다.

```
[1] CLI --phoenix-enabled / --tracker 옵션
    │
    ▼
[2] config/phoenix_support.ensure_phoenix_instrumentation()
    │  - OpenTelemetry TracerProvider 구성
    │  - LangChain/OpenAI 자동 계측
    │
    └─> instrumentation_span() 컨텍스트 매니저
            │
            ├─> MemoryAwareEvaluator / DatasetLoader / PhoenixSyncService
            │       - Domain Memory 검색, 스트리밍 로딩, Phoenix 업로드에 span 부여
            │
            └─> domain/entities/rag_trace.py
                    - RetrievalData, GenerationData, RAGTraceData 작성

[3] TrackerPort 구현체 (Langfuse / MLflow / Phoenix)
    │  - run 결과를 trace/span/score로 기록
    │  - Prompt manifest diff 정보를 metadata에 포함
    │
    └─> config/phoenix_support.extract_phoenix_links()
            - CLI/Web UI 출력에 Phoenix Trace/Experiment URL 삽입

[4] PhoenixSyncService (옵션)
    │  - Dataset/Experiment 업로드
    │  - Prompt manifest + Phoenix metadata 연동
    │
    └─> Phoenix UI에서 트레이스/실험/데이터셋을 한 번에 탐색

[5] reports/release_notes.py
    │  - 최근 run/분석 요약을 Markdown으로 생성
    │
    └─> README/PR/Slack에 붙일 수 있는 자동 보고서 제공
```

### 4.11 자동화 · 에이전트 흐름 (Automation & Agent Flow)

```
[1] evalvault agent list/info/run
    │
    ▼
[2] config/agent_types.py
    │  - AgentType, AgentConfig, 운영/개발 프로필
    │
    └─> agent/main.py
            │  - claude-agent-sdk 기반 개발용 에이전트 실행
            │  - agent/prompts/*, agent/memory/* 관리

[3] scripts/regression_runner.py
    │  - config/regressions/*.json 로드
    │  - RegressionSuite 정의, subprocess 실행, httpx 호출
    │
    └─> CI/에이전트가 회귀 시나리오를 자동으로 반복
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
- 데이터셋 로더: `CSVDatasetLoader` vs `JSONDatasetLoader` vs `ExcelDatasetLoader`

**예시:**
```python
# Strategy 인터페이스
class BaseDatasetLoader(ABC):
    @abstractmethod
    def load(self, file_path: Path) -> Dataset: ...

    @abstractmethod
    def supports(self, file_path: Path) -> bool: ...

# 전략 구현
class CSVDatasetLoader(BaseDatasetLoader):
    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".csv"

class JSONDatasetLoader(BaseDatasetLoader):
    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".json"
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
settings = Settings()
storage = SQLiteStorageAdapter(db_path=settings.evalvault_db_path)
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

### 7.0 확장 지점 요약

EvalVault는 포트 기반 설계를 따르므로 새로운 통합은 포트 인터페이스를 구현하는 어댑터 형태로 추가됩니다.

**주요 확장 지점**:
- **커스텀 메트릭**: `src/evalvault/domain/metrics/`에 구현하고 `RagasEvaluator`의 매핑 테이블로 등록
- **리트리버**: CLI 옵션으로 `bm25/dense/hybrid/graphrag`를 선택할 수 있으며, 한국어 BM25 등은 outbound NLP 어댑터로 구현
- **트래킹/관측**: `TrackerPort` 기반으로 외부 시스템과 연결되며 CLI에서 Phoenix/Langfuse/MLflow 연동 옵션 제공
- **분석 모듈**: `AnalysisModulePort`를 구현하여 DAG 파이프라인에 추가
- **저장소**: `StoragePort` 또는 `DomainMemoryPort`를 구현하여 새로운 저장소 추가

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

#### 7.1.4 새로운 분석 모듈 추가

**단계:**
1. `AnalysisModulePort` 구현
2. `BaseAnalysisModule` 상속
3. `PipelineOrchestrator`에 등록

**예시:**
```python
# 1. 분석 모듈 구현
class CustomAnalysisModule(BaseAnalysisModule):
    module_id = "custom_analysis"
    name = "Custom Analysis"

    def execute(
        self,
        context: AnalysisContext,
        inputs: dict[str, Any],
    ) -> NodeResult:
        # 분석 로직
        ...

# 2. 오케스트레이터에 등록
orchestrator = PipelineOrchestrator()
orchestrator.register_module(CustomAnalysisModule())
```

#### 7.1.5 새로운 분석 의도 추가

**단계:**
1. `AnalysisIntent` enum에 추가
2. 템플릿 정의
3. `PipelineTemplateRegistry`에 등록

**예시:**
```python
# 1. 의도 추가
class AnalysisIntent(str, Enum):
    CUSTOM_ANALYSIS = "custom_analysis"  # 새 의도

# 2. 템플릿 정의
template = AnalysisPipeline(
    intent=AnalysisIntent.CUSTOM_ANALYSIS,
    nodes=[...],
    edges=[...],
)

# 3. 레지스트리에 등록
registry = PipelineTemplateRegistry()
registry.register_template(template)
```

#### 7.1.6 새로운 저장소 추가

**단계:**
1. `StoragePort` 또는 `DomainMemoryPort` 구현
2. 어댑터 클래스 생성
3. Factory에 등록

**예시:**
```python
# 1. 저장소 어댑터 구현
class MongoDBStorageAdapter(StoragePort):
    def save_run(self, run: EvaluationRun) -> str:
        # MongoDB 저장 로직
        ...

# 2. Factory에 등록
def get_storage_adapter(settings: Settings) -> StoragePort:
    if settings.storage_type == "mongodb":
        return MongoDBStorageAdapter(settings)
    # ...
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
6. **모듈성**: DAG 기반 분석 파이프라인으로 복잡한 분석 워크플로우 구성 가능
7. **학습 능력**: 도메인 메모리 시스템으로 평가 결과에서 지속적으로 학습
8. **개선 가이드**: 규칙 기반 및 LLM 기반 하이브리드 분석으로 실질적인 개선 제안

### 8.2 아키텍처 원칙 요약

- **의존성 규칙**: 의존성은 항상 외부 → 내부 방향
- **포트와 어댑터**: 도메인은 포트를 통해 외부와 통신
- **도메인 중심**: 핵심 비즈니스 로직은 도메인 계층에 집중
- **인터페이스 분리**: 각 포트는 단일 책임을 가짐
- **의존성 주입**: 구체적인 구현이 아닌 인터페이스에 의존
- **템플릿 기반 구성**: 분석 파이프라인을 템플릿으로 재사용 가능하게 구성
- **메모리 기반 학습**: 평가 결과를 도메인 메모리로 저장하여 지속적 학습

### 8.3 현재 아키텍처의 주요 특징

#### 8.3.1 다층 분석 시스템
- **통계 분석**: 기본적인 통계 지표 계산
- **NLP 분석**: 자연어 처리 기반 심층 분석
- **인과 분석**: 인과 관계 추론 및 원인 분석
- **메타 분석**: 여러 실행 결과 비교 및 종합 분석

#### 8.3.2 DAG 기반 파이프라인
- **의도 분류**: 사용자 쿼리에서 분석 의도 자동 추출
- **템플릿 기반**: 의도별 미리 정의된 파이프라인 템플릿
- **모듈화**: 각 분석 단계를 독립적인 모듈로 구성
- **비동기 실행**: 의존성 순서에 따른 효율적인 실행

#### 8.3.3 도메인 메모리 시스템
- **Factual Layer**: 검증된 도메인 사실 저장 (SPO 트리플)
- **Experiential Layer**: 평가에서 학습된 패턴 저장
- **Behavior Layer**: 재사용 가능한 행동 패턴 저장
- **Formation/Evolution/Retrieval**: 메모리 형성, 진화, 검색 dynamics

#### 8.3.4 개선 가이드 시스템
- **규칙 기반 탐지**: 플레이북 기반 빠른 패턴 탐지
- **LLM 기반 분석**: 심층적인 인사이트 생성
- **하이브리드 분석**: 두 방법을 결합한 종합 리포트
- **액션 우선순위**: 개선 효과와 구현 난이도 기반 우선순위 결정

이 아키텍처는 소프트웨어의 복잡성을 관리하고, 변경에 유연하게 대응하며, 장기적인 유지보수를 용이하게 합니다. 특히 분석 파이프라인과 도메인 메모리 시스템을 통해 RAG 평가의 지속적인 개선을 지원합니다.

---

## 8. 구조 파악 방법론 요약

프로젝트 구조를 빠르게 이해하기 위한 여러 방법론이 있습니다:

| 방법론 | 핵심 질문 | 산출물 |
|--------|-----------|--------|
| 폴더 지형도 + 책임 태깅 | "폴더가 무엇을 책임지나?" | 디렉터리 맵 |
| 헥사고날 레이어 맵 | "도메인/포트/어댑터 관계는?" | 레이어 다이어그램 |
| 엔트리포인트 흐름 추적 | "실행 시 어디를 거치나?" | 시퀀스/플로우 |
| C4/컴포넌트 관점 | "큰 덩어리와 경계는?" | 컨테이너/컴포넌트 맵 |
| 모듈 의존성 그래프 | "결합이 어디에 몰려 있나?" | 의존성 그래프 |
| 데이터/설정 플로우 | "입력/설정이 어떻게 흘러가나?" | 데이터 플로우 |
| 테스트 기반 기능 지도 | "테스트가 말하는 핵심 기능은?" | 테스트-모듈 매핑 |

**주요 실행 플로우**:
- **CLI**: `run`, `pipeline`, `domain`, `benchmark`, `stage` 등 주요 실행 흐름 제공
- **평가 입력**: JSON/CSV/XLSX 데이터셋을 받아 테스트 케이스 단위로 변환
- **평가 실행**: Ragas 기반 메트릭과 커스텀 메트릭을 계산해 `EvaluationRun`으로 집계
- **Domain Memory**: `--use-domain-memory` 옵션으로 활성화되며 threshold 조정과 컨텍스트 보강
- **분석 파이프라인**: 사용자 쿼리에서 의도를 분류하고 DAG 파이프라인을 구성

**설정/프로파일/환경 변수**:
- 모델 프로필: `config/models.yaml`에 정의 (dev/prod/openai 등)
- `Settings`: `.env`를 기본으로 읽고 API 키, 엔드포인트, 트래커 설정 관리
- `EVALVAULT_PROFILE`: 프로필 선택을 런타임에 노출
- `pyproject.toml`: optional-dependencies로 기능 단위 설치 구성 제공

자세한 방법론은 `docs/guides/structure-methods/` 폴더의 개별 문서를 참고하세요.

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
