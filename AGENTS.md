# Repository Guidelines

## Project Structure & Module Organization
EvalVault uses a hexagonal layout: `src/evalvault/domain` hosts entities, services, and metrics, `src/evalvault/ports` define contracts, and `src/evalvault/adapters` wire Typer CLI, LLM, storage, and tracing integrations. Runtime profiles and secrets live in `config/` (notably `models.yaml`) plus `.env`, while datasets sit in `data/` and curated fixtures in `tests/fixtures/`. Docs that clarify architecture and roadmap live under `docs/`, and automation helpers remain in `scripts/`. Mirror production modules with tests in `tests/unit`, `tests/integration`, and `tests/e2e_data` to preserve coverage.

## Build, Test, and Development Commands
- `uv sync --extra dev`: install full development environment (dev tools + all feature extras) on Python 3.12.
- `uv sync --extra <analysis|korean|postgres|mlflow|phoenix|docs|anthropic|perf>`: install only selected feature extras (omit dev tooling).
  - `--extra korean`: Korean NLP (kiwipiepy, rank-bm25, sentence-transformers)
  - `--extra analysis`: Statistical/NLP analysis helpers (scikit-learn)
  - `--extra postgres`: PostgreSQL storage support
  - `--extra mlflow`: MLflow tracker integration
- `uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness`: smoke-test the CLI; extend with `--profile dev` or `--langfuse`.
- `uv run evalvault serve-api --reload`: launch the FastAPI backend for the React UI.
- `cd frontend && npm install && npm run dev`: launch the Vite React frontend (API must be running).
- `uv run evalvault pipeline analyze "요약해줘"`: run query-based analysis pipeline (requires `--extra korean`).
- `uv run pytest tests -v`: primary suite (1352 tests: 1261 unit + 91 integration); target `tests/integration/test_e2e_scenarios.py` only when external APIs are configured.
- `uv run ruff check src/ tests/ && uv run ruff format src/ tests/`: keep style/lint errors out of CI (line length 100).
- `docker compose -f docker-compose.langfuse.yml up`: optional Langfuse playground for tracing comparisons.
- vLLM (optional): set `EVALVAULT_PROFILE=vllm` and configure `VLLM_BASE_URL`/`VLLM_MODEL` in `.env`.

## Coding Style & Naming Conventions
Adhere to Ruff’s config (Py312, line length 100) and keep modules fully type-hinted. Modules/functions use snake_case, classes PascalCase (e.g., `EvaluationRunService`), and CLI commands stay terse verbs. Favor dependency injection through ports, keep adapters free of domain assumptions, and add concise docstrings whenever orchestration is non-obvious.

## Testing Guidelines
Place focused unit specs in `tests/unit`, adapter/infrastructure checks in `tests/integration`, and long-running datasets under `tests/e2e_data`. Stick to `test_<behavior>` naming, mark async code with `pytest.mark.asyncio`, and prefer fixtures in `tests/fixtures/` over ad-hoc inline payloads. Run `pytest --cov=src --cov-report=term` whenever evaluation metrics or scoring orchestration changes, and document external dependencies (OPENAI, Ollama) inside the test docstring so CI skips gracefully.

## Commit & Pull Request Guidelines
History shows Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`); keep the subject under ~72 chars and call out the subsystem (`feat(metrics): ...`). Each PR must link the issue, note user impact, enumerate new CLI flags or config keys, and paste the latest `pytest`/`ruff` summary. Attach screenshots or Langfuse run IDs for UX or tracing tweaks, and explicitly flag breaking schema/profile changes in both the PR body and affected docs.

### Automatic Versioning (python-semantic-release)
main 브랜치에 머지되면 Conventional Commits 규칙에 따라 자동으로 버전이 결정되고 PyPI에 배포됩니다:
- `feat:` → Minor version bump (0.x.0)
- `fix:`, `perf:` → Patch version bump (0.0.x)
- `docs:`, `chore:`, `ci:`, `test:`, `style:`, `refactor:` → No release

**주의**: `pyproject.toml`의 버전은 릴리스 워크플로에서 git 태그와 동기화됨. 실제 배포 버전은 git 태그 기반.

## CI/CD Pipeline
CI는 Ubuntu, macOS, Windows에서 Python 3.12/3.13으로 테스트를 실행합니다. PR 머지 전 모든 테스트와 린트가 통과해야 합니다. main 브랜치 푸시 시 Release 워크플로우가 자동으로 버전 태그 생성, PyPI 배포, GitHub Release 생성을 수행합니다.

## Security & Configuration Tips
Do not commit `.env`; copy `.env.example`, inject `OPENAI_API_KEY` or Ollama host values locally, and keep profile overrides in `config/models.yaml`. Supply Langfuse keys via environment variables (or the provided Compose file) and scrub customer data from fixtures before attaching them to issues.

## Parallel Work Approval (공유 스키마/공유 파일)
병렬 작업 시 충돌을 방지하기 위해, 아래 공유 파일/스키마는 변경 전에 승인 절차를 거친다.

**Shared files**
- `src/evalvault/adapters/inbound/cli/commands/__init__.py`
- `src/evalvault/adapters/inbound/cli/app.py`
- `src/evalvault/domain/services/async_batch_executor.py`
- 리포트 템플릿/공통 JSON 스키마 정의 문서

**Shared schemas**
- `artifacts/index.json`
- CLI JSON envelope
- stage metrics naming conventions
- comparison/benchmark output JSON

**Approval workflow**
1. 변경 요청 등록 (작업 ID, 오너, 목적 명시)
2. 영향 범위 검토 — 관련 에픽 오너 확인
3. 변경 승인 — 2명 이상 승인 권장
4. 변경 적용 + 검증 (테스트/리포트 재생성)
5. 변경 로그 기록 (run_id 또는 작업 ID 연결)

**원칙**
- 승인 없는 공유 스키마/파일 변경 금지
- 공통 포맷 변경 시 관련 문서/테스트 업데이트 동반
- `commands/__init__.py` 수정은 반드시 승인 필요

**Change request template**
```
[CHANGE REQUEST]
- Work ID:
- Owner:
- Target File/Schema:
- Reason:
- Impacted Epics:
- Validation Plan:
- Rollback Plan:
```

# 표시 방법
사용자에게는 반드시 한글 위주로 설명해줘야 함.
