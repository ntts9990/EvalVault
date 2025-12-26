# Repository Guidelines

## Project Structure & Module Organization
EvalVault uses a hexagonal layout: `src/evalvault/domain` hosts entities, services, and metrics, `src/evalvault/ports` define contracts, and `src/evalvault/adapters` wire Typer CLI, LLM, storage, and tracing integrations. Runtime profiles and secrets live in `config/` (notably `models.yaml`) plus `.env`, while datasets sit in `data/` and curated fixtures in `tests/fixtures/`. Docs that clarify architecture and roadmap live under `docs/`, and automation helpers remain in `scripts/`. Mirror production modules with tests in `tests/unit`, `tests/integration`, and `tests/e2e_data` to preserve coverage.

## Build, Test, and Development Commands
- `uv pip install -e ".[dev]"`: install runtime plus dev tooling on Python 3.12.
- `evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness`: smoke-test the CLI; extend with `--profile dev` or `--langfuse`.
- `pytest tests -v`: primary suite; target `tests/integration/test_e2e_scenarios.py` only when external APIs are configured.
- `ruff check src/ tests/ && ruff format src/ tests/`: keep style/lint errors out of CI (line length 100).
- `docker compose -f docker-compose.langfuse.yml up`: optional Langfuse playground for tracing comparisons.

## Coding Style & Naming Conventions
Adhere to Ruff’s config (Py312, line length 100) and keep modules fully type-hinted. Modules/functions use snake_case, classes PascalCase (e.g., `EvaluationRunService`), and CLI commands stay terse verbs. Favor dependency injection through ports, keep adapters free of domain assumptions, and add concise docstrings whenever orchestration is non-obvious.

## Testing Guidelines
Place focused unit specs in `tests/unit`, adapter/infrastructure checks in `tests/integration`, and long-running datasets under `tests/e2e_data`. Stick to `test_<behavior>` naming, mark async code with `pytest.mark.asyncio`, and prefer fixtures in `tests/fixtures/` over ad-hoc inline payloads. Run `pytest --cov=src --cov-report=term` whenever evaluation metrics or scoring orchestration changes, and document external dependencies (OPENAI, Ollama) inside the test docstring so CI skips gracefully.

## Commit & Pull Request Guidelines
History shows Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`); keep the subject under ~72 chars and call out the subsystem (`feat(metrics): ...`). Each PR must link the issue, note user impact, enumerate new CLI flags or config keys, and paste the latest `pytest`/`ruff` summary. Attach screenshots or Langfuse run IDs for UX or tracing tweaks, and explicitly flag breaking schema/profile changes in both the PR body and affected docs.

## Security & Configuration Tips
Do not commit `.env`; copy `.env.example`, inject `OPENAI_API_KEY` or Ollama host values locally, and keep profile overrides in `config/models.yaml`. Supply Langfuse keys via environment variables (or the provided Compose file) and scrub customer data from fixtures before attaching them to issues.

# 표시 방법
사용자에게는 반드시 한글 위주로 설명해줘야 함.