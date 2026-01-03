# EvalVault 개발 가이드 (Dev Guide)

> Audience: 기여자/개발자
> Purpose: 로컬 개발·테스트·린트·문서 갱신의 기본 루틴을 표준화
> Last Updated: 2026-01-03

---

## 개발 환경 준비

권장: Python 3.12 + `uv`

```bash
uv sync --extra dev
```

기능별 extras(선택):

- `--extra web`: Streamlit Web UI
- `--extra korean`: 한국어 NLP
- `--extra analysis`: 통계/NLP 분석 보조
- `--extra postgres`: PostgreSQL 저장소
- `--extra mlflow`: MLflow tracker

---

## 자주 쓰는 명령 (로컬 개발 루틴)

```bash
# 테스트
uv run pytest tests -v

# 린트/포맷 (Ruff)
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

스모크 테스트(예):

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness
```

Web UI:

```bash
uv run evalvault web
```

---

## 문서 작업 규칙 (Docs)

- "현재 상태"는 [STATUS.md](STATUS.md)가 단일 출처(SSoT)입니다.
- 사용자 문서는 `README.ko.md`/`USER_GUIDE.md`/`tutorials/`에, 내부 설계/운영은 `internal/`에 둡니다.
- 새 문서를 추가하면 [README.md](README.md)에 링크를 반드시 추가합니다.

---

## 더 자세한 정보

- **상세 개발 가이드**: [internal/DEVELOPMENT_GUIDE.md](internal/DEVELOPMENT_GUIDE.md) - 아키텍처 원칙, 코드 품질, AI 에이전트 시스템
- **기능 스펙**: [internal/FEATURE_SPECS.md](internal/FEATURE_SPECS.md) - 한국어 RAG, Phoenix, Domain Memory 등
- **클래스 카탈로그**: [internal/CLASS_CATALOG.md](internal/CLASS_CATALOG.md)
