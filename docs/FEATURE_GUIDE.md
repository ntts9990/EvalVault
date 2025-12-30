# EvalVault 기능 가이드

> **문서 버전**: 1.0.0
> **최종 업데이트**: 2025-12-30
> **목적**: EvalVault의 전체 기능, 아키텍처, 고급 분석 기능 통합 안내
>
> *이 문서는 기존 FEATURE_OVERVIEW.md, FEATURE_CATALOG.md, ADVANCED_FEATURES.md를 통합한 문서입니다.*

---

## EvalVault란?

**EvalVault는 RAG 솔루션이 아닙니다.**

EvalVault는 기존 RAG 시스템의 성능을 **측정, 분석, 시각화**하여 개선 방향을 제시하는 **평가 전문 도구**입니다.

```
┌─────────────────────────────────────────────────────────────┐
│                     EvalVault의 역할                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   고객의 RAG 시스템  →  EvalVault  →  분석 결과 & 인사이트   │
│   (측정 대상)           (분석 도구)     (제공 가치)           │
│                                                             │
│   제공하는 것:                                               │
│   ✅ 객관적인 성능 측정 데이터                               │
│   ✅ 병목 지점과 개선 영역 분석                              │
│   ✅ A/B 테스트 및 실험 비교                                 │
│   ✅ 시각화된 대시보드                                       │
│   ✅ 액션 가능한 보고서                                      │
│                                                             │
│   제공하지 않는 것:                                          │
│   ❌ RAG 파이프라인 구현                                     │
│   ❌ 벡터 데이터베이스                                       │
│   ❌ 프로덕션 검색 서비스                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 핵심 가치 제안

| 가치 | 설명 | 제공 형태 |
|------|------|----------|
| **측정** | RAG 품질을 객관적 수치로 측정 | 7개 표준 메트릭 |
| **분석** | 성능 저하 원인과 개선점 도출 | 인과 분석 보고서 |
| **비교** | 변경 전후 효과 검증 | A/B 테스트 프레임워크 |
| **추적** | 품질 변화 모니터링 | 대시보드 & 히스토리 |
| **보고** | 의사결정 지원 자료 | HTML/Markdown 리포트 |

---

## 전체 아키텍처 개요

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
│      └─> Knowledge Graph Update (KG 기반 테스트셋 개선)         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 기능 카테고리

### Category A: 품질 측정 (Quality Metrics)

고객의 RAG 시스템이 얼마나 잘 작동하는지 **객관적으로 측정**합니다.

| 메트릭 | 측정 대상 | 인사이트 제공 |
|--------|----------|--------------|
| **Faithfulness** | 답변이 컨텍스트에 근거하는가? | 환각(Hallucination) 발생률 및 패턴 |
| **Answer Relevancy** | 답변이 질문에 적절한가? | 사용자 만족도 예측 지표 |
| **Context Precision** | 검색 결과 순위가 적절한가? | 검색 랭킹 알고리즘 효과성 |
| **Context Recall** | 필요한 정보가 검색되었는가? | 검색 커버리지 분석 |
| **Factual Correctness** | 사실 관계가 정확한가? | Ground truth 대비 정확도 |
| **Semantic Similarity** | 의미적으로 유사한가? | 답변 품질 일관성 |
| **InsuranceTermAccuracy** | 전문용어가 정확한가? | 도메인 특화 품질 분석 |

### Category B: 검색 성능 벤치마킹 (Retrieval Benchmarking)

고객의 **검색 전략 효과를 측정**하고 최적 전략을 찾도록 돕습니다.

| 분석 항목 | 측정 내용 | 제공 인사이트 |
|----------|----------|--------------|
| **검색 전략 비교** | BM25 vs Dense vs Hybrid | 어떤 전략이 더 효과적인지 |
| **임베딩 모델 비교** | 다양한 임베딩 모델 성능 | 최적 임베딩 모델 추천 |
| **청킹 전략 분석** | 청크 크기/오버랩 영향 | 최적 청킹 설정 도출 |
| **Top-K 분석** | 검색 결과 수 영향 | 정확도-비용 균형점 |

### Category C: 분석 및 인사이트 (Analysis & Insights)

평가 결과에서 **액션 가능한 인사이트**를 도출합니다.

| 기능 | 제공 내용 | 가치 |
|------|----------|------|
| **NLP 분석** | 질문 유형 분류, 키워드 추출, 토픽 클러스터링 | 어떤 유형의 질문에서 문제가 발생하는가 |
| **인과 분석** | 근본 원인 파악, 개선 제안 | 왜 점수가 낮은지, 어떻게 개선할지 |
| **통계 분석** | 메트릭 분포, 상관관계 | 메트릭 간 관계 파악 |

### Category D: 실험 관리 (Experiment Management)

**A/B 테스트 및 실험 비교**를 통해 변경 효과를 검증합니다.

| 기능 | 제공 내용 | 가치 |
|------|----------|------|
| **실험 생성** | 그룹별 설정, 메타데이터 | 체계적인 실험 관리 |
| **그룹 비교** | 메트릭 차이, 통계적 유의성 | 변경이 실제로 효과적인지 검증 |
| **히스토리 추적** | 시간별 변화, 트렌드 | 품질 변화 모니터링 |

### Category E: 대시보드 및 모니터링 (Dashboard & Monitoring)

**시각화된 대시보드**로 품질 상태를 한눈에 파악합니다.

| 통합 | 제공 내용 | 가치 |
|------|----------|------|
| **Langfuse** | 트레이스 뷰, 스코어 히스토리, 비용 추적 | 실시간 모니터링 |
| **MLflow** | 실험 추적, 모델 비교, 아티팩트 관리 | ML 워크플로우 통합 |

### Category F: 테스트셋 생성 (Testset Generation)

**자동 테스트셋 생성**으로 평가 효율성을 높입니다.

| 기능 | 제공 내용 | 가치 |
|------|----------|------|
| **Basic Generator** | 문서에서 QA 쌍 생성 | 빠른 테스트셋 확보 |
| **KG Generator** | 지식 그래프 기반 생성 | 구조화된 테스트셋 |
| **다양성 옵션** | 질문 유형, 난이도 조절 | 포괄적인 테스트 커버리지 |

### Category G: 한국어 NLP 분석 (Korean NLP)

**한국어 특화 분석**으로 정확한 평가를 지원합니다.

| 기능 | 제공 내용 | 가치 |
|------|----------|------|
| **형태소 분석** | Kiwi 기반 토큰화 | 조사/어미 제거로 정확한 매칭 |
| **키워드 추출** | 의미 있는 키워드만 | 60% → 85% 정확도 향상 |
| **문장 청킹** | 의미 단위 청킹 | 컨텍스트 무결성 보장 |

---

## 고급 분석 기능 (Advanced Analytics)

### 우선순위 매트릭스

```
                        가치 (높음)
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
       │   Quick Wins       │   Strategic        │
       │   (즉시 가치)       │   (전략적 가치)     │
       │                    │                    │
       │  Quality Gate      │  Multi-Model       │
       │  Hallucination     │  Analysis          │
       │  Analysis          │  Golden Dataset    │
       │                    │  Curation          │
EFFORT ├────────────────────┼────────────────────┤ EFFORT
(낮음) │                    │                    │ (높음)
       │   Nice to Have     │   Research         │
       │   (부가 가치)       │   (연구 단계)       │
       │                    │                    │
       │  Strategy          │  KG Regression     │
       │  Analysis          │  Embedding         │
       │  Adaptive Eval     │  Analysis          │
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                        가치 (낮음)
```

### P0: 핵심 분석 기능

#### 1. Continuous Quality Gate

CI/CD 파이프라인을 위한 **자동화된 품질 검증 리포트**

```bash
# 사용 예시
evalvault run data.json --metrics faithfulness,answer_relevancy \
    --threshold faithfulness:0.8 --fail-on-threshold

# Exit Code
# 0: 모든 임계값 통과
# 1: 하나 이상 실패
```

#### 2. Hallucination Deep Analysis

환각(Hallucination) 발생 패턴을 **심층 분석**

- 환각 발생 케이스 자동 식별
- 환각 유형 분류 (사실 왜곡, 정보 추가, 컨텍스트 무시)
- 근본 원인 및 개선 제안

### P1: 확장 분석 기능

#### 3. Optimization Effect Analyzer

RAG 최적화 기법의 **효과를 측정**

```bash
# A/B 테스트로 효과 비교
evalvault experiment compare baseline optimized
```

#### 4. Retrieval Strategy Analysis

검색 전략별 성능을 **비교 분석**

- BM25 vs Dense vs Hybrid 효과 측정
- 질문 유형별 최적 전략 분석

### P2: 심화 분석 기능

#### 5. Multi-Model Comparison

여러 LLM 모델의 성능을 **비교 분석**

- 모델별 메트릭 비교
- 비용 대비 성능 분석
- 도메인별 최적 모델 추천

#### 6. Golden Dataset Curation

고품질 평가 데이터셋 **자동 큐레이션**

- 다양성 분석 및 권장
- 난이도 분포 최적화
- 커버리지 분석

---

## 핵심 기능 상세

### 1. RagasEvaluator

Ragas 라이브러리 기반 평가 엔진

```python
from evalvault.domain.services.evaluator import RagasEvaluator

evaluator = RagasEvaluator(
    metrics=["faithfulness", "answer_relevancy"],
    llm_adapter=openai_adapter,
    tracker=langfuse_adapter
)

run = evaluator.evaluate(dataset)
print(f"평균 Faithfulness: {run.metrics['faithfulness'].mean}")
```

### 2. Experiment Manager

A/B 테스트 및 실험 관리

```python
from evalvault.domain.services.experiment_manager import ExperimentManager

manager = ExperimentManager()
experiment = manager.create_experiment("model_comparison", ["gpt4", "claude"])

# 각 그룹 평가
manager.add_run_to_group(experiment.id, "gpt4", run_gpt4)
manager.add_run_to_group(experiment.id, "claude", run_claude)

# 비교 분석
comparison = manager.compare_groups(experiment.id, ["gpt4", "claude"])
```

### 3. Domain Memory

평가에서 학습한 도메인 지식 축적

```python
from evalvault.domain.services.domain_learning_hook import DomainLearningHook

hook = DomainLearningHook(memory_adapter)
hook.on_evaluation_complete(run, domain="insurance")

# 학습된 패턴 조회
reliability = memory_adapter.get_aggregated_reliability("organization")
# → 0.92 (organization 타입 엔티티의 신뢰도)
```

### 4. NLP Analysis

텍스트 분석 및 인사이트 도출

```python
from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter

nlp = NLPAnalysisAdapter()
analysis = nlp.analyze(run)

print(f"질문 유형 분포: {analysis.question_types}")
print(f"주요 키워드: {analysis.keywords}")
print(f"토픽 클러스터: {analysis.topics}")
```

### 5. Causal Analysis

근본 원인 분석 및 개선 제안

```python
from evalvault.adapters.outbound.analysis.causal_adapter import CausalAnalysisAdapter

causal = CausalAnalysisAdapter()
analysis = causal.analyze_causality(run)

print(f"근본 원인: {analysis.root_causes}")
print(f"개선 제안: {analysis.interventions}")
```

---

## CLI 사용 예시

```bash
# 기본 평가
evalvault run data.json --metrics faithfulness,answer_relevancy

# 병렬 처리
evalvault run data.json --parallel --batch-size 10

# 테스트셋 생성
evalvault generate docs.txt --method knowledge_graph -n 50

# 실험 비교
evalvault compare run_id_1 run_id_2

# 히스토리 조회
evalvault history --limit 10

# 결과 내보내기
evalvault export run_id --format html --output report.html
```

---

## 참고 문서

- [USER_GUIDE.md](USER_GUIDE.md) - 설치 및 시작 가이드
- [ARCHITECTURE.md](ARCHITECTURE.md) - 시스템 아키텍처 상세
- [KOREAN_RAG_OPTIMIZATION.md](KOREAN_RAG_OPTIMIZATION.md) - 한국어 최적화 가이드
- [RAG_OPTIMIZATION_GUIDE.md](RAG_OPTIMIZATION_GUIDE.md) - RAG 최적화 효과 측정 가이드

---

**문서 끝**
