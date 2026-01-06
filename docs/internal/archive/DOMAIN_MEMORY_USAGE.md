# 도메인 메모리 사용 현황

> **도메인 메모리 저장 후 활용 방안 분석**

이 문서는 EvalVault의 도메인 메모리 시스템이 현재 어떻게 구현되어 있고, 저장된 메모리를 어떻게 사용할 수 있는지(또는 사용해야 하는지)를 분석합니다.

## 📚 관련 문서

| 문서 | 역할 | 설명 |
|------|------|------|
| **[DOMAIN_MEMORY_USAGE.md](./DOMAIN_MEMORY_USAGE.md)** (이 문서) | 현황 리포트 | 구현 상태, 사용법, 향후 개선 항목 정리 |
| [USER_GUIDE.md](../../guides/USER_GUIDE.md#도메인-메모리-활용) | 사용자 가이드 | CLI/Python 관점에서 Domain Memory를 사용하는 절차 |
| [tutorials/07-domain-memory.md](../../tutorials/07-domain-memory.md) | 튜토리얼 | 단계별 실습 및 고급 활용법 |
| [ARCHITECTURE.md](../../architecture/ARCHITECTURE.md#46-도메인-메모리-활용-흐름-domain-memory-usage-flow) | 아키텍처 | Domain Memory 형성·활용 플로우 |
| [CLI_GUIDE.md](../../guides/CLI_GUIDE.md#4-domain-memory-서브커맨드) | CLI 참조 | `evalvault domain memory` 하위 명령 모음 |

---

## 현재 구현 상태

### ✅ 구현 완료된 기능

#### 1. 메모리 저장 (Formation Dynamics)

**구현 위치**:
- `src/evalvault/domain/services/domain_learning_hook.py` - `DomainLearningHook`
- `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py` - `SQLiteDomainMemoryAdapter`

**기능**:
- ✅ 평가 결과에서 사실(FactualFact) 추출 및 저장
- ✅ 평가 결과에서 학습 패턴(LearningMemory) 추출 및 저장
- ✅ 평가 결과에서 행동 패턴(BehaviorEntry) 추출 및 저장
- ✅ 중복 사실 통합 (consolidate_facts)
- ✅ 오래된 메모리 삭제 (forget_obsolete)
- ✅ 검증 점수 감소 (decay_verification_scores)

**사용 방법**:
```python
from evalvault.domain.services.domain_learning_hook import DomainLearningHook
from evalvault.adapters.outbound.domain_memory.sqlite_adapter import SQLiteDomainMemoryAdapter

# 메모리 어댑터 초기화
memory_adapter = SQLiteDomainMemoryAdapter("data/db/evalvault_memory.db")
hook = DomainLearningHook(memory_adapter)

# 평가 완료 후 메모리 형성
result = await hook.on_evaluation_complete(
    evaluation_run=run,
    domain="insurance",
    language="ko"
)
```

#### 2. 메모리 검색 (Retrieval Dynamics)

**구현 위치**:
- `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py`

**기능**:
- ✅ `search_facts()`: FTS5 기반 키워드 사실 검색
- ✅ `search_behaviors()`: 컨텍스트 기반 행동 검색
- ✅ `hybrid_search()`: Factual/Experiential/Behavior 레이어 통합 검색
- ✅ `list_facts()`: 필터링된 사실 목록 조회
- ✅ `get_fact()`: 특정 사실 조회
- ✅ `get_learning()`: 학습 메모리 조회
- ✅ `get_handbook()`: 도메인별 행동 핸드북 조회

**사용 방법**:
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

#### 3. 메모리 관리 (Evolution Dynamics)

**구현 위치**:
- `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py`
- `src/evalvault/domain/services/domain_learning_hook.py`

**기능**:
- ✅ `consolidate_facts()`: 중복 사실 통합
- ✅ `resolve_conflict()`: 충돌하는 사실 해결
- ✅ `forget_obsolete()`: 오래된 메모리 삭제
- ✅ `decay_verification_scores()`: 검증 점수 감소

**사용 방법**:
```python
# Evolution 실행
result = hook.run_evolution(domain="insurance", language="ko")
# {"consolidated": 5, "forgotten": 2, "decayed": 10}
```

---

## ✅ 구현 완료된 기능 (사용 부분)

### 1. 평가 과정에서 메모리 활용

**현재 상태**: 평가 과정에서 저장된 메모리를 조회하여 활용하는 기능이 **구현 완료**

**구현 위치**:
- `src/evalvault/domain/services/memory_aware_evaluator.py` - `MemoryAwareEvaluator`
- `src/evalvault/adapters/inbound/cli/commands/run.py` - CLI 통합

**구현된 기능**:
- ✅ 평가 전: 과거 평가 결과에서 학습한 패턴을 조회하여 평가 전략 조정
- ✅ 평가 중: 저장된 사실을 참조하여 컨텍스트 보강
- ✅ CLI 통합: `--use-domain-memory`, `--augment-context` 옵션

**실제 사용 방법**:

#### CLI를 통한 사용

```bash
# Domain Memory를 활용한 평가 (threshold 자동 조정)
evalvault run dataset.json \
  --metrics faithfulness,answer_relevancy \
  --use-domain-memory \
  --memory-domain insurance \
  --memory-language ko

# 컨텍스트 보강 옵션 사용
evalvault run dataset.json \
  --metrics faithfulness \
  --augment-context \
  --memory-domain insurance
```

#### Python 코드를 통한 사용

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

# 평가 전: 과거 학습 패턴 조회 및 threshold 자동 조정
run = await memory_evaluator.evaluate_with_memory(
    dataset=dataset,
    metrics=["faithfulness", "answer_relevancy"],
    llm=llm_adapter,
    domain="insurance",
    language="ko"
)
# reliability 점수에 따라 threshold가 자동으로 조정됨

# 컨텍스트 보강
augmented_context = memory_evaluator.augment_context_with_facts(
    question="보험료는 얼마인가요?",
    original_context="기본 컨텍스트...",
    domain="insurance",
    language="ko",
    limit=5
)
# 관련 사실이 자동으로 컨텍스트에 추가됨
```

**동작 원리**:
1. `evaluate_with_memory()` 호출 시 `get_aggregated_reliability()`로 과거 신뢰도 점수 조회
2. 신뢰도 점수에 따라 threshold 자동 조정:
   - 신뢰도 < 0.6: threshold를 0.1 낮춤 (최소 0.5)
   - 신뢰도 > 0.85: threshold를 0.05 높임 (최대 0.95)
3. `augment_context_with_facts()` 호출 시 질문과 관련된 사실을 검색하여 컨텍스트에 추가

### 2. 분석 과정에서 메모리 활용

**현재 상태**: 분석 과정에서 저장된 메모리를 활용하는 기능이 **구현 완료**

**구현 위치**:
- `src/evalvault/domain/services/memory_based_analysis.py` - `MemoryBasedAnalysis`

**구현된 기능**:
- ✅ 분석 전: 과거 분석 결과와 비교 (트렌드 분석)
- ✅ 분석 중: 저장된 사실을 기반으로 인사이트 생성
- ✅ 행동 패턴 재사용: 성공한 행동 패턴 자동 적용

**실제 사용 방법**:

```python
from evalvault.domain.services.memory_based_analysis import MemoryBasedAnalysis
from evalvault.adapters.outbound.domain_memory.sqlite_adapter import SQLiteDomainMemoryAdapter

# 메모리 기반 분석 초기화
memory_adapter = SQLiteDomainMemoryAdapter("data/db/evalvault_memory.db")
analysis = MemoryBasedAnalysis(memory_adapter)

# 인사이트 생성 (과거 학습 메모리와 비교)
insights = analysis.generate_insights(
    evaluation_run=run,
    domain="insurance",
    language="ko",
    history_limit=10
)
# {
#   "trends": {
#     "faithfulness": {"current": 0.85, "baseline": 0.82, "delta": 0.03},
#     ...
#   },
#   "related_facts": [...],
#   "recommendations": ["faithfulness 개선 중: 현재 전략을 유지하거나 확장하세요."]
# }

# 성공한 행동 패턴 적용
actions = analysis.apply_successful_behaviors(
    test_case=test_case,
    domain="insurance",
    language="ko",
    min_success_rate=0.8,
    limit=5
)
# ["retrieve_contexts", "extract_monetary_value", "generate_response"]
```

**동작 원리**:
1. `generate_insights()`: 과거 학습 메모리와 현재 메트릭을 비교하여 트렌드 분석
2. `apply_successful_behaviors()`: 질문 컨텍스트에 맞는 성공한 행동 패턴을 검색하여 재사용 가능한 액션 시퀀스 반환

### 3. CLI 통합

**현재 상태**: CLI에서 메모리를 활용하는 기능이 **구현 완료**

**구현된 CLI 옵션** (`evalvault run`):
- `--use-domain-memory`: Domain Memory를 활용하여 threshold 자동 조정
- `--memory-domain`: 도메인 이름 지정 (기본값: dataset metadata에서 추출)
- `--memory-language`: 언어 코드 지정 (기본값: ko)
- `--memory-db`: Domain Memory 데이터베이스 경로 (기본값: data/db/evalvault_memory.db)
- `--augment-context`: 각 테스트 케이스의 컨텍스트에 관련 사실 자동 추가

**사용 예제**:

```bash
# 기본 사용 (threshold 자동 조정)
evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --use-domain-memory \
  --memory-domain insurance

# 컨텍스트 보강 포함
evalvault run dataset.json \
  --metrics faithfulness \
  --use-domain-memory \
  --augment-context \
  --memory-domain insurance \
  --memory-language ko

# 커스텀 메모리 DB 경로 지정
evalvault run dataset.json \
  --use-domain-memory \
  --memory-db /path/to/custom_memory.db \
  --memory-domain insurance
```

**동작 흐름**:
1. `--use-domain-memory` 옵션 사용 시 `MemoryAwareEvaluator` 자동 생성
2. 평가 전: `get_aggregated_reliability()`로 신뢰도 점수 조회 및 표시
3. 평가 실행: 신뢰도 점수에 따라 threshold 자동 조정
4. `--augment-context` 옵션 사용 시: 각 테스트 케이스의 질문으로 관련 사실 검색하여 컨텍스트에 추가

### 4. 도메인 메모리 CLI 명령어

**현재 상태**: `evalvault domain memory` 서브커맨드 세트가 **구현 완료**

**구현 위치**:
- `src/evalvault/adapters/inbound/cli/commands/domain.py`

**지원 명령어**:
- `stats`: Facts/Learnings/Behaviors/Contexts 개수를 도메인별로 요약
- `search`: Factual 사실 검색 (`--min-score`, `--limit` 지원)
- `behaviors`: 행동 패턴 검색 (`--min-success`, `--context` 지원)
- `learnings`: Experiential 학습 로그 조회
- `evolve`: consolidation/forgetting/decay 실행 (`--dry-run`, `--yes` 제공)

**예시**:

```bash
$ evalvault domain memory stats --domain insurance
$ evalvault domain memory search "청약 철회" --domain insurance --min-score 0.7
$ evalvault domain memory behaviors --domain insurance --min-success 0.8
$ evalvault domain memory learnings --domain insurance --limit 10
$ evalvault domain memory evolve --domain insurance --yes
```

각 명령은 `--memory-db/-M` 옵션으로 별도 DB를 지정할 수 있으며, Rich 테이블로 결과를 출력합니다.

### 5. 데이터셋 보강 (Dataset Enrichment)

**현재 상태**: 평가 전 데이터셋에 메모리 사실을 추가하는 기능이 **구현 완료**

**구현 위치**:
- `src/evalvault/adapters/inbound/cli/commands/run.py` - `enrich_dataset_with_memory()`

**기능**:
- ✅ 평가 전: 각 테스트 케이스의 질문으로 관련 사실 검색
- ✅ 컨텍스트에 관련 사실 자동 추가
- ✅ 중복 방지 (이미 컨텍스트에 있는 사실은 추가하지 않음)

**사용 방법**:

```python
from evalvault.adapters.inbound.cli.commands.run import enrich_dataset_with_memory
from evalvault.domain.services.memory_aware_evaluator import MemoryAwareEvaluator

# 데이터셋 보강
enriched_count = enrich_dataset_with_memory(
    dataset=dataset,
    memory_evaluator=memory_evaluator,
    domain="insurance",
    language="ko"
)
# 보강된 테스트 케이스 수 반환
```

---

## 향후 개선 사항

### 1. 개선 가이드 생성 시 메모리 활용

**현재 상태**: 개선 가이드 생성 시 저장된 메모리를 직접 활용하는 기능은 아직 없음

**향후 개선 방안**:
- `ImprovementGuideService`와 `DomainMemoryPort`를 연결하여 성공/실패 패턴을 가이드에 반영
- `MemoryBasedAnalysis.apply_successful_behaviors()` 결과를 개선 시나리오의 Recommended Actions로 노출
- CLI `gate`/`run` 명령에서 생성한 Improvement Guide 패널에 메모리 출처를 표시

### 2. 자동화된 리포트 및 시각화

**현재 상태**: 메모리 기반 트렌드/사실은 CLI 결과 패널에만 표시되며, Web UI·Langfuse에는 노출되지 않음

**향후 개선 방안**:
- Streamlit Web UI (`uv run evalvault web`)에 Domain Memory Insights 섹션 추가
- Langfuse/MLflow 트래커에 메모리 기반 지표를 부가 속성으로 기록
- `evalvault analyze` 명령의 JSON 출력에 메모리 인사이트 필드를 포함하여 자동화 워크플로우에서도 활용 가능하게 확장

---

## 결론

### 현재 상태

✅ **저장 기능**: 완전히 구현됨
- 평가 결과에서 메모리 추출 및 저장
- Evolution dynamics (통합, 삭제, 감소)

✅ **검색 기능**: 완전히 구현됨
- 사실 검색 (FTS5)
- 행동 검색
- 하이브리드 검색

✅ **사용 기능**: 핵심 기능 구현 완료
- ✅ 평가 과정에서 메모리 활용 (`MemoryAwareEvaluator`)
- ✅ 분석 과정에서 메모리 활용 (`MemoryBasedAnalysis`)
- ✅ CLI 통합 (`run` 명령 + `domain memory` 서브커맨드)
- ✅ 데이터셋 보강 (`enrich_dataset_with_memory`)

### 구현 완료된 기능 요약

| 기능 | 구현 상태 | 위치 |
|------|----------|------|
| 메모리 저장 | ✅ 완료 | `DomainLearningHook`, `SQLiteDomainMemoryAdapter` |
| 메모리 검색 | ✅ 완료 | `SQLiteDomainMemoryAdapter` |
| 평가 최적화 | ✅ 완료 | `MemoryAwareEvaluator.evaluate_with_memory()` |
| 컨텍스트 보강 | ✅ 완료 | `MemoryAwareEvaluator.augment_context_with_facts()` |
| 트렌드 분석 | ✅ 완료 | `MemoryBasedAnalysis.generate_insights()` |
| 행동 패턴 재사용 | ✅ 완료 | `MemoryBasedAnalysis.apply_successful_behaviors()` |
| CLI 통합 | ✅ 완료 | `run` 명령어 옵션 |
| 메모리 CLI 명령어 | ✅ 완료 | `domain` 명령의 `memory` 서브커맨드 |
| 데이터셋 보강 | ✅ 완료 | `enrich_dataset_with_memory()` |

### 향후 개선 사항

1. **개선 가이드 통합**: `ImprovementGuideService`와 Domain Memory를 연결하여 행동 패턴/사실을 기반으로 한 권고안을 생성
2. **자동화된 리포트**: Web UI·Langfuse·`evalvault analyze` 출력에 메모리 인사이트를 포함해 시각화/자동화를 지원

---

**문서 버전**: 2.0
**최종 업데이트**: 2026-01-02
**작성 기준**: EvalVault 1.5.0 코드베이스 분석
