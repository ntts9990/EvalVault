# Reports

테스트 및 평가 실행 시 생성되는 산출물 디렉터리입니다.

## 디렉터리 용도

이 디렉터리는 다음과 같은 자동 생성 파일들을 저장합니다:

| 파일 유형 | 설명 | 생성 시점 |
|-----------|------|-----------|
| `*.html` | pytest-html 테스트 리포트 | `pytest --html=reports/report.html` |
| `*.xml` | JUnit XML 테스트 결과 | `pytest --junitxml=reports/results.xml` |
| `*.json` | 평가 통계 리포트 | KG Generator, Evaluator 실행 시 |
| `assets/` | HTML 리포트 관련 정적 파일 | pytest-html 실행 시 |

## Git 추적 정책

이 디렉터리의 파일들은 **버전 관리에서 제외**됩니다:

```gitignore
# .gitignore
reports/*.html
reports/*.xml
reports/*.json
reports/assets/
!reports/.gitkeep
!reports/README.md
```

- `.gitkeep` - 빈 디렉터리 유지용
- `README.md` - 이 문서 (추적됨)
- 그 외 모든 파일 - gitignore (추적 안 함)

## 리포트 생성 방법

### pytest 테스트 리포트

```bash
# HTML 리포트 생성
pytest tests/ --html=reports/test_report.html --self-contained-html

# JUnit XML 리포트 생성 (CI용)
pytest tests/ --junitxml=reports/test_results.xml

# 둘 다 생성
pytest tests/ --html=reports/test_report.html --junitxml=reports/test_results.xml
```

### 커버리지 리포트

```bash
# HTML 커버리지 리포트
pytest tests/ --cov=src/evalvault --cov-report=html:reports/coverage

# 터미널 + HTML 동시 출력
pytest tests/ --cov=src/evalvault --cov-report=term --cov-report=html:reports/coverage
```

### Knowledge Graph 통계

```bash
# KG 통계 리포트 생성
evalvault kg-stats --output reports/kg_stats_report.json
```

## 로컬 파일 정리

불필요한 리포트 파일 정리:

```bash
# 모든 생성된 리포트 삭제 (README와 .gitkeep 제외)
find reports/ -type f ! -name 'README.md' ! -name '.gitkeep' -delete
find reports/ -type d -empty -delete
```

## 관련 문서

- [TEST_COVERAGE_PLAN.md](../docs/TEST_COVERAGE_PLAN.md) - 테스트 커버리지 개선 계획
- [STRUCTURE_REVIEW.md](../docs/STRUCTURE_REVIEW.md) - 프로젝트 구조 리뷰
