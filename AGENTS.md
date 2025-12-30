# Repository Guidelines

## Project Structure & Module Organization
EvalVault uses a hexagonal layout: `src/evalvault/domain` hosts entities, services, and metrics, `src/evalvault/ports` define contracts, and `src/evalvault/adapters` wire Typer CLI, LLM, storage, and tracing integrations. Runtime profiles and secrets live in `config/` (notably `models.yaml`) plus `.env`, while datasets sit in `data/` and curated fixtures in `tests/fixtures/`. Docs that clarify architecture and roadmap live under `docs/`, and automation helpers remain in `scripts/`. Mirror production modules with tests in `tests/unit`, `tests/integration`, and `tests/e2e_data` to preserve coverage.

## Build, Test, and Development Commands
- `uv sync --extra dev`: install basic runtime plus dev tooling on Python 3.12.
- `uv sync --extra dev --extra korean --extra web`: install full development environment (recommended).
  - `--extra korean`: Korean NLP (kiwipiepy, rank-bm25)
  - `--extra web`: Streamlit Web UI (streamlit, plotly)
  - `--extra postgres`: PostgreSQL storage support
  - `--extra mlflow`: MLflow tracker integration
- `uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness`: smoke-test the CLI; extend with `--profile dev` or `--langfuse`.
- `uv run evalvault web`: launch Streamlit Web UI (requires `--extra web`).
- `uv run evalvault pipeline analyze "요약해줘"`: run query-based analysis pipeline (requires `--extra korean`).
- `uv run pytest tests -v`: primary suite (1244 tests); target `tests/integration/test_e2e_scenarios.py` only when external APIs are configured.
- `uv run ruff check src/ tests/ && uv run ruff format src/ tests/`: keep style/lint errors out of CI (line length 100).
- `docker compose -f docker-compose.langfuse.yml up`: optional Langfuse playground for tracing comparisons.

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

**주의**: `pyproject.toml`의 버전은 자동 업데이트되지 않음. 실제 배포 버전은 git 태그 기반.

## CI/CD Pipeline
CI는 Ubuntu, macOS, Windows에서 Python 3.12/3.13으로 테스트를 실행합니다. PR 머지 전 모든 테스트와 린트가 통과해야 합니다. main 브랜치 푸시 시 Release 워크플로우가 자동으로 버전 태그 생성, PyPI 배포, GitHub Release 생성을 수행합니다.

## Security & Configuration Tips
Do not commit `.env`; copy `.env.example`, inject `OPENAI_API_KEY` or Ollama host values locally, and keep profile overrides in `config/models.yaml`. Supply Langfuse keys via environment variables (or the provided Compose file) and scrub customer data from fixtures before attaching them to issues.

# 표시 방법
사용자에게는 반드시 한글 위주로 설명해줘야 함.
