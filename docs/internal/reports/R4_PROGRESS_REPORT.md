# R4 진행 보고서 (벤치마크 doc_id 스키마)

> 업데이트: 2026-01-04
> 범위: R4 하이브리드 서치 벤치마크 - doc_id 스키마/메트릭/매핑

---

## 1. 현재 상태 요약

- ground_truth doc_id 스키마 확정 및 샘플 fixture 2개 추가
- Retrieval 벤치마크에서 `relevant_doc_ids`/`relevant_docs` 호환 지원
- Retrieval 벤치마크 CLI(`evalvault benchmark retrieval`) 및 JSON/CSV 출력 추가
- nDCG@K 계산 유틸 추가 및 단위 테스트 보강
- StageEvent `doc_ids`와 ground_truth `doc_id` 매핑 규칙 점검 완료

---

## 2. ground_truth doc_id 스키마 (확정)

### 2.1 기본 구조

```json
{
  "name": "retrieval-ground-truth-<name>",
  "version": "1.0.0",
  "description": "...",
  "documents": [
    {"doc_id": "doc-001", "content": "..."}
  ],
  "test_cases": [
    {
      "test_id": "ret-001",
      "query": "...",
      "relevant_doc_ids": ["doc-001"]
    }
  ]
}
```

### 2.2 필드 규칙

- `documents[].doc_id`: **필수**, 문자열 권장, 중복 불가
- `test_cases[].test_id`: StageEvent `metadata.test_case_id`와 동일해야 함
- `test_cases[].relevant_doc_ids`: 관련 문서 doc_id 목록 (1개 이상 권장)
- **레거시 호환**: `relevant_docs`도 허용 (R4 이전 포맷)

### 2.3 relevance map 파생 규칙

StageMetricService 입력용 JSON은 아래 형태로 파생 가능:

```json
{
  "ret-001": ["doc-001"],
  "ret-002": ["doc-002", "doc-003"]
}
```

---

## 3. 메트릭 범위 합의안 (Recall@K, MRR, nDCG@K)

| 메트릭 | 범위 | 기본 K | 계산 규칙 | 비고 |
| --- | --- | --- | --- | --- |
| Recall@K | 0.0 ~ 1.0 | 5 | Top-K 내 관련 문서 비율 | K는 {1, 3, 5, 10} 권장 |
| MRR | 0.0 ~ 1.0 | - | 첫 관련 문서의 역순위(1/rank) | 미조회 시 0.0 |
| nDCG@K | 0.0 ~ 1.0 | 10 | binary relevance 기준 | 관련 문서 0개면 계산 생략 권장 |

합의안(권장 기준):
- K는 데이터셋 크기가 작으면 5, 중대형이면 10을 기본값으로 사용
- 관련 문서가 비어있을 경우 결과를 0으로 기록하거나 계산에서 제외(벤치마크 설정에 명시)
- 경고 기준(초안): Recall@5 < 0.6, MRR < 0.5, nDCG@10 < 0.6

---

## 4. StageEvent doc_ids 매핑 검증

### 4.1 확인 경로

- CLI retriever 경로: `load_retriever_documents` → `apply_retriever_to_dataset` → `StageEventBuilder`
- GraphRAG 경로: `GraphRAGRetriever._normalize_doc_id`가 `document_ids`를 기준으로 정규화
- 비-retriever 경로: contexts 기반 `context_<n>` 값으로 fallback

### 4.2 검증 결과

- **정상 매핑**: retriever 문서에 `doc_id`가 존재하면 StageEvent `doc_ids`는 해당 값으로 기록됨
- **정규화 케이스**: retriever/GraphRAG 결과가 `int`/`"0"` 형태일 때도 문서 목록의 `doc_id`로 변환됨
- **주의 케이스**: retriever 없이 실행 시 `context_<n>`이 사용되어 ground_truth doc_id와 매핑 불가
- **KG 불일치 경고**: GraphRAG 사용 시 KG `source_document_id`와 문서 `doc_id` 불일치 경고 출력

결론: ground_truth doc_id는 **retriever 문서의 doc_id와 동일**하게 유지해야 매핑이 보장됨.

### 4.3 R1~R3 호환성 점검 (요약)

- **R1**: `load_retriever_documents`가 `doc_id`를 우선 사용하고 없으면 `doc_<index>`로 대체함.
  → R4 ground_truth는 **retriever 문서에 명시된 `doc_id`와 동일**해야 함.
- **R2(GraphRAG)**: `_normalize_doc_id()`가 **숫자만 있는 doc_id 문자열을 인덱스로 해석**할 수 있음.
  → `doc-001`처럼 **비숫자 prefix가 있는 doc_id 권장**.
  → KG `source_document_id`도 동일한 `doc_id`로 맞춰야 경고 없이 매핑됨.
- **R3(Dense/Hybrid)**: 검색 결과는 int doc_id(0-based)이며, R1의 `doc_ids` 목록으로 안정적으로 매핑됨.

### 4.4 KG doc_id 정합성 확인 (GraphRAG)

- `tests/fixtures/kg/minimal_graph.json`의 `source_document_id`를
  `doc-001`, `doc-002`로 통일해 `retrieval_test.json`과 정합성 맞춤.
- GraphRAG 벤치마크 실행 시 doc_id 불일치 경고 없이 매핑됨.

---

## 5. 준비된 fixture

- `tests/fixtures/benchmark/retrieval_ground_truth_min.json`
  - 최소 스키마/단일 relevance 테스트용
- `tests/fixtures/benchmark/retrieval_ground_truth_multi.json`
  - 복수 relevant_doc_ids 및 nDCG@K 테스트용

## 6. 스모크 실행 결과 (한국어 retrieval_test.json)

실행 환경:
- embedding profile: `dev` (qwen3-embedding:0.6b, Ollama)
- testset: `examples/benchmarks/korean_rag/retrieval_test.json`
- KG: `tests/fixtures/kg/minimal_graph.json`

```bash
uv run evalvault benchmark retrieval examples/benchmarks/korean_rag/retrieval_test.json \
  --methods bm25,dense,hybrid,graphrag \
  --top-k 5 \
  --embedding-profile dev \
  --kg tests/fixtures/kg/minimal_graph.json \
  --output reports/retrieval_benchmark_korean_rag_dev_k5_20260104.json
```

결과 요약:

| 메트릭 | BM25 | Dense | Hybrid | GraphRAG |
| --- | --- | --- | --- | --- |
| Recall@5 | 1.000 | 1.000 | 1.000 | 1.000 |
| MRR | 0.967 | 0.950 | 0.967 | 0.933 |
| nDCG@5 | 0.975 | 0.962 | 0.975 | 0.951 |

결과 파일:
- `reports/retrieval_benchmark_korean_rag_dev_k5_20260104.json`
- `reports/retrieval_benchmark_graphrag_korean_rag_dev_k5_20260104.json` (GraphRAG 단독)

---

## 7. 후속 제안

- `relevant_docs` → `relevant_doc_ids` 마이그레이션 안내 문서화
- GraphRAG 포함 실측 결과 수집 (Recall/MRR/nDCG)
