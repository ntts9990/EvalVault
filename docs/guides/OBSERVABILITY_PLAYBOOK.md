# Observability Playbook

> Phoenix 12.27.0 · EvalVault 3.2 · 마지막 업데이트: 2026-01-05

EvalVault 운영 환경에서 Phoenix 기반 옵저버빌리티를 표준화하기 위한 실행 가이드를 정리했습니다. Drift 감시 → Gate → 릴리즈 노트에 이르는 자동화를 단계별로 참고하세요.

---

## 1. Phoenix Drift Watcher

`scripts/ops/phoenix_watch.py`는 Phoenix Dataset/Experiment 변화를 폴링하여 Slack/파일 알림을 보내고, 임계치를 넘으면 자동으로 EvalVault Gate를 실행합니다.

### 주요 특징

- **상태 저장**: `--state-file`에 마지막 업데이트 타임스탬프를 기록하여 중복 알림을 방지합니다.
- **Drift 지표 선택**: `--drift-key`(기본 `embedding_drift_score`)에 지정한 키를 Experiment payload, `metrics`, `metadata`에서 순차적으로 찾습니다.
- **임계치 알림**: `--drift-threshold` 이상이면 터미널/Slack/이슈 로그에 경고를 남기고, 필요 시 Gate를 실행합니다.
- **자동 Gate 실행**: `--gate-command`로 전달한 EvalVault Gate 명령이나 쉘 파이프라인을 실행하며, stdout/stderr를 Slack과 이슈 파일에 동일하게 기록합니다.
- **Slack 포맷 통일**: 알림 메시지에 Experiment/Project/성공·실패 카운트와 드리프트 값이 함께 찍히므로 어떤 Phoenix 실험을 열어야 할지 즉시 파악할 수 있습니다.
- **Regression Runner 연계**: `--run-regressions event|threshold` 플래그와 `--regression-config config/regressions/default.json`을 지정하면 Phoenix 이벤트 발생 시 `scripts/tests/run_regressions.py`를 자동 호출해 회귀 테스트를 실행하고 결과 요약을 Slack/Issue로 공유합니다. `--regression-suite` 옵션을 여러 번 넘겨 특정 스위트만 골라 실행할 수 있습니다.

### 실행 예시

```bash
uv run python scripts/ops/phoenix_watch.py \
  --endpoint http://localhost:6006 \
  --dataset-id ds_12345 \
  --interval 120 \
  --drift-key embedding_drift_score \
  --drift-threshold 0.2 \
  --slack-webhook https://hooks.slack.com/services/... \
  --issue-file reports/phoenix_watch.md \
  --gate-command "uv run evalvault gate RUN_ID --format github-actions --db evalvault.db" \
  --run-regressions threshold \
  --regression-config config/regressions/default.json \
  --regression-suite integration-english-smoke \
  --regression-stop-on-failure
```

> **Tip**: 복잡한 파이프라인이 필요하면 `--gate-shell`을 추가해 하나의 쉘 문자열로 파이프를 구성할 수 있습니다.

### Alert 정책

1. Drift 지표 ≥ threshold 인 경우 `⚠` 메시지로 Slack/Issue에 기록.
2. Gate 명령을 실행하고 exit code 및 로그를 동일하게 공유.
3. Gate 실패 시 Slack 메시지가 `exit_code != 0`를 포함하므로 온콜이 즉시 후속 조치를 취할 수 있습니다.

### Regression Runner 스크립트

`scripts/tests/run_regressions.py`는 `config/regressions/default.json`에 정의된 스위트를 순차 실행하고, 상태 요약을 표준 출력·Slack·이슈 파일에 남깁니다. 기본 설정은 품질 게이트 유닛 테스트와 영어 데이터셋 E2E 스모크 테스트 두 가지이며, JSON 파일을 수정하거나 `--suite` 플래그를 반복 지정하여 필요한 스위트만 선택할 수 있습니다. Phoenix Watcher는 `--run-regressions`가 활성화되면 동일한 스크립트를 자동으로 호출하므로 온콜 담당자는 Drift 알림 → 회귀 테스트까지 단일 로그로 추적할 수 있습니다.

---

## 2. Release Notes + Phoenix Links

`scripts/reports/generate_release_notes.py`는 EvalVault CLI `--output` JSON을 읽어 Markdown/Slack 릴리즈 노트를 생성합니다. `evalvault.config.phoenix_support.format_phoenix_links` 헬퍼가 `phoenix_trace_url`, Experiment URL, Dataset URL, Embedding Export CLI를 표준 변수로 묶어 주므로 Slack/Confluence/Issue 템플릿에 그대로 사용할 수 있습니다.

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness --tracker phoenix --output reports/run.json
uv run python scripts/reports/generate_release_notes.py \
  --summary reports/run.json \
  --style slack
```

생성된 텍스트는 다음 정보를 포함합니다.

- 데이터셋/모델/Pass Rate 요약
- 주요 메트릭 평균
- 실패한 테스트 케이스 상위 `--max-failures` 개
- Phoenix Trace/Dataset/Experiment 링크 및 임베딩 내보내기 CLI

Slack 스타일(`<http://...|Phoenix Trace>`)을 사용하면 Phoenix 링크를 별도로 복사할 필요 없이 즉시 공유할 수 있습니다.

---

## 3. Embedding Overlay → Domain Memory

Phoenix Embedding export 결과를 Domain Memory Facts로 옮기려면 `uv run evalvault domain memory ingest-embeddings` 명령을 사용합니다. CSV/Parquet 파일에서 클러스터별 대표 질문과 컨텍스트를 추려서 `embedding_pattern` 사실로 저장합니다.

```bash
uv run evalvault phoenix export-embeddings --dataset ds_123 --output /tmp/phoenix.csv
uv run evalvault domain memory ingest-embeddings /tmp/phoenix.csv \
  --domain insurance \
  --language ko \
  --min-cluster-size 5 \
  --sample-size 3
```

`--dry-run`으로 저장 전 요약을 확인할 수 있고, `--cluster-key`를 변경해 사용자 정의 컬럼(예: `topic_id`)을 Fact subject로 사용할 수도 있습니다. 저장된 Fact는 Domain Memory 검색/인사이트 패널에 즉시 노출되어 Phoenix에서 찾은 실패 패턴을 EvalVault 개선 루프에 재사용할 수 있습니다.

---

## 4. History & Web Dashboards

- `uv run evalvault history` 명령은 Phoenix Experiment가 연결된 실행에 대해 `Phoenix P@K`, `Drift` 컬럼을 자동으로 채웁니다. `.env`의 `PHOENIX_ENDPOINT`/`PHOENIX_API_TOKEN`을 이용해 Phoenix REST API에서 precision@k·drift 지표를 가져오며, 테이블에서 바로 이상치를 확인할 수 있습니다.
- Web UI Home/History/Reports 페이지에서도 동일한 지표가 표시되고 Phoenix Experiment 링크가 함께 제공되므로 EvalVault 통계 → Phoenix Embeddings 탭으로 원클릭 전환이 가능합니다.

---

## 5. 운영 팁

- Drift Watcher는 `systemd`/`supervisor`/GitHub Actions Cron 등 반복 실행 환경에서 구동하며, Slack WebHook 실패 시 stderr에 경고를 남기므로 로그로도 추적 가능합니다.
- Release Notes 스크립트는 CI에서 `uv run evalvault gate RUN_ID --format json` 결과와 함께 실행해 릴리즈 PR description을 자동 채우는데 사용하세요.
- Phoenix 클러스터/드리프트 지표는 Dataset마다 다를 수 있으므로 `--drift-key`를 도메인별로 설정한 `.env.ops` 파일에 저장해두면 편리합니다.

---

## 6. Prompt Playground Loop

Phoenix Prompt Playground에서 실험한 프롬프트를 EvalVault 실행/리포트에 반영하려면 다음 단계를 따르세요.

1. **Manifest에 Prompt ID 기록**

```bash
uv run evalvault phoenix prompt-link agent/prompts/baseline.txt \
  --prompt-id pr-428 --experiment-id exp-20250115 \
  --notes "Gemma3 베이스라인"
```

2. **Diff 확인 및 공유**

```bash
uv run evalvault phoenix prompt-diff \
  agent/prompts/baseline.txt agent/prompts/system.txt \
  --manifest agent/prompts/prompt_manifest.json \
  --format table  # json으로 기계 처리도 가능
```

3. **평가 실행 시 Prompt 상태 주입**

```bash
DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
uv run evalvault run "$DATASET" --metrics faithfulness \
  --profile prod \
  --tracker phoenix \
  --prompt-files agent/prompts/baseline.txt,agent/prompts/system.txt \
  --prompt-manifest agent/prompts/prompt_manifest.json
```

> 💡 **Prompt Loop 전용 모델**: Phoenix Prompt Playground → EvalVault 검증 루프에서는 `prod` 프로필(LLM=`gpt-oss-safeguard:20b`, OpenAI OSS)로 실행하세요. 이 모델은 Phoenix tool-calling을 지원하므로 `gemma3:1b`에서 발생하던 “does not support tools” 오류 없이 Prompt diff/Trace 데이터를 수집할 수 있습니다. (실행 시간은 길어지지만 Prompt 회귀 검증 품질을 위해 권장됩니다.)

CLI는 `result.tracker_metadata["phoenix"]["prompts"]`에 각 파일의 상태(동기화/수정/미추적), 체크섬, diff를 저장합니다. Release Notes 스크립트, History CLI, Web UI가 이 필드를 이용해 Prompt 변화를 Trace/Dataset/Experiment 링크 옆에 표시하므로, Prompt 회귀 여부를 Phoenix Embeddings·Prompt Playground와 동시에 추적할 수 있습니다.
