# EvalVault (한국어)

> RAG(Retrieval-Augmented Generation) 시스템 평가 자동화를 위한 CLI · Web UI 도구

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)

English version? See the [root README](README.md).

---

## 개요

EvalVault는 Ragas v1.0 메트릭을 기반으로 Typer CLI와 FastAPI + React Web UI를 제공하여 RAG 품질을 일관되게 측정하고 저장합니다. OpenAI, Ollama, Azure, Anthropic 등 프로필 기반으로 모델을 교체할 수 있으며, Langfuse · Phoenix · Domain Memory · DAG 분석 파이프라인을 통해 추적 및 개선 업무를 자동화합니다.

**주요 특징**
- Typer CLI 한 번으로 평가/비교/내보내기/저장 실행
- OpenAI/Ollama/폐쇄망을 아우르는 프로필 기반 모델 구성
- FastAPI + React UI에서 Evaluation Studio/Analysis Lab 결과 저장 및 재조회
- Langfuse 및 Phoenix 트래커로 트레이스/데이터셋/실험/프롬프트 동기화
- Domain Memory로 과거 결과를 학습하여 threshold 조정·컨텍스트 보강·트렌드 분석
- 통계·NLP·인과 모듈을 가진 DAG 분석 파이프라인

상세 워크플로와 Phoenix/자동화 예시는 [사용자 가이드](docs/guides/USER_GUIDE.md)를 참고하세요.

---

## 설치

### PyPI
```bash
uv pip install evalvault
```

### 소스 설치 (개발자 권장)
```bash
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault
uv sync --extra dev
```

필요한 추가 기능은 extras로 확장합니다.

| Extra | 패키지 | 용도 |
|-------|--------|------|
| `analysis` | scikit-learn | 통계/NLP 분석 모듈 |
| `korean` | kiwipiepy, rank-bm25, sentence-transformers | 한국어 형태소·검색 |
| `postgres` | psycopg | PostgreSQL 저장소 |
| `mlflow` | mlflow | MLflow 추적기 |
| `phoenix` | arize-phoenix + OpenTelemetry | Phoenix 트레이싱/데이터셋/실험 연동 |
| `anthropic` | anthropic | Anthropic LLM 어댑터 |

`.python-version` 덕분에 uv가 Python 3.12를 자동으로 내려받습니다.

---

## 빠른 사용법

1. **환경 설정**
   ```bash
   cp .env.example .env
   # OPENAI_API_KEY, OLLAMA_BASE_URL, LANGFUSE_* , PHOENIX_* 등을 채워 넣으세요.
   ```
   SQLite 경로를 바꾸려면 아래 값을 추가합니다.
   ```bash
   # .env
   EVALVAULT_DB_PATH=/path/to/evalvault.db
   ```
   Ollama에서 tool/function calling 지원 모델을 쓰려면 `OLLAMA_TOOL_MODELS`에
   콤마로 모델명을 추가하세요. 확인은 `ollama show <model>`로 하고
   `Capabilities`에 `tools`가 표시되는 모델만 넣으면 됩니다.
   vLLM(OpenAI-compatible) 사용 예:
   ```bash
   # .env
   EVALVAULT_PROFILE=vllm
   VLLM_BASE_URL=http://localhost:8001/v1
   VLLM_MODEL=gpt-oss-120b
   VLLM_EMBEDDING_MODEL=qwen3-embedding:0.6b
   # 선택: VLLM_EMBEDDING_BASE_URL=http://localhost:8002/v1
   ```
   초간단 시작 (Ollama 3줄):
   ```bash
   cp .env.example .env
   ollama pull gemma3:1b
   uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
     --metrics faithfulness \
     --db evalvault.db \
     --profile dev
   ```
   Tip: `answer_relevancy` 등 임베딩 메트릭을 쓰려면 `qwen3-embedding:0.6b`도 내려받으세요.

   초간단 시작 (vLLM 3줄):
   ```bash
   cp .env.example .env
   printf "\nEVALVAULT_PROFILE=vllm\nVLLM_BASE_URL=http://localhost:8001/v1\nVLLM_MODEL=gpt-oss-120b\n" >> .env
   uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
     --metrics faithfulness \
     --db evalvault.db
   ```
   Tip: 임베딩 메트릭은 `VLLM_EMBEDDING_MODEL`과 `/v1/embeddings` 엔드포인트가 필요합니다.

2. **API + React 프론트 실행 (dev)**
   ```bash
   # API
   uv run evalvault serve-api --reload

   # Frontend
   cd frontend
   npm install
   npm run dev
   ```
   브라우저에서 `http://localhost:5173`를 열어 확인합니다.

3. **평가 실행**
   ```bash
   uv run evalvault run tests/fixtures/sample_dataset.json \
     --metrics faithfulness,answer_relevancy \
     --profile dev \
     --db evalvault.db
   ```
   Tip: 결과를 history/export/Web UI에서 보려면 `--db` 경로를 동일하게 유지하세요.
   Phoenix 추적이 필요하면 `--tracker phoenix`를 추가하고 `uv sync --extra phoenix`로 설치합니다.

4. **히스토리 확인**
   ```bash
   uv run evalvault history --db evalvault.db
   ```

Langfuse, Phoenix Dataset/Experiment 업로드, Prompt manifest diff, Streaming dataset 처리 등 고급 시나리오는 [USER_GUIDE.md](docs/guides/USER_GUIDE.md)에 정리되어 있습니다.

## 실행 모드 (Simple / Full)

EvalVault CLI는 **심플(Simple)** 모드와 **전체(Full)** 모드를 제공합니다. 심플 모드는 2개 메트릭과 Phoenix 추적을 자동으로 묶어 초보자에게 안전한 기본값을 제공하고, 전체 모드는 Domain Memory·Prompt manifest·Phoenix Dataset/Experiment·스트리밍 등 모든 플래그를 그대로 노출합니다.

| 모드 | 명령 | 기본 프리셋 | 활용 사례 |
|------|------|-------------|-----------|
| Simple | `uv run evalvault run --mode simple dataset.json`<br>`uv run evalvault run-simple dataset.json` | `faithfulness + answer_relevancy`, Phoenix tracker 고정, Domain Memory/Prompt 비활성 | 첫 실행, 데모, 온보딩 |
| Full | `uv run evalvault run --mode full dataset.json`<br>`uv run evalvault run-full dataset.json` | 모든 고급 옵션 노출 (Domain Memory, Phoenix dataset/experiment, prompt manifest, streaming) | 파워 유저, CI 게이트, 옵저버빌리티 연동 |

```bash
# 심플 모드: dataset + profile 정도만 지정해도 실행 가능
uv run evalvault run-simple tests/fixtures/e2e/insurance_qa_korean.json -p dev

# 전체 모드: Phoenix + Domain Memory 옵션을 한 번에
uv run evalvault run-full tests/fixtures/e2e/insurance_qa_korean.json \
  --profile prod \
  --tracker phoenix \
  --phoenix-dataset insurance-qa-ko \
  --phoenix-experiment gemma3-prod \
  --use-domain-memory --memory-domain insurance --augment-context
```

- `uv run evalvault history --mode simple/full`로 CLI 히스토리를 즉시 필터링할 수 있습니다.
- Web UI에서도 동일한 모드 토글과 Mode Pill이 표시됩니다.

---

## 문서
- [docs/INDEX.md](docs/INDEX.md): 전체 문서 인덱스
- [docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md): 설치/환경설정/CLI/Web UI/Phoenix/자동화/문제 해결
- [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md): 설계 문서
- [CHANGELOG.md](CHANGELOG.md): 릴리스 히스토리

---

## 기여 & 라이선스

Pull Request는 언제든 환영합니다. [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하고 제출 전 `uv run ruff check`, `uv run pytest`를 실행해주세요.

EvalVault는 [Apache 2.0](LICENSE.md) 라이선스를 따릅니다.
