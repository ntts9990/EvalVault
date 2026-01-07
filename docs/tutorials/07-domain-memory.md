# Domain Memory 활용 튜토리얼

> Domain Memory를 활용하여 평가 품질을 지속적으로 개선하는 방법

이 튜토리얼은 EvalVault의 Domain Memory 기능을 활용하여 과거 평가에서 학습한 지식을 향후 평가에 활용하는 방법을 설명합니다.

---

## 목차

1. [Domain Memory란?](#domain-memory란)
2. [기본 사용법](#기본-사용법)
3. [컨텍스트 보강](#컨텍스트-보강)
4. [메모리 기반 분석](#메모리-기반-분석)
5. [Python API 사용법](#python-api-사용법)
6. [고급 활용](#고급-활용)

---

## Domain Memory란?

Domain Memory는 평가 결과에서 학습한 지식을 축적하여 향후 평가에 활용하는 시스템입니다.

### 주요 기능

1. **Threshold 자동 조정**: 과거 평가에서 학습한 메트릭별 신뢰도 점수를 기반으로 평가 threshold를 자동으로 조정합니다.
2. **컨텍스트 보강**: 각 테스트 케이스의 질문과 관련된 사실을 검색하여 컨텍스트에 자동으로 추가합니다.
3. **트렌드 분석**: 과거 학습 메모리와 현재 평가 결과를 비교하여 트렌드를 분석합니다.
4. **행동 패턴 재사용**: 성공한 행동 패턴을 검색하여 재사용 가능한 액션 시퀀스를 제공합니다.

### 메모리 레이어

Domain Memory는 세 가지 레이어로 구성됩니다:

- **Factual Layer**: 검증된 도메인 사실 (SPO 트리플)
- **Experiential Layer**: 학습 메모리 (패턴, 신뢰도)
- **Behavior Layer**: 행동 패턴 엔트리

---

## 기본 사용법

### 1. Domain Memory를 활용한 평가 실행

가장 간단한 사용법은 `--use-domain-memory` 옵션을 사용하는 것입니다:

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --use-domain-memory \
  --memory-domain insurance \
  --memory-language ko
```

> Streaming 모드(`--stream`)에서는 Domain Memory를 사용할 수 없습니다.

**동작 원리**:
1. 과거 평가에서 학습한 메트릭별 신뢰도 점수 조회
2. 신뢰도 점수에 따라 threshold 자동 조정:
   - 신뢰도 < 0.6: threshold를 0.1 낮춤 (최소 0.5)
   - 신뢰도 > 0.85: threshold를 0.05 높임 (최대 0.95)
3. 조정된 threshold로 평가 실행

### 2. 메모리 데이터베이스 경로 지정

기본적으로 `data/db/evalvault_memory.db`를 사용하지만, 커스텀 경로를 지정할 수 있습니다:

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" \
  --use-domain-memory \
  --memory-db /path/to/custom_memory.db \
  --memory-domain insurance
```

### 3. 도메인 자동 감지

`--memory-domain` 옵션을 생략하면 데이터셋의 메타데이터에서 도메인을 자동으로 추출합니다:

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" \
  --use-domain-memory \
  --memory-language ko
```

---

## 컨텍스트 보강

각 테스트 케이스의 질문과 관련된 사실을 자동으로 컨텍스트에 추가할 수 있습니다.

### 기본 사용법

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" \
  --metrics faithfulness \
  --use-domain-memory \
  --augment-context \
  --memory-domain insurance \
  --memory-language ko
```

**동작 원리**:
1. 각 테스트 케이스의 질문으로 관련 사실 검색
2. 검색된 사실을 컨텍스트에 자동 추가
3. 형식: `[관련 사실]\n- 주체 관계 객체`

### 예제

**원본 컨텍스트**:
```
보험료는 연령, 성별, 보험 종류에 따라 달라집니다.
```

**보강된 컨텍스트**:
```
보험료는 연령, 성별, 보험 종류에 따라 달라집니다.

[관련 사실]
- 보험료 연령에 따라 증가
- 보험료 성별에 따라 차등 적용
- 보험료 보험 종류에 따라 달라짐
```

---

## 메모리 기반 분석

과거 학습 메모리와 현재 평가 결과를 비교하여 트렌드 분석 및 인사이트를 생성할 수 있습니다.

### Python 코드 예제

```python
from evalvault.domain.services.memory_based_analysis import MemoryBasedAnalysis
from evalvault.adapters.outbound.domain_memory.sqlite_adapter import SQLiteDomainMemoryAdapter

# 메모리 기반 분석 초기화
memory_adapter = SQLiteDomainMemoryAdapter("data/db/evalvault_memory.db")
analysis = MemoryBasedAnalysis(memory_adapter)

# 인사이트 생성
insights = analysis.generate_insights(
    evaluation_run=run,
    domain="insurance",
    language="ko",
    history_limit=10
)

print(insights)
# {
#   "trends": {
#     "faithfulness": {
#       "current": 0.85,
#       "baseline": 0.82,
#       "delta": 0.03
#     },
#     ...
#   },
#   "related_facts": [...],
#   "recommendations": [
#     "faithfulness 개선 중: 현재 전략을 유지하거나 확장하세요."
#   ]
# }
```

### 행동 패턴 재사용

성공한 행동 패턴을 검색하여 재사용 가능한 액션 시퀀스를 얻을 수 있습니다:

```python
# 성공한 행동 패턴 적용
actions = analysis.apply_successful_behaviors(
    test_case=test_case,
    domain="insurance",
    language="ko",
    min_success_rate=0.8,
    limit=5
)

print(actions)
# ["retrieve_contexts", "extract_monetary_value", "generate_response"]
```

---

## Python API 사용법

### MemoryAwareEvaluator 사용

```python
from evalvault.domain.services.memory_aware_evaluator import MemoryAwareEvaluator
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.adapters.outbound.domain_memory.sqlite_adapter import SQLiteDomainMemoryAdapter
from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter

# 메모리 어댑터 초기화
memory_adapter = SQLiteDomainMemoryAdapter("data/db/evalvault_memory.db")
evaluator = RagasEvaluator()
memory_evaluator = MemoryAwareEvaluator(
    evaluator=evaluator,
    memory_port=memory_adapter
)

# 평가 실행 (threshold 자동 조정)
run = await memory_evaluator.evaluate_with_memory(
    dataset=dataset,
    metrics=["faithfulness", "answer_relevancy"],
    llm=llm_adapter,
    domain="insurance",
    language="ko"
)
```

### 컨텍스트 보강

```python
# 컨텍스트 보강
augmented_context = memory_evaluator.augment_context_with_facts(
    question="보험료는 얼마인가요?",
    original_context="기본 컨텍스트...",
    domain="insurance",
    language="ko",
    limit=5
)

print(augmented_context)
# 기본 컨텍스트...
#
# [관련 사실]
# - 보험료 연령에 따라 증가
# - 보험료 성별에 따라 차등 적용
# ...
```

### 메모리 형성

평가 완료 후 메모리를 자동으로 형성할 수 있습니다:

```python
from evalvault.domain.services.domain_learning_hook import DomainLearningHook

# 메모리 형성 훅 초기화
hook = DomainLearningHook(memory_adapter)

# 평가 완료 후 메모리 형성
await hook.on_evaluation_complete(
    evaluation_run=run,
    domain="insurance",
    language="ko"
)

# 학습된 패턴 조회
reliability = memory_adapter.get_aggregated_reliability(
    domain="insurance",
    language="ko"
)

print(reliability)
# {"faithfulness": 0.85, "answer_relevancy": 0.78, ...}
```

---

## 고급 활용

### 1. 메모리 검색

직접 메모리를 검색할 수 있습니다:

```python
# 사실 검색
facts = memory_adapter.search_facts(
    query="보험료",
    domain="insurance",
    language="ko",
    limit=10
)

# 행동 검색
behaviors = memory_adapter.search_behaviors(
    context="보험료를 조회하는 질문",
    domain="insurance",
    language="ko",
    limit=5
)

# 하이브리드 검색
results = memory_adapter.hybrid_search(
    query="보험료 계산",
    domain="insurance",
    language="ko"
)
```

### 2. 메모리 진화 (Evolution)

메모리를 정리하고 최적화할 수 있습니다:

```python
# Evolution 실행
result = hook.run_evolution(domain="insurance", language="ko")

print(result)
# {"consolidated": 5, "forgotten": 2, "decayed": 10}
```

**Evolution 동작**:
- **Consolidation**: 중복 사실 통합
- **Forgetting**: 오래된 메모리 삭제
- **Decay**: 검증 점수 감소

### 3. 데이터셋 보강

평가 전에 데이터셋에 메모리 사실을 추가할 수 있습니다:

```python
from evalvault.adapters.inbound.cli.commands.run import enrich_dataset_with_memory

# 데이터셋 보강
enriched_count = enrich_dataset_with_memory(
    dataset=dataset,
    memory_evaluator=memory_evaluator,
    domain="insurance",
    language="ko"
)

print(f"보강된 테스트 케이스: {enriched_count}개")
```

---

## 실전 예제

### 시나리오: 보험 도메인 평가 개선

1. **초기 평가 실행** (메모리 없음):
```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" \
  --metrics faithfulness,answer_relevancy
```

2. **메모리 형성** (자동):
- 평가 완료 후 `DomainLearningHook`이 자동으로 메모리 형성
- 사실, 학습 패턴, 행동 패턴 저장

3. **메모리 활용 평가**:
```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" \
  --metrics faithfulness,answer_relevancy \
  --use-domain-memory \
  --augment-context \
  --memory-domain insurance
```

4. **트렌드 분석**:
```python
insights = analysis.generate_insights(
    evaluation_run=run,
    domain="insurance",
    language="ko"
)

# faithfulness가 0.82 → 0.85로 개선됨
# 현재 전략을 유지하거나 확장하라는 추천
```

---

## 주의사항

1. **메모리 데이터베이스 경로**: 기본값은 `data/db/evalvault_memory.db`입니다. 프로젝트별로 다른 경로를 사용하는 것을 권장합니다.
2. **도메인 분리**: 다른 도메인 간 메모리가 섞이지 않도록 `--memory-domain` 옵션을 명시적으로 지정하세요.
3. **메모리 진화**: 정기적으로 `run_evolution()`을 실행하여 메모리를 정리하세요.
4. **성능**: 대용량 메모리 데이터베이스의 경우 검색 성능이 저하될 수 있습니다.

---

## 다음 단계

- [USER_GUIDE.md](../guides/USER_GUIDE.md)에서 더 자세한 사용법 확인
- [DOMAIN_MEMORY_USAGE.md](../internal/archive/DOMAIN_MEMORY_USAGE.md)에서 구현 상세 확인
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md)에서 아키텍처 이해

---

**문서 버전**: 1.0
**최종 업데이트**: 2026-01-02
**작성 기준**: EvalVault 1.5.0
