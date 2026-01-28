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

## CI Gate CLI 종료 코드 정책

`evalvault ci-gate`는 CI/CD 스크립트에서 종료 코드로 상태를 판별합니다.

- `0`: 성공 (게이트 통과)
- `1`: 임계치 미달/검증 실패 또는 잘못된 입력 (예: DB 경로 누락, 잘못된 포맷)
- `2`: 회귀 감지 및 `--fail-on-regression` 활성화
- `3`: 런 조회 실패/데이터 누락 등 **복구 불가능한 오류**
