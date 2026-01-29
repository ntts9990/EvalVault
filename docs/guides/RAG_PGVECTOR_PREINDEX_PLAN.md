# Postgres/pgvector 사전 인덱싱 계획 (Run 결과 포함)

## 목표
- Postgres + pgvector에 RAG 문서를 사전 인덱싱해, 챗 요청 시 즉시 검색 가능하도록 한다.
- 기존 run_id 결과물도 사전에 벡터화/저장하여 RAG 응답 지연을 최소화한다.
- 임베딩 모델은 `qwen3-embedding:8b`로 고정한다.

## 범위
### 1) RAG 문서 범위
- `docs/guides/USER_GUIDE.md` 기반 문서
- 필요 시 추가 문서 집합(제품 문서/운영 가이드 등)로 확장 가능

### 2) Run 결과 범위
- `EvaluationRun` 메타정보
- `TestCaseResult` 요약(질문/정답/예측/스코어/오류)
- 분석 리포트/아티팩트(요약본/경로)

## 전제
- Postgres + pgvector 준비 완료
- Ollama 서버에서 `qwen3-embedding:8b` 사용 가능
- DB 경로/접속은 `Settings` 기준으로 통일

## 사전 인덱싱 전략
### A. 문서 인덱싱
1) USER_GUIDE 로딩
2) 청킹(문단/문서 단위)
3) 임베딩 생성 (`qwen3-embedding:8b`)
4) `rag_documents` 테이블에 upsert

### B. Run 결과 인덱싱
1) DB에서 모든 run_id 조회
2) run 요약 텍스트 생성
   - 예: run 메타, 메트릭 요약, 실패 케이스 요약 등
3) 필요한 경우 run별 아티팩트/리포트 텍스트 일부 포함
4) 임베딩 생성 (`qwen3-embedding:8b`)
5) `rag_documents`에 run_id 기반 source로 저장
   - 예: `source = "run:{run_id}"`

## 저장 스키마 제안
- 테이블: `rag_documents`
  - `source`: 문서 그룹 구분 (`user_guide` / `run:{run_id}`)
  - `source_hash`: 문서 변경 감지용 해시
  - `doc_id`: 문서 내 순번
  - `content`: 청크 텍스트
  - `embedding`: vector
  - `metadata`: JSON (run_id, metric_name, case_id 등)

## 운영 플로우 (계획)
1) API 서버 시작 시 warm-up
   - `warm_rag_index()`에서 문서/런 인덱스 상태 점검
2) 인덱스 상태 불일치 시 재생성
3) run 신규 생성 시 증분 인덱싱

## 성능/안정성 고려
- 초기 인덱싱은 백그라운드에서 수행 (API 시작 지연 최소화)
- 임베딩 생성 실패 시 재시도/로그
- 대규모 run에 대해 배치 처리 (예: 100개 단위)

## MCP run 요약 필요성
- **필수 아님**
- 목적이 “문서 검색 기반 응답”이면, run 데이터를 직접 텍스트로 인덱싱해서 충분
- MCP는 실행 시 동적 질의에 유리하지만, 지연 원인이므로 기본 경로에서 제외 권장

## 구성 값 (예시)
```
EVALVAULT_RAG_VECTOR_STORE=pgvector
EVALVAULT_RAG_USE_HYBRID=true
EVALVAULT_RAG_EMBEDDING_PROFILE=ollama
OLLAMA_EMBEDDING_MODEL=qwen3-embedding:8b
```

## 체크리스트
- [ ] 문서/런 인덱싱 스크립트 작성
- [ ] 인덱스 상태 체크(해시/카운트)
- [ ] 증분 인덱싱 경로 추가
- [ ] 운영 로그/모니터링

## 구현 스크립트
- 스크립트: `scripts/dev/preindex_pgvector_runs.py`
- 목적: USER_GUIDE + 모든 run 결과를 pgvector에 사전 인덱싱

### 사용 예시
```bash
uv run python scripts/dev/preindex_pgvector_runs.py \
  --source-db data/db/evalvault.db \
  --embedding-model qwen3-embedding:8b \
  --matryoshka-dim 1024 \
  --user-guide-limit 20
```

### 참고 옵션
- `--limit-runs`: 일부 run만 인덱싱
- `--skip-user-guide`: USER_GUIDE 제외
- `--skip-runs`: run 결과 제외
