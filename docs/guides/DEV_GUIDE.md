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

## 타입체크 (Pyright 비활성화)

EvalVault는 Ruff만 사용합니다. Pyright/Pylance 경고가 보이면 에디터 설정을 끄세요.

- VS Code: 확장(“Pylance”, “Pyright”) 비활성화 또는 제거
- VS Code 설정 예시: `"python.analysis.typeCheckingMode": "off"`

---

## 문서 작업 규칙 (Docs)

- `docs/`는 **현재 프로젝트에 필요한 문서만** 유지합니다. (중복/과거 정보는 삭제)
- 새 문서를 추가/삭제하면 `docs/INDEX.md`와 `mkdocs.yml` 네비게이션을 함께 갱신합니다.
- 문서 스타일/업데이트 규칙은 `docs/new_whitepaper/STYLE_GUIDE.md`를 기준으로 합니다.

---

## 더 자세한 정보

- 설계/컴포넌트/운영 기준: `docs/new_whitepaper/INDEX.md`
- CLI→MCP 이식 계획: `docs/guides/CLI_MCP_PLAN.md`
- Open RAG Trace 스펙/샘플: `docs/architecture/open-rag-trace-spec.md`, `docs/guides/OPEN_RAG_TRACE_SAMPLES.md`
- 실행 결과 엑셀 컬럼 설명: `docs/guides/EVALVAULT_RUN_EXCEL_SHEETS.md`
