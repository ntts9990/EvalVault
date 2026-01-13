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
- 관련 문서: `docs/guides/USER_GUIDE.md`

---

## 지원 메트릭(대표)

- Ragas 계열: `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`, `factual_correctness`, `semantic_similarity`
- 커스텀 예시(도메인): `insurance_term_accuracy`

정확한 옵션/운영 레시피는 `docs/guides/USER_GUIDE.md`를 기준으로 최신화합니다.

---

## RAGAS 0.4.2 데이터 전처리/후처리 (중요)

아래 항목은 **RAGAS 0.4.2 기준**으로 EvalVault가 데이터와 점수를 안정화하기 위해 수행하는 처리들입니다. 모두 재현성과 품질 저하 방지를 위해 의도적으로 설계되었습니다.

### 1) 데이터 전처리 (입력 안정화)
- **빈 질문/답변/컨텍스트 제거**: 평가 불가능한 케이스를 사전에 제거합니다. (`src/evalvault/domain/services/dataset_preprocessor.py`)
- **컨텍스트 정규화**: 공백 정리, 중복 제거, 길이 제한을 통해 컨텍스트 품질을 표준화합니다. (`src/evalvault/domain/services/dataset_preprocessor.py`)
- **레퍼런스 보완**: 레퍼런스가 필요한 메트릭에서 부족할 경우 질문/답변/컨텍스트 기반으로 보완합니다. (`src/evalvault/domain/services/dataset_preprocessor.py`)

**이유**: 입력 품질 편차로 인해 RAGAS 점수 분산이 커지는 것을 방지하고, 메트릭 실행 실패/왜곡을 줄입니다.

### 2) 한국어/비영어권 대응 (프롬프트 언어 정렬)
- **한국어 데이터셋 자동 감지** 후 `answer_relevancy`, `factual_correctness`에 한국어 프롬프트를 기본 적용합니다. (`src/evalvault/domain/services/evaluator.py`)
- **사용자 프롬프트 오버라이드 지원**: 필요 시 YAML로 메트릭별 프롬프트를 덮어쓸 수 있습니다. (`src/evalvault/domain/services/ragas_prompt_overrides.py`)
- **외부 근거(비영어권 이슈)**:
  - https://github.com/explodinggradients/ragas/issues/1829
  - https://github.com/explodinggradients/ragas/issues/402
- **공식 문서(언어 이슈 직접 언급)**:
  - https://docs.ragas.io/en/stable/howtos/customizations/metrics/_metrics_language_adaptation/

**이유**: 질문 생성/판정 프롬프트가 영어에 고정될 경우, 비영어 입력에서 언어 불일치로 점수 왜곡이 발생할 수 있으므로 이를 최소화합니다.

### 3) 점수 후처리 (안정성 확보)
- **비숫자/NaN 점수는 0.0 처리**: 메트릭 실패가 전체 파이프라인을 중단시키지 않도록 방어합니다. (`src/evalvault/domain/services/evaluator.py`)
- **Faithfulness 폴백**: RAGAS가 실패하거나 한국어 텍스트에서 불안정할 경우, 한국어 전용 claim-level 분석으로 점수를 재구성합니다. (`src/evalvault/domain/services/evaluator.py`)

**이유**: LLM/임베딩 실패나 NaN으로 인해 결과가 끊기는 문제를 방지하고, 한국어에서 최소한의 신뢰도를 확보하기 위해서입니다.

### 4) 요약/시각화 후처리 (비교 가능성 강화)
- **임계값 기준 정규화**: threshold를 0점 기준으로 정규화하여 성능 개선/악화를 직관적으로 표시합니다. (`src/evalvault/domain/services/visual_space_service.py`)
- **가중 합산**: `faithfulness`, `factual_correctness`, `answer_relevancy` 등을 가중 결합하여 축/지표로 요약합니다. (`src/evalvault/domain/services/visual_space_service.py`)

**이유**: 단일 지표만으로는 해석이 어려운 경우가 많아, 정책적 기준(임계값)과 함께 비교 가능한 요약 점수로 제공하기 위함입니다.

---

## 모델/프로필 설정(요약)

- 프로필 정의: `config/models.yaml`
- 공통 환경 변수(예):
  - `EVALVAULT_PROFILE`
  - `EVALVAULT_DB_PATH`
  - `OPENAI_API_KEY` 또는 `OLLAMA_BASE_URL` 등
- 관련 문서: `docs/guides/USER_GUIDE.md`, `docs/guides/DEV_GUIDE.md`, `config/models.yaml`

---

## Open RAG Trace (외부 RAG 시스템까지 통합)

EvalVault는 OpenTelemetry + OpenInference 기반의 **Open RAG Trace** 스키마를 제공해, 외부/내부 RAG 시스템을 동일한 방식으로 계측/수집/분석할 수 있게 합니다.

- 스펙: `docs/architecture/open-rag-trace-spec.md`
- Collector: `docs/architecture/open-rag-trace-collector.md`
- 샘플/내부 래퍼: `docs/guides/OPEN_RAG_TRACE_SAMPLES.md`, `docs/guides/OPEN_RAG_TRACE_INTERNAL_ADAPTER.md`
- 관련 문서: `docs/INDEX.md`, `docs/architecture/open-rag-trace-collector.md`

---

## 개발/기여

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pytest tests -v
```

- 기여 가이드: `CONTRIBUTING.md`
- 개발 루틴: `docs/guides/DEV_GUIDE.md`
- 관련 문서: `docs/STATUS.md`, `docs/ROADMAP.md`

---

## 문서

- `docs/INDEX.md`: 문서 허브
- `docs/STATUS.md`, `docs/ROADMAP.md`: 현재 상태/방향
- `docs/guides/USER_GUIDE.md`: 사용/운영 종합
- `docs/new_whitepaper/INDEX.md`: 설계/운영/품질 기준(전문가 관점)

---

## License

EvalVault is licensed under the [Apache 2.0](LICENSE.md) license.
