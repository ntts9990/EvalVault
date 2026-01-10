# 벤치마크 통합 중간 진행 기록

> **Last Updated**: 2026-01-11
> **Status**: 진행 중 (lm-eval 우선 통합)

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
| `api` | 운영 서버/상용 API 연동 | task 제한 있을 수 있음 | OpenAI 호환 서버 |

### 4.2 EvalVault vLLM 현황
- **OpenAI-compatible API 방식으로 동작**
- `vllm_base_url` + `OpenAI` 클라이언트 사용
- lm-eval에서는 `local-completions` / `local-chat-completions` 매핑

### 4.3 설치 권장
```bash
pip install "lm_eval[hf,vllm,api]"
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

### 즉시 진행
- [x] lm-eval 백엔드 전략 확정
- [x] EvalVault ↔ lm-eval 모델 인자 매핑표 작성
- [ ] KMMLU 로컬 로딩 테스트 (외부망에서 다운로드 후 검증)
- [ ] lm-eval 어댑터 설계 착수

### 단기 (1-2주)
- [ ] `evalvault benchmark kmmlu` CLI 명령어 구현
- [ ] 시각화 breakdown 연동 구현
- [ ] 보험 도메인 KMMLU 평가 파일럿

### 중기 (1개월)
- [ ] HRET 검증 체크리스트 실행
- [ ] 검증 통과 시 HRET 선택 통합

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

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-11 | 초안 작성 (lm-eval 우선 통합 계획) |
