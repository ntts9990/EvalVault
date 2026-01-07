# 보험 도메인 한/영 RAG 시스템 평가 프레임워크 (최종본)

## 문서 정보
- **버전:** v3.0 (Final)
- **대상 시스템:** 보험 도메인 Q&A + 요약 RAG 시스템
- **언어 환경:** 한국어/영어 이중 언어
- **현재 단계:** 개발 중 (PoC/Pilot)

---

## Executive Summary

보험 도메인 RAG 시스템은 **"침묵의 실패(Silent Failure)"**가 가장 위험합니다. 검색이 실패했음에도 LLM이 그럴듯한 답변을 생성하면 면책 조항 누락, 보장 범위 오판 등 치명적 결과로 이어집니다.

본 프레임워크의 핵심 원칙:

1. **P0 게이트 4종 동시 적용:** Context Recall + Faithfulness + Factual Correctness + Citation Coverage
2. **Claim(주장) 단위 평가:** Response-level이 아닌 claim-level로 분해하여 디버깅·감사 대응
3. **개발/운영 HITL 분리:** 개발 중에는 플래그 기반 배치 리뷰, 운영 중에는 실시간 게이팅
4. **한국어 특화 처리:** N-gram 메트릭 한계 인식, 의미 기반 평가 중심

---

## 1. 평가 목표 정의

보험 Q&A/요약에서 "좋은 답변"의 기준:

| 목표 | 설명 | 우선순위 |
|------|------|----------|
| **(A) 검색 완전성** | 답에 필요한 조항/예외/면책/특약을 빠짐없이 가져왔는가? | P0 |
| **(B) 근거 충실도** | 답변의 모든 주장이 검색 문맥으로부터 지지되는가? (환각 차단) | P0 |
| **(C) 사실 정확도** | 답변이 정답(정책/약관/업무 규정)과 일치하는가? | P0 |
| **(D) 감사 가능성** | 답변이 어떤 문서/조항/페이지/표에 근거하는지 추적 가능한가? | P0 |
| **(E) 한/영 일관성** | 질의 언어/문서 언어가 달라도 의미 손실 없이 동일한 판단을 내리는가? | P0 보조 |

---

## 2. 메트릭 우선순위 체계

### 2.1 P0: 게이트 지표 (4종 동시 적용)

**핵심 원칙:** 단일 점수가 아닌 4종을 동시에 게이트에 걸어야 합니다. 하나라도 실패 시 해당 건은 리뷰 대상으로 플래깅됩니다.

| 순위 | 메트릭 | 목적 | 보험 리스크 | 권장 임계값 (개발 초기) |
|------|--------|------|-------------|------------------------|
| **P0-1** | Context Recall | 필요한 근거(면책/예외/조건) 누락 여부 | 검색 실패는 이후 단계에서 복구 불가 | ≥0.85 |
| **P0-2** | Faithfulness / Groundedness | 답변이 검색 문맥에 의해 지지되는가 | "그럴듯한 거짓"이 가장 위험 | ≥0.90 |
| **P0-3** | Factual Correctness | 답변이 정답과 사실적으로 일치하는가 | 근거가 있어도 문서가 구버전이면 오답 | ≥0.80 |
| **P0-4** | Citation Coverage | 답변 각 주장에 근거 인용이 충분한가 | 감사/분쟁/민원 대응의 실전 요구 | ≥0.90 |

**P0 지표 간 관계:**

```
Context Recall ──→ Faithfulness ──→ Factual Correctness
    (검색)            (생성)            (정답 대비)
                         │
                         ▼
                  Citation Coverage
                    (감사 가능성)
```

- **Faithfulness는 높은데 Factual Correctness가 낮음:** 문서가 구버전이거나 GT 오류
- **Faithfulness가 낮은데 Factual Correctness가 높음:** 모델이 검색 문맥이 아닌 자체 지식으로 답변 (위험)
- **Context Recall이 낮음:** 이후 모든 지표가 무의미 (검색 실패)

### 2.2 P1: 품질 보증 지표 (모델 개선 방향)

| 메트릭 | 목적 | 보험에서 중요한 이유 | 권장 목표 |
|--------|------|---------------------|-----------|
| **Context Precision** | 노이즈 감소 | 유사 문구가 많아 헛근거가 섞이기 쉬움 | ≥0.70 |
| **Context Entities Recall** | 핵심 엔티티(날짜/금액/조항번호) 정확 검색 | 엔티티 오류가 곧 오판정 | ≥0.85 |
| **Noise Sensitivity** | 노이즈 문맥 무시 능력 | "비슷한 조항" 섞임으로 인한 오해 방지 | ≤0.15 |
| **Response Relevancy** | 질문 의도에 직접 답하는가 | 고객/상담 UX 품질 | ≥0.75 |

### 2.3 P2: 운영 관측 지표

| 메트릭 | 목적 | 개발 중 활용 | 운영 중 활용 |
|--------|------|-------------|-------------|
| **Outlier Detection** | 위험 답변 자동 검출 | 리뷰 플래그 자동 부착 | 상담 전환 트리거 |
| **언어 일치율** | 한/영 정책 위반 탐지 | 위반 건 플래깅 | 경고 메시지 표시 |
| **문서 버전 커버리지** | 구버전 인용 방지 | 버전 불일치 건 리포팅 | 재검색 트리거 |

---

## 3. HITL 프로세스: 개발 중 vs 운영 중

### 3.1 개발 중 HITL (현재 단계) — 플래그 기반 배치 리뷰

개발 단계에서는 실시간 상담원 연결이 불가능하므로, **평가 결과를 저장하고 플래그 시스템으로 관리**합니다.

#### 3.1.1 플래그 체계

```
┌─────────────────────────────────────────────────────────────────┐
│  평가 실행 (배치)                                                │
│  - 테스트셋 전체에 대해 P0/P1 메트릭 계산                         │
│  - 각 케이스별 Claim 단위 평가 로그 저장                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  자동 플래깅 (Flag Assignment)                                   │
│                                                                 │
│  🔴 CRITICAL (P0 실패)                                          │
│     - Context Recall < 0.85                                     │
│     - Faithfulness < 0.90                                       │
│     - Citation Coverage < 0.90                                  │
│     - 환각 Claim 1개 이상 탐지                                   │
│                                                                 │
│  🟠 WARNING (P1 미달 또는 이상 패턴)                             │
│     - Factual Correctness < 0.80                                │
│     - Context Precision < 0.70                                  │
│     - Faithfulness↑ + Factual Correctness↓ (문서 버전 의심)      │
│     - Faithfulness↓ + Factual Correctness↑ (자체 지식 의심)      │
│                                                                 │
│  🟢 PASSED (모든 P0 통과)                                        │
│     - 샘플링 대상으로 풀에 적재                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  리뷰 큐 (Review Queue)                                          │
│                                                                 │
│  [전량 리뷰]                                                     │
│  - 🔴 CRITICAL 플래그 전체                                       │
│  - 새로운 질문 유형 (클러스터링으로 탐지)                         │
│                                                                 │
│  [샘플 리뷰]                                                     │
│  - 🟠 WARNING 중 30%                                            │
│  - 🟢 PASSED 중 15-20%                                          │
│  - 층화 기준: 언어(한/영), 업무유형(Q&A/요약), 질문 복잡도        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  전문가 리뷰 (Expert Review)                                     │
│                                                                 │
│  리뷰 항목:                                                      │
│  1. 자동 평가 결과 동의/비동의                                   │
│  2. 실패 원인 분류 (검색/생성/GT/문서버전)                        │
│  3. 정답 수정 또는 GT 보강 제안                                   │
│  4. 리스크 등급 재평가                                           │
│                                                                 │
│  출력:                                                           │
│  - review_decision: agree | disagree | partial                  │
│  - failure_root_cause: retrieval | generation | gt | doc_version│
│  - corrected_answer: (수정된 정답, 있을 경우)                    │
│  - gt_update_needed: true | false                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  피드백 루프 (Feedback Loop)                                     │
│                                                                 │
│  → 검색 실패 다수: 인덱스/청킹/필터 전략 재검토                   │
│  → 환각 다수: 프롬프트/생성 정책 강화                             │
│  → GT 불일치 다수: Ground Truth 데이터셋 보강                     │
│  → 문서 버전 이슈: 문서 관리 프로세스 개선                        │
│                                                                 │
│  → 리뷰 완료 건 → Golden Dataset 확장                            │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 플래그 상태 스키마

```json
{
  "eval_id": "eval_20260107_001",
  "query_id": "q_123",
  "timestamp": "2026-01-07T10:30:00Z",

  "flag": {
    "level": "CRITICAL | WARNING | PASSED",
    "reasons": [
      "P0-2_FAITHFULNESS_BELOW_THRESHOLD",
      "HALLUCINATED_CLAIM_DETECTED"
    ],
    "auto_assigned": true
  },

  "review_status": {
    "in_queue": true,
    "queue_type": "FULL_REVIEW | SAMPLE_REVIEW",
    "assigned_reviewer": null,
    "review_deadline": "2026-01-10T18:00:00Z"
  },

  "review_result": {
    "completed": false,
    "reviewer_id": null,
    "review_decision": null,
    "failure_root_cause": null,
    "notes": null,
    "gt_update_needed": null
  }
}
```

#### 3.1.3 개발 중 리뷰 우선순위

| 우선순위 | 대상 | 리뷰 비율 | 목적 |
|----------|------|-----------|------|
| **1순위** | 🔴 CRITICAL 전체 | 100% | 치명적 실패 원인 분석 |
| **2순위** | 지표 간 불일치 건 | 100% | 시스템 이상 탐지 |
| **3순위** | 🟠 WARNING | 30% | 개선 방향 도출 |
| **4순위** | 🟢 PASSED | 15-20% | 자동 평가 신뢰도 검증 |

### 3.2 운영 중 HITL (향후 단계) — 실시간 게이팅

운영 단계에서는 실시간으로 게이팅하고, 실패 건은 즉시 대안 액션을 수행합니다.

```
사용자 질의
     ↓
┌─────────────────────────────────────────┐
│  RAG 파이프라인 실행                     │
│  검색 → 생성 → 실시간 평가               │
└─────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│  P0 게이트 (실시간)                      │
│                                         │
│  IF all P0 metrics >= threshold:        │
│     → 답변 제공                          │
│  ELIF Citation만 미달:                   │
│     → 답변 + "근거 불충분" 경고          │
│  ELIF Faithfulness 미달:                 │
│     → 답변 보류 + 재생성 시도            │
│  ELSE:                                   │
│     → 상담원 연결 / 에스컬레이션         │
└─────────────────────────────────────────┘
     ↓
[모든 건 로깅 → 배치 분석 → 모델 개선]
```

**운영 단계 임계값 (목표):**

| 단계 | Context Recall | Faithfulness | Factual Correctness | Citation Coverage | Deflection Rate |
|------|----------------|--------------|---------------------|-------------------|-----------------|
| 안정화 | ≥0.90 | ≥0.92 | ≥0.85 | ≥0.95 | 20-35% |
| 고도화 | ≥0.93 | ≥0.95 | ≥0.90 | ≥0.97 | ≤15% |

---

## 4. 요약 태스크 평가

### 4.1 요약 P0 지표

| 메트릭 | 목적 | 설정 |
|--------|------|------|
| **Summarization Score** | 정보 보존 + 간결성 | `coeff=0.3` (정보 보존 우선) |
| **Summary Faithfulness** | 요약 환각 차단 | 원문에 없는 주장 생성 탐지 |

**요약에서 특히 위험한 실패:**
- 면책/제외 조건이 반대로 요약되는 경우
- "단, ~은 제외" 같은 단서 조항 누락

### 4.2 요약 보조 지표

| 메트릭 | 용도 | 한국어 적용 시 주의 |
|--------|------|---------------------|
| **Semantic Similarity** | 요약-원문 의미 드리프트 감지 | 다국어 임베딩 모델 사용 |
| **ROUGE/CHRF** | 표면적 겹침 확인 | 보조 지표로만 사용, 형태소 전처리 권장 |

---

## 5. 한/영 이중 언어 평가 전략

### 5.1 한국어 평가의 핵심 문제

| 문제 | 원인 | 해결책 |
|------|------|--------|
| **N-gram 메트릭 왜곡** | 조사/어미 변화로 표면형 불일치 | 의미 기반 평가 중심 전환 |
| **BPE 토크나이징 불일치** | 형태소 경계와 다른 분절 | MeCab-ko 전처리 후 평가 |
| **LLM Judge 한국어 약점** | 사실 오류/경어법 탐지 미흡 | 루브릭 기반 + 전문가 보완 |

### 5.2 교차 언어(CLIR) 평가

한국어 질의 → 영어 약관 검색, 또는 그 반대의 경우를 **별도 테스트셋으로 분리 평가**합니다.

**CLIR 테스트셋 구성:**

```json
{
  "pair_id": "clir_001",
  "query_ko": "침수 피해 보상 범위가 어떻게 되나요?",
  "query_en": "What is the coverage scope for flood damage?",
  "expected_docs": ["policy_en_flood_coverage.pdf"],
  "expected_claims": [
    "침수 피해는 자연재해 특약 가입 시 보장",
    "자기부담금 20% 적용"
  ]
}
```

**CLIR 평가 기준:**
1. 동일 질문의 한/영 버전이 **같은 문서를 검색**하는가?
2. 최종 답변의 **Claim set이 의미적으로 동치**인가?

### 5.3 권장 도구

| 용도 | 도구 | 비고 |
|------|------|------|
| **한국어 형태소 분석** | MeCab-ko, KoNLPy | 토크나이징 전처리 |
| **한국어 NLI** | klue/roberta-large | Faithfulness 판정 |
| **다국어 임베딩** | multilingual-e5-large | 교차 언어 유사도 |
| **한국어 NER** | KLUE-NER | 엔티티 추출 |

---

## 6. Claim 단위 평가 로그 스키마

### 6.1 최상위 구조

```json
{
  "eval_id": "eval_20260107_001",
  "query_id": "q_123",
  "query_language": "ko",
  "query_text": "이 보험으로 임플란트 치료가 보장되나요?",
  "eval_timestamp": "2026-01-07T10:30:00Z",

  "retrieval": {
    "retrieved_docs": [
      {
        "doc_id": "policy_dental_v2024",
        "chunks": ["chunk_15", "chunk_16"],
        "version": "2024-01"
      }
    ],
    "metrics": {
      "context_recall": 0.92,
      "context_precision": 0.81,
      "context_entities_recall": 0.88
    }
  },

  "response": {
    "response_text": "치과 보존 치료는 보장되나, 임플란트는 보철 치료로 분류되어 보장되지 않습니다.",
    "claims": [
      {
        "claim_id": "c1",
        "claim_text": "치과 보존 치료는 보장된다",
        "evaluation": {
          "faithfulness": {"supported": true, "supporting_chunks": ["chunk_15"], "confidence": 0.97},
          "factual_correctness": {"label": "correct", "confidence": 0.95}
        },
        "citation": {"provided": true, "doc_id": "policy_dental_v2024", "location": "제3조 보장범위", "accurate": true},
        "risk_tags": ["coverage"]
      },
      {
        "claim_id": "c2",
        "claim_text": "임플란트는 보철 치료로 분류된다",
        "evaluation": {
          "faithfulness": {"supported": true, "supporting_chunks": ["chunk_16"], "confidence": 0.94},
          "factual_correctness": {"label": "correct", "confidence": 0.92}
        },
        "citation": {"provided": true, "doc_id": "policy_dental_v2024", "location": "제5조 면책사항", "accurate": true},
        "risk_tags": ["exclusion", "high_risk"]
      },
      {
        "claim_id": "c3",
        "claim_text": "임플란트는 보장되지 않는다",
        "evaluation": {
          "faithfulness": {"supported": true, "supporting_chunks": ["chunk_16"], "confidence": 0.96},
          "factual_correctness": {"label": "correct", "confidence": 0.94}
        },
        "citation": {"provided": true, "doc_id": "policy_dental_v2024", "location": "제5조 면책사항", "accurate": true},
        "risk_tags": ["exclusion", "high_risk"]
      }
    ]
  },

  "aggregate_scores": {
    "faithfulness": 0.96,
    "factual_correctness": 0.94,
    "citation_coverage": 1.0,
    "citation_accuracy": 1.0,
    "response_relevancy": 0.89
  },

  "flag": {
    "level": "PASSED",
    "reasons": []
  }
}
```

### 6.2 실패 케이스 예시 (환각 탐지)

```json
{
  "claim_id": "c4",
  "claim_text": "임플란트도 50% 부분 보장이 가능할 수 있습니다",
  "evaluation": {
    "faithfulness": {
      "supported": false,
      "supporting_chunks": [],
      "confidence": 0.12,
      "failure_reason": "NO_SUPPORTING_CONTEXT"
    },
    "factual_correctness": {"label": "incorrect", "confidence": 0.88}
  },
  "citation": {"provided": false},
  "risk_tags": ["hallucination", "coverage", "critical"]
}
```

이 경우 전체 응답이 🔴 CRITICAL로 플래깅됩니다.

---

## 7. 대시보드 지표 정의

### 7.1 Executive View (의사결정용)

| 지표 | 계산 방식 | 목표 (개발 초기) |
|------|-----------|-----------------|
| **P0 통과율** | PASSED / 전체 건수 | ≥70% |
| **환각 발생률** | 환각 Claim 포함 건 / 전체 | ≤5% |
| **Citation 누락률** | Citation 없는 Claim / 전체 Claim | ≤10% |
| **리뷰 완료율** | 리뷰 완료 / 리뷰 대상 | ≥90% |

### 7.2 Model Debug View (엔지니어용)

| 지표 | 용도 |
|------|------|
| **Claim-level 실패 패턴 Top 5** | 검색 누락 / 환각 / 인용 오류 등 분류 |
| **Retrieval vs Generation 실패 비율** | 파이프라인 병목 진단 |
| **Noise Sensitivity 추이** | 검색 품질 vs 생성 강건성 분리 |
| **문서 버전별 실패율** | 구버전 문서 인용 문제 탐지 |

### 7.3 Compliance View (감사용)

| 지표 | 용도 |
|------|------|
| **근거 인용 없는 Claim 비율** | 감사 대응 가능성 |
| **고위험 Claim 실패율** | 면책/금액/지급조건 관련 |
| **리뷰 불일치율** | 자동 평가 vs 전문가 판단 괴리 |

---

## 8. 제공된 보고서 비판적 검토

### 8.1 채택 (강하게 동의)

| 항목 | 출처 | 채택 이유 |
|------|------|-----------|
| **Context Recall 최상위** | 보고서 1 | 면책/예외 누락은 복구 불가능한 실패 |
| **Faithfulness-first** | 양쪽 | 보험에서 "그럴듯한 거짓"이 가장 위험 |
| **Claim-level 평가** | 양쪽 | 디버깅/감사/규제 대응에 필수 |
| **Citation 별도 KPI** | 보고서 1 | 규제/민원 대응의 실전 요구 |
| **3단계 임계값 로드맵** | 보고서 2 | 점진적 고도화에 현실적 |
| **P0 4종 동시 게이트** | 보고서 1 | 단일 점수로는 위험 답변 차단 불가 |

### 8.2 수정 (부분 채택)

| 항목 | 원래 제안 | 수정 내용 | 수정 이유 |
|------|-----------|-----------|-----------|
| **HITL 설계** | 운영 중 기준만 제시 | 개발/운영 분리, 플래그 기반 배치 리뷰 추가 | 현재 개발 단계에 맞지 않음 |
| **Deflection Rate** | 운영 지표로 제시 | 개발 중에는 "리뷰 비율"로 대체 | 상담원 연결이 없는 개발 단계 |
| **샘플링 비율 10-15%** | 고정 비율 | 플래그 레벨별 차등 (CRITICAL 100%, PASSED 15-20%) | 위험 건 전량 리뷰 필요 |

### 8.3 보류 (검증 필요)

| 항목 | 보류 이유 | 검증 방법 |
|------|-----------|-----------|
| **특정 프레임워크 상관관계 수치** | 원문 근거 미제공, 환경별 차이 가능 | 자체 벤치마크에서 재확인 |
| **Perplexity/Confidence 기반 트리거** | LLM 로그프롭 접근성, 모델별 일관성 이슈 | 사용 모델에서 실현 가능성 테스트 |
| **구체적 임계값 (0.85, 0.90 등)** | 도메인/데이터에 따라 조정 필요 | 초기 평가 결과로 캘리브레이션 |

### 8.4 기각 (채택하지 않음)

| 항목 | 기각 이유 |
|------|-----------|
| **MultiLingualRank (MLR)** | 비표준 메트릭, Semantic Similarity로 대체 가능 |
| **ROUGE/BLEU를 한국어 주요 지표로** | 형태소 특성으로 왜곡 심함, 보조 지표로만 유지 |

---

## 9. 실행 로드맵

### 9.1 Phase 1: 기반 구축 (현재 ~ 2주)

- [ ] P0 메트릭 4종 파이프라인 구현
- [ ] Claim 분해 로직 구현 (LLM 기반)
- [ ] 플래그 자동 부착 시스템 구축
- [ ] 리뷰 큐 인터페이스 구축 (간단한 스프레드시트 또는 Streamlit)

### 9.2 Phase 2: 평가 실행 (2주 ~ 4주)

- [ ] 테스트셋 200-300개 Q&A 구축
- [ ] CLIR 테스트셋 50-100개 구축
- [ ] 첫 배치 평가 실행
- [ ] 전문가 리뷰 1차 사이클 완료
- [ ] 임계값 캘리브레이션

### 9.3 Phase 3: 개선 루프 (4주 ~)

- [ ] 리뷰 결과 기반 파이프라인 개선
- [ ] Golden Dataset 확장
- [ ] P0 통과율 70% 이상 달성
- [ ] 운영 전환 준비

---

## 10. 결론

### 핵심 원칙 요약

1. **P0 게이트는 4종 동시:** Context Recall + Faithfulness + Factual Correctness + Citation Coverage
2. **Claim 단위로 분해:** Response-level이 아닌 claim-level로 평가해야 디버깅·감사 가능
3. **개발 중에는 플래그 기반 배치 리뷰:** 실시간 상담 전환이 아닌, 저장 후 전문가 검토
4. **한국어는 의미 기반 평가:** N-gram 메트릭은 보조로만 사용
5. **리뷰 결과를 GT로 환류:** 선순환 구조(Data Flywheel) 구축

### 개발 단계에서의 성공 기준

| 지표 | 목표 |
|------|------|
| P0 통과율 | ≥70% |
| 환각 발생률 | ≤5% |
| 리뷰 완료율 | ≥90% |
| 자동-전문가 평가 일치율 | ≥80% |

이 프레임워크는 보험 RAG 시스템이 **"점수 높이기"가 아니라 "위험 답변 차단"**에 집중하도록 설계되었습니다. Claim 단위 로그 없이는 디버깅·감사·규제 대응이 불가능하며, 개발 단계에서부터 체계적인 플래그 기반 리뷰 프로세스를 구축해야 운영 단계로의 안전한 전환이 가능합니다.
