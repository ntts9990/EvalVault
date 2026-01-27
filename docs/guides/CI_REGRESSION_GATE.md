# CI 회귀 게이트 (Regression Gate)

EvalVault의 회귀 게이트는 CI에서 **핵심 CLI 흐름이 깨지지 않았는지** 빠르게 확인하는 안전장치입니다.

## 목적
- PR/릴리즈마다 핵심 CLI 경로를 최소 비용으로 재검증
- API 키 없이 실행 가능한 스위트만 사용

## 구성

### 설정 파일
- `config/regressions/ci.json`
  - `unit-cli-gate`: gate 관련 CLI 유닛 테스트
  - `integration-cli-e2e`: API 키 없이 가능한 CLI e2e 스모크

### 실행 스크립트
- `scripts/ci/run_regression_gate.py`

## 로컬 실행

```bash
uv run python scripts/ci/run_regression_gate.py \
  --config config/regressions/ci.json \
  --format text
```

## CI 통합

- `.github/workflows/ci.yml`의 `regression-gate` job에서 실행
- 실패 시 CI가 실패하며, GitHub Actions 로그에 실패 스위트가 표시됩니다.

## 실패 기준
- 어떤 스위트든 실패 시 게이트 실패

## 요약 파일
- `reports/regression/ci_gate.json`에 요약이 저장됩니다.
