# EvalVault — Adapter Contract

> 인수팀 / AI Tool Suite 어댑터 저자가 EvalVault를 reverse-engineer 하지 않고
> 통합할 수 있도록 만든 **운영 계약 문서**. SSoT 머신-리더블 상태는
> [`.ai-tool-suite/project-state.json`](../.ai-tool-suite/project-state.json),
> 변경 narrative는 [`development-journal.md`](./development-journal.md).

- 기준 버전: **v1.77.0** (main = `bc88726`, latest in-session HEAD = `e9c79f3`)
- 마지막 갱신: 2026-05-22
- 분류: `trusted-runtime`
- T-level cap: **T2 (Evaluation Gate)**. T3 promote/rollback는 Reverra-Gate 권한.

---

## 1. 안정 명령 (Stable Commands)

| 명령 | 목적 | 안정성 |
|---|---|---|
| `evalvault run <dataset> [--profile <name>] [--metrics ...]` | RAG 평가 실행 | stable |
| `evalvault regress <candidate> --baseline <baseline> [--format json] [--output <path>]` | 회귀 게이트 비교 + JSON 아티팩트 | stable |
| `evalvault history [--format json] [--limit N]` | 저장된 run 목록 | stable |
| `evalvault export <run_id> --output <path>` | run 한 건을 JSON으로 추출 | stable |
| `evalvault metrics` | 등록된 평가 메트릭 목록 | stable |
| `evalvault config` | 해석된 설정 출력 (시크릿 마스킹) | stable |
| `evalvault analyze <run_id> [--intent ...]` | DAG 기반 분석 (선택적 LLM 사용) | beta |
| `evalvault calibrate-judge <run_id> --metric <name>` | LLM judge 보정 (isotonic/Platt) | beta |
| `evalvault api serve [--host ... --port ...]` | FastAPI 로컬 백엔드 + Web UI | stable |

`--help`는 모든 명령에 대해 동작; non-interactive 사용을 기본으로 가정.

---

## 2. 안정 아티팩트 (Stable Artifacts)

### 2.1 Regression-Gate Report (`schema_version: 1.0`)

`evalvault regress` 명령이 `--format json --output <path>` 옵션과 함께 호출될 때 생성되는 단일 JSON 파일. **이 스키마는 안정 보장됨** — 필드 제거/이름 변경은 major bump.

```json
{
  "candidate_run_id": "string",
  "baseline_run_id": "string",
  "status": "passed | failed",
  "regression_detected": false,
  "fail_on_regression": 0.05,
  "test": "t-test | mann-whitney",
  "metrics": ["faithfulness", "answer_relevancy"],
  "results": [
    {
      "metric": "faithfulness",
      "baseline_score": 0.823,
      "candidate_score": 0.812,
      "diff": -0.011,
      "diff_percent": -1.337,
      "p_value": 0.412,
      "effect_size": 0.07,
      "effect_level": "negligible | small | medium | large",
      "is_significant": false,
      "regression": false
    }
  ],
  "parallel": true,
  "concurrency": 4
}
```

#### 필드 의미

| 필드 | 타입 | 의미 |
|---|---|---|
| `candidate_run_id` | string | 평가 대상 run ID |
| `baseline_run_id` | string | 비교 기준 run ID |
| `status` | `"passed" \| "failed"` | 종합 verdict. **`promote`/`rollback`은 절대 출력되지 않음** (T2 cap) |
| `regression_detected` | bool | 어떤 메트릭이라도 `fail_on_regression`보다 떨어졌는지 |
| `fail_on_regression` | float | 회귀 판단 임계값 (기본 0.05) |
| `test` | `"t-test" \| "mann-whitney"` | 사용한 통계 검정 |
| `metrics` | list[string] | 비교 대상 메트릭 이름 |
| `results[].metric` | string | 메트릭 이름 |
| `results[].baseline_score` | float | 베이스라인 mean |
| `results[].candidate_score` | float | 후보 mean |
| `results[].diff` | float | candidate − baseline (음수 = 후퇴) |
| `results[].diff_percent` | float | diff / baseline × 100 |
| `results[].p_value` | float | 통계 검정 p-value |
| `results[].effect_size` | float | Cohen's d 등 |
| `results[].effect_level` | enum string | `negligible/small/medium/large` |
| `results[].is_significant` | bool | p_value 기반 유의성 |
| `results[].regression` | bool | 이 메트릭이 후퇴 임계 넘었는지 |
| `parallel` | bool | 병렬 실행 여부 |
| `concurrency` | int \| null | 동시성 한계 |

#### 안정 보장 필드 (`fields_safe_to_rely_on`)

- 모든 위 필드 (베타 enum 제외)
- `evalvault` CLI exit code: `0`=pass, non-zero=error or regression

#### 실험 단계 필드 (`fields_experimental`)

- `results[].effect_level` enum 값 — 향후 minor에서 새 level이 추가될 가능성 있음

### 2.2 Calibration Artifact (`schema_version: 0.9`)

`evalvault calibrate-judge`가 생성. `reports/calibration/artifacts/<calibration_id>/` 디렉터리 하위에:

- `summary.json` — 보정 메타데이터 + per-metric 통계
- `case_results.<metric>.jsonl` — case-level 보정 전후 점수
- `parameters.<metric>.json` — isotonic regression / Platt scaling 파라미터

스키마 베타. 디렉터리 파일명은 안정, 내부 구조는 minor에서 진화 가능.

### 2.3 History / Export Artifacts (`schema_version: 1.0`)

- `evalvault history --format json` — `[{ run_id, dataset_name, model_name, pass_rate, total_test_cases, started_at, finished_at, metrics_evaluated, ... }]`
- `evalvault export <run_id> --output <path>` — 단일 run + per-case scores + metadata

---

## 3. 필요한 시크릿

| 시크릿 | 사용처 | 기본 모드 |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI judge / 임베딩 | optional (profile=ollama/vllm/anthropic 사용 시 불필요) |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | Langfuse tracker | optional (TRACKER_PROVIDER에 따라 다름) |
| `MLFLOW_TRACKING_URI` | MLflow 추적 | optional, default localhost:5000 |
| `PHOENIX_ENDPOINT` | Phoenix 관측 | optional, default localhost:6006 |
| `OPENAI_BASE_URL` | OpenAI-호환 게이트웨이 / 폐쇄망 프록시 | optional |

`evalvault config` 출력에서 시크릿은 항상 마스킹.

---

## 4. 네트워크 자세 (Network Posture)

| 명령 | posture | 비고 |
|---|---|---|
| `regress`, `history`, `export`, `metrics`, `config` | offline | OpenAI / Langfuse / MLflow / Phoenix 호출 없음 |
| `run` | cloud-opt-in | profile에 따라 OpenAI / Azure / Anthropic 호출. Ollama / vLLM 프로필은 local-service. |
| `analyze`, `calibrate-judge` | offline (옵션 LLM은 cloud-opt-in) | 보정 자체는 통계 연산; intent classifier가 LLM을 쓸 수 있음 |
| `api serve` | local-service | FastAPI 백엔드는 로컬 binding. CORS / 인증은 운영자 책임 |

### 폐쇄망 실행 (Closed-Network Run)

가장 작은 폐쇄망 smoke:

```bash
TRACKER_PROVIDER= \
LANGFUSE_PUBLIC_KEY= LANGFUSE_SECRET_KEY= \
OPENAI_API_KEY= \
uv run pytest tests/unit/ -q -m \
  "not requires_openai and not requires_langfuse and not requires_phoenix and not requires_mlflow"
```

기대치: 2,076 passed (현재 머지 대기 브랜치 기준; main은 약간 다를 수 있음). 6건은 환경 의존성(Ollama 미설치, Postgres role 부재)으로 fail; 해당 마커 추가는 향후 슬라이스.

평가 자체를 폐쇄망에서 실행하려면:

```bash
EVALVAULT_PROFILE=ollama-local uv run evalvault run tests/fixtures/e2e/edge_cases.json \
  --metrics faithfulness,answer_relevancy --output reports/run_$(date +%s).json
```

(Ollama 서버가 `localhost:11434`에서 동작해야 함.)

---

## 5. 생성/픽스처 경로 (Generated vs Fixture)

| 분류 | 경로 | gitignore | 설명 |
|---|---|---|---|
| 픽스처 | `tests/fixtures/e2e/` | tracked | 큐레이션된 평가 데이터셋. 한국어 보험 / 콜센터 / 엣지 케이스 / regression 베이스라인 등. |
| 픽스처 | `tests/fixtures/` | tracked | 단위 테스트용 작은 결정적 데이터 |
| 생성물 | `data/exports/` | ignored | `evalvault export` 출력 |
| 생성물 | `mlruns/` | ignored | MLflow 로컬 트래킹 |
| 생성물 | `reports/calibration/artifacts/<id>/` | partially | calibration 결과; 운영 환경에서는 외부 storage로 |
| 생성물 | `reports/regression/` | partially | `evalvault regress --output` 결과 |
| 생성물 | `frontend/test-results/`, `frontend/playwright-report/` | ignored | Playwright 산출물 |
| 워크스페이스 | `.claude/`, `.omc/`, `.sisyphus/`, `scratch/` | ignored | 에이전트 / 도구 로컬 상태 |

---

## 6. 구조적 에러 동작 (Structured Error Behavior)

- CLI 명령은 실패 시 exit code non-zero + stderr에 human-readable 메시지.
- `--format json`을 지원하는 명령(`history`, `regress` 등)은 오류도 JSON으로 출력하지 않음 (현재); CI에서 JSON 파싱하기 전에 exit code를 먼저 검사할 것.
- 향후 어댑터 통합을 위해 **structured error JSON 출력** 옵션 (`--error-format json` 또는 자동 wrap)이 next_priorities에 있음. 현재는 stderr 텍스트로 가정하고 어댑터 작성.

---

## 7. 롤백 경로 (Rollback)

- 모든 변경은 슬라이스(브랜치) 단위로 머지. 회귀 발견 시 `git revert <merge_commit>`이 1차 롤백.
- 데이터 측면 롤백: SQLite/Postgres 어댑터의 run은 immutable. 잘못된 run은 archive 플래그로 표시 (CLI 직접 노출 안 됨; 운영자가 DB 레벨에서 처리).
- regression 베이스라인 파일(`tests/fixtures/e2e/regression_baseline.json`)이 갱신되었을 때 롤백: `git checkout <prev_commit> -- tests/fixtures/e2e/regression_baseline.json` + 다음 회귀 게이트 실행으로 검증.

---

## 8. 대표 아티팩트 재생성

```bash
# 1. 베이스라인 run 생성 (또는 history에서 기존 run 사용)
uv run evalvault run tests/fixtures/e2e/edge_cases.json \
  --metrics faithfulness,answer_relevancy --profile dev \
  --output reports/baseline_run.json

# 2. 후보 run 생성 (같은 데이터셋, 변경된 모델/프롬프트)
uv run evalvault run tests/fixtures/e2e/edge_cases.json \
  --metrics faithfulness,answer_relevancy --profile dev-candidate \
  --output reports/candidate_run.json

# 3. regression-gate 아티팩트 생성
uv run evalvault regress <candidate_run_id> --baseline <baseline_run_id> \
  --format json --output reports/regression/sample.json
```

---

## 9. T0-T4 권한 계약

- EvalVault 기본 프로필은 **T0 진단 / T1 메트릭 근거 / T2 평가 게이트** 출력까지 emit.
- **T3 (release-gate: promote / rollback / hold) 는 절대 emit 하지 않음.** 본 계약에 통합하는 어댑터는 EvalVault status를 그대로 promote/rollback에 매핑하지 말 것.
- Web UI에 표시되는 `AuthorityBadge` primitive (`frontend/src/design/components/AuthorityBadge.tsx`)는 T0~T4를 시각적으로 분리. Reverra-Gate가 T3을 emit할 때만 그 단계 배지를 표시.

---

## 10. 후속 어댑터 작업 후보

- Level 1 → Level 2 adapter (현재 `Level 2 exists`): regression-gate JSON 직접 polling
- Level 2 → Level 3 (`Next useful target`): `evalvault` CLI를 로컬 invoke하면서 no-network guard 강제. AI Tool Suite가 sandbox 안에서 직접 명령 실행.

기대 입력/출력:

```
input:  workspace path + dataset path + profile name
output: regression-gate JSON (schema 1.0) + run history append + exit code
```

---

## 11. 변경 이력

전체 narrative는 [`docs/development-journal.md`](./development-journal.md).
이 계약 문서 자체의 변경은 git log로 추적 (`git log --oneline -- docs/adapter-contract.md`).
