# 06. Quality & Testing (검증 문화, 자동 게이트, 신뢰 가능한 변경)

이 챕터는 EvalVault가 “변경을 안전하게 받아들이는 방법”을 정리한다.
핵심은 테스트의 양이 아니라, 회귀를 빠르게 잡고 원인을 빠르게 좁히는 시스템(명령/마커/CI/게이트)이다.

## TL;DR

- 빠른 피드백(유닛)과 계약 검증(통합)을 분리한다.
- CI는 “API 키 없는 상태”를 기본으로 테스트를 돌린다. (근거: `.github/workflows/ci.yml`)
- 회귀 게이트는 baseline 대비 성능 저하를 자동으로 판단해 PR을 차단할 수 있다. (근거: `.github/workflows/regression-gate.yml`, `src/evalvault/domain/services/regression_gate_service.py`)
- 린트/포맷(Ruff)은 스타일 논쟁을 제거하고, 리뷰를 “의미”에 집중하게 한다. (근거: `pyproject.toml#[tool.ruff]`)

## 목표

- 로컬에서 CI 수준의 검증을 재현한다.
- 테스트/마커/CI의 역할 분리를 이해하고, 실패 triage를 빠르게 한다.
- 회귀 게이트의 목적/입력/출력/exit code를 이해한다.

---

## 1) 품질의 정의(팀이 합의해야 하는 것)

EvalVault에서 품질은 단일 점수가 아니다.

- 기능 품질: 기능이 의도대로 동작하는가?
- 평가 품질: 메트릭 계산이 신뢰 가능한가(입력/전처리/threshold)?
- 운영 품질: 재현 가능한가(run_id/DB/아티팩트)?
- 변경 품질: 변경이 회귀를 만들지 않는가(게이트/회귀 탐지)?

---

## 2) 로컬에서 돌리는 표준 명령(= CI 재현의 최소 세트)

### 2.1 린트/포맷(Ruff)

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

근거:

- 개발/테스트 루틴: `AGENTS.md`
- Ruff 설정: `pyproject.toml#[tool.ruff]`, `pyproject.toml#[tool.ruff.lint]`

### 2.2 테스트(Pytest)

```bash
uv run pytest tests -v
```

커버리지(메트릭/스코어링/평가 로직에 영향이 있을 때 권장):

```bash
uv run pytest tests -v --cov=src --cov-report=term
```

근거:

- CI 실행: `.github/workflows/ci.yml`

### 2.3 (선택) xdist 병렬(로컬 속도 최적화)

pytest-xdist가 설치되어 있고 `EVALVAULT_XDIST` 환경변수를 주면 워커 수를 조정한다.

- 근거: `tests/conftest.py#pytest_configure`

예:

```bash
EVALVAULT_XDIST=auto uv run pytest tests -v
EVALVAULT_XDIST=4 uv run pytest tests -v
```

---

## 3) 테스트 전략(피라미드) + 레포의 실제 운영

### 3.1 유닛 테스트(빠르고 많은 수)

- 순수 로직(엔티티/서비스/메트릭)을 빠르게 검증
- 외부 의존(LLM/네트워크)은 최대한 배제

### 3.2 통합 테스트(경계/계약)

- 어댑터/포트 경계에서 동작을 검증
- 일부 테스트는 외부 시크릿이 필요할 수 있으며, 없으면 스킵된다.

근거(스킵 로직/마커): `tests/integration/conftest.py#pytest_runtest_setup`

### 3.3 “키가 없으면 스킵”을 명시적으로 관리한다

레포는 아래 마커를 사용해 외부 의존 테스트를 분리한다.

- `requires_openai`
- `requires_langfuse`
- `requires_phoenix`

근거:

- 마커 정의: `pyproject.toml#[tool.pytest.ini_options].markers`
- 스킵 로직: `tests/integration/conftest.py#pytest_runtest_setup`

---

## 4) CI가 실제로 하는 일(= 실패 triage의 지도)

### 4.1 test job: 멀티 OS + Python 매트릭스

- OS: ubuntu/macos/windows
- Python: 3.12 + (ubuntu에서 3.13)

근거: `.github/workflows/ci.yml`

### 4.2 기본 테스트는 “API 키 없이” 실행

CI는 기본 테스트에서 아래 마커를 제외한다.

- `requires_openai`
- `requires_langfuse`

근거: `.github/workflows/ci.yml` (pytest `-m "not requires_openai and not requires_langfuse"`)

### 4.3 lint job: docs build + 링크 체크 + 포맷/린트

CI는 문서가 깨지지 않도록 docs build/link check를 수행한다.

- docs build: `uv run mkdocs build -q`
- 링크 체크: workflow 내 python 스크립트

근거: `.github/workflows/ci.yml`

---

## 5) 회귀 게이트(Regression Gate): “점수 하락을 자동으로 실패 처리”

회귀 게이트는 두 층이 있다.

1) 통계 기반 회귀 판단(서비스): `RegressionGateService`
2) CI 친화 포맷/exit code(커맨드): `regress`, `ci-gate`, `regress-baseline`

### 5.1 통계 기반 회귀 판단(서비스)

- regression 기준: `comparison.diff < -fail_on_regression` (기본 0.05)
- 결과에는 p-value/effect size/유의성/회귀 여부가 포함된다.

근거: `src/evalvault/domain/services/regression_gate_service.py`

### 5.2 `regress`: 회귀 감지용 CLI

- 회귀가 감지되면 Exit(2)

근거: `src/evalvault/adapters/inbound/cli/commands/regress.py`

### 5.3 `ci-gate`: CI 통합용(요약 + PR 코멘트 포맷)

- 포맷: `github`, `gitlab`, `json`, `pr-comment`
- gate_passed 계산: (a) thresholds 통과 (b) regression_rate < regression_threshold
- 실패 시 exit code:
  - thresholds 실패: Exit(1)
  - gate 실패 + fail_on_regression=true: Exit(2)

근거: `src/evalvault/adapters/inbound/cli/commands/regress.py#ci_gate`

### 5.4 `regress-baseline`: baseline을 DB에 저장/조회

- `set`: baseline key에 run_id 저장
- `get`: baseline key의 run_id 출력

근거: `src/evalvault/adapters/inbound/cli/commands/regress.py#regress_baseline`

### 5.5 GitHub Actions 회귀 게이트 워크플로

레포에는 “main에서 baseline DB artifact를 저장”하고 “PR에서 baseline을 가져와 비교/코멘트”하는 워크플로가 있다.

- 워크플로: `.github/workflows/regression-gate.yml`

---

## 6) 실패 triage(실전)

### 6.1 Ruff 실패

- `uv run ruff check src/ tests/`부터 재현
- 포맷 이슈는 `uv run ruff format src/ tests/`로 해결

근거: `AGENTS.md`, `pyproject.toml#[tool.ruff]`

### 6.2 테스트 실패

1) 로컬에서 동일 명령으로 재현: `uv run pytest tests -v`
2) 외부 의존 테스트인지 확인: `requires_*` 마커 여부
3) 스킵이 아니라 실패라면, 테스트가 외부 의존을 “숨겨서” 호출하고 있는지 점검

근거:

- 마커/스킵 로직: `tests/integration/conftest.py`
- CI의 기본 마커 제외: `.github/workflows/ci.yml`

### 6.3 docs build/link check 실패

```bash
uv sync --extra docs
uv run mkdocs build -q
```

근거: `.github/workflows/ci.yml`

### 6.4 회귀 게이트 실패

1) baseline/current 조건이 동일한지 확인(데이터셋/메트릭/threshold)
2) `ci-gate` 출력에서 regressed_metrics/threshold_failures 확인
3) 원인 분석은 리포트/아티팩트(index.json)로 내려간다

근거:

- ci-gate 계산/출력: `src/evalvault/adapters/inbound/cli/commands/regress.py#ci_gate`
- 아티팩트 인덱스: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`

---

## 7) 테스트 작성 가이드(실수 방지)

### 7.1 좋은 테스트의 조건

- 한 테스트는 한 행동(behavior)을 검증한다.
- 실패 시 원인이 명확하다.
- 입력/기대 결과가 작고 명확하다.

### 7.2 흔한 실수

- 외부 API 호출이 섞여 불안정해지는 테스트
- 하나의 테스트가 너무 많은 것을 검증
- 픽스처/데이터셋이 비현실적으로 커져 실행 시간이 폭발

---

## 8) 릴리즈 관점 체크리스트(개발자/리뷰어 공통)

- [ ] 새 기능은 유닛 테스트로 최소 1개 이상 커버되는가?
- [ ] 어댑터/포트 변경은 통합 테스트로 최소 1개 이상 커버되는가?
- [ ] CI에서 “키 없는 기본 모드”로도 안정적으로 통과하는가?
- [ ] 회귀 게이트가 의미 있게 동작하도록 baseline/current 조건이 동일한가?

## 자기 점검 질문

1) CI 기본 테스트는 어떤 마커를 제외하고 도는가?
2) 회귀 게이트가 실패하면 어떤 정보(메트릭/threshold/조건)가 있어야 원인을 빠르게 좁힐 수 있나?
3) exit code 1/2/3은 각각 어떤 실패를 의미하는가(`regress`/`ci-gate` 기준)?

---

## 향후 변경 시 업데이트 가이드

- 테스트 마커/스킵 정책이 바뀜: `pyproject.toml`, `tests/integration/conftest.py`
- CI 워크플로가 바뀜: `.github/workflows/ci.yml`, `.github/workflows/regression-gate.yml`
- 회귀 게이트 판단 로직이 바뀜: `src/evalvault/domain/services/regression_gate_service.py`
