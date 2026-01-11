# 03. 데이터/실행 흐름 (run_id 중심)

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: EvalVault를 “실행 단위(run_id)” 관점으로 이해한다. 실행 → 저장 → 분석 → 비교가 어떻게 연결되는지 설명한다.
- **독자**: EvalVault를 실제로 실행/운영하는 내부 개발자
- **선행 지식**: CLI 실행, 파일/DB 기반 아티팩트 개념

---

## TL;DR

- EvalVault의 중심 객체는 “평가 실행”이며, 실행은 `run_id`로 식별된다.
- 실행 결과는 DB에 저장되고, 분석/리포트 아티팩트가 파일로 생성된다.
- 분석(단일 실행)과 비교(두 실행)는 별도 산출물 디렉터리를 사용한다.
- Web UI는 동일 DB를 바라보면 CLI 실행 결과를 그대로 조회할 수 있다.

---

## 1) 사용자 관점 플로우

### 1.1 단일 실행 + 자동 분석

```bash
uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db \
  --auto-analyze
```

### 1.2 A/B 비교

```bash
uv run evalvault analyze-compare <RUN_A> <RUN_B> --db data/db/evalvault.db
```

---

## 2) 산출물(Artifacts) 구조

> EvalVault는 “요약 리포트”와 “모듈별 원본 결과(아티팩트)”를 분리한다.

### 2.1 단일 실행 자동 분석 산출물

- 요약 JSON: `reports/analysis/analysis_<RUN_ID>.json`
- 보고서(Markdown): `reports/analysis/analysis_<RUN_ID>.md`
- 아티팩트 디렉터리: `reports/analysis/artifacts/analysis_<RUN_ID>/`
  - 인덱스: `index.json`
  - 노드별 결과: `<node_id>.json`
  - 최종 출력(있다면): `final_output.json`

이 구조는 CLI 유틸에서 실제로 생성한다.
- 경로/디렉터리: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py` (`resolve_output_paths`, `resolve_artifact_dir`)
- 아티팩트 쓰기: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py` (`write_pipeline_artifacts`)

### 2.2 비교 분석 산출물

- 요약 JSON: `reports/comparison/comparison_<RUN_A>_<RUN_B>.json`
- 보고서(Markdown): `reports/comparison/comparison_<RUN_A>_<RUN_B>.md`
- 아티팩트 인덱스: `reports/comparison/artifacts/comparison_<RUN_A>_<RUN_B>/index.json`

> 비교 쪽 산출물 구조는 커맨드별 구현에 따라 prefix/경로가 달라질 수 있으므로, 실제 산출물은 “index.json을 기준으로 탐색”하는 것을 원칙으로 한다.

---

## 3) 내부 동작(구현) 플로우 (CLI `run` 기준)

> 이 절은 ‘개념’이 아니라, 실제 코드가 어떤 흐름으로 연결되는지의 요약이다.

### 3.1 평가 실행

- CLI 엔트리: `src/evalvault/adapters/inbound/cli/commands/run.py` (`def run(...)`)
- 평가 엔진: `src/evalvault/domain/services/evaluator.py` (`class RagasEvaluator`)

핵심 개념:
- `RagasEvaluator.evaluate()`는 threshold 우선순위를 명시한다.
  - **CLI 옵션 > 데이터셋 내장 > 기본값(0.7)**
- retriever가 지정되면 평가 전에 컨텍스트가 채워질 수 있다.
  - `RagasEvaluator.evaluate()` 내부에서 `apply_retriever_to_dataset(...)` 호출

### 3.2 Domain Memory 옵션

- 메모리 기반 threshold 조정: `src/evalvault/domain/services/memory_aware_evaluator.py` (`MemoryAwareEvaluator.evaluate_with_memory`)
- 컨텍스트 보강(사실 삽입): `MemoryAwareEvaluator.augment_context_with_facts`

### 3.3 Stage Events(단계 이벤트) 생성

- Stage 이벤트 빌더: `src/evalvault/domain/services/stage_event_builder.py` (`StageEventBuilder.build_for_run`)
- 생성되는 대표 stage_type 예:
  - `input` / `retrieval` / `output`

> Stage 이벤트는 `--stage-events`(JSONL로 내보내기), `--stage-store`(DB 저장) 같은 옵션과 연결된다.

### 3.4 자동 분석(`--auto-analyze`)

CLI 구현 흐름(요약):

- `analysis_prefix = f"analysis_{result.run_id}"`
- 출력 경로 해석: `resolve_output_paths(...)`
- 파이프라인 실행:
  - `build_analysis_pipeline_service(storage=..., llm_adapter=...)`
  - `pipeline_service.analyze_intent(AnalysisIntent.GENERATE_DETAILED, run_id=..., evaluation_run=..., use_llm_report=True, ...)`
- 아티팩트 저장:
  - `resolve_artifact_dir(...)`
  - `write_pipeline_artifacts(pipeline_result, artifacts_dir=...)` → `index.json` 생성
- 요약 JSON 저장:
  - `serialize_pipeline_result(...)` + `artifacts` 필드 추가
- 리포트(Markdown) 저장:
  - `extract_markdown_report(pipeline_result.final_output)`

근거:
- `src/evalvault/adapters/inbound/cli/commands/run.py` (auto-analyze 블록)
- `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
- `src/evalvault/domain/entities/analysis_pipeline.py` (`AnalysisIntent.GENERATE_DETAILED`)
- `src/evalvault/adapters/outbound/analysis/pipeline_factory.py` (모듈 등록)

---

## 4) 실패/예외 흐름(운영 관점)

- 입력 스키마 오류: 데이터셋 파서/전처리 단계에서 실패할 수 있다.
- 외부 의존성 오류: LLM/Tracker 연동(키/네트워크/의존성 미설치) 실패 가능
- 장시간 실행: 분석 파이프라인이 장시간 수행될 수 있으므로 타임아웃/리소스 관리를 고려한다.

> **NOTE**: 실패 케이스의 “원인 위치”를 빠르게 찾으려면 `run_id` 기준으로 DB 기록과 `artifacts/index.json`을 함께 본다.

---

## 5) 향후 변경 시 업데이트 가이드

- `--auto-analyze`의 기본 intent/옵션이 바뀌면: 03장(자동 분석 흐름)과 06장(검증 루틴)을 함께 갱신한다.
- Stage 이벤트 스키마/저장 방식이 바뀌면: 03장(Stage Events), 12장(운영), 13장(표준)을 갱신한다.
- 분석 파이프라인 노드/모듈이 추가되면: 03장에는 “저장 규칙(index.json 중심)”을 유지하고, 노드 목록은 별도 장(07/08)으로 이동한다.

---

## Evidence

- `src/evalvault/adapters/inbound/cli/commands/run.py` (평가/저장/자동 분석 오케스트레이션)
- `src/evalvault/domain/services/evaluator.py` (`RagasEvaluator.evaluate`, threshold 우선순위)
- `src/evalvault/adapters/inbound/cli/utils/analysis_io.py` (artifacts/index.json 생성 규칙)
- `src/evalvault/domain/services/stage_event_builder.py` (stage 이벤트 생성)
- `docs/guides/USER_GUIDE.md` (워크플로/결과 확인 가이드)

---

## 전문가 관점 체크리스트

- [ ] 초급 독자가 “어떤 파일이 어디에 생기는지” 즉시 이해할 수 있는가
- [ ] 실행/분석/비교의 산출물 경로가 일관적으로 제시되는가
- [ ] 실패/예외 흐름이 최소한의 실무 힌트를 제공하는가
