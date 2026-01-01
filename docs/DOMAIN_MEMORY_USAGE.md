# 도메인 메모리 사용 현황

> **도메인 메모리 저장 후 활용 방안 분석**

이 문서는 EvalVault의 도메인 메모리 시스템이 현재 어떻게 구현되어 있고, 저장된 메모리를 어떻게 사용할 수 있는지(또는 사용해야 하는지)를 분석합니다.

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
memory_adapter = SQLiteDomainMemoryAdapter("evalvault_memory.db")
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

## ❌ 미구현된 기능 (사용 부분)

### 1. 평가 과정에서 메모리 활용

**현재 상태**: 평가 과정에서 저장된 메모리를 조회하여 활용하는 기능이 **없음**

**필요한 기능**:
- 평가 전: 과거 평가 결과에서 학습한 패턴을 조회하여 평가 전략 조정
- 평가 중: 저장된 사실을 참조하여 컨텍스트 보강
- 평가 후: 저장된 행동 패턴을 참조하여 응답 생성 최적화

**예상 사용 시나리오**:
```python
# 평가 전: 과거 학습 패턴 조회
learning = memory_adapter.get_aggregated_reliability(
    domain="insurance",
    language="ko"
)
# {"faithfulness": 0.85, "answer_relevancy": 0.78, ...}

# 평가 중: 관련 사실 조회하여 컨텍스트 보강
related_facts = memory_adapter.search_facts(
    query=test_case.question,
    domain="insurance",
    language="ko"
)
# 컨텍스트에 관련 사실 추가

# 평가 후: 성공한 행동 패턴 적용
behaviors = memory_adapter.search_behaviors(
    context=test_case.question,
    domain="insurance",
    language="ko"
)
# 행동 패턴을 다음 평가에 활용
```

### 2. 분석 과정에서 메모리 활용

**현재 상태**: 분석 과정에서 저장된 메모리를 활용하는 기능이 **없음**

**필요한 기능**:
- 분석 전: 과거 분석 결과와 비교
- 분석 중: 저장된 사실을 기반으로 인사이트 생성
- 분석 후: 분석 결과를 메모리에 저장

**예상 사용 시나리오**:
```python
# 분석 전: 과거 학습 메모리 조회
learnings = memory_adapter.list_learnings(
    domain="insurance",
    language="ko",
    limit=10
)

# 분석 중: 관련 사실을 기반으로 인사이트 생성
facts = memory_adapter.search_facts(
    query=analysis_query,
    domain="insurance",
    language="ko"
)
# 인사이트 생성 시 사실 참조

# 분석 후: 분석 결과를 메모리에 저장
# (이미 DomainLearningHook에서 수행)
```

### 3. 개선 가이드 생성 시 메모리 활용

**현재 상태**: 개선 가이드 생성 시 저장된 메모리를 활용하는 기능이 **없음**

**필요한 기능**:
- 과거 성공한 행동 패턴을 개선 가이드에 포함
- 저장된 사실을 기반으로 개선 제안 생성
- 학습 메모리의 신뢰도 점수를 기반으로 우선순위 결정

**예상 사용 시나리오**:
```python
# 개선 가이드 생성 시
improvement_service = ImprovementGuideService(...)

# 과거 성공한 행동 패턴 조회
behaviors = memory_adapter.list_behaviors(
    domain="insurance",
    language="ko",
    min_success_rate=0.8
)

# 개선 가이드에 성공 패턴 포함
guide = improvement_service.generate_guide(
    run=evaluation_run,
    successful_behaviors=behaviors  # 메모리에서 조회한 패턴
)
```

### 4. CLI 명령어에서 메모리 조회

**현재 상태**: CLI에서 메모리를 조회하는 명령어가 **없음**

**현재 CLI 명령어** (`evalvault domain`):
- `domain init`: 도메인 설정 초기화
- `domain list`: 도메인 목록 조회
- `domain show`: 도메인 설정 조회
- `domain terms`: 용어 사전 조회

**필요한 CLI 명령어**:
```bash
# 메모리 통계 조회
evalvault domain memory stats --domain insurance

# 사실 검색
evalvault domain memory search "보험료" --domain insurance --limit 10

# 행동 패턴 조회
evalvault domain memory behaviors --domain insurance --min-success 0.8

# 학습 메모리 조회
evalvault domain memory learnings --domain insurance --limit 10

# Evolution 실행
evalvault domain memory evolve --domain insurance
```

---

## 메모리 활용 방안

### 1. 평가 최적화 (Evaluation Optimization)

**목적**: 과거 평가에서 학습한 패턴을 활용하여 평가 품질 향상

**구현 방안**:
```python
class MemoryAwareEvaluator:
    """메모리를 활용하는 평가기"""

    def __init__(
        self,
        evaluator: RagasEvaluator,
        memory_port: DomainMemoryPort
    ):
        self.evaluator = evaluator
        self.memory_port = memory_port

    async def evaluate_with_memory(
        self,
        dataset: Dataset,
        domain: str,
        language: str = "ko"
    ) -> EvaluationRun:
        # 1. 과거 학습 패턴 조회
        reliability = self.memory_port.get_aggregated_reliability(
            domain=domain,
            language=language
        )

        # 2. 평가 전략 조정 (신뢰도 낮은 메트릭에 더 집중)
        adjusted_metrics = self._adjust_metrics_by_reliability(
            reliability
        )

        # 3. 평가 실행
        run = await self.evaluator.evaluate(
            dataset=dataset,
            metrics=adjusted_metrics
        )

        # 4. 평가 중: 관련 사실 조회하여 컨텍스트 보강
        for result in run.results:
            related_facts = self.memory_port.search_facts(
                query=result.question,
                domain=domain,
                language=language,
                limit=3
            )
            # 컨텍스트에 관련 사실 추가

        return run
```

### 2. 컨텍스트 보강 (Context Augmentation)

**목적**: 저장된 사실을 활용하여 평가 컨텍스트 보강

**구현 방안**:
```python
class MemoryAugmentedContext:
    """메모리로 보강된 컨텍스트"""

    def augment_context(
        self,
        original_context: str,
        question: str,
        memory_port: DomainMemoryPort,
        domain: str,
        language: str
    ) -> str:
        # 관련 사실 조회
        facts = memory_port.search_facts(
            query=question,
            domain=domain,
            language=language,
            limit=5
        )

        # 사실을 컨텍스트에 추가
        fact_texts = [
            f"{fact.subject} {fact.predicate} {fact.object}"
            for fact in facts
        ]

        augmented = original_context
        if fact_texts:
            augmented += "\n\n[관련 사실]\n" + "\n".join(fact_texts)

        return augmented
```

### 3. 행동 패턴 재사용 (Behavior Reuse)

**목적**: 과거 성공한 행동 패턴을 재사용하여 평가 효율 향상

**구현 방안**:
```python
class BehaviorReusingEvaluator:
    """행동 패턴을 재사용하는 평가기"""

    def apply_learned_behaviors(
        self,
        test_case: TestCase,
        memory_port: DomainMemoryPort,
        domain: str,
        language: str
    ) -> list[str]:
        # 관련 행동 패턴 조회
        behaviors = memory_port.search_behaviors(
            context=test_case.question,
            domain=domain,
            language=language,
            limit=3
        )

        # 성공률 높은 행동 패턴 적용
        actions = []
        for behavior in behaviors:
            if behavior.success_rate >= 0.8:
                actions.extend(behavior.action_sequence)

        return actions
```

### 4. 분석 인사이트 생성 (Analysis Insight Generation)

**목적**: 저장된 메모리를 기반으로 분석 인사이트 생성

**구현 방안**:
```python
class MemoryBasedAnalysis:
    """메모리 기반 분석"""

    def generate_insights(
        self,
        evaluation_run: EvaluationRun,
        memory_port: DomainMemoryPort,
        domain: str,
        language: str
    ) -> dict:
        # 과거 학습 메모리와 비교
        current_metrics = self._extract_metrics(evaluation_run)
        historical_learnings = memory_port.list_learnings(
            domain=domain,
            language=language,
            limit=10
        )

        # 트렌드 분석
        trends = self._analyze_trends(
            current=current_metrics,
            historical=historical_learnings
        )

        # 관련 사실 기반 인사이트
        facts = memory_port.search_facts(
            query=evaluation_run.run_id,
            domain=domain,
            language=language
        )

        insights = {
            "trends": trends,
            "related_facts": facts,
            "recommendations": self._generate_recommendations(
                trends, facts
            )
        }

        return insights
```

---

## 구현 우선순위

### Phase 1: 기본 조회 기능 (High Priority)

1. **CLI 명령어 추가**
   - `evalvault domain memory stats`: 메모리 통계 조회
   - `evalvault domain memory search`: 사실 검색
   - `evalvault domain memory behaviors`: 행동 패턴 조회

2. **평가 과정에서 메모리 조회**
   - 평가 전: 과거 학습 패턴 조회
   - 평가 중: 관련 사실 조회 (선택적)

### Phase 2: 활용 기능 (Medium Priority)

3. **컨텍스트 보강**
   - 평가 중: 저장된 사실로 컨텍스트 보강
   - 분석 중: 관련 사실 기반 인사이트 생성

4. **행동 패턴 재사용**
   - 평가 중: 성공한 행동 패턴 자동 적용
   - 개선 가이드에 행동 패턴 포함

### Phase 3: 고급 활용 (Low Priority)

5. **트렌드 분석**
   - 과거 학습 메모리와 현재 결과 비교
   - 시계열 분석

6. **자동 최적화**
   - 메모리 기반 평가 전략 자동 조정
   - 메모리 기반 개선 제안 자동 생성

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

❌ **사용 기능**: 거의 없음
- 평가 과정에서 메모리 활용 없음
- 분석 과정에서 메모리 활용 없음
- CLI에서 메모리 조회 명령어 없음

### 권장 사항

1. **즉시 구현 가능**: CLI 명령어 추가
   - 메모리 통계, 검색, 조회 명령어

2. **단기 구현**: 평가 과정에서 메모리 활용
   - 평가 전 학습 패턴 조회
   - 평가 중 관련 사실 조회

3. **중기 구현**: 컨텍스트 보강 및 행동 패턴 재사용
   - 메모리 기반 컨텍스트 보강
   - 성공한 행동 패턴 자동 적용

4. **장기 구현**: 자동 최적화
   - 메모리 기반 평가 전략 자동 조정
   - 메모리 기반 개선 제안 자동 생성

---

**문서 버전**: 1.0
**최종 업데이트**: 2026년
**작성 기준**: EvalVault 프로젝트 코드베이스 분석
