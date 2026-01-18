# EvalVault CLI 시나리오 워크플로 가이드

이 문서는 EvalVault CLI를 **시나리오 기반**으로 안내합니다.
사용자가 원하는 작동 방법을 빠르게 찾고, 그대로 실행할 수 있게 구성했습니다.

---

## 대상 독자

- 처음 사용자: 최소 실행 → 결과 확인 → 분석/리포트까지 빠르게 도달
- 숙련 사용자: 프로필/메트릭/비교/게이트/파이프라인/트래커까지 재현 가능한 운용

---

## 공통 전제: 설치/환경/주요 경로

- 설치
  - `uv sync --extra dev`
  - `.env`는 `.env.example` 복사 후 설정
- 주요 경로
  - 모델 프로필: `config/models.yaml`
  - 환경 변수 템플릿: `.env.example`
  - 기본 DB: `data/db/evalvault.db`
  - 픽스처 데이터셋: `tests/fixtures/e2e/`

기본값(문서/README 기준)
- profile: `dev`
- db: `data/db/evalvault.db`
- metrics: `faithfulness,answer_relevancy`
- dataset: `tests/fixtures/e2e/insurance_qa_korean.json`
- tracing: `phoenix`
- language: `ko`

---

## 1) CLI 기능 구조화 요약

### 핵심 평가 루프
- `evalvault run` → `evalvault history` → `evalvault compare` → `evalvault analyze`/`analyze-compare`

### 품질 게이트/회귀
- `evalvault gate`, `evalvault regress`, `evalvault profile-difficulty`, `evalvault calibrate`, `evalvault calibrate-judge`

### 관찰/추적
- `evalvault phoenix`, `evalvault langfuse-dashboard`, `evalvault stage`, `evalvault debug`

### 프롬프트/지식 관리
- `evalvault prompts`, `evalvault domain`, `evalvault kg`

### 실험/벤치마크
- `evalvault experiment`, `evalvault benchmark`

### 파이프라인/확장
- `evalvault pipeline`, `evalvault method`, `evalvault generate`, `evalvault artifacts`, `evalvault ops`, `evalvault serve-api`

---

## 2) 시나리오별 실행 템플릿

각 시나리오는 “무엇을, 어떤 순서로, 어떤 옵션으로 실행할지”를 바로 쓸 수 있게 제공합니다.

### 검증 결과 메모 (2026-01-18)

- 시나리오 1: Phoenix 기동 상태에서 재실행 성공 (RUN_ID: 745f7188-a243-4d56-98b8-09b278cea6b7). Phoenix 연결 실패 로그 해소.
- 시나리오 2: Phoenix 기동 상태에서 재실행 성공 (RUN_ID: ab379baa-0cee-447c-baee-98acf765bc5b). Phoenix 연결 실패 로그 해소.
- 시나리오 3: `metrics`, `config`, `run` 모두 성공 (RUN_ID: fa6068c9-26b2-4489-81ea-31b49b72007b).
- 시나리오 4: `--profile prod` 실행 성공 (RUN_ID: c5729e79-a9f6-467f-be42-6057717183ff). 대형 모델이라 기본 타임아웃(120s) 초과 → 300s로 재시도 필요.
- 시나리오 5: `init` 기본/`--output-dir`/`--skip-env --skip-sample` 모두 성공.
- 시나리오 6: `history`, `analyze`, `analyze-compare`, `compare`, `export` 모두 성공. `t-test` 시 `p-value=nan` 경고(분산 부족) 발생.
- 시나리오 7: `gate` 성공. `regress`는 `RUN_ID`/`--baseline` 필수라 문서 예시 보정 필요. `regress` 정상 실행은 `evalvault regress <RUN_ID> --baseline <BASELINE_RUN_ID> --db ...`.
- 시나리오 8: 18건 데이터셋으로 재실행 성공 (RUN_ID: 660592a6-6717-4ef7-8bb9-f4a1f4d7d1d6). 인과 분석 경고 해소. Ollama 환경에서 faithfulness verdict 오류 재현되지 않음(우회 로직 적용 이후).
- 시나리오 9: API 서버는 8000 포트에서 실행 중 확인. Web UI는 5173 포트에서 재기동 완료(omo-evalvault-webui).
- 시나리오 10: `stage ingest`는 Stage 이벤트 JSON/JSONL만 허용. 데이터셋 파일 입력 시 실패. `run --stage-events <PATH>`로 생성한 이벤트로 `ingest/summary/compute-metrics/list/report` 정상 실행. `system_prompt` stage는 `--prompt-manifest` + `--prompt-files` 제공 시 정상 기록됨 (RUN_ID: 01ffa508-0a8f-4451-9249-c44666b337c6).
- 시나리오 11: `prompts show/suggest`, `run`, `analyze-compare` 성공. 개선 전후 성능 변화 없음.
- 시나리오 12: 시나리오 10과 동일 단계로 검증 완료.
- 시나리오 13: `domain init`은 `--name` 옵션 없음 + `--db` 옵션 없음. 문서 예시 수정 필요. 실제 동작: `evalvault domain init <domain>`; 이후 `run --use-domain-memory --memory-domain <domain>` 성공 (RUN_ID: a05f055a-1327-464c-a04e-2317211629b4).
- 시나리오 14: `benchmark run -n korean-rag` 원인 수정 후 재실행 성공. 출력 저장: `reports/benchmark.json`.

### 시나리오 1: 기본 평가(처음 사용자)

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --tracker phoenix \
  --db data/db/evalvault.db \
  --auto-analyze

uv run evalvault history --db data/db/evalvault.db
uv run evalvault analyze <RUN_ID> --db data/db/evalvault.db
```

### 시나리오 2: 빠른 운용 모드 선택

```bash
# Simple vs Full
uv run evalvault run-simple tests/fixtures/e2e/insurance_qa_korean.json -p dev
uv run evalvault run-full tests/fixtures/e2e/insurance_qa_korean.json -p dev

# Preset 기반
uv run evalvault run --preset production tests/fixtures/e2e/insurance_qa_korean.json \
  --profile dev \
  --tracker phoenix \
  --db data/db/evalvault.db
```

### 시나리오 3: 커스텀 메트릭 선택

```bash
uv run evalvault metrics
uv run evalvault config

uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --tracker phoenix \
  --db data/db/evalvault.db
```

- `answer_relevancy`, `semantic_similarity`는 임베딩 엔드포인트 필요
- Simple 모드는 `faithfulness`, `answer_relevancy`만 허용

### 시나리오 4: 프로필/환경 변수로 모델 전환

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness \
  --profile prod \
  --tracker phoenix \
  --db data/db/evalvault.db
```

- 대형 모델은 평가 시간이 길어져 타임아웃을 늘려야 할 수 있습니다.

### 시나리오 5: 데이터셋/템플릿 기반 재현 실행

```bash
uv run evalvault init
uv run evalvault init --output-dir ./my-project
uv run evalvault init --skip-env --skip-sample
```

### 시나리오 6: 분석/비교 워크플로

```bash
uv run evalvault history --db data/db/evalvault.db

uv run evalvault analyze <RUN_ID> \
  --db data/db/evalvault.db \
  --nlp --causal \
  --output reports/analysis/custom_<RUN_ID>.json \
  --report reports/analysis/custom_<RUN_ID>.md

uv run evalvault analyze-compare <RUN_A> <RUN_B> \
  --db data/db/evalvault.db \
  --metrics faithfulness,answer_relevancy \
  --test t-test \
  --output reports/comparison/comparison_<RUN_A>_<RUN_B>.json \
  --report reports/comparison/comparison_<RUN_A>_<RUN_B>.md

uv run evalvault compare <RUN_A> <RUN_B> \
  --db data/db/evalvault.db \
  --metrics faithfulness,answer_relevancy \
  --test t-test \
  --format table

uv run evalvault export <RUN_ID> -o reports/run_<RUN_ID>.json --db data/db/evalvault.db
```

### 시나리오 7: 품질 게이트(회귀 포함)

```bash
uv run evalvault gate <RUN_ID> \
  --db data/db/evalvault.db \
  --format github-actions

uv run evalvault gate <RUN_ID> \
  --db data/db/evalvault.db \
  --threshold faithfulness:0.8 \
  --baseline <BASELINE_RUN_ID> \
  --fail-on-regression 0.05

uv run evalvault regress <RUN_ID> --baseline <BASELINE_RUN_ID> --db data/db/evalvault.db
```

### 시나리오 8: 자연어 분석 파이프라인

```bash
uv run evalvault pipeline analyze "낮은 메트릭 원인 분석" \
  --run <RUN_ID> \
  --db data/db/evalvault.db \
  --output reports/analysis/pipeline_<RUN_ID>.json

uv run evalvault pipeline intents
uv run evalvault pipeline templates
```

- 인과 분석이 필요한 경우 10건 이상 데이터셋을 권장합니다.

### 시나리오 9: API 서버/프론트 연계

```bash
uv run evalvault serve-api --reload

cd frontend
npm install
npm run dev
```

- CLI와 Web UI는 동일 DB 경로를 사용해야 히스토리가 공유됩니다.

### 시나리오 10: Stage 이벤트 기반 분석/후처리

```bash
uv run evalvault stage ingest path/to/stage_events.jsonl --db data/db/evalvault.db
uv run evalvault stage summary <RUN_ID> --db data/db/evalvault.db
uv run evalvault stage compute-metrics <RUN_ID> --db data/db/evalvault.db

uv run evalvault stage list <RUN_ID> --db data/db/evalvault.db
uv run evalvault stage report <RUN_ID> --db data/db/evalvault.db
```

- 실행 중 Stage 기록 옵션
  - `evalvault run --stage-events <PATH>`
  - `evalvault run --stage-store/--no-stage-store`
- system_prompt stage를 기록하려면 아래 옵션을 함께 지정합니다.
  - `--prompt-manifest agent/prompts/prompt_manifest.json`
  - `--prompt-files agent/prompts/system.txt`

### 시나리오 11: 프롬프트 개선 루프

```bash
uv run evalvault prompts show <RUN_ID> --db data/db/evalvault.db
uv run evalvault prompts suggest <RUN_ID> --db data/db/evalvault.db \
  --metrics faithfulness,answer_relevancy \
  --weights faithfulness=0.7,answer_relevancy=0.3 \
  --candidates 5

uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --tracker phoenix \
  --db data/db/evalvault.db

uv run evalvault analyze-compare <BASELINE_RUN> <NEW_RUN> --db data/db/evalvault.db
```

### 시나리오 12: 검색 품질 진단(스테이지 기반)

```bash
uv run evalvault stage ingest path/to/stage_events.jsonl --db data/db/evalvault.db
uv run evalvault stage summary <RUN_ID> --db data/db/evalvault.db
uv run evalvault stage compute-metrics <RUN_ID> --db data/db/evalvault.db
uv run evalvault stage report <RUN_ID> --db data/db/evalvault.db
```

### 시나리오 13: 지식/도메인 보강 기반 개선

```bash
uv run evalvault domain init insurance

uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --tracker phoenix \
  --use-domain-memory --memory-domain insurance \
  --db data/db/evalvault.db
```

### 시나리오 14: 벤치마크 확장

```bash
uv run evalvault benchmark run -n korean-rag -o reports/benchmark.json -v
uv run evalvault benchmark compare --db data/db/evalvault.db
```

- 벤치마크 데이터 디렉터리: `examples/benchmarks/korean_rag`

---

## 3) RAG 성능 측정/개선 관점의 연계 시나리오

- 엔드투엔드 품질 루프: `run` → `analyze` → `prompts suggest` → `compare` → `gate`
- 검색 품질 집중 루프: `run` → `stage compute-metrics` → `analyze` → `kg`/`domain` → `compare`
- 실험/A-B 기반 루프: `experiment create/add-run` → `compare` → `analyze-compare` → `regress`
- 벤치마크 확장 루프: `benchmark run/retrieval/kmmlu` → `compare` → `analyze`
- 관찰 가능성 강화 루프: `phoenix export-embeddings` → `stage report` → `debug report`
- 데이터 품질 개선 루프: `generate` → `run` → `profile-difficulty` → `analyze`
- 파이프라인 모듈 개선 루프: `method list/run` → `run` → `compare` → `analyze`

---

## 4) 연계가 만드는 추가 가치

- **정량-정성 통합**: `analyze` 플레이북 + `prompts suggest`로 수치와 품질을 함께 개선
- **원인 분해**: `stage` 지표와 `kg`/`domain` 조합으로 검색/지식/응답 실패 원인 분리
- **재현성**: `history export` + `ops snapshot`으로 비교 가능한 기준선 확보
- **운영 자동화**: `gate`/`regress`로 배포 전후 품질 보증 루프 구축
- **관찰 가능성**: `phoenix`/`langfuse`로 실험 로그까지 일원화

---

## 5) 운영 팁

- **DB 경로 고정**: `--db`를 고정해야 history/compare/analyze가 재현됩니다.
- **모델 프로필 분리**: `--profile dev/prod`를 분리해 환경별 결과를 비교하세요.
- **자동 분석 활성화**: `--auto-analyze`는 기본 리포트 + 아티팩트 저장을 자동화합니다.
- **관찰 가능성 옵션화**: 필요할 때만 `--tracker phoenix`를 켜서 비용을 제어하세요.

---

## 6) 관련 문서

- 사용자 가이드: `docs/guides/USER_GUIDE.md`
- 진단 플레이북: `docs/guides/EVALVAULT_DIAGNOSTIC_PLAYBOOK.md`
- RAG 성능 개선 제안서: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`
- Open RAG Trace: `docs/architecture/open-rag-trace-spec.md`
- 프롬프트 추천 설계: `docs/guides/prompt_suggestions_design.md`
