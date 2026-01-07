# RAGAS 0.4.2 호환성 및 재현성 검증 계획

## 목적

EvalVault가 RAGAS 0.4.2 프레임워크에서 제안한 메트릭 평가 방식을 정확히 따르고 있는지 확인하고, 다른 사용자들이 동일한 환경에서 유사한 결과를 얻을 수 있는지 검증합니다.

---

## 1. 현재 상태 분석

### 1.1 RAGAS 버전 및 의존성 확인

**검증 항목:**
- [ ] `uv.lock`에서 ragas 버전 확인 (예상: 0.4.2)
- [ ] `pyproject.toml`의 ragas 의존성 버전 범위 확인
- [ ] 실제 설치된 ragas 버전과 문서화된 버전 일치 여부

**확인 위치:**
- `uv.lock` (line 4178-4203)
- `pyproject.toml` (dependencies 섹션)

**현재 상태:**
- `uv.lock`에서 `ragas-0.4.2` 확인됨
- `pyproject.toml`에 버전 고정 없음 (최신 버전 사용)

---

### 1.2 RAGAS API 사용 방식 검증

**검증 항목:**
- [ ] 메트릭 초기화 방식이 RAGAS 0.4.2 권장 방식과 일치하는지
- [ ] `ascore()` API 사용 여부 (RAGAS 0.4+ 표준)
- [ ] 메트릭별 필수 인자 전달 방식 확인
- [ ] SingleTurnSample 변환 로직 검증

**확인 위치:**
- `src/evalvault/domain/services/evaluator.py` (line 298-366, 534-633)
- `src/evalvault/adapters/outbound/llm/instructor_factory.py`

**현재 상태:**
- ✅ `ascore()` API 사용 중 (line 556, 570)
- ✅ `single_turn_ascore()` fallback 지원 (line 572-574)
- ✅ 메트릭별 required arguments 정의됨 (line 103-111)
- ✅ SingleTurnSample 변환 로직 존재 (line 321-330)

**검증 필요:**
- RAGAS 0.4.2 공식 문서와 인자 전달 방식 비교
- 메트릭 초기화 시 LLM/embeddings 전달 방식 확인

---

### 1.3 LLM 어댑터 및 RAGAS 통합 검증

**검증 항목:**
- [ ] InstructorLLM 생성 방식이 RAGAS 권장 방식과 일치하는지
- [ ] Embeddings 생성 방식 검증
- [ ] LLM provider별 일관성 확인

**확인 위치:**
- `src/evalvault/adapters/outbound/llm/instructor_factory.py`
- `src/evalvault/adapters/outbound/llm/openai_adapter.py`
- `src/evalvault/adapters/outbound/llm/ollama_adapter.py`
- `src/evalvault/adapters/outbound/llm/base.py`

**현재 상태:**
- ✅ `create_instructor_llm()` 함수로 일관된 LLM 생성
- ✅ OpenAI, Ollama, Azure, Anthropic 어댑터 지원
- ✅ Embeddings는 `create_openai_embeddings_with_legacy()` 사용

**검증 필요:**
- RAGAS 0.4.2의 `llm_factory`/`embedding_factory` 사용 여부 확인
- Instructor 패키지 버전 호환성 확인

---

## 2. 재현성 검증

### 2.1 LLM 파라미터 설정 검증

**검증 항목:**
- [ ] Temperature 설정 여부 (재현성을 위해 0.0 권장)
- [ ] Seed 설정 여부 (결정론적 결과를 위해 필수)
- [ ] Top-p, Top-k 등 샘플링 파라미터 설정
- [ ] Provider별 파라미터 전달 방식 확인

**확인 위치:**
- `src/evalvault/adapters/outbound/llm/*_adapter.py`
- `src/evalvault/adapters/outbound/llm/instructor_factory.py`
- `src/evalvault/config/settings.py`

**현재 상태:**
- ⚠️ Temperature, seed 설정이 명시적으로 보이지 않음
- ⚠️ LLM 호출 시 파라미터 전달 로직 확인 필요

**개선 필요:**
- Temperature=0.0 기본값 설정
- Seed 설정 옵션 추가
- 설정 문서화

---

### 2.2 임베딩 모델 재현성

**검증 항목:**
- [ ] 동일 입력에 대한 임베딩 결과 일관성
- [ ] 임베딩 모델 버전 고정 여부
- [ ] Matryoshka dimension 설정의 재현성

**확인 위치:**
- `src/evalvault/adapters/outbound/llm/ollama_adapter.py` (line 139-201)
- `src/evalvault/adapters/outbound/llm/base.py` (line 180-218)

**현재 상태:**
- ✅ 임베딩 모델명은 설정에서 관리
- ⚠️ Matryoshka dimension이 동적으로 설정 가능 (재현성 저해 가능)

---

### 2.3 평가 순서 및 병렬 처리 영향

**검증 항목:**
- [ ] 순차 평가 vs 병렬 평가 결과 일관성
- [ ] 배치 크기가 결과에 미치는 영향
- [ ] 비결정론적 요소 (타이밍, 네트워크 등)의 영향

**확인 위치:**
- `src/evalvault/domain/services/evaluator.py` (line 368-532)
- `src/evalvault/domain/services/batch_executor.py`

**현재 상태:**
- ✅ 순차 평가와 병렬 평가 모두 지원
- ⚠️ 병렬 평가 시 결과 일관성 검증 필요

---

## 3. RAGAS 0.4.2 공식 문서 대조

### 3.1 메트릭 초기화 방식

**검증 항목:**
- [ ] RAGAS 0.4.2 공식 문서의 메트릭 초기화 예제와 비교
- [ ] LLM/embeddings 전달 방식 일치 여부
- [ ] 메트릭별 옵션 파라미터 지원 여부

**검증 방법:**
1. RAGAS 0.4.2 공식 문서/예제 코드 수집
2. 현재 구현과 비교 분석
3. 차이점 문서화

---

### 3.2 ascore() API 사용 방식

**검증 항목:**
- [ ] 인자 이름이 RAGAS 0.4.2와 일치하는지
- [ ] 필수/선택 인자 구분이 올바른지
- [ ] 반환값 처리 방식 확인

**현재 구현:**
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

**검증 필요:**
- RAGAS 0.4.2 문서의 인자 이름 확인
- None 값 처리 방식이 올바른지

---

### 3.3 SingleTurnSample 변환

**검증 항목:**
- [ ] 필드 매핑이 RAGAS 0.4.2와 일치하는지
- [ ] None 값 처리 방식
- [ ] 컨텍스트 리스트 형식 확인

**현재 구현:**
```python
# evaluator.py line 324-329
sample = SingleTurnSample(
    user_input=test_case.question,
    response=test_case.answer,
    retrieved_contexts=test_case.contexts,
    reference=test_case.ground_truth,
)
```

---

## 4. 재현성 테스트 계획

### 4.1 동일 환경 재실행 테스트

**목적:** 동일한 환경에서 동일한 데이터셋을 여러 번 실행하여 결과 일관성 확인

**절차:**
1. 고정된 데이터셋 준비 (예: `tests/fixtures/e2e/insurance_qa_korean.json`)
2. 동일한 LLM 모델 및 설정으로 3회 실행
3. 결과 비교:
   - 메트릭 점수 차이 분석
   - 토큰 사용량 일관성 확인
   - 실행 시간 변동성 측정

**기대 결과:**
- LLM이 결정론적이면 점수 차이 < 0.01
- LLM이 비결정론적이면 점수 차이 범위 문서화

---

### 4.2 다른 환경 재현성 테스트

**목적:** 다른 사용자가 동일한 설정으로 실행했을 때 유사한 결과를 얻는지 확인

**절차:**
1. 재현 가능한 설정 파일 생성:
   - `config/models.yaml` 스냅샷
   - `.env.example` 업데이트
   - Python/ragas 버전 고정
2. 테스트 스크립트 작성:
   - 자동화된 평가 실행
   - 결과 저장 및 비교
3. 여러 환경에서 실행:
   - 다른 머신
   - 다른 시점
   - 다른 사용자

**검증 항목:**
- 메트릭 점수 범위 (예: ±0.05 이내)
- 상대적 순서 일관성
- 에러 발생 패턴

---

### 4.3 RAGAS 공식 예제와 비교

**목적:** RAGAS 공식 문서의 예제 코드와 동일한 결과를 얻는지 확인

**절차:**
1. RAGAS 0.4.2 공식 예제 코드 수집
2. EvalVault로 동일한 평가 실행
3. 결과 비교 및 차이점 분석

---

## 5. 문서화 및 개선 계획

### 5.1 재현성 가이드 작성

**내용:**
- 재현 가능한 평가를 위한 설정 방법
- Temperature, seed 등 파라미터 설명
- 환경별 차이점 및 대응 방법

**위치:**
- `docs/guides/REPRODUCIBILITY.md` (신규 생성)

---

### 5.2 설정 검증 도구

**기능:**
- 현재 설정이 재현 가능한지 검증
- 누락된 파라미터 경고
- 권장 설정 제안

**구현 위치:**
- `scripts/verify_reproducibility.py` (신규 생성)

---

### 5.3 테스트 케이스 추가

**추가할 테스트:**
- [ ] 동일 입력에 대한 메트릭 점수 일관성 테스트
- [ ] RAGAS 공식 예제와의 호환성 테스트
- [ ] 환경별 재현성 테스트

**위치:**
- `tests/integration/test_ragas_reproducibility.py` (신규 생성)

---

## 6. 실행 계획

### Phase 1: 현재 상태 분석 (1-2일)

1. **RAGAS 0.4.2 문서 수집 및 분석**
   - 공식 문서 읽기
   - 예제 코드 분석
   - API 레퍼런스 확인

2. **코드베이스 분석**
   - `evaluator.py` 상세 분석
   - LLM 어댑터 통합 방식 확인
   - 설정 파일 검토

3. **차이점 문서화**
   - RAGAS 표준 vs 현재 구현 비교표 작성
   - 개선 필요 항목 식별

---

### Phase 2: 재현성 검증 (2-3일)

1. **동일 환경 재실행 테스트**
   - 고정 데이터셋으로 3회 실행
   - 결과 비교 및 분석

2. **파라미터 영향 분석**
   - Temperature 변경 시 결과 비교
   - Seed 설정 시 결과 비교
   - 병렬/순차 평가 결과 비교

3. **환경별 테스트**
   - 다른 Python 버전
   - 다른 OS
   - 다른 ragas 버전 (0.4.2 고정)

---

### Phase 3: 개선 및 문서화 (2-3일)

1. **재현성 개선**
   - Temperature=0.0 기본값 설정
   - Seed 설정 옵션 추가
   - 설정 검증 로직 추가

2. **문서 작성**
   - 재현성 가이드
   - RAGAS 호환성 문서
   - 설정 가이드 업데이트

3. **테스트 추가**
   - 재현성 테스트 케이스
   - 호환성 테스트 케이스

---

## 7. 검증 체크리스트

### RAGAS 0.4.2 호환성

- [ ] 메트릭 초기화 방식 일치
- [ ] `ascore()` API 올바른 사용
- [ ] 인자 이름 및 형식 일치
- [ ] SingleTurnSample 변환 정확
- [ ] LLM/embeddings 전달 방식 일치

### 재현성

- [ ] 동일 환경에서 결과 일관성 확인
- [ ] Temperature 설정 문서화
- [ ] Seed 설정 옵션 제공
- [ ] 환경별 차이점 문서화
- [ ] 재현 가능한 설정 가이드 제공

### 문서화

- [ ] RAGAS 호환성 문서 작성
- [ ] 재현성 가이드 작성
- [ ] 설정 가이드 업데이트
- [ ] 테스트 결과 문서화

---

## 8. 참고 자료

- RAGAS 0.4.2 공식 문서: https://docs.ragas.io/
- RAGAS GitHub: https://github.com/explodinggradients/ragas
- Instructor 패키지: https://github.com/jxnl/instructor

---

## 9. 예상 이슈 및 대응

### 이슈 1: LLM 비결정론성

**문제:** LLM이 temperature=0이어도 비결정론적일 수 있음

**대응:**
- 결과 범위 문서화
- 상대적 순서 일관성 검증
- Seed 설정 옵션 제공

### 이슈 2: RAGAS API 변경

**문제:** RAGAS 0.4.2와 현재 구현 간 API 차이

**대응:**
- 차이점 문서화
- 호환성 레이어 추가
- 버전별 분기 처리

### 이슈 3: 환경별 차이

**문제:** 다른 환경에서 다른 결과

**대응:**
- 환경 요구사항 명시
- Docker 컨테이너 제공
- 버전 고정 가이드

---

## 10. 성공 기준

1. **호환성:** RAGAS 0.4.2 공식 예제와 동일한 방식으로 메트릭 평가 수행
2. **재현성:** 동일 환경에서 3회 실행 시 메트릭 점수 차이 < 0.05
3. **문서화:** 재현 가능한 평가를 위한 완전한 가이드 제공
4. **검증:** 자동화된 테스트로 지속적 검증

---

**작성일:** 2025-01-XX
**담당자:** [작성자명]
**상태:** 계획 수립 완료, 실행 대기
