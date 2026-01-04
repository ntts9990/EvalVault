# R2 완료 보고서

> 업데이트: 2026-01-04
> 범위: R2 GraphRAG 스타일 검색 최적화

---

## 1. 완료 요약

- GraphRAGRetriever KG/BM25/Dense RRF 융합 경로 구현
- `evalvault run --retriever graphrag --kg ...` 실행 흐름 연결
- 쿼리 키워드 매칭, KG 검색 캐시, 증분 병합 지원 추가
- StageEvent 확장 메타데이터/레이턴시 기록 및 span attribute 보강

---

## 2. 구현 내역 (핵심 변경)

- KG 로딩 헬퍼 추가 (`load_knowledge_graph`)
- GraphRAG retriever: 키워드 매칭(옵션), doc_id 매핑 보강, LRU 캐시, `update_graph` 지원
- CLI: `--retriever graphrag`, `--kg` 옵션 및 경고/검증 흐름 추가
- StageEvent 확장 메타데이터 기록
  - `retrieval_time_ms`
  - `graph_nodes`, `graph_edges`, `subgraph_size`, `community_id`
- span attributes 추가 (`retriever.graphrag.*`)
- doc_id 정규화 규칙: GraphRAG 결과의 `doc_id` → dataset `doc_id` 매핑 우선

---

## 3. 검증 및 증거

- 추가 테스트:
  - `tests/unit/adapters/outbound/kg/test_graph_rag_retriever.py`
  - `tests/unit/test_kg_networkx.py`
  - `tests/unit/test_run_memory_helpers.py`
- 실행:
  - run_id: `d60bce6a-ce38-4210-a63e-c8d73d9ecfe7`
  - DB: `reports/r2_graphrag.db`
  - stage_events: `reports/r2_graphrag_stage_events.jsonl`
  - stage_report: `reports/r2_graphrag_stage_report.txt`
  - 모델 프로필: `dev` (ollama/gemma3:1b)
  - dataset: `tests/fixtures/e2e/graphrag_smoke.json`
  - retriever docs: `tests/fixtures/e2e/graphrag_retriever_docs.json`
  - KG fixture: `tests/fixtures/kg/minimal_graph.json`
  - 참고: 영어 쿼리에서 Kiwi 토큰이 비어 BM25 경고가 발생했으며, regex fallback으로 해소
- 비교 샘플(openai 프로필):
  - run_id: `fd810155-d69f-4c2c-944a-be960a32aa62`
  - DB: `reports/r2_graphrag_openai.db`
  - stage_events: `reports/r2_graphrag_openai_stage_events.jsonl`
  - stage_report: `reports/r2_graphrag_openai_stage_report.txt`
  - DebugReport: `reports/debug_report_r2_graphrag_openai.md`, `reports/debug_report_r2_graphrag_openai.json`
  - 참고: 온라인 실행으로 Dense retriever 초기화 정상 (TOKENIZERS_PARALLELISM=false)

---

## 4. 사용자 가이드 반영

- CLI 가이드 retriever/GraphRAG 옵션 추가 (`docs/guides/CLI_GUIDE.md`)
- ROADMAP R2 체크리스트 갱신 (`docs/status/ROADMAP.md`)

---

## 5. 미해결/후속 항목

- GraphRAG 벤치마크 비교/성능 지표(Recall@K, nDCG) 실측
- 대용량(R3) 최적화와의 연계 검증
