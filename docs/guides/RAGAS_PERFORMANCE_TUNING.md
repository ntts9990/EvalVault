# Ragas 성능 최적화 가이드

> EvalVault에서 Ragas 기반 평가 속도를 높이기 위한 **실행 가능한 설정**과 **코드 개선 아이디어**를 정리합니다.

---

## TL;DR (우선순위 요약)

1. **병렬 평가 + 배치 크기 조절**로 처리량 확보
2. **느린 메트릭 제외** (특히 `factual_correctness`, `semantic_similarity`)
3. **빠른 LLM/임베딩 모델**로 교체 (프로필/옵션 조정)
4. **컨텍스트 길이/개수 줄이기** (retriever/top_k, 데이터 전처리)
5. **부가 기능 끄기** (Domain Memory, Tracker)

---

## 1) 코드 수정 없이 바로 적용 가능한 방법

### 1.1 병렬 평가와 배치 크기

EvalVault는 배치 단위 `asyncio.gather`로 병렬 평가를 수행합니다.
동시성은 `batch_size`가 결정하며, `parallel`은 병렬 활성화 스위치입니다.

**CLI 예시**
```bash
uv run evalvault run data.json --metrics faithfulness --parallel --batch-size 10
```

**Web UI 예시**
- `Advanced Configuration → Performance & Batching`
- `Parallel Users`가 1 초과이면 병렬 활성화
- 실제 동시성은 `Batch Size` 값이 결정

> 권장: 로컬 Ollama는 5~10, 외부 API는 레이트리밋에 맞춰 단계적으로 증가

---

### 1.2 메트릭 최소화 (속도 영향 큼)

현재 EvalVault는 메트릭을 **순차적으로 평가**합니다.
필요한 메트릭만 선택해 호출 수를 줄이는 것이 가장 큰 효과를 냅니다.

| 메트릭 | 호출 성격 | 속도 영향 |
|--------|-----------|-----------|
| `faithfulness` | LLM 호출 | 중 |
| `answer_relevancy` | LLM + 임베딩 | 중~높음 |
| `context_precision` | LLM | 중 |
| `context_recall` | LLM | 중 |
| `semantic_similarity` | 임베딩 | 높음 (임베딩 모델 속도 영향) |
| `factual_correctness` | LLM 다중 호출 (claim 분해/검증) | 매우 높음 |
| 커스텀 메트릭 | 규칙 기반/비LLM | 낮음 |

> 빠른 반복 평가 단계에서는 `faithfulness` 단일 메트릭만으로 시작하세요.

---

### 1.3 LLM/임베딩 모델 선택

평가 속도는 모델이 좌우합니다. 빠른 모델을 별도 프로필로 두고 사용하세요.

```bash
# 빠른 모델 프로필로 전환
EVALVAULT_PROFILE=dev uv run evalvault run data.json --metrics faithfulness
```

**Ollama**:
- `config/models.yaml`에서 `think_level`을 낮추거나 제거하면 속도 개선
- 임베딩 모델은 소형 모델(`qwen3-embedding:0.6b` 등) 권장

---

### 1.4 컨텍스트 길이/개수 줄이기

프롬프트 토큰이 늘어날수록 평가 속도는 급격히 느려집니다.

- 데이터셋의 `contexts`를 **짧게 유지**
- `retriever`를 사용할 경우 `top_k`를 낮춤
- 중복/불필요한 컨텍스트 제거

**CLI 예시**
```bash
uv run evalvault run data.json \
  --metrics faithfulness \
  --retriever bm25 \
  --retriever-docs docs.jsonl \
  --retriever-top-k 3
```

> Web UI는 현재 `top_k=5` 고정이므로, 더 낮추려면 CLI 또는 API 사용이 필요합니다.

---

### 1.5 부가 기능 비활성화

아래 기능은 평가 속도에 직접적인 부하를 더합니다.

- Domain Memory (`--use-domain-memory` OFF)
- Tracker (`--tracker none`)
- Phoenix 자동 트레이싱 (`PHOENIX_ENABLED=false`)
- Retriever (컨텍스트가 이미 있으면 비활성화)

---

## 2) 코드 개선 아이디어 (향후 작업 제안)

아래 항목은 **소스 수정이 필요한 개선안**입니다. 현재 구조를 기준으로 실현 가능성이 높습니다.

### 2.1 메트릭별 동시 실행

`_score_single_sample()`은 메트릭을 순차 실행합니다.
`asyncio.gather()`로 메트릭을 병렬화하면 **샘플당 지연 시간을 단축**할 수 있습니다.

### 2.2 LLM/임베딩 캐시 도입

동일 입력(질문/답변/컨텍스트)에 대한 호출이 반복됩니다.
`BaseLLMAdapter` 또는 ragas 래퍼에 **캐싱 레이어**를 붙이면 재평가가 빨라집니다.

### 2.3 임베딩 사전 계산/재사용

`answer_relevancy`, `semantic_similarity`는 임베딩에 의존합니다.
평가 전에 임베딩을 저장하고 재사용하면 비용과 시간을 줄일 수 있습니다.

### 2.4 메트릭 입력 조건 기반 스킵

`reference`/`contexts`가 없을 때 해당 메트릭은 즉시 스킵하도록
검증 로직을 추가하면 불필요한 호출을 줄일 수 있습니다.

### 2.5 병렬 제어 개선

현재 `run_in_batches()`는 고정 배치 크기만 제공합니다.
동적 배치/세마포어 기반 제한으로 **API 레이트리밋/리소스 사용을 최적화**할 수 있습니다.

### 2.6 AsyncBatchExecutor 도입 (적응형 배치)

코드베이스에 `AsyncBatchExecutor`가 이미 존재합니다.
`Evaluator._evaluate_with_ragas()`가 사용하는 고정 배치 대신
`src/evalvault/domain/services/async_batch_executor.py`를 연결하면
성공률/429 비율에 따라 배치 크기를 자동 조정할 수 있습니다.

### 2.7 LLM 응답 토큰 상한 조정

현재 어댑터는 `max_completion_tokens` 기본값이 큽니다.
`BaseLLMAdapter`/`*_adapter.py`에 **프로필별 상한**을 두면
짧은 답변 기준 평가에서 체감 속도를 줄일 수 있습니다.

---

## 3) 성능 측정 체크리스트

1. 동일 데이터셋으로 **baseline run** 확보
2. `--parallel`/`--batch-size` 단계별 증가
3. 메트릭 제거 후 지연/비용 변화 기록
4. `EvaluationRun.total_tokens`, `latency_ms`, `total_cost_usd` 비교
5. Tracker 비활성화/활성화 차이 확인

---

---

## 재현성 (Reproducibility) 고려사항

### 평가 결과의 변동성

RAGAS 메트릭 평가는 LLM을 사용하므로, 동일한 입력에 대해 결과가 달라질 수 있습니다. 이는 다음과 같은 이유 때문입니다:

1. **LLM의 비결정론적 샘플링**: 대부분의 LLM은 기본적으로 비결정론적으로 동작
2. **Temperature 설정**: 기본값이 1.0 이상인 경우 변동성 증가
3. **Seed 설정 부재**: 랜덤 시드가 없으면 매번 다른 결과

### 재현성을 높이는 방법

#### 1. 모델별 설정 (지원하는 경우)

**OpenAI:**
```python
# 직접 클라이언트 설정 (Ragas 외부 호출 시)
client = OpenAI(api_key="...")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    temperature=0.0,  # 재현성 향상
    seed=42,  # 결정론적 결과
)
```

**Ollama:**
```bash
# Ollama API 직접 호출 시
curl http://localhost:11434/api/generate -d '{
  "model": "gemma3:1b",
  "prompt": "...",
  "options": {
    "temperature": 0.0,
    "seed": 42
  }
}'
```

**주의사항:**
- 일부 모델에서는 `temperature=0`이 오류를 발생시킬 수 있음
- RAGAS 메트릭이 InstructorLLM을 통해 호출하므로, 직접 설정이 적용되지 않을 수 있음
- 모델별 API 명세를 확인하여 지원 여부 확인 필요

#### 2. 결과 비교 시 주의사항

동일한 데이터셋을 여러 번 평가할 때:

- **점수 차이**: ±0.05 (5%) 이내는 정상 범위로 간주
- **상대적 순서**: 개별 점수보다는 전체적인 순서가 일관되는지 확인
- **평균 점수**: 여러 실행의 평균을 사용하여 변동성 완화

#### 3. 재현 가능한 평가를 위한 권장사항

1. **동일 환경 사용**
   - 같은 Python/ragas 버전
   - 같은 모델 및 설정
   - 같은 데이터셋

2. **결과 문서화**
   - 사용한 모델 및 버전 기록
   - 평가 시점 기록
   - 환경 정보 기록

3. **여러 실행 평균**
   - 중요한 평가는 3회 이상 실행
   - 평균 점수 사용
   - 표준편차 기록

### 모델별 지원 현황

| 모델 | Temperature | Seed | 비고 |
|------|-------------|------|------|
| OpenAI | ✅ | ✅ | 완전 지원 |
| Anthropic | ✅ | ⚠️ | Seed 제한적 |
| Ollama | ✅ | ✅ | 모델별 차이 |
| vLLM | ✅ | ✅ | 완전 지원 |
| Azure | ✅ | ✅ | OpenAI와 동일 |

**참고:** RAGAS 메트릭 평가는 InstructorLLM을 통해 내부적으로 처리되므로, 직접 설정한 파라미터가 항상 적용되는 것은 아닙니다. 재현성이 중요한 경우, 여러 실행의 평균을 사용하거나 모델별 API를 직접 호출하는 것을 고려하세요.

---

## 참고

- 병렬 실행 로직: `src/evalvault/domain/services/batch_executor.py`
- 적응형 배치 실행기: `src/evalvault/domain/services/async_batch_executor.py`
- 평가 핵심 루프: `src/evalvault/domain/services/evaluator.py`
- 재현성 분석: `docs/internal/reports/TEMPERATURE_SEED_ANALYSIS.md`
