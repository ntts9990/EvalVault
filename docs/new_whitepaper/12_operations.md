# 12. 운영/모니터링(Operations)

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: 내부 개발자가 로컬/개발 환경에서 EvalVault를 안정적으로 구동하고,
  관측 도구(Phoenix/Langfuse)와 연결할 때 필요한 최소 절차(런북)를 제공한다.
- **독자**: 내부 개발자/운영자
- **선행 지식**: Docker/Compose 기본

---

## TL;DR

- CLI 스모크: `uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness`
- API 서버: `uv run evalvault serve-api --reload`
- 프론트엔드: `cd frontend && npm install && npm run dev`
- Phoenix(+OTel Collector): `docker compose -f docker-compose.phoenix.yaml up`
- Langfuse(선택): `docker compose -f docker-compose.langfuse.yml up`

---

## 1) 로컬(개발) 실행

### 1.1 CLI 스모크

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness
```

- `--db`를 지정하면 결과가 SQLite에 저장되어 Web UI와 연동할 수 있다.
- Domain Memory는 별도의 DB를 사용한다(Settings 기본: `data/db/evalvault_memory.db`).
  - 근거: `src/evalvault/config/settings.py`

### 1.2 API + Web UI

```bash
# Terminal 1
uv run evalvault serve-api --reload

# Terminal 2
cd frontend
npm install
npm run dev
```

운영 원칙:
- CLI와 Web UI는 “같은 DB 경로”를 공유해야 결과가 자연스럽게 이어진다.

---

## 2) Phoenix + OpenTelemetry Collector

### 2.1 Compose로 실행

```bash
docker compose -f docker-compose.phoenix.yaml up
```

- Phoenix: `6006`
- Collector: `4317`(gRPC), `4318`(HTTP)

근거:
- `docker-compose.phoenix.yaml`
- `scripts/dev/otel-collector-config.yaml`

### 2.2 EvalVault에서 Phoenix를 쓰는 두 가지 경로

1) **Tracker로 Phoenix에 span을 보낸다(명시적)**
- `evalvault run`의 tracker 옵션: `--tracker phoenix`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/run.py`
- 구현: `src/evalvault/adapters/outbound/tracker/phoenix_adapter.py`

2) **자동 계측(OTel instrumentation)을 켠다(환경 기반)**
- Settings:
  - `phoenix_enabled`, `phoenix_endpoint`, `phoenix_sample_rate`, `phoenix_api_token`
  - 근거: `src/evalvault/config/settings.py`
- CLI에서 계측 활성화 보조:
  - `ensure_phoenix_instrumentation(settings, ...)`
  - 근거: `src/evalvault/config/phoenix_support.py`

> **NOTE**: 트레이싱은 “관측 비용”이 있으므로 샘플링(`phoenix_sample_rate`)을 기본으로 검토한다.

---

## 3) Stage Events / Stage Metrics (운영 디버깅의 기본 단위)

### 3.1 Stage Events(단계 이벤트)

- `StageEventBuilder`가 `EvaluationRun`에서 stage 이벤트를 만든다.
  - 근거: `src/evalvault/domain/services/stage_event_builder.py`

운영 팁:
- `evalvault run`에서 stage 이벤트를 파일로 남길 수 있다.
  - 옵션: `--stage-events <path>`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/run.py`

### 3.2 Stage Metrics(단계 지표)

- `StageMetricService.build_metrics(...)`가 stage 이벤트에서
  `retrieval.latency_ms`, `output.latency_ms` 같은 표준 지표를 만든다.
- 기본 임계값은 `DEFAULT_STAGE_THRESHOLDS`에 있다.

근거:
- `src/evalvault/domain/services/stage_metric_service.py`

---

## 4) 분석 파이프라인(DAG) 운영

### 4.1 실행

- 파이프라인 실행: `evalvault pipeline analyze "<query>"`
  - 근거: `src/evalvault/adapters/inbound/cli/commands/pipeline.py`

예:
```bash
uv run evalvault pipeline analyze "검색 방식 비교" --run <RUN_ID>
```

### 4.2 디버깅(아티팩트/인덱스)

- 파이프라인 결과는 노드별 JSON + 인덱스로 저장될 수 있다.
  - 근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py` (`write_pipeline_artifacts`)

운영 루틴:
- “어느 노드가 실패했는지”는 `index.json`의 `nodes[].status/error`로 바로 추적한다.

---

## 5) Langfuse(선택)

```bash
docker compose -f docker-compose.langfuse.yml up
```

주의:
- `docker-compose.langfuse.yml`의 `# CHANGEME` 비밀값을 로컬에서도 교체하는 것을 기본으로 한다.

---

## 6) 문제 해결 런북(체크리스트)

- 결과가 Web UI에 안 보인다
  - [ ] CLI와 Web UI가 같은 `--db` 경로를 쓰는지 확인
  - [ ] `Settings.evalvault_db_path`가 상대 경로를 repo root 기준으로 해석하는지 확인

- Phoenix에 트레이스가 안 쌓인다
  - [ ] Phoenix/Collector가 떠 있는지(`docker-compose.phoenix.yaml`)
  - [ ] `--tracker phoenix`로 명시적 전송을 켰는지
  - [ ] 자동 계측을 쓰면 `phoenix_enabled`가 true인지
  - [ ] endpoint가 올바른지(`phoenix_endpoint`, 기본 `http://localhost:6006/v1/traces`)

- 분석 파이프라인이 특정 노드에서 실패한다
  - [ ] 해당 모듈이 `pipeline_factory.py`에 등록되어 있는지
  - [ ] `analysis_io`의 아티팩트 인덱스에서 에러 메시지를 확인했는지

---

## Evidence

- 실행/설정:
  - `AGENTS.md`
  - `src/evalvault/config/settings.py`
- CLI run/pipeline:
  - `src/evalvault/adapters/inbound/cli/commands/run.py`
  - `src/evalvault/adapters/inbound/cli/commands/pipeline.py`
- Phoenix:
  - `docker-compose.phoenix.yaml`
  - `scripts/dev/otel-collector-config.yaml`
  - `src/evalvault/adapters/outbound/tracker/phoenix_adapter.py`
  - `src/evalvault/config/phoenix_support.py`
- Langfuse:
  - `docker-compose.langfuse.yml`
- Stage/Analysis IO:
  - `src/evalvault/domain/services/stage_event_builder.py`
  - `src/evalvault/domain/services/stage_metric_service.py`
  - `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`

---

## 전문가 관점 체크리스트

- [ ] 재현 가능한 실행 명령이 제공되는가
- [ ] 포트/구성 파일의 근거가 링크로 연결되는가
- [ ] run_id를 기준으로 “점수/트레이스/아티팩트”를 상호 참조할 수 있는가

---

## 향후 변경 시 업데이트 가이드

- 새 운영 커맨드/옵션이 추가되면:
  - `src/evalvault/adapters/inbound/cli/commands/` 근거로 이 장의 **1장/4장**에 재현 예시를 추가한다.

- Phoenix/OTel 설정이 바뀌면:
  - `src/evalvault/config/settings.py`, `src/evalvault/config/phoenix_support.py` 근거로
    이 장의 **2장**을 갱신한다.

- 산출물 경로/포맷이 바뀌면:
  - `src/evalvault/adapters/inbound/cli/utils/analysis_io.py` 근거로
    이 장의 **4.2**를 업데이트한다.
