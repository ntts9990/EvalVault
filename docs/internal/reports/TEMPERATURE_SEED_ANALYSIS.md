# Temperature/Seed 설정 분석 리포트

## 핵심 질문에 대한 답변

### 1. Temperature=0.0이 RAGAS 권장사항인가?

**답변: ❌ 아니오**

- RAGAS 0.4.2 공식 문서에서 `temperature=0.0`을 명시적으로 권장하지 않음
- 일부 모델에서는 `temperature=0` 설정이 오류를 발생시킬 수 있음 (예: HuggingFace GPT-2)
- 일반적으로 재현성을 높이기 위한 방법이지만, RAGAS 공식 권장사항은 아님

### 2. 모델마다 API가 다른데 우리 시스템에 적용 가능한가?

**답변: ⚠️ 부분적으로 가능하지만 제한적**

#### 현재 시스템 구조의 문제점

1. **InstructorLLM 래핑 구조**
   - Ragas는 `InstructorLLM`을 통해 LLM을 사용
   - `InstructorLLM`은 내부적으로 OpenAI/Anthropic 클라이언트를 래핑
   - Ragas 메트릭이 LLM을 호출할 때는 Instructor가 내부적으로 처리
   - 우리가 설정한 파라미터가 실제로 전달되는지 불명확

2. **모델별 API 차이**
   - **OpenAI**: `temperature`, `seed` 지원
   - **Anthropic**: `temperature` 지원, `seed`는 제한적
   - **Ollama**: `temperature`, `seed` 지원 (일부 모델)
   - **vLLM**: `temperature`, `seed` 지원
   - **Azure**: OpenAI와 동일

3. **현재 구현 상태**
   - `TokenTrackingAsyncOpenAI`의 `create()` 메서드에서 kwargs를 받아 전달
   - 하지만 Ragas 메트릭이 호출할 때는 Instructor가 처리하므로 직접 제어 어려움

#### 적용 가능성

**가능한 방법:**
1. `TokenTrackingAsyncOpenAI`의 `create()` 메서드에서 기본 파라미터 주입
2. Settings에 옵션 추가하고, 클라이언트 래퍼에서 주입

**제한사항:**
1. Instructor가 내부적으로 처리하므로, 모든 호출에 적용되는지 불명확
2. 일부 모델에서는 지원하지 않을 수 있음
3. Ragas 메트릭이 직접 클라이언트를 호출하는 경우에만 적용 가능

---

## 실용적인 접근 방안

### 옵션 1: 문서화 중심 (권장)

**장점:**
- 구현 복잡도 낮음
- 모델별 차이를 명확히 문서화
- 사용자가 필요시 직접 설정 가능

**단점:**
- 자동으로 재현성 보장 안 됨

**구현:**
- 재현성 가이드 문서 작성
- 모델별 설정 방법 설명
- 주의사항 명시

### 옵션 2: 선택적 파라미터 주입

**장점:**
- 일부 모델에서 재현성 개선 가능
- 사용자가 선택적으로 사용 가능

**단점:**
- 모든 모델에서 작동하지 않을 수 있음
- Instructor 래핑으로 인해 적용 여부 불명확
- 구현 복잡도 증가

**구현:**
- Settings에 `llm_temperature`, `llm_seed` 옵션 추가
- `TokenTrackingAsyncOpenAI`에서 기본값 주입
- 모델별 지원 여부 문서화

### 옵션 3: 하이브리드 접근

**장점:**
- 문서화 + 선택적 구현
- 사용자 선택권 제공

**구현:**
- 재현성 가이드 문서 작성
- Settings에 옵션 추가 (기본값 None)
- 지원하는 모델에서만 적용
- 명확한 경고 메시지

---

## 권장 사항

### 즉시 조치: 문서화

1. **재현성 가이드 작성**
   - `docs/guides/REPRODUCIBILITY.md` 생성
   - 모델별 Temperature/Seed 설정 방법
   - 주의사항 및 제한사항 명시

2. **기존 문서 업데이트**
   - `docs/guides/USER_GUIDE.md`에 재현성 섹션 추가
   - `docs/guides/RAGAS_PERFORMANCE_TUNING.md`에 관련 내용 추가

### 선택적 조치: 파라미터 주입 (필요시)

1. Settings에 옵션 추가
2. 지원하는 모델에서만 적용
3. 명확한 경고 메시지

---

## 모델별 지원 현황

| 모델 | Temperature | Seed | 비고 |
|------|-------------|------|------|
| OpenAI | ✅ | ✅ | 완전 지원 |
| Anthropic | ✅ | ⚠️ | Seed 제한적 |
| Ollama | ✅ | ✅ | 모델별 차이 |
| vLLM | ✅ | ✅ | 완전 지원 |
| Azure | ✅ | ✅ | OpenAI와 동일 |

---

## 결론

1. **Temperature=0.0은 RAGAS 권장사항이 아님**
   - 일반적인 재현성 방법이지만 공식 권장사항 아님
   - 일부 모델에서 오류 발생 가능

2. **모델별 API 차이로 인한 제한**
   - Instructor 래핑 구조로 인해 직접 제어 어려움
   - 모든 모델에서 작동하지 않을 수 있음

3. **권장 접근: 문서화 중심**
   - 재현성 가이드 작성
   - 모델별 설정 방법 설명
   - 사용자가 필요시 직접 설정

4. **선택적 구현**
   - Settings에 옵션 추가 (기본값 None)
   - 지원하는 모델에서만 적용
   - 명확한 경고 메시지

---

**작성일:** 2025-01-XX
**상태:** 분석 완료, 문서화 권장
