# Project Structure Review

> 작성일: 2025-12-28
> 상태: 검토 완료

이 문서는 EvalVault 저장소의 디렉터리 구성을 분석하고 개선 방안을 제시합니다.

---

## 1. 디렉터리 구조 개요

```
EvalVault/
├── .github/                    # GitHub 워크플로우 및 템플릿
│   ├── workflows/              # CI, Release
│   ├── ISSUE_TEMPLATE/
│   └── dependabot.yml, stale.yml
├── config/                     # 런타임 설정 (YAML)
│   └── models.yaml
├── data/                       # 로컬 데이터
│   ├── datasets/               # 샘플 데이터셋
│   ├── e2e_results/
│   └── evaluations.db
├── docs/                       # 문서
├── examples/                   # 예제 코드
├── reports/                    # 테스트 리포트 (생성됨)
├── scripts/                    # 유틸리티 스크립트
├── src/evalvault/              # 메인 소스 코드 (Hexagonal)
│   ├── adapters/               # inbound(CLI), outbound(LLM, Storage)
│   ├── config/                 # Python 설정
│   ├── domain/                 # entities, services, metrics, prompts
│   ├── ports/                  # 인터페이스 정의
│   └── utils/
└── tests/                      # 테스트 스위트
    ├── unit/, integration/
    ├── fixtures/, e2e_data/
```

---

## 2. 평가 요약

| 경로 | 용도 | 평가 |
|------|------|------|
| `src/evalvault/` | Hexagonal Architecture | ✅ 명확한 분리, 일관된 모듈화 |
| `tests/` | unit/integration/fixtures | ✅ 가이드라인 일치 |
| `config/` | 런타임 프로필 | ✅ |
| `docs/` | 아키텍처/유저 가이드 | ✅ |
| `scripts/` | CI 보조 스크립트 | ✅ |
| `.github/` | 워크플로우, 템플릿 | ✅ |
| `data/` | 로컬 DB, 샘플 데이터 | ⚠️ evaluations.db가 git 추적됨 |
| `examples/` | 데모 스크립트 | ⚠️ README 부재 |
| `reports/` | 테스트 산출물 | ⚠️ 샘플과 생성물 혼재 |

---

## 3. 발견된 문제점

### 3.1 Git 추적 오류 (Critical)

| 파일 | 문제점 |
|------|--------|
| `data/evaluations.db` | 로컬 SQLite DB가 git에 포함됨 |
| `data/datasets/*.{csv,json,xlsx}` | tests/fixtures와 중복 |
| `reports/kg_stats_report.json` | 생성된 리포트가 추적됨 |

### 3.2 테스트 데이터 중복

동일 목적의 데이터가 4곳에 분산:
- `tests/fixtures/` - 메인 픽스처
- `tests/fixtures/e2e/` - E2E 픽스처
- `tests/e2e_data/` - 중복
- `data/datasets/` - 중복

### 3.3 문서 부재

- `examples/README.md` - 데모 실행 방법 없음
- `reports/README.md` - 디렉터리 용도 설명 없음

---

## 4. 권장 조치

### Phase 1: Git 추적 정리 (즉시 적용)

**.gitignore 추가:**
```gitignore
data/evaluations.db
data/e2e_results/
reports/*.json
reports/*.html
reports/*.xml
!reports/.gitkeep
```

**Git에서 제거:**
```bash
git rm --cached data/evaluations.db
git rm --cached data/datasets/sample_insurance_qa.*
git rm --cached reports/kg_stats_report.json
```

### Phase 2: 테스트 데이터 통합 (권장)

1. `tests/e2e_data/*` → `tests/fixtures/e2e/`로 이동
2. `data/datasets/` 내용 삭제 (tests/fixtures와 중복)
3. `tests/fixtures/README.md` 추가

### Phase 3: 문서 보완 (선택)

1. `examples/README.md` 추가 - 데모 실행 방법
2. `reports/README.md` 추가 - 산출물 디렉터리 설명

---

## 5. 유지해야 할 부분

### Hexagonal Architecture ✅
```
src/evalvault/
├── adapters/       # 올바른 구조
├── config/         # 올바른 구조
├── domain/         # 올바른 구조
├── ports/          # 올바른 구조
└── utils/          # 올바른 구조
```

### 설정 분리 ✅
- `config/models.yaml` - 사용자가 수정하는 런타임 설정
- `src/evalvault/config/` - 개발자가 작성한 설정 코드

---

## 6. 결론

| 카테고리 | 상태 | 조치 |
|----------|------|------|
| 소스 코드 구조 | ✅ 우수 | 유지 |
| 설정 분리 | ✅ 올바름 | 유지 |
| 문서 구조 | ✅ 양호 | 유지 |
| Git 추적 | ❌ 문제 | Phase 1 즉시 적용 |
| 테스트 데이터 | ⚠️ 중복 | Phase 2 권장 |

**우선순위**: Phase 1 → Phase 2 → Phase 3
