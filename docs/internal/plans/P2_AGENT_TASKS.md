# P2 작업 분담 문서 (R1 / R4)

> 작성일: 2026-01-07
> 목적: P2 단계에서 두 에이전트가 병렬로 진행할 작업 범위와 구현 방향을 명확히 한다.
> 기준: main 브랜치 기준 문서/코드 (문서 허브 파일명은 main 기준으로 확인)

---

## 1) P2 우선순위 (공유)

- 우선순위: R1 + R4 병렬 -> D1 병렬(완료) -> R2 -> R3
- 본 문서는 R1, R4만 분담한다.

---

## 2) 공통 규칙 (충돌 방지)

- Agent 1은 R1 전용 파일만 수정한다 (R4 파일 수정 금지).
- Agent 2는 R4 전용 파일만 수정한다 (R1 파일 수정 금지).
- 공용 파일(예: `docs/DOCS_HUB.md` 또는 `docs/README.md`)은 수정 금지.
- 변경 전후에 `git status -sb`로 범위를 확인한다.
- 테스트는 해당 작업 영역에 맞는 최소 단위만 수행한다.

---

## 3) Agent 1 (R1: 하이브리드 서치 평가 파이프라인 통합)

### 목표
- Evaluator에 retriever 주입 경로를 만들고, 평가 파이프라인에서 컨텍스트 자동 생성이 동작하도록 통합한다.

### 현재 상태 요약
- CLI에 `--retriever` 옵션과 자동 컨텍스트 채움 로직이 이미 존재한다.
- EvaluatorPort/RagasEvaluator에는 retriever 주입 경로가 없다.

### 작업 범위

1. **포트 확장**
   - `EvaluatorPort`에 retriever 관련 인자를 추가한다.
   - Retriever는 `RetrieverPort`(korean_nlp_port)를 재사용한다.

2. **도메인 평가 통합**
   - `RagasEvaluator.evaluate()`에 retriever/문서 ID/Top-K 입력을 추가한다.
   - 컨텍스트가 비어 있는 경우에만 retriever를 호출하도록 한다.
   - retriever 결과의 `doc_ids/scores/top_k`를 메타데이터로 구성한다.

3. **CLI 연계 정리**
   - 기존 `apply_retriever_to_dataset()` 호출을 제거하거나, Evaluator로 위임한다.
   - StageEventBuilder에 전달되는 `retrieval_metadata`가 유지되도록 경로를 조정한다.

### 수정 대상 파일 (예시)
- `src/evalvault/ports/inbound/evaluator_port.py`
- `src/evalvault/domain/services/evaluator.py`
- `src/evalvault/adapters/inbound/cli/commands/run.py`
- `src/evalvault/adapters/inbound/cli/commands/run_helpers.py`
- `src/evalvault/domain/services/stage_event_builder.py` (필요 시)

### DoD
- retriever 주입 시 빈 컨텍스트가 자동 생성된다.
- Stage events에 `doc_ids/top_k/scores/retrieval_time_ms`가 기록된다.
- 기존 CLI 사용 방식(`--retriever`, `--retriever-docs`)은 깨지지 않는다.

### 테스트 가이드
- `tests/unit`에 retriever 주입 경로 테스트 추가.
- 기존 `evalvault run` 스모크(작은 fixture)로 회귀 확인.

---

## 4) Agent 2 (R4: 벤치마크 정비/검색 품질 메트릭)

### 목표
- 검색 품질 메트릭을 표준화하고 벤치마크 출력 스키마를 안정화한다.

### 현재 상태 요약
- retrieval benchmark는 `recall_at_k/mrr/ndcg_at_k` 중심이다.
- stage metrics에는 `retrieval.precision_at_k`와 `retrieval.recall_at_k`가 존재한다.

### 작업 범위

1. **검색 품질 메트릭 보강**
   - `compute_retrieval_metrics()`에 `precision_at_k`를 추가한다.
   - `average_retrieval_metrics()`에 새 메트릭이 평균에 포함되도록 한다.

2. **벤치마크 출력 정비**
   - CLI `benchmark retrieval` 출력에 `precision_at_k` 포함.
   - JSON/CSV 스키마를 문서/테스트와 정합성 맞추기.

3. **테스트 갱신**
   - `tests/unit/test_benchmark_runner.py`의 메트릭 키 기대값 갱신.
   - 필요한 경우 `tests/unit/test_cli.py`의 출력 스키마 기대값 갱신.

### 수정 대상 파일 (예시)
- `src/evalvault/domain/services/retrieval_metrics.py`
- `src/evalvault/adapters/inbound/cli/commands/benchmark.py`
- `tests/unit/test_benchmark_runner.py`
- `tests/unit/test_cli.py` (필요 시)

### DoD
- 벤치마크 결과에 `precision_at_k`가 포함된다.
- JSON/CSV 출력 스키마가 문서와 테스트를 통과한다.
- Stage metrics와 벤치마크의 지표명이 호환된다.

### 테스트 가이드
- `uv run pytest tests/unit/test_benchmark_runner.py -v`
- 필요 시 `tests/unit/test_cli.py` 부분 실행

---

## 5) 공통 주의 사항

- 문서 허브 경로는 main 기준 파일명을 따른다.
- 구현 후 문서 업데이트가 필요하면 별도 PR로 분리한다.
