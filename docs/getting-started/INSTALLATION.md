# EvalVault 설치 가이드

> Audience: 처음 사용자
> Last Updated: 2026-01-07

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
| `web` | streamlit, plotly | Streamlit Web UI |
| `postgres` | psycopg | PostgreSQL 저장소 |
| `mlflow` | mlflow | MLflow 추적기 |
| `phoenix` | arize-phoenix + OpenTelemetry | Phoenix 추적/데이터셋/실험 연동 |
| `anthropic` | anthropic | Anthropic LLM 어댑터 |

`.python-version` 덕분에 uv가 Python 3.12를 자동으로 내려받습니다.

---

## 기본 설정

```bash
cp .env.example .env
# OPENAI_API_KEY, OLLAMA_BASE_URL, LANGFUSE_* , PHOENIX_* 등을 채워 넣으세요.
```

---

## 다음 단계

- 5분 빠른 시작: [tutorials/01-quickstart.md](../tutorials/01-quickstart.md)
- 설치/환경설정/CLI/Web UI: [guides/USER_GUIDE.md](../guides/USER_GUIDE.md)
- 명령어 참조: [guides/CLI_GUIDE.md](../guides/CLI_GUIDE.md)
- 프로젝트 개요(한국어): [README.ko.md](../../README.ko.md)
- 프로젝트 개요(영문): [README.md](../../README.md)
