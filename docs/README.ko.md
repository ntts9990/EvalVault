# EvalVault (한국어)

> RAG(Retrieval-Augmented Generation) 시스템의 성능을 측정하고 분석하는 평가 전문 도구

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![Ragas](https://img.shields.io/badge/Ragas-v1.0-green.svg)](https://docs.ragas.io/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](../LICENSE.md)
[![PSF Supporting Member](https://img.shields.io/badge/PSF-Supporting%20Member-3776AB?logo=python&logoColor=FFD343)](https://www.python.org/psf/membership/)

English version? See the root [README.md](../README.md).

---

## 개요

EvalVault는 구조화된 데이터셋을 Ragas v1.0 메트릭에 연결해 Typer CLI로 평가를 실행하고,
SQLite 또는 Langfuse에 결과를 저장합니다. OpenAI, Ollama, 폐쇄망 프로필을 모두 지원하며
재현 가능한 RAG 평가 파이프라인을 제공합니다.

## 주요 특징

- Typer 기반 CLI로 평가·비교·내보내기를 한 번에 수행
- OpenAI/Ollama 프로필 기반 의존성 주입
- Langfuse 연동으로 트레이스 단위 분석
- Phoenix 연동으로 OpenTelemetry 트레이싱·데이터셋/실험 동기화·임베딩 분석·프롬프트 manifest 추적 제공
- Prompt Playground 루프로 Phoenix Prompt ID/차이를 EvalVault 실행과 동기화
- JSON/CSV/Excel 데이터 로더
- Linux·macOS·Windows 호환
- **Web UI**: Streamlit 대시보드로 평가, 이력, 리포트 관리
- **Korean NLP**: Kiwi 형태소 분석, BM25/Dense/Hybrid 검색
- **Domain Memory**: 평가 결과에서 학습하여 지속적 개선 (threshold 자동 조정, 컨텍스트 보강, 트렌드 분석)
- **NLP Analysis**: 텍스트 통계, 질문 유형 분류, 키워드 추출
- **Causal Analysis**: 인과 관계 분석 및 근본 원인 파악
- **Knowledge Graph**: 문서에서 자동으로 테스트셋 생성
- **Analysis Pipeline**: DAG 기반 쿼리 분석 및 의도 분류

## 빠른 시작

```bash
# PyPI를 통한 설치
uv pip install evalvault
evalvault run data.json --metrics faithfulness

# 또는 소스에서 설치 (개발 환경 권장)
git clone https://github.com/ntts9990/EvalVault.git && cd EvalVault
uv sync --extra dev
uv run evalvault run tests/fixtures/sample_dataset.json --metrics faithfulness
```

> **왜 uv인가?** EvalVault는 빠르고 안정적인 의존성 관리를 위해 [uv](https://docs.astral.sh/uv/)를 사용합니다. 소스에서 실행할 때는 모든 명령어 앞에 `uv run`을 붙여야 합니다.

## 핵심 기능

- Ragas v1.0 기반 6가지 표준 메트릭 + 도메인 특화 메트릭
- 버전 메타데이터를 포함한 JSON/CSV/Excel 데이터셋
- SQLite + PostgreSQL + Langfuse/MLflow 자동 결과 저장
- Phoenix 통합: OpenTelemetry 트레이싱, `--phoenix-max-traces`, 데이터셋/실험 동기화, 임베딩 분석, Prompt manifest/diff 워크플로
- Prompt manifest + diff 명령으로 Phoenix Prompt ID를 agent 파일 및 트래커 메타데이터에 기록
- Ollama 프로필을 통한 폐쇄망/온프레미스 지원
- 간결한 CLI UX
- **Web UI**: Streamlit 대시보드로 평가, 이력, 리포트 생성
- **Korean NLP**: Kiwi 형태소 분석, BM25/Dense/Hybrid 검색
- **Domain Memory**: 평가 결과에서 학습하여 지속적 개선 (threshold 자동 조정, 컨텍스트 보강, 트렌드 분석)
- **NLP Analysis**: 텍스트 통계, 질문 유형 분류, 키워드 추출, 토픽 클러스터링
- **Causal Analysis**: 인과 관계 분석 및 근본 원인 파악, 개선 제안 생성
- **Knowledge Graph**: 문서에서 자동으로 테스트셋 생성
- **Experiment Management**: A/B 테스트 및 그룹 간 메트릭 비교
- **Analysis Pipeline**: DAG 기반 쿼리 분석 (12가지 의도 분류)

## 설치

### PyPI (권장)

```bash
uv pip install evalvault
```

### 개발 환경 (소스에서 설치)

```bash
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault

# 기본 개발 환경
uv sync --extra dev

# 전체 기능 개발 환경 (권장)
uv sync --extra dev --extra analysis --extra korean --extra web
```

**선택적 Extras:**
| Extra | 패키지 | 용도 |
|-------|--------|------|
| `korean` | kiwipiepy, rank-bm25, sentence-transformers | 한국어 NLP (형태소 분석/임베딩) |
| `analysis` | scikit-learn | 통계/NLP 분석 파이프라인 |
| `web` | streamlit, plotly | Streamlit Web UI 대시보드 |
| `postgres` | psycopg | PostgreSQL 저장소 지원 |
| `mlflow` | mlflow | MLflow 트래커 연동 |
| `phoenix` | arize-phoenix, openinference-instrumentation-langchain, opentelemetry-sdk, opentelemetry-exporter-otlp | Phoenix 트레이싱/데이터셋 동기화/임베딩 분석 |
| `anthropic` | anthropic | Anthropic LLM 어댑터 |

> **참고**: `.python-version` 파일이 Python 3.12를 지정합니다. uv가 Python 3.12를 자동으로 다운로드하여 사용합니다.

## Phoenix 옵저버빌리티 (트레이싱 + 실험)

EvalVault는 `arize-phoenix` 12.27.0 기준으로 검증된 Phoenix 연동 기능을 제공합니다. `uv sync --extra phoenix`로 OpenTelemetry exporter와 Phoenix 클라이언트를 설치한 뒤 `.env`에 다음 값을 설정하세요.

```bash
PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_API_TOKEN= # Phoenix Cloud 사용 시
PHOENIX_SAMPLE_RATE=1.0
```

### 트래커 & 트레이스 옵션

- `--tracker phoenix`로 테스트 케이스별 OpenInference 스팬이 활성화되며, `--phoenix-max-traces`로 전송 케이스 수를 제어할 수 있습니다.
- CLI는 데이터셋 경로, 메트릭, Domain Memory 상태, 신뢰도 스냅샷을 자동으로 Phoenix 메타데이터에 포함합니다.
- Phoenix 로깅에 성공하면 JSON 출력의 `tracker_metadata["phoenix"]["trace_url"]` 필드에서 대시보드 링크를 바로 확인할 수 있습니다.

### 데이터셋 / 실험 동기화

새로운 CLI 옵션으로 EvalVault 데이터셋과 실험을 Phoenix와 동기화하세요:

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --tracker phoenix \
  --phoenix-dataset insurance-qa-ko \
  --phoenix-dataset-description "보험 QA v2025.01" \
  --phoenix-experiment gemma3-ko-baseline \
  --phoenix-experiment-description "Gemma3 vs OpenAI 비교"
```

- `--phoenix-dataset`은 EvalVault 데이터셋(컨텍스트/답변/메타데이터/threshold 포함)을 Phoenix Dataset으로 업로드합니다. 설명은 `--phoenix-dataset-description` 또는 기본 `"{name} v{version}"`을 사용합니다.
- `--phoenix-experiment`는 업로드된 Dataset과 연결된 Phoenix Experiment를 만들고, EvalVault 점수·Pass Rate·Domain Memory 정보를 포함합니다. `--phoenix-experiment-description`으로 설명을 지정하세요.
- 두 작업 모두 `result.tracker_metadata["phoenix"]`에 URL을 저장하므로 후속 자동화에서 Phoenix 화면으로 바로 이동할 수 있습니다.

### 임베딩 시각화 & 분석

Phoenix 12.27.0의 Embeddings Analysis 뷰(UMAP + HDBSCAN)는 다음 정보를 제공합니다.

- **시간대별 드리프트/Query Distance**: 기본/비교 임베딩 사이의 유클리드 거리를 시계열로 확인해 이상 구간을 빠르게 찾습니다.
- **드리프트 우선 클러스터**: HDBSCAN으로 추출된 클러스터를 드리프트 순으로 정렬해 저성과 영역을 먼저 표시합니다.
- **3D 포인트 클라우드 컬러링**: 정확도, 태그, 세그먼트별로 색상을 지정해 패턴을 시각적으로 탐지할 수 있습니다.

EvalVault가 업로드한 Dataset/Experiment URL을 클릭한 뒤 Phoenix 대시보드의 “Embeddings” 탭을 열면 질문/답변/컨텍스트 벡터를 즉시 탐색하고, Domain Memory 태그를 겹쳐 본 뒤 클러스터를 다시 EvalVault 개선 작업으로 연결할 수 있습니다.

### 오프라인 임베딩 내보내기

Phoenix Dataset을 CSV/Parquet으로 덤프해 Domain Memory 교차 분석에 활용하세요:

```bash
uv run evalvault phoenix export-embeddings \
  --dataset phoenix-dataset-id \
  --endpoint http://localhost:6006 \
  --output tmp/phoenix_embeddings.csv
```

UMAP/HDBSCAN 라이브러리가 설치되어 있으면 동일한 알고리즘을 사용하고, 없는 경우 PCA/DBSCAN으로 자동 대체합니다.

### Prompt Playground 루프 (Phoenix 프롬프트)

Phoenix Prompt Playground에서 튜닝한 프롬프트를 EvalVault 실행과 동기화하기 위해 기본 manifest(`agent/prompts/prompt_manifest.json`)와 전용 CLI를 제공합니다.

1. **프롬프트 ↔ Phoenix ID 연결**

```bash
uv run evalvault phoenix prompt-link agent/prompts/baseline.txt \
  --prompt-id pr-428 \
  --experiment-id exp-20250115 \
  --notes "Gemma3 베이스라인 프롬프트"
```

2. **릴리즈 전 diff 확인**

```bash
uv run evalvault phoenix prompt-diff \
  agent/prompts/baseline.txt agent/prompts/system.txt \
  --manifest agent/prompts/prompt_manifest.json \
  --format table  # 또는 json
```

3. **평가 실행에 Prompt 상태 주입**

```bash
uv run evalvault run data.json --metrics faithfulness \
  --profile prod \
  --tracker phoenix \
  --prompt-files agent/prompts/baseline.txt,agent/prompts/system.txt \
  --prompt-manifest agent/prompts/prompt_manifest.json
```

> 💡 **Prompt Loop 팁**: Phoenix Prompt Playground 연동 시에는 `prod` 프로필(`gpt-oss-safeguard:20b`, OpenAI OSS)을 사용하세요. 이 모델은 Phoenix tool-calling을 지원하므로 `gemma3:1b`에서 발생하던 “does not support tools” 오류 없이 Prompt diff/Trace 메타데이터가 기록됩니다. 실행 시간은 길지만 Prompt 회귀 추적 품질이 크게 향상됩니다.

`result.tracker_metadata["phoenix"]["prompts"]`에 파일별 상태(동기화/수정/미추적), 체크섬, diff가 저장되어 Slack 릴리즈 노트, history 테이블, Streamlit UI에서 Prompt 변화를 Trace/Dataset/Experiment 링크와 함께 확인할 수 있습니다.

> 참고: [Phoenix Embeddings Analysis (arize-phoenix-v12.27.0)](https://github.com/Arize-ai/phoenix/blob/arize-phoenix-v12.27.0/docs/phoenix/cookbook/retrieval-and-inferences/embeddings-analysis.mdx) 문서를 기준으로 임베딩 및 Prompt 메타데이터 동작을 검증했습니다.

### Phoenix Drift Watcher & 자동 Gate

`scripts/ops/phoenix_watch.py`는 Phoenix Dataset/Experiment를 주기적으로 조회하고 Slack 알림을 보내며, 임계값을 초과한 경우 `evalvault gate` 명령을 자동으로 실행합니다.

- REST API로 최신 Experiment를 가져오고 state 파일로 마지막 타임스탬프를 저장합니다.
- 기본 `embedding_drift_score` 또는 사용자가 지정한 지표 키를 읽어 임계값 이상이면 즉시 경고를 보냅니다.
- 임계값 초과 시 `--gate-command`에 전달된 EvalVault Gate 명령(또는 쉘 파이프라인)을 실행해 회귀 테스트를 강제합니다.

```bash
uv run python scripts/ops/phoenix_watch.py \
  --endpoint http://localhost:6006 \
  --dataset-id ds_123 \
  --drift-key embedding_drift_score \
  --drift-threshold 0.18 \
  --slack-webhook https://hooks.slack.com/services/... \
  --gate-command "uv run evalvault gate tests/fixtures/gates/regression.yaml --profile prod"
```

### 릴리즈 노트 자동화

`evalvault.config.phoenix_support.format_phoenix_links` 헬퍼가 `phoenix_trace_url`·Dataset·Experiment 링크를 표준화하므로 외부 보고서에서도 일관되게 재사용할 수 있습니다. CLI JSON 요약을 Markdown/Slack 형식으로 변환하려면 아래 스크립트를 사용하세요.

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --output run.json
uv run python scripts/reports/generate_release_notes.py \
  --summary run.json \
  --style markdown \
  --out reports/release_notes.md
```

`--style slack` 옵션을 주면 `<http://...|Phoenix Trace>` 형식으로 렌더링되므로 온콜 채널에 바로 붙여넣을 수 있습니다.

### CLI/웹에서 Phoenix 메트릭 확인

- `uv run evalvault history` 테이블에 `Phoenix P@K`/`Drift` 컬럼이 추가되어 Phoenix Experiment가 연결된 실행의 정밀도/드리프트 값을 즉시 확인할 수 있습니다. `PHOENIX_ENDPOINT`/`PHOENIX_API_TOKEN`이 설정되어 있으면 Phoenix REST API에서 최신 값을 자동으로 가져옵니다.
- Streamlit 홈/History/Reports 화면에서도 동일한 메트릭과 Experiment 링크가 표시되어 EvalVault 통계에서 Phoenix Embeddings 뷰로 곧바로 이동할 수 있습니다.

---

## 완전 설정 가이드 (git clone → 평가 저장 완료)

이 섹션은 저장소 클론부터 Langfuse 추적 및 SQLite 저장을 포함한 평가 실행까지 모든 단계를 안내합니다.

### 사전 요구사항

| 요구사항 | 버전 | 설치 방법 |
|----------|------|-----------|
| **Python** | 3.12.x | uv가 자동 설치 |
| **uv** | 최신 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Docker** | 최신 | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Ollama** | 최신 | `curl -fsSL https://ollama.com/install.sh \| sh` |

### 1단계: 클론 및 의존성 설치

```bash
# 저장소 클론
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault

# 의존성 설치 (.python-version으로 Python 3.12 자동 선택)
uv sync --extra dev

# Python 버전 확인
uv run python --version
# 예상 출력: Python 3.12.x
```

### 2단계: Ollama 설정 (로컬 LLM)

EvalVault는 폐쇄망/로컬 LLM 평가를 위해 Ollama를 사용합니다. Ollama 서버를 시작하고 필요한 모델을 다운로드하세요:

```bash
# Ollama 서버 시작 (백그라운드 실행)
ollama serve &

# dev 프로필에 필요한 모델 다운로드
ollama pull gemma3:1b              # 평가용 LLM
ollama pull qwen3-embedding:0.6b   # 임베딩 모델

# 설치된 모델 확인
ollama list
```

**예상 출력:**
```
NAME                    SIZE
gemma3:1b               815 MB
qwen3-embedding:0.6b    639 MB
```

### 3단계: Langfuse 시작 (평가 추적)

Langfuse는 트레이스 레벨 검사 및 평가 실행의 이력 비교를 제공합니다.

```bash
# Docker Compose로 Langfuse 시작
docker compose -f docker-compose.langfuse.yml up -d

# 모든 컨테이너가 healthy 상태인지 확인
docker compose -f docker-compose.langfuse.yml ps
```

**예상 컨테이너:**
| 컨테이너 | 포트 | 상태 |
|----------|------|------|
| langfuse-web | 3000 | healthy |
| langfuse-worker | 3030 | healthy |
| postgres | 5432 | healthy |
| clickhouse | 8123 | healthy |
| redis | 6379 | healthy |
| minio | 9090 | healthy |

### 4단계: Langfuse 프로젝트 및 API 키 생성

1. 브라우저에서 http://localhost:3000 열기
2. **Sign Up** - 계정 생성 (이메일 + 비밀번호)
3. **New Organization** - 조직 생성 (예: "EvalVault")
4. **New Project** - 프로젝트 생성 (예: "RAG-Evaluation")
5. **Settings → API Keys** - 새 API 키 생성
6. **Public Key** (`pk-lf-...`)와 **Secret Key** (`sk-lf-...`) 복사

### 5단계: 환경 변수 설정

설정 파일 `.env`를 생성합니다:

```bash
# 예제 파일 복사
cp .env.example .env
```

`.env` 파일을 편집합니다:

```bash
# EvalVault 설정
EVALVAULT_PROFILE=dev

# Ollama 설정
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=120

# Langfuse 설정 (여기에 키를 붙여넣으세요)
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=http://localhost:3000
```

### 6단계: 첫 번째 평가 실행

```bash
# 샘플 데이터셋으로 평가 실행
uv run evalvault run tests/fixtures/sample_dataset.json \
  --metrics faithfulness,answer_relevancy

# 예상 출력:
# ╭───────────────────────────── Evaluation Results ─────────────────────────────╮
# │ Evaluation Summary                                                           │
# │   Run ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx                               │
# │   Dataset: test_dataset v1.0.0                                               │
# │   Model: ollama/gemma3:1b                                                    │
# │   Duration: ~45s                                                             │
# │ Results                                                                      │
# │   Total Test Cases: 4                                                        │
# │   Passed: 4                                                                  │
# │   Pass Rate: 100.0%                                                          │
# ╰──────────────────────────────────────────────────────────────────────────────╯
```

### 7단계: 저장 옵션을 포함한 평가 실행

결과를 Langfuse와 SQLite 모두에 저장합니다:

```bash
# Langfuse 추적 + SQLite 저장으로 실행
uv run evalvault run tests/fixtures/sample_dataset.json \
  --metrics faithfulness,answer_relevancy \
  --langfuse \
  --db evalvault.db

# 예상 출력에 포함되는 내용:
# Logged to Langfuse (trace_id: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
# Results saved to database: evalvault.db
# Run ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 8단계: 저장된 결과 확인

**SQLite 이력:**
```bash
uv run evalvault history --db evalvault.db

# ┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┓
# ┃ Run ID      ┃ Dataset    ┃ Model       ┃ Started At ┃ Pass Rate ┃ Test Cases ┃
# ┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━┩
# │ 51f0286a... │ test_data… │ ollama/gem… │ 2025-12-29 │    100.0% │          4 │
# └─────────────┴────────────┴─────────────┴────────────┴───────────┴────────────┘
```

**Langfuse 대시보드:**
- http://localhost:3000 열기
- **Traces** 탭으로 이동
- 각 평가 실행의 상세 트레이스 정보 확인

### 빠른 참조

| 작업 | 명령어 |
|------|--------|
| 평가 실행 | `uv run evalvault run data.json --metrics faithfulness` |
| 저장 옵션 포함 실행 | `uv run evalvault run data.json --metrics faithfulness --langfuse --db evalvault.db` |
| 이력 조회 | `uv run evalvault history --db evalvault.db` |
| 메트릭 목록 | `uv run evalvault metrics` |
| 설정 확인 | `uv run evalvault config` |
| Langfuse 중지 | `docker compose -f docker-compose.langfuse.yml down` |

---

## 지원 메트릭

| 메트릭 | 설명 | Ground Truth |
|--------|------|--------------|
| `faithfulness` | 답변이 컨텍스트에 충실한지 (환각 감지) | 불필요 |
| `answer_relevancy` | 답변이 질문과 관련있는지 | 불필요 |
| `context_precision` | 검색된 컨텍스트의 정밀도 | 필요 |
| `context_recall` | 필요한 정보를 검색했는지 | 필요 |
| `factual_correctness` | 답변과 정답의 사실적 일치 여부 | 필요 |
| `semantic_similarity` | 답변과 정답의 의미적 유사도 | 필요 |

## CLI 명령어

> **참고**: 소스에서 실행할 때는 모든 명령어 앞에 `uv run`을 붙이세요. PyPI로 설치한 경우 `evalvault`만 사용합니다.

```bash
# 평가 실행
uv run evalvault run data.json --metrics faithfulness,answer_relevancy

# Langfuse 추적 + SQLite 저장으로 실행
uv run evalvault run data.json --metrics faithfulness --langfuse --db evalvault.db

# 병렬 평가 (대용량 데이터셋에 효과적)
uv run evalvault run data.json --metrics faithfulness --parallel --batch-size 10

# Ollama 프로필 선택
uv run evalvault run data.json --profile dev --metrics faithfulness

# OpenAI 프로필 선택
uv run evalvault run data.json -p openai --metrics faithfulness

# 이력 조회
uv run evalvault history --db evalvault.db --limit 10

# 실행 비교
uv run evalvault compare <run_id1> <run_id2> --db evalvault.db

# 결과 내보내기
uv run evalvault export <run_id> -o result.json --db evalvault.db

# 설정 확인
uv run evalvault config

# 사용 가능한 메트릭 목록
uv run evalvault metrics

# Web UI 실행 (--extra web 필요)
uv run evalvault web --port 8501

# 쿼리 기반 분석 파이프라인 (--extra korean 필요)
uv run evalvault pipeline analyze "요약해줘" --run-id <run_id>
uv run evalvault pipeline intents     # 분석 의도 목록
uv run evalvault pipeline templates   # 파이프라인 템플릿 목록

# Domain Memory 활용 (threshold 자동 조정)
uv run evalvault run data.json --metrics faithfulness \
  --use-domain-memory --memory-domain insurance --memory-language ko

# Domain Memory + 컨텍스트 보강
uv run evalvault run data.json --metrics faithfulness \
  --use-domain-memory --augment-context --memory-domain insurance

# Phoenix 임베딩 클러스터를 Domain Memory로 가져오기
uv run evalvault domain memory ingest-embeddings phoenix_embeddings.csv \
  --domain insurance \
  --language ko \
  --min-cluster-size 5 \
  --sample-size 3

# 벤치마크 실행
uv run evalvault benchmark run --name korean-rag
uv run evalvault benchmark list
```

## A/B 테스트 가이드

EvalVault는 모델, 프롬프트, 설정 등을 비교하는 A/B 테스트를 지원합니다. 이 가이드는 실험의 전체 과정을 안내합니다.

### 1단계: 실험 생성

```bash
uv run evalvault experiment-create \
  --name "모델 비교" \
  --hypothesis "큰 모델이 answer_relevancy에서 더 높은 점수를 받을 것" \
  --db experiment.db
```

출력:
```
Created experiment: 20421536-e09a-4255-89a3-c402b2b80a2d
  Name: 모델 비교
  Status: draft
```

> 실험 ID를 저장해두세요. 이후 단계에서 사용합니다.

### 2단계: 그룹 추가 (A/B)

비교할 두 그룹을 생성합니다:

```bash
# 그룹 A: 기준 모델
uv run evalvault experiment-add-group \
  --id <experiment-id> \
  -g "baseline" \
  -d "gemma3:1b (1B 파라미터)" \
  --db experiment.db

# 그룹 B: 도전 모델
uv run evalvault experiment-add-group \
  --id <experiment-id> \
  -g "challenger" \
  -d "gemma3n:e2b (4.5B 파라미터)" \
  --db experiment.db
```

### 3단계: 평가 실행

각 그룹에 대해 다른 설정으로 평가를 실행합니다:

```bash
# 그룹 A: 기준 모델로 실행
uv run evalvault run tests/fixtures/sample_dataset.json \
  --profile dev \
  --model gemma3:1b \
  --metrics faithfulness,answer_relevancy \
  --db experiment.db

# 출력에서 Run ID를 저장 (예: 34f364e9-cd28-4cf9-a93d-5c706aaf9f14)

# 그룹 B: 도전 모델로 실행
uv run evalvault run tests/fixtures/sample_dataset.json \
  --profile dev \
  --model gemma3n:e2b \
  --metrics faithfulness,answer_relevancy \
  --db experiment.db

# 출력에서 Run ID를 저장 (예: 034da928-0f74-4205-8654-6492712472b3)
```

### 4단계: 실행 결과를 그룹에 연결

평가 실행을 해당 그룹에 연결합니다:

```bash
# 기준 모델 실행을 그룹 A에 추가
uv run evalvault experiment-add-run \
  --id <experiment-id> \
  -g "baseline" \
  -r <baseline-run-id> \
  --db experiment.db

# 도전 모델 실행을 그룹 B에 추가
uv run evalvault experiment-add-run \
  --id <experiment-id> \
  -g "challenger" \
  -r <challenger-run-id> \
  --db experiment.db
```

### 5단계: 결과 비교

비교 테이블을 확인합니다:

```bash
uv run evalvault experiment-compare --id <experiment-id> --db experiment.db
```

출력:
```
Experiment Comparison

모델 비교
Hypothesis: 큰 모델이 answer_relevancy에서 더 높은 점수를 받을 것

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric           ┃ baseline ┃ challenger ┃ Best Group ┃ Improvement ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ faithfulness     │    1.000 │      1.000 │  baseline  │       +0.0% │
│ answer_relevancy │    0.908 │      0.957 │ challenger │       +5.4% │
└──────────────────┴──────────┴────────────┴────────────┴─────────────┘
```

### 6단계: 실험 결론 기록

결론을 기록합니다:

```bash
uv run evalvault experiment-conclude \
  --id <experiment-id> \
  --conclusion "도전 모델이 answer_relevancy에서 5.4% 개선, 단 2배의 지연 시간 트레이드오프" \
  --db experiment.db
```

### 추가 명령어

```bash
# 실험 요약 보기
uv run evalvault experiment-summary --id <experiment-id> --db experiment.db

# 모든 실험 목록
uv run evalvault experiment-list --db experiment.db
```

### 빠른 참조

| 단계 | 명령어 |
|------|--------|
| 실험 생성 | `experiment-create --name "..." --hypothesis "..."` |
| 그룹 추가 | `experiment-add-group --id <exp> -g "이름" -d "설명"` |
| 평가 실행 | `run dataset.json --model <model> --db experiment.db` |
| 실행 연결 | `experiment-add-run --id <exp> -g "그룹" -r <run>` |
| 결과 비교 | `experiment-compare --id <exp>` |
| 결론 기록 | `experiment-conclude --id <exp> --conclusion "..."` |

---

## 데이터 형식

### JSON (권장)

```json
{
  "name": "my-dataset",
  "version": "1.0.0",
  "thresholds": {
    "faithfulness": 0.8,
    "answer_relevancy": 0.7
  },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "보험금은 얼마인가요?",
      "answer": "1억원입니다.",
      "contexts": ["사망보험금은 1억원입니다."],
      "ground_truth": "1억원"
    }
  ]
}
```

> `thresholds`: 메트릭별 통과 기준 (0.0~1.0). 기본값 0.7.

### CSV

```csv
id,question,answer,contexts,ground_truth
tc-001,"보험금은 얼마인가요?","1억원입니다.","[""사망보험금은 1억원입니다.""]","1억원"
```

## 환경 설정

```bash
# .env 예시

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=120

LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

## 모델 프로필 (`config/models.yaml`)

| 프로필 | LLM | Embedding | 용도 |
|--------|-----|-----------|------|
| `dev` | gemma3:1b (Ollama) | qwen3-embedding:0.6b | 개발/테스트 |
| `prod` | gpt-oss-safeguard:20b (Ollama) | qwen3-embedding:8b | 운영 환경 |
| `openai` | gpt-5-nano | text-embedding-3-small | 외부망 |

## 아키텍처

```
EvalVault/
├── config/               # 모델 프로필, 런타임 설정
├── src/evalvault/        # 도메인 · 포트 · 어댑터
├── docs/                 # 가이드, 아키텍처, 로드맵
└── tests/                # unit / integration / e2e_data
```

## 문서

| 파일 | 설명 |
|------|------|
| [docs/USER_GUIDE.md](USER_GUIDE.md) | 설치, 설정, 문제 해결 |
| [docs/ARCHITECTURE.md](ARCHITECTURE.md) | Hexagonal Architecture 상세 가이드 |
| [docs/ARCHITECTURE_C4.md](ARCHITECTURE_C4.md) | C4 Model 기반 아키텍처 문서 |
| [docs/COMPLETED.md](COMPLETED.md) | Phase 1-14 완료 내역 및 기술 스펙 |
| [docs/ROADMAP.md](ROADMAP.md) | 2026-2027 개발 로드맵 |
| [docs/IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md) | 코드 품질 개선 계획 |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | 기여 가이드 |

## 개발

```bash
# 테스트 (항상 uv run 사용)
uv run pytest tests/ -v
# 총 1,352개 테스트 (1,261 유닛 + 91 통합) | 커버리지: 89%

uv run pytest tests/integration/test_e2e_scenarios.py -v   # 외부 API 필요

# 린트 & 포맷팅
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## 커뮤니티 & PSF 멤버십

EvalVault는 [Python Software Foundation](https://www.python.org/psf/) Supporting Member가
주도하는 프로젝트입니다. 오픈소스 생태계와 파이썬 커뮤니티에 기여하는 것이 목표입니다.

<p align="left">
  <a href="https://www.python.org/psf/membership/">
    <img src="./assets/psf-supporting-member.png" alt="PSF Supporting Member" width="130" />
  </a>
</p>

## 라이선스

Apache 2.0 - [LICENSE.md](../LICENSE.md) 참조.

---

<div align="center">
  <strong>EvalVault</strong> - RAG 평가의 새로운 기준.
</div>
