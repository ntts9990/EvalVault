# EvalVault 사용자 가이드

> RAG 시스템 품질 평가 · 분석 · 추적을 위한 종합 워크플로 가이드

이 문서는 README에서 다룬 간단한 소개를 넘어, 설치부터 Phoenix 연동·Domain Memory·자동화까지 모든 기능을 심층적으로 설명합니다.

---

## 목차

1. [핵심 워크플로](#핵심-워크플로) - 평가 → 자동 분석 → 보고서/아티팩트 저장 → 비교
2. [시작하기](#시작하기)
3. [환경 구성](#환경-구성)
4. [CLI 명령어 참조](#cli-명령어-참조)
5. [Web UI](#web-ui)
6. [분석 워크플로](#분석-워크플로)
7. [Domain Memory 활용](#domain-memory-활용)
8. [관측성 & Phoenix](#관측성--phoenix)
   - [Open RAG Trace 표준 연동](#open-rag-trace-표준-연동)
9. [프롬프트 관리](#프롬프트-관리)
10. [성능 튜닝](#성능-튜닝)
11. [메서드 플러그인](#메서드-플러그인)
12. [문제 해결](#문제-해결)
13. [참고 자료](#참고-자료)

---

## 핵심 워크플로

EvalVault의 가장 큰 장점은 **평가 → 자동 분석 → 보고서/아티팩트 저장 → 비교**가 하나의 `run_id`로 끊김 없이 이어져서, 재현성과 개선 루프가 매우 빠르다는 점입니다. 점수만 보는 게 아니라 통계·NLP·원인 분석까지 묶어서 바로 "왜 좋아졌는지/나빠졌는지"로 이어지는 게 핵심입니다.

### 초간단 실행 (CLI)

```bash
uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db \
  --auto-analyze
```

### 결과 확인 경로

평가 실행 후 자동 분석이 완료되면 다음 파일들이 생성됩니다:

- **요약 JSON**: `reports/analysis/analysis_<RUN_ID>.json`
- **Markdown 보고서**: `reports/analysis/analysis_<RUN_ID>.md`
- **아티팩트 인덱스**: `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`
- **노드별 결과**: `reports/analysis/artifacts/analysis_<RUN_ID>/<node_id>.json`

요약 JSON에는 `artifacts.dir`와 `artifacts.index`가 포함되어 있어 경로 조회가 쉽습니다.

### A/B 비교

두 실행 결과를 비교하려면:

```bash
uv run evalvault analyze-compare <RUN_A> <RUN_B> --db data/db/evalvault.db
```

결과는 `reports/comparison/comparison_<RUN_A>_<RUN_B>.md`에 저장됩니다.

### Web UI 연동

CLI와 Web UI가 동일한 DB를 사용하면 Web UI에서 바로 결과를 확인할 수 있습니다:

```bash
# Terminal 1: API 서버
uv run evalvault serve-api --reload

# Terminal 2: React 프론트엔드
cd frontend
npm install
npm run dev
```

동일한 DB(`data/db/evalvault.db`)를 사용하면 Web UI에서 바로 이어서 볼 수 있습니다.

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
uv sync --extra dev        # 전체 기능 포함 (dev 도구 + 모든 extras)
# 경량 설치 예시: uv sync --extra analysis
```

Phoenix 트레이싱은 `dev`에 포함되어 있습니다. 경량 설치라면 `--extra phoenix`를 추가하세요.

**Extras 설명**:

| Extra | 패키지 | 목적 |
|-------|--------|------|
| `analysis` | scikit-learn | 통계/NLP 분석 모듈 |
| `korean` | kiwipiepy, rank-bm25, sentence-transformers | 한국어 토크나이저 및 검색 |
| `postgres` | psycopg | PostgreSQL 저장소 지원 |
| `mlflow` | mlflow | MLflow 트래커 통합 |
| `phoenix` | arize-phoenix + OpenTelemetry exporters | Phoenix 트레이싱, 데이터셋/실험 동기화 |
| `anthropic` | anthropic | Anthropic LLM 어댑터 |
| `perf` | faiss-cpu, ijson | 대용량 데이터셋 성능 도우미 |
| `docs` | mkdocs, mkdocs-material, mkdocstrings | 문서 빌드 |

`.python-version`이 Python 3.12를 고정하므로 추가 설치가 필요 없습니다.

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
EVALVAULT_DB_PATH=data/db/evalvault.db     # SQLite 저장 경로 (API/CLI 공통)
EVALVAULT_MEMORY_DB_PATH=data/db/evalvault_memory.db  # 도메인 메모리 DB 경로
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
VLLM_MODEL=gpt-oss-120b
VLLM_EMBEDDING_MODEL=qwen3-embedding:0.6b
# 선택: VLLM_EMBEDDING_BASE_URL=http://localhost:8002/v1
```

OpenAI를 쓰지 않는다면 `OPENAI_API_KEY`는 비워둬도 됩니다.

### 초간단 시작 (Ollama 3줄)

```bash
cp .env.example .env
ollama pull gemma3:1b
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness \
  --db data/db/evalvault.db \
  --profile dev
```

Tip: `answer_relevancy` 등 임베딩 메트릭을 쓰려면 `qwen3-embedding:0.6b`도 내려받으세요.

### 초간단 시작 (vLLM 3줄)

```bash
cp .env.example .env
printf "\nEVALVAULT_PROFILE=vllm\nVLLM_BASE_URL=http://localhost:8001/v1\nVLLM_MODEL=gpt-oss-120b\n" >> .env
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness \
  --db data/db/evalvault.db
```

Tip: 임베딩 메트릭은 `VLLM_EMBEDDING_MODEL`과 `/v1/embeddings` 엔드포인트가 필요합니다.

Ollama를 사용할 경우 `OLLAMA_BASE_URL`, `OLLAMA_TIMEOUT`을 추가하고, 평가 전에 `ollama pull`로 모델을 내려받습니다.
Tool/function calling 지원 모델을 쓰려면 `.env`에 `OLLAMA_TOOL_MODELS`를 콤마로 지정합니다.
지원 여부는 `ollama show <model>` 출력의 `Capabilities`에 `tools`가 있는지 확인합니다.

> 참고: vLLM이 임베딩 엔드포인트(`/v1/embeddings`)를 제공하지 않으면 임베딩 기반 메트릭은 실패할 수 있습니다.
> 이 경우 `faithfulness`, `answer_relevancy` 등 LLM 기반 메트릭만 선택하거나 별도의 임베딩 서버를 지정하세요.

### 임베딩 엔드포인트 체크리스트

- 임베딩이 필요한 메트릭: `answer_relevancy`, `semantic_similarity`
- Ollama: `ollama pull qwen3-embedding:0.6b` 후 `ollama list`로 확인
- vLLM: `/v1/embeddings` 응답 확인
- 임베딩 서버가 분리돼 있으면 `VLLM_EMBEDDING_BASE_URL`을 설정

예시:
```bash
curl -s http://localhost:8001/v1/embeddings \
  -H "Authorization: Bearer local" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3-embedding:0.6b","input":"ping"}'
```

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
      model: gpt-oss-120b
    embedding:
      provider: vllm
      model: qwen3-embedding:0.6b
```

사용법:
- 환경 변수 `EVALVAULT_PROFILE` 설정
- 또는 CLI `--profile <name>` / `-p <name>` (예: dev, openai, vllm)

### 데이터셋 준비

EvalVault는 JSON/CSV/Excel을 지원합니다. **threshold는 데이터셋에 포함**되며,
값이 없으면 기본값 `0.7`을 사용합니다. Domain Memory를 켜면 신뢰도에 따라 자동 조정될 수 있습니다.

JSON 예시는 아래와 같습니다.

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

- `thresholds`: 메트릭별 pass 기준 (0.0~1.0)
- `ground_truth`: `context_precision`, `context_recall`, `factual_correctness`, `semantic_similarity`에 필요

CSV/Excel의 경우 `id,question,answer,contexts,ground_truth` 컬럼을 포함하고,
선택적으로 `threshold_*` 컬럼을 넣을 수 있습니다. `threshold_*` 값은 **첫 번째로 채워진 행 기준**으로
데이터셋 전체 임계값으로 사용됩니다. `contexts`는 JSON 배열 문자열 또는 `|` 로 구분합니다.
대용량 파일은 `--stream` 옵션으로 스트리밍 평가를 활성화하세요.

#### 데이터셋 템플릿

빈 템플릿은 아래 위치에서 사용할 수 있습니다. 필요한 값만 채워 바로 사용할 수 있습니다.

- 프로젝트 초기화 시: `dataset_templates/` 폴더에 JSON/CSV/XLSX 템플릿 생성
- 문서 저장소: `docs/templates/dataset_template.json`
- 문서 저장소: `docs/templates/dataset_template.csv`
- 문서 저장소: `docs/templates/dataset_template.xlsx`

JSON 템플릿의 `thresholds` 값은 `null`로 비워져 있으므로 사용 전 숫자로 채우거나 삭제하세요. CSV/Excel은 `threshold_*` 컬럼에 값을 채우면 동일하게 적용됩니다.

#### 실행 결과 엑셀(컬럼 설명)
- 시트/컬럼 상세: `docs/guides/EVALVAULT_RUN_EXCEL_SHEETS.md`

---

## CLI 명령어 참조

### 루트 명령어

#### `init` - 프로젝트 초기화

```bash
uv run evalvault init
uv run evalvault init --output-dir ./my-project
uv run evalvault init --skip-env --skip-sample
```

- `.env` 템플릿과 `sample_dataset.json`을 생성합니다.
- `dataset_templates/`에 JSON/CSV/XLSX 템플릿을 생성합니다.
- `--output-dir`로 생성 위치를 지정할 수 있습니다.
- `--skip-env`/`--skip-sample`/`--skip-templates`로 단계별 생성을 끌 수 있습니다.

#### `run` - 평가 실행

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --tracker phoenix \
  --profile dev \
  --db data/db/evalvault.db \
  --auto-analyze
```

**주요 옵션**:

- `--metrics, -m`: 쉼표로 구분된 메트릭 목록
- `--preset`: `quick`/`production`/`comprehensive` 프리셋 적용
- `--mode`: `simple`/`full` 실행 모드
- `--auto-analyze`: 평가 완료 후 통합 분석을 자동 실행하고 보고서를 저장
- `--analysis-json`: 자동 분석 JSON 결과 파일 경로 (기본값: `reports/analysis`)
- `--analysis-report`: 자동 분석 Markdown 보고서 경로 (기본값: `reports/analysis`)
- `--analysis-dir`: 자동 분석 결과 저장 디렉터리 (기본: `reports/analysis`)
- `--parallel, -P`: 병렬 평가 활성화
- `--batch-size, -b`: 배치 크기 (기본: 5)
- `--stream, -s`: 대용량 데이터셋 스트리밍 평가
- `--stream-chunk-size`: 스트리밍 청크 크기 (기본: 200)
- `--tracker, -t`: 추적기 선택 (`none`, `langfuse`, `mlflow`, `phoenix`)
- `--db, -D`: SQLite 저장소 지정
- `--use-domain-memory`: Domain Memory 기반 threshold/컨텍스트 보강 활성화
- `--memory-domain`: Domain Memory 도메인 이름
- `--memory-language`: Domain Memory 언어 코드 (기본: ko)
- `--augment-context`: Domain Memory 사실을 컨텍스트에 추가
- `--memory-db, -M`: Domain Memory DB 경로
- `--retriever, -r`: 리트리버 선택 (`bm25`, `dense`, `hybrid`, `graphrag`)
- `--retriever-docs`: 리트리버 문서 파일 (.json/.jsonl/.txt)
- `--kg, -k`: GraphRAG용 Knowledge Graph JSON 파일
- `--retriever-top-k`: 리트리버 Top-K (기본: 5)
- `--phoenix-dataset`: Phoenix Dataset 이름
- `--phoenix-experiment`: Phoenix Experiment 이름
- `--prompt-manifest`: Phoenix prompt manifest JSON 경로
- `--prompt-files`: 프롬프트 파일 목록 (쉼표로 구분)
- `--system-prompt`: 시스템 프롬프트 텍스트
- `--system-prompt-file`: 시스템 프롬프트 파일 경로
- `--ragas-prompts`: Ragas 프롬프트 오버라이드 YAML 파일

**Run Modes**:

| 모드 | 명령 | 동작 |
|------|------|------|
| Simple | `uv run evalvault run --mode simple DATASET.json`<br>`uv run evalvault run-simple DATASET.json` | `faithfulness,answer_relevancy` 메트릭 + Phoenix tracker 고정, Domain Memory/Prompt manifest 비활성 |
| Full | `uv run evalvault run --mode full DATASET.json`<br>`uv run evalvault run-full DATASET.json` | 모든 Typer 옵션(프로파일, Prompt manifest, Phoenix dataset/experiment, Domain Memory, streaming)을 노출 |

**Evaluation Presets**:

| 프리셋 | 설명 | 기본 메트릭 |
|--------|------|-------------|
| `quick` | 빠른 반복 평가 (parallel, batch_size=10) | `faithfulness` |
| `production` | 프로덕션 밸런스 (parallel, batch_size=5) | `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall` |
| `comprehensive` | 전체 메트릭 평가 (parallel, batch_size=3) | `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`, `factual_correctness`, `semantic_similarity` |

#### `pipeline` - 분석 파이프라인 실행

```bash
uv run evalvault pipeline analyze "요약해줘" --run-id <RUN_ID> --db data/db/evalvault.db
```

의도 분류 후 DAG 모듈을 실행하여 통계/NLP/인과 분석을 수행합니다.

#### `history` - 평가 이력 조회

```bash
uv run evalvault history --limit 20 --db data/db/evalvault.db
uv run evalvault history --mode simple --db data/db/evalvault.db
```

#### `analyze` - 단일 실행 분석

```bash
uv run evalvault analyze <RUN_ID> \
  --db data/db/evalvault.db \
  --nlp --causal \
  --output analysis.json \
  --report analysis.md
```

**옵션**:
- `--nlp, -N`: NLP 분석 포함
- `--causal, -c`: 인과 분석 포함
- `--playbook, -B`: 플레이북 기반 개선 분석 포함
- `--enable-llm, -L`: LLM 기반 인사이트 생성 활성화
- `--output, -o`: 출력 JSON 파일
- `--report, -r`: 출력 보고서 파일 (*.md or *.html)
- `--save, -S`: 분석 결과를 데이터베이스에 저장

#### `analyze-compare` - A/B 비교 분석

```bash
uv run evalvault analyze-compare <RUN_A> <RUN_B> \
  --db data/db/evalvault.db \
  --metrics faithfulness,answer_relevancy \
  --test t-test
```

기본 저장 위치:
- JSON 결과: `reports/comparison/comparison_<RUN_A>_<RUN_B>.json`
- Markdown 보고서: `reports/comparison/comparison_<RUN_A>_<RUN_B>.md`

비교 보고서는 **프롬프트 변경 요약 + 통계 비교 + 개선 제안**을 자동으로 포함합니다.

#### `generate` - 테스트셋 생성

```bash
uv run evalvault generate --from-docs documents.txt --output dataset.json
```

#### `gate` - 품질 게이트 검사

```bash
uv run evalvault gate <RUN_ID> --db data/db/evalvault.db --format github-actions
```

#### `agent` - 에이전트 관리

```bash
uv run evalvault agent list
uv run evalvault agent info <agent_type>
uv run evalvault agent run <agent_type> --project-dir .
```

#### `experiment` - 실험 관리

```bash
uv run evalvault experiment create --name "A/B Test" --db data/db/evalvault.db
uv run evalvault experiment add-group <EXPERIMENT_ID> --name "baseline"
uv run evalvault experiment add-run <EXPERIMENT_ID> <GROUP_NAME> <RUN_ID> --db data/db/evalvault.db
uv run evalvault experiment compare <EXPERIMENT_ID> --db data/db/evalvault.db
```

#### `config` - 설정 확인

```bash
uv run evalvault config
```

현재 설정 상태를 확인합니다.

#### `langfuse` - Langfuse 설정 확인

```bash
uv run evalvault langfuse check
```

#### `serve-api` - FastAPI 서버 실행

```bash
uv run evalvault serve-api --reload
```

### 서브앱 명령어

#### `kg` - Knowledge Graph

```bash
uv run evalvault kg build ./docs --output data/kg/knowledge_graph.json
uv run evalvault kg stats ./docs --use-llm --profile dev
```

#### `domain` - Domain Memory

```bash
uv run evalvault domain memory stats --db data/db/evalvault_memory.db
uv run evalvault domain memory ingest-embeddings phoenix.csv --domain insurance --language ko
```

#### `benchmark` - KMMLU 벤치마크 실행

lm-evaluation-harness를 사용하여 KMMLU(Korean MMLU) 벤치마크를 실행합니다.

```bash
# Ollama 백엔드로 실행
uv run evalvault benchmark kmmlu -s Insurance --backend ollama -m gemma3:1b

# Thinking 모델로 실행 (gpt-oss-safeguard, deepseek-r1 등)
uv run evalvault benchmark kmmlu -s Accounting --backend ollama -m gpt-oss-safeguard:20b --limit 10

# Phoenix 트레이싱 활성화
uv run evalvault benchmark kmmlu -s Insurance --backend ollama -m gemma3:1b --phoenix

# vLLM 백엔드로 실행
uv run evalvault benchmark kmmlu -s Insurance --backend vllm

# 여러 도메인 동시 실행
uv run evalvault benchmark kmmlu -s "Insurance,Finance" -m llama2

# 테스트용 샘플 제한
uv run evalvault benchmark kmmlu -s Insurance --limit 10 -o results.json
```

**주요 옵션**:
- `-s, --subjects`: 평가할 KMMLU 도메인 (Insurance, Finance, Accounting 등)
- `--backend`: 백엔드 선택 (`ollama`, `vllm`, `hf`, `openai`)
- `-m, --model`: 모델 이름
- `--limit`: 테스트 샘플 수 제한
- `--phoenix`: Phoenix 트레이싱 활성화
- `-o, --output`: 결과 JSON 파일 경로

**Thinking Model 지원**:
Ollama의 thinking 모델(예: `gpt-oss-safeguard:20b`, `deepseek-r1:*`)은 자동으로 감지됩니다.
- `max_gen_toks`가 8192로 증가 (thinking 토큰 포함)
- Stop sequence가 `["Q:", "\n\n\n"]`로 수정
- MCQ 응답에서 첫 번째 A/B/C/D를 자동 추출

#### `method` - 메서드 플러그인

```bash
uv run evalvault method list
uv run evalvault method run data.json --method my_team_method --metrics faithfulness
```

#### `phoenix` - Phoenix 연동

```bash
uv run evalvault phoenix export-embeddings --dataset ds_123 --output embeddings.csv
uv run evalvault phoenix prompt-link agent/prompts/baseline.txt --prompt-id pr-428
uv run evalvault phoenix prompt-diff baseline.txt system.txt --manifest manifest.json
```

#### `prompts` - 프롬프트 관리

```bash
uv run evalvault prompts show <RUN_ID> --db data/db/evalvault.db
uv run evalvault prompts diff <RUN_A> <RUN_B> --db data/db/evalvault.db
```

프롬프트 언어 기본값은 `ko`이며, 필요 시 API/SDK에서 다음 옵션으로 영어를 지정할 수 있습니다.
- 평가/요약 판정: `language="en"`
- 프롬프트 후보 평가: `prompt_language="en"`

#### `stage` - 단계별 성능 평가

```bash
uv run evalvault stage ingest examples/stage_events.jsonl --db data/db/evalvault.db
uv run evalvault stage summary <RUN_ID> --db data/db/evalvault.db
uv run evalvault stage compute-metrics <RUN_ID> --db data/db/evalvault.db
```

#### `debug` - 디버그 리포트

```bash
uv run evalvault debug report <RUN_ID> --db data/db/evalvault.db
```

### 공통 옵션

| 옵션 | 설명 | 사용 예 |
|------|------|---------|
| `--profile, -p` | `config/models.yaml`에 정의된 프로필을 적용합니다. | `uv run evalvault run dataset.json -p dev` |
| `--db, -D` | 평가 결과를 저장할 SQLite 경로입니다. 기본값은 `EVALVAULT_DB_PATH` 또는 `data/db/evalvault.db`. | `uv run evalvault history -D reports/evalvault.db` |
| `--memory-db, -M` | 도메인 메모리 SQLite 경로입니다. 기본값은 `EVALVAULT_MEMORY_DB_PATH` 또는 `data/db/evalvault_memory.db`. | `uv run evalvault domain memory stats -M data/memory.db` |

---

## Web UI

### 실행 방법

```bash
# Terminal 1: API 서버
uv run evalvault serve-api --reload

# Terminal 2: React 프론트엔드
cd frontend
npm install
npm run dev
```

- 기본 접속: http://localhost:5173
- API 기본: http://127.0.0.1:8000
- Vite dev 서버는 `/api`를 API로 프록시합니다.

### 주요 기능

- **Evaluation Studio**: 데이터셋 업로드, 평가 실행, 결과 확인
- **Analysis Lab**: 분석 파이프라인 실행, 결과 저장/불러오기
- **Reports**: 평가 결과 보고서, 히스토리, 비교 뷰

### Web UI와 CLI 연동

CLI와 Web UI가 동일한 DB(`--db` 또는 `EVALVAULT_DB_PATH`)를 사용하면:
- CLI에서 실행한 평가 결과를 Web UI에서 바로 확인 가능
- Web UI에서 실행한 평가 결과를 CLI `history` 명령으로 확인 가능
- 분석 결과도 양쪽에서 공유

### 보고서 언어 옵션

LLM 보고서는 기본 한국어이며, 필요 시 영어로 요청할 수 있습니다.

- `GET /api/v1/runs/{run_id}/report?language=en` (기본값: `ko`)

### 피드백 집계 규칙

Web UI의 별점/Thumb 피드백 집계는 다음 규칙을 따릅니다.

- 집계 기준: 동일 `rater_id` + `test_case_id`의 **최신 피드백만** 반영
- 취소(`thumb_feedback=none` 또는 빈 값)는 집계에서 제외

---

## 분석 워크플로

### 자동 분석 (옵션 방식)

평가 완료 후 자동으로 분석을 실행하려면 `--auto-analyze` 옵션을 사용합니다:

```bash
uv run evalvault run data.json \
  --metrics faithfulness,answer_relevancy \
  --db data/db/evalvault.db \
  --auto-analyze
```

### 기본 저장 위치

- JSON 결과: `reports/analysis/analysis_<run_id>.json`
- Markdown 보고서: `reports/analysis/analysis_<run_id>.md`
- 아티팩트 인덱스: `reports/analysis/artifacts/analysis_<run_id>/index.json`
- 노드별 결과: `reports/analysis/artifacts/analysis_<run_id>/<node_id>.json`

### 저장 위치 커스터마이즈

```bash
uv run evalvault run data.json \
  --db data/db/evalvault.db \
  --auto-analyze \
  --analysis-dir reports/custom \
  --analysis-json reports/custom/run_001.json \
  --analysis-report reports/custom/run_001.md
```

### 단일 실행 분석 (수동)

```bash
uv run evalvault analyze RUN_ID \
  --db data/db/evalvault.db \
  --nlp --causal
```

필요 시 `--output`, `--report`로 파일 저장 가능합니다.

### A/B 직접 비교 분석

```bash
uv run evalvault analyze-compare RUN_A RUN_B \
  --db data/db/evalvault.db \
  --metrics faithfulness,answer_relevancy \
  --test t-test
```

기본 저장 위치:
- JSON 결과: `reports/comparison/comparison_<run_a>_<run_b>.json`
- Markdown 보고서: `reports/comparison/comparison_<run_a>_<run_b>.md`

비교 보고서는 **프롬프트 변경 요약 + 통계 비교 + 개선 제안**을 자동으로 포함합니다.

### 분석 결과에 포함되는 내용

- **통계 요약**: 평균/분산/상관관계/통과율
- **Ragas 요약**: 메트릭별 평균, 케이스별 점수
- **저성과 케이스**: 낮은 점수 샘플, 우선순위 케이스
- **진단/원인 분석**: 문제 원인 가설 + 개선 힌트
- **패턴/트렌드**: 키워드/질문 유형 패턴, 실행 이력 추세
- **A/B 변경 사항**: 시스템 프롬프트, Ragas 프롬프트, 모델/옵션 차이
- **LLM 종합 보고서**: 원인 분석 + 개선 방향 + 다음 실험 제안

### 평가 → 분석 전체 흐름

1. **평가 실행**
   - `evalvault run data.json --db ...`
2. **자동 분석 (옵션)**
   - `--auto-analyze`로 즉시 보고서 생성
3. **추가 분석**
   - 필요 시 `evalvault analyze`로 상세 분석
4. **A/B 비교**
   - `evalvault analyze-compare`로 비교 보고서 생성
5. **프롬프트/메트릭 개선**
   - 보고서의 개선 제안을 반영해 다음 실행

### 품질 확보 팁

- A/B 비교는 **데이터셋 동일** 조건에서 수행하세요.
- 프롬프트 변경은 프롬프트 관리 섹션의 흐름대로 스냅샷 저장하세요.
- 비교 결과가 애매하면 샘플 수를 늘리고 재실행하세요.

---

## Domain Memory 활용

Domain Memory는 과거 평가 결과에서 도메인 지식/패턴을 축적하여 다음 평가에 활용하는 시스템입니다.

### 기본 사용법

```bash
uv run evalvault run data.json \
  --metrics faithfulness,answer_relevancy \
  --use-domain-memory \
  --memory-domain insurance \
  --memory-language ko \
  --augment-context \
  --db data/db/evalvault.db
```

**옵션 설명**:
- `--use-domain-memory`: Domain Memory 활성화
- `--memory-domain`: 도메인 이름 (기본값: 데이터셋 메타데이터에서 추출)
- `--memory-language`: 언어 코드 (기본: ko)
- `--augment-context`: 관련 사실을 컨텍스트에 추가
- `--memory-db, -M`: Domain Memory DB 경로

### 동작 원리

1. **Threshold 자동 조정**: Domain Memory의 신뢰도 점수에 따라 메트릭 임계값을 자동 조정
2. **컨텍스트 보강**: 각 테스트 케이스의 질문으로 관련 사실을 검색하여 컨텍스트에 추가
3. **학습**: 평가 완료 후 Domain Learning Hook이 결과에서 사실/패턴/행동을 추출하여 저장

### MemoryBasedAnalysis

과거 학습 메모리와 현재 결과를 비교하여 추세와 추천을 생성합니다:

```bash
uv run evalvault analyze <RUN_ID> \
  --db data/db/evalvault.db \
  --use-domain-memory
```

**제한 사항**:
- Streaming 모드(`--stream`)에서는 Domain Memory를 사용할 수 없습니다.
- Web UI 인사이트: Domain Memory/MemoryBasedAnalysis 인사이트는 CLI 출력 기준으로만 제공됩니다.

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

- `--phoenix-dataset`: EvalVault Dataset을 Phoenix Dataset으로 업로드
- `--phoenix-experiment`: Phoenix Experiment 생성 및 메트릭/Pass Rate/Domain Memory 메타데이터 포함
- 생성된 URL은 JSON 출력과 Web UI 히스토리에서 확인할 수 있습니다.

### Open RAG Trace 표준 연동

외부/내부 RAG 시스템을 EvalVault·Phoenix와 동일한 스키마로 연결하려면
OpenTelemetry + OpenInference 기반의 **Open RAG Trace 표준**을 따르세요.

**핵심 규칙**
- `rag.module`로 모듈 단위를 식별 (retrieve/llm/eval 등)
- 로그는 span event로 흡수
- 표준 필드 외 데이터는 `custom.*`로 보존
- 객체 배열은 `*_json`으로 직렬화 (`retrieval.documents_json` 등)

**연동 순서**
1. Collector 실행
   ```bash
   docker run --rm \
     -p 4317:4317 -p 4318:4318 \
     -e PHOENIX_OTLP_ENDPOINT=http://host.docker.internal:6006 \
     -v "$(pwd)/scripts/dev/otel-collector-config.yaml:/etc/otelcol/config.yaml" \
     otel/opentelemetry-collector:latest \
     --config=/etc/otelcol/config.yaml
   ```
2. 계측 래퍼 적용
   - `OpenRagTraceAdapter`, `trace_module`, `install_open_rag_log_handler`
   - `build_retrieval_attributes`, `build_llm_attributes` 등 헬퍼 사용
3. OTLP 전송
   - Collector: `http://localhost:4318/v1/traces`
   - Phoenix 직접: `http://localhost:6006/v1/traces`
4. 검증 스크립트 실행
   ```bash
   python3 scripts/dev/validate_open_rag_trace.py --input traces.json
   ```

**관련 문서**
- `docs/architecture/open-rag-trace-spec.md`
- `docs/architecture/open-rag-trace-collector.md`
- `docs/guides/OPEN_RAG_TRACE_INTERNAL_ADAPTER.md`
- `docs/guides/OPEN_RAG_TRACE_SAMPLES.md`

### 임베딩 분석 & 내보내기

Phoenix 12.27.0의 Embeddings Analysis 뷰는 드리프트/클러스터/3D 시각화를 제공합니다. 업로드된 Dataset/Experiment 화면에서 "Embeddings" 탭을 열면 EvalVault 질문/답변 벡터 및 Domain Memory 태그를 확인할 수 있습니다.

오프라인 분석이 필요하면 CLI로 내보내세요:
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

- `scripts/ops/phoenix_watch.py`: Phoenix Dataset을 주기적으로 조회하여 `embedding_drift_score` 초과 시 Slack 알림 또는 `uv run evalvault gate <run_id>`/회귀 테스트 실행
  ```bash
  uv run python scripts/ops/phoenix_watch.py \
    --endpoint http://localhost:6006 \
    --dataset-id ds_123 \
    --drift-key embedding_drift_score \
    --drift-threshold 0.18 \
    --slack-webhook https://hooks.slack.com/services/... \
    --gate-command "uv run evalvault gate RUN_ID --format github-actions --db data/db/evalvault.db" \
    --run-regressions threshold \
    --regression-config config/regressions/default.json
  ```
- `scripts/reports/generate_release_notes.py`: `uv run evalvault run --output run.json` 결과를 Markdown/Slack 형식 릴리스 노트로 변환하고 Phoenix 링크를 삽입합니다.

---

## 프롬프트 관리

EvalVault는 **시스템 프롬프트**와 **Ragas 메트릭 프롬프트**를 실행 단위로 스냅샷 저장하고,
실행 간 변경점을 비교할 수 있도록 설계되어 있습니다.

### 저장되는 프롬프트 범위

- **시스템 프롬프트**: 대상 LLM에 실제로 주입한 시스템 메시지
- **Ragas 메트릭 프롬프트**: faithfulness 등 평가 메트릭용 프롬프트 오버라이드
- **Prompt Set 스냅샷**: 위 프롬프트들을 `run_id`와 함께 DB에 저장 (비교/회귀 추적용)

> **중요**: Prompt Set 저장은 `--db` 옵션이 있어야 동작합니다.

### 시스템 프롬프트 등록

#### 텍스트 직접 입력

```bash
uv run evalvault run data.json \
  --system-prompt "당신은 보험 약관 전문가입니다..." \
  --prompt-set-name "sys-v2" \
  --db data/db/evalvault.db
```

#### 파일로 입력

```bash
uv run evalvault run data.json \
  --system-prompt-file agent/prompts/system.txt \
  --system-prompt-name sys-v2 \
  --prompt-set-name "sys-v2" \
  --db data/db/evalvault.db
```

### Ragas 프롬프트 YAML 오버라이드

#### YAML 예시

```yaml
faithfulness: |
  너는 답변의 근거가 컨텍스트에 있는지 평가한다...

answer_relevancy: |
  질문 의도와 답변의 연관성을 평가한다...
```

#### 실행 예시

```bash
uv run evalvault run data.json \
  --ragas-prompts config/ragas_prompts.yaml \
  --prompt-set-name "ragas-v3" \
  --db data/db/evalvault.db
```

> YAML에 있는 메트릭이 `--metrics`에 없으면 경고가 출력됩니다.

### 저장된 프롬프트 확인/비교

#### 스냅샷 보기

```bash
uv run evalvault prompts show RUN_ID --db data/db/evalvault.db
```

#### 두 실행 간 비교

```bash
uv run evalvault prompts diff RUN_A RUN_B --db data/db/evalvault.db
```

#### 비교 분석 보고서에서 자동 반영

```bash
uv run evalvault analyze-compare RUN_A RUN_B --db data/db/evalvault.db
```

`analyze-compare` 결과에는 **프롬프트 변경 요약 + 메트릭 변화**가 함께 포함됩니다.

### 운영 팁

- **Prompt Set 이름 규칙화**: `sys-v3`, `ragas-v2`, `release-2025-02` 등으로 관리
- **A/B 비교 시 데이터셋 고정**: 데이터셋이 바뀌면 비교 해석이 왜곡됩니다
- **Prompt Manifest 활용**: Phoenix Prompt Playground와 연결하려면 관측성 & Phoenix 섹션의 Prompt Manifest 절을 참고하세요.

---

## 성능 튜닝

### TL;DR (우선순위 요약)

1. **병렬 평가 + 배치 크기 조절**로 처리량 확보
2. **느린 메트릭 제외** (특히 `factual_correctness`, `semantic_similarity`)
3. **빠른 LLM/임베딩 모델**로 교체 (프로필/옵션 조정)
4. **컨텍스트 길이/개수 줄이기** (retriever/top_k, 데이터 전처리)
5. **부가 기능 끄기** (Domain Memory, Tracker)

### 병렬 평가와 배치 크기

EvalVault는 배치 단위 `asyncio.gather`로 병렬 평가를 수행합니다.
동시성은 `batch_size`가 결정하며, `parallel`은 병렬 활성화 스위치입니다.

**CLI 예시**
```bash
uv run evalvault run data.json --metrics faithfulness --parallel --batch-size 10
```

> 권장: 로컬 Ollama는 5~10, 외부 API는 레이트리밋에 맞춰 단계적으로 증가

### 메트릭 최소화 (속도 영향 큼)

현재 EvalVault는 메트릭을 **순차적으로 평가**합니다.
필요한 메트릭만 선택해 호출 수를 줄이는 것이 가장 큰 효과를 냅니다.

| 메트릭 | 호출 성격 | 속도 영향 |
|--------|-----------|-----------|
| `faithfulness` | LLM 호출 | 중 |
| `answer_relevancy` | LLM + 임베딩 | 중~높음 |
| `context_precision` | LLM | 중 |
| `context_recall` | LLM | 중 |
| `semantic_similarity` | 임베딩 | 높음 (임베딩 모델 속도 영향) |
| `factual_correctness` | LLM 다중 호출 (claim 분해/검증) | 매우 높음 |
| 커스텀 메트릭 | 규칙 기반/비LLM | 낮음 |

> 빠른 반복 평가 단계에서는 `faithfulness` 단일 메트릭만으로 시작하세요.

### LLM/임베딩 모델 선택

평가 속도는 모델이 좌우합니다. 빠른 모델을 별도 프로필로 두고 사용하세요.

```bash
# 빠른 모델 프로필로 전환
EVALVAULT_PROFILE=dev uv run evalvault run data.json --metrics faithfulness
```

**Ollama**:
- `config/models.yaml`에서 `think_level`을 낮추거나 제거하면 속도 개선
- 임베딩 모델은 소형 모델(`qwen3-embedding:0.6b` 등) 권장

### 컨텍스트 길이/개수 줄이기

프롬프트 토큰이 늘어날수록 평가 속도는 급격히 느려집니다.

- 데이터셋의 `contexts`를 **짧게 유지**
- `retriever`를 사용할 경우 `top_k`를 낮춤
- 중복/불필요한 컨텍스트 제거

**CLI 예시**
```bash
uv run evalvault run data.json \
  --metrics faithfulness \
  --retriever bm25 \
  --retriever-docs docs.jsonl \
  --retriever-top-k 3
```

> Web UI는 현재 `top_k=5` 고정이므로, 더 낮추려면 CLI 또는 API 사용이 필요합니다.

### 부가 기능 비활성화

아래 기능은 평가 속도에 직접적인 부하를 더합니다.

- Domain Memory (`--use-domain-memory` OFF)
- Tracker (`--tracker none`)
- Phoenix 자동 트레이싱 (`PHOENIX_ENABLED=false`)
- Retriever (컨텍스트가 이미 있으면 비활성화)

---

## 메서드 플러그인

EvalVault는 메서드 플러그인 인터페이스를 지원하여 팀별 RAG 파이프라인을 공유 기본 데이터셋에 대해 실행하고,
표준 메트릭 및 분석 도구로 출력을 평가할 수 있습니다.

### 소스

- **내부 레지스트리**: `config/methods.yaml`
- **외부 패키지**: `evalvault.methods` entry points

### 기본 데이터셋 템플릿

`dataset_templates/method_input_template.json`의 질문 우선 템플릿을 사용하세요.
`question/ground_truth/contexts/metadata`만 필요하며 팀 간 안정적으로 유지됩니다.

### 내부 레지스트리 예시

```yaml
methods:
  baseline_oracle:
    class_path: "evalvault.adapters.outbound.methods.baseline_oracle:BaselineOracleMethod"
    description: "Use ground truth as the answer when available."
    tags: ["baseline", "oracle"]
```

### Entry Point 예시 (외부 패키지)

```toml
[project.entry-points."evalvault.methods"]
my_team_method = "my_team_pkg.methods:MyTeamMethod"
```

`examples/method_plugin_template`에서 작동하는 스캐폴드를 참고하세요.

### 외부 명령 (의존성 격리)

메서드 의존성이 충돌할 때 별도 venv/컨테이너에서 실행합니다.
`config/methods.yaml`에 명령 기반 메서드를 구성하세요:

```yaml
methods:
  team_method_external:
    runner: external
    command: "bash -lc 'cd ../team_method && uv run python -m team_method.run --input \"$EVALVAULT_METHOD_INPUT\" --output \"$EVALVAULT_METHOD_OUTPUT\"'"
    shell: true
    timeout_seconds: 3600
    description: "Team method executed in its own env"
```

명령에 전달되는 환경 변수:
- `EVALVAULT_METHOD_INPUT`: 기본 데이터셋 경로
- `EVALVAULT_METHOD_OUTPUT`: 출력 JSON 경로 (메서드 출력)
- `EVALVAULT_METHOD_DOCS`: 문서 경로 (제공된 경우)
- `EVALVAULT_METHOD_CONFIG`: 메서드 설정 경로 (제공된 경우)
- `EVALVAULT_METHOD_RUN_ID`: 실행 ID
- `EVALVAULT_METHOD_ARTIFACTS`: 아티팩트 디렉터리

외부 출력 형식:
```json
{
  "outputs": [
    {
      "id": "tc-001",
      "answer": "...",
      "contexts": ["..."],
      "metadata": {},
      "retrieval_metadata": {}
    }
  ]
}
```

`command`에서 지원되는 플레이스홀더:
`{input}`, `{output}`, `{docs}`, `{config}`, `{run_id}`, `{artifacts}`, `{method}`

### CLI 사용법

```bash
# 사용 가능한 메서드 목록
evalvault method list

# 메서드 실행 및 평가
evalvault method run data/base_questions.json --method my_team_method --metrics faithfulness

# 평가 없이 데이터셋 출력 저장
evalvault method run data/base_questions.json --method my_team_method --no-evaluate
```

선택적 입력:
- `--docs` for domain corpus (json/jsonl/txt)
- `--method-config` or `--method-config-file` for method parameters

### 로깅 & 출력

- 메서드 출력: `reports/experiments/<method>/<run_id>/method_outputs.json`
- 평가 데이터셋: `reports/experiments/<method>/<run_id>/dataset.json`
- 평가 결과: `--db`가 활성화되면 `data/db/evalvault.db`에 저장
- 실행 메타데이터: 메서드 이름/버전/설정 + 런타임 정보가 tracker metadata에 저장

---

## 저장·추적

### SQLite/PostgreSQL

- 기본값은 `data/db/evalvault.db` (SQLite)
- PostgreSQL 사용 시 `.env`에 `POSTGRES_CONNECTION_STRING=postgresql://...` 또는 `POSTGRES_HOST/PORT/USER/PASSWORD`를 설정하고 `uv sync --extra postgres` 를 실행합니다.
- 분석 파이프라인 저장 결과는 `pipeline_results` 테이블에 기록됩니다.

### Langfuse

1. `docker compose -f docker-compose.langfuse.yml up -d`
2. http://localhost:3000 접속 후 프로젝트를 만들고 API 키를 발급
3. `.env` 에 키/호스트를 설정 후 `--tracker langfuse` 옵션 사용

Langfuse에는 테스트 케이스별 스팬과 메트릭 점수가 기록되며, Web UI/CLI 히스토리에도 trace URL이 나타납니다.

---

## 문제 해결

| 증상 | 해결 방법 |
|------|------------|
| `Command 'evalvault' not found` | `uv run evalvault ...` 또는 PATH에 `.venv/bin` 추가 |
| OpenAI 401 에러 | `.env` 의 `OPENAI_API_KEY` 확인, 프로필이 OpenAI인지 확인 |
| Ollama connection refused | `ollama serve` 실행 여부, `OLLAMA_BASE_URL` 확인 |
| Phoenix tracing 미동작 | `uv sync --extra phoenix`, `.env` 의 `PHOENIX_ENABLED` 등 확인, endpoint가 `/v1/traces` 로 끝나는지 검증 (`/v1/traces`는 POST 전용이므로 GET 405는 정상) |
| Langfuse history 비어있음 | `--tracker langfuse` 사용 여부, Docker Compose 컨테이너 상태 확인 |
| Web UI 접속 불가 | API 서버(`evalvault serve-api`)와 프론트(`npm run dev`)가 켜져 있는지 확인 |
| React 프론트 CORS 에러 | `CORS_ORIGINS`에 `http://localhost:5173` 추가 또는 Vite 프록시 사용, `VITE_API_BASE_URL` 확인 |

추가 이슈는 GitHub Issues 또는 `uv run evalvault config` 출력을 참고하세요.

---

## 참고 자료

### EvalVault 문서
- [README.md](../../README.md) - 프로젝트 개요
- [INDEX.md](../INDEX.md) - 문서 허브
- [STATUS.md](../STATUS.md) - 1페이지 상태 요약
- [ROADMAP.md](../ROADMAP.md) - 공개 로드맵
- [DEV_GUIDE.md](DEV_GUIDE.md) - 개발/테스트 루틴
- [CLI_MCP_PLAN.md](CLI_MCP_PLAN.md) - CLI→MCP 이식 계획
- [new_whitepaper/INDEX.md](../new_whitepaper/INDEX.md) - 개발 백서(설계/운영/품질 기준)
- [open-rag-trace-spec.md](../architecture/open-rag-trace-spec.md) - Open RAG Trace 표준
- [open-rag-trace-collector.md](../architecture/open-rag-trace-collector.md) - Collector 구성 가이드
- [OPEN_RAG_TRACE_INTERNAL_ADAPTER.md](OPEN_RAG_TRACE_INTERNAL_ADAPTER.md) - 내부 시스템 계측
- [CHANGELOG.md](https://github.com/ntts9990/EvalVault/blob/main/CHANGELOG.md) - 변경 이력

### 외부 리소스
- [Phoenix 공식 문서](https://docs.arize.com/phoenix)
- [Langfuse 공식 문서](https://langfuse.com/docs)
- [Ragas 공식 문서](https://docs.ragas.io/)

필요 시 `uv run evalvault --help`로 명령 전체 목록을 확인하세요.
