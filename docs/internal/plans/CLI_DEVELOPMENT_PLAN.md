# CLI 개발 계획서

> **작성일**: 2026-01-05
> **목적**: EvalVault CLI 기능 확장 및 UX 개선 로드맵
> **범위**: P4.1 ~ Phase 19 CLI 관련 작업

---

## 개요

EvalVault CLI는 RAG 평가 워크플로우의 핵심 인터페이스입니다. 현재 16개 명령어 파일(총 7,960 LOC)이 구현되어 있으며, 사용성 개선과 기능 확장을 계획합니다.

### 현재 CLI 구조

```
cli/commands/           LOC     상태
├── run.py             1,470    🔴 리팩토링 필요
├── run_helpers.py       869    ⚠️ 분리됨
├── analyze.py           765    ✅ 적정
├── domain.py            681    ✅ 적정
├── benchmark.py         673    ✅ 적정
├── kg.py                529    ✅ 적정
├── phoenix.py           474    ✅ 적정
├── stage.py             459    ✅ 적정
├── experiment.py        254    ✅ 간결
├── history.py           242    ✅ 간결
├── gate.py              236    ✅ 간결
├── init.py              214    ✅ 간결
├── agent.py             205    ✅ 간결
├── pipeline.py          182    ✅ 간결
├── config.py            150    ✅ 간결
├── generate.py          128    ✅ 간결
├── langfuse.py          114    ✅ 간결
├── web.py                75    ✅ 간결
├── api.py                60    ✅ 신규
└── debug.py              60    ✅ 간결
────────────────────────────────
합계                   7,960 LOC
```

---

## Phase 1: P4.1 CLI UX 개선 (현재)

### 완료된 항목 ✅

| 항목 | 상태 | 구현 위치 |
|------|------|----------|
| QW1: 에러 메시지 개선 | ✅ 완료 | `utils/errors.py` |
| QW3: 명령어 별칭 | ✅ 완료 | 전체 commands |
| QW4: 설정 검증 | ✅ 완료 | `utils/validators.py` |
| 프리셋 시스템 | ✅ 완료 | `utils/presets.py` |
| `evalvault init` | ✅ 완료 | `commands/init.py` |

### 미완료 항목 🚧

#### QW2: Progress Bar (우선순위: 높음)

**현재 상태**: Rich 라이브러리 사용 중이나 평가 진행률 표시 미흡

**구현 계획**:
```python
# commands/run.py 개선
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

async def run_with_progress(dataset: Dataset, metrics: list[str]):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TextColumn("ETA: {task.fields[eta]}"),
    ) as progress:
        task = progress.add_task("Evaluating...", total=len(dataset.test_cases), eta="--:--")

        for i, test_case in enumerate(dataset.test_cases):
            result = await evaluate_single(test_case, metrics)
            eta = calculate_eta(i, len(dataset.test_cases), elapsed)
            progress.update(task, advance=1, eta=eta)
```

**작업 항목**:
- [ ] `utils/progress.py` 생성 (진행률 유틸리티)
- [ ] `run.py`에 Progress 통합
- [ ] `benchmark.py`에 Progress 통합
- [ ] `generate.py`에 Progress 통합
- [ ] ETA 계산 로직 추가

**예상 LOC 변경**: +150 (신규), 각 명령어 +20

---

#### 도움말 메시지 개선 (우선순위: 중간)

**현재 문제**:
- 일부 옵션 설명이 불명확
- 예제가 부족
- 관련 명령어 안내 없음

**구현 계획**:
```python
# 개선된 도움말 예시
@app.command()
def run(
    dataset: Path = typer.Argument(
        ...,
        help="Dataset file (JSON/CSV/Excel). Example: data.json",
        show_default=False,
    ),
    metrics: str = typer.Option(
        "faithfulness,answer_relevancy",
        "-m", "--metrics",
        help="Comma-separated metrics. Available: faithfulness, answer_relevancy, "
             "context_precision, context_recall, factual_correctness, semantic_similarity. "
             "Or use --preset for predefined sets.",
    ),
    # ...
):
    """
    Run RAG evaluation on a dataset.

    \b
    Examples:
        # Basic evaluation
        evalvault run data.json -m faithfulness

        # With retriever (auto-fill contexts)
        evalvault run questions.json -r hybrid --retriever-docs docs.json

        # Production preset with tracking
        evalvault run data.json --preset production --tracker phoenix

    \b
    See also:
        evalvault metrics     - List available metrics
        evalvault history     - View past runs
        evalvault analyze     - Analyze run results
    """
```

**작업 항목**:
- [ ] 모든 명령어에 Examples 섹션 추가
- [ ] 모든 명령어에 See also 섹션 추가
- [ ] 옵션 help 문자열 표준화
- [ ] `--help-examples` 플래그 추가 (상세 예제 출력)

---

## Phase 2: P4.2 CLI 코드 정리

### run.py 분리 (우선순위: 높음)

**목표**: 1,470 LOC → 500 LOC 이하

**분리 계획**:
```
commands/
├── run.py                    # 메인 진입점 (~300 LOC)
├── run_helpers.py            # 기존 헬퍼 (유지)
├── run_modes/
│   ├── __init__.py
│   ├── simple.py             # Simple 모드 로직 (~200 LOC)
│   └── full.py               # Full 모드 로직 (~300 LOC)
└── run_output/
    ├── __init__.py
    ├── table.py              # Rich 테이블 출력
    ├── json.py               # JSON 출력
    └── summary.py            # 요약 출력
```

**작업 항목**:
- [ ] `run_modes/` 디렉토리 생성
- [ ] Simple/Full 모드 로직 분리
- [ ] `run_output/` 디렉토리 생성
- [ ] 출력 로직 분리
- [ ] 기존 테스트 유지 보장

---

## Phase 3: CLI 기능 확장 (Q2-Q3 2026)

### 3.1 커스텀 메트릭 CLI (Phase 15 연계)

**신규 명령어**: `evalvault metric`

```bash
# 메트릭 목록 (기존 metrics 확장)
evalvault metric list
evalvault metric list --custom-only

# 커스텀 메트릭 등록
evalvault metric register ./my_metric.py
evalvault metric register ./metrics/ --recursive

# 메트릭 테스트
evalvault metric test my_custom_metric --sample data.json

# 메트릭 정보
evalvault metric info faithfulness
evalvault metric info my_custom_metric --show-source
```

**구현 파일**: `commands/metric.py` (신규)

**작업 항목**:
- [ ] `metric list` 서브명령어
- [ ] `metric register` 서브명령어 (플러그인 로더 연동)
- [ ] `metric test` 서브명령어
- [ ] `metric info` 서브명령어
- [ ] 메트릭 플러그인 디렉토리 설정 (`~/.evalvault/metrics/`)

---

### 3.2 개선 제안 CLI (Phase 17 연계)

**신규 명령어**: `evalvault suggest`

```bash
# 기본 제안
evalvault suggest <run_id>

# LLM 기반 상세 제안
evalvault suggest <run_id> --llm --detail

# 특정 메트릭만
evalvault suggest <run_id> --metric faithfulness

# 플레이북 기반
evalvault suggest <run_id> --playbook insurance

# 제안을 마크다운으로 저장
evalvault suggest <run_id> -o suggestions.md
```

**구현 파일**: `commands/suggest.py` (신규)

**작업 항목**:
- [ ] ImprovementEngine 서비스 연동
- [ ] 플레이북 로더 구현
- [ ] Rich 패널로 제안 출력
- [ ] 마크다운/JSON 출력 지원

---

### 3.3 RAG 파이프라인 CLI (Phase 18 연계)

**신규 명령어**: `evalvault pipeline run` (기존 pipeline 확장)

```bash
# 파이프라인 설정 파일로 실행
evalvault pipeline run config.yaml --questions questions.json

# 인라인 파이프라인 정의
evalvault pipeline run \
  --retriever hybrid \
  --llm openai \
  --prompt-template "Answer based on: {context}\nQuestion: {question}" \
  --questions questions.json

# 파이프라인 검증
evalvault pipeline validate config.yaml

# 파이프라인 템플릿 생성
evalvault pipeline init --template basic > pipeline.yaml
```

**구현 파일**: `commands/pipeline.py` 확장

**작업 항목**:
- [ ] YAML 파이프라인 파서
- [ ] `pipeline run` 서브명령어 확장
- [ ] `pipeline validate` 서브명령어
- [ ] `pipeline init` 서브명령어
- [ ] LangChain/LlamaIndex 어댑터 연동

---

### 3.4 KG 고급 CLI (Phase 19 연계)

**기존 명령어 확장**: `evalvault kg`

```bash
# 기존
evalvault kg build documents/ -o kg.json
evalvault kg stats kg.json

# 신규: 분석
evalvault kg analyze kg.json --centrality --clusters

# 신규: 시각화
evalvault kg visualize kg.json -o graph.html --format interactive
evalvault kg visualize kg.json -o graph.png --format static

# 신규: 쿼리
evalvault kg query kg.json "보험금 청구 절차"
evalvault kg query kg.json --entity "보험금" --depth 2

# 신규: 병합
evalvault kg merge kg1.json kg2.json -o merged.json

# 신규: 검증
evalvault kg validate kg.json --check-orphans --check-duplicates
```

**구현 파일**: `commands/kg.py` 확장

**작업 항목**:
- [ ] `kg analyze` 서브명령어
- [ ] `kg visualize` 서브명령어 (Plotly/Graphviz)
- [ ] `kg query` 서브명령어
- [ ] `kg merge` 서브명령어
- [ ] `kg validate` 서브명령어

---

## Phase 4: CLI 고급 기능 (Q4 2026)

### 4.1 대화형 모드

**신규 명령어**: `evalvault shell`

```bash
evalvault shell

EvalVault Shell v1.0.0
Type 'help' for commands, 'exit' to quit.

evalvault> load data.json
Dataset loaded: 100 test cases

evalvault> run -m faithfulness
Running evaluation...
[████████████████████] 100/100

evalvault> analyze
Statistical analysis complete.

evalvault> suggest
3 improvement suggestions found.

evalvault> history
┌─────────────┬────────────┬─────────────┐
│ Run ID      │ Date       │ Avg Score   │
├─────────────┼────────────┼─────────────┤
│ run-001     │ 2026-01-05 │ 0.82        │
└─────────────┴────────────┴─────────────┘

evalvault> exit
```

**구현 파일**: `commands/shell.py` (신규)

---

### 4.2 Watch 모드

**신규 옵션**: `--watch`

```bash
# 파일 변경 시 자동 재평가
evalvault run data.json -m faithfulness --watch

Watching data.json for changes...
[2026-01-05 10:00:00] File changed, re-evaluating...
[2026-01-05 10:00:15] Evaluation complete. Avg: 0.82

[2026-01-05 10:05:00] File changed, re-evaluating...
[2026-01-05 10:05:12] Evaluation complete. Avg: 0.85 (+0.03)
```

**작업 항목**:
- [ ] watchdog 의존성 추가 (optional)
- [ ] `--watch` 옵션 구현
- [ ] 변경 감지 및 자동 재실행 로직
- [ ] 결과 diff 출력

---

### 4.3 프로파일 관리

**신규 명령어**: `evalvault profile`

```bash
# 프로파일 목록
evalvault profile list

# 프로파일 생성
evalvault profile create production \
  --llm openai \
  --model gpt-4 \
  --tracker phoenix

# 프로파일 편집
evalvault profile edit production

# 프로파일 내보내기/가져오기
evalvault profile export production > prod.yaml
evalvault profile import prod.yaml

# 프로파일 삭제
evalvault profile delete production
```

**구현 파일**: `commands/profile.py` (신규)

---

## 우선순위 및 일정

### 즉시 착수 (2026 Q1)

| 작업 | 우선순위 | 예상 기간 | 의존성 |
|------|----------|----------|--------|
| QW2: Progress Bar | 🔴 높음 | 2일 | 없음 |
| 도움말 메시지 개선 | 🟡 중간 | 3일 | 없음 |
| run.py 분리 | 🔴 높음 | 5일 | 없음 |

### 단기 (2026 Q2)

| 작업 | 우선순위 | 예상 기간 | 의존성 |
|------|----------|----------|--------|
| `evalvault metric` | 🟡 중간 | 1주 | Phase 15 |
| `evalvault suggest` | 🟡 중간 | 1주 | Phase 17 |
| KG 분석/시각화 | 🟢 낮음 | 1주 | Phase 19 |

### 중기 (2026 Q3-Q4)

| 작업 | 우선순위 | 예상 기간 | 의존성 |
|------|----------|----------|--------|
| `pipeline run` 확장 | 🟡 중간 | 2주 | Phase 18 |
| `evalvault shell` | 🟢 낮음 | 1주 | 없음 |
| Watch 모드 | 🟢 낮음 | 3일 | 없음 |
| 프로파일 관리 | 🟢 낮음 | 3일 | 없음 |

---

## 테스트 전략

### 단위 테스트

- 모든 새 명령어에 대해 `tests/unit/test_cli_*.py` 추가
- 옵션 파싱, 출력 포맷, 에러 처리 검증

### 통합 테스트

- E2E 시나리오 테스트 (`tests/integration/test_cli_e2e.py`)
- 실제 데이터셋으로 전체 워크플로우 검증

### 스냅샷 테스트

- Rich 출력 형식 검증
- 도움말 메시지 회귀 방지

---

## 관련 문서

- [ROADMAP.md](../../status/ROADMAP.md) - 전체 로드맵
- [PARALLEL_WORK_PLAN.md](./PARALLEL_WORK_PLAN.md) - 병렬 작업 계획
- [CLI_GUIDE.md](../../guides/CLI_GUIDE.md) - 사용자 가이드

---

**문서 끝**
