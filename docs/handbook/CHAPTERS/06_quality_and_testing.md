# 06. Quality & Testing

## 목표

테스트/회귀 게이트/품질 기준을 이해하고, 변경이 실제 개선인지 검증하는 방법을 정리한다.

## 품질 게이트 개요

- CI 기본: `../../.github/workflows/ci.yml`
- 회귀 게이트: `../../.github/workflows/regression-gate.yml`
- 회귀 실행 스크립트: `../../scripts/ci/run_regression_gate.py`

## 테스트 구성

- pytest/ruff 설정: `../../pyproject.toml`
- 유닛 테스트: `../../tests/unit/`
- 통합 테스트: `../../tests/integration/`
- E2E 시나리오: `../../tests/integration/test_e2e_scenarios.py`

## 회귀 게이트 설정

- 설정 파일: `../../config/regressions/ci.json`, `../../config/regressions/default.json`, `../../config/regressions/ux.json`
- 서비스 로직: `../../src/evalvault/domain/services/regression_gate_service.py`
- 러너: `../../src/evalvault/scripts/regression_runner.py`

## 표준 명령

테스트:
- `uv run pytest tests -v`
- `uv run pytest --cov=src --cov-report=term`

린트/포맷:
- `uv run ruff check src/ tests/`
- `uv run ruff format src/ tests/`

회귀 게이트:
- `uv run python scripts/ci/run_regression_gate.py --config config/regressions/ci.json --format text`

## 참고

- 개발 가이드: `../guides/DEV_GUIDE.md`
- 회귀 게이트: `../guides/CI_REGRESSION_GATE.md`
- 릴리즈 체크리스트: `../guides/RELEASE_CHECKLIST.md`
- 품질 백서: `../new_whitepaper/09_quality.md`
- 테스트: `../../tests/`
