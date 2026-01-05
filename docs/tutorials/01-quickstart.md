# 5분 빠른 시작 가이드

> EvalVault를 설치하고 첫 RAG 평가를 실행하는 가장 빠른 방법

---

## 전제 조건

- Python 3.12+
- OpenAI API 키 또는 로컬 모델(Ollama/vLLM)

---

## Step 1: 설치

```bash
# 저장소 클론
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault

# 의존성 설치 (uv 사용 권장)
uv sync --extra dev
```

pip을 사용하는 경우:

```bash
uv venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

---

## Step 2: 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# OpenAI API 키 설정 (OpenAI 사용 시)
echo "OPENAI_API_KEY=sk-your-api-key" >> .env
```

OpenAI를 쓰지 않는다면 위 키 설정은 생략해도 됩니다.

### 초간단 시작 (Ollama 3줄)

```bash
cp .env.example .env
ollama pull gemma3:1b
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness \
  --db evalvault.db \
  --profile dev
```

Tip: `answer_relevancy` 등 임베딩 메트릭을 쓰려면 `qwen3-embedding:0.6b`도 내려받으세요.

### 초간단 시작 (vLLM 3줄)

```bash
cp .env.example .env
printf "\nEVALVAULT_PROFILE=vllm\nVLLM_BASE_URL=http://localhost:8001/v1\nVLLM_MODEL=gpt-oss-120b\n" >> .env
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness \
  --db evalvault.db
```

Tip: 임베딩 메트릭은 `VLLM_EMBEDDING_MODEL`과 `/v1/embeddings` 엔드포인트가 필요합니다.

설정 확인(선택):

```bash
uv run evalvault config
```

출력 예시:
```
EvalVault Configuration
========================
OpenAI Model: gpt-5-nano
Embedding Model: text-embedding-3-small
Langfuse: Not configured
```

---

## Step 3: 첫 Ragas 평가 실행

샘플 데이터셋으로 Ragas 평가를 실행하고 결과를 DB에 저장합니다:

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness \
  --db evalvault.db
```

Tip: `--db`를 빼면 결과가 콘솔에만 출력되고 history/export/Web UI에는 저장되지 않습니다.

출력 예시:
```
EvalVault v1.0.0
================
Dataset: insurance-qa-dataset (5 test cases)
Metrics: faithfulness

Evaluating... [####################################] 100%

Results:
--------
faithfulness: 0.92
Pass Rate: 100% (5/5 passed)

Results saved to database: evalvault.db
Run ID: abc123-def456-...
```

---

## Step 4: 결과 확인 (CLI/Web UI)

```bash
# 평가 히스토리 조회 (동일한 DB 경로)
uv run evalvault history --db evalvault.db

# 상세 결과 내보내기
uv run evalvault export <run_id> -o result.json --db evalvault.db

# Web UI에서 결과 보기 (Streamlit)
uv run evalvault web --db evalvault.db
```
Tip: Streamlit UI를 쓰려면 `uv sync --extra web`이 필요합니다.

---

## Step 5: API + React 프론트 실행 (선택)

```bash
# API
uv run evalvault serve-api --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## 다음 단계

축하합니다! 첫 RAG 평가를 성공적으로 완료했습니다.

### 더 알아보기

| 주제 | 튜토리얼 |
|------|----------|
| 데이터셋 형식과 메트릭 이해 | [02-basic-evaluation.md](02-basic-evaluation.md) |
| 커스텀 메트릭 만들기 | [03-custom-metrics.md](03-custom-metrics.md) |
| Phoenix 연동하기 | [04-phoenix-integration.md](04-phoenix-integration.md) |
| 한국어 RAG 최적화 | [05-korean-rag.md](05-korean-rag.md) |
| 프로덕션 배포 가이드 | [06-production-tips.md](06-production-tips.md) |

---

## 문제 해결

### API 키 오류

```
Error: OPENAI_API_KEY not set
```

**해결**: `.env` 파일에 API 키가 올바르게 설정되었는지 확인하세요.

```bash
cat .env | grep OPENAI_API_KEY
```

### 설치 문제

uv가 설치되지 않은 경우:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## 요약

| 단계 | 명령어 |
|------|--------|
| 1. 설치 | `uv sync --extra dev` |
| 2. 환경 설정 | `.env` 파일에 `OPENAI_API_KEY` 설정 |
| 3. 평가 실행 | `uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness --db evalvault.db` |
| 4. 결과 확인 | `uv run evalvault history --db evalvault.db` 또는 `uv run evalvault web --db evalvault.db` |
| 5. (선택) API + React 실행 | `uv run evalvault serve-api --reload` + `npm run dev` |

소요 시간: 약 5분

---

<div align="center">

[다음: 기본 평가 실행](02-basic-evaluation.md)

</div>
