# RAG 평가 메트릭 추가 권장사항 (2026년 기준)

> **Last Updated**: 2026-01-10
> **Based on**: 전문가 합의 문서 및 최신 연구 동향

## 개요

이 문서는 EvalVault에 추가하면 좋을 메트릭들을 전문가 합의 문서와 최신 연구를 바탕으로 정리한 것입니다. 현재 EvalVault가 지원하는 메트릭과 비교하여 우선순위를 제시합니다.

---

## 현재 EvalVault 지원 현황

### ✅ 이미 지원하는 메트릭

#### 핵심 RAGAS 메트릭
- ✅ **Faithfulness** (충실도)
- ✅ **Answer Relevancy** (답변 관련성)
- ✅ **Context Precision** (컨텍스트 정밀도)
- ✅ **Context Recall** (컨텍스트 재현율)
- ✅ **Factual Correctness** (답변 정확성)
- ✅ **Semantic Similarity** (의미적 유사도)
- ✅ **Summary Score** (요약 품질)
- ✅ **Summary Faithfulness** (요약 충실도)

#### 커스텀 메트릭
- ✅ **Entity Preservation** (엔티티 보존)
- ✅ **Insurance Term Accuracy** (도메인 용어 정확도)

#### Stage-level 메트릭
- ✅ **Retrieval**: `precision_at_k`, `recall_at_k`, `result_count`, `avg_score`, `score_gap`, `latency_ms`
- ✅ **Rerank**: `keep_rate`, `avg_score`, `score_gap`, `latency_ms`
- ✅ **Output**: `citation_count`, `token_ratio`, `latency_ms`
- ✅ **Input**: `query_length`

#### 운영 메트릭
- ✅ **Token Usage Tracking** (토큰 사용량 추적)
- ✅ **Cost Calculation** (비용 계산)
- ✅ **Error Rate** (에러율 추적)

---

## 추가 권장 메트릭 (우선순위별)

### 🔴 높은 우선순위 (즉시 구현 권장)

#### 1. **Contextual Relevancy (문맥 관련성)**
- **정의**: 검색된 컨텍스트가 질문과 얼마나 관련이 있는지를 평가
- **중요성**: RAG 트라이어드의 세 번째 축으로 TruLens, Microsoft Azure AI에서 강조
- **계산 방식**: 검색된 문서들이 질문과의 관련성을 LLM 또는 임베딩으로 평가
- **임계값**: >0.7 (프로덕션 목표)
- **구현 난이도**: ⭐⭐ (RAGAS에 유사 메트릭 존재 가능성)
- **참고**: RAGAS 0.4.x에 `contextual_relevancy` 메트릭이 있을 수 있음

#### 2. **Claim-level Faithfulness (주장 수준 충실도)**
- **정의**: 응답 전체가 아닌 개별 주장(Claim) 단위로 근거성을 검사
- **중요성**:
  - NeurIPS 2024 RAGChecker 연구에서 인간 판단과 **더 높은 상관관계** 달성
  - 메트릭 붕괴(Metric Collapse) 문제 해결
  - 응답 수준 평가보다 **59% 더 정확한 컨텍스트 관련성 평가** (Stanford ARES)
- **계산 방식**:
  1. 응답에서 주장(Claim) 추출
  2. 각 주장이 컨텍스트에 의해 함의(Entailment)되는지 검사
  3. 지원되는 주장 수 / 전체 주장 수
- **임계값**: >0.85 (기존 faithfulness와 동일)
- **구현 난이도**: ⭐⭐⭐ (주장 추출 + 함의 검사 로직 필요)

#### 3. **하이브리드 검색 가중치 최적화 메트릭**
- **정의**: Dense + BM25 하이브리드 검색에서 최적 가중치 비율 평가
- **중요성**:
  - Anthropic 권장: **4:1 비율** (Dense:BM25)
  - 상위 20개 청크 검색 실패율 **67% 감소** (5.7% → 1.9%)
- **계산 방식**:
  - 다양한 가중치 조합(예: 1:1, 2:1, 4:1, 8:1) 테스트
  - 각 조합의 `context_recall`, `context_precision` 비교
  - 최적 가중치 비율 도출
- **임계값**: N/A (비교 메트릭)
- **구현 난이도**: ⭐⭐ (현재 하이브리드 검색 지원, 가중치 튜닝 로직 추가)
- **참고**: `src/evalvault/adapters/outbound/nlp/korean/hybrid_retriever.py` 이미 존재

#### 4. **Hit Rate@K, MRR, NDCG (명시적 검색 메트릭)**
- **정의**:
  - **Hit Rate@K**: 상위 K개 결과 중 정답 문서 포함 비율
  - **MRR (Mean Reciprocal Rank)**: 정답의 역순위 평균
  - **NDCG (Normalized Discounted Cumulative Gain)**: 순위 품질 평가
- **중요성**:
  - OpenAI Cookbook, 벡터 DB 업계 표준 메트릭
  - 검색 단계 품질을 정량적으로 측정
- **현재 상태**: Stage Metric으로 `precision_at_k`, `recall_at_k`는 있지만 명시적 Hit Rate@K, MRR, NDCG는 없음
- **계산 방식**: Ground truth 문서 ID와 검색 결과 비교
- **임계값**:
  - Hit Rate@10: >0.8
  - MRR: >0.6
  - NDCG@10: >0.7
- **구현 난이도**: ⭐ (Stage Metric 확장 또는 별도 메트릭)

### 🟡 중간 우선순위 (단기 구현 권장)

#### 5. **Information Integration Capability (정보 통합 능력)**
- **정의**: 여러 출처에서 검색된 정보를 효과적으로 통합하여 일관된 응답 생성 능력
- **중요성**: 복잡한 질문에 대한 응답 품질 향상
- **계산 방식**:
  - 여러 문서에서 추출된 정보 간 일관성 검사
  - 정보 충돌 감지 및 해결 능력 평가
- **임계값**: >0.7
- **구현 난이도**: ⭐⭐⭐ (복잡한 로직 필요)

#### 6. **Robustness to Noise (잡음 강건성)**
- **정의**: 입력 데이터의 변동이나 잡음에 대해 시스템이 안정적으로 작동하는지 평가
- **중요성**: 프로덕션 환경의 다양한 입력에 대한 신뢰성
- **계산 방식**:
  - 원본 질문에 약간의 변형(오타, 동의어 교체 등) 추가
  - 변형 전후 메트릭 점수 비교
  - 점수 하락 폭이 작을수록 강건성 높음
- **임계값**: 점수 하락 <10%
- **구현 난이도**: ⭐⭐⭐ (데이터 증강 + 비교 로직)

#### 7. **Throughput (처리량)**
- **정의**: 단위 시간당 처리 가능한 요청 수
- **중요성**: 프로덕션 환경의 확장성 평가
- **계산 방식**: 초당 요청 수 (QPS) 또는 분당 요청 수
- **임계값**: 도메인별 상이 (일반적으로 >10 QPS)
- **구현 난이도**: ⭐⭐ (Stage Metric 확장)

### 🟢 낮은 우선순위 (장기 계획)

#### 8. **Drift Detection (드리프트 감지)**
- **정의**: 시간에 따른 메트릭 점수 변화 추적 및 이상 감지
- **중요성**: 지속적 모니터링의 핵심
- **계산 방식**:
  - 과거 실행과 현재 실행 간 메트릭 비교
  - 통계적 유의미한 변화 감지 (예: Z-score 기반)
- **임계값**: 변화율 >10% 시 경고
- **구현 난이도**: ⭐⭐⭐⭐ (시계열 분석 + 통계 모델)

#### 9. **Cost Efficiency (비용 효율성)**
- **정의**: 메트릭 점수 대비 비용 효율 평가
- **중요성**: 비용 최적화 전략 수립
- **계산 방식**:
  - 점수 / 비용 비율
  - 또는 목표 점수 달성 시 최소 비용 계산
- **임계값**: 도메인별 상이
- **구현 난이도**: ⭐ (이미 Cost tracking 있음, 비율 계산만 추가)

#### 10. **Multi-modal Faithfulness (멀티모달 충실도)**
- **정의**: 이미지, 표 등 멀티모달 컨텍스트에 대한 충실도 평가
- **중요성**: 멀티모달 RAG 시스템 평가
- **계산 방식**: 텍스트 기반 faithfulness 확장
- **임계값**: >0.85
- **구현 난이도**: ⭐⭐⭐⭐ (멀티모달 처리 필요)

---

## 구현 로드맵 제안

### Phase 1: 즉시 구현 (1-2주)
1. **Contextual Relevancy** - RAGAS 확인 후 추가
2. **Hit Rate@K, MRR, NDCG** - Stage Metric 확장

### Phase 2: 단기 구현 (1-2개월)
3. **Claim-level Faithfulness** - 핵심 개선 메트릭
4. **하이브리드 검색 가중치 최적화** - 실용적 가치 높음

### Phase 3: 중기 구현 (3-6개월)
5. **Information Integration Capability**
6. **Robustness to Noise**
7. **Throughput**

### Phase 4: 장기 계획 (6개월+)
8. **Drift Detection**
9. **Cost Efficiency** (비율 계산)
10. **Multi-modal Faithfulness**

---

## 참고 자료

### 학술 연구
- **RAGChecker (NeurIPS 2024)**: Claim-level entailment 검사
- **Stanford ARES**: 단계별 평가의 정확도 향상
- **Meta CRAG**: 최첨단 시스템도 63% 환각 없음 비율

### 업계 표준
- **Anthropic Contextual Retrieval**: 4:1 하이브리드 검색 가중치
- **Microsoft Azure AI Foundry**: RAG 트라이어드 (검색 품질, 근거성, 관련성)
- **OpenAI Cookbook**: Hit Rate, MRR 권장

### 프레임워크
- **RAGAS**: 20개 이상 메트릭, 참조 불필요 평가
- **DeepEval**: 50개 이상 메트릭, CI/CD 통합
- **TruLens**: RAG 트라이어드 집중

---

## 결론

EvalVault는 이미 핵심 RAG 평가 메트릭을 잘 지원하고 있습니다. 추가로 구현하면 좋을 메트릭들은:

1. **즉시**: Contextual Relevancy, 명시적 검색 메트릭 (Hit Rate@K, MRR, NDCG)
2. **단기**: Claim-level Faithfulness (가장 큰 정확도 향상), 하이브리드 검색 최적화
3. **중기**: 정보 통합 능력, 잡음 강건성, 처리량

이러한 메트릭들을 추가하면 EvalVault가 2026년 최신 RAG 평가 표준을 완전히 지원하는 플랫폼이 될 것입니다.
