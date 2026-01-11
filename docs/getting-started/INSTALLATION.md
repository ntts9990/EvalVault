# EvalVault 설치 가이드

> Audience: 처음 사용자
> Last Updated: 2026-01-10

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

**Extras 설명**:

`dev` extra는 개발 도구와 모든 기능 extras를 포함합니다:
- 개발 도구: pytest, ruff, mkdocs 등
- 모든 기능 extras: analysis, korean, postgres, mlflow, phoenix, perf, anthropic, docs

경량 설치가 필요하면 개별 extras만 선택하세요:

| Extra | 패키지 | 용도 |
|-------|--------|------|
| `analysis` | scikit-learn | 통계/NLP 분석 모듈 |
| `korean` | kiwipiepy, rank-bm25, sentence-transformers | 한국어 형태소·검색 |
| `postgres` | psycopg[binary] | PostgreSQL 저장소 |
| `mlflow` | mlflow | MLflow 추적기 |
| `phoenix` | arize-phoenix + OpenTelemetry exporters | Phoenix 트레이싱, 데이터셋/실험 동기화 |
| `anthropic` | anthropic, langchain-anthropic | Anthropic LLM 어댑터 |
| `perf` | faiss-cpu, ijson | 대용량 데이터셋 성능 보조 (FAISS 인덱스, JSON 스트리밍) |
| `docs` | mkdocs, mkdocs-material, mkdocstrings | 문서 빌드 |

**설치 예시**:
```bash
# 경량 설치: 분석 기능만
uv sync --extra analysis

# 한국어 NLP 기능 포함
uv sync --extra korean

# 여러 extras 조합
uv sync --extra analysis --extra korean --extra phoenix
```

`.python-version` 덕분에 uv가 Python 3.12를 자동으로 내려받습니다.

---

## 기본 설정

```bash
cp .env.example .env
# OPENAI_API_KEY, OLLAMA_BASE_URL, LANGFUSE_* , PHOENIX_* 등을 채워 넣으세요.
```

---

## API + React 프론트 실행 (dev)

```bash
# API
uv run evalvault serve-api --reload

# Frontend
cd frontend
npm install
npm run dev
```
브라우저에서 `http://localhost:5173`를 열어 확인합니다.

---

## 다음 단계

- 설치/환경설정/CLI/Web UI: [guides/USER_GUIDE.md](../guides/USER_GUIDE.md)
- 개발/기여: [guides/DEV_GUIDE.md](../guides/DEV_GUIDE.md)
- 개발 백서(설계/운영/품질 기준): [new_whitepaper/INDEX.md](../new_whitepaper/INDEX.md)
- 외부 시스템 트레이싱 표준: [architecture/open-rag-trace-spec.md](../architecture/open-rag-trace-spec.md)
- Collector 구성: [architecture/open-rag-trace-collector.md](../architecture/open-rag-trace-collector.md)
- 프로젝트 개요(한국어): [README.md](../../README.md)
- 프로젝트 개요(영문): [README.en.md](../../README.en.md)
