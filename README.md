# EvalVault

RAG(Retrieval-Augmented Generation) 시스템을 대상으로 **평가(Eval) → 분석(Analysis) → 추적(Tracing) → 개선 루프**를 하나의 워크플로로 묶는 CLI + Web UI 플랫폼입니다.

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)

English version? See `README.en.md`.

---

## Quickstart (CLI)

```bash
uv sync --extra dev
cp .env.example .env

uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --auto-analyze
```

Tip: 기본 저장소는 Postgres+pgvector입니다. SQLite를 쓰려면 `--db` 또는 `DB_BACKEND=sqlite` + `EVALVAULT_DB_PATH`를 지정하세요.

---

## 핵심 기능

- **End-to-End 평가 루프**: Eval → Analysis → Tracing → Improvement를 한 흐름으로 실행
- **Dataset 중심 운영**: 합격 기준(threshold)을 데이터셋에 유지
- **Artifacts-first**: 보고서뿐 아니라 모듈별 원본 결과를 구조화 저장
- **옵션형 Observability**: Phoenix/Langfuse/MLflow는 필요할 때만 활성화
- **CLI + Web UI**: 동일 run_id 기반으로 히스토리/비교/리포트 통합

---

## 문서 허브

- 문서 인덱스: `docs/INDEX.md`
- 핸드북(교과서형): `docs/handbook/INDEX.md`
- 외부 요약본: `docs/handbook/EXTERNAL.md`
- 운영 가이드(로컬/도커/관측/런북): `docs/handbook/CHAPTERS/04_operations.md`
- 워크플로(실행/분석/비교/회귀): `docs/handbook/CHAPTERS/03_workflows.md`
- 품질/테스트/CI: `docs/handbook/CHAPTERS/06_quality_and_testing.md`
- 아키텍처: `docs/handbook/CHAPTERS/01_architecture.md`
- 오프라인/폐쇄망(Docker/모델 캐시): `docs/guides/OFFLINE_DOCKER.md`, `docs/guides/OFFLINE_MODELS.md`

참고(호환성): `docs/guides/USER_GUIDE.md`, `docs/guides/DEV_GUIDE.md` 등 일부 문서는 과거 링크 호환을 위한 deprecated 스텁이며, 최신 내용은 handbook을 따릅니다.

---

## Web UI

```bash
# API
uv run evalvault serve-api --reload

# Frontend
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속 후, Evaluation Studio에서 실행/히스토리/리포트를 확인합니다.

---

## 오프라인/폐쇄망

- Docker 이미지 번들: `docs/guides/OFFLINE_DOCKER.md`
- NLP 모델 캐시 번들: `docs/guides/OFFLINE_MODELS.md`

LLM 모델은 폐쇄망 내부 인프라가 관리하며, EvalVault는 **분석용 NLP 모델 캐시**만 번들에 포함합니다.

---

## 기여

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pytest tests -v
```

- 기여 가이드: `CONTRIBUTING.md`
- 개발/테스트 루틴: `AGENTS.md`, `docs/handbook/CHAPTERS/06_quality_and_testing.md`

---

## License

EvalVault is licensed under the [Apache 2.0](LICENSE.md) license.
