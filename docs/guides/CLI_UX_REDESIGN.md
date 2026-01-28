# CLI UX 개선 설계서 (비파괴적 개선)

## 목표
- 기존 동작을 깨지 않고 인지적 부담을 줄인다.
- 명령/옵션 이름의 일관성을 높여 학습 비용을 낮춘다.
- 도움말 구조를 개선해 빠른 탐색이 가능하도록 한다.

## 비파괴 원칙
- 기존 옵션/명령 삭제 금지 (alias 추가만 허용)
- 기존 출력 포맷, 기본값, 동작 유지
- 변경은 UX 중심 (help/alias/문서)으로 제한

## 현재 문제 요약 (관측)
- `run` 옵션 과다로 `--help` 가독성 저하
- `compare` vs `analyze-compare` 기능 중복 인지 혼란
- `--analysis-report` vs `--report` 옵션 이름 불일치
- 단축키 충돌/혼용 (`-v`, `-m`, `--fmt` 등)
- 도움말 언어 혼재 (한/영 혼용)

## 개선 범위 (1차 적용)
### 1) 옵션/명령 별칭 추가
- `run --analysis-report`에 `--report` 별칭 추가
- `analyze-compare`에 별칭 명령 추가 (예: `compare-analysis`)
- `--verbose`에 `-V` 별칭 추가 (기존 `-v` 유지)

### 2) 도움말 개선 (텍스트/선택지 명시)
- `compare --test` 도움말에 지원 선택지 명시
- `history --limit` 도움말에 기본값 명시

### 3) 도움말 구조 정리 (비파괴)
- `run` 명령의 `rich_help_panel` 구획 추가/정리
  - 출력/저장/분석/리트리버/메모리/트래커 등 카테고리 강조

## 구현 계획
1. `run.py` 옵션 alias/단축키 추가
2. `analyze.py` 별칭 명령 추가
3. `compare.py`, `history.py` 도움말 텍스트 개선
4. 문서 업데이트 (USER_GUIDE, API 문서)
5. 최소 단위 테스트 실행 (관련 CLI 유닛)

## 검증 계획
- `uv run pytest tests/unit/test_ci_gate_cli.py::test_ci_gate_invalid_format -v`
- 변경 범위 관련 CLI 도움말 확인 (수동):
  - `uv run evalvault run --help`
  - `uv run evalvault analyze-compare --help`
  - `uv run evalvault compare --help`

## 비고
- 장기적으로는 `compare`/`analyze-compare` 통합을 설계하되,
  1차 적용에서는 alias와 문서 정리로 혼선을 줄인다.
