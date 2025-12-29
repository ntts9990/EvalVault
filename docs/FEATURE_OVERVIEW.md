# EvalVault 기능 개요 및 유즈케이스 분석

> **문서 버전**: 1.0.0
> **작성일**: 2025-12-29
> **목적**: 완료된 각 기능이 전체 유즈케이스에서 담당하는 역할을 구조적으로 분석

---

## 목차

1. [전체 아키텍처 개요](#1-전체-아키텍처-개요)
2. [핵심 평가 시스템 (Core Evaluation System)](#2-핵심-평가-시스템-core-evaluation-system)
3. [데이터 영속성 계층 (Storage Layer)](#3-데이터-영속성-계층-storage-layer)
4. [추적 및 관찰성 (Tracing & Observability)](#4-추적-및-관찰성-tracing--observability)
5. [실험 관리 (Experiment Management)](#5-실험-관리-experiment-management)
6. [도메인 메모리 계층화 (Domain Memory Layering)](#6-도메인-메모리-계층화-domain-memory-layering)
7. [NLP 분석 (NLP Analysis)](#7-nlp-분석-nlp-analysis)
8. [인과 분석 (Causal Analysis)](#8-인과-분석-causal-analysis)
9. [지식 그래프 (Knowledge Graph)](#9-지식-그래프-knowledge-graph)
10. [기능 간 상호작용 및 데이터 흐름](#10-기능-간-상호작용-및-데이터-흐름)

---

## 1. 전체 아키텍처 개요

### 1.1 시스템 목적

EvalVault는 **RAG (Retrieval-Augmented Generation) 시스템의 품질을 평가하고 개선하는 종합 플랫폼**입니다. 단순한 평가 도구를 넘어서, 평가 결과에서 학습하여 지속적으로 개선되는 시스템을 지향합니다.

### 1.2 핵심 가치 제안

```
기존 RAGAS 래퍼의 한계
└─> 평가 실행 → 결과 출력 → 끝
    (매번 동일한 방식으로 평가, 학습 없음)

EvalVault의 차별화
└─> 평가 실행 → 결과 분석 → 패턴 학습 → 다음 평가에 반영
    (사용할수록 정확도 향상, 도메인 지식 축적)
```

**중요한 설명:**
- **Ragas 평가 자체는 매번 동일한 프롬프트를 사용합니다** (Ragas 메트릭의 고정된 프롬프트)
- **학습 피드백 루프는 평가가 아닌 다른 컴포넌트에서 작동합니다:**
  1. **KG 생성 및 테스트셋 생성**: EntityExtractor가 학습된 패턴을 사용하여 더 정확한 엔티티 추출
  2. **도메인 지식 축적**: 평가 결과에서 검증된 사실(FactualFact)을 추출하여 도메인 지식베이스 구축
  3. **패턴 학습**: 엔티티 타입별 신뢰도, 실패 패턴 등을 학습하여 다음 KG 생성에 반영

**실제 작동 방식:**
```
평가 #1: Dataset → RagasEvaluator → EvaluationRun
    │
    └─> DomainLearningHook.on_evaluation_complete()
            ├─> 엔티티 타입별 신뢰도 계산 (예: "organization" 타입 = 0.92)
            └─> LearningMemory 저장

평가 #2 (KG 기반 테스트셋 생성 시):
    │
    └─> KnowledgeGraphGenerator.build_graph(documents)
            └─> EntityExtractor.extract_entities()
                    └─> DomainMemoryAdapter.get_aggregated_reliability()
                            └─> 학습된 신뢰도 점수를 가중치로 적용
                                    └─> 더 정확한 엔티티 추출 → 더 나은 KG → 더 나은 테스트셋
```

### 1.3 전체 유즈케이스 맵

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVALVAULT USE CASE MAP                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [1] 데이터셋 준비                                               │
│      ├─> Basic Testset Generator (문서 → 테스트셋)              │
│      └─> KG Testset Generator (문서 → KG → 테스트셋)           │
│                                                                  │
│  [2] 평가 실행                                                   │
│      ├─> RagasEvaluator (Ragas 메트릭 실행)                     │
│      ├─> Custom Metrics (도메인 특화 메트릭)                    │
│      └─> Token/Cost 추적                                         │
│                                                                  │
│  [3] 결과 저장 및 추적                                           │
│      ├─> Storage Adapter (SQLite/PostgreSQL)                    │
│      ├─> Tracker Adapter (Langfuse/MLflow)                      │
│      └─> Domain Memory (학습 패턴 저장)                         │
│                                                                  │
│  [4] 결과 분석                                                   │
│      ├─> Statistical Analysis (기본 통계)                       │
│      ├─> NLP Analysis (텍스트 분석, 질문 유형 분류)             │
│      └─> Causal Analysis (인과 관계, 근본 원인 분석)             │
│                                                                  │
│  [5] 실험 관리                                                   │
│      ├─> Experiment Manager (A/B 테스트)                        │
│      └─> Group Comparison (그룹 간 메트릭 비교)                  │
│                                                                  │
│  [6] 학습 및 개선                                                │
│      ├─> Domain Memory Formation (평가에서 사실 추출)           │
│      ├─> Pattern Learning (성공/실패 패턴 학습)                 │
│      └─> Behavior Extraction (재사용 가능한 행동 추출)         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 핵심 평가 시스템 (Core Evaluation System)

### 2.1 역할 및 책임

**RagasEvaluator**는 EvalVault의 핵심 평가 엔진으로, RAG 시스템의 품질을 정량적으로 측정합니다.

**주요 책임:**
- Ragas 메트릭 실행 (faithfulness, answer_relevancy, context_precision 등)
- 커스텀 메트릭 실행 (도메인 특화 메트릭)
- 결과 집계 및 임계값 판정
- 토큰 사용량 및 비용 추적

### 2.2 유즈케이스에서의 위치

```
평가 실행 유즈케이스
═══════════════════════════════════════════════════════════════

[입력] Dataset (테스트 케이스 집합)
    │
    ▼
[1] RagasEvaluator.evaluate()
    │
    ├─> [1-1] 임계값 해석 (CLI > Dataset > 기본값)
    │
    ├─> [1-2] Ragas 메트릭 실행
    │       │
    │       ├─> Dataset → Ragas SingleTurnSample 변환
    │       ├─> LLMPort.as_ragas_llm() 호출
    │       ├─> 각 메트릭별 ascore() 실행
    │       └─> 토큰 사용량/비용 추적
    │
    ├─> [1-3] 커스텀 메트릭 실행
    │       │
    │       └─> InsuranceTermAccuracy 등 도메인 메트릭
    │
    └─> [1-4] 결과 집계
            │
            ├─> TestCaseResult 생성 (각 테스트 케이스별)
            ├─> MetricScore 생성 (메트릭별 점수, 임계값 판정)
            └─> EvaluationRun 생성 (전체 실행 결과)
    │
    ▼
[출력] EvaluationRun
    │
    ├─> Storage Adapter로 저장
    ├─> Tracker Adapter로 추적
    └─> Analysis Service로 분석
```

### 2.3 핵심 구현 세부사항

#### 2.3.1 메트릭 분류 및 처리

```python
# RagasEvaluator의 메트릭 분류
RAGAS_METRICS = {
    "faithfulness": Faithfulness,           # 답변이 컨텍스트에 기반하는지
    "answer_relevancy": AnswerRelevancy,    # 답변이 질문과 관련 있는지
    "context_precision": ContextPrecision,  # 검색된 컨텍스트의 정밀도
    "context_recall": ContextRecall,       # 필요한 컨텍스트 회수율
    "factual_correctness": FactualCorrectness,  # 사실 정확도
    "semantic_similarity": SemanticSimilarity, # 의미적 유사도
}

CUSTOM_METRICS = {
    "insurance_term_accuracy": InsuranceTermAccuracy,  # 보험 용어 정확도
}
```

**처리 흐름:**
1. Ragas 메트릭: LLM을 사용하여 평가 (토큰 소비)
2. 커스텀 메트릭: 규칙 기반 평가 (토큰 소비 없음)

#### 2.3.2 임계값 해석 전략

```python
# 우선순위: CLI 옵션 > Dataset 내장 > 기본값(0.7)
resolved_thresholds = {}
for metric in metrics:
    if thresholds and metric in thresholds:
        resolved_thresholds[metric] = thresholds[metric]  # CLI 우선
    elif dataset.thresholds and metric in dataset.thresholds:
        resolved_thresholds[metric] = dataset.thresholds[metric]  # Dataset
    else:
        resolved_thresholds[metric] = 0.7  # 기본값
```

**의미:** 사용자가 명시적으로 지정한 임계값이 가장 높은 우선순위를 가집니다.

### 2.4 다른 기능과의 연계

- **Storage Adapter**: `EvaluationRun`을 데이터베이스에 저장
- **Tracker Adapter**: 평가 실행을 Langfuse/MLflow에 추적
- **Domain Memory**: 평가 결과에서 사실 및 패턴 추출
- **Analysis Service**: 평가 결과에 대한 통계/NLP/인과 분석

---

## 3. 데이터 영속성 계층 (Storage Layer)

### 3.1 역할 및 책임

**Storage Adapter**는 평가 결과를 영구적으로 저장하고 조회하는 책임을 담당합니다.

**주요 책임:**
- `EvaluationRun` 저장 및 조회
- `Experiment` 저장 및 조회
- `AnalysisResult` 저장 및 조회
- 히스토리 조회 및 필터링

### 3.2 구현체

#### 3.2.1 SQLiteStorageAdapter

**용도:** 로컬 개발 및 소규모 프로덕션 환경

**특징:**
- 파일 기반 데이터베이스 (이식성 높음)
- 외래 키 제약 조건 지원
- 인덱스 최적화 (dataset_name, model_name, started_at)

**스키마 구조:**
```sql
evaluation_runs (메인 실행 정보)
    ├─> test_case_results (각 테스트 케이스 결과)
    │       └─> metric_scores (메트릭별 점수)
    │
    ├─> experiments (실험 정보)
    │       ├─> experiment_groups (그룹 정보)
    │       └─> experiment_group_runs (그룹-실행 매핑)
    │
    └─> analysis_results (분석 결과)
```

#### 3.2.2 PostgreSQLStorageAdapter

**용도:** 대규모 프로덕션 환경

**특징:**
- JSONB 타입 활용 (메트릭 목록, 임계값 등)
- UUID 기반 기본 키
- 타임존 지원 (TIMESTAMP WITH TIME ZONE)

### 3.3 유즈케이스에서의 위치

```
저장 및 조회 유즈케이스
═══════════════════════════════════════════════════════════════

[저장 흐름]
    │
    ├─> [1] 평가 실행 완료 후
    │       │
    │       └─> StorageAdapter.save_run(evaluation_run)
    │               │
    │               ├─> evaluation_runs 테이블에 메인 정보 저장
    │               ├─> test_case_results 테이블에 각 결과 저장
    │               └─> metric_scores 테이블에 메트릭 점수 저장
    │
    └─> [2] 실험 생성/수정 시
            │
            └─> StorageAdapter.save_experiment(experiment)
                    │
                    ├─> experiments 테이블에 실험 정보 저장
                    └─> experiment_groups 테이블에 그룹 정보 저장

[조회 흐름]
    │
    ├─> [1] 히스토리 조회
    │       │
    │       └─> StorageAdapter.list_runs(
    │               dataset_name="...",
    │               model_name="...",
    │               limit=10
    │           )
    │
    ├─> [2] 특정 실행 조회
    │       │
    │       └─> StorageAdapter.get_run(run_id)
    │               │
    │               └─> JOIN으로 test_case_results, metric_scores 조회
    │
    └─> [3] 실험 비교
            │
            └─> ExperimentManager.compare_groups()
                    │
                    └─> StorageAdapter.get_run() 여러 번 호출
                            (각 그룹의 run_id에 대해)
```

### 3.4 다른 기능과의 연계

- **RagasEvaluator**: 평가 완료 후 `save_run()` 호출
- **ExperimentManager**: 실험 그룹의 실행 결과 조회
- **Analysis Service**: 분석 결과 저장 (`save_analysis()`)
- **CLI**: `history`, `compare`, `export` 명령어에서 사용

---

## 4. 추적 및 관찰성 (Tracing & Observability)

### 4.1 역할 및 책임

**Tracker Adapter**는 평가 실행을 외부 추적 시스템에 기록하여 관찰성을 제공합니다.

**주요 책임:**
- 평가 실행을 trace로 기록
- 각 테스트 케이스를 span으로 기록
- 메트릭 점수를 score로 기록
- 메타데이터 및 리소스 사용량 기록

### 4.2 구현체

#### 4.2.1 LangfuseAdapter

**용도:** LLM 애플리케이션 전용 추적

**특징:**
- Trace-Span 구조 (평가 실행 = Trace, 테스트 케이스 = Span)
- Score 기록 (메트릭 점수)
- Input/Output 기록 (질문, 답변, 컨텍스트)
- 메트릭 요약 (평균 점수, 통과율)

**기록 구조:**
```
Trace (evaluation-{run_id})
    ├─> Metadata: dataset_name, model_name, metrics_evaluated
    ├─> Output: metric_summary (평균 점수, 통과율)
    │
    └─> Spans (각 테스트 케이스)
            ├─> Input: question, contexts
            ├─> Output: answer, ground_truth
            └─> Scores: faithfulness, answer_relevancy, ...
```

#### 4.2.2 MLflowAdapter

**용도:** ML 실험 추적

**특징:**
- Run-Experiment 구조 (평가 실행 = Run)
- Parameters 기록 (데이터셋, 모델 정보)
- Metrics 기록 (평균 메트릭 점수, 통과율)
- Artifacts 기록 (개별 테스트 결과 JSON)

**기록 구조:**
```
MLflow Run (evaluation-{run_id})
    ├─> Parameters: dataset_name, model_name, total_test_cases
    ├─> Metrics: avg_faithfulness, avg_answer_relevancy, pass_rate
    └─> Artifacts: test_results.json (모든 테스트 케이스 결과)
```

### 4.3 유즈케이스에서의 위치

```
추적 유즈케이스
═══════════════════════════════════════════════════════════════

[평가 실행 시]
    │
    ├─> [1] CLI에서 --langfuse 옵션 활성화
    │       │
    │       └─> TrackerAdapter.log_evaluation_run(evaluation_run)
    │               │
    │               ├─> Trace/Run 시작
    │               ├─> 메타데이터 기록
    │               ├─> 각 테스트 케이스를 Span으로 기록
    │               ├─> 메트릭 점수를 Score로 기록
    │               └─> Trace/Run 종료
    │
    └─> [2] 외부 시스템에서 조회
            │
            ├─> Langfuse UI: trace_id로 상세 조회
            └─> MLflow UI: run_id로 실험 비교
```

### 4.4 다른 기능과의 연계

- **RagasEvaluator**: 평가 완료 후 `log_evaluation_run()` 호출
- **CLI**: `--langfuse` 옵션으로 활성화
- **Storage Adapter**: `langfuse_trace_id`를 저장하여 연결

---

## 5. 실험 관리 (Experiment Management)

### 5.1 역할 및 책임

**ExperimentManager**는 A/B 테스트 및 실험을 생성, 관리하고 그룹 간 메트릭을 비교합니다.

**주요 책임:**
- 실험 생성 및 그룹 관리
- 그룹에 평가 실행 추가
- 그룹 간 메트릭 비교
- 실험 결론 기록

### 5.2 핵심 개념

#### 5.2.1 Experiment 엔티티

```python
@dataclass
class Experiment:
    experiment_id: str
    name: str
    hypothesis: str  # 가설 (예: "모델 A가 모델 B보다 성능이 좋을 것이다")
    status: Literal["draft", "running", "completed", "archived"]
    groups: list[ExperimentGroup]  # "control", "variant_a", "variant_b"
    metrics_to_compare: list[str]  # 비교할 메트릭 목록
    conclusion: str | None  # 실험 결론
```

#### 5.2.2 ExperimentGroup

```python
@dataclass
class ExperimentGroup:
    name: str  # "control", "variant_a"
    run_ids: list[str]  # 이 그룹에 속한 평가 실행 ID 목록
    description: str
```

### 5.3 유즈케이스에서의 위치

```
A/B 테스트 유즈케이스
═══════════════════════════════════════════════════════════════

[1] 실험 생성
    │
    └─> ExperimentManager.create_experiment(
            name="Model Comparison",
            hypothesis="Larger model will score higher",
            metrics=["faithfulness", "answer_relevancy"]
        )

[2] 그룹 추가
    │
    ├─> experiment.add_group("control", "Baseline model")
    └─> experiment.add_group("variant_a", "Larger model")

[3] 평가 실행 추가
    │
    ├─> [3-1] 모델 A로 평가 실행
    │       │
    │       └─> run_id_1 = evaluator.evaluate(...)
    │
    ├─> [3-2] 모델 B로 평가 실행
    │       │
    │       └─> run_id_2 = evaluator.evaluate(...)
    │
    └─> [3-3] 그룹에 추가
            │
            ├─> experiment.add_run_to_group("control", run_id_1)
            └─> experiment.add_run_to_group("variant_a", run_id_2)

[4] 그룹 비교
    │
    └─> ExperimentManager.compare_groups(experiment_id)
            │
            ├─> [4-1] 각 그룹의 EvaluationRun 조회
            │       │
            │       └─> StorageAdapter.get_run(run_id) 여러 번 호출
            │
            ├─> [4-2] 메트릭별 평균 점수 계산
            │       │
            │       ├─> control 그룹: avg_faithfulness = 0.85
            │       └─> variant_a 그룹: avg_faithfulness = 0.92
            │
            └─> [4-3] MetricComparison 생성
                    │
                    ├─> best_group: "variant_a"
                    └─> improvement: 8.2% 향상
```

### 5.4 다른 기능과의 연계

- **Storage Adapter**: 실험 및 그룹 정보 저장, 실행 결과 조회
- **RagasEvaluator**: 그룹별 평가 실행
- **CLI**: `experiment-create`, `experiment-add-group`, `experiment-compare` 명령어

---

## 6. 도메인 메모리 계층화 (Domain Memory Layering)

### 6.1 역할 및 책임

**Domain Memory**는 평가 결과에서 학습하여 도메인 지식을 축적하고, 다음 평가에 반영하는 학습 피드백 루프를 제공합니다.

**주요 책임:**
- **Factual Layer**: 검증된 도메인 사실 저장 (SPO 트리플)
- **Experiential Layer**: 평가에서 학습된 패턴 저장 (신뢰도, 실패 패턴)
- **Working Layer**: 현재 세션의 활성 컨텍스트 관리
- **Dynamics**: Formation (형성), Evolution (진화), Retrieval (검색)

### 6.2 메모리 계층 구조

```
Domain Memory Layers
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────┐
│  Factual Layer (정적, 검증된 사실)                       │
│  ├── 용어 사전 (terms_dictionary.json)                   │
│  ├── 규정 문서 (regulatory_rules.md)                     │
│  └── 검증된 사실 DB (factual_facts 테이블)              │
│      └── SPO 트리플: (subject, predicate, object)      │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Experiential Layer (학습된 패턴)                        │
│  ├── 엔티티 타입별 신뢰도 (entity_type_reliability)      │
│  ├── 관계 타입별 신뢰도 (relation_type_reliability)     │
│  ├── 실패 패턴 (failed_patterns)                        │
│  └── 행동 핸드북 (behavior_handbook)                     │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Working Layer (런타임 컨텍스트)                         │
│  ├── 세션 캐시 (session_cache.db)                        │
│  ├── 활성 엔티티 집합 (active_entities)                  │
│  └── 실시간 품질 지표 (quality_metrics)                 │
└─────────────────────────────────────────────────────────┘
```

### 6.3 Dynamics (동작 메커니즘)

#### 6.3.1 Formation (형성)

**역할:** 평가 결과에서 메모리 형성

**프로세스:**
```python
# 평가 완료 후 자동 호출
DomainLearningHook.on_evaluation_complete(evaluation_run)
    │
    ├─> [1] 사실 추출
    │       │
    │       └─> extract_facts_from_evaluation()
    │               │
    │               ├─> faithfulness >= 0.7인 결과에서 SPO 트리플 추출
    │               └─> FactualFact로 저장
    │
    ├─> [2] 패턴 추출
    │       │
    │       └─> extract_patterns_from_evaluation()
    │               │
    │               ├─> 엔티티 타입별 신뢰도 계산
    │               ├─> 관계 타입별 신뢰도 계산
    │               └─> LearningMemory로 저장
    │
    └─> [3] 행동 추출 (Metacognitive Reuse)
            │
            └─> extract_behaviors_from_evaluation()
                    │
                    └─> 높은 점수 테스트 케이스에서 재사용 가능한 행동 추출
                            └─> BehaviorEntry로 저장
```

#### 6.3.2 Evolution (진화)

**역할:** 메모리 통합, 업데이트, 망각

**프로세스:**
```python
# 주기적으로 실행
DomainMemoryAdapter.evolution_dynamics()
    │
    ├─> [1] consolidate_facts()
    │       │
    │       └─> 동일 SPO 트리플 병합
    │               ├─> verification_score 평균화
    │               └─> verification_count 합산
    │
    ├─> [2] resolve_conflict()
    │       │
    │       └─> 충돌하는 사실 해결
    │               └─> 우선순위: score × log(count+1) × recency
    │
    ├─> [3] forget_obsolete()
    │       │
    │       └─> 오래되거나 신뢰도 낮은 메모리 삭제
    │               └─> 조건: (age > 90일 AND count < 1) OR score < 0.3
    │
    └─> [4] decay_verification_scores()
            │
            └─> 시간에 따른 검증 점수 감소
                    └─> 7일 이상 검증되지 않은 사실에 적용
```

#### 6.3.3 Retrieval (검색)

**역할:** 하이브리드 검색 (키워드 + 의미론적)

**프로세스:**
```python
# 엔티티 추출 시 호출
DomainMemoryAdapter.hybrid_search(query, domain, language)
    │
    ├─> [1] search_facts() (FTS5 기반)
    │       │
    │       └─> BM25 랭킹으로 관련 사실 검색
    │
    ├─> [2] search_behaviors() (FTS5 + regex)
    │       │
    │       └─> 컨텍스트에 적용 가능한 행동 검색
    │
    └─> [3] search_learnings() (패턴 매칭)
            │
            └─> 최근 학습 패턴 검색
```

### 6.4 Forms (형태)

#### 6.4.1 Planar Form (KG 통합)

**역할:** Knowledge Graph와 사실 연결

**프로세스:**
```python
# KG 엔티티와 사실 연결
DomainMemoryAdapter.link_fact_to_kg(fact_id, kg_entity_id)
    │
    └─> fact_kg_bindings 테이블에 연결 정보 저장
            │
            └─> KG 탐색 시 관련 사실 자동 조회 가능
```

#### 6.4.2 Hierarchical Form (요약 계층)

**역할:** 사실의 계층 구조 (원본 → 요약 → 메타 요약)

**프로세스:**
```python
# 여러 사실을 요약하는 상위 사실 생성
DomainMemoryAdapter.create_summary_fact(
    child_fact_ids=["fact-1", "fact-2", "fact-3"],
    summary_subject="보험료",
    summary_predicate="요약",
    summary_object="납입 관련 정보"
)
    │
    └─> abstraction_level=1인 요약 사실 생성
            │
            └─> fact_hierarchy 테이블에 계층 관계 저장
```

### 6.5 유즈케이스에서의 위치

**중요: 학습 피드백 루프의 실제 작동 방식**

Ragas 평가 자체는 매번 동일한 프롬프트를 사용합니다. 학습 피드백 루프는 **평가가 아닌 다른 컴포넌트**에서 작동합니다:

1. **KG 생성 및 테스트셋 생성**: EntityExtractor가 학습된 패턴을 사용
2. **도메인 지식 축적**: 평가 결과에서 검증된 사실 추출
3. **패턴 학습**: 엔티티 타입별 신뢰도, 실패 패턴 학습

```
학습 피드백 루프 유즈케이스 (실제 작동 방식)
═══════════════════════════════════════════════════════════════

[시나리오 1: KG 기반 테스트셋 생성 개선]

[평가 #1] (초기 KG 생성)
    │
    ├─> [1] 문서에서 KG 생성
    │       │
    │       └─> KnowledgeGraphGenerator.build_graph(documents)
    │               │
    │               └─> EntityExtractor.extract_entities()
    │                       │
    │                       └─> 기본 신뢰도 사용 (organization=0.95, product=0.9)
    │
    ├─> [2] KG로 테스트셋 생성
    │       │
    │       └─> KnowledgeGraphGenerator.generate_questions()
    │
    ├─> [3] 테스트셋으로 평가 실행
    │       │
    │       └─> RagasEvaluator.evaluate()  [Ragas는 동일한 프롬프트 사용]
    │
    └─> [4] 메모리 형성 (Formation)
            │
            └─> DomainLearningHook.on_evaluation_complete()
                    │
                    ├─> 엔티티 타입별 신뢰도 계산
                    │       │
                    │       └─> 예: "organization" 타입이 추출된 케이스의
                    │               평균 faithfulness = 0.92
                    │               → entity_type_reliability["organization"] = 0.92
                    │
                    └─> LearningMemory 저장

[평가 #2] (학습된 패턴 적용)
    │
    ├─> [1] 문서에서 KG 생성 (개선된 추출기 사용)
    │       │
    │       └─> KnowledgeGraphGenerator.build_graph(documents)
    │               │
    │               └─> EntityExtractor.extract_entities()
    │                       │
    │                       └─> DomainMemoryAdapter.get_aggregated_reliability()
    │                               │
    │                               └─> 학습된 신뢰도 점수 조회
    │                                       │
    │                                       └─> "organization" = 0.92 (평가 #1에서 학습)
    │                                               │
    │                                               └─> 가중치 적용:
    │                                                       base_confidence = 0.95
    │                                                       weight = 0.92
    │                                                       final_confidence = 0.95 * 0.92 = 0.874
    │
    ├─> [2] 더 정확한 KG 생성
    │       │
    │       └─> 신뢰도가 높은 엔티티만 포함 → 더 정확한 관계 추출
    │
    ├─> [3] 더 나은 테스트셋 생성
    │       │
    │       └─> 정확한 KG → 더 관련성 높은 질문 생성
    │
    └─> [4] 평가 실행 (더 나은 테스트셋으로)
            │
            └─> RagasEvaluator.evaluate()  [여전히 동일한 프롬프트 사용]
                    │
                    └─> 하지만 더 나은 테스트셋으로 평가 → 더 나은 결과

[시나리오 2: 도메인 지식 축적]

[평가 #1]
    │
    └─> DomainLearningHook.on_evaluation_complete()
            │
            └─> extract_facts_from_evaluation()
                    │
                    ├─> faithfulness >= 0.7인 결과에서 SPO 트리플 추출
                    │       │
                    │       └─> 예: ("삼성생명", "PROVIDES", "종신보험")
                    │
                    └─> FactualFact 저장

[평가 #2] (누적된 지식 활용)
    │
    └─> KG 생성 시
            │
            └─> DomainMemoryAdapter.search_facts("삼성생명")
                    │
                    └─> 이전 평가에서 검증된 사실 조회
                            │
                            └─> KG 생성 시 참고하여 더 정확한 관계 추출

[핵심 포인트]
═══════════════════════════════════════════════════════════════

1. Ragas 평가 자체는 학습하지 않음 (고정된 프롬프트)
2. 학습은 평가 결과를 분석하여 패턴 추출
3. 학습된 패턴은 다음 KG 생성/테스트셋 생성에 적용
4. 더 나은 테스트셋 → 더 나은 평가 결과 (간접적 개선)
```

### 6.6 다른 기능과의 연계

- **RagasEvaluator**: 평가 완료 후 `DomainLearningHook` 호출
- **EntityExtractor**: 학습된 신뢰도 점수 적용
- **KG Generator**: Planar Form으로 KG 엔티티와 사실 연결
- **CLI**: `domain init`, `domain list`, `domain terms` 명령어

---

## 7. NLP 분석 (NLP Analysis)

### 7.1 역할 및 책임

**NLPAnalysisAdapter**는 평가 결과의 텍스트를 분석하여 질문 유형, 키워드, 토픽 등을 추출합니다.

**주요 책임:**
- 텍스트 기본 통계 계산 (문자 수, 단어 수, 문장 수)
- 질문 유형 분류 (FACTUAL, REASONING, COMPARATIVE, PROCEDURAL, OPINION)
- TF-IDF 기반 키워드 추출
- 토픽 클러스터링 (선택적)

### 7.2 핵심 기능

#### 7.2.1 텍스트 통계

```python
TextStats(
    char_count=1250,           # 총 문자 수
    word_count=180,            # 총 단어 수
    sentence_count=12,         # 총 문장 수
    avg_word_length=6.9,       # 평균 단어 길이
    unique_word_ratio=0.65    # 어휘 다양성 (고유 단어 비율)
)
```

**의미:** 데이터셋의 텍스트 복잡도 및 다양성 파악

#### 7.2.2 질문 유형 분류

```python
QuestionTypeStats(
    question_type=QuestionType.FACTUAL,  # 사실형
    count=45,                            # 45개 질문
    percentage=0.75,                     # 75% 비중
    avg_scores={
        "faithfulness": 0.88,            # 사실형 질문의 평균 faithfulness
        "answer_relevancy": 0.82
    }
)
```

**질문 유형:**
- **FACTUAL**: "무엇", "언제", "어디", "누가" (what, when, where, who)
- **REASONING**: "왜", "어떻게" (why, how)
- **COMPARATIVE**: "비교", "차이" (compare, difference)
- **PROCEDURAL**: "방법", "절차", "단계" (how to, steps)
- **OPINION**: "생각", "의견" (opinion, think)

**의미:** 질문 유형별 성능 차이 분석

#### 7.2.3 키워드 추출

```python
KeywordInfo(
    keyword="보험료",
    frequency=23,              # 23번 등장
    tfidf_score=0.85,         # TF-IDF 점수
    avg_metric_scores={
        "faithfulness": 0.91   # 이 키워드 포함 케이스의 평균 점수
    }
)
```

**의미:** 중요한 키워드 식별 및 키워드-성능 상관관계 분석

### 7.3 유즈케이스에서의 위치

```
NLP 분석 유즈케이스
═══════════════════════════════════════════════════════════════

[평가 실행 후]
    │
    └─> AnalysisService.analyze_run(
            run=evaluation_run,
            include_nlp=True
        )
            │
            └─> NLPAnalysisAdapter.analyze(run)
                    │
                    ├─> [1] 텍스트 통계 계산
                    │       │
                    │       ├─> question_stats = _calculate_text_stats(questions)
                    │       ├─> answer_stats = _calculate_text_stats(answers)
                    │       └─> context_stats = _calculate_text_stats(contexts)
                    │
                    ├─> [2] 질문 유형 분류
                    │       │
                    │       └─> question_types = _classify_question_types(run)
                    │               │
                    │               └─> 규칙 기반 패턴 매칭 (LLM 호출 없음)
                    │
                    ├─> [3] 키워드 추출
                    │       │
                    │       └─> top_keywords = _extract_keywords_tfidf(
                    │               documents=[q + " " + a for q, a in zip(questions, answers)],
                    │               top_k=20
                    │           )
                    │
                    └─> [4] 인사이트 생성
                            │
                            └─> insights = _generate_insights(
                                    question_types, top_keywords
                                )
                                    │
                                    └─> 예: "FACTUAL 질문이 75%를 차지하며 평균 faithfulness가 0.88로 높음"
```

### 7.4 다른 기능과의 연계

- **AnalysisService**: NLP 분석 오케스트레이션
- **CausalAnalysis**: NLP 분석 결과를 인과 요인으로 활용
- **CLI**: `analyze --nlp` 옵션
- **Report Generator**: NLP 분석 결과를 보고서에 포함

---

## 8. 인과 분석 (Causal Analysis)

### 8.1 역할 및 책임

**CausalAnalysisAdapter**는 평가 결과에서 인과 관계를 분석하여 근본 원인을 파악하고 개선 제안을 생성합니다.

**주요 책임:**
- 인과 요인 추출 (질문 길이, 컨텍스트 수, 키워드 겹침 등)
- 요인-메트릭 영향 분석 (상관분석)
- 인과 관계 식별
- 근본 원인 분석
- 개선 제안 생성

### 8.2 핵심 개념

#### 8.2.1 인과 요인 (Causal Factors)

```python
CausalFactorType:
    - question_length        # 질문 길이 (단어 수)
    - answer_length          # 답변 길이 (단어 수)
    - context_count          # 컨텍스트 수
    - context_length         # 컨텍스트 총 길이
    - question_complexity    # 질문 복잡도
    - has_ground_truth       # ground_truth 존재 여부
    - keyword_overlap        # 질문-컨텍스트 키워드 겹침
```

#### 8.2.2 요인-메트릭 영향

```python
FactorImpact(
    factor_type=CausalFactorType.question_length,
    metric_name="faithfulness",
    impact_direction=ImpactDirection.NEGATIVE,  # 음의 상관관계
    impact_strength=ImpactStrength.MODERATE,    # 중간 강도
    correlation_coefficient=-0.45,              # 상관계수
    p_value=0.02,                              # 유의수준
    is_significant=True,                        # 유의미한 영향
    stratified_groups={
        "low": StratifiedGroup(avg_score=0.92, count=15),
        "medium": StratifiedGroup(avg_score=0.85, count=20),
        "high": StratifiedGroup(avg_score=0.78, count=10)
    }
)
```

**의미:** 질문이 길수록 faithfulness 점수가 낮아지는 경향

#### 8.2.3 근본 원인 분석

```python
RootCause(
    metric_name="faithfulness",
    primary_causes=[
        CausalFactorType.question_length,      # 주요 원인 1
        CausalFactorType.keyword_overlap       # 주요 원인 2
    ],
    contributing_factors=[
        CausalFactorType.context_count
    ],
    explanation="질문 길이와 키워드 겹침이 faithfulness에 가장 큰 영향을 미침"
)
```

#### 8.2.4 개선 제안

```python
InterventionSuggestion(
    metric_name="faithfulness",
    suggestion="긴 질문을 여러 개의 짧은 질문으로 분할",
    expected_effect="faithfulness 점수 5-10% 향상 예상",
    priority=1,  # 높은 우선순위
    related_factors=[CausalFactorType.question_length]
)
```

### 8.3 유즈케이스에서의 위치

```
인과 분석 유즈케이스
═══════════════════════════════════════════════════════════════

[평가 실행 후]
    │
    └─> AnalysisService.analyze_run(
            run=evaluation_run,
            include_causal=True
        )
            │
            └─> CausalAnalysisAdapter.analyze_causality(run)
                    │
                    ├─> [1] 요인 추출
                    │       │
                    │       └─> factors = _extract_factors(run)
                    │               │
                    │               ├─> 각 테스트 케이스에서 요인값 계산
                    │               └─> 예: question_length = len(question.split())
                    │
                    ├─> [2] 요인별 통계 계산
                    │       │
                    │       └─> factor_stats = _calculate_factor_stats(factors)
                    │               │
                    │               └─> 각 요인의 분포, 평균, 표준편차 계산
                    │
                    ├─> [3] 요인-메트릭 영향 분석
                    │       │
                    │       └─> factor_impacts = _analyze_factor_impacts(
                    │               factors, metric_scores, significance_level=0.05
                    │           )
                    │               │
                    │               ├─> 상관분석 (Pearson, Spearman)
                    │               ├─> 계층화 분석 (low/medium/high 그룹)
                    │               └─> 통계적 유의성 검정 (p-value)
                    │
                    ├─> [4] 인과 관계 식별
                    │       │
                    │       └─> causal_relationships = _identify_causal_relationships(
                    │               factor_impacts, sample_size
                    │           )
                    │               │
                    │               └─> 유의미한 영향만 필터링하여 인과 관계로 간주
                    │
                    ├─> [5] 근본 원인 분석
                    │       │
                    │       └─> root_causes = _analyze_root_causes(
                    │               factor_impacts, metrics
                    │           )
                    │               │
                    │               └─> 메트릭별로 영향력이 큰 요인들을 주요 원인으로 식별
                    │
                    └─> [6] 개선 제안 생성
                            │
                            └─> interventions = _generate_interventions(
                                    factor_impacts, root_causes, thresholds
                                )
                                    │
                                    └─> 근본 원인에 대한 구체적인 개선 방안 제시
```

### 8.4 다른 기능과의 연계

- **AnalysisService**: 인과 분석 오케스트레이션
- **NLP Analysis**: 질문 유형, 키워드 등을 인과 요인으로 활용
- **CLI**: `analyze --causal` 옵션
- **Report Generator**: 인과 분석 결과를 보고서에 포함

---

## 9. 지식 그래프 (Knowledge Graph)

### 9.1 역할 및 책임

**KnowledgeGraphGenerator**는 문서에서 엔티티와 관계를 추출하여 지식 그래프를 구축하고, 그래프를 탐색하여 테스트셋을 생성합니다.

**주요 책임:**
- 문서에서 엔티티 추출 (EntityExtractor 사용)
- 문서에서 관계 추출
- 지식 그래프 구축 (NetworkX 기반)
- 그래프 탐색을 통한 질문 생성

### 9.2 핵심 개념

#### 9.2.1 엔티티 및 관계 모델

```python
EntityModel(
    name="삼성생명",
    entity_type="COMPANY",
    confidence=0.95,
    source_document="doc-1"
)

RelationModel(
    source="삼성생명",
    target="종신보험",
    relation_type="PROVIDES",
    confidence=0.88
)
```

#### 9.2.2 지식 그래프 구조

```python
KnowledgeGraph (NetworkX MultiDiGraph)
    │
    ├─> Nodes: EntityModel (엔티티)
    │       ├─> Attributes: entity_type, confidence, source_document
    │       └─> Metadata: EntityModel 객체
    │
    └─> Edges: RelationModel (관계)
            ├─> Attributes: relation_type, confidence
            └─> Metadata: RelationModel 객체
```

### 9.3 유즈케이스에서의 위치

```
KG 기반 테스트셋 생성 유즈케이스
═══════════════════════════════════════════════════════════════

[1] 문서 입력
    │
    └─> documents = ["삼성생명의 종신보험은...", "한화생명의 암보험은..."]

[2] 지식 그래프 구축
    │
    └─> KnowledgeGraphGenerator.build_graph(documents)
            │
            ├─> [2-1] 엔티티 추출
            │       │
            │       └─> EntityExtractor.extract_entities(doc)
            │               │
            │               ├─> "삼성생명" (COMPANY, confidence=0.95)
            │               ├─> "종신보험" (PRODUCT, confidence=0.92)
            │               └─> "한화생명" (COMPANY, confidence=0.94)
            │
            ├─> [2-2] 관계 추출
            │       │
            │       └─> EntityExtractor.extract_relations(doc, entities)
            │               │
            │               ├─> ("삼성생명", "PROVIDES", "종신보험")
            │               └─> ("한화생명", "PROVIDES", "암보험")
            │
            └─> [2-3] 그래프에 추가
                    │
                    └─> KnowledgeGraph.add_entity(), add_relation()

[3] 질문 생성
    │
    └─> KnowledgeGraphGenerator.generate_questions(num_questions=10)
            │
            ├─> [3-1] 그래프 탐색 전략 선택
            │       │
            │       ├─> Direct Relation: 엔티티의 직접 관계 탐색
            │       ├─> Path Traversal: 2-hop 경로 탐색
            │       └─> Random Walk: 랜덤 워크
            │
            ├─> [3-2] 질문 템플릿 적용
            │       │
            │       ├─> "What is {entity}?" → "What is 종신보험?"
            │       ├─> "What does {source} {relation}?" → "What does 삼성생명 provide?"
            │       └─> "What is the relationship between {source} and {target}?"
            │
            └─> [3-3] TestCase 생성
                    │
                    └─> TestCase(
                            question="삼성생명이 제공하는 보험은 무엇인가요?",
                            answer="종신보험",
                            contexts=[원본 문서 청크],
                            ground_truth="종신보험"
                        )

[4] Dataset 생성
    │
    └─> KnowledgeGraphGenerator.generate_dataset(
            num_questions=10,
            name="insurance-kg-testset",
            version="1.0.0"
        )
            │
            └─> Dataset(test_cases=[...])
```

### 9.4 다른 기능과의 연계

- **EntityExtractor**: 엔티티 및 관계 추출
- **Domain Memory**: Planar Form으로 KG 엔티티와 사실 연결
- **RagasEvaluator**: KG로 생성된 테스트셋 평가
- **CLI**: `generate --method knowledge_graph` 명령어

---

## 10. 기능 간 상호작용 및 데이터 흐름

### 10.1 전체 평가 파이프라인

```
전체 평가 파이프라인
═══════════════════════════════════════════════════════════════

[입력] Dataset (JSON/CSV/Excel)
    │
    ▼
[1] CLI Adapter
    │  - 명령 파싱 및 검증
    │  - 설정 로드 (Settings, ModelConfig)
    │
    ├─> Dataset Loader (CSV/Excel/JSON)
    │       └─> Dataset 엔티티 생성
    │
    ├─> LLM Adapter Factory
    │       └─> LLMPort 구현체 생성 (OpenAI/Anthropic/Ollama)
    │
    └─> RagasEvaluator.evaluate()
            │
            ├─> Ragas 메트릭 실행
            │       └─> LLMPort.as_ragas_llm() 호출
            │
            ├─> 커스텀 메트릭 실행
            │       └─> InsuranceTermAccuracy 등
            │
            └─> EvaluationRun 생성
                    │
                    ├─> StorageAdapter.save_run()  [저장]
                    ├─> TrackerAdapter.log_evaluation_run()  [추적]
                    └─> DomainLearningHook.on_evaluation_complete()  [학습]
                            │
                            ├─> FactualFact 추출 및 저장
                            ├─> LearningMemory 추출 및 저장
                            └─> BehaviorEntry 추출 및 저장
    │
    ▼
[2] Analysis Service
    │
    ├─> StatisticalAnalysisAdapter.analyze_statistics()
    │       └─> 기본 통계 (평균, 표준편차, 통과율)
    │
    ├─> NLPAnalysisAdapter.analyze()  [선택적]
    │       ├─> 텍스트 통계
    │       ├─> 질문 유형 분류
    │       └─> 키워드 추출
    │
    └─> CausalAnalysisAdapter.analyze_causality()  [선택적]
            ├─> 인과 요인 추출
            ├─> 요인-메트릭 영향 분석
            ├─> 근본 원인 분석
            └─> 개선 제안 생성
    │
    ▼
[3] 결과 출력
    │
    ├─> CLI 표시 (Rich 테이블)
    ├─> JSON 파일 저장
    ├─> Markdown/HTML 보고서 생성
    └─> Langfuse/MLflow UI에서 조회
```

### 10.2 학습 피드백 루프

```
학습 피드백 루프
═══════════════════════════════════════════════════════════════

평가 #N
    │
    ├─> [1] 평가 실행
    │       └─> RagasEvaluator.evaluate()
    │
    ├─> [2] 메모리 형성 (Formation)
    │       └─> DomainLearningHook.on_evaluation_complete()
    │               ├─> 사실 추출 → FactualFact
    │               ├─> 패턴 추출 → LearningMemory
    │               └─> 행동 추출 → BehaviorEntry
    │
    ├─> [3] 메모리 진화 (Evolution)
    │       └─> DomainMemoryAdapter.evolution_dynamics()
    │               ├─> consolidate_facts()  # 중복 병합
    │               ├─> resolve_conflict()   # 충돌 해결
    │               ├─> forget_obsolete()    # 오래된 메모리 삭제
    │               └─> decay_verification_scores()  # 점수 감소
    │
    └─> [4] 메모리 검색 (Retrieval)
            └─> DomainMemoryAdapter.get_reliability_scores()
                    └─> 엔티티 타입별 신뢰도 점수 반환

평가 #N+1 (학습된 메모리 적용)
    │
    ├─> [1] EntityExtractor 초기화
    │       └─> DomainMemoryAdapter.get_reliability_scores() 호출
    │               └─> 엔티티 타입별 가중치 설정
    │
    ├─> [2] 평가 실행 (개선된 추출기 사용)
    │       └─> EntityExtractor.extract_entities()
    │               └─> 학습된 가중치 적용 → 더 정확한 추출
    │
    └─> [3] 결과 비교
            └─> 평가 #N+1의 정확도 > 평가 #N의 정확도
                    └─> 학습 피드백 루프 성공
```

### 10.3 실험 관리 흐름

```
A/B 테스트 실험 흐름
═══════════════════════════════════════════════════════════════

[1] 실험 생성
    └─> ExperimentManager.create_experiment()
            └─> StorageAdapter.save_experiment()

[2] 그룹 추가
    └─> Experiment.add_group("control", "variant_a")

[3] 그룹별 평가 실행
    │
    ├─> [3-1] Control 그룹
    │       └─> RagasEvaluator.evaluate(model="gpt-3.5")
    │               └─> run_id_1 = StorageAdapter.save_run()
    │
    └─> [3-2] Variant A 그룹
            └─> RagasEvaluator.evaluate(model="gpt-4")
                    └─> run_id_2 = StorageAdapter.save_run()

[4] 그룹에 실행 추가
    │
    ├─> Experiment.add_run_to_group("control", run_id_1)
    └─> Experiment.add_run_to_group("variant_a", run_id_2)

[5] 그룹 비교
    └─> ExperimentManager.compare_groups(experiment_id)
            │
            ├─> StorageAdapter.get_run(run_id_1)  # Control 그룹
            ├─> StorageAdapter.get_run(run_id_2)  # Variant A 그룹
            │
            ├─> 메트릭별 평균 점수 계산
            │       ├─> Control: avg_faithfulness = 0.85
            │       └─> Variant A: avg_faithfulness = 0.92
            │
            └─> MetricComparison 생성
                    ├─> best_group: "variant_a"
                    └─> improvement: 8.2% 향상
```

### 10.4 분석 파이프라인

```
분석 파이프라인
═══════════════════════════════════════════════════════════════

[입력] EvaluationRun (저장된 실행 결과)
    │
    ▼
[1] AnalysisService.analyze_run()
    │
    ├─> [1-1] 캐시 조회 (선택적)
    │       └─> AnalysisCacheAdapter.get(cache_key)
    │
    ├─> [1-2] 통계 분석 (항상 수행)
    │       └─> StatisticalAnalysisAdapter.analyze_statistics()
    │               ├─> MetricStats (평균, 표준편차, 최소/최대)
    │               ├─> LowPerformerInfo (저성능 케이스)
    │               └─> CorrelationInsight (메트릭 간 상관관계)
    │
    ├─> [1-3] NLP 분석 (선택적)
    │       └─> NLPAnalysisAdapter.analyze()
    │               ├─> TextStats (질문/답변/컨텍스트 통계)
    │               ├─> QuestionTypeStats (질문 유형별 통계)
    │               └─> KeywordInfo (TF-IDF 키워드)
    │
    └─> [1-4] 인과 분석 (선택적)
            └─> CausalAnalysisAdapter.analyze_causality()
                    ├─> FactorImpact (요인-메트릭 영향)
                    ├─> CausalRelationship (인과 관계)
                    ├─> RootCause (근본 원인)
                    └─> InterventionSuggestion (개선 제안)
    │
    ▼
[2] AnalysisBundle 생성
    │
    └─> AnalysisBundle(
            statistical=StatisticalAnalysis,
            nlp=NLPAnalysis | None,
            causal=CausalAnalysis | None
        )
    │
    ▼
[3] 결과 출력
    │
    ├─> CLI 표시 (Rich 테이블)
    ├─> JSON 파일 저장
    ├─> Markdown/HTML 보고서 생성
    └─> StorageAdapter.save_analysis()  [선택적]
```

---

## 11. 요약 및 핵심 인사이트

### 11.1 각 기능의 고유 가치

| 기능 | 고유 가치 | 차별화 포인트 |
|------|----------|--------------|
| **RagasEvaluator** | RAG 품질 정량 측정 | Ragas 메트릭 + 커스텀 메트릭 통합 |
| **Storage Adapter** | 평가 결과 영속성 | SQLite/PostgreSQL 이중 지원 |
| **Tracker Adapter** | 관찰성 제공 | Langfuse/MLflow 통합 |
| **Experiment Manager** | A/B 테스트 지원 | 그룹 간 메트릭 비교 자동화 |
| **Domain Memory** | 학습 피드백 루프 | 평가에서 학습하여 지속적 개선 |
| **NLP Analysis** | 텍스트 인사이트 | 질문 유형, 키워드, 토픽 분석 |
| **Causal Analysis** | 근본 원인 분석 | 요인-메트릭 인과 관계 식별 |
| **Knowledge Graph** | 구조화된 테스트셋 생성 | 문서 → KG → 질문 자동 생성 |

### 11.2 기능 간 시너지

1. **Domain Memory + EntityExtractor**: 학습된 패턴을 추출기에 적용하여 정확도 향상
2. **NLP Analysis + Causal Analysis**: 질문 유형, 키워드를 인과 요인으로 활용
3. **Knowledge Graph + Domain Memory**: KG 엔티티와 사실을 Planar Form으로 연결
4. **Experiment Manager + Storage Adapter**: 그룹별 실행 결과를 효율적으로 조회
5. **Tracker Adapter + Storage Adapter**: 추적 ID를 저장하여 외부 시스템과 연결

### 11.3 전체 시스템의 가치 제안

```
EvalVault = RAGAS 래퍼 + 학습 시스템 + 분석 플랫폼

핵심 차별화:
1. 학습 피드백 루프 (Domain Memory)
   └─> 사용할수록 정확도 향상

2. 종합 분석 (NLP + Causal)
   └─> 단순 점수가 아닌 인사이트 제공

3. 실험 관리 (A/B 테스트)
   └─> 모델/프롬프트 비교 자동화

4. 구조화된 테스트셋 생성 (KG)
   └─> 문서에서 자동으로 평가 데이터 생성
```

---

## 부록: 주요 파일 위치

### Core System
- `src/evalvault/domain/services/evaluator.py` - RagasEvaluator
- `src/evalvault/domain/services/experiment_manager.py` - ExperimentManager
- `src/evalvault/domain/services/analysis_service.py` - AnalysisService

### Storage
- `src/evalvault/adapters/outbound/storage/sqlite_adapter.py` - SQLiteStorageAdapter
- `src/evalvault/adapters/outbound/storage/postgres_adapter.py` - PostgreSQLStorageAdapter

### Tracker
- `src/evalvault/adapters/outbound/tracker/langfuse_adapter.py` - LangfuseAdapter
- `src/evalvault/adapters/outbound/tracker/mlflow_adapter.py` - MLflowAdapter

### Domain Memory
- `src/evalvault/domain/entities/memory.py` - 메모리 엔티티
- `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py` - SQLiteDomainMemoryAdapter
- `src/evalvault/domain/services/domain_learning_hook.py` - DomainLearningHook

### NLP Analysis
- `src/evalvault/adapters/outbound/analysis/nlp_adapter.py` - NLPAnalysisAdapter
- `src/evalvault/domain/entities/analysis.py` - NLPAnalysis 엔티티

### Causal Analysis
- `src/evalvault/adapters/outbound/analysis/causal_adapter.py` - CausalAnalysisAdapter
- `src/evalvault/domain/entities/analysis.py` - CausalAnalysis 엔티티

### Knowledge Graph
- `src/evalvault/domain/services/kg_generator.py` - KnowledgeGraphGenerator
- `src/evalvault/domain/services/entity_extractor.py` - EntityExtractor

---

**문서 끝**
