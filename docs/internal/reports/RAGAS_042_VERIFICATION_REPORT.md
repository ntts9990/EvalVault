# RAGAS 0.4.2 호환성 검증 리포트

**검증 일시:** 2025-01-XX
**검증 스크립트:** `scripts/verify_ragas_compliance.py`

---

## 검증 결과 요약

### ✅ 통과 항목

1. **RAGAS 버전 확인**
   - ✅ 버전: 0.4.2 (정확히 일치)
   - ✅ `uv.lock`과 실제 설치 버전 일치

2. **RagasEvaluator 구현**
   - ✅ 모든 필수 메트릭 매핑 존재
   - ✅ `ascore()` API 사용 (RAGAS 0.4+ 표준)
   - ✅ 메트릭별 required arguments 정확히 정의됨
   - ✅ SingleTurnSample 변환 로직 정확

3. **LLM 어댑터 통합**
   - ✅ `as_ragas_llm()` 메서드 정상 작동
   - ✅ `as_ragas_embeddings()` 메서드 지원
   - ✅ InstructorLLM 생성 방식 일관됨

---

### ⚠️ 경고 항목

1. **RAGAS API 사용 확인**
   - ⚠️ 메트릭 초기화 체크에서 경고 발생
   - **원인:** 테스트 코드에서 MagicMock 사용으로 인한 경고
   - **영향:** 실제 운영 환경에서는 문제 없음
   - **조치:** 테스트 코드 개선 (선택적)

2. **재현성 테스트**
   - ⚠️ 재현 가능: False
   - **점수 분산:** 0.100000 (10%)
   - **실행 1:** 평균 0.7000
   - **실행 2:** 평균 0.6000
   - **원인:** LLM의 비결정론적 특성 (Temperature 설정 없음)
   - **영향:** 동일 환경에서도 결과가 달라질 수 있음
   - **조치:** Temperature=0.0 설정 추가 필요

---

## 상세 분석

### 1. RAGAS 0.4.2 API 호환성

#### ✅ 올바르게 구현된 부분

**메트릭 초기화:**
```python
# evaluator.py line 338-347
ragas_metrics = []
for metric_name in metrics:
    metric_class = self.METRIC_MAP.get(metric_name)
    if metric_class:
        if metric_name in self.EMBEDDING_REQUIRED_METRICS and ragas_embeddings:
            ragas_metrics.append(metric_class(llm=ragas_llm, embeddings=ragas_embeddings))
        else:
            ragas_metrics.append(metric_class(llm=ragas_llm))
```

**ascore() API 사용:**
```python
# evaluator.py line 556-570
if hasattr(metric, "ascore"):
    all_args = {
        "user_input": sample.user_input,
        "response": sample.response,
        "retrieved_contexts": sample.retrieved_contexts,
        "reference": sample.reference,
    }
    required_args = self.METRIC_ARGS.get(metric.name, [...])
    kwargs = {k: v for k, v in all_args.items() if k in required_args and v is not None}
    result = await metric.ascore(**kwargs)
```

**SingleTurnSample 변환:**
```python
# evaluator.py line 324-329
sample = SingleTurnSample(
    user_input=test_case.question,
    response=test_case.answer,
    retrieved_contexts=test_case.contexts,
    reference=test_case.ground_truth,
)
```

#### ⚠️ 개선 필요 부분

**Temperature 설정 부재:**
- 현재 LLM 호출 시 temperature 파라미터가 명시적으로 설정되지 않음
- 재현성을 위해 temperature=0.0 설정 필요

**Seed 설정 부재:**
- 결정론적 결과를 위한 seed 파라미터 없음
- 재현 가능한 평가를 위해 seed 옵션 추가 필요

---

### 2. 재현성 분석

#### 현재 상태

**테스트 결과:**
- 동일 환경에서 2회 실행
- 점수 차이: 0.1 (10%)
- 원인: LLM의 비결정론적 샘플링

**영향:**
- 다른 사용자가 동일한 설정으로 실행해도 결과가 다를 수 있음
- 평가 결과 비교 시 변동성을 고려해야 함

#### 개선 방안

1. **Temperature 설정 추가**
   ```python
   # instructor_factory.py 또는 adapter에서
   temperature=0.0  # 재현성을 위한 기본값
   ```

2. **Seed 설정 옵션 추가**
   ```python
   # Settings에 추가
   llm_seed: int | None = Field(default=None, description="Random seed for LLM")
   ```

3. **재현성 가이드 작성**
   - Temperature/Seed 설정 방법
   - 환경별 차이점 설명
   - 결과 비교 시 주의사항

---

## RAGAS 0.4.2 공식 문서 대조

### 메트릭 초기화 방식

**RAGAS 0.4.2 표준:**
```python
from ragas.metrics.collections import Faithfulness
from ragas.llms import llm_factory

llm = llm_factory("gpt-4o-mini")
metric = Faithfulness(llm=llm)
```

**현재 구현:**
```python
from ragas.metrics.collections import Faithfulness
from evalvault.adapters.outbound.llm.instructor_factory import create_instructor_llm

ragas_llm = create_instructor_llm("openai", model_name, client)
metric = Faithfulness(llm=ragas_llm)
```

**비교 결과:**
- ✅ InstructorLLM 사용 (RAGAS 요구사항 충족)
- ⚠️ `llm_factory` 대신 커스텀 팩토리 사용
- **평가:** 기능적으로 동일하지만, RAGAS 표준 방식과 다름

### ascore() API 사용

**RAGAS 0.4.2 표준:**
```python
result = await metric.ascore(
    user_input="...",
    response="...",
    retrieved_contexts=["..."],
    reference="...",  # 선택적
)
```

**현재 구현:**
```python
all_args = {
    "user_input": sample.user_input,
    "response": sample.response,
    "retrieved_contexts": sample.retrieved_contexts,
    "reference": sample.reference,
}
required_args = self.METRIC_ARGS.get(metric.name, [...])
kwargs = {k: v for k, v in all_args.items() if k in required_args and v is not None}
result = await metric.ascore(**kwargs)
```

**비교 결과:**
- ✅ 인자 이름 일치
- ✅ 필수/선택 인자 구분 정확
- ✅ None 값 처리 적절

---

## 개선 권장 사항

### 우선순위 높음

1. **Temperature 설정 추가**
   - LLM 호출 시 temperature=0.0 기본값 설정
   - 설정 파일에서 오버라이드 가능하도록

2. **재현성 가이드 작성**
   - `docs/guides/REPRODUCIBILITY.md` 생성
   - Temperature/Seed 설정 방법 설명
   - 환경별 차이점 문서화

### 우선순위 중간

3. **Seed 설정 옵션 추가**
   - Settings에 llm_seed 필드 추가
   - LLM 어댑터에서 seed 전달

4. **재현성 테스트 추가**
   - `tests/integration/test_ragas_reproducibility.py` 생성
   - CI/CD에 포함

### 우선순위 낮음

5. **RAGAS llm_factory 사용 검토**
   - 현재 커스텀 팩토리와 비교
   - 마이그레이션 비용 평가

---

## 결론

### 호환성 평가

**전체 평가: ✅ 양호**

- RAGAS 0.4.2 API를 올바르게 사용하고 있음
- 메트릭 초기화 및 호출 방식이 표준과 일치
- SingleTurnSample 변환 정확

### 재현성 평가

**전체 평가: ⚠️ 개선 필요**

- 현재는 재현성이 보장되지 않음 (점수 분산 10%)
- Temperature 설정 추가로 개선 가능
- Seed 설정으로 추가 개선 가능

### 권장 조치

1. **즉시 조치:** Temperature=0.0 설정 추가
2. **단기 조치:** 재현성 가이드 작성
3. **중기 조치:** Seed 설정 옵션 추가
4. **장기 조치:** 재현성 테스트 자동화

---

**다음 단계:**
1. Temperature 설정 추가 구현
2. 재현성 가이드 문서 작성
3. 개선 후 재검증
