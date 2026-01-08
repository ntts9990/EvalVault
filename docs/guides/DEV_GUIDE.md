# EvalVault 개발 가이드 (Dev Guide)

> Audience: 기여자/개발자
> Purpose: 로컬 개발·테스트·린트·문서 갱신의 기본 루틴을 표준화
> Last Updated: 2026-01-06

---

## 개발 환경 준비

권장: Python 3.12 + `uv`

```bash
uv sync --extra dev
```

`dev`는 모든 extras를 포함합니다. 경량 설치가 필요하면 dev 대신 개별 extras만 선택하세요:
- `--extra korean`: 한국어 NLP
- `--extra analysis`: 통계/NLP 분석 보조
- `--extra postgres`: PostgreSQL 저장소
- `--extra mlflow`: MLflow tracker
- `--extra phoenix`: Phoenix 트레이싱
- `--extra docs`: MkDocs 문서 빌드
- `--extra anthropic`: Anthropic LLM 어댑터
- `--extra perf`: FAISS/JSON 스트리밍 등 성능 보조

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

Web UI (React + FastAPI):

```bash
# FastAPI 서버
uv run evalvault serve-api --reload

# 프론트엔드
cd frontend
npm install
npm run dev
```

환경 변수:
- `VITE_API_PROXY_TARGET`: Vite 프록시 대상 (기본: `http://localhost:8000`)
- `VITE_API_BASE_URL`: 프록시 없이 직접 호출할 때 API 주소
- `CORS_ORIGINS`: API 서버 허용 오리진 (예: `http://localhost:5173`)

---

## 문서 작업 규칙 (Docs)

- "내부 상태"는 [internal/status/STATUS.md](../internal/status/STATUS.md)가 단일 출처(SSoT)입니다.
- 사용자 문서는 `README.ko.md`(루트)/`docs/guides/USER_GUIDE.md`/`docs/tutorials/`에, 내부 설계/운영은 `docs/internal/`에 둡니다.
- 새 문서를 추가하면 [INDEX.md](../INDEX.md)와 `mkdocs.yml` 네비게이션을 함께 갱신합니다.
- [INDEX.md](../INDEX.md)는 문서 허브로 유지합니다.
- 튜토리얼 코드는 `scripts/validate_tutorials.py`로 검증합니다.
  - 실행: `uv run python scripts/validate_tutorials.py`
- 문서 스타일 가이드는 [internal/reference/STYLE_GUIDE.md](../internal/reference/STYLE_GUIDE.md)를 따릅니다.

---

## 더 자세한 정보

- **상세 개발 가이드**: [internal/reference/DEVELOPMENT_GUIDE.md](../internal/reference/DEVELOPMENT_GUIDE.md) - 아키텍처 원칙, 코드 품질, AI 에이전트 시스템
- **기능 스펙**: [internal/reference/FEATURE_SPECS.md](../internal/reference/FEATURE_SPECS.md) - 한국어 RAG, Phoenix, Domain Memory 등
- **클래스 카탈로그**: [internal/reference/CLASS_CATALOG.md](../internal/reference/CLASS_CATALOG.md)
