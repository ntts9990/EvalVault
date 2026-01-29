# 03. Workflows (평가 → 분석 → 비교 → 개선)

이 챕터는 “어떤 순서로 무엇을 실행해야 하는지”를 작업 흐름 중심으로 정리한다.
각 워크플로는 목표, 명령어, 기대 결과, 실패 시 조치까지 포함한다.

## TL;DR

- 기본 루프는 4단계다: 평가(run) → 분석(analyze/pipeline) → 비교(compare) → 개선(데이터/프롬프트/리트리버 변경).
- 실행의 연결 키는 항상 `run_id`다.
- 분석의 근거는 아티팩트 디렉터리(`.../analysis_<RUN_ID>/index.json`)로 추적한다.

이 문서는 두 레벨로 구성한다.

- 상단: 빠른 실행 템플릿(“바로 돌리기”)
- 하단: 책 수준의 상세 플레이북(“운영/CI/트러블슈팅까지”)
  각 명령의 진실은 코드(특히 Typer CLI)이며, 필요한 경우 근거 파일 경로를 함께 적는다.

## 목차

- Part 1. 빠른 실행 템플릿
  - 워크플로 0: 5분 스모크
  - 워크플로 1: 평가 + 자동 분석
  - 워크플로 2: 재분석
  - 워크플로 3: 비교
  - 워크플로 4: 통계 기반 비교
  - 워크플로 5: Web UI
  - 워크플로 6: 회귀 게이트
  - 공통 트러블슈팅
- Part 2. 운영 플레이북(상세)
  - 7. 워크플로 설계 원칙(실험 단위/조건 고정/산출물)
  - 8. 환경 준비(설치/.env/프로필/DB)
  - 9. 평가 실행(run) 심화: preset, run-simple/run-full, auto-analyze
  - 10. 이력 조회/내보내기(history/export)
  - 11. 분석(analyze) 심화: nlp/causal/playbook/dashboard
  - 12. 비교(compare) 심화: 파일/아티팩트/표 출력
  - 13. 통계 비교(analyze-compare) 심화: comparison_{A8}_{B8}
  - 14. 쿼리 기반 파이프라인(pipeline analyze)
  - 15. 품질 게이트(gate) vs 회귀 게이트(regress/ci-gate)
  - 16. Web UI 운영 루프(serve-api + frontend)
  - 17. 아티팩트 무결성(lint)과 자동화
  - 18. 흔한 실패 모드별 디버깅 트리
  - 19. 체크리스트/자가 점검(확장)

## 공통 전제(모든 워크플로에 적용)

- DB 경로를 고정하면 재현과 UI 동기화가 쉬워진다.
- 동일 데이터셋/동일 프로필로 두 번 실행하면 비교 가능한 실험이 된다.
- 실패 원인 파악은 “추측”보다 “아티팩트/로그”를 우선한다.

---

## 워크플로 0: 5분 스모크(환경이 살아 있는지 확인)

### 목표

- LLM 설정/프로필/DB 연결이 정상인지 확인한다.

### 실행

```bash
uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db
```

### 기대 결과

- `run_id` 출력
- 최소 결과 요약 출력

### 실패 시 조치(우선순위)

1) API 키/프로필 설정 확인
2) DB 경로 권한/경로 확인
3) 선택 메트릭 입력 요구사항 확인(ground truth 유무 등)

---

## 워크플로 1: 평가 + 자동 분석(기본 루프)

### 목표

- 한 번의 실행으로 평가와 분석 리포트를 모두 만든다.

### 실행

```bash
uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db \
  --auto-analyze
```

### 기대 결과

- `analysis_<RUN_ID>.json`, `analysis_<RUN_ID>.md` 생성
- `reports/analysis/artifacts/analysis_<RUN_ID>/index.json` 생성

### 해석(바로 읽는 순서)

1) MD 리포트로 전체 스캔(어떤 메트릭이 문제인지)
2) 요약 JSON으로 수치 확인(평균/분산/통과율)
3) 아티팩트 index.json으로 근거 파일 점프(원인 후보)

---

## 워크플로 2: 기존 run_id를 재분석(분석만 다시 돌리기)

### 목표

- 이미 저장된 실행(run_id)에 대해 분석만 다시 실행한다.
- 분석 모듈 옵션(예: NLP/인과/플레이북)을 바꿔가며 원인을 좁힌다.

### 실행

```bash
uv run evalvault analyze <RUN_ID> \
  --profile dev \
  --db data/db/evalvault.db
```

### 기대 결과

- 동일 run_id의 분석 산출물/아티팩트가 새로 갱신된다.

---

## 워크플로 3: 두 실행 비교(개선/회귀 판단)

### 목표

- 변경 전/후 두 `run_id`를 비교해 “실제 개선”인지 판단한다.

### 실행

```bash
uv run evalvault compare <RUN_A> <RUN_B> \
  --profile dev \
  --db data/db/evalvault.db
```

### 기대 결과

- 메트릭별 변화량과 방향(개선/악화)이 요약된다.

### 실무 팁

- 비교는 반드시 동일 조건에서 해야 한다(데이터셋/프로필/메트릭).
- 조건이 바뀌면 “개선”이 아니라 “다른 실험”이다.

---

## 워크플로 4: 통계 기반 비교(유의미한 변화인지)

### 목표

- 변화가 ‘우연’인지 ‘의미’인지 판단한다(표본이 있을 때만).

### 실행

```bash
uv run evalvault analyze-compare <RUN_A> <RUN_B> \
  --profile dev \
  --db data/db/evalvault.db
```

### 기대 결과

- 평균 차이/효과 크기/유의확률 같은 통계 요약이 포함된다.

---

## 워크플로 5: Web UI로 조회(운영/공유)

### 목표

- CLI로 만든 실행 결과를 UI에서 탐색/공유한다.

### 실행

```bash
# API
uv run evalvault serve-api --reload

# UI
cd frontend && npm install && npm run dev
```

### 기대 결과

- Run list에서 `run_id`가 보인다.
- Run details에서 리포트/대시보드를 열 수 있다.

### 실패 시 조치

- 가장 먼저 DB 경로가 동일한지 확인한다.

---

## 워크플로 6: 회귀 게이트(자동 품질 차단)

### 목표

- PR/배포 단계에서 기준 이하 회귀를 자동으로 실패 처리한다.

### 핵심 규칙

- baseline(기준 run)과 current(현재 run)를 비교한다.
- 허용 회귀율(예: 5%)을 넘으면 실패한다.

### 실행(로컬 개념 검증)

프로젝트마다 게이트 실행 방법이 다를 수 있지만, 원리는 동일하다.
“기준 run_id”와 “현재 run_id”를 정해 비교하고, 결과를 사람이 읽거나 CI 포맷으로 출력한다.

---

## 공통 트러블슈팅(가장 자주 막히는 지점)

### 1) 점수가 갑자기 요동친다

- 데이터셋이 바뀌었거나(버전/샘플), 프로필이 바뀌었거나(모델/임베딩), 리트리버 옵션이 바뀐 경우가 많다.

### 2) 분석 결과는 있는데 근거가 없다

- 아티팩트가 생성되지 않았거나, index.json이 없으면 추적이 어려워진다.
- 분석을 `--auto-analyze`로 돌렸는지, artifacts 경로가 쓰기 가능했는지 확인한다.

### 3) UI에서 실행이 안 보인다

- CLI와 API가 같은 DB를 바라보는지 확인한다.

---

## 체크리스트

- [ ] 비교 실험은 동일 조건(데이터셋/프로필/메트릭)인가?
- [ ] 분석 산출물과 근거(artifacts/index.json)가 함께 생성되었는가?
- [ ] `run_id`를 팀이 공유/추적 가능한 방식으로 기록하고 있는가?

## 자기 점검 질문

1) 두 run을 비교할 때 “같아야 하는 조건 3가지”는 무엇인가?
2) 분석에서 `index.json`이 하는 역할은 무엇인가?
3) 회귀 게이트가 실패하면 어떤 정보를 남겨야 디버깅이 빠른가?

---

## Part 2. 운영 플레이북(상세)

이 섹션은 “팀이 실제로 굴리는 방식”을 기준으로 작성한다.
명령어는 CLI 코드(Typer)에서 확인 가능한 옵션/기본값을 우선한다.

### 7. 워크플로 설계 원칙(실험 단위/조건 고정/산출물)

#### 7.1 실험의 최소 단위는 `run_id`

- 실행 결과/분석/비교/아티팩트/트레이스는 `run_id`로 조인된다.
- 근거(도메인 엔티티): `src/evalvault/domain/entities/result.py#EvaluationRun.run_id`.

실무 규칙(권장):

- Slack/이슈/PR 코멘트에 run_id를 "텍스트"로 남긴다.
- 단, UI/리포트 공유가 목적이면 run_id만 남기지 말고 "산출물 경로"도 같이 남긴다.
  예: `reports/analysis/analysis_<RUN_ID>.md`, `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`

#### 7.2 비교 가능한 실험의 조건(최소 4개)

두 run을 “개선/회귀”로 비교하려면 최소한 아래가 같아야 한다.

1) 데이터셋(이름/버전/표본)
2) 메트릭 집합
3) thresholds(최종 run.thresholds)
4) 모델/임베딩/프로필

이 중 하나라도 다르면 “개선”이 아니라 “다른 실험”이다.

#### 7.3 산출물은 두 층이다: 사람용 vs 근거용

- 사람용: 보고서/요약(의사결정)
- 근거용: 아티팩트(재현/디버깅)

근거:

- 아티팩트 index 작성: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`.

---

### 8. 환경 준비(설치/.env/프로필/DB)

이 섹션은 “워크플로가 안 도는 이유”의 70%를 제거한다.

#### 8.1 설치(개발 환경)

권장(레포 가이드):

```bash
uv sync --extra dev
```

근거: `AGENTS.md`.

#### 8.2 .env / Settings: DB 설정과 프로필이 워크플로의 뿌리다

Settings는 `.env`를 읽고, profile을 적용하며, prod에서는 필수 설정을 강제한다.

- 근거: `src/evalvault/config/settings.py`.

실무에서 핵심인 필드:

- `EVALVAULT_PROFILE` (profile 적용)
- `POSTGRES_*` / `POSTGRES_CONNECTION_STRING` (기본 DB: Postgres + pgvector)

#### 8.3 DB 설정을 고정하는 이유

DB는 "과거 run"을 재사용하기 위한 저장소다.
DB 설정이 달라지면:

- history가 달라지고
- UI에서 보이는 run이 달라지고
- compare/analyze가 다른 데이터를 본다

따라서 팀은 최소한 개발 환경에서 DB 설정을 고정해야 한다.

---

### 9. 평가 실행(run) 심화: preset, run-simple/run-full, auto-analyze

#### 9.1 run 명령의 핵심 옵션(워크플로 관점)

`evalvault run`은 옵션이 많다.
하지만 워크플로 관점에서 핵심은 아래다.

- 데이터셋 경로(첫 번째 인자)
- 메트릭(`--metrics`)
- 프로필(`--profile` 또는 Settings profile)
- DB(Postgres 연결 설정)
- 자동 분석(`--auto-analyze`)
- preset(`--preset` 또는 평가 preset)

근거:

- preset/alias 존재: `src/evalvault/adapters/inbound/cli/commands/run.py` (run-simple/run-full, --preset).

#### 9.2 alias: run-simple / run-full

CLI에는 alias가 있다.

- `evalvault run-simple` (simple 모드 별칭)
- `evalvault run-full` (full 모드 별칭)

근거: `src/evalvault/adapters/inbound/cli/commands/run.py`에 name="run-simple", name="run-full".

실무 팁:

- 팀 템플릿 문서에는 alias를 쓰면 설명이 짧아진다.
- 하지만 “무슨 옵션이 적용되는지”가 불명확해질 수 있으므로, PR/회귀에서는 `evalvault run` + 명시 옵션이 안전하다.

#### 9.3 auto-analyze가 생성하는 산출물

auto-analyze는 평가 직후 분석 파이프라인을 돌리고, 보고서/아티팩트를 남긴다.

산출물 기본 형태:

- `reports/analysis/analysis_<RUN_ID>.json`
- `reports/analysis/analysis_<RUN_ID>.md`
- `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`

근거(자동 분석 파일/아티팩트 생성): `src/evalvault/adapters/inbound/cli/commands/run.py`, `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`.

---

### 10. 이력 조회/내보내기(history/export)

#### 10.1 history: DB에서 run 목록을 보는 가장 빠른 방법

```bash
uv run evalvault history
uv run evalvault history --limit 20
uv run evalvault history --dataset <DATASET_NAME>
uv run evalvault history --model <MODEL_NAME>
uv run evalvault history --mode simple
```

근거: `src/evalvault/adapters/inbound/cli/commands/history.py#history`.

#### 10.2 export: run 상세를 JSON으로 내보내기

```bash
uv run evalvault export <RUN_ID> -o reports/run_<RUN_ID>.json
```

SQLite를 쓰는 경우 `--db` 또는 `DB_BACKEND=sqlite` + `EVALVAULT_DB_PATH`로 경로를 고정한다.

근거: `src/evalvault/adapters/inbound/cli/commands/history.py#export_cmd`.

export가 포함하는 데이터(코드 기준):

- run 요약(to_summary_dict)
- test_case 결과 목록(메트릭별 score/threshold/passed)

---

### 11. 분석(analyze) 심화: nlp/causal/playbook/dashboard

`evalvault analyze`는 "DB에 저장된 run"을 읽어 통계/NLP/인과 분석 등을 수행한다.

근거: `src/evalvault/adapters/inbound/cli/commands/analyze.py#analyze`.

#### 11.1 핵심 옵션(워크플로 관점)

- `--nlp`: LLM/임베딩을 활용한 NLP 분석(환경에 따라 비용/시간 증가)
- `--causal`: 인과 분석(데이터 규모가 작으면 의미가 약할 수 있음)
- `--playbook`: 개선 가이드 생성
- `--dashboard`: 시각화 대시보드 생성
- `--output` / `--report`: 파일로 저장(미지정 시 콘솔 중심)

주의:

- analyze는 기본적으로 "자동으로 보고서를 파일로 쓰지 않는다".
  보고서를 파일로 남기고 싶으면 `--report`를 지정한다.

#### 11.2 재분석 워크플로(파일 산출물까지 남기기)

```bash
uv run evalvault analyze <RUN_ID> \
  --nlp --causal \
  --output reports/analysis/custom_<RUN_ID>.json \
  --report reports/analysis/custom_<RUN_ID>.md
```

이 패턴이 유용한 이유:

- auto-analyze 결과를 "그대로 덮어쓰기"가 아니라, 분석 조건을 바꿔 비교할 수 있다.

---

### 12. 비교(compare) 심화: 파일/아티팩트/표 출력

`evalvault compare`는 두 run의 차이를 요약하고, 비교 보고서/아티팩트를 저장할 수 있다.

근거: `src/evalvault/adapters/inbound/cli/commands/compare.py#compare`.

#### 12.1 기본 실행(파일 + 아티팩트 생성)

compare는 기본적으로 output/report 경로를 resolve해 파일을 만든다.

- prefix: `comparison_{RUN_A[:8]}_{RUN_B[:8]}`
- base_dir 기본값: `reports/comparison`

근거: `src/evalvault/adapters/inbound/cli/commands/compare.py`.

```bash
uv run evalvault compare <RUN_A> <RUN_B> --db data/db/evalvault.db
```

기대 산출물(경로 형태):

- `reports/comparison/comparison_<A8>_<B8>.json`
- `reports/comparison/comparison_<A8>_<B8>.md`
- `reports/comparison/artifacts/comparison_<A8>_<B8>/index.json`

주의:

- 실제 파일명은 run_id의 앞 8자리 기준으로 잘린다.

#### 12.2 표만 보고 싶을 때

```bash
uv run evalvault compare <RUN_A> <RUN_B> --db data/db/evalvault.db --format table
```

---

### 13. 통계 비교(analyze-compare) 심화: comparison_{A8}_{B8}

`evalvault analyze-compare`는 통계 비교 + 비교 보고서/아티팩트 생성을 한 번에 수행한다.

근거: `src/evalvault/adapters/inbound/cli/commands/analyze.py#analyze_compare`.

```bash
uv run evalvault analyze-compare <RUN_A> <RUN_B> --db data/db/evalvault.db
```

기대 산출물(경로 형태):

- `reports/comparison/comparison_<A8>_<B8>.json`
- `reports/comparison/comparison_<A8>_<B8>.md`
- `reports/comparison/artifacts/comparison_<A8>_<B8>/index.json`

---

### 14. 쿼리 기반 파이프라인(pipeline analyze)

이 워크플로는 "자연어 쿼리"로 분석 의도를 추정하고 DAG 파이프라인을 실행한다.

근거: `src/evalvault/adapters/inbound/cli/commands/pipeline.py`.

#### 14.1 실행

```bash
uv run evalvault pipeline analyze "낮은 메트릭 원인 분석" --db data/db/evalvault.db --run <RUN_ID>
```

옵션:

- `--run/-r`: 특정 run_id를 대상으로 분석
- `--output/-o`: 파이프라인 결과를 JSON으로 저장

#### 14.1.1 예: 데이터셋 특성 분석(회귀/편차의 원인을 데이터 관점에서 좁히기)

데이터셋 특성 분석은 질문/답변/정답/컨텍스트에서 특성(feature)을 추출하고,
메트릭과의 상관/중요도/엔티티 그래프를 만든다.

근거(모듈): `src/evalvault/adapters/outbound/analysis/dataset_feature_analyzer_module.py#DatasetFeatureAnalyzerModule`.

실행(의도 추정은 자연어 쿼리로 유도):

```bash
uv run evalvault pipeline analyze "데이터셋 특성 분석" --db data/db/evalvault.db --run <RUN_ID>
```

파이프라인 템플릿(의도/노드):

- 의도: `AnalysisIntent.ANALYZE_DATASET_FEATURES`
  - 근거: `src/evalvault/domain/entities/analysis_pipeline.py#AnalysisIntent`
- 노드: `load_data` -> `dataset_feature_analysis`
  - 근거: `src/evalvault/domain/services/pipeline_template_registry.py#_create_analyze_dataset_features_template`

저장(중요):

`pipeline analyze`는 파이프라인 히스토리(pipeline_results)와 별개로,
데이터셋 특성 분석 결과를 analysis_results에도 저장하려고 시도한다(best-effort).

- 근거: `src/evalvault/adapters/inbound/cli/commands/pipeline.py` (`save_dataset_feature_analysis` 호출)
- 근거(저장 구현): `src/evalvault/adapters/outbound/storage/sqlite_adapter.py#save_dataset_feature_analysis`, `src/evalvault/adapters/outbound/storage/postgres_adapter.py#save_dataset_feature_analysis`

파라미터(기본값/의미, 현재 CLI 플래그로는 노출되지 않음):

- `min_samples`(default=5): 상관/중요도 계산 최소 샘플 수
- `max_graph_nodes`(default=50): 엔티티 그래프 노드 상한
- `max_graph_edges`(default=200): 엔티티 그래프 엣지 상한
- `include_vectors`(default=false): 샘플별 feature vector 포함

근거: `src/evalvault/adapters/outbound/analysis/dataset_feature_analyzer_module.py`.

팁(API를 쓰는 경우):

FastAPI 파이프라인 엔드포인트는 `params`를 받아 `additional_params`로 전달한다.
다만 “모든 분석 모듈이 이 값을 읽는 것은 아니다”.

- API가 `params`를 수용: `frontend/src/services/api.ts#runAnalysis`, `src/evalvault/adapters/inbound/api/routers/pipeline.py` (`AnalyzeRequest.params`)
- 전달 경로는 `__context__.additional_params`: `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator._prepare_inputs`

현재 `dataset_feature_analyzer`는 `__context__.additional_params`를 읽지 않고, 오직 노드의 `params`만 본다.
즉, 위 파라미터를 런타임에서 바꾸려면 (1) 템플릿/노드 params를 주입하거나 (2) 모듈이 additional_params를 읽도록 코드가 연결되어야 한다.

- 근거(모듈이 읽는 값): `src/evalvault/adapters/outbound/analysis/dataset_feature_analyzer_module.py#DatasetFeatureAnalyzerModule.execute`
- 근거(노드 params 전달): `src/evalvault/domain/services/pipeline_orchestrator.py#PipelineOrchestrator._execute_node`

#### 14.2 intents/templates: 무엇이 가능한지 먼저 보기

```bash
uv run evalvault pipeline intents
uv run evalvault pipeline templates
```

근거: `src/evalvault/adapters/inbound/cli/commands/pipeline.py`.

---

### 15. 품질 게이트(gate) vs 회귀 게이트(regress/ci-gate)

이 섹션은 CI/CD에서 가장 자주 쓰는 흐름이다.

#### 15.1 gate: threshold 통과 + (옵션) baseline 대비 회귀 감지

```bash
uv run evalvault gate <RUN_ID> --db data/db/evalvault.db
uv run evalvault gate <RUN_ID> --db data/db/evalvault.db --threshold faithfulness:0.8
uv run evalvault gate <RUN_ID> --db data/db/evalvault.db --baseline <BASELINE_RUN_ID> --fail-on-regression 0.05
```

근거: `src/evalvault/adapters/inbound/cli/commands/gate.py`.

출력 포맷:

- table
- json
- github-actions

Exit code(의미, 코드 흐름 기준):

- threshold 실패: Exit(1)
- regression 감지: Exit(2)

#### 15.2 regress: 통계 기반 회귀 게이트

```bash
uv run evalvault regress <RUN_ID> --baseline <BASELINE_RUN_ID> --db data/db/evalvault.db
```

근거: `src/evalvault/adapters/inbound/cli/commands/regress.py#regress`.

출력 포맷:

- table
- json
- github-actions

Exit code(요약):

- regression 감지: Exit(2)

#### 15.3 regress-baseline: baseline을 키로 저장/조회

```bash
uv run evalvault regress-baseline set --db data/db/evalvault.db --key default --run-id <RUN_ID>
uv run evalvault regress-baseline get --db data/db/evalvault.db --key default
```

근거: `src/evalvault/adapters/inbound/cli/commands/regress.py#regress_baseline`.

#### 15.4 ci-gate: CI 전용 리포트 포맷

`ci-gate`는 format 옵션이 github/gitlab/json/pr-comment를 지원한다.

- 근거: `src/evalvault/adapters/inbound/cli/commands/regress.py#ci_gate`.

---

### 16. Web UI 운영 루프(serve-api + frontend)

핵심 규칙:

- CLI와 API가 같은 DB를 봐야 한다.

실행:

```bash
uv run evalvault serve-api --reload
cd frontend && npm install && npm run dev
```

근거: `README.md`, `AGENTS.md`.

자주 나는 문제:

- UI에서 run이 안 보임 -> DB 경로 불일치
- CORS 문제 -> settings.cors_origins 확인

근거: `src/evalvault/config/settings.py`.

---

### 17. 아티팩트 무결성(lint)과 자동화

아티팩트는 "있다"고 끝이 아니라 "깨지지 않았다"가 중요하다.
CI에서 이걸 자동화하면 디버깅 시간이 크게 줄어든다.

#### 17.1 artifacts lint

```bash
uv run evalvault artifacts lint reports/analysis/artifacts/analysis_<RUN_ID>
uv run evalvault artifacts lint reports/analysis/artifacts/analysis_<RUN_ID> --strict
```

근거:

- CLI: `src/evalvault/adapters/inbound/cli/commands/artifacts.py`
- 서비스: `src/evalvault/domain/services/artifact_lint_service.py`

---

### 18. 흔한 실패 모드별 디버깅 트리

이 절은 “현장에서 바로 쓸 수 있는 순서”만 담는다.

#### 18.1 LLM 어댑터 초기화 실패

증상:

- run/compare/analyze-compare에서 LLM adapter 초기화 경고 또는 실패

진단 순서:

1) Settings profile 확인
2) provider별 필수 설정 확인(OpenAI key, Ollama base url, vLLM base url 등)
3) embeddings가 필요한 메트릭인지 확인

근거:

- Settings: `src/evalvault/config/settings.py`
- LLM 선택: `src/evalvault/adapters/outbound/llm/__init__.py#get_llm_adapter`

#### 18.2 DB 설정이 누락됐다

증상:

- 여러 명령에서 "DB 경로가 설정되지 않았습니다" 오류

진단:

- Postgres 설정(`POSTGRES_*` 또는 `POSTGRES_CONNECTION_STRING`)을 확인
- SQLite를 쓰는 경우 `--db` 옵션을 명시하거나 `.env`의 `EVALVAULT_DB_PATH`를 설정

근거:

- 각 커맨드에서 Settings().evalvault_db_path를 fallback으로 사용
  예: `src/evalvault/adapters/inbound/cli/commands/history.py`, `analyze.py`.

#### 18.3 비교 결과가 이상하다(개선/회귀가 뒤집힌 것처럼 보임)

진단 순서:

1) metrics가 같은지
2) thresholds가 같은지(run.thresholds)
3) 데이터셋 표본이 같은지(전처리로 dropped 사례는 없는지)

---

### 19. 체크리스트/자가 점검(확장)

#### 19.1 실행 전 체크리스트

- [ ] DB 설정이 고정돼 있는가(CLI/API/UI 동일)?
- [ ] 프로필이 기대와 같은가(모델/임베딩)?
- [ ] 선택한 메트릭이 데이터셋 입력을 충족하는가(02장)?

#### 19.2 실행 후 체크리스트

- [ ] run_id를 기록했는가?
- [ ] 보고서(사람용)와 아티팩트(근거용)가 함께 생성됐는가?
- [ ] 비교/회귀에서 조건이 동일했는가?

#### 19.3 CI 게이트 체크리스트

- [ ] gate/regress가 실패할 때, 어떤 출력을 남길지 결정했는가(json/github-actions/pr-comment)
- [ ] baseline 관리(regress-baseline)를 자동화할 계획이 있는가?

---

## Part 3. 워크플로 레시피(책 수준, 실무 중심)

Part 1/2는 “명령을 어떻게 이어 붙이는지”에 초점을 맞췄다.
Part 3는 “팀이 품질 루프를 지속 가능하게 굴리는 방법”을 문서화한다.

이 장의 핵심 규칙은 하나다.

- 워크플로의 진실은 CLI 구현이며, 문서의 각 주장에는 근거 파일 경로를 붙인다.

---

### 20. 산출물 규약: 보고서(사람용) vs 아티팩트(근거용)

EvalVault의 워크플로는 기본적으로 아래 2종 산출물로 “의사결정”과 “재현/디버깅”을 분리한다.

- 보고서(사람용): `.md` (또는 일부 커맨드는 `.html`)
- 아티팩트(근거용): `artifacts/<prefix>/` 아래 per-node JSON + `index.json`

#### 20.1 파일명 prefix 규칙

커맨드별 prefix는 코드로 고정돼 있어, 파일명만 봐도 무엇인지 추적 가능해야 한다.

- 자동 분석: `analysis_<RUN_ID>`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/run.py` (auto-analyze에서 `analysis_prefix = f"analysis_{result.run_id}"`).
- 비교(Compare): `comparison_<RUN_A[:8]>_<RUN_B[:8]>`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/compare.py`.
- 프롬프트 추천: `prompt_suggestions_<RUN_ID>`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/prompts.py`.

#### 20.2 기본 출력 디렉터리 규칙

`resolve_output_paths()`의 기본 base_dir는 `reports/analysis`이며, 비교 같은 커맨드는 base_dir를 따로 지정한다.

- 기본(analysis 계열): `reports/analysis/<prefix>.json`, `reports/analysis/<prefix>.md`
  - 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#resolve_output_paths`.
- 비교(compare): base_dir 기본값 `reports/comparison`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/compare.py`.

#### 20.3 아티팩트 디렉터리 규칙

아티팩트는 항상 `.../artifacts/<prefix>/`로 생성된다.

- 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#resolve_artifact_dir`.

#### 20.4 아티팩트 파일 구성(노드 단위 JSON)

파이프라인 기반 커맨드(자동 분석/비교/프롬프트 추천 등)는 per-node JSON을 생성한다.

- `<artifacts_dir>/<node_id_sanitized>.json`: 노드의 status/duration/error/output
- `<artifacts_dir>/final_output.json`: pipeline final_output 스냅샷
- `<artifacts_dir>/index.json`: 인덱스(노드 목록 + 경로)

근거:

- `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`

실무 규칙(권장):

- “원인”을 찾을 때는 보고서보다 먼저 `index.json → 관련 node JSON` 순으로 들어가라.
- 팀 커뮤니케이션에서는 “run_id + 보고서 경로 + index.json 경로”를 함께 남겨라.

---

### 21. run 실행 전략: 모드/프리셋/메트릭을 어떻게 고를 것인가

`evalvault run`은 기능이 넓다. 실무에서는 “모드 선택”이 워크플로 품질을 결정한다.

#### 21.1 3가지 run mode

- `--mode simple`: 간편 실행(메트릭/트래커 일부 고정)
- `--mode full`: 전체 옵션 노출
- `--mode multiturn`: 멀티턴 전용(멀티턴 메트릭)

근거:

- 모드 정의: `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#RUN_MODE_PRESETS`
- 모드 파싱/검증: `src/evalvault/adapters/inbound/cli/commands/run.py` (`RUN_MODE_PRESETS.get(run_mode_value)` 실패 시 Exit(2)).

#### 21.2 simple 모드의 “잠금(lock)” 특성

simple 모드는 빠른 스모크를 위해 일부 옵션을 강제한다.

- 메트릭: `faithfulness,answer_relevancy` 강제
- tracker: `phoenix` 강제
- Domain Memory 비활성화
- prompt manifest/metadata 비활성화

근거:

- presets: `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#RUN_MODE_PRESETS`
- 강제/경고 UX: `src/evalvault/adapters/inbound/cli/commands/run.py` (simple 모드에서 metrics/tracker/prompt 옵션 경고).

#### 21.3 preset vs --metrics 우선순위

`--preset`이 지정되어도, `--metrics`를 명시하면 metrics가 override된다.

- 근거: `src/evalvault/adapters/inbound/cli/commands/run.py` (`metrics_override = _option_was_provided(ctx, "metrics")`).

실무 팁:

- 빠른 반복: `--preset quick`
- 팀/CI: `--metrics`를 명시해 “무슨 평가를 했는지”를 고정(문서화)

---

### 22. run에서 컨텍스트를 채우는 워크플로(리트리버)

데이터셋에 `contexts`가 비어 있거나 불완전할 때, `--retriever`로 자동 채울 수 있다.

#### 22.1 핵심 옵션

- `--retriever/-r`: `bm25|dense|hybrid|graphrag`
- `--retriever-docs`: 문서 소스(.json/.jsonl/.txt 또는 PDF 디렉터리)
- `--retriever-top-k`: 기본 5
- `--kg/-k`: GraphRAG용 knowledge graph JSON

근거:

- 옵션 정의: `src/evalvault/adapters/inbound/cli/commands/run.py`.

#### 22.2 PDF 디렉터리 입력(청킹/OCR)

문서가 PDF 디렉터리로 들어오면 청킹 파라미터와 OCR fallback이 동작할 수 있다.

- `--pdf-chunk-size` (default 1200)
- `--pdf-chunk-overlap` (default 120)
- `--pdf-max-chunks` (optional)
- `--pdf-ocr/--no-pdf-ocr`
- `--pdf-ocr-backend` (default paddleocr)
- `--pdf-ocr-mode` (text|structure)
- `--pdf-ocr-lang` (default korean)
- `--pdf-ocr-device` (auto|cpu|gpu)
- `--pdf-ocr-min-chars` (default 200)

근거:

- 옵션 정의: `src/evalvault/adapters/inbound/cli/commands/run.py`.

---

### 23. run에서 프롬프트/스냅샷을 남기는 워크플로

실험에서 “프롬프트 변경”은 가장 흔한 변수다.
EvalVault는 run 시점에 프롬프트를 스냅샷으로 남겨 비교 가능하게 만든다(단, DB 저장이 필요).

#### 23.1 시스템 프롬프트 주입

- `--system-prompt`: inline
- `--system-prompt-file`: 파일 로딩
- 둘은 동시에 사용 불가

근거:

- 상호 배제 검증: `src/evalvault/adapters/inbound/cli/commands/run.py`.

#### 23.2 Ragas 프롬프트 오버라이드

- `--ragas-prompts <yaml>`: 메트릭별 프롬프트를 YAML로 덮어씀

근거:

- 로딩/검증: `src/evalvault/adapters/inbound/cli/commands/run.py` (`load_ragas_prompt_overrides`).

#### 23.3 프롬프트 스냅샷은 DB 저장 시에만 기록

프롬프트 스냅샷을 남겨 “prompts show/diff/suggest”를 쓰려면 `--db`가 필요하다.

근거:

- 경고 UX: `src/evalvault/adapters/inbound/cli/commands/run.py` (prompt_inputs 존재 + db_path 없음 경고)
- prompts 서브커맨드의 DB 강제: `src/evalvault/adapters/inbound/cli/commands/prompts.py#_require_db_path`.

---

### 24. stage 이벤트 워크플로(관찰가능성: 외부/내부 파이프라인 로그)

stage는 “RAG 파이프라인 내부 단계”를 이벤트로 저장하고, 요약/메트릭/가이드를 생성한다.
워크플로는 크게 2가지다.

- A) 실행 중 생성: `evalvault run --stage-events <PATH>` 또는 `--stage-store`
- B) 외부 시스템에서 생성한 JSON/JSONL을 ingest

#### 24.1 stage ingest

- 입력 포맷: `.json` 또는 `.jsonl`만 지원
- `--skip-invalid`로 유효성 실패를 건너뛰고 집계
- `--failed-output`으로 실패 샘플을 JSONL로 저장

근거:

- 포맷/옵션/검증: `src/evalvault/adapters/inbound/cli/commands/stage.py#ingest`.

#### 24.2 stage list/summary

- `evalvault stage list <RUN_ID> [--stage-type <TYPE>] [--limit N]`
- `evalvault stage summary <RUN_ID>`

근거:

- `src/evalvault/adapters/inbound/cli/commands/stage.py#list_events`, `src/evalvault/adapters/inbound/cli/commands/stage.py#summary`.

#### 24.3 stage compute-metrics/report

stage 이벤트에서 메트릭을 계산하고(선택적으로 threshold JSON 적용), 저장하거나 리포트를 만든다.

- `evalvault stage compute-metrics <RUN_ID> [--relevance-json ...] [--thresholds-json ...] [--thresholds-profile ...]`
- `evalvault stage report <RUN_ID> ... [--playbook ...] [--save-metrics/--no-save-metrics]`

근거:

- `src/evalvault/adapters/inbound/cli/commands/stage.py#compute_metrics`, `src/evalvault/adapters/inbound/cli/commands/stage.py#report`.

---

### 25. analyze 워크플로(콘솔 분석 → 파일 저장 → 대시보드)

`evalvault analyze`는 DB에 저장된 run을 읽어 통계/NLP/인과/플레이북 등 추가 분석을 수행한다.

#### 25.1 analyze의 기본 성격: 콘솔 출력 중심

`--output`/`--report`는 옵션이며, 기본은 콘솔에 요약을 출력한다.

근거:

- `src/evalvault/adapters/inbound/cli/commands/analyze.py` (output/report 기본 None).

#### 25.2 playbook 분석은 stage metrics와 연결될 수 있음

`--playbook`을 켜면 DB의 stage metrics를 조회하고, 없으면 안내 메시지를 출력한다.

근거:

- `src/evalvault/adapters/inbound/cli/commands/analyze.py` (`storage.list_stage_metrics(run_id)` 확인).

#### 25.3 dashboard 출력 경로 규칙

대시보드는 기본 `reports/dashboard/dashboard_<RUN_ID[:8]>.<format>`에 저장한다.

근거:

- `src/evalvault/adapters/inbound/cli/commands/analyze.py` (`output_dir = Path("reports/dashboard")`).

---

### 26. pipeline 워크플로(자연어 질의 기반 분석)

`evalvault pipeline analyze`는 자연어 query를 intent로 분류하고 DAG 파이프라인을 실행한다.

#### 26.1 intents/templates로 “지원 범위”를 먼저 확인

- `evalvault pipeline intents`: intent 목록
- `evalvault pipeline templates`: intent별 DAG 노드 구조

근거:

- `src/evalvault/adapters/inbound/cli/commands/pipeline.py`.

#### 26.2 pipeline analyze의 결과 저장

- `--output` 지정 시 JSON 파일 저장

근거:

- `src/evalvault/adapters/inbound/cli/commands/pipeline.py` (`serialize_pipeline_result` + json.dump).

---

### 27. compare/analyze-compare/regress의 역할 분리

이 3개는 모두 “두 run 비교”처럼 보이지만, 워크플로에서 역할이 다르다.

#### 27.1 compare: 비교 요약 + (파이프라인 기반) 비교 보고서/아티팩트

- 기본 출력 디렉터리: `reports/comparison`
- 아티팩트: `reports/comparison/artifacts/comparison_<A8>_<B8>/index.json`
- 리포트가 일부 누락되면 degraded로 간주되고 Exit(2)

근거:

- 파일/아티팩트 생성: `src/evalvault/adapters/inbound/cli/commands/compare.py`
- degraded exit: `src/evalvault/adapters/inbound/cli/commands/compare.py` (`if outcome.is_degraded: raise typer.Exit(2)`).

#### 27.2 analyze-compare: 통계 검정 + 파이프라인 기반 비교 보고서/아티팩트

`evalvault analyze-compare`는 통계 검정과 보고서 생성이 한 커맨드로 묶인다.

근거:

- `src/evalvault/adapters/inbound/cli/commands/analyze.py#analyze_compare`.

#### 27.3 regress: 통계 기반 회귀 감지(게이트 목적)

`evalvault regress`는 “회귀 감지” 목적의 gate이며, 회귀 감지 시 Exit(2)로 실패한다.

근거:

- `src/evalvault/adapters/inbound/cli/commands/regress.py` (`if report.regression_detected: raise typer.Exit(2)`).

---

### 28. gate/regress/ci-gate: CI 통합을 위한 exit code/출력 규약

CI에서 중요한 건 “사람이 읽는 출력”이 아니라 “머신이 해석 가능한 신호”다.

#### 28.1 gate exit code

- Exit(1): threshold 실패
- Exit(2): regression 감지(baseline 대비)
- Exit(3): run/baseline not found

근거:

- `src/evalvault/adapters/inbound/cli/commands/gate.py`.

#### 28.2 regress exit code

- Exit(2): regression 감지
- 그 외 오류는 Exit(1) 또는 Exit(3) (예외 타입에 따라 분기)

근거:

- `src/evalvault/adapters/inbound/cli/commands/regress.py`.

#### 28.3 ci-gate: 포맷 전용(대시/PR 코멘트)

`evalvault ci-gate`는 출력 포맷을 `github|gitlab|json|pr-comment`로 제공한다.

근거:

- `src/evalvault/adapters/inbound/cli/commands/regress.py#ci_gate`.

#### 28.4 regress-baseline: baseline을 key로 관리

baseline을 외부 CI 변수로만 관리하면 drift가 생기기 쉽다.
EvalVault는 baseline을 DB에 key로 저장/조회하는 커맨드를 제공한다.

- `evalvault regress-baseline set --key <KEY> --run-id <RUN_ID> [--dataset ...] [--branch ...] [--commit ...]`
- `evalvault regress-baseline get --key <KEY>`

근거:

- `src/evalvault/adapters/inbound/cli/commands/regress.py#regress_baseline`.

---

### 29. artifacts lint 워크플로(무결성 자동화)

아티팩트는 “있다”가 끝이 아니라 “깨지지 않았다”가 중요하다.
`evalvault artifacts lint`는 `index.json`을 기준으로 파일 누락/구조 오류를 점검한다.

#### 29.1 기본 실행

```bash
uv run evalvault artifacts lint reports/analysis/artifacts/analysis_<RUN_ID>
uv run evalvault artifacts lint reports/analysis/artifacts/analysis_<RUN_ID> --strict
```

근거:

- CLI: `src/evalvault/adapters/inbound/cli/commands/artifacts.py`.

#### 29.2 실패 처리

- lint 결과 status가 error면 Exit(1)

근거:

- `src/evalvault/adapters/inbound/cli/commands/artifacts.py` (`if summary.status == "error": raise typer.Exit(1)`).

---

### 30. ops snapshot 워크플로(재현성: run + 설정 스냅샷)

비교/회귀가 느려지는 가장 큰 이유는 “실험 조건을 다시 못 맞추는 것”이다.
`evalvault ops snapshot`은 run을 기준으로 운영 스냅샷 JSON을 남긴다.

```bash
uv run evalvault ops snapshot --run-id <RUN_ID> --db data/db/evalvault.db \
  --output reports/ops_snapshot_<RUN_ID>.json \
  --include-model-config --include-env \
  --redact OPENAI_API_KEY --redact LANGFUSE_SECRET_KEY
```

근거:

- `src/evalvault/adapters/inbound/cli/commands/ops.py`.

---

### 31. 프롬프트 개선 루프(스냅샷 → 후보 생성 → 홀드아웃 평가)

EvalVault는 “프롬프트 후보를 생성하고, 홀드아웃에서 점수로 랭킹”하는 워크플로를 제공한다.

#### 31.1 prompts show/diff

- `evalvault prompts show <RUN_ID> --db ...`: run에 연결된 prompt set 확인
- `evalvault prompts diff <RUN_A> <RUN_B> --db ...`: role별 checksum diff + (옵션) unified diff 출력

근거:

- `src/evalvault/adapters/inbound/cli/commands/prompts.py`.

#### 31.2 prompts suggest의 산출물 규약

prefix는 `prompt_suggestions_<RUN_ID>`이며, 기본 base_dir는 `reports/analysis`다.

- `reports/analysis/prompt_suggestions_<RUN_ID>.json`
- `reports/analysis/prompt_suggestions_<RUN_ID>.md`
- `reports/analysis/artifacts/prompt_suggestions_<RUN_ID>/index.json`

근거:

- prefix/경로: `src/evalvault/adapters/inbound/cli/commands/prompts.py`, `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`.

#### 31.3 홀드아웃 분리 파라미터(재현성)

- `--holdout-ratio` (default 0.2)
- `--seed` (optional)

근거:

- `src/evalvault/adapters/inbound/cli/commands/prompts.py`.

---

### 32. init/config/metrics/serve-api: 팀 온보딩 워크플로

#### 32.1 init로 시작 파일 생성

`evalvault init`은 `.env`, 샘플 데이터셋, 템플릿을 생성한다(옵션으로 스킵 가능).

근거:

- `src/evalvault/adapters/inbound/cli/commands/init.py`.

#### 32.2 config/metrics로 “현재 상태”를 확인

- `evalvault metrics`: 사용 가능한 메트릭/ground truth 요구 여부
- `evalvault config`: 현재 profile/provider/model/트래킹 설정 표시

근거:

- `src/evalvault/adapters/inbound/cli/commands/config.py`.

#### 32.3 serve-api 실행 규약

- 기본 host: 127.0.0.1
- 기본 port: 8000
- `--reload` 시 uvicorn factory 모드

근거:

- `src/evalvault/adapters/inbound/cli/commands/api.py`.

---

### 33. 트러블슈팅 트리(워크플로 관점)

이 섹션은 “코드 레벨 진단”이 아니라, 워크플로 상에서 가장 빠른 분기만 정리한다.

#### 33.1 DB 경로 관련

증상:

- history/analyze/compare/gate/regress 등이 “DB 경로가 설정되지 않았다”로 실패

원인 후보:

- Postgres 설정 누락
- SQLite를 쓰는 경우 `--db` 미지정 + `.env`에 `EVALVAULT_DB_PATH` 미설정

근거:

- 예: analyze/history는 `db_path or Settings().evalvault_db_path`를 사용
  - `src/evalvault/adapters/inbound/cli/commands/analyze.py`
  - `src/evalvault/adapters/inbound/cli/commands/history.py`

#### 33.2 gate threshold 입력 형식 오류

증상:

- `--threshold`가 `metric:value`가 아니라서 실패

근거:

- `src/evalvault/adapters/inbound/cli/commands/gate.py`.

#### 33.3 compare가 Exit(2)로 종료

증상:

- compare 결과가 저장되긴 했는데 프로세스가 2로 종료

의미:

- degraded 상태(리포트 일부 누락 가능성)

근거:

- `src/evalvault/adapters/inbound/cli/commands/compare.py`.

#### 33.4 stage ingest에서 파일 포맷 에러

증상:

- `.json/.jsonl` 외 파일로 ingest 시 실패

근거:

- `src/evalvault/adapters/inbound/cli/commands/stage.py#_load_stage_events_with_stats`.

#### 33.5 prompts suggest에서 “스냅샷 없음”

증상:

- `이 run에 연결된 프롬프트 스냅샷이 없습니다.`

원인 후보:

- run 실행 시 `--db`를 사용하지 않아 스냅샷이 DB에 저장되지 않음

근거:

- `src/evalvault/adapters/inbound/cli/commands/prompts.py`.

---

### 34. 실무 체크리스트(확장)

#### 34.1 “비교 가능” 체크리스트(실험 단위)

- [ ] 동일 dataset (name/version/샘플)인가?
- [ ] 동일 metrics 집합인가?
- [ ] thresholds가 동일하게 적용됐는가?
- [ ] profile/provider/model이 동일한가?
- [ ] run에서 프롬프트 스냅샷이 남아 있고(diff 가능) 변경 내역이 설명 가능한가?

근거:

- thresholds 적용/저장: `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_resolve_thresholds`, `src/evalvault/domain/entities/result.py` (run.thresholds).
- prompt snapshot 제약: `src/evalvault/adapters/inbound/cli/commands/run.py`, `src/evalvault/adapters/inbound/cli/commands/prompts.py`.

#### 34.2 CI 게이트 체크리스트(자동화)

- [ ] `gate`에서 사용한 threshold(기본/커스텀)가 문서화되어 있는가?
- [ ] baseline run_id가 고정/추적 가능한가(regress-baseline 또는 CI 변수)?
- [ ] 실패 시 Exit code(1/2/3)를 CI가 올바르게 해석하는가?
- [ ] artifacts lint를 gate 이후에 실행해 산출물 무결성을 보장하는가?

근거:

- gate exit code: `src/evalvault/adapters/inbound/cli/commands/gate.py`.
- artifacts lint: `src/evalvault/adapters/inbound/cli/commands/artifacts.py`.

#### 34.3 운영 기록 체크리스트(재현성)

- [ ] run_id만 저장하지 말고, 보고서/아티팩트 경로도 함께 기록했는가?
- [ ] ops snapshot으로 설정 스냅샷을 남겼는가(특히 profile/model/env)?

근거:

- ops snapshot: `src/evalvault/adapters/inbound/cli/commands/ops.py`.

---

### 35. run 성능/안정성 노브(병렬/스트리밍)와 제약 조건

실험이 커지면 “정확도”만큼 “시간/비용/실패율”이 중요해진다.
`evalvault run`은 실행 전략을 바꾸는 옵션을 제공한다.

#### 35.1 병렬 실행

- `--parallel/-P`: 평가 병렬 처리 활성화
- `--batch-size/-b`: 병렬 배치 크기(기본 5)

근거:

- 옵션 정의: `src/evalvault/adapters/inbound/cli/commands/run.py`.

실무 규칙(권장):

- 평가가 느릴수록 병렬을 켜고 batch-size를 올리고 싶어진다.
- 하지만 LLM/임베딩 호출이 rate limit에 걸리면 “실패율”이 올라가 전체 루프가 느려질 수 있다.
- 팀 템플릿에는 기본값을 유지하고, 병렬은 “속도 문제를 확인한 뒤” 켜는 것을 권장한다.

#### 35.2 스트리밍 실행(대규모 데이터셋)

- `--stream`: 데이터셋을 chunk로 나눠 처리
- `--stream-chunk-size`: chunk 크기(기본 200)

근거:

- 옵션 정의: `src/evalvault/adapters/inbound/cli/commands/run.py`.
- 스트리밍 런 병합 로직: `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_merge_evaluation_runs`, `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_evaluate_streaming_run`.

#### 35.3 스트리밍 모드의 제약(강제 에러)

스트리밍은 “조각 단위 처리”라는 특성 때문에, 일부 기능과 동시에 사용할 수 없다.

- Domain Memory와 함께 사용할 수 없음
- Phoenix Dataset/Experiment 업로드 옵션과 함께 사용할 수 없음

근거:

- 검증/차단: `src/evalvault/adapters/inbound/cli/commands/run.py` (stream + domain_memory_requested → Exit(1), stream + phoenix_dataset/phoenix_experiment → Exit(1)).

실무 팁:

- 대규모 데이터셋에서는 먼저 스트리밍으로 “대략적인 방향성”을 잡고
- 최종 품질/추적이 필요한 경우 표본을 줄여 non-stream으로 “근거/추적 가능한 실행”을 따로 만든다.

---

### 36. Tracking(phoenix/langfuse/mlflow) 워크플로

트래킹은 “필요할 때 켜는” 형태다.
워크플로 관점에서는 다음 2가지를 분리해서 생각해야 한다.

- 평가 결과의 DB 저장(필수: history/compare/analyze/프롬프트 스냅샷)
- 외부 트래커로의 로그 전송(선택: Phoenix/Langfuse/MLflow)

#### 36.1 tracker 선택

`evalvault run`은 `--tracker`로 트래커를 선택한다.

- `--tracker langfuse|mlflow|phoenix|none`

근거:

- 옵션 정의: `src/evalvault/adapters/inbound/cli/commands/run.py`.
- 트래커 획득: `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_get_tracker`.

#### 36.2 “트래커가 켜졌는데 아무것도 안 남는” 케이스

트래커는 best-effort로 동작한다. 설정이 부족하면 경고를 내고 로깅을 건너뛴다.

예시:

- Langfuse 키가 없으면 로깅 스킵
- MLflow tracking uri가 없으면 로깅 스킵
- Phoenix extra가 설치되지 않았으면 로깅 스킵

근거:

- `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_get_tracker`.

#### 36.3 Phoenix에서 per-test-case RAG trace 기록

Phoenix tracker를 사용할 때, 추가로 per-test-case trace를 기록할 수 있다.

- `--phoenix-max-traces`: 최대 트레이스 수 제한

근거:

- 옵션/전달: `src/evalvault/adapters/inbound/cli/commands/run.py` (phoenix_opts)
- trace 기록 구현: `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#log_phoenix_traces`.

실무 팁:

- 데이터셋이 크면 `--phoenix-max-traces`로 “대표 케이스만” 보내라.
- 분석 시점에는 보고서/아티팩트로 원인을 좁힌 뒤, 트레이스는 “확인/설명” 용도로 쓰는 게 효율적이다.

---

### 37. DB 저장/엑셀 내보내기 워크플로(재현성 기본)

EvalVault의 기본 워크플로는 DB 저장을 중심으로 한다.
DB가 있어야 다음이 가능하다.

- history로 run 목록 추적
- analyze/compare/gate/regress 실행
- prompts show/diff/suggest

근거:

- DB 의존 커맨드: `src/evalvault/adapters/inbound/cli/commands/history.py`, `analyze.py`, `compare.py`, `gate.py`, `regress.py`, `prompts.py`.

#### 37.1 run 저장 시 엑셀 자동 생성

기본적으로 DB 저장 시 `evalvault_run_<RUN_ID>.xlsx`를 DB 디렉터리 아래에 생성하려고 시도한다.

근거:

- `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_save_to_db`.

#### 37.2 output이 .xlsx/.xls일 때의 동작

`evalvault run -o something.xlsx` 형태로 “엑셀을 직접 지정”할 수 있다.
이 경우:

- DB 저장이 필수
- 지정한 경로로만 저장(기본 DB 엑셀을 생성하지 않는다고 경고)

근거:

- `src/evalvault/adapters/inbound/cli/commands/run.py` (output suffix가 xlsx/xls인 경우 분기 + 경고 + `export_excel=excel_output is None`).

실무 팁:

- 팀 공유가 목적이면 `.xlsx`를 명시 경로로 저장하는 것이 편하다.
- CI에서는 파일 아카이빙 전략(artifact 업로드)을 정한 뒤 `.xlsx` 생성 여부를 결정하라.

---

### 38. 멀티턴(multiturn) 워크플로

멀티턴은 단일 QA 평가와 성격이 다르다.
EvalVault는 `--mode multiturn`을 별도 모드로 제공하며, 멀티턴 데이터셋 로더/평가기가 다르다.

#### 38.1 multiturn 모드의 기본 메트릭

- `turn_faithfulness`
- `context_coherence`
- `drift_rate`

근거:

- `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#RUN_MODE_PRESETS`.

#### 38.2 multiturn 모드에서의 제약/경고

멀티턴 모드에서는 일부 옵션이 무시되거나 지원되지 않는다.

- `--stream` 무시
- `--retriever` 지원하지 않음
- `--use-domain-memory` 지원하지 않음

근거:

- 경고 출력: `src/evalvault/adapters/inbound/cli/commands/run.py` (preset.name == "multiturn" 분기 내부).

#### 38.3 multiturn 저장(run_id)

멀티턴은 별도 엔티티로 DB에 저장하며 run_id는 UUID로 생성된다.

근거:

- run_id 생성/저장: `src/evalvault/adapters/inbound/cli/commands/run.py` (multiturn 분기에서 `run_id = str(uuid4())` + `_save_multiturn_to_db`).

---

### 39. JSON 출력의 “Envelope” 규약(머신 친화)

EvalVault의 일부 커맨드는 JSON을 “그냥 데이터”가 아니라 envelope 형태로 감싼다.
CI/자동화에서 유용한 이유는 다음 때문이다.

- 어떤 커맨드가 만들었는지(`command`)
- 스키마 버전(`version`)
- 상태(`status`)
- 실행 시간(`started_at`, `finished_at`, `duration_ms`)
- 아티팩트 루트(`artifacts.dir`, `artifacts.index`)

#### 39.1 compare envelope

compare는 저장되는 JSON에 envelope 메타를 포함한다.

- 근거: `src/evalvault/adapters/inbound/cli/commands/compare.py#_build_envelope`.

최소 필드(코드 기준):

- `command`: "compare"
- `version`: 1
- `status`
- `started_at`, `finished_at`, `duration_ms`
- `artifacts.dir`, `artifacts.index`

#### 39.2 regress envelope

regress는 JSON 출력(콘솔 또는 파일)에 envelope를 사용한다.

- 근거: `src/evalvault/adapters/inbound/cli/commands/regress.py#_build_envelope`.

특징:

- 실패 시에도 `status="error"` + `error_type`/`message`를 포함할 수 있다.

#### 39.3 artifacts lint envelope

`artifacts lint`도 동일한 envelope 패턴으로 결과를 출력한다.

- 근거: `src/evalvault/adapters/inbound/cli/commands/artifacts.py#_build_payload`.

실무 팁:

- CI에서는 이 envelope JSON을 그대로 artifact로 업로드하면,
  실패 재현 없이도 “무엇이 실패했는지”를 구조적으로 남길 수 있다.

---

### 40. GitHub Actions/GitLab CI 통합 패턴(실전)

여기서는 “CI YAML 예시”를 제공하지 않는다(레포마다 구조가 다르기 때문).
대신 EvalVault 커맨드가 제공하는 출력/exit code를 기준으로, CI가 무엇을 해야 하는지만 정리한다.

#### 40.1 gate의 github-actions 포맷

- `evalvault gate <RUN_ID> --format github-actions`

이 모드는 `::error::`, `::warning::`, `::set-output` 형태의 출력을 생성한다.

근거:

- `src/evalvault/adapters/inbound/cli/commands/gate.py`.

#### 40.2 regress의 github-actions 포맷

- `evalvault regress <RUN_ID> --baseline <BASELINE> --format github-actions`

근거:

- `src/evalvault/adapters/inbound/cli/commands/regress.py#_render_github_actions`.

#### 40.3 ci-gate의 pr-comment 포맷

- `evalvault ci-gate <BASELINE> <CURRENT> --format pr-comment`

이 모드는 PR 코멘트에 바로 붙일 수 있는 Markdown을 출력한다.

근거:

- `src/evalvault/adapters/inbound/cli/commands/regress.py#ci_gate`.

---

### 41. Worked Examples(끝까지 따라가는 예시)

이 절은 “명령을 그대로 복사해서” 팀 템플릿으로 쓰기 위한 예시다.
수치/결과는 환경에 따라 달라지므로, 출력 숫자는 문서에 적지 않는다.

#### 41.1 새 프로젝트 온보딩: init → run → history

```bash
uv run evalvault init --output-dir ./evalvault-demo

cd ./evalvault-demo

# (필요하면 .env 수정)

uv run evalvault run sample_dataset.json \
  --preset quick \
  --db data/db/evalvault.db

uv run evalvault history --db data/db/evalvault.db
```

근거:

- init: `src/evalvault/adapters/inbound/cli/commands/init.py`
- run/history: `src/evalvault/adapters/inbound/cli/commands/run.py`, `src/evalvault/adapters/inbound/cli/commands/history.py`

#### 41.2 평가 + 자동 분석 + 아티팩트 린트

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --tracker phoenix \
  --db data/db/evalvault.db \
  --auto-analyze

# 자동 분석 산출물(기본 경로)
# - reports/analysis/analysis_<RUN_ID>.json
# - reports/analysis/analysis_<RUN_ID>.md
# - reports/analysis/artifacts/analysis_<RUN_ID>/index.json

uv run evalvault artifacts lint reports/analysis/artifacts/analysis_<RUN_ID> --strict
```

근거:

- auto-analyze: `src/evalvault/adapters/inbound/cli/commands/run.py`
- artifacts lint: `src/evalvault/adapters/inbound/cli/commands/artifacts.py`

#### 41.3 A/B 비교: compare → (필요 시) analyze-compare

```bash
uv run evalvault compare <RUN_A> <RUN_B> --db data/db/evalvault.db

# 통계 검정을 포함하고 싶으면
uv run evalvault analyze-compare <RUN_A> <RUN_B> --db data/db/evalvault.db \
  --test t-test \
  --metrics faithfulness,answer_relevancy
```

근거:

- compare: `src/evalvault/adapters/inbound/cli/commands/compare.py`
- analyze-compare: `src/evalvault/adapters/inbound/cli/commands/analyze.py`

#### 41.4 CI 품질 차단: gate/regress/ci-gate

```bash
# 1) 단일 run에 대한 threshold 확인
uv run evalvault gate <RUN_ID> --db data/db/evalvault.db --format github-actions

# 2) baseline 대비 회귀 감지(간단)
uv run evalvault gate <RUN_ID> --db data/db/evalvault.db \
  --baseline <BASELINE_RUN_ID> \
  --fail-on-regression 0.05

# 3) 통계 기반 회귀 감지
uv run evalvault regress <RUN_ID> --baseline <BASELINE_RUN_ID> --db data/db/evalvault.db

# 4) CI용 종합 포맷
uv run evalvault ci-gate <BASELINE_RUN_ID> <RUN_ID> --db data/db/evalvault.db --format pr-comment
```

근거:

- gate: `src/evalvault/adapters/inbound/cli/commands/gate.py`
- regress/ci-gate: `src/evalvault/adapters/inbound/cli/commands/regress.py`

#### 41.5 프롬프트 개선 루프: prompts suggest → 재실행 → 비교

```bash
uv run evalvault prompts suggest <RUN_ID> --db data/db/evalvault.db \
  --role system \
  --metrics faithfulness,answer_relevancy \
  --weights faithfulness=0.7,answer_relevancy=0.3 \
  --candidates 5

# 개선 후보를 반영한 프롬프트로 재실행(예: --system-prompt-file)
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db \
  --system-prompt-file prompts/system.txt

uv run evalvault compare <BASELINE_RUN_ID> <NEW_RUN_ID> --db data/db/evalvault.db
```

근거:

- prompts suggest: `src/evalvault/adapters/inbound/cli/commands/prompts.py`
- system prompt injection: `src/evalvault/adapters/inbound/cli/commands/run.py`

#### 41.6 stage 기반 진단 루프: ingest → report → analyze(playbook)

```bash
uv run evalvault stage ingest path/to/stage_events.jsonl --db data/db/evalvault.db --skip-invalid
uv run evalvault stage report <RUN_ID> --db data/db/evalvault.db

# stage metrics를 포함한 playbook 분석
uv run evalvault analyze <RUN_ID> --db data/db/evalvault.db --playbook --enable-llm
```

근거:

- stage: `src/evalvault/adapters/inbound/cli/commands/stage.py`
- analyze playbook: `src/evalvault/adapters/inbound/cli/commands/analyze.py`

---

### 42. 흔한 안티패턴(워크플로를 망치는 습관)

이 절은 “베스트 프랙티스”가 아니라, 실제로 루프를 망치는 흔한 패턴을 정리한다.

#### 42.1 DB를 고정하지 않고 실행

증상:

- history/compare/analyze 결과가 팀원마다 다르게 보임

원인:

- `--db`를 각자 다르게 쓰거나, `.env` 설정이 제각각임

근거:

- 대부분의 커맨드가 `Settings().evalvault_db_path`를 fallback으로 사용
  - 예: `src/evalvault/adapters/inbound/cli/commands/history.py`, `analyze.py`.

#### 42.2 동일 조건 비교 없이 “개선”이라고 결론

원인:

- metrics/thresholds/profile/provider/model 중 하나가 바뀌었는데도 A/B 비교

근거:

- run 결과는 `metrics_evaluated`, `thresholds`, `model_name`, `tracker_metadata`에 영향을 받음
  - 예: history 출력이 tracker_metadata의 run_mode를 읽음: `src/evalvault/adapters/inbound/cli/commands/history.py`.

#### 42.3 gate 실패를 “점수 문제”로만 취급

gate는 두 종류 실패가 있다.

- threshold 실패(Exit 1)
- baseline 대비 회귀(Exit 2)

근거:

- `src/evalvault/adapters/inbound/cli/commands/gate.py`.

실무 규칙(권장):

- Exit code에 따라 대응 루프를 분리하라.
  - Exit(1): 절대 기준 미달 → 데이터/프롬프트/리트리버 자체 개선
  - Exit(2): 상대 회귀 → 변경점 좁히기(compare + prompt diff + stage)

---

### 43. 이슈/PR에 남겨야 하는 최소 정보(팀 규약 템플릿)

EvalVault 기반 개선 루프는 “기록이 남아야” 재현된다.
아래 템플릿은 팀이 그대로 복사해 쓰는 것을 목표로 한다.

#### 43.1 최소 기록(필수)

- run_id: `<RUN_ID>`
- DB: `data/db/evalvault.db` (또는 실제 사용 경로)
- dataset: (파일 경로 + dataset name/version)
- metrics: (쉼표 리스트)
- thresholds: (dataset thresholds인지, --threshold override인지)
- 산출물 경로:
  - `reports/analysis/analysis_<RUN_ID>.md`
  - `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`

근거:

- 산출물 경로 규칙: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`, `src/evalvault/adapters/inbound/cli/commands/run.py`.

#### 43.2 비교/회귀가 포함된 경우(추가)

- baseline run_id: `<BASELINE_RUN_ID>`
- compare 보고서:
  - `reports/comparison/comparison_<A8>_<B8>.md`
  - `reports/comparison/artifacts/comparison_<A8>_<B8>/index.json`
- gate/regress exit code

근거:

- compare 산출물: `src/evalvault/adapters/inbound/cli/commands/compare.py`
- gate/regress exit code: `src/evalvault/adapters/inbound/cli/commands/gate.py`, `src/evalvault/adapters/inbound/cli/commands/regress.py`.

---

### 44. 부록: 워크플로별 “내가 지금 어디에 있나?” 체크

이 부록은 “지금 내가 어떤 단계인지”를 빠르게 확인하기 위한 표식이다.

#### 44.1 가장 흔한 루프(개발)

1) run (DB 저장)
2) auto-analyze 또는 analyze
3) 보고서에서 저점 메트릭 확인
4) 아티팩트(index.json → node JSON)로 원인 후보 좁히기
5) 프롬프트/리트리버/데이터 수정
6) 재실행
7) compare/analyze-compare

근거:

- 각 커맨드 구현: `src/evalvault/adapters/inbound/cli/commands/run.py`, `analyze.py`, `compare.py`.

#### 44.2 가장 흔한 루프(CI)

1) current run 생성
2) gate(regression 포함 여부 선택)
3) regress 또는 ci-gate
4) artifacts lint
5) 실패 시: compare + ops snapshot으로 재현 단서 확보

근거:

- gate/regress/ci-gate: `src/evalvault/adapters/inbound/cli/commands/gate.py`, `regress.py`
- artifacts lint: `src/evalvault/adapters/inbound/cli/commands/artifacts.py`
- ops snapshot: `src/evalvault/adapters/inbound/cli/commands/ops.py`

---

### 45. 참고 시나리오 문서

이 챕터는 CLI 구현을 근거로 작성했지만, “검증된 실행 시나리오”는 별도 문서에 모여 있다.

- 실행 가능한 E2E 픽스처(스모크/재현의 기준점): `tests/fixtures/e2e/`
- 예시 워크플로 스크립트/산출물: `examples/`

주의:

- 시나리오 문서의 예시는 실제 검증 메모가 포함될 수 있으며, 코드가 바뀌면 최신 구현을 우선한다.
  - 근거: 이 문서의 “진실은 CLI 구현” 원칙.

---

## Part 4. 심화 부록(옵션/포맷/재현성 레이어)

Part 4는 “자주 필요하지만, 앞 파트에 넣으면 흐름이 끊기는” 내용을 모아 둔다.

---

### 46. 리트리버 문서 입력 포맷(현실적인 데이터 준비)

`evalvault run --retriever ... --retriever-docs ...`는 문서 입력 형식을 유연하게 받는다.

#### 46.1 .txt

- 한 줄이 한 문서로 처리된다(빈 줄 제외)

근거:

- `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_load_retriever_text`.

#### 46.2 .json

아래 두 가지 형태를 허용한다.

- (A) 리스트
- (B) `{ "documents": [...] }` 래핑

근거:

- `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_load_retriever_json`.

#### 46.3 .jsonl

- 한 줄이 JSON 객체 1개
- 라인 단위 파싱 실패 시 에러

근거:

- `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_load_retriever_jsonl`.

#### 46.4 문서 아이템 스키마(가벼운 표준)

각 문서 아이템은 문자열 또는 dict일 수 있다.

- 문자열: 그대로 content로 사용, doc_id는 `doc_<index>`
- dict: content 후보 키(`content|text|document`)를 우선 순서로 탐색
  - doc_id 후보 키(`doc_id|id`)를 우선 순서로 탐색

근거:

- `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_normalize_document_item`.

실무 팁:

- retriever-docs는 “정답 컨텍스트”가 아니라 “검색 후보 풀”이다.
- 문서가 너무 길면 PDF chunk 옵션을 활용하거나, 사전 청킹을 통해 문서 길이를 통제하라.

---

### 47. prompt manifest/diff 워크플로(프롬프트 변경 추적)

run 실행 시점의 프롬프트를 “파일 단위로 추적”하고 싶을 때, prompt manifest + prompt files를 사용한다.

#### 47.1 run에서 prompt metadata 수집

- `--prompt-manifest` (기본: `agent/prompts/prompt_manifest.json`)
- `--prompt-files` (쉼표로 파일 경로)

근거:

- 옵션 정의: `src/evalvault/adapters/inbound/cli/commands/run.py`.

#### 47.2 manifest와 파일이 다르면 경고

manifest와 실제 파일이 다르면 경고를 띄우고, `phoenix prompt-diff`를 안내한다.

근거:

- `src/evalvault/adapters/inbound/cli/commands/run.py` (unsynced 검사 + 경고)
- 메타 수집 로직: `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_collect_prompt_metadata`.

실무 규칙(권장):

- PR/회귀 분석에서 “프롬프트가 바뀌지 않았다”를 증명해야 할 때, prompt diff는 가장 강한 근거가 된다.
- run 결과만 공유하면 프롬프트 변경이 “기억/추측”이 되기 쉽다.

---

### 48. stage thresholds JSON 구조(프로필별 오버라이드)

stage metrics는 별도 thresholds JSON으로 합격 기준을 적용할 수 있다.

#### 48.1 기본 thresholds 파일 경로

- 기본 파일 후보: `config/stage_metric_thresholds.json` (존재할 때만 사용)

근거:

- `src/evalvault/adapters/inbound/cli/commands/stage.py#_default_thresholds_path`.

#### 48.2 thresholds JSON의 profile 오버라이드 규칙

thresholds JSON이 아래 형태면, `default` + `profiles[<profile>]`를 병합한다.

```json
{
  "default": {"retrieval_precision": 0.7},
  "profiles": {
    "dev": {"retrieval_precision": 0.6},
    "prod": {"retrieval_precision": 0.75}
  }
}
```

근거:

- 선택/병합: `src/evalvault/adapters/inbound/cli/commands/stage.py#_select_threshold_block`.

---

### 49. “Exit code 표준화” 메모(워크플로 자동화용)

커맨드마다 exit code가 조금씩 다르다.
CI/스크립트는 이를 “규약”으로 취급해야 한다.

#### 49.1 run

- 잘못된 `--mode`: Exit(2)

근거:

- `src/evalvault/adapters/inbound/cli/commands/run.py` (RUN_MODE_PRESETS 검증 실패 시 Exit(2)).

#### 49.2 history

- `--mode` 값이 `simple|full`이 아니면 Exit(2)

근거:

- `src/evalvault/adapters/inbound/cli/commands/history.py`.

#### 49.3 gate

- Exit(1): threshold 실패
- Exit(2): regression 감지
- Exit(3): run/baseline not found

근거:

- `src/evalvault/adapters/inbound/cli/commands/gate.py`.

#### 49.4 regress

- Exit(2): regression 감지

근거:

- `src/evalvault/adapters/inbound/cli/commands/regress.py`.

#### 49.5 artifacts lint

- status가 error면 Exit(1)

근거:

- `src/evalvault/adapters/inbound/cli/commands/artifacts.py`.

실무 팁:

- “Exit code 하나로 모든 실패를 표현”하지 말고, 1/2/3을 파이프라인에서 분리해라.
- 예: Exit(2)는 회귀이므로, 자동으로 compare 보고서를 생성/첨부하는 후속 스텝을 붙일 수 있다.

---

### 50. 스트리밍 워크플로 예시(대규모 데이터셋)

이 예시는 “대규모 파일을 끝까지 돌려보는” 목적이다.
재현 가능한 비교(프롬프트/추적)는 별도 표본 실행으로 분리하는 것을 권장한다.

```bash
uv run evalvault run data/large_dataset.csv \
  --mode full \
  --metrics faithfulness,answer_relevancy \
  --db data/db/evalvault.db \
  --stream \
  --stream-chunk-size 200 \
  --parallel \
  --batch-size 10
```

근거:

- 옵션 정의: `src/evalvault/adapters/inbound/cli/commands/run.py`
- 스트리밍 병합: `src/evalvault/adapters/inbound/cli/commands/run_helpers.py#_evaluate_streaming_run`.

주의:

- 스트리밍에서는 Domain Memory/Phoenix dataset 업로드 같은 옵션이 막힐 수 있다.
  - 근거: `src/evalvault/adapters/inbound/cli/commands/run.py`.

---

### 51. artifacts/index.json 해부(근거 탐색의 시작점)

EvalVault의 파이프라인 기반 산출물은 `index.json`이 “엔트리 포인트”다.
문서/리포트가 길어질수록, index.json을 잘 쓰는 팀이 디버깅이 빠르다.

#### 51.1 index.json의 핵심 필드(코드 기준)

`write_pipeline_artifacts()`가 생성하는 index payload는 다음 필드를 포함한다.

- `pipeline_id`
- `intent`
- `duration_ms`
- `started_at`, `finished_at`
- `nodes`: 노드 메타(경로 포함)
- `final_output_path` (있을 때)

근거:

- `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`.

#### 51.2 nodes 배열의 의미

nodes는 “실행된 DAG 노드”의 목록이며, 각 요소는 대략 아래 형태다.

- `node_id`
- `status`
- `duration_ms`
- `error`
- `path` (해당 노드 JSON)

근거:

- `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`.

#### 51.3 디버깅 루틴(권장)

1) index.json을 열어 `nodes`에서 status가 error인 노드를 찾는다.
2) 해당 노드의 `path` 파일을 열어 `error`/`output`을 확인한다.
3) “원인이 데이터인지(입력 결함) / 모델인지(설정/키) / 코드인지(예외)”를 구분한다.

이 루틴의 장점:

- 보고서가 LLM 생성(요약)이라도, 노드 JSON은 구조화된 근거로 남는다.

---

### 52. stage ingest 유효성 검증/실패 샘플 수집(운영에서 가장 유용한 옵션)

외부 시스템 로그는 항상 깨끗하지 않다.
stage ingest는 이를 전제로 “검증 통계 + 실패 샘플 수집”을 제공한다.

#### 52.1 --skip-invalid: 계속 진행 + 집계

- 일부 이벤트가 깨져 있어도 전체 ingest를 계속 진행
- 마지막에 invalid 타입별 집계를 출력

근거:

- `src/evalvault/adapters/inbound/cli/commands/stage.py#ingest`
- 집계 출력: `src/evalvault/adapters/inbound/cli/commands/stage.py#_print_validation_stats`.

#### 52.2 --failed-output: 실패 샘플을 JSONL로 저장

실패 샘플은 단순 로그로는 분석하기 어렵다.
`--failed-output`을 주면, 실패 payload와 에러 메시지를 라인 단위 JSONL로 남긴다.

근거:

- `src/evalvault/adapters/inbound/cli/commands/stage.py#_record_failed_sample`.

#### 52.3 실패 분류(error type)

stage ingest는 에러 메시지에서 원인을 대략 분류해 집계한다.

- missing_run_id
- invalid_stage_type
- invalid_attributes
- invalid_metadata
- invalid_attempt
- invalid_duration
- invalid_datetime
- invalid_payload_ref
- other

근거:

- `src/evalvault/adapters/inbound/cli/commands/stage.py#ValidationStats`.

실무 팁:

- 처음 외부 시스템과 연동할 때는 `--skip-invalid --failed-output ...`를 항상 켜라.
- 데이터 파이프라인이 안정화되면 `--skip-invalid`를 끄고 “실패를 빨리 발견”하는 방식으로 전환한다.

---

### 53. compare가 degraded(Exit 2)일 때의 대응 절차

compare가 Exit(2)로 끝나는 경우가 있다.
이 상황은 “완전 실패”와 다르며, 워크플로 관점에서 대응이 다르다.

#### 53.1 의미

- 비교는 수행되었고 JSON/MD/아티팩트 저장도 시도됨
- 다만 리포트가 일부 누락되었을 수 있어 degraded로 표시

근거:

- degraded 처리/Exit(2): `src/evalvault/adapters/inbound/cli/commands/compare.py`.

#### 53.2 우선 확인 순서(권장)

1) compare 출력에 표시된 파일 경로가 실제로 생성됐는지 확인
2) `reports/comparison/artifacts/comparison_<A8>_<B8>/index.json`을 열어 error 노드가 있는지 확인
3) error 노드 JSON을 열어 실패 원인(예: LLM 어댑터 초기화 경고 등)을 확인

근거:

- 아티팩트 생성/인덱스 구조: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`.

#### 53.3 CI에서의 처리(권장)

Exit(2)를 “완전 실패”로 취급할지, “경고 + artifact 업로드”로 취급할지는 팀 정책이다.

권장 정책(일반적):

- main 브랜치 병합을 막는 게이트로는 Exit(2)를 실패로 취급
- 하지만 동시에, compare 산출물을 CI artifact로 업로드해 디버깅을 빠르게 한다

---

### 54. ops snapshot의 redaction 전략(민감정보를 남기지 않으면서 재현성 확보)

ops snapshot은 “재현성”에 도움이 되지만, 설정 스냅샷에는 민감정보가 섞일 수 있다.
따라서 snapshot 생성 시점에 redaction 정책을 팀 규약으로 정해두는 것이 중요하다.

#### 54.1 include-env는 선택 옵션이다

- `--include-env`를 켜지 않으면, 설정 스냅샷 자체를 포함하지 않는다.

근거:

- 옵션 정의: `src/evalvault/adapters/inbound/cli/commands/ops.py`.

#### 54.2 redact는 “키 기반”으로 여러 번 지정한다

- `--redact <KEY>`를 반복 가능

근거:

- 옵션 정의/전달: `src/evalvault/adapters/inbound/cli/commands/ops.py` (`redact: list[str]`).

실무 팁(권장):

- 최소한 아래 키는 redact 대상으로 포함시키는 것이 안전하다.
  - `OPENAI_API_KEY`
  - `LANGFUSE_SECRET_KEY`
  - `LANGFUSE_PUBLIC_KEY` (조직 정책에 따라)
  - `VLLM_API_KEY`

주의:

- 실제로 어떤 키가 존재하는지는 환경마다 다르다.
- ops snapshot은 “값을 직접 공유”하기 위한 도구가 아니라, “어떤 설정이었다”를 남기는 도구다.

---

### 55. 명령 인덱스(이 장에서 다룬 것만)

이 인덱스는 검색용이다. 세부 워크플로는 Part 1~4를 따른다.

#### 55.1 평가/분석/비교

- `evalvault run` / `evalvault run-simple` / `evalvault run-full`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/run.py`
- `evalvault history` / `evalvault export`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/history.py`
- `evalvault analyze` / `evalvault analyze-compare`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/analyze.py`
- `evalvault compare`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/compare.py`

#### 55.2 게이트/운영

- `evalvault gate`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/gate.py`
- `evalvault regress` / `evalvault ci-gate` / `evalvault regress-baseline`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/regress.py`
- `evalvault artifacts lint`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/artifacts.py`
- `evalvault ops snapshot`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/ops.py`

#### 55.3 파이프라인/프롬프트/stage

- `evalvault pipeline analyze|intents|templates`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/pipeline.py`
- `evalvault prompts show|diff|suggest`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/prompts.py`
- `evalvault stage ingest|list|summary|compute-metrics|report`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/stage.py`
