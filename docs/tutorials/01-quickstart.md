# 5분 빠른 시작 가이드

> EvalVault를 설치하고 첫 RAG 평가를 실행하는 가장 빠른 방법

---

## 전제 조건

- Python 3.12+
- OpenAI API 키

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

# OpenAI API 키 설정 (필수)
echo "OPENAI_API_KEY=sk-your-api-key" >> .env
```

설정 확인:

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

## Step 3: API + React 프론트 실행 (dev)

```bash
# API
uv run evalvault serve-api --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Step 4: 첫 평가 실행

샘플 데이터셋으로 평가를 실행합니다:

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness
```

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

Run ID: abc123-def456-...
```

---

## 다음 단계

축하합니다! 첫 RAG 평가를 성공적으로 완료했습니다.

### 결과 확인

```bash
# 평가 히스토리 조회
uv run evalvault history

# 상세 결과 내보내기
uv run evalvault export <run_id> -o result.json
```

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
| 3. API + React 실행 | `uv run evalvault serve-api --reload` + `npm run dev` |
| 4. 평가 실행 | `uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness` |

소요 시간: 약 5분

---

<div align="center">

[다음: 기본 평가 실행](02-basic-evaluation.md)

</div>
