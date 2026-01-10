# RAG 평가 시스템 요구사항 및 메트릭 권장사항

> **Last Updated**: 2026-01-10 (P0 Claim-level Faithfulness, Exact Match / F1 Score 구현 완료)
> **Based on**: 폐쇄망 RAG 시스템 평가 보고서 + 전문가 합의 문서 + 최신 연구 동향

## 개요

이 문서는 EvalVault의 RAG 평가 기능 확장을 위한 통합 요구사항을 정리합니다. 폐쇄망 환경 특수 요구사항과 최신 연구 기반 메트릭 권장사항을 결합하여 구현 우선순위를 제시합니다.

### 우선순위 요약

```
┌─────────────────────────────────────────────────────────────┐
│  P0 (핵심)                                                  │
│  ├─ ✅ Claim-level Faithfulness ← 구현 완료 (2026-01-10)     │
│  ├─ ✅ Exact Match / F1 Score   ← 구현 완료 (2026-01-10)     │
│  └─ "정답 없음" 평가          ← 환각 방지                    │
│                                                             │
│  P1 (중요)                                                  │
│  ├─ Synthetic Q&A 생성        ← Ground Truth 확보            │
│  ├─ MRR, NDCG                 ← 검색 순위 품질               │
│  ├─ Confidence Score          ← Human-in-the-Loop            │
│  └─ Contextual Relevancy      ← 중복 확인 후 결정            │
│                                                             │
│  P2 (개선)                                                  │
│  ├─ BERTScore                 ← BLEU/ROUGE 대신 이것만       │
│  ├─ 하이브리드 검색 벤치마크  ← 가중치 최적화                 │
│  ├─ Throughput                ← 운영 메트릭                  │
│  └─ Human 평가 연계           ← Escalation Rate 등           │
│                                                             │
│  ❌ 추가하지 않음: BLEU, ROUGE (중복, 한국어 제한적)          │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. 현재 EvalVault 지원 현황

### 1.1 폐쇄망 환경 지원

| 기능 | 상태 | 설명 |
|------|------|------|
| Ollama 통합 | ✅ | `ollama_base_url`, `ollama_model` 지원 |
| vLLM 통합 | ✅ | OpenAI-compatible 서버 지원 |
| 로컬 임베딩 | ✅ | `qwen3-embedding:0.6b` 등 지원 |
| 프로필 시스템 | ✅ | `config/models.yaml` 다중 환경 관리 |

### 1.2 핵심 RAGAS 메트릭

| 메트릭 | 상태 | 설명 |
|--------|------|------|
| Faithfulness | ✅ | 답변이 컨텍스트에 충실한지 (Reference-free) |
| Answer Relevancy | ✅ | 답변이 질문과 관련있는지 |
| Context Precision | ✅ | 검색된 컨텍스트의 정밀도 |
| Context Recall | ✅ | 필요한 정보가 검색되었는지 |
| Factual Correctness | ✅ | Ground truth 대비 사실적 정확성 |
| Semantic Similarity | ✅ | 답변과 ground_truth 간 의미적 유사도 |
| Summary Score | ✅ | 요약 품질 평가 |
| Summary Faithfulness | ✅ | 요약 충실도 평가 |

### 1.3 커스텀 메트릭

| 메트릭 | 상태 | 설명 |
|--------|------|------|
| Entity Preservation | ✅ | 엔티티 보존율 |
| Insurance Term Accuracy | ✅ | 도메인 용어 정확도 |
| Exact Match | ✅ | 완전 일치율 (number_strict 지원) |
| F1 Score | ✅ | 부분 일치 평가 (number_weight 지원) |

### 1.4 Stage-level 메트릭

| 단계 | 메트릭 |
|------|--------|
| **Retrieval** | `precision_at_k`, `recall_at_k`, `result_count`, `avg_score`, `score_gap`, `latency_ms` |
| **Rerank** | `keep_rate`, `avg_score`, `score_gap`, `latency_ms` |
| **Output** | `citation_count`, `token_ratio`, `latency_ms` |
| **Input** | `query_length` |

### 1.5 운영 메트릭

- ✅ Token Usage Tracking
- ✅ Cost Calculation
- ✅ Error Rate

---

## 2. 추가 필요 메트릭 (우선순위별)

> **Note**: 우선순위는 EvalVault의 보험 도메인 특성과 폐쇄망 환경을 고려하여 재정렬됨

### 2.1 🔴 핵심 우선순위 (P0 - 즉시 구현)

#### ✅ Claim-level Faithfulness (주장 수준 충실도) - 구현 완료

> **구현 완료**: 2026-01-10 | PR #108

- **정의**: 개별 주장(Claim) 단위로 근거성 검사
- **중요성**:
  - NeurIPS 2024 RAGChecker 연구에서 인간 판단과 **더 높은 상관관계** 달성
  - 메트릭 붕괴(Metric Collapse) 문제 해결
  - 응답 수준 평가보다 **59% 더 정확한 컨텍스트 관련성 평가** (Stanford ARES)
  - **환각 탐지의 핵심** - 현재 Faithfulness는 응답 전체 평가로 세밀도 부족
- **계산 방식**:
  1. 응답에서 주장(Claim) 추출 (한국어 NLP 형태소 분석)
  2. 각 주장이 컨텍스트에 의해 함의(Entailment)되는지 검사
  3. 지원되는 주장 수 / 전체 주장 수
- **임계값**: >0.85
- **사용법**:
  ```bash
  uv run evalvault run data.json --metrics faithfulness --claim-level -v
  ```
- **출력 예시**:
  ```
  tc-001: FAIL
    - faithfulness: 0.750 (threshold: 0.8)
      Claims: 4 total, 3 supported, 1 not supported
        ✗ 보장기간 20년
          숫자 불일치 발견
  ```

#### ✅ 생성 단계 정확도 메트릭 - 구현 완료

> **구현 완료**: 2026-01-10 | PR #109

| 메트릭 | 정의 | 중요성 | 상태 |
|--------|------|--------|------|
| **Exact Match (EM)** | 완전 일치율 | 보험 도메인에서 보장금액, 보험료 등 정확한 숫자 일치 필수 | ✅ |
| **F1 Score** | 부분 일치 평가 | 부분 정답 인정 | ✅ |

**구현 특징**:
- 한국어 particle 제거 (은/는, 이/가, 을/를, 입니다, etc.)
- number_strict 모드: 숫자만 일치해도 1.0 점수
- F1에서 숫자 토큰 가중치 조절 가능 (`number_weight`)
- Reference-based (ground_truth 필요)

**사용법**:
```bash
uv run evalvault run data.json --metrics exact_match,f1_score
```

**참고**: Ground truth가 있는 경우 정량적 평가에 필수. 보험 도메인 특성상 EM이 특히 중요

#### "정답 없음" 상황 평가

- **정의**: 답이 문서에 없을 때 "정보 없음"으로 올바르게 응답하는지 평가
- **중요성**:
  - **환각 방지의 핵심** - 보험에서 잘못된 정보 제공은 실제 피해로 이어질 수 있음
  - 지식 공백 상황 대응 능력 평가
- **평가 방식**:
  - 의도적으로 정답 없는 질문을 평가 세트에 포함
  - "답변 불가" 또는 "정보 없음" 응답 비율 측정
- **구현 난이도**: ⭐⭐ (평가 데이터셋 구성 + 메트릭 추가)

---

### 2.2 🟠 높은 우선순위 (P1 - 단기 구현)

#### 검색 단계 명시적 메트릭

| 메트릭 | 정의 | 근거 | 구현 난이도 |
|--------|------|------|------------|
| **Hit Rate@K** | 상위 K개 결과 중 정답 문서 포함 비율 | OpenAI Cookbook, 벡터 DB 업계 표준 | ⭐ |
| **MRR** | 첫 번째 관련 문서의 역순위 평균 | 정답 문서의 순위 민감도 평가 | ⭐ |
| **NDCG@K** | 관련성 등급을 고려한 순위 품질 | 다수 문서 제시 시 전반적 랭킹 평가 | ⭐⭐ |
| **F1@K** | Precision@K와 Recall@K의 조화평균 | 정밀도-재현율 균형 평가 | ⭐ |

**구현 방식**: Stage Metric 확장 또는 별도 메트릭
**임계값**: Hit Rate@10 >0.8, MRR >0.6, NDCG@10 >0.7
**참고**: 이미 `precision_at_k`, `recall_at_k` 있으므로 급하지 않음

#### Synthetic Q&A 데이터셋 생성

- **정의**: 내부 문서로부터 질문-답변 쌍을 자동 생성
- **중요성**:
  - 폐쇄망 환경의 Ground Truth 부족 문제 해결
  - 평가용 레이블 데이터 확보
  - 초기 성능 측정 가능
- **구현 방식**:
  1. 문서에서 잠재 질문 생성 (LLM 활용)
  2. 해당 문서 내용으로 답변 추출
  3. 품질 검수 및 필터링
- **구현 난이도**: ⭐⭐⭐

**참고**: 현재 `evalvault generate` 명령 존재, Synthetic Q&A 특화 기능 추가 필요

#### Confidence Score (모델 신뢰도 점수)

- **정의**: 모델이 각 답변에 대해 추정하는 자신감 수준 (0~1)
- **중요성**:
  - 폐쇄망 Human-in-the-Loop의 핵심 지표
  - 낮은 신뢰도 답변을 사람 검토 대상으로 선별
  - Escalation Rate와 연계하여 운영 정책 수립
- **계산 방식**:
  - Retrieval 스코어 기반
  - 모델 로짓 기반
  - Faithfulness 점수 기반
  - Calibration: 신뢰도와 실제 정답률 일치도 보정
- **구현 난이도**: ⭐⭐⭐
- **주의**: 개념은 좋지만 구현 복잡. 투자 대비 효과 검토 필요

#### Contextual Relevancy (문맥 관련성) - 확인 필요

- **정의**: 검색된 컨텍스트가 질문과 얼마나 관련이 있는지 평가
- **중요성**: RAG 트라이어드의 세 번째 축 (TruLens, Microsoft Azure AI 강조)
- **계산 방식**: LLM 또는 임베딩으로 질문-컨텍스트 관련성 평가
- **임계값**: >0.7
- **구현 난이도**: ⭐⭐
- **주의**: `Context Precision`과 중복 가능성 있음. RAGAS 확인 후 추가 여부 결정

---

### 2.3 🟡 중간 우선순위 (P2 - 중기 구현)

#### BERTScore (의미 유사도)

- **정의**: 임베딩 기반 의미 유사도
- **중요성**: 표현 다르지만 의미 같으면 높은 점수
- **구현 난이도**: ⭐⭐⭐
- **참고**: 현재 `semantic_similarity` 있지만 BERTScore가 더 정교한 평가 제공. BLEU/ROUGE는 n-gram 기반으로 한국어에서 제한적이므로 **BERTScore만 추가 권장**

#### 하이브리드 검색 벤치마크

- **정의**: Dense + BM25 하이브리드 검색에서 최적 가중치 비율 평가
- **중요성**:
  - Anthropic 권장: **4:1 비율** (Dense:BM25)
  - 상위 20개 청크 검색 실패율 **67% 감소** (5.7% → 1.9%)
- **계산 방식**:
  - 다양한 가중치 조합(1:1, 2:1, 4:1, 8:1) 테스트
  - 각 조합의 `context_recall`, `context_precision` 비교
  - 최적 가중치 비율 도출
- **구현 난이도**: ⭐⭐
- **참고**: `src/evalvault/adapters/outbound/nlp/korean/hybrid_retriever.py` 이미 존재. 벤치마크 기능만 추가

#### 운영 메트릭 확장

| 메트릭 | 정의 | 중요성 | 구현 난이도 |
|--------|------|--------|------------|
| **Throughput** | 초당 처리 쿼리 수 (QPS) | 확장성 평가 | ⭐⭐ |
| **First Token Latency** | 첫 번째 토큰 출력 시간 | 스트리밍 초기 반응성 | ⭐⭐ |

#### Human 평가 연계 메트릭

| 메트릭 | 정의 | 중요성 | 구현 난이도 |
|--------|------|--------|------------|
| **Disagreement Rate** | 평가자 간 판정 불일치 비율 | 평가 기준 모호함 감지 | ⭐⭐⭐ |
| **Escalation Rate** | 사람 전문가에게 넘긴 케이스 비중 | Human-in-the-Loop 효율성 | ⭐⭐⭐ |

#### Information Integration Capability (정보 통합 능력)

- **정의**: 여러 출처의 정보를 통합하여 일관된 응답 생성 능력
- **계산 방식**: 다중 문서 정보 간 일관성 검사, 충돌 감지/해결 능력 평가
- **임계값**: >0.7
- **구현 난이도**: ⭐⭐⭐

#### Robustness to Noise (잡음 강건성)

- **정의**: 입력 데이터의 변동/잡음에 대한 안정성
- **계산 방식**: 원본에 변형(오타, 동의어) 추가 후 점수 비교
- **임계값**: 점수 하락 <10%
- **구현 난이도**: ⭐⭐⭐

---

### 2.4 🟢 낮은 우선순위 (P3 - 장기 계획)

| 메트릭 | 정의 | 구현 난이도 |
|--------|------|------------|
| **Drift Detection** | 시간에 따른 메트릭 변화 추적 및 이상 감지 | ⭐⭐⭐⭐ |
| **Cost Efficiency** | 메트릭 점수 대비 비용 효율 | ⭐ |
| **Multi-modal Faithfulness** | 이미지/표 등 멀티모달 충실도 | ⭐⭐⭐⭐ |
| **LLM-as-a-Judge (G-Eval)** | 강력한 LLM을 채점자로 활용 (폐쇄망: 온프레미스 버전) | ⭐⭐⭐ |
| **Coverage** | 검색된 문서가 질문의 모든 쟁점 포함 | ⭐⭐⭐⭐ |
| **Completeness** | 답변이 모든 부분을 빠짐없이 다룸 | ⭐⭐⭐⭐ |

### 2.5 ❌ 추가하지 않음 (중복/불필요)

| 메트릭 | 사유 |
|--------|------|
| **BLEU** | n-gram 기반으로 한국어에서 제한적. `semantic_similarity` + BERTScore로 충분 |
| **ROUGE-L** | 위와 동일. BERTScore가 더 효과적 |

---

## 3. 폐쇄망 환경 특수 고려사항

### 3.1 데이터 접근성과 프라이버시

| 항목 | 현재 상태 | 추가 필요 |
|------|----------|----------|
| 온프레미스 LLM | ✅ Ollama, vLLM | - |
| 로컬 임베딩 | ✅ 지원 | - |
| 민감 정보 마스킹 | ❌ | 평가 시 자동 마스킹 |
| 감사 로그 | ❌ | 데이터 유출 방지 로깅 |

### 3.2 평가용 Ground Truth 부족

| 항목 | 현재 상태 | 추가 필요 |
|------|----------|----------|
| Reference-free 평가 | ✅ Faithfulness, Answer Relevancy | - |
| 과거 평가 활용 | ✅ Domain Memory | - |
| Synthetic Q&A | ❌ | 자동 생성 기능 |
| 골드셋 구축 가이드 | ❌ | 문서화 필요 |

### 3.3 모델/시스템 제약

| 항목 | 현재 상태 | 추가 필요 |
|------|----------|----------|
| 다중 모델 프로필 | ✅ `config/models.yaml` | - |
| Latency 추적 | ✅ Stage Metric | - |
| 성능 한계 가이드 | ❌ | 모델별 목표치 조정 가이드 |
| 리소스 최적화 | ❌ | 하드웨어 제약 고려 가이드 |

---

## 4. 구현 로드맵

### Phase 1: 즉시 구현 (1-2주) - 핵심

| 항목 | 우선순위 | 상태 | 설명 |
|------|---------|------|------|
| **Claim-level Faithfulness** | P0 | ✅ 완료 | 환각 탐지 핵심. `--claim-level` 옵션으로 사용 |
| **Exact Match, F1 Score** | P0 | ✅ 완료 | 보험 도메인 정확도 (보장금액, 보험료 등) |
| "정답 없음" 평가 | P0 | 🔲 예정 | 환각 방지. 잘못된 정보 제공 차단 |

### Phase 2: 단기 구현 (1-2개월) - 중요

| 항목 | 우선순위 | 설명 |
|------|---------|------|
| Synthetic Q&A 생성 | P1 | Ground Truth 부족 해결 |
| Hit Rate@K, MRR, NDCG | P1 | 검색 순위 품질 (이미 precision/recall 있어 급하지 않음) |
| Confidence Score | P1 | Human-in-the-Loop 연계 (구현 복잡도 고려) |
| Contextual Relevancy | P1 | Context Precision과 중복 확인 후 결정 |

### Phase 3: 중기 구현 (3-6개월) - 개선

| 항목 | 우선순위 | 설명 |
|------|---------|------|
| BERTScore | P2 | 의미 유사도 정교화 (BLEU/ROUGE 대신) |
| 하이브리드 검색 벤치마크 | P2 | 가중치 최적화 도구 |
| Throughput, First Token Latency | P2 | 운영 메트릭 |
| Disagreement Rate, Escalation Rate | P2 | Human 평가 연계 |
| Information Integration | P2 | 복잡한 질문 대응 |
| Robustness to Noise | P2 | 프로덕션 신뢰성 |

### Phase 4: 장기 계획 (6개월+) - 확장

| 항목 | 우선순위 | 설명 |
|------|---------|------|
| Drift Detection | P3 | 시계열 모니터링 |
| Multi-modal Faithfulness | P3 | 멀티모달 RAG 지원 |
| LLM-as-a-Judge (온프레미스) | P3 | 고급 자동 평가 |
| 도메인 특화 기준 확장 | P3 | Coverage, Completeness 등 |

---

## 5. 운영 권장사항

### 5.1 평가 전략

```
┌─────────────────────────────────────────────────────────────┐
│                    평가 전략 우선순위                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Reference-free 평가 우선                                  │
│    - Faithfulness, Answer Relevancy로 넓은 범위 커버          │
│                                                             │
│ 2. 소규모 골드셋 구축                                         │
│    - 중요 질문에 대해서만 레퍼런스 작성                         │
│                                                             │
│ 3. Synthetic Q&A 활용                                       │
│    - 초기 성능 측정 및 지속적 개선                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 모니터링 체계

| 항목 | 권장 사항 |
|------|----------|
| 자동 선별 | Confidence Score < 0.7 → 사람 검토 |
| 정기 검증 | 주간/월간 샘플 인간 평가 |
| 추이 추적 | 지식베이스 업데이트 후 성능 모니터링 |

### 5.3 운영 임계값

| 메트릭 | 임계값 | 조치 |
|--------|--------|------|
| Confidence Score | < 0.7 | Human 검토 |
| Faithfulness | < 0.85 | Human fallback |
| Latency P95 | < 3초 | 엔터프라이즈 |
| Latency P95 | < 1초 | 실시간 상담 |

---

## 6. 참고 자료

### 학술 연구

| 연구 | 핵심 내용 |
|------|----------|
| **RAGChecker (NeurIPS 2024)** | Claim-level entailment 검사로 인간 판단과 높은 상관관계 |
| **Stanford ARES** | 단계별 평가로 59% 정확도 향상 |
| **Meta CRAG** | 최첨단 시스템도 63% 환각 없음 비율 |

### 업계 표준

| 출처 | 권장 사항 |
|------|----------|
| **Anthropic Contextual Retrieval** | 4:1 하이브리드 검색 가중치 (Dense:BM25) |
| **Microsoft Azure AI Foundry** | RAG 트라이어드 (검색 품질, 근거성, 관련성) |
| **OpenAI Cookbook** | Hit Rate, MRR 권장 |

### 프레임워크

| 프레임워크 | 특징 |
|-----------|------|
| **RAGAS** | 20개 이상 메트릭, Reference-free 평가 |
| **DeepEval** | 50개 이상 메트릭, CI/CD 통합 |
| **TruLens** | RAG 트라이어드 집중 |

---

## 7. 결론

EvalVault는 이미 폐쇄망 환경과 핵심 RAG 평가를 잘 지원합니다. 보험 도메인 특성과 폐쇄망 환경을 고려한 추가 구현 우선순위:

### 즉시 (P0) - 핵심
```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Claim-level Faithfulness ← 구현 완료 (--claim-level)     │
│  ✅ Exact Match / F1 Score   ← 구현 완료 (exact_match, f1)   │
│  🔲 "정답 없음" 평가         ← 환각 방지                     │
└─────────────────────────────────────────────────────────────┘
```

### 단기 (P1) - 중요
- Synthetic Q&A 생성 (Ground Truth 확보)
- MRR, NDCG (검색 순위 품질)
- Confidence Score (Human-in-the-Loop)
- Contextual Relevancy (중복 확인 후)

### 중기 (P2) - 개선
- BERTScore (BLEU/ROUGE 대신 이것만)
- 하이브리드 검색 벤치마크
- Throughput, First Token Latency
- Human 평가 연계 메트릭

### 추가하지 않음
- BLEU, ROUGE: `semantic_similarity` + BERTScore로 충분. n-gram 기반은 한국어에서 제한적

이러한 기능들을 추가하면 EvalVault가 2026년 최신 RAG 평가 표준을 완전히 지원하는 폐쇄망 친화적 플랫폼이 될 것입니다.
