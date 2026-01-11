# 10. 성능 최적화(Performance)

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: EvalVault를 대규모 데이터/고비용 모델로 운용할 때 고려해야 할 성능 축과, “측정→개선→회귀 방지” 루틴을 근거 기반으로 정리한다.
- **독자**: 고급 내부 개발자
- **선행 지식**: 프로파일링/병렬 처리 기본, 검색/임베딩 비용 구조

---

## TL;DR

- 성능은 “평가(LLM) + 검색/임베딩 + 분석 DAG + 저장/리포트 + 트레이싱”의 합이다.
- EvalVault는 StageEvent/StageMetric로 **단계별 레이턴시**와 기본 지표를 남긴다.
- p50/p95 같은 분포 지표는
  - (A) 전용 성능 스모크 스크립트(`scripts/perf/`) 또는
  - (B) 분석 어댑터(통계) 확장
  으로 보강한다.

---

## 1) 성능 축(체크리스트)

- LLM 평가: 메트릭 수 × 샘플 수 × 토큰(입력/출력)
- 검색 단계: 인덱스 구축 + top_k + 캐시
- 분석 파이프라인(DAG): 노드 수/의존성/병렬성
- 저장/리포트: 아티팩트 JSON 수 + 보고서 렌더링
- 트레이싱: span 수/attribute 크기/샘플링 비율

---

## 2) Stage 기반 측정(운영에서 먼저 보는 값)

### 2.1 StageEvent: 무엇을 기록하나

- StageEvent 생성: `src/evalvault/domain/services/stage_event_builder.py`
  - `StageEventBuilder.build_for_run(...)`
  - 주요 stage:
    - `input` (query)
    - `retrieval` (doc_ids/top_k/scores + perf attributes)
    - `output` (answer/citations/tokens_used + duration)

- 성능 속성(옵션, retrieval_metadata에 있을 때만 주입):
  - 공통: `retrieval_time_ms`
  - 인덱스/캐시/배치: `index_build_time_ms`, `cache_hit`, `batch_size`, `index_size`, `total_docs_searched`
  - FAISS/GPU: `faiss_gpu_active`
  - GraphRAG 계열: `graph_nodes`, `graph_edges`, `subgraph_size`

### 2.2 StageMetric: 무엇을 계산하나

- StageMetric 계산: `src/evalvault/domain/services/stage_metric_service.py`
  - `StageMetricService.build_metrics(...)`
  - `duration_ms`가 있으면 자동으로 `<stage_type>.latency_ms`를 만든다.
    - 예: `retrieval.latency_ms`, `output.latency_ms`
  - retrieval에 대해 추가로 계산 가능한 지표:
    - `retrieval.result_count`, `retrieval.avg_score`, `retrieval.score_gap`
    - (relevance_map이 있으면) `retrieval.precision_at_k`, `retrieval.recall_at_k`

- 기본 임계값(예시): `DEFAULT_STAGE_THRESHOLDS`
  - `retrieval.latency_ms=500`, `rerank.latency_ms=800`, `output.latency_ms=3000`

---

## 3) p50/p95 같은 분포 지표는 어디서 보나

### 3.1 전용 성능 스모크(권장: 빠른 반복)

- Dense retriever R3 스모크: `scripts/perf/r3_dense_smoke.py`
  - p50/p95/p99를 출력한다: `search_ms_p50`, `search_ms_p95`, `search_ms_p99`

```bash
python scripts/perf/r3_dense_smoke.py --documents 1000 --queries 200 --top-k 5 --mock-embeddings
```

### 3.2 통계 분석(리포트용)

- 기술통계 계산: `src/evalvault/adapters/outbound/analysis/statistical_adapter.py`
  - `StatisticalAnalysisAdapter._calculate_metric_stats(...)`는 `percentile_25`, `percentile_75`를 제공한다.

> **NOTE**: 현재 기술통계에는 p95가 기본 필드로 포함되어 있지 않다.
> p95를 리포트에 포함하려면 분석 어댑터/엔티티를 확장하는 작업이 필요하다.

---

## 4) 트레이싱/OTel의 성능 비용

- 자동 계측/샘플링: `src/evalvault/config/instrumentation.py`, `src/evalvault/config/settings.py`
  - `phoenix_sample_rate`로 trace volume을 조절할 수 있다.
- Open RAG Trace 속성 제한(스칼라/배열) 때문에, 큰 payload는 JSON 문자열로 직렬화된다.
  - 근거: `src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py`

실무 원칙:
- attribute에 “큰 본문”을 넣기보다, 로컬 아티팩트 저장 후 “경로/요약”만 span에 넣는 방향을 우선한다.

---

## 5) 성능 작업 시 권장 루틴

1) **측정 고정**
- p50/p95, 메모리 피크, 처리량(QPS)

2) **대상 분리**
- LLM/검색/분석/저장/트레이싱 중 어디가 병목인지 먼저 분해

3) **회귀 방지**
- 최소 1개 fixture로 스모크 실행
- StageMetric 임계값/알림이 의미 있게 유지되는지 확인

---

## Evidence

- StageEvent/StageMetric:
  - `src/evalvault/domain/services/stage_event_builder.py`
  - `src/evalvault/domain/services/stage_metric_service.py`
- 통계 기술통계:
  - `src/evalvault/adapters/outbound/analysis/statistical_adapter.py`
- 성능 스모크:
  - `scripts/perf/r3_dense_smoke.py`
- 트레이싱/샘플링:
  - `src/evalvault/config/settings.py`
  - `src/evalvault/config/instrumentation.py`
  - `src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py`

---

## 전문가 관점 체크리스트

- [ ] 성능 이야기가 추정이 아니라 측정/지표로 연결되는가
- [ ] 단계별(검색/생성/분석/트레이싱) 병목이 분리되어 설명되는가
- [ ] 운영(샘플링/attribute 크기 제한) 관점의 비용이 숨겨지지 않는가

---

## 향후 변경 시 업데이트 가이드

- StageEvent에 새 성능 속성 키를 추가했다면:
  - `src/evalvault/domain/services/stage_event_builder.py`의 퍼포먼스 키 목록과 함께
    이 장의 **2.1**에 해당 키를 추가한다.

- StageMetric 기본 임계값을 바꿨다면:
  - `src/evalvault/domain/services/stage_metric_service.py`의 `DEFAULT_STAGE_THRESHOLDS` 근거로
    이 장의 **2.2**를 갱신한다.

- p95 같은 새로운 통계 필드를 리포트에 추가했다면:
  - `src/evalvault/adapters/outbound/analysis/statistical_adapter.py`와 관련 엔티티 변경 근거를
    이 장의 **3.2**에 추가한다.
