# Project Structure Review

> 작성일: 2025-12-28
> 상태: 검토 완료

---

## 현재 구조 개요

```
EvalVault/
├── .github/                    # GitHub 워크플로우 및 템플릿
│   ├── workflows/              # CI, Release 워크플로우
│   ├── ISSUE_TEMPLATE/         # 이슈 템플릿
│   ├── dependabot.yml
│   ├── pull_request_template.md
│   └── stale.yml
├── config/                     # 런타임 설정 (YAML)
│   └── models.yaml             # 모델 프로필 정의
├── data/                       # 로컬 데이터 (문제 있음 ⚠️)
│   ├── datasets/               # 샘플 데이터셋 (중복)
│   ├── e2e_results/
│   └── evaluations.db          # 로컬 DB (잘못 추적됨)
├── docs/                       # 문서
│   ├── assets/                 # 이미지 등 에셋
│   ├── ARCHITECTURE.md
│   ├── KG_IMPROVEMENT_PLAN.md
│   ├── README.ko.md
│   ├── ROADMAP.md
│   └── USER_GUIDE.md
├── examples/                   # 예제 코드
│   └── kg_generator_demo.py
├── reports/                    # 테스트 리포트 (생성됨)
│   └── .gitkeep
├── scripts/                    # 유틸리티 스크립트
│   ├── run_with_timeout.py
│   ├── test_full_evaluation.py
│   └── verify_workflows.py
├── src/evalvault/              # 메인 소스 코드
│   ├── adapters/               # 어댑터 (Hexagonal)
│   │   ├── inbound/            # CLI
│   │   └── outbound/           # LLM, Dataset, Storage, Tracker
│   ├── config/                 # Python 설정
│   ├── domain/                 # 비즈니스 로직
│   │   ├── entities/           # 데이터 모델
│   │   ├── metrics/            # 커스텀 메트릭
│   │   ├── prompts/            # 다국어 프롬프트
│   │   └── services/           # 핵심 서비스
│   ├── ports/                  # 포트 인터페이스
│   └── utils/                  # 유틸리티
├── tests/                      # 테스트 스위트
│   ├── e2e_data/               # E2E 테스트 데이터 (중복 ⚠️)
│   ├── fixtures/               # 테스트 픽스처
│   │   └── e2e/                # E2E 픽스처
│   ├── integration/            # 통합 테스트
│   └── unit/                   # 단위 테스트
└── [Root Files]                # 프로젝트 루트 파일
```

---

## 발견된 문제점

### 1. Git 추적 오류 (Critical)

| 파일/폴더 | 현재 상태 | 문제점 |
|-----------|-----------|--------|
| `data/evaluations.db` | 추적됨 | 로컬 SQLite DB가 git에 포함됨 |
| `data/datasets/*.{csv,json,xlsx}` | 추적됨 | `tests/fixtures/`와 중복 |
| `reports/kg_stats_report.json` | 추적됨 | 생성된 리포트가 추적됨 |

### 2. 테스트 데이터 중복

```
tests/fixtures/              # 메인 픽스처 위치
tests/fixtures/e2e/          # E2E 픽스처
tests/e2e_data/              # 또 다른 E2E 데이터 (중복!)
data/datasets/               # 또 다른 샘플 데이터 (중복!)
```

**문제**: 동일 목적의 데이터가 4곳에 분산되어 있음

### 3. 루트 레벨 파일 과다

```
AGENTS.md           # AI 에이전트 지침
CHANGELOG.md        # 변경 이력
CLAUDE.md           # Claude Code 지침
CODE_OF_CONDUCT.md  # 행동 강령
CONTRIBUTING.md     # 기여 가이드
LICENSE.md          # 라이선스
README.md           # 메인 README
SECURITY.md         # 보안 정책
```

**평가**: GitHub 표준 파일들(CODE_OF_CONDUCT, CONTRIBUTING, LICENSE, README, SECURITY)은 루트에 있어야 함. AGENTS.md와 CLAUDE.md는 선택적으로 이동 가능.

---

## 권장 변경사항

### Phase 1: Git 추적 정리 (필수)

#### 1.1 `.gitignore` 업데이트

```gitignore
# 추가 필요
data/evaluations.db
data/e2e_results/
reports/*.json
reports/*.html
reports/*.xml
!reports/.gitkeep
```

#### 1.2 잘못 추적된 파일 제거

```bash
# 실행 필요
git rm --cached data/evaluations.db
git rm --cached data/datasets/sample_insurance_qa.*
git rm --cached reports/kg_stats_report.json
```

### Phase 2: 테스트 데이터 통합 (권장)

#### 현재 → 개선안

```
# 현재 (분산)
tests/fixtures/sample_dataset.*
tests/fixtures/e2e/*.{csv,json,xlsx}
tests/e2e_data/comprehensive_dataset.json
tests/e2e_data/insurance_document.txt
data/datasets/sample_insurance_qa.*

# 개선안 (통합)
tests/fixtures/
├── unit/                   # 단위 테스트용
│   └── sample_dataset.*
├── e2e/                    # E2E 테스트용 (기존 유지)
│   ├── insurance_qa_*.{csv,json,xlsx}
│   ├── edge_cases.*
│   ├── comprehensive_dataset.json
│   └── insurance_document.txt
└── README.md               # 픽스처 설명
```

#### 변경 작업

1. `tests/e2e_data/*` → `tests/fixtures/e2e/`로 이동
2. `data/datasets/` 삭제 (tests/fixtures와 중복)
3. `tests/fixtures/sample_dataset.*` → `tests/fixtures/unit/`로 이동

### Phase 3: 선택적 개선

#### 3.1 AI 지침 파일 이동 (선택)

```
# 현재
AGENTS.md
CLAUDE.md

# 개선안 (선택)
docs/ai/
├── AGENTS.md
└── CLAUDE.md
```

**주의**: IDE/AI 도구가 루트에서 이 파일들을 찾을 수 있으므로, 이동 시 심볼릭 링크 또는 해당 도구 설정 변경 필요.

#### 3.2 scripts/ 폴더 정리 (선택)

```
scripts/
├── dev/                    # 개발용 스크립트
│   └── run_with_timeout.py
└── ci/                     # CI용 스크립트
    ├── test_full_evaluation.py
    └── verify_workflows.py
```

---

## 변경하지 않아도 되는 부분

### Hexagonal Architecture (유지)

```
src/evalvault/
├── adapters/       # ✅ 올바른 구조
├── config/         # ✅ 올바른 구조
├── domain/         # ✅ 올바른 구조
├── ports/          # ✅ 올바른 구조
└── utils/          # ✅ 올바른 구조
```

### 설정 분리 (유지)

```
config/models.yaml          # ✅ 런타임 설정 (YAML)
src/evalvault/config/       # ✅ Python 설정 코드
```

이 분리는 올바름:
- `config/`: 사용자가 수정하는 런타임 설정
- `src/evalvault/config/`: 개발자가 작성한 설정 코드

### 문서 구조 (유지)

```
docs/
├── ARCHITECTURE.md     # ✅
├── ROADMAP.md          # ✅
├── USER_GUIDE.md       # ✅
└── README.ko.md        # ✅
```

---

## 실행 계획

### 즉시 적용 (Phase 1)

1. `.gitignore` 업데이트
2. 잘못 추적된 파일 git에서 제거
3. 커밋: `chore: Clean up git tracking for local files`

### 차후 적용 (Phase 2)

1. 테스트 픽스처 통합
2. 중복 데이터 제거
3. 커밋: `refactor: Consolidate test fixtures`

### 선택적 적용 (Phase 3)

1. 팀 합의 후 진행
2. AI 지침 파일 이동 여부 결정
3. scripts 폴더 구조 개선 여부 결정

---

## 결론

| 카테고리 | 현재 상태 | 권장 조치 |
|----------|-----------|-----------|
| 소스 코드 구조 | ✅ 우수 | 유지 |
| 테스트 구조 | ⚠️ 중복 | Phase 2 적용 |
| Git 추적 | ❌ 문제 | Phase 1 즉시 적용 |
| 문서 구조 | ✅ 양호 | 유지 |
| 설정 분리 | ✅ 올바름 | 유지 |

**우선순위**: Phase 1 (Git 정리) → Phase 2 (픽스처 통합) → Phase 3 (선택)
