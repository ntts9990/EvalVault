# R3 완료 보고서

> 업데이트: 2026-01-04
> 범위: R3 1000건 대규모 문서 처리 최적화 (Track D 중심)

---

## 1. 완료 요약

- 병렬/배치 기반 KG 구축 모듈 추가로 대용량 처리 경로 확보
- Dense retriever에 배치 자동 튜닝 및 FAISS CPU/GPU 자동 선택 로직 적용
- JSON 스트리밍 로더에 ijson 경로 추가(설치 시 진짜 스트리밍 파싱)
- R3 스모크 스크립트 + JSONL 로그 포맷 확정 및 실측 저장 완료
- **`evalvault kg build` CLI 명령 추가** (ParallelKGBuilder 연결)
- **`pyproject.toml`에 `perf` optional extra 추가** (`faiss-cpu`, `ijson`)

---

## 2. 구현 내역 (핵심 변경)

- 병렬 KG 빌더: `src/evalvault/adapters/outbound/kg/parallel_kg_builder.py`
  - ProcessPool 기반 병렬 추출 + 배치 처리
  - 진행 콜백/통계 수집 + 문서 저장 옵션
- Dense retriever 최적화: `src/evalvault/adapters/outbound/nlp/korean/dense_retriever.py`
  - `batch_size<=0` 자동 튜닝
  - FAISS CPU/GPU 자동 선택 (`faiss_use_gpu=None` 기본)
  - 실제 GPU 사용 여부 `faiss_gpu_active` 제공
  - span에 성능 attributes 기록 (`index_build_time_ms`, `index_size`, `batch_size`, `cache_hit`, `faiss_gpu_active`)
- 스트리밍 JSON 개선: `src/evalvault/adapters/outbound/dataset/streaming_loader.py`
  - ijson 설치 시 진짜 스트리밍 파싱 경로
- 스모크 스크립트/로그: `scripts/perf/r3_dense_smoke.py`
  - JSONL 로그 포맷 유지 + `--faiss-gpu/--faiss-cpu` 강제 옵션
  - `--allow-omp-duplicate`로 macOS libomp 충돌 회피
- StageEvent 보강: `src/evalvault/domain/services/stage_event_builder.py`
  - `retrieval_time_ms` → `duration_ms` 기록
  - 성능 attributes pass-through (`index_build_time_ms`, `batch_size` 등)
- Langfuse 메타데이터 보강: `src/evalvault/adapters/outbound/tracker/langfuse_adapter.py`
  - trace_id/trace_url를 `tracker_metadata`와 `langfuse_trace_id`에 저장
- **CLI 명령 추가**: `src/evalvault/adapters/inbound/cli/commands/kg.py`
  - `evalvault kg build` 명령으로 ParallelKGBuilder 연결
  - 옵션: `--output`, `--workers`, `--batch-size`, `--store-documents`, `--verbose`
  - Rich 테이블로 빌드 결과 통계 출력
  - JSON 파일 저장 지원 (`--output`)
- **pyproject.toml 확장**: `pyproject.toml`
  - `perf` optional extra 추가: `faiss-cpu>=1.8.0`, `ijson>=3.3.0`
  - 설치: `uv sync --extra perf`

---

## 3. 검증 및 증거

### 3.1 스모크 스크립트

- 실행 스크립트:
  - `uv run python scripts/perf/r3_dense_smoke.py --use-faiss --faiss-cpu --allow-omp-duplicate --model-name sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 --documents 1000 --queries 200 --output scripts/perf/r3_smoke_real.jsonl`
- 최신 실행 결과:
  - run_id: `r3-smoke-1767502115`
  - index_ms: `9374.449` (약 `106.673 docs/sec`)
  - search_total_ms: `4130.96`, p95 `22.804ms`, QPS `48.415`
  - faiss_enabled: `true`, faiss_gpu_active: `false`
  - 산출물 위치: `scripts/perf/r3_smoke_real.jsonl`

### 3.2 테스트

- `uv run pytest tests/unit/adapters/outbound/kg/test_parallel_kg_builder.py -v`
- `uv run pytest tests/unit/test_korean_dense.py -v`
- `uv run pytest tests/unit/test_streaming_loader.py -v`
- `uv run pytest tests/unit/test_cli.py -k "kg_build" -v` (7 tests: help, basic, output, workers, verbose, empty, directory)

### 3.3 evalvault run 기반 샘플 (DB/리포트)

- 실행 스크립트:
  - `OPENAI_API_KEY=dummy uv run evalvault run scripts/perf/r3_evalvault_run_dataset.json --metrics "" --retriever bm25 --retriever-docs scripts/perf/r3_retriever_docs.json --retriever-top-k 2 --db reports/r3_bm25.db --stage-store --stage-events reports/r3_bm25_stage_events.jsonl`
  - `uv run evalvault stage report 3fd2f7e6-98ba-4d7b-9b1d-2760aade541d --db reports/r3_bm25.db > reports/r3_bm25_stage_report.txt`
- run_id: `3fd2f7e6-98ba-4d7b-9b1d-2760aade541d`
- DB/로그
  - DB: `reports/r3_bm25.db`
  - stage_events: `reports/r3_bm25_stage_events.jsonl`
  - stage report: `reports/r3_bm25_stage_report.txt`
  - DebugReport: `reports/debug_report_r3_bm25.md`, `reports/debug_report_r3_bm25.json`
- fixtures
  - `scripts/perf/r3_evalvault_run_dataset.json`
  - `scripts/perf/r3_retriever_docs.json`

### 3.4 dense/FAISS run 샘플 (DB/리포트)

- run_id: `r3-dense-faiss-1767506494`
- 모델: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- DB/로그
  - DB: `reports/r3_dense_faiss.db`
  - stage_events: `reports/r3_dense_faiss_stage_events.jsonl`
  - stage report: `reports/r3_dense_faiss_stage_report.txt`
  - DebugReport: `reports/debug_report_r3_dense_faiss.md`, `reports/debug_report_r3_dense_faiss.json`
- retrieval attributes 예시
  - `index_build_time_ms`, `index_size`, `total_docs_searched`, `faiss_gpu_active`

### 3.5 Phoenix 로깅 스모크

- 실행 로그: `reports/r3_bm25_phoenix_run.log`
- run_id: `d82e84fe-9b56-4b28-bde6-dad0f031f99a`
- DB: `reports/r3_bm25_phoenix.db`
- Phoenix trace: `http://localhost:6006/#/traces/df215755-c975-4012-a6c1-ccb13d360453`

### 3.6 Langfuse 로깅 스모크

- 실행 로그: `reports/r3_bm25_langfuse3_run.log`
- run_id: `3ab112c4-f0ae-447d-ab2e-1a4f30e2e114`
- DB: `reports/r3_bm25_langfuse3.db`
- Langfuse trace_id: `73eea26251f01a2b352d17842887f98a`
- Langfuse trace_url: `http://localhost:3000/project/cmjixj06j0006nq07ys4tz9i2/traces/73eea26251f01a2b352d17842887f98a`
- DebugReport: `reports/debug_report_r3_bm25_langfuse3.md`, `reports/debug_report_r3_bm25_langfuse3.json`
- tracker_metadata 저장 확인: trace_id/host/trace_url 저장됨
- Langfuse API `trace.get`으로 조회 확인
- backfill 스크립트: `scripts/perf/backfill_langfuse_trace_url.py`
  - 적용 DB: `reports/r3_bm25_langfuse.db`, `reports/r3_bm25_langfuse2.db`
  - 전체 DB 스캔 완료 (metadata 없는 DB는 자동 스킵)

---

## 4. 후속 항목 (R3 범위 외)

- ~~CLI 연결: `evalvault kg build`에 ParallelKGBuilder 연결 필요~~ ✅ 완료
- ~~공유 파일: `pyproject.toml`에 `faiss-cpu`, `ijson` optional extra 반영 필요~~ ✅ 완료
- CUDA 환경 검증: macOS 환경 제약으로 FAISS GPU 실검증은 보류 (Linux/CUDA 환경에서 후속 검증)
- Langfuse trace_url/CLI 표시 연동은 P4.1 이후 CLI/로깅 조율 필요
- R2 GraphRAG 최적화 경로는 R2 완료 이후 연동 예정

---

## 5. JSONL ↔ StageEvent 매핑 가이드

> JSONL 성능 로그는 run-level 지표이며, StageEvent는 test_case 단위입니다.
> Debug/D1에서 run-level 요약을 stage_type="retrieval" attributes에 병합할 때 사용합니다.

### 5.1 매핑 규칙 (권장)

| JSONL 필드 | StageEvent.attributes | 비고 |
|-----------|-----------------------|------|
| index_ms | index_build_time_ms | 인덱스 구축 시간 |
| documents | index_size | 검색 인덱스 크기 |
| search_total_ms | total_search_time_ms | run-level 합계 |
| search_ms_p95 | search_p95_ms | run-level p95 |
| search_qps | search_qps | run-level QPS |
| batch_size | batch_size | 임베딩 배치 |
| faiss_gpu_active | faiss_gpu_active | GPU 사용 여부 |
| total_docs_searched | total_docs_searched | run-level 검색 문서 수 |

### 5.2 StageEvent duration_ms

- retrieval 단계 `retrieval_time_ms`가 전달되면 `duration_ms`에 동일 값을 기록하도록 반영됨.
- 대용량 경로에서 `retrieval_time_ms`를 수집할 수 있는 경우 StageMetricService 레이턴시 계산에 자동 반영됨.

---

## 6. 환경 및 비고

- 로컬 환경: macOS, CPU 기준 측정
- 설치된 런타임 패키지(로컬): `faiss-cpu`, `ijson`
