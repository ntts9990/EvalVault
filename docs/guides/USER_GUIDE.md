# EvalVault 사용자 가이드

> RAG 시스템 품질 평가 · 분석 · 추적을 위한 종합 워크플로 가이드

이 문서는 README에서 다룬 간단한 소개를 넘어, 설치부터 Phoenix 연동·Domain Memory·자동화까지 모든 기능을 심층적으로 설명합니다.

---

## 목차

1. [시작하기](#시작하기)
   - [시스템 요구 사항](#시스템-요구-사항)
   - [설치 옵션](#설치-옵션)
2. [환경 구성](#환경-구성)
   - [.env 작성](#env-작성)
   - [모델 프로필 관리](#모델-프로필-관리)
   - [데이터셋 준비](#데이터셋-준비)
3. [핵심 워크플로](#핵심-워크플로)
   - [CLI 실행](#cli-실행)
   - [히스토리/비교/내보내기](#히스토리비교내보내기)
   - [Web UI](#web-ui)
   - [단계별 성능 평가 (stage)](#단계별-성능-평가-stage)
4. [저장·추적](#저장추적)
   - [SQLite/PostgreSQL](#sqlitepostgresql)
   - [Langfuse](#langfuse)
5. [관측성 & Phoenix](#관측성--phoenix)
   - [트레이싱 활성화](#트레이싱-활성화)
   - [Dataset/Experiment 동기화](#datasetexperiment-동기화)
   - [임베딩 분석 & 내보내기](#임베딩-분석--내보내기)
   - [Prompt Manifest 루프](#prompt-manifest-루프)
   - [드리프트 감시 & 릴리스 노트](#드리프트-감시--릴리스-노트)
6. [Domain Memory & 분석 기능](#도메인-메모리-활용)
7. [한국어 NLP & 데이터 스트리밍](#한국어-nlp--데이터-스트리밍)
8. [자동화 & 에이전트](#자동화--에이전트)
9. [문제 해결](#문제-해결)
10. [참고 자료](#참고-자료)

---

## 시작하기

### 시스템 요구 사항

| 항목 | 권장 버전 | 비고 |
|------|-----------|------|
| Python | 3.12.x | `uv`가 자동 설치 (macOS/Linux/Windows 지원) |
| uv | 최신 | [설치 가이드](https://docs.astral.sh/uv/getting-started/installation/) |
| Docker (선택) | 최신 | Langfuse/Phoenix 로컬 배포 시 |
| Ollama (선택) | 최신 | 폐쇄망/로컬 모델 사용 시 |

### 설치 옵션

#### PyPI
```bash
uv pip install evalvault
```

#### 소스 (권장)
```bash
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault
uv sync --extra dev        # 기본 개발 환경
uv sync --extra dev --extra analysis --extra korean --extra web   # 전체 기능
```

Extras 설명은 README 표를 참고하세요. `.python-version`이 Python 3.12를 고정하므로 추가 설치가 필요 없습니다.

---

## 환경 구성

### 프로젝트 초기화 (init)
빠르게 시작하려면 초기화 명령으로 기본 파일을 생성합니다.

```bash
uv run evalvault init
```

- `.env` 템플릿과 `sample_dataset.json`을 생성합니다.
- `dataset_templates/`에 JSON/CSV/XLSX 빈 템플릿을 생성합니다.
- `--output-dir`로 생성 위치를 바꿀 수 있습니다.
- `--skip-env`/`--skip-sample`/`--skip-templates`로 단계별 생성을 끌 수 있습니다.

### .env 작성
`cp .env.example .env` 후 아래 값을 채웁니다.

```bash
# 공통
EVALVAULT_PROFILE=dev              # config/models.yaml에 정의된 프로필
OPENAI_API_KEY=sk-...

# Langfuse (선택)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000

# Phoenix/OpenTelemetry (선택)
PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_SAMPLE_RATE=1.0

# React 프론트엔드에서 API 호출 시 (선택)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# vLLM(OpenAI-compatible) 사용 예
EVALVAULT_PROFILE=vllm
VLLM_BASE_URL=http://localhost:8001/v1
VLLM_MODEL=gpt-oss:120b
VLLM_EMBEDDING_MODEL=qwen3-embedding:0.6b
# 선택: VLLM_EMBEDDING_BASE_URL=http://localhost:8002/v1
```

Ollama를 사용할 경우 `OLLAMA_BASE_URL`, `OLLAMA_TIMEOUT`을 추가하고, 평가 전에 `ollama pull`로 모델을 내려받습니다.
Tool/function calling 지원 모델을 쓰려면 `.env`에 `OLLAMA_TOOL_MODELS`를 콤마로 지정합니다.
지원 여부는 `ollama show <model>` 출력의 `Capabilities`에 `tools`가 있는지 확인합니다.

> 참고: vLLM이 임베딩 엔드포인트(`/v1/embeddings`)를 제공하지 않으면 임베딩 기반 메트릭은 실패할 수 있습니다.
> 이 경우 `faithfulness`, `answer_relevancy` 등 LLM 기반 메트릭만 선택하거나 별도의 임베딩 서버를 지정하세요.

vLLM(OpenAI-compatible)을 사용할 경우 `EVALVAULT_PROFILE=vllm`로 전환하고,
`.env`에 `VLLM_BASE_URL`, `VLLM_MODEL`, `VLLM_EMBEDDING_MODEL`을 채웁니다.
임베딩 서버가 분리돼 있다면 `VLLM_EMBEDDING_BASE_URL`을 추가하세요.

### Ollama 모델 추가
Ollama는 **로컬에 내려받은 모델만** 목록에 노출됩니다. 다음 순서로 추가하세요.

1. **모델 내려받기**
   ```bash
   ollama pull gpt-oss:120b
   ollama pull gpt-oss-safeguard:120b
   ```
2. **목록 확인**
   ```bash
   ollama list
   ```
3. **EvalVault에서 선택**
   - Web UI: `Provider = ollama` 선택 후 모델 카드에서 선택
   - CLI: `config/models.yaml`의 프로필 모델을 변경하거나 `--profile`로 지정
4. **Tool 지원 모델 등록**
   - `ollama show <model>`로 `Capabilities: tools` 확인
   - 지원 모델은 `.env`의 `OLLAMA_TOOL_MODELS`에 콤마로 추가

미리 받아두면 좋은 모델:
`gpt-oss:120b`, `gpt-oss-safeguard:120b`, `gpt-oss-safeguard:20b`.

### 모델 프로필 관리
`config/models.yaml`은 프로필별 LLM/임베딩 구성을 정의합니다.

```yaml
profiles:
  dev:
    llm:
      provider: ollama
      model: gemma3:1b
    embedding:
      provider: ollama
      model: qwen3-embedding:0.6b
  openai:
    llm:
      provider: openai
      model: gpt-5-nano
    embedding:
      provider: openai
      model: text-embedding-3-small
  vllm:
    llm:
      provider: vllm
      model: gpt-oss:120b
    embedding:
      provider: vllm
      model: qwen3-embedding:0.6b
```

사용법:
- 환경 변수 `EVALVAULT_PROFILE` 설정
- 또는 CLI `--profile <name>` / `-p <name>` (예: dev, openai, vllm)

### 데이터셋 준비
EvalVault는 JSON/CSV/Excel을 지원합니다. JSON 예시는 아래와 같습니다.

```json
{
  "name": "insurance_qa_korean",
  "version": "1.0.0",
  "thresholds": {"faithfulness": 0.8},
  "test_cases": [
    {
      "id": "tc-001",
      "question": "보험 해지 환급금은 어떻게 계산하나요?",
      "answer": "...",
      "contexts": ["..."],
      "ground_truth": "..."
    }
  ]
}
```

CSV/Excel의 경우 `id,question,answer,contexts,ground_truth` 컬럼을 포함하고 `contexts`는 `|` 로 구분합니다. 대용량 파일은 Streaming Dataset Loader가 자동 적용됩니다.

#### 데이터셋 템플릿
빈 템플릿은 아래 위치에서 사용할 수 있습니다. 필요한 값만 채워 바로 사용할 수 있습니다.

- 프로젝트 초기화 시: `dataset_templates/` 폴더에 JSON/CSV/XLSX 템플릿 생성
- 문서 저장소: `docs/templates/dataset_template.json`
- 문서 저장소: `docs/templates/dataset_template.csv`
- 문서 저장소: `docs/templates/dataset_template.xlsx`

JSON 템플릿의 `thresholds` 값은 `null`로 비워져 있으므로 사용 전 숫자로 채우거나 삭제하세요.

---

## 핵심 워크플로

### CLI 실행
```bash
uv run evalvault run tests/fixtures/sample_dataset.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --tracker langfuse \
  --db evalvault.db
```

옵션 요약:
- `--metrics` : 쉼표로 구분된 메트릭 목록
- `--preset` : `quick`/`production`/`comprehensive` 프리셋 적용
- `--parallel / --batch-size (-b)` : 대량 데이터 병렬 평가
- `--tracker {none,langfuse,phoenix,mlflow}` : 추적기 선택
- `--db path/to.sqlite` : SQLite 저장소 지정
- `--use-domain-memory` : Domain Memory 기반 threshold/컨텍스트 보강 활성화

### 메트릭 가이드 {#metrics}

- `uv run evalvault metrics`로 사용 가능한 메트릭을 확인합니다.
- 기본 추천: `faithfulness` → `answer_relevancy` → `context_precision/context_recall`.
- `semantic_similarity`, `factual_correctness`는 ground truth가 있는 데이터셋에서만 사용하세요.

프리셋 예시:
```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --preset production
```

### 히스토리/비교/내보내기
```bash
uv run evalvault history --limit 20 --db evalvault.db
uv run evalvault compare <run_a> <run_b>
uv run evalvault export <run_id> -o run.json
```

### Web UI

#### Streamlit Web UI
```bash
uv run evalvault web --browser
```
Streamlit 앱에서 평가 실행, 파일 업로드, 히스토리 탐색, 보고서 생성이 가능합니다. `--profile` 및 `--tracker` 설정은 CLI와 동일하게 적용됩니다.
현재 Web UI 보고서는 기본/상세 템플릿과 LLM 보고서가 중심이며, 비교 템플릿과 Domain Memory 인사이트 패널은 준비 중입니다.
Dataset 선택 화면에서 JSON/CSV/XLSX 템플릿을 내려받아 바로 입력할 수 있습니다.

#### React Frontend (Vite)
```bash
# 1) API 서버 실행
uv run evalvault serve-api --reload

# 2) 프론트엔드 실행
cd frontend
npm install
npm run dev
```

- 기본 접속: http://localhost:5173
- API 기본: http://127.0.0.1:8000
- Vite dev 서버는 `/api`를 API로 프록시합니다.
- vLLM을 쓰려면 `.env`에 `EVALVAULT_PROFILE=vllm`과 `VLLM_*` 값을 설정하세요.
- API 주소를 바꾸려면 아래 중 하나를 사용하세요.
  - 프록시 유지: `VITE_API_PROXY_TARGET=http://localhost:8000`
  - 직접 호출: `VITE_API_BASE_URL=http://localhost:8000/api/v1`
- 직접 호출 시에는 API 서버 `.env`에 `CORS_ORIGINS`로 프론트 오리진을 추가합니다.

### 단계별 성능 평가 (stage)
단계별 실행 이벤트를 JSON/JSONL로 수집해 저장하고, 단계별 지표를 계산합니다.

```bash
uv run evalvault stage ingest examples/stage_events.jsonl --db evalvault.db
uv run evalvault stage summary run_20260103_001 --db evalvault.db
uv run evalvault stage compute-metrics run_20260103_001 \
  --thresholds-json config/stage_metric_thresholds.json \
  --thresholds-profile dev
```

- `output.attributes.citations`를 기록하면 `output.citation_count` 지표가 계산됩니다.
- 임계값은 `config/stage_metric_thresholds.json`의 `default`/`profiles`로 관리합니다.
- 지연 메트릭은 `duration_ms` 또는 `started_at`/`finished_at`이 있어야 계산됩니다.

실제 평가 파이프라인 실행 예시:
```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness \
  --profile dev \
  --db evalvault.db
```
- 평가 실행 후 `uv run evalvault history --limit 1 --db evalvault.db`로 `run_id`를 확인합니다.
- 동일한 `run_id`로 stage 이벤트를 기록하면 `uv run evalvault analyze <run_id> --playbook`에서
  단계별 개선 가이드까지 확인할 수 있습니다.

---

## 저장·추적

### SQLite/PostgreSQL
- 기본값은 `evalvault.db` (SQLite)
- PostgreSQL 사용 시 `.env`에 `POSTGRES_CONNECTION_STRING=postgresql://...` 또는 `POSTGRES_HOST/PORT/USER/PASSWORD`를 설정하고 `uv sync --extra postgres` 를 실행합니다.

### Langfuse
1. `docker compose -f docker-compose.langfuse.yml up -d`
2. http://localhost:3000 접속 후 프로젝트를 만들고 API 키를 발급
3. `.env` 에 키/호스트를 설정 후 `--tracker langfuse` 옵션 사용

Langfuse에는 테스트 케이스별 스팬과 메트릭 점수가 기록되며, Streamlit/CLI 히스토리에도 trace URL이 나타납니다.

---

## 관측성 & Phoenix

### 트레이싱 활성화
1. `uv sync --extra phoenix`
2. `.env` 에 `PHOENIX_ENABLED=true`, `PHOENIX_ENDPOINT`, `PHOENIX_SAMPLE_RATE`, `PHOENIX_API_TOKEN(선택)` 설정
3. CLI 실행 시 `--tracker phoenix` 또는 `--phoenix-max-traces` 사용

Phoenix 트레이스는 OpenTelemetry 스팬으로 생성되며 `tracker_metadata["phoenix"]["trace_url"]` 에 링크가 저장됩니다.

### Dataset/Experiment 동기화
```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --tracker phoenix \
  --phoenix-dataset insurance-qa-ko \
  --phoenix-dataset-description "보험 QA v2025.01" \
  --phoenix-experiment gemma3-ko-baseline \
  --phoenix-experiment-description "Gemma3 vs OpenAI 비교"
```
- `--phoenix-dataset` : EvalVault Dataset을 Phoenix Dataset으로 업로드
- `--phoenix-experiment` : Phoenix Experiment 생성 및 메트릭/Pass Rate/Domain Memory 메타데이터 포함
- 생성된 URL은 JSON 출력과 Web UI 히스토리에서 확인할 수 있습니다.

### 임베딩 분석 & 내보내기
Phoenix 12.27.0의 Embeddings Analysis 뷰는 드리프트/클러스터/3D 시각화를 제공합니다. 업로드된 Dataset/Experiment 화면에서 “Embeddings” 탭을 열면 EvalVault 질문/답변 벡터 및 Domain Memory 태그를 확인할 수 있습니다.

오프라인 분석이 필요하면 CLI로 내보내세요.
```bash
uv run evalvault phoenix export-embeddings \
  --dataset phoenix-dataset-id \
  --endpoint http://localhost:6006 \
  --output tmp/phoenix_embeddings.csv
```
UMAP/HDBSCAN 라이브러리가 없는 경우 자동으로 PCA/DBSCAN으로 대체합니다.

### Prompt Manifest 루프
Prompt Playground와 EvalVault 실행을 동기화하려면 `agent/prompts/prompt_manifest.json`과 전용 명령을 사용합니다.

1. **프롬프트 ↔ Phoenix ID 연결**
   ```bash
   uv run evalvault phoenix prompt-link agent/prompts/baseline.txt \
     --prompt-id pr-428 \
     --experiment-id exp-20250115 \
     --notes "Gemma3 베이스라인"
   ```
2. **Diff 확인**
   ```bash
   uv run evalvault phoenix prompt-diff \
     agent/prompts/baseline.txt agent/prompts/system.txt \
     --manifest agent/prompts/prompt_manifest.json --format table
   ```
3. **평가 실행에 Prompt 정보 주입**
   ```bash
   DATASET="tests/fixtures/e2e/insurance_qa_korean.json"
   uv run evalvault run "$DATASET" --metrics faithfulness \
     --profile prod \
     --tracker phoenix \
     --prompt-files agent/prompts/baseline.txt,agent/prompts/system.txt \
     --prompt-manifest agent/prompts/prompt_manifest.json
   ```

`tracker_metadata["phoenix"]["prompts"]` 에 파일 상태/체크섬/diff가 기록되어 Slack 릴리즈 노트, 히스토리, Web UI에 그대로 노출됩니다.

> **Tip**: Prompt Playground 연동 시에는 Phoenix tool-calling을 지원하는 `prod` 프로필(`gpt-oss-safeguard:20b`)을 사용하면 "does not support tools" 오류 없이 메타데이터가 기록됩니다.

### 드리프트 감시 & 릴리스 노트
- `scripts/ops/phoenix_watch.py` : Phoenix Dataset을 주기적으로 조회하여 `embedding_drift_score` 초과 시 Slack 알림 또는 `uv run evalvault gate <run_id>`/회귀 테스트 실행
  ```bash
  uv run python scripts/ops/phoenix_watch.py \
    --endpoint http://localhost:6006 \
    --dataset-id ds_123 \
    --drift-key embedding_drift_score \
    --drift-threshold 0.18 \
    --slack-webhook https://hooks.slack.com/services/... \
    --gate-command "uv run evalvault gate RUN_ID --format github-actions --db evalvault.db" \
    --run-regressions threshold \
    --regression-config config/regressions/default.json
  ```
- `scripts/reports/generate_release_notes.py` : `uv run evalvault run --output run.json` 결과를 Markdown/Slack 형식 릴리스 노트로 변환하고 Phoenix 링크를 삽입합니다.

---

## Domain Memory & 분석 기능 {#도메인-메모리-활용}
- `--use-domain-memory` : 평가 전 Domain Memory의 신뢰도로 메트릭 임계값을 자동 조정하고 관련 사실을 컨텍스트에 보강합니다.
- `MemoryBasedAnalysis` : `uv run evalvault analyze`에서 과거 LearningMemory와 현재 성능을 비교하여 추세/추천을 생성합니다. (Web UI 미노출)
- **Web UI 인사이트**: Domain Memory/MemoryBasedAnalysis 인사이트는 CLI 출력 기준으로만 제공됩니다.
- `ImprovementGuideService` : 규칙 기반 패턴 탐지 + LLM 인사이트를 결합해 우선순위가 매겨진 개선 액션을 제공합니다.
- `Analysis Pipeline` : `uv run evalvault pipeline analyze "요약해줘"` 형태로 12가지 의도를 분류하고 DAG 모듈을 실행합니다.

---

## 한국어 NLP & 데이터 스트리밍
- `uv sync --extra korean` 설치 시 Kiwi 기반 형태소 분석, BM25/Dense/Hybrid 검색기, 한국어 Faithfulness/Factual 검증기가 활성화됩니다.
- 대용량 CSV/JSON/Excel은 `StreamingDatasetLoader`가 청크 단위로 처리하여 메모리 사용량을 줄이고 진행률 콜백을 제공합니다 (`StreamingConfig.chunk_size`, `max_rows` 등 조정 가능).

---

## 자동화 & 에이전트
- `scripts/regression_runner.py` : JSON (`config/regressions/*.json`) 으로 정의된 회귀 스위트를 순차 실행하고 stdout/stderr를 캡처합니다.
- `uv run evalvault agent ...` : `agent/` 폴더의 claude-agent-sdk 기반 개발/운영 에이전트를 실행하여 아키텍처/관측성/테스트/문서 등을 자동 개선합니다. 에이전트 상태와 로그는 `agent/memory/` 하위에 저장되며, `AgentConfig` 는 `src/evalvault/config/agent_types.py` 에 정의되어 있습니다.

---

## 문제 해결

| 증상 | 해결 방법 |
|------|------------|
| `Command 'evalvault' not found` | `uv run evalvault ...` 또는 PATH에 `.venv/bin` 추가 |
| OpenAI 401 에러 | `.env` 의 `OPENAI_API_KEY` 확인, 프로필이 OpenAI인지 확인 |
| Ollama connection refused | `ollama serve` 실행 여부, `OLLAMA_BASE_URL` 확인 |
| Phoenix tracing 미동작 | `uv sync --extra phoenix`, `.env` 의 `PHOENIX_ENABLED` 등 확인, endpoint가 `/v1/traces` 로 끝나는지 검증 |
| Langfuse history 비어있음 | `--tracker langfuse` 사용 여부, Docker Compose 컨테이너 상태 확인 |
| Streamlit ImportError | `uv sync --extra web` 실행 |
| React 프론트 CORS 에러 | `CORS_ORIGINS`에 `http://localhost:5173` 추가 또는 Vite 프록시 사용, `VITE_API_BASE_URL` 확인 |

추가 이슈는 GitHub Issues 또는 `uv run evalvault config` 출력을 참고하세요.

---

## 참고 자료

### EvalVault 문서
- [README.md](https://github.com/ntts9990/EvalVault/blob/main/README.md) / [README.ko.md](../README.ko.md) - 프로젝트 개요
- [INDEX.md](../INDEX.md) - 전체 문서 인덱스
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - 아키텍처 가이드
- [CLI_GUIDE.md](CLI_GUIDE.md) - CLI 참조
- [ROADMAP.md](../status/ROADMAP.md) - 개발 로드맵
- [CHANGELOG.md](https://github.com/ntts9990/EvalVault/blob/main/CHANGELOG.md) - 변경 이력

### 튜토리얼
- [tutorials/01-quickstart.md](../tutorials/01-quickstart.md) - 5분 빠른 시작
- [tutorials/04-phoenix-integration.md](../tutorials/04-phoenix-integration.md) - Phoenix 통합
- [tutorials/05-korean-rag.md](../tutorials/05-korean-rag.md) - 한국어 RAG
- [tutorials/07-domain-memory.md](../tutorials/07-domain-memory.md) - Domain Memory

### 외부 리소스
- [Phoenix 공식 문서](https://docs.arize.com/phoenix)
- [Langfuse 공식 문서](https://langfuse.com/docs)
- [Ragas 공식 문서](https://docs.ragas.io/)

필요 시 `uv run evalvault --help`로 명령 전체 목록을 확인하세요.
