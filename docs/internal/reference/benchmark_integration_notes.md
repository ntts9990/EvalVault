# 벤치마크 통합 중간 진행 기록

> **Last Updated**: 2026-01-11 (3차 업데이트)
> **Status**: 진행 중 (lm-eval 어댑터, CLI, Thinking Model 지원, Phoenix 트레이싱 완료)

---

## 1. 배경 및 목표

### 1.1 핵심 목표
**다차원 성능 분석 체계 구축**
- 단일 점수가 아닌 여러 축으로 모델/RAG 품질을 평가
- 신뢰도, 정확도, 영업 근거 등 파생 가치 확보

### 1.2 다차원 분석 축 정의
| 축 | 지표 | 의미 |
|----|------|------|
| **정확도** | EM/F1, KMMLU Accuracy | 정답이 맞는가 |
| **근거성** | Faithfulness/Claim-level | 근거 기반인가 |
| **관련성** | Answer Relevancy / Contextual Relevancy | 질문과 맥락이 맞는가 |
| **안정성** | No-Answer Accuracy / Confidence | 리스크 회피가 되는가 |

---

## 2. 결정 사항

### 2.1 시각화 통합 전략
- **기존 3축(x/y/z) 유지**
- **새 차원은 `breakdown`/`stats` 레이어로 확장**
- 시각화 담당 에이전트 작업과 충돌 방지

**삽입 구조 예시**
```json
"breakdown": {
  "benchmark": {
    "kmmlu_accuracy": 0.72,
    "kmmlu_subject_accuracy": {
      "보험학": 0.81,
      "금융": 0.75
    }
  }
}
```

### 2.2 벤치마크 도구 우선순위
| 순위 | 도구 | 이유 |
|------|------|------|
| **1순위** | lm-evaluation-harness | 성숙도 높음, 폐쇄망 대응 용이, 결과 포맷 안정 |
| **2순위** | HRET | 한국어 특화 강점, API 아직 유동적 → 검증 후 선택 통합 |

### 2.3 KMMLU 도입 범위
- **우선 도메인**: 보험학 + 금융
- **확장 계획**: 회계/경제학 (Phase 2)

---

## 3. 폐쇄망 운영 전략

### 3.1 데이터 반입 흐름
**외부망**
```bash
python -c "from datasets import load_dataset; \
ds = load_dataset('HAERAE-HUB/KMMLU', 'Insurance'); \
ds.save_to_disk('./kmmlu_insurance')"
tar -czf kmmlu_insurance.tar.gz kmmlu_insurance
```

**폐쇄망**
```bash
tar -xzf kmmlu_insurance.tar.gz -C /data/benchmarks
```

### 3.2 데이터 저장 원칙
- **프로젝트 저장소에는 포함하지 않음** (용량/라이선스 이슈)
- 로컬 경로로 분리 저장
- 기본 경로: `data/benchmarks/kmmlu/insurance`

---

## 4. lm-eval 백엔드 전략

### 4.1 백엔드 비교
| 백엔드 | 장점 | 단점 | 적합 상황 |
|--------|------|------|----------|
| `hf` | 완전 로컬/폐쇄망 적합 | GPU 메모리 요구 큼 | 로컬 체크포인트 |
| `vllm` | 가장 빠름, 대규모 모델 효율적 | vLLM 서버 필요 | vLLM 기반 RAG 시스템 |
| `ollama` | 로컬 실행 용이, thinking 모델 지원 | 상대적 느린 속도 | 개발/테스트, thinking 모델 |
| `api` | 운영 서버/상용 API 연동 | task 제한 있을 수 있음 | OpenAI 호환 서버 |

### 4.2 EvalVault vLLM 현황
- **OpenAI-compatible API 방식으로 동작**
- `vllm_base_url` + `OpenAI` 클라이언트 사용
- lm-eval에서는 `local-completions` / `local-chat-completions` 매핑

### 4.3 설치 권장
```bash
pip install "lm_eval[hf,vllm,api]"
```

### 4.4 Ollama Thinking Model 지원

**Thinking Model**이란 응답에 별도의 `thinking` 필드로 추론 과정을 출력하는 모델입니다.
(예: `gpt-oss-safeguard:20b`, `deepseek-r1:*` 등)

**문제점**
1. OpenAI-compatible API에서 `max_tokens`에 thinking 토큰이 포함되어 조기 종료 발생
2. Stop sequence (`.`, `\n\n`)가 thinking 단계에서 트리거되어 응답 절단
3. 최종 답변이 verbose한 형태 (예: `정답: **B**`)로 나와 exact match 실패

**해결 방안 (lm_eval_adapter.py)**
```python
# 1. Thinking 모델 자동 감지
def _is_ollama_thinking_model(self, model: str) -> bool:
    # 테스트 API 호출로 thinking 필드 존재 여부 확인

# 2. max_gen_toks 증가 (256 → 8192)
self.max_gen_toks = 8192 if is_thinking else 256

# 3. Stop sequence 수정
# 기본: [".", "\n\n"] → Thinking용: ["Q:", "\n\n\n"]

# 4. MCQ 추출 정규식
def _parse_results_with_mcq_extraction(self, results: dict) -> dict:
    # 응답에서 첫 번째 A/B/C/D 추출
    pattern = r'\b([A-D])\b'
```

**사용 예시**
```bash
# Thinking 모델로 KMMLU 실행
evalvault benchmark kmmlu -s Accounting --backend ollama -m gpt-oss-safeguard:20b --limit 10
```

---

## 5. EvalVault ↔ lm-eval 모델 인자 매핑

### 5.1 vLLM (OpenAI-compatible)
| EvalVault 설정 | lm-eval 인자 |
|---------------|-------------|
| `vllm_base_url` | `base_url` |
| `vllm_model` | `model` |
| `vllm_api_key` | (기본 `"local"`) |

**lm-eval 실행 예시**
```bash
lm_eval --model local-chat-completions \
  --model_args model=<model_name>,base_url=http://<host>:8000/v1 \
  --tasks kmmlu_insurance \
  --batch_size auto
```

### 5.2 HuggingFace 로컬
| EvalVault 설정 | lm-eval 인자 |
|---------------|-------------|
| 로컬 체크포인트 경로 | `pretrained=/path/to/model` |

**lm-eval 실행 예시**
```bash
lm_eval --model hf \
  --model_args pretrained=/data/models/my-model \
  --tasks kmmlu_insurance \
  --device cuda:0 \
  --batch_size 8
```

### 5.3 OpenAI API
| EvalVault 설정 | lm-eval 인자 |
|---------------|-------------|
| `openai_api_key` | `OPENAI_API_KEY` 환경변수 |
| `openai_model` | `model` |

**lm-eval 실행 예시**
```bash
export OPENAI_API_KEY=<key>
lm_eval --model openai-chat-completions \
  --model_args model=gpt-4 \
  --tasks kmmlu_insurance
```

---

## 6. 시각화 연동 스펙

### 6.1 `VisualSpaceService` 확장 포인트
- 기존 `breakdown` 필드에 `benchmark` 키 추가
- 축 변경 없이 UI 툴팁/패널에서 노출

### 6.2 데이터 구조
```python
"breakdown": {
    # 기존 필드 유지
    "phoenix_drift": 0.12,
    "regression_rate": 0.03,
    "variance": 0.08,
    "reliability": 0.85,
    "prompt_risk": 0.02,

    # 신규 벤치마크 필드
    "benchmark": {
        "kmmlu_accuracy": 0.72,
        "kmmlu_subject_accuracy": {
            "보험학": 0.81,
            "금융": 0.75,
            "회계": 0.68
        }
    }
}
```

---

## 7. HRET 검증 체크리스트 (후순위)

### 7.1 배포/설치 가능성
- [ ] PyPI 배포 여부 확인
- [ ] 설치 방식: `pip install` vs `git clone`
- [ ] 라이선스 확인 (기업 배포 가능 여부)

### 7.2 폐쇄망 데이터 접근성
- [ ] 로컬 파일 로드 지원 여부
- [ ] HuggingFace Hub 연결 없이 동작 가능 여부
- [ ] KMMLU 로컬 경로 로딩 지원

### 7.3 평가 실행 구조
- [ ] 모델 호출 방식 확인 (API / 로컬 / vLLM)
- [ ] EvalVault profile ↔ 모델 이름 매핑 가능 여부
- [ ] 배치 처리 / 타임아웃 / retry 설정 가능 여부

### 7.4 결과 포맷 호환성
- [ ] EvalVault 리포트 포맷 변환 가능 여부
- [ ] 다차원 축 매핑 가능 여부
- [ ] `VisualSpaceService` breakdown 삽입 가능 여부

### 7.5 안정성/유지보수
- [ ] 최근 업데이트/커뮤니티 활동 유지 여부
- [ ] API 안정성(버전 변경 빈도)
- [ ] EvalVault 내부 모듈과 충돌 없음

---

## 8. 다음 단계 체크리스트

### 즉시 진행 (완료)
- [x] lm-eval 백엔드 전략 확정
- [x] EvalVault ↔ lm-eval 모델 인자 매핑표 작성
- [x] lm-eval 어댑터 구현 (`src/evalvault/adapters/outbound/benchmark/lm_eval_adapter.py`)
- [x] 벤치마크 포트 정의 (`src/evalvault/ports/outbound/benchmark_port.py`)
- [x] `evalvault benchmark kmmlu` CLI 명령어 구현
- [x] KMMLU 로컬 다운로드 스크립트 (`scripts/benchmark/download_kmmlu.py`)
- [x] Ollama thinking model 자동 감지 및 지원
- [x] Phoenix 트레이싱 연동 (`--phoenix` CLI 옵션)
- [x] 벤치마크 결과 DB 저장 (BenchmarkStorageAdapter)

### 단기 (1-2주)
- [ ] 실제 vLLM 서버로 KMMLU 평가 파일럿 테스트
- [ ] 폐쇄망 환경에서 로컬 로딩 검증
- [ ] 보험 도메인 KMMLU 평가 실행 및 결과 분석

### 중기 (1개월)
- [ ] HRET 검증 체크리스트 실행
- [ ] 검증 통과 시 HRET 선택 통합
- [ ] 시각화 breakdown 연동 (VisualSpaceService 구현 후)

---

## 9. 참고 자료

### lm-evaluation-harness
- GitHub: https://github.com/EleutherAI/lm-evaluation-harness
- 문서: CLI Reference, Configuration Guide, Task Guide

### HRET (Haerae Evaluation Toolkit)
- GitHub: https://github.com/HAE-RAE/haerae-evaluation-toolkit
- 논문: arXiv:2503.22968

### KMMLU
- HuggingFace: `HAERAE-HUB/KMMLU`
- 서브셋: Insurance, Finance, Accounting 등 45개 분야

---

## 10. 구현된 파일 목록

| 파일 | 설명 |
|------|------|
| `src/evalvault/ports/outbound/benchmark_port.py` | 벤치마크 포트 인터페이스 (BenchmarkRequest, BenchmarkResponse) |
| `src/evalvault/adapters/outbound/benchmark/__init__.py` | 벤치마크 어댑터 모듈 |
| `src/evalvault/adapters/outbound/benchmark/lm_eval_adapter.py` | lm-evaluation-harness 어댑터 (thinking model 지원 포함) |
| `src/evalvault/adapters/outbound/storage/benchmark_storage_adapter.py` | 벤치마크 결과 DB 저장 어댑터 |
| `src/evalvault/domain/entities/benchmark_run.py` | 벤치마크 실행 엔티티 (BenchmarkRun, BenchmarkResult) |
| `src/evalvault/domain/services/benchmark_service.py` | 벤치마크 서비스 (오케스트레이션) |
| `src/evalvault/adapters/inbound/cli/commands/benchmark.py` | `evalvault benchmark kmmlu` CLI 명령어 (Phoenix 트레이싱 지원) |
| `src/evalvault/adapters/inbound/api/routers/benchmark.py` | 벤치마크 API 라우터 |
| `scripts/benchmark/download_kmmlu.py` | KMMLU 다운로드/로드 스크립트 |
| `tests/unit/test_lm_eval_adapter.py` | lm-eval 어댑터 유닛 테스트 |
| `tests/integration/benchmark/` | 벤치마크 통합 테스트 |

---

## 11. 사용 예시

### CLI로 KMMLU 벤치마크 실행

```bash
# Ollama 백엔드로 보험 도메인 KMMLU 실행
evalvault benchmark kmmlu -s Insurance --backend ollama -m gemma3:1b

# Thinking 모델로 실행 (자동 감지됨)
evalvault benchmark kmmlu -s Accounting --backend ollama -m gpt-oss-safeguard:20b --limit 10

# Phoenix 트레이싱 활성화
evalvault benchmark kmmlu -s Insurance --backend ollama -m gemma3:1b --phoenix

# vLLM 백엔드로 실행
evalvault benchmark kmmlu -s Insurance --backend vllm

# 여러 도메인 동시 실행
evalvault benchmark kmmlu -s "Insurance,Finance" -m llama2

# 테스트용 샘플 제한
evalvault benchmark kmmlu -s Insurance --limit 10 -o results.json
```

### Python API로 직접 사용

```python
from evalvault.adapters.outbound.benchmark import LMEvalAdapter
from evalvault.ports.outbound.benchmark_port import BenchmarkBackend, BenchmarkRequest
from evalvault.config.settings import get_settings

settings = get_settings()
adapter = LMEvalAdapter(settings=settings)

request = BenchmarkRequest(
    tasks=["kmmlu_insurance", "kmmlu_finance"],
    backend=BenchmarkBackend.VLLM,
    num_fewshot=5,
    limit=100,  # 테스트용
)

response = adapter.run_benchmark(request)
print(response.to_breakdown_dict())
```

---

## 12. Thinking Model 상세 구현

### 12.1 문제 상황

Ollama의 thinking 모델(예: `gpt-oss-safeguard:20b`, `deepseek-r1:*`)은 응답에 `thinking` 필드로
추론 과정을 별도로 출력합니다. lm-evaluation-harness와 연동 시 다음 문제가 발생했습니다:

1. **max_tokens 문제**: OpenAI-compatible API에서 `max_tokens`에 thinking 토큰이 포함되어
   실제 답변이 잘리는 현상
2. **Stop sequence 문제**: 기본 stop sequence (`.`, `\n\n`)가 thinking 단계에서 트리거되어
   응답이 조기 종료됨
3. **Verbose 응답**: 최종 답변이 `정답: **B**` 같은 형태로 나와 exact match 실패

### 12.2 해결 방안

```python
# lm_eval_adapter.py

class LMEvalAdapter:
    def _is_ollama_thinking_model(self, model: str) -> bool:
        """테스트 API 호출로 thinking 필드 존재 여부 확인"""
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10
        )
        # response.choices[0].message에 thinking 속성이 있으면 True
        return hasattr(response.choices[0].message, "thinking")

    def _build_model_args_from_settings(self, ...):
        # Thinking 모델 감지
        is_thinking = self._is_ollama_thinking_model(model)
        self._ollama_is_thinking = is_thinking

        if is_thinking:
            # 1. max_gen_toks 증가 (thinking 토큰 포함)
            self.max_gen_toks = 8192

            # 2. Stop sequence 수정
            gen_kwargs["stop"] = ["Q:", "\n\n\n"]

    def _parse_results_with_mcq_extraction(self, results: dict) -> dict:
        """Thinking 모델의 verbose 응답에서 첫 번째 A/B/C/D 추출"""
        pattern = r'\b([A-D])\b'
        # log_samples에서 응답 파싱 후 정답 추출
```

### 12.3 테스트 결과

| 모델 | 백엔드 | 정확도 | 비고 |
|------|--------|--------|------|
| `gemma3:1b` | ollama | ~10% | 소형 모델 |
| `gpt-oss-safeguard:20b` | ollama | 80-100% | Thinking 모델, MCQ 추출 적용 |

---

## 13. Phoenix 트레이싱 연동

### 13.1 활성화 방법

```bash
# CLI 옵션으로 활성화
evalvault benchmark kmmlu -s Insurance --backend ollama -m gemma3:1b --phoenix
```

### 13.2 구현 상세

```python
# benchmark.py CLI

@app.command("kmmlu")
def benchmark_kmmlu(
    ...
    phoenix: bool = typer.Option(False, "--phoenix", help="Enable Phoenix tracing"),
):
    if phoenix:
        from evalvault.adapters.outbound.tracing.phoenix_adapter import (
            ensure_phoenix_instrumentation,
        )
        ensure_phoenix_instrumentation()
```

Phoenix 트레이싱이 활성화되면 lm-eval의 모든 LLM 호출이 자동으로 추적됩니다.

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-11 | 초안 작성 (lm-eval 우선 통합 계획) |
| 2026-01-11 | lm-eval 어댑터 및 CLI 구현 완료, 사용 예시 추가 |
| 2026-01-11 | Ollama thinking model 지원, Phoenix 트레이싱 연동, DB 저장 추가 |
