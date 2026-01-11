# EvalVault

RAG(Retrieval-Augmented Generation) 시스템을 대상으로 **평가(Eval) → 분석(Analysis) → 추적(Tracing) → 개선 루프**를 하나의 워크플로로 묶는 CLI + Web UI 플랫폼입니다.

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)

English version? See `README.en.md`.

---

## Quick Links

- 문서 허브: `docs/INDEX.md`
- 사용자 가이드: `docs/guides/USER_GUIDE.md`
- 개발 가이드: `docs/guides/DEV_GUIDE.md`
- 상태/로드맵: `docs/STATUS.md`, `docs/ROADMAP.md`
- 개발 백서(설계/운영/품질 기준): `docs/new_whitepaper/INDEX.md`
- Open RAG Trace: `docs/architecture/open-rag-trace-spec.md`

---

## EvalVault가 해결하는 문제

RAG를 운영하다 보면 결국 아래 질문으로 귀결됩니다.

- “모델/프롬프트/리트리버를 바꿨는데, **진짜 좋아졌나?**”
- “좋아졌다면 **왜** 좋아졌고, 나빠졌다면 **어디서** 깨졌나?”
- “이 결론을 **재현 가능하게** 팀/CI에서 계속 검증할 수 있나?”

EvalVault는 위 질문을 **데이터셋 + 메트릭 + (선택)트레이싱** 관점에서 한 번에 답할 수 있게 설계했습니다.

---

## 핵심 개념

- **Run 단위**: 평가/분석/아티팩트/트레이스가 하나의 `run_id`로 묶입니다.
- **Dataset 중심**: threshold(합격 기준)는 데이터셋에 포함되어 “도메인별 합격 기준”을 유지합니다.
- **Artifacts-first**: 보고서(요약)뿐 아니라, 분석 모듈별 원본 결과(아티팩트)를 구조화된 디렉터리에 보존합니다.
- **Observability 옵션화**: Phoenix/Langfuse/MLflow는 “필요할 때 켜는” 방식으로, 실행 경로는 최대한 단순하게 유지합니다.

---

## 3분 Quickstart (CLI)

```bash
uv sync --extra dev
cp .env.example .env

uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db \
  --auto-analyze
```

- 결과는 `--db`에 저장되어 `history`, Web UI, 비교 분석에서 재사용됩니다.
- `--auto-analyze`는 요약 리포트 + 모듈별 아티팩트를 함께 생성합니다.

---

## Web UI (FastAPI + React)

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

## 산출물(Artifacts) 경로

- 단일 실행 자동 분석:
  - 요약 JSON: `reports/analysis/analysis_<RUN_ID>.json`
  - 보고서: `reports/analysis/analysis_<RUN_ID>.md`
  - 아티팩트 인덱스: `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`
  - 노드별 결과: `reports/analysis/artifacts/analysis_<RUN_ID>/<node_id>.json`

- A/B 비교 분석:
  - 요약 JSON: `reports/comparison/comparison_<RUN_A>_<RUN_B>.json`
  - 보고서: `reports/comparison/comparison_<RUN_A>_<RUN_B>.md`

---

## 데이터셋 포맷(요약)

```json
{
  "name": "insurance-qa",
  "version": "1.0.0",
  "thresholds": { "faithfulness": 0.8 },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "...",
      "answer": "...",
      "contexts": ["..."]
    }
  ]
}
```

- 필수 필드: `id`, `question`, `answer`, `contexts`
- `ground_truth`는 일부 메트릭에서 필요합니다.
- 템플릿: `docs/templates/dataset_template.json`, `docs/templates/dataset_template.csv`, `docs/templates/dataset_template.xlsx`

---

## 지원 메트릭(대표)

- Ragas 계열: `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`, `factual_correctness`, `semantic_similarity`
- 커스텀 예시(도메인): `insurance_term_accuracy`

정확한 옵션/운영 레시피는 `docs/guides/USER_GUIDE.md`를 기준으로 최신화합니다.

---

## 모델/프로필 설정(요약)

- 프로필 정의: `config/models.yaml`
- 공통 환경 변수(예):
  - `EVALVAULT_PROFILE`
  - `EVALVAULT_DB_PATH`
  - `OPENAI_API_KEY` 또는 `OLLAMA_BASE_URL` 등

---

## Open RAG Trace (외부 RAG 시스템까지 통합)

EvalVault는 OpenTelemetry + OpenInference 기반의 **Open RAG Trace** 스키마를 제공해, 외부/내부 RAG 시스템을 동일한 방식으로 계측/수집/분석할 수 있게 합니다.

- 스펙: `docs/architecture/open-rag-trace-spec.md`
- Collector: `docs/architecture/open-rag-trace-collector.md`
- 샘플/내부 래퍼: `docs/guides/open-rag-trace-samples.md`, `docs/guides/open-rag-trace-internal-adapter.md`

---

## 개발/기여

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pytest tests -v
```

- 기여 가이드: `CONTRIBUTING.md`
- 개발 루틴: `docs/guides/DEV_GUIDE.md`

---

## 문서

- `docs/INDEX.md`: 문서 허브
- `docs/STATUS.md`, `docs/ROADMAP.md`: 현재 상태/방향
- `docs/guides/USER_GUIDE.md`: 사용/운영 종합
- `docs/new_whitepaper/INDEX.md`: 설계/운영/품질 기준(전문가 관점)

---

## License

EvalVault is licensed under the [Apache 2.0](LICENSE.md) license.
