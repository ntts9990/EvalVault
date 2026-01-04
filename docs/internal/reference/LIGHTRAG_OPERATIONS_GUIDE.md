# LightRAG 운영 가이드 (현 구조 기준)

> 범위: EvalVault의 GraphRAG/LightRAG 스타일 구성(`NetworkXKnowledgeGraph` + `GraphRAGRetriever`) 운영
> 전제: LlamaIndex는 사용하지 않음

## 1. 구조 요약

| 구성 요소 | 역할 | 위치 |
|----------|------|------|
| GraphRAGRetriever | KG + BM25/Dense 결과를 RRF로 합쳐 검색 | `src/evalvault/adapters/outbound/kg/graph_rag_retriever.py` |
| NetworkXKnowledgeGraph | 엔티티/관계를 NetworkX로 보관 | `src/evalvault/adapters/outbound/kg/networkx_adapter.py` |
| ParallelKGBuilder | 대용량 문서 병렬 KG 생성 | `src/evalvault/adapters/outbound/kg/parallel_kg_builder.py` |
| EntityExtractor | 보험 도메인 정규식 기반 엔티티/관계 추출 | `src/evalvault/domain/services/entity_extractor.py` |
| KiwiTokenizer(옵션) | 키워드 추출(한국어) | `src/evalvault/adapters/outbound/nlp/korean/kiwi_tokenizer.py` |
| StageEvent 로깅 | retriever 메타데이터/성능 기록 | `src/evalvault/domain/entities/stage.py` |

## 2. 운영 흐름 (요약)

1) 문서/문서 ID 준비
2) KG 생성 및 JSON 저장
3) GraphRAG 실행 (`evalvault run --retriever graphrag`)
4) StageEvent/트레이스 확인
5) 배치 업데이트 및 버전 관리

## 3. KG JSON 스키마

`NetworkXKnowledgeGraph.to_dict()` 출력과 동일하며, `entities`/`relations` 배열을 포함합니다.

```json
{
  "entities": [
    {
      "name": "삼성생명",
      "entity_type": "organization",
      "canonical_name": "삼성생명",
      "source_document_id": "doc-001",
      "attributes": {"domain": "insurance"},
      "confidence": 0.95,
      "provenance": "regex"
    }
  ],
  "relations": [
    {
      "source": "삼성생명",
      "target": "종신보험",
      "relation_type": "provides",
      "attributes": {"evidence": "삼성생명 종신보험 상품"},
      "confidence": 0.9,
      "provenance": "regex"
    }
  ],
  "statistics": {
    "num_entities": 10,
    "num_relations": 8
  }
}
```

!!! warning
    `source_document_id`는 **retriever 문서의 `doc_id`와 반드시 일치**해야 합니다.

## 4. 운영 절차

### 4.1 문서/ID 준비

- GraphRAG는 `--retriever-docs` 파일을 기준으로 문서 본문을 로딩합니다.
- `doc_id`는 KG의 `source_document_id`와 일치해야 경고 없이 정상 매핑됩니다.
- 지원 형식: JSON/JSONL/TXT

```json
[
  {"doc_id": "doc-001", "content": "보험 약관 텍스트..."},
  {"doc_id": "doc-002", "content": "보장 내용 텍스트..."}
]
```

### 4.2 KG 생성 (병렬 빌더)

아래 예시는 단일 문서로 KG를 만든 뒤 JSON으로 저장하는 **실행 가능 예시**입니다.

```bash
uv run python - <<'PY'
from pathlib import Path
import json

from evalvault.adapters.outbound.kg.parallel_kg_builder import ParallelKGBuilder

doc_path = Path("docs/guides/USER_GUIDE.md")
documents = [doc_path.read_text(encoding="utf-8")]
doc_ids = ["user_guide"]

builder = ParallelKGBuilder(workers=1, batch_size=1, store_documents=False)
result = builder.build(documents, document_ids=doc_ids)

output = Path("reports/kg_light_rag.json")
payload = result.graph.to_dict()
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved: {output}")
PY
```

### 4.3 GraphRAG 실행

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --retriever graphrag \
  --retriever-docs scripts/perf/r3_retriever_docs.json \
  --kg reports/kg_light_rag.json \
  --metrics faithfulness
```

### 4.4 관측/디버깅 포인트

- StageEvent 기본 필드: `doc_ids`, `scores`, `top_k`, `retrieval_time_ms`
- GraphRAG 확장 attributes: `graph_nodes`, `graph_edges`, `subgraph_size`, `community_id`
- span attributes: `retriever.graphrag.*` (예: `retriever.graphrag.search_ms`)

StageEvent는 DB 저장 및 JSONL로 추출되며, Phoenix/Langfuse 트레이스와 연결됩니다.

## 5. 성능/품질 튜닝 포인트

| 파라미터 | 설명 | 위치 |
|---------|------|------|
| hop_limit | KG 이웃 확장 깊이 | `GraphRAGRetriever` |
| entity_weight / relation_weight / chunk_weight | RRF 가중치 분배 | `GraphRAGRetriever` |
| rrf_k | RRF 분모 상수 | `GraphRAGRetriever` |
| candidate_multiplier | BM25/Dense 후보 확장 배수 | `GraphRAGRetriever` |
| min_entity_match_length | 엔티티 매칭 최소 길이 | `GraphRAGRetriever` |
| workers / batch_size | KG 빌드 병렬성 | `ParallelKGBuilder` |

!!! tip
    Dense/BM25가 초기화 실패하더라도 KG만으로 검색이 동작합니다.
    다만 품질 저하 가능성이 있으므로 로그 경고를 확인하세요.

## 6. 확장 포인트

1) **엔티티/관계 추출 개선**
   - 규칙 기반: `EntityExtractor` 패턴 확장
   - LLM 보강: `RelationAugmenterPort` 구현 + `LLMRelationAugmenter` 활용
   - 경로: `src/evalvault/domain/services/entity_extractor.py`, `src/evalvault/ports/outbound/relation_augmenter_port.py`

2) **키워드 추출 교체**
   - 기본: `KiwiTokenizer.extract_keywords`
   - 대체: `GraphRAGRetriever(keyword_extractor=...)` 주입
   - 경로: `src/evalvault/adapters/outbound/nlp/korean/kiwi_tokenizer.py`

3) **KG 저장소/구조 변경**
   - 현재: `NetworkXKnowledgeGraph`
   - 확장: 다른 그래프 저장소 어댑터 추가 후 `GraphRAGRetriever`에 주입
   - 경로: `src/evalvault/adapters/outbound/kg/networkx_adapter.py`

4) **검색 융합 로직 확장**
   - RRF 외 다른 랭킹(예: weighted sum, reranker) 추가
   - 경로: `GraphRAGRetriever._rrf_merge`, `_resolve_rrf_weights`

5) **StageEvent/Trace 메타데이터 확장**
   - `attributes`에 성능/품질 지표 추가
   - 경로: `apply_retriever_to_dataset` 및 `_extract_graphrag_attributes`
   - 파일: `src/evalvault/adapters/inbound/cli/commands/run_helpers.py`

6) **KG 기반 테스트셋 생성**
   - `query_strategies` 기반 질문 생성
   - 경로: `src/evalvault/adapters/outbound/kg/query_strategies.py`

## 7. 운영 체크리스트

- KG `source_document_id`와 retriever `doc_id` 일치 여부 확인
- `GraphRAGRetriever` 가중치/후보 수 설정 기록
- StageEvent JSONL 및 Trace URL 보관
- 배치 업데이트 시 KG 버전 태깅(파일명/메타데이터)

!!! note
    GraphRAG는 NetworkX in-memory 구조입니다. 문서 수가 크게 늘면
    프로세스 메모리 사용량을 반드시 점검하세요.

## 8. 운영/장애 대응 체크리스트 (실사용 기준)

### 8.1 증상별 점검 순서

1) **검색 결과가 비어 있음**
   - `--retriever-docs` 로딩 실패 여부 확인 (빈 문서 포함)
   - KG JSON에 `entities/relations`가 존재하는지 확인
   - KG `source_document_id`와 문서 `doc_id` 매칭 확인

2) **품질 급락**
   - StageEvent의 `graph_nodes`, `graph_edges`, `retrieval_time_ms` 비교
   - `hop_limit`/`candidate_multiplier` 과도 설정 여부 확인
   - Dense/BM25 초기화 실패 로그 확인 (경고 발생 시 품질 저하 가능)

3) **지연 급증**
   - `retriever.graphrag.search_ms` span 확인
   - `candidate_multiplier`/`top_k` 축소로 후보 수 조정
   - KG 빌드 batch/worker 설정 재검토

### 8.2 신속 복구 옵션

- Dense/BM25가 불안정하면 KG 단독 모드로 임시 운용
- `hop_limit`을 0~1로 낮춰 탐색 깊이를 축소
- `candidate_multiplier`를 1로 낮춰 후보 수를 제한
- KG를 직전 안정 버전으로 롤백(파일 버전 유지)

### 8.3 관측/로그 확인

```bash
uv run evalvault stage summary <run_id> --db-path <db_path>
```

- StageEvent `retrieval_time_ms`, `duration_ms` 추이 확인
- `graph_nodes`/`graph_edges` 급감 여부 확인
- Phoenix/Langfuse trace로 retriever span 지표 확인

### 8.4 배치 업데이트 운영 규칙

- KG 파일과 retriever 문서 파일을 **동일 버전 명명 규칙**으로 저장
- KG 빌드 통계(`documents_processed`, `entities_added`, `relations_added`) 기록
- 업데이트 후 샘플 쿼리 스모크 실행(5~10건)
