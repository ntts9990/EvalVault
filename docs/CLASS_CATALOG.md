# EvalVault 클래스 카탈로그

> **헥사고날 아키텍처 & 클린 아키텍처 & DDD & TDD & YAGNI & SOLID 원칙 기반 클래스 분류**

이 문서는 EvalVault 프로젝트의 모든 클래스를 체계적으로 분류하고 정리한 카탈로그입니다. 각 클래스의 역할, 책임, 그리고 아키텍처 관점에서의 위치를 명확히 정의합니다.

---

## 목차

1. [분류 체계](#1-분류-체계)
2. [헥사고날 아키텍처 관점 분류](#2-헥사고날-아키텍처-관점-분류)
3. [클린 아키텍처 관점 분류](#3-클린-아키텍처-관점-분류)
4. [DDD 관점 분류](#4-ddd-관점-분류)
5. [역할별 분류](#5-역할별-분류)
6. [프로세스 순서별 분류](#6-프로세스-순서별-분류)
7. [클래스 상세 목록](#7-클래스-상세-목록)

---

## 1. 분류 체계

EvalVault는 다음 아키텍처 원칙을 따릅니다:

- **헥사고날 아키텍처 (Ports & Adapters)**: 도메인을 외부 의존성으로부터 격리
- **클린 아키텍처**: 계층별 의존성 규칙 준수
- **DDD (Domain-Driven Design)**: 도메인 중심 설계
- **SOLID 원칙**: 단일 책임, 개방-폐쇄, 리스코프 치환, 인터페이스 분리, 의존성 역전
- **YAGNI (You Aren't Gonna Need It)**: 필요한 것만 구현
- **TDD (Test-Driven Development)**: 테스트 주도 개발

각 클래스는 다음 기준으로 분류됩니다:
1. **역할**: 클래스가 수행하는 책임
2. **프로세스 순서**: 실행 흐름상의 위치
3. **아키텍처 관점**: 헥사고날/클린/DDD 관점에서의 위치

---

## 2. 헥사고날 아키텍처 관점 분류

헥사고날 아키텍처는 **도메인(Domain)**, **포트(Ports)**, **어댑터(Adapters)** 세 계층으로 구성됩니다.

### 2.1 Domain Layer (도메인 계층)

도메인 계층은 비즈니스 로직의 핵심이며, 외부 의존성이 없는 순수한 도메인 모델과 서비스를 포함합니다.

#### 2.1.1 Domain Entities (도메인 엔티티)

**위치**: `src/evalvault/domain/entities/`

**역할**: 비즈니스 도메인의 핵심 개념을 표현하는 불변 데이터 모델

| 클래스명 | 파일 | 역할 | DDD 분류 |
|---------|------|------|----------|
| `TestCase` | `dataset.py` | 평가 테스트 케이스 (질문, 답변, 컨텍스트) | Entity |
| `Dataset` | `dataset.py` | 테스트 케이스 집합 | Aggregate Root |
| `EvaluationRun` | `result.py` | 평가 실행 결과 집계 | Aggregate Root |
| `MetricScore` | `result.py` | 메트릭 점수 (메트릭 타입, 점수, 설명) | Value Object |
| `TestCaseResult` | `result.py` | 개별 테스트 케이스 평가 결과 | Entity |
| `MetricType` | `result.py` | 메트릭 타입 열거형 | Value Object |
| `AnalysisResult` | `analysis.py` | 분석 결과 기본 클래스 | Entity |
| `StatisticalAnalysis` | `analysis.py` | 통계 분석 결과 | Entity |
| `MetaAnalysisResult` | `analysis.py` | 메타 분석 결과 | Entity |
| `AnalysisBundle` | `analysis.py` | 여러 분석 결과 묶음 | Aggregate |
| `ComparisonResult` | `analysis.py` | 비교 분석 결과 | Entity |
| `CorrelationInsight` | `analysis.py` | 상관관계 인사이트 | Value Object |
| `LowPerformerInfo` | `analysis.py` | 저성능 케이스 정보 | Value Object |
| `MetricStats` | `analysis.py` | 메트릭 통계 | Value Object |
| `EffectSizeLevel` | `analysis.py` | 효과 크기 수준 | Value Object |
| `AnalysisType` | `analysis.py` | 분석 타입 열거형 | Value Object |
| `QuestionType` | `analysis.py` | 질문 타입 열거형 | Value Object |
| `TextStats` | `analysis.py` | 텍스트 통계 | Value Object |
| `QuestionTypeStats` | `analysis.py` | 질문 타입별 통계 | Value Object |
| `KeywordInfo` | `analysis.py` | 키워드 정보 | Value Object |
| `TopicCluster` | `analysis.py` | 토픽 클러스터 | Value Object |
| `NLPAnalysis` | `analysis.py` | NLP 분석 결과 | Entity |
| `CausalAnalysis` | `analysis.py` | 인과 분석 결과 | Entity |
| `CausalFactorType` | `analysis.py` | 인과 요인 타입 | Value Object |
| `ImpactDirection` | `analysis.py` | 영향 방향 | Value Object |
| `ImpactStrength` | `analysis.py` | 영향 강도 | Value Object |
| `FactorStats` | `analysis.py` | 요인 통계 | Value Object |
| `StratifiedGroup` | `analysis.py` | 계층화 그룹 | Value Object |
| `FactorImpact` | `analysis.py` | 요인 영향 | Value Object |
| `CausalRelationship` | `analysis.py` | 인과 관계 | Value Object |
| `RootCause` | `analysis.py` | 근본 원인 | Value Object |
| `InterventionSuggestion` | `analysis.py` | 개입 제안 | Value Object |
| `Experiment` | `experiment.py` | 실험 설정 및 결과 | Aggregate Root |
| `ExperimentGroup` | `experiment.py` | 실험 그룹 | Entity |
| `ImprovementReport` | `improvement.py` | 개선 보고서 | Aggregate Root |
| `RAGImprovementGuide` | `improvement.py` | RAG 개선 가이드 | Entity |
| `ImprovementAction` | `improvement.py` | 개선 액션 | Entity |
| `ImprovementEvidence` | `improvement.py` | 개선 근거 | Value Object |
| `PatternEvidence` | `improvement.py` | 패턴 근거 | Value Object |
| `FailureSample` | `improvement.py` | 실패 샘플 | Value Object |
| `RAGComponent` | `improvement.py` | RAG 컴포넌트 열거형 | Value Object |
| `PatternType` | `improvement.py` | 패턴 타입 열거형 | Value Object |
| `ImprovementPriority` | `improvement.py` | 개선 우선순위 열거형 | Value Object |
| `EffortLevel` | `improvement.py` | 노력 수준 열거형 | Value Object |
| `EvidenceSource` | `improvement.py` | 근거 출처 열거형 | Value Object |
| `EntityModel` | `kg.py` | 지식 그래프 엔티티 모델 | Entity |
| `RelationModel` | `kg.py` | 지식 그래프 관계 모델 | Entity |
| `FactualFact` | `memory.py` | 검증된 도메인 사실 (SPO 트리플) | Entity |
| `LearningMemory` | `memory.py` | 학습 메모리 (패턴, 신뢰도) | Entity |
| `DomainMemoryContext` | `memory.py` | 워킹 메모리 컨텍스트 | Value Object |
| `BehaviorEntry` | `memory.py` | 행동 패턴 엔트리 | Entity |
| `BehaviorHandbook` | `memory.py` | 행동 핸드북 | Aggregate |
| `AnalysisIntent` | `analysis_pipeline.py` | 분석 의도 열거형 | Value Object |
| `AnalysisIntentCategory` | `analysis_pipeline.py` | 분석 의도 카테고리 | Value Object |
| `NodeExecutionStatus` | `analysis_pipeline.py` | 노드 실행 상태 | Value Object |
| `AnalysisNode` | `analysis_pipeline.py` | 분석 파이프라인 노드 | Entity |
| `AnalysisContext` | `analysis_pipeline.py` | 분석 컨텍스트 | Value Object |
| `AnalysisPipeline` | `analysis_pipeline.py` | 분석 파이프라인 DAG | Aggregate Root |
| `NodeResult` | `analysis_pipeline.py` | 노드 실행 결과 | Value Object |
| `PipelineResult` | `analysis_pipeline.py` | 파이프라인 실행 결과 | Aggregate |
| `ModuleMetadata` | `analysis_pipeline.py` | 모듈 메타데이터 | Value Object |
| `ModuleCatalog` | `analysis_pipeline.py` | 모듈 카탈로그 | Aggregate |
| `TaskType` | `benchmark.py` | 벤치마크 태스크 타입 | Value Object |
| `RAGTestCase` | `benchmark.py` | RAG 테스트 케이스 | Entity |
| `RAGTestCaseResult` | `benchmark.py` | RAG 테스트 케이스 결과 | Entity |
| `SplitScores` | `benchmark.py` | 분할 점수 | Value Object |
| `BenchmarkResult` | `benchmark.py` | 벤치마크 결과 | Aggregate |
| `BenchmarkSuite` | `benchmark.py` | 벤치마크 스위트 | Aggregate Root |
| `BenchmarkConfig` | `benchmark.py` | 벤치마크 설정 | Value Object |

#### 2.1.2 Domain Services (도메인 서비스)

**위치**: `src/evalvault/domain/services/`

**역할**: 여러 엔티티에 걸친 비즈니스 로직을 처리하는 서비스

| 클래스명 | 파일 | 역할 | 책임 |
|---------|------|------|------|
| `RagasEvaluator` | `evaluator.py` | RAG 평가 실행 | 테스트 케이스 평가, 메트릭 계산 |
| `AnalysisService` | `analysis_service.py` | 분석 서비스 | 통계/NLP/인과 분석 오케스트레이션 |
| `ImprovementGuideService` | `improvement_guide_service.py` | 개선 가이드 생성 | 패턴 탐지, 인사이트 생성, 가이드 생성 |
| `DomainLearningHook` | `domain_learning_hook.py` | 도메인 학습 훅 | 평가 결과에서 도메인 지식 추출 |
| `PipelineOrchestrator` | `pipeline_orchestrator.py` | 파이프라인 오케스트레이터 | DAG 기반 분석 파이프라인 실행 |
| `AnalysisPipelineService` | `pipeline_orchestrator.py` | 분석 파이프라인 서비스 | 파이프라인 빌드 및 실행 |
| `PipelineTemplateRegistry` | `pipeline_template_registry.py` | 파이프라인 템플릿 레지스트리 | 템플릿 등록 및 조회 |
| `IntentClassifier` | `intent_classifier.py` | 의도 분류기 | 사용자 쿼리에서 분석 의도 추출 |
| `KeywordIntentClassifier` | `intent_classifier.py` | 키워드 기반 의도 분류기 | 키워드 매칭으로 의도 분류 |
| `IntentKeywordRegistry` | `intent_classifier.py` | 의도 키워드 레지스트리 | 의도-키워드 매핑 관리 |
| `KnowledgeGraphGenerator` | `kg_generator.py` | 지식 그래프 생성기 | 문서에서 KG 생성 |
| `KnowledgeGraph` | `kg_generator.py` | 지식 그래프 | 엔티티-관계 그래프 표현 |
| `EntityExtractor` | `entity_extractor.py` | 엔티티 추출기 | 텍스트에서 엔티티/관계 추출 |
| `Entity` | `entity_extractor.py` | 엔티티 데이터 모델 | 추출된 엔티티 표현 |
| `Relation` | `entity_extractor.py` | 관계 데이터 모델 | 추출된 관계 표현 |
| `ExperimentManager` | `experiment_manager.py` | 실험 관리자 | 실험 실행 및 비교 |
| `MetricComparison` | `experiment_manager.py` | 메트릭 비교 | 실험 간 메트릭 비교 |
| `BenchmarkRunner` | `benchmark_runner.py` | 벤치마크 실행기 | 벤치마크 실행 및 비교 |
| `BenchmarkComparison` | `benchmark_runner.py` | 벤치마크 비교 | 벤치마크 결과 비교 |
| `KoreanRAGBenchmarkRunner` | `benchmark_runner.py` | 한국어 RAG 벤치마크 실행기 | 한국어 특화 벤치마크 |
| `TestsetGenerator` | `testset_generator.py` | 테스트셋 생성기 | 합성 테스트 케이스 생성 |
| `BasicTestsetGenerator` | `testset_generator.py` | 기본 테스트셋 생성기 | 기본 생성 로직 |
| `GenerationConfig` | `testset_generator.py` | 생성 설정 | 테스트셋 생성 설정 |
| `DocumentChunker` | `document_chunker.py` | 문서 청킹 서비스 | 문서를 청크로 분할 |
| `TestCaseEvalResult` | `evaluator.py` | 테스트 케이스 평가 결과 | 개별 평가 결과 데이터 |

### 2.2 Ports Layer (포트 계층)

포트 계층은 도메인과 외부 세계 사이의 계약(Contract)을 정의합니다.

#### 2.2.1 Inbound Ports (입력 포트)

**위치**: `src/evalvault/ports/inbound/`

**역할**: 도메인이 제공하는 기능을 외부에 노출하는 인터페이스

| 클래스명 | 파일 | 역할 | 구현체 |
|---------|------|------|--------|
| `EvaluatorPort` | `evaluator_port.py` | 평가 실행 인터페이스 | `RagasEvaluator` |
| `AnalysisPipelinePort` | `analysis_pipeline_port.py` | 분석 파이프라인 인터페이스 | `AnalysisPipelineService` |
| `DomainLearningHookPort` | `learning_hook_port.py` | 도메인 학습 훅 인터페이스 | `DomainLearningHook` |
| `WebUIPort` | `web_port.py` | 웹 UI 인터페이스 | `WebUIAdapter` |
| `EvalRequest` | `web_port.py` | 평가 요청 데이터 모델 | - |
| `EvalProgress` | `web_port.py` | 평가 진행 상황 데이터 모델 | - |
| `RunSummary` | `web_port.py` | 실행 요약 데이터 모델 | - |
| `RunFilters` | `web_port.py` | 실행 필터 데이터 모델 | - |

#### 2.2.2 Outbound Ports (출력 포트)

**위치**: `src/evalvault/ports/outbound/`

**역할**: 도메인이 필요로 하는 외부 서비스를 정의하는 인터페이스

| 클래스명 | 파일 | 역할 | 구현 어댑터 |
|---------|------|------|------------|
| `DatasetPort` | `dataset_port.py` | 데이터셋 로딩 인터페이스 | `JSONDatasetLoader`, `CSVDatasetLoader`, `ExcelDatasetLoader` |
| `LLMPort` | `llm_port.py` | LLM 인터페이스 | `OpenAIAdapter`, `AnthropicAdapter`, `OllamaAdapter`, `AzureOpenAIAdapter` |
| `StoragePort` | `storage_port.py` | 저장소 인터페이스 | `SQLiteStorageAdapter`, `PostgreSQLStorageAdapter` |
| `TrackerPort` | `tracker_port.py` | 추적 인터페이스 | `LangfuseAdapter`, `MLflowAdapter` |
| `AnalysisPort` | `analysis_port.py` | 분석 인터페이스 | `StatisticalAnalysisAdapter`, `NLPAnalysisAdapter`, `CausalAnalysisAdapter` |
| `AnalysisModulePort` | `analysis_module_port.py` | 분석 모듈 인터페이스 | `BaseAnalysisModule` 구현체들 |
| `AnalysisCachePort` | `analysis_cache_port.py` | 분석 캐시 인터페이스 | `MemoryCacheAdapter` |
| `NLPAnalysisPort` | `nlp_analysis_port.py` | NLP 분석 인터페이스 | `NLPAnalysisAdapter` |
| `CausalAnalysisPort` | `causal_analysis_port.py` | 인과 분석 인터페이스 | `CausalAnalysisAdapter` |
| `ReportPort` | `report_port.py` | 보고서 생성 인터페이스 | `LLMReportGenerator`, `MarkdownReportAdapter` |
| `EmbeddingPort` | `embedding_port.py` | 임베딩 인터페이스 | LLM 어댑터 내부 구현 |
| `EmbeddingResult` | `embedding_port.py` | 임베딩 결과 데이터 모델 | - |
| `DomainMemoryPort` | `domain_memory_port.py` | 도메인 메모리 인터페이스 | `SQLiteDomainMemoryAdapter` |
| `ImprovementPort` | `improvement_port.py` | 개선 관련 인터페이스들 | `PatternDetector`, `InsightGenerator`, `PlaybookLoader` |
| `PatternDetectorPort` | `improvement_port.py` | 패턴 탐지 인터페이스 | `PatternDetector` |
| `InsightGeneratorPort` | `improvement_port.py` | 인사이트 생성 인터페이스 | `InsightGenerator` |
| `PlaybookPort` | `improvement_port.py` | 플레이북 인터페이스 | `PlaybookLoader` |
| `ActionDefinitionProtocol` | `improvement_port.py` | 액션 정의 프로토콜 | `ActionDefinition` |
| `PatternDefinitionProtocol` | `improvement_port.py` | 패턴 정의 프로토콜 | `PatternDefinition` |
| `MetricPlaybookProtocol` | `improvement_port.py` | 메트릭 플레이북 프로토콜 | `MetricPlaybook` |
| `ClaimImprovementProtocol` | `improvement_port.py` | 클레임 개선 프로토콜 | - |
| `KoreanNLPToolkitPort` | `korean_nlp_port.py` | 한국어 NLP 툴킷 인터페이스 | `KoreanNLPToolkit` |
| `RetrieverPort` | `korean_nlp_port.py` | 검색기 인터페이스 | `KoreanBM25Retriever`, `KoreanDenseRetriever`, `KoreanHybridRetriever` |
| `RetrieverResultProtocol` | `korean_nlp_port.py` | 검색 결과 프로토콜 | `RetrievalResult`, `DenseRetrievalResult`, `HybridResult` |
| `FaithfulnessResultProtocol` | `korean_nlp_port.py` | 신뢰성 결과 프로토콜 | `FaithfulnessResult` |
| `FaithfulnessClaimResultProtocol` | `korean_nlp_port.py` | 신뢰성 클레임 결과 프로토콜 | `ClaimVerification` |
| `RelationAugmenterPort` | `relation_augmenter_port.py` | 관계 보강 인터페이스 | `LLMRelationAugmenter` |
| `IntentClassifierPort` | `intent_classifier_port.py` | 의도 분류기 인터페이스 | `KeywordIntentClassifier` |
| `IntentClassificationResult` | `intent_classifier_port.py` | 의도 분류 결과 데이터 모델 | - |
| `ThinkingConfig` | `llm_port.py` | 사고 설정 데이터 모델 | - |

### 2.3 Adapters Layer (어댑터 계층)

어댑터 계층은 외부 시스템과 도메인 사이의 변환을 담당합니다.

#### 2.3.1 Inbound Adapters (입력 어댑터)

**위치**: `src/evalvault/adapters/inbound/`

**역할**: 외부에서 들어오는 요청을 도메인 서비스로 변환

##### CLI Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| CLI 명령어들 | `cli/commands/*.py` | Typer 기반 CLI 명령어 구현 |

##### Web Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| `WebUIAdapter` | `web/adapter.py` | Streamlit 기반 웹 UI 어댑터 |
| `GateResult` | `web/adapter.py` | 게이트 결과 데이터 모델 |
| `GateReport` | `web/adapter.py` | 게이트 보고서 데이터 모델 |
| `WebSession` | `web/session.py` | 웹 세션 데이터 모델 |
| `EvaluationConfig` | `web/components/evaluate.py` | 평가 설정 데이터 모델 |
| `EvaluationResult` | `web/components/evaluate.py` | 평가 결과 데이터 모델 |
| `EvaluationProgress` | `web/components/progress.py` | 평가 진행 상황 데이터 모델 |
| `ProgressStep` | `web/components/progress.py` | 진행 단계 데이터 모델 |
| `DashboardStats` | `web/components/stats.py` | 대시보드 통계 데이터 모델 |
| `MetricSummaryCard` | `web/components/cards.py` | 메트릭 요약 카드 데이터 모델 |
| `StatCard` | `web/components/cards.py` | 통계 카드 데이터 모델 |
| `RecentRunsList` | `web/components/lists.py` | 최근 실행 목록 데이터 모델 |
| `RunFilter` | `web/components/history.py` | 실행 필터 데이터 모델 |
| `RunTable` | `web/components/history.py` | 실행 테이블 데이터 모델 |
| `RunDetailPanel` | `web/components/history.py` | 실행 상세 패널 데이터 모델 |
| `HistoryExporter` | `web/components/history.py` | 히스토리 내보내기 데이터 모델 |
| `RunSearch` | `web/components/history.py` | 실행 검색 데이터 모델 |
| `FileUploadHandler` | `web/components/upload.py` | 파일 업로드 핸들러 |
| `ValidationResult` | `web/components/upload.py` | 검증 결과 데이터 모델 |
| `MetricSelector` | `web/components/metrics.py` | 메트릭 선택기 |
| `ReportConfig` | `web/components/reports.py` | 보고서 설정 데이터 모델 |
| `ReportResult` | `web/components/reports.py` | 보고서 결과 데이터 모델 |
| `ReportTemplate` | `web/components/reports.py` | 보고서 템플릿 데이터 모델 |
| `ReportGenerator` | `web/components/reports.py` | 보고서 생성기 |
| `ReportDownloader` | `web/components/reports.py` | 보고서 다운로더 |
| `RunSelector` | `web/components/reports.py` | 실행 선택기 |
| `ReportPreview` | `web/components/reports.py` | 보고서 미리보기 |

#### 2.3.2 Outbound Adapters (출력 어댑터)

**위치**: `src/evalvault/adapters/outbound/`

**역할**: 도메인이 필요로 하는 외부 서비스를 제공

##### Dataset Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| `BaseDatasetLoader` | `dataset/base.py` | 데이터셋 로더 기본 클래스 |
| `JSONDatasetLoader` | `dataset/json_loader.py` | JSON 데이터셋 로더 |
| `CSVDatasetLoader` | `dataset/csv_loader.py` | CSV 데이터셋 로더 |
| `ExcelDatasetLoader` | `dataset/excel_loader.py` | Excel 데이터셋 로더 |

##### LLM Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| `BaseLLMAdapter` | `llm/base.py` | LLM 어댑터 기본 클래스 |
| `OpenAIAdapter` | `llm/openai_adapter.py` | OpenAI API 어댑터 |
| `AnthropicAdapter` | `llm/anthropic_adapter.py` | Anthropic API 어댑터 |
| `OllamaAdapter` | `llm/ollama_adapter.py` | Ollama API 어댑터 |
| `AzureOpenAIAdapter` | `llm/azure_adapter.py` | Azure OpenAI API 어댑터 |
| `LLMRelationAugmenter` | `llm/llm_relation_augmenter.py` | LLM 기반 관계 보강기 |
| `TokenTrackingAsyncOpenAI` | `llm/openai_adapter.py` | 토큰 추적 OpenAI 래퍼 |
| `ThinkingTokenTrackingAsyncOpenAI` | `llm/token_aware_chat.py` | Ollama용 토큰 추적 OpenAI 클라이언트 |
| `ThinkingTokenTrackingAsyncAnthropic` | `llm/anthropic_adapter.py` | 사고 토큰 추적 Anthropic 래퍼 |
| `TokenUsage` | `llm/base.py` | 토큰 사용량 데이터 모델 |
| `LLMConfigurationError` | `llm/base.py` | LLM 설정 오류 예외 |

##### Storage Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| `BaseSQLStorageAdapter` | `storage/base_sql.py` | SQL 저장소 기본 클래스 |
| `SQLiteStorageAdapter` | `storage/sqlite_adapter.py` | SQLite 저장소 어댑터 |
| `PostgreSQLStorageAdapter` | `storage/postgres_adapter.py` | PostgreSQL 저장소 어댑터 |
| `SQLQueries` | `storage/base_sql.py` | SQL 쿼리 유틸리티 |

##### Tracker Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| `LangfuseAdapter` | `tracker/langfuse_adapter.py` | Langfuse 추적 어댑터 |
| `MLflowAdapter` | `tracker/mlflow_adapter.py` | MLflow 추적 어댑터 |

##### Analysis Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| `BaseAnalysisAdapter` | `analysis/common.py` | 분석 어댑터 기본 클래스 |
| `StatisticalAnalysisAdapter` | `analysis/statistical_adapter.py` | 통계 분석 어댑터 |
| `NLPAnalysisAdapter` | `analysis/nlp_adapter.py` | NLP 분석 어댑터 |
| `CausalAnalysisAdapter` | `analysis/causal_adapter.py` | 인과 분석 어댑터 |
| `AnalysisDataProcessor` | `analysis/common.py` | 분석 데이터 프로세서 |
| `BaseAnalysisModule` | `analysis/base_module.py` | 분석 모듈 기본 클래스 |
| `DataLoaderModule` | `analysis/data_loader_module.py` | 데이터 로더 모듈 |
| `StatisticalAnalyzerModule` | `analysis/statistical_analyzer_module.py` | 통계 분석 모듈 |
| `NLPAnalyzerModule` | `analysis/nlp_analyzer_module.py` | NLP 분석 모듈 |
| `CausalAnalyzerModule` | `analysis/causal_analyzer_module.py` | 인과 분석 모듈 |
| `SummaryReportModule` | `analysis/summary_report_module.py` | 요약 보고서 모듈 |
| `VerificationReportModule` | `analysis/verification_report_module.py` | 검증 보고서 모듈 |
| `ComparisonReportModule` | `analysis/comparison_report_module.py` | 비교 보고서 모듈 |
| `AnalysisReportModule` | `analysis/analysis_report_module.py` | 분석 보고서 모듈 |

##### Report Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| `LLMReportGenerator` | `report/llm_report_generator.py` | LLM 기반 보고서 생성기 |
| `MarkdownReportAdapter` | `report/markdown_adapter.py` | Markdown 보고서 어댑터 |
| `LLMReport` | `report/llm_report_generator.py` | LLM 보고서 데이터 모델 |
| `LLMReportSection` | `report/llm_report_generator.py` | LLM 보고서 섹션 데이터 모델 |

##### Improvement Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| `PatternDetector` | `improvement/pattern_detector.py` | 패턴 탐지기 |
| `InsightGenerator` | `improvement/insight_generator.py` | 인사이트 생성기 |
| `PlaybookLoader` | `improvement/playbook_loader.py` | 플레이북 로더 |
| `FeatureVector` | `improvement/pattern_detector.py` | 특징 벡터 데이터 모델 |
| `LLMInsight` | `improvement/insight_generator.py` | LLM 인사이트 데이터 모델 |
| `BatchPatternInsight` | `improvement/insight_generator.py` | 배치 패턴 인사이트 데이터 모델 |
| `DetectionRule` | `improvement/playbook_loader.py` | 탐지 규칙 데이터 모델 |
| `ActionDefinition` | `improvement/playbook_loader.py` | 액션 정의 데이터 모델 |
| `PatternDefinition` | `improvement/playbook_loader.py` | 패턴 정의 데이터 모델 |
| `MetricPlaybook` | `improvement/playbook_loader.py` | 메트릭 플레이북 데이터 모델 |
| `Playbook` | `improvement/playbook_loader.py` | 플레이북 데이터 모델 |

##### Korean NLP Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| `KoreanNLPToolkit` | `nlp/korean/toolkit.py` | 한국어 NLP 툴킷 |
| `_RetrieverWrapper` | `nlp/korean/toolkit.py` | 검색기 래퍼 |
| `KiwiTokenizer` | `nlp/korean/kiwi_tokenizer.py` | Kiwi 형태소 분석기 |
| `Token` | `nlp/korean/kiwi_tokenizer.py` | 토큰 데이터 모델 |
| `KoreanBM25Retriever` | `nlp/korean/bm25_retriever.py` | BM25 검색기 |
| `RetrievalResult` | `nlp/korean/bm25_retriever.py` | 검색 결과 데이터 모델 |
| `KoreanDenseRetriever` | `nlp/korean/dense_retriever.py` | Dense 임베딩 검색기 |
| `DenseRetrievalResult` | `nlp/korean/dense_retriever.py` | Dense 검색 결과 데이터 모델 |
| `DeviceType` | `nlp/korean/dense_retriever.py` | 디바이스 타입 열거형 |
| `KoreanHybridRetriever` | `nlp/korean/hybrid_retriever.py` | 하이브리드 검색기 |
| `HybridResult` | `nlp/korean/hybrid_retriever.py` | 하이브리드 검색 결과 데이터 모델 |
| `FusionMethod` | `nlp/korean/hybrid_retriever.py` | 융합 방법 열거형 |
| `KoreanDocumentChunker` | `nlp/korean/document_chunker.py` | 한국어 문서 청커 |
| `ParagraphChunker` | `nlp/korean/document_chunker.py` | 문단 청커 |
| `Chunk` | `nlp/korean/document_chunker.py` | 청크 데이터 모델 |
| `KoreanFaithfulnessChecker` | `nlp/korean/korean_evaluation.py` | 한국어 신뢰성 검사기 |
| `KoreanSemanticSimilarity` | `nlp/korean/korean_evaluation.py` | 한국어 의미 유사도 |
| `FaithfulnessResult` | `nlp/korean/korean_evaluation.py` | 신뢰성 결과 데이터 모델 |
| `ClaimVerification` | `nlp/korean/korean_evaluation.py` | 클레임 검증 데이터 모델 |
| `SemanticSimilarityResult` | `nlp/korean/korean_evaluation.py` | 의미 유사도 결과 데이터 모델 |
| `NumberWithUnit` | `nlp/korean/korean_evaluation.py` | 숫자+단위 데이터 모델 |

##### Cache Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| `MemoryCacheAdapter` | `cache/memory_cache.py` | 메모리 캐시 어댑터 |

##### Domain Memory Adapters

| 클래스명 | 파일 | 역할 |
|---------|------|------|
| `SQLiteDomainMemoryAdapter` | `domain_memory/sqlite_adapter.py` | SQLite 도메인 메모리 어댑터 |

---

## 3. 클린 아키텍처 관점 분류

클린 아키텍처는 **Entities**, **Use Cases**, **Interface Adapters**, **Frameworks & Drivers** 네 계층으로 구성됩니다.

### 3.1 Entities (엔티티 계층)

비즈니스 규칙을 포함하는 핵심 엔티티들입니다.

**해당 클래스**: [2.1.1 Domain Entities](#211-domain-entities-domain-엔티티) 참조

### 3.2 Use Cases (유스 케이스 계층)

애플리케이션의 비즈니스 로직을 구현하는 서비스들입니다.

**해당 클래스**: [2.1.2 Domain Services](#212-domain-services-도메인-서비스) 참조

### 3.3 Interface Adapters (인터페이스 어댑터 계층)

외부 세계와 내부 세계를 변환하는 어댑터들입니다.

**해당 클래스**: [2.3 Adapters Layer](#23-adapters-layer-어댑터-계층) 참조

### 3.4 Frameworks & Drivers (프레임워크 & 드라이버 계층)

외부 프레임워크와 도구들입니다.

**해당 클래스**:
- LLM API 클라이언트 (`OpenAI`, `Anthropic`, `Ollama`)
- 데이터베이스 드라이버 (`sqlite3`, `psycopg`)
- 웹 프레임워크 (`Streamlit`, `Typer`)

---

## 4. DDD 관점 분류

DDD는 **Entities**, **Value Objects**, **Aggregates**, **Domain Services**, **Repositories**로 구성됩니다.

### 4.1 Entities (엔티티)

고유 식별자를 가지는 도메인 객체입니다.

**해당 클래스**:
- `TestCase`, `Dataset`, `EvaluationRun`, `TestCaseResult`
- `Experiment`, `ExperimentGroup`
- `ImprovementReport`, `RAGImprovementGuide`, `ImprovementAction`
- `EntityModel`, `RelationModel`
- `FactualFact`, `LearningMemory`, `BehaviorEntry`
- `AnalysisNode`, `AnalysisPipeline`
- `RAGTestCase`, `BenchmarkSuite`

### 4.2 Value Objects (값 객체)

값으로 식별되는 불변 객체입니다.

**해당 클래스**:
- `MetricScore`, `MetricType`, `AnalysisType`, `QuestionType`
- `EffectSizeLevel`, `RAGComponent`, `PatternType`, `ImprovementPriority`
- `AnalysisIntent`, `NodeExecutionStatus`
- `TaskType`, `FusionMethod`, `DeviceType`
- 모든 통계/분석 결과의 세부 데이터 모델들

### 4.3 Aggregates (집합체)

일관성 경계를 가지는 엔티티 그룹입니다.

**해당 클래스**:
- `Dataset` (Aggregate Root: `TestCase`들을 포함)
- `EvaluationRun` (Aggregate Root: `TestCaseResult`, `MetricScore`들을 포함)
- `AnalysisBundle` (여러 `AnalysisResult`를 포함)
- `BehaviorHandbook` (`BehaviorEntry`들을 포함)
- `AnalysisPipeline` (Aggregate Root: `AnalysisNode`들을 포함)
- `ModuleCatalog` (`ModuleMetadata`들을 포함)
- `BenchmarkSuite` (Aggregate Root: `BenchmarkResult`들을 포함)

### 4.4 Domain Services (도메인 서비스)

여러 엔티티에 걸친 비즈니스 로직을 처리하는 서비스입니다.

**해당 클래스**: [2.1.2 Domain Services](#212-domain-services-도메인-서비스) 참조

### 4.5 Repositories (저장소)

엔티티의 영속성을 관리하는 인터페이스입니다.

**해당 클래스**:
- `StoragePort` 구현체들 (`SQLiteStorageAdapter`, `PostgreSQLStorageAdapter`)
- `DomainMemoryPort` 구현체 (`SQLiteDomainMemoryAdapter`)

---

## 5. 역할별 분류

### 5.1 데이터 모델 (Data Models)

도메인 개념을 표현하는 데이터 구조입니다.

**카테고리**:
- **엔티티 모델**: `TestCase`, `EvaluationRun`, `Experiment` 등
- **값 객체 모델**: `MetricScore`, `AnalysisType` 등
- **집계 모델**: `Dataset`, `AnalysisBundle` 등

### 5.2 비즈니스 로직 (Business Logic)

도메인 규칙과 비즈니스 로직을 구현하는 서비스입니다.

**카테고리**:
- **평가 서비스**: `RagasEvaluator`
- **분석 서비스**: `AnalysisService`, `PipelineOrchestrator`
- **개선 서비스**: `ImprovementGuideService`
- **학습 서비스**: `DomainLearningHook`

### 5.3 인터페이스 (Interfaces)

도메인과 외부 세계 사이의 계약을 정의하는 포트입니다.

**카테고리**:
- **입력 포트**: `EvaluatorPort`, `AnalysisPipelinePort`, `WebUIPort`
- **출력 포트**: `DatasetPort`, `LLMPort`, `StoragePort`, `TrackerPort` 등

### 5.4 구현체 (Implementations)

포트 인터페이스를 구현하는 어댑터들입니다.

**카테고리**:
- **입력 어댑터**: CLI, Web UI
- **출력 어댑터**: LLM, Storage, Tracker, Analysis, Report 등

### 5.5 유틸리티 (Utilities)

공통 기능을 제공하는 헬퍼 클래스들입니다.

**카테고리**:
- `AnalysisDataProcessor`, `SQLQueries`, `TokenUsage` 등

---

## 6. 프로세스 순서별 분류

평가 파이프라인의 실행 순서에 따라 클래스를 분류합니다.

### 6.1 입력 단계 (Input Stage)

**역할**: 외부에서 데이터를 받아 도메인 모델로 변환

**클래스**:
- **어댑터**: `JSONDatasetLoader`, `CSVDatasetLoader`, `ExcelDatasetLoader`
- **포트**: `DatasetPort`
- **엔티티**: `Dataset`, `TestCase`

### 6.2 평가 단계 (Evaluation Stage)

**역할**: 테스트 케이스를 평가하고 메트릭을 계산

**클래스**:
- **서비스**: `RagasEvaluator`
- **포트**: `EvaluatorPort`, `LLMPort`, `EmbeddingPort`
- **어댑터**: `OpenAIAdapter`, `AnthropicAdapter`, `OllamaAdapter` 등
- **엔티티**: `EvaluationRun`, `TestCaseResult`, `MetricScore`

### 6.3 분석 단계 (Analysis Stage)

**역할**: 평가 결과를 분석하여 인사이트 생성

**클래스**:
- **서비스**: `AnalysisService`, `PipelineOrchestrator`
- **포트**: `AnalysisPort`, `AnalysisModulePort`, `NLPAnalysisPort`, `CausalAnalysisPort`
- **어댑터**: `StatisticalAnalysisAdapter`, `NLPAnalysisAdapter`, `CausalAnalysisAdapter` 등
- **엔티티**: `AnalysisResult`, `StatisticalAnalysis`, `NLPAnalysis`, `CausalAnalysis`

### 6.4 개선 단계 (Improvement Stage)

**역할**: 분석 결과를 바탕으로 개선 가이드 생성

**클래스**:
- **서비스**: `ImprovementGuideService`
- **포트**: `PatternDetectorPort`, `InsightGeneratorPort`, `PlaybookPort`
- **어댑터**: `PatternDetector`, `InsightGenerator`, `PlaybookLoader`
- **엔티티**: `ImprovementReport`, `RAGImprovementGuide`, `ImprovementAction`

### 6.5 저장 단계 (Storage Stage)

**역할**: 평가 결과와 분석 결과를 영속화

**클래스**:
- **포트**: `StoragePort`, `TrackerPort`, `DomainMemoryPort`
- **어댑터**: `SQLiteStorageAdapter`, `PostgreSQLStorageAdapter`, `LangfuseAdapter`, `MLflowAdapter`, `SQLiteDomainMemoryAdapter`

### 6.6 보고 단계 (Reporting Stage)

**역할**: 결과를 보고서로 생성

**클래스**:
- **포트**: `ReportPort`
- **어댑터**: `LLMReportGenerator`, `MarkdownReportAdapter`
- **엔티티**: `LLMReport`, `LLMReportSection`

### 6.7 학습 단계 (Learning Stage)

**역할**: 평가 결과에서 도메인 지식을 추출하여 메모리에 저장

**클래스**:
- **서비스**: `DomainLearningHook`, `KnowledgeGraphGenerator`, `EntityExtractor`
- **포트**: `DomainLearningHookPort`, `DomainMemoryPort`
- **어댑터**: `SQLiteDomainMemoryAdapter`
- **엔티티**: `FactualFact`, `LearningMemory`, `DomainMemoryContext`, `EntityModel`, `RelationModel`

---

## 7. 클래스 상세 목록

### 7.1 Domain Entities (도메인 엔티티)

#### 7.1.1 Core Entities (핵심 엔티티)

| 클래스명 | 패키지 | 책임 | 의존성 |
|---------|--------|------|--------|
| `TestCase` | `domain.entities.dataset` | 평가 테스트 케이스 표현 | 없음 |
| `Dataset` | `domain.entities.dataset` | 테스트 케이스 집합 관리 | `TestCase` |
| `EvaluationRun` | `domain.entities.result` | 평가 실행 결과 집계 | `TestCaseResult`, `MetricScore` |
| `TestCaseResult` | `domain.entities.result` | 개별 테스트 케이스 평가 결과 | `MetricScore` |
| `MetricScore` | `domain.entities.result` | 메트릭 점수 표현 | `MetricType` |

#### 7.1.2 Analysis Entities (분석 엔티티)

| 클래스명 | 패키지 | 책임 | 의존성 |
|---------|--------|------|--------|
| `AnalysisResult` | `domain.entities.analysis` | 분석 결과 기본 클래스 | 없음 |
| `StatisticalAnalysis` | `domain.entities.analysis` | 통계 분석 결과 | `AnalysisResult` |
| `NLPAnalysis` | `domain.entities.analysis` | NLP 분석 결과 | `AnalysisResult` |
| `CausalAnalysis` | `domain.entities.analysis` | 인과 분석 결과 | `AnalysisResult` |
| `AnalysisBundle` | `domain.entities.analysis` | 여러 분석 결과 묶음 | `AnalysisResult` |

#### 7.1.3 Improvement Entities (개선 엔티티)

| 클래스명 | 패키지 | 책임 | 의존성 |
|---------|--------|------|--------|
| `ImprovementReport` | `domain.entities.improvement` | 개선 보고서 | `RAGImprovementGuide` |
| `RAGImprovementGuide` | `domain.entities.improvement` | RAG 개선 가이드 | `ImprovementAction` |
| `ImprovementAction` | `domain.entities.improvement` | 개선 액션 | `ImprovementEvidence` |

#### 7.1.4 Memory Entities (메모리 엔티티)

| 클래스명 | 패키지 | 책임 | 의존성 |
|---------|--------|------|--------|
| `FactualFact` | `domain.entities.memory` | 검증된 도메인 사실 | 없음 |
| `LearningMemory` | `domain.entities.memory` | 학습 메모리 | 없음 |
| `DomainMemoryContext` | `domain.entities.memory` | 워킹 메모리 컨텍스트 | 없음 |
| `BehaviorEntry` | `domain.entities.memory` | 행동 패턴 엔트리 | 없음 |
| `BehaviorHandbook` | `domain.entities.memory` | 행동 핸드북 | `BehaviorEntry` |

#### 7.1.5 Pipeline Entities (파이프라인 엔티티)

| 클래스명 | 패키지 | 책임 | 의존성 |
|---------|--------|------|--------|
| `AnalysisPipeline` | `domain.entities.analysis_pipeline` | 분석 파이프라인 DAG | `AnalysisNode` |
| `AnalysisNode` | `domain.entities.analysis_pipeline` | 분석 파이프라인 노드 | `AnalysisContext` |
| `PipelineResult` | `domain.entities.analysis_pipeline` | 파이프라인 실행 결과 | `NodeResult` |

### 7.2 Domain Services (도메인 서비스)

| 클래스명 | 패키지 | 책임 | 의존성 |
|---------|--------|------|--------|
| `RagasEvaluator` | `domain.services.evaluator` | RAG 평가 실행 | `EvaluatorPort`, `LLMPort`, `EmbeddingPort` |
| `AnalysisService` | `domain.services.analysis_service` | 분석 서비스 오케스트레이션 | `AnalysisPort`, `NLPAnalysisPort`, `CausalAnalysisPort` |
| `ImprovementGuideService` | `domain.services.improvement_guide_service` | 개선 가이드 생성 | `PatternDetectorPort`, `InsightGeneratorPort`, `PlaybookPort` |
| `DomainLearningHook` | `domain.services.domain_learning_hook` | 도메인 학습 훅 | `DomainMemoryPort` |
| `PipelineOrchestrator` | `domain.services.pipeline_orchestrator` | 파이프라인 오케스트레이션 | `AnalysisModulePort`, `AnalysisCachePort` |
| `IntentClassifier` | `domain.services.intent_classifier` | 의도 분류 | `IntentClassifierPort` |
| `KnowledgeGraphGenerator` | `domain.services.kg_generator` | 지식 그래프 생성 | `LLMPort`, `EntityExtractor` |

### 7.3 Ports (포트)

#### 7.3.1 Inbound Ports (입력 포트)

| 클래스명 | 패키지 | 책임 | 구현체 |
|---------|--------|------|--------|
| `EvaluatorPort` | `ports.inbound.evaluator_port` | 평가 실행 인터페이스 | `RagasEvaluator` |
| `AnalysisPipelinePort` | `ports.inbound.analysis_pipeline_port` | 분석 파이프라인 인터페이스 | `AnalysisPipelineService` |
| `WebUIPort` | `ports.inbound.web_port` | 웹 UI 인터페이스 | `WebUIAdapter` |

#### 7.3.2 Outbound Ports (출력 포트)

| 클래스명 | 패키지 | 책임 | 구현 어댑터 |
|---------|--------|------|------------|
| `DatasetPort` | `ports.outbound.dataset_port` | 데이터셋 로딩 | `JSONDatasetLoader`, `CSVDatasetLoader`, `ExcelDatasetLoader` |
| `LLMPort` | `ports.outbound.llm_port` | LLM 인터페이스 | `OpenAIAdapter`, `AnthropicAdapter`, `OllamaAdapter`, `AzureOpenAIAdapter` |
| `StoragePort` | `ports.outbound.storage_port` | 저장소 인터페이스 | `SQLiteStorageAdapter`, `PostgreSQLStorageAdapter` |
| `TrackerPort` | `ports.outbound.tracker_port` | 추적 인터페이스 | `LangfuseAdapter`, `MLflowAdapter` |
| `AnalysisPort` | `ports.outbound.analysis_port` | 분석 인터페이스 | `StatisticalAnalysisAdapter`, `NLPAnalysisAdapter`, `CausalAnalysisAdapter` |
| `ReportPort` | `ports.outbound.report_port` | 보고서 생성 인터페이스 | `LLMReportGenerator`, `MarkdownReportAdapter` |

### 7.4 Adapters (어댑터)

#### 7.4.1 Inbound Adapters (입력 어댑터)

| 클래스명 | 패키지 | 책임 | 의존성 |
|---------|--------|------|--------|
| CLI 명령어들 | `adapters.inbound.cli.commands` | CLI 명령어 구현 | `EvaluatorPort`, `AnalysisPipelinePort` 등 |
| `WebUIAdapter` | `adapters.inbound.web.adapter` | Streamlit 웹 UI | `WebUIPort` |

#### 7.4.2 Outbound Adapters (출력 어댑터)

| 클래스명 | 패키지 | 책임 | 의존성 |
|---------|--------|------|--------|
| `BaseLLMAdapter` | `adapters.outbound.llm.base` | LLM 어댑터 기본 클래스 | `LLMPort` |
| `OpenAIAdapter` | `adapters.outbound.llm.openai_adapter` | OpenAI API 어댑터 | `BaseLLMAdapter` |
| `SQLiteStorageAdapter` | `adapters.outbound.storage.sqlite_adapter` | SQLite 저장소 | `StoragePort` |
| `StatisticalAnalysisAdapter` | `adapters.outbound.analysis.statistical_adapter` | 통계 분석 | `AnalysisPort` |
| `LLMReportGenerator` | `adapters.outbound.report.llm_report_generator` | LLM 보고서 생성 | `ReportPort`, `LLMPort` |

---

## 8. 아키텍처 원칙 준수

### 8.1 SOLID 원칙

#### Single Responsibility Principle (단일 책임 원칙)

각 클래스는 하나의 책임만 가집니다:

- **엔티티**: 도메인 개념 표현
- **서비스**: 비즈니스 로직 처리
- **포트**: 인터페이스 정의
- **어댑터**: 외부 시스템 연동

#### Open/Closed Principle (개방-폐쇄 원칙)

- **포트 인터페이스**: 확장에는 열려 있고 수정에는 닫혀 있음
- **기본 클래스**: `BaseLLMAdapter`, `BaseAnalysisAdapter` 등으로 확장 가능

#### Liskov Substitution Principle (리스코프 치환 원칙)

- 모든 LLM 어댑터는 `LLMPort` 인터페이스를 완전히 구현
- 모든 저장소 어댑터는 `StoragePort` 인터페이스를 완전히 구현

#### Interface Segregation Principle (인터페이스 분리 원칙)

- 포트는 작고 집중된 인터페이스로 분리 (`DatasetPort`, `LLMPort`, `StoragePort` 등)
- 프로토콜 기반으로 필요한 메서드만 정의

#### Dependency Inversion Principle (의존성 역전 원칙)

- 도메인 계층은 포트(인터페이스)에 의존
- 어댑터가 포트를 구현
- 의존성 방향: `Domain → Ports ← Adapters`

### 8.2 YAGNI 원칙

- 필요한 기능만 구현
- 미래의 요구사항을 위한 추상화 지양
- 실제 사용되는 기능만 포함

### 8.3 TDD 원칙

- 모든 도메인 로직은 테스트 가능
- 포트 인터페이스로 외부 의존성 격리
- Mock을 통한 단위 테스트 용이

---

## 9. 클래스 간 의존성 관계

### 9.1 의존성 방향

```
Adapters → Ports ← Domain
   ↓         ↓        ↓
External  Interface  Business
Systems   Contract   Logic
```

### 9.2 주요 의존성 체인

#### 평가 파이프라인

```
CLI/Web Adapter
    ↓
EvaluatorPort (인터페이스)
    ↓
RagasEvaluator (서비스)
    ↓
LLMPort, EmbeddingPort (인터페이스)
    ↓
LLM Adapters (구현체)
```

#### 분석 파이프라인

```
CLI/Web Adapter
    ↓
AnalysisPipelinePort (인터페이스)
    ↓
PipelineOrchestrator (서비스)
    ↓
AnalysisModulePort (인터페이스)
    ↓
Analysis Modules (구현체)
```

#### 저장 파이프라인

```
Domain Services
    ↓
StoragePort, TrackerPort (인터페이스)
    ↓
Storage/Tracker Adapters (구현체)
```

---

## 10. 확장 포인트

### 10.1 새로운 LLM 프로바이더 추가

1. `LLMPort` 인터페이스 구현
2. `BaseLLMAdapter` 상속
3. `adapters/outbound/llm/`에 어댑터 추가
4. `get_llm_adapter()` 팩토리에 등록

### 10.2 새로운 분석 모듈 추가

1. `AnalysisModulePort` 인터페이스 구현
2. `BaseAnalysisModule` 상속
3. `adapters/outbound/analysis/`에 모듈 추가
4. `ModuleCatalog`에 등록

### 10.3 새로운 저장소 추가

1. `StoragePort` 인터페이스 구현
2. `adapters/outbound/storage/`에 어댑터 추가
3. 설정에서 선택 가능하도록 구성

---

## 11. 결론

이 문서는 EvalVault 프로젝트의 모든 클래스를 체계적으로 분류하고 정리한 카탈로그입니다. 각 클래스는:

1. **역할**: 명확한 단일 책임
2. **위치**: 헥사고날/클린/DDD 아키텍처 관점에서의 명확한 위치
3. **의존성**: 다른 클래스와의 관계
4. **프로세스**: 실행 흐름상의 위치

를 가지고 있습니다.

이 분류 체계를 통해:
- **새로운 개발자**는 빠르게 코드베이스를 이해할 수 있습니다
- **리팩토링** 시 영향 범위를 쉽게 파악할 수 있습니다
- **테스트** 작성 시 Mock 대상과 테스트 대상이 명확합니다
- **확장** 시 적절한 위치에 새로운 클래스를 추가할 수 있습니다

---

**문서 버전**: 1.0
**최종 업데이트**: 2026년
**작성 기준**: EvalVault 프로젝트 전체 코드베이스
