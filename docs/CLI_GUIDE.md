# EvalVault CLI 가이드

EvalVault CLI는 `src/evalvault/adapters/inbound/cli/commands/` 패키지에 있는 Typer 모듈이 자동으로 등록되도록 구성되었습니다. `commands/__init__.py`가 루트 앱에 커맨드를 주입하고, `attach_sub_apps()`가 `domain`, `kg`, `benchmark` 서브앱을 연결합니다. 이 문서는 반복적으로 사용되는 패턴과 도움말 템플릿을 요약합니다.

---

## 1. 공통 구조

| 영역 | 설명 | 엔트리 포인트 |
|------|------|---------------|
| 루트 명령 | `run`, `gate`, `generate`, `pipeline`, `analyze`, `experiment`, `agent`, `config`, `web`, `langfuse` | `register_all_commands()` |
| 서브앱 | `domain`, `kg`, `benchmark` | `attach_sub_apps()` |
| 공통 옵션 | `--profile/-p`, `--db/-D`, `--memory-db/-M` | `cli/utils/options.py` |

```bash
$ evalvault --help
$ evalvault run data.csv --metrics faithfulness --profile dev
$ evalvault kg stats ./docs --use-llm --profile dev
```

---

## 2. 공통 옵션 템플릿

| 옵션 | 설명 | 사용 예 |
|------|------|---------|
| `--profile, -p` | `config/models.yaml`에 정의된 프로필을 적용합니다. | `evalvault run dataset.json -p dev` |
| `--db, -D` | 평가 결과를 저장할 SQLite 경로입니다. 기본값은 `evalvault.db`. | `evalvault history list -D reports/evalvault.db` |
| `--memory-db, -M` | 도메인 메모리 SQLite 경로입니다. 기본값은 `evalvault_memory.db`. | `evalvault domain memory stats -M data/memory.db` |

도움말에 공통 옵션을 추가할 때는 `cli/utils/options.py`의 팩토리를 사용해 동일한 설명과 기본값을 재사용합니다.

---

## 3. 대표 명령 요약

### 3.1 `run`
```bash
evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness answer_relevancy \
  --llm openai \
  --tracker phoenix \
  --profile dev
```
- `--thresholds`, `--db`, `--profile`, `--tracker`를 조합해 CI나 실험용 러너를 구성합니다.
- Domain Memory 연동:
  - `--use-domain-memory`: 학습된 신뢰도로 임계값을 자동 보정합니다.
  - `--memory-domain` / `--memory-language`: 도메인·언어를 강제 지정합니다.
  - `--augment-context`: 평가 전 각 테스트 케이스에 `[관련 사실]` 블록을 추가해 컨텍스트를 확장합니다.
  - `--memory-db/-M`: 메모리 DB 경로를 재지정합니다.

### 3.2 `pipeline`
```bash
evalvault pipeline analyze "요약해줘" --profile analysis
```
- 파이프라인 노드별 출력이 Rich 테이블로 표시됩니다.

### 3.3 `gate`
```bash
evalvault gate check --run-id RUN123 --json --github
```
- 품질 게이트 보고서를 JSON 또는 GitHub Actions 주석으로 출력합니다.

### 3.4 `domain`
```bash
evalvault domain init insurance --languages ko,en --description "보험 QA"
evalvault domain list
evalvault domain show insurance
```

---

## 4. Domain Memory 서브커맨드

도메인 메모리 Phase 1 활용을 위해 `evalvault domain memory` 하위 명령이 추가되었습니다. 모든 명령은 `--memory-db/-M` 옵션으로 대상 DB를 바꿀 수 있습니다.

| 명령 | 설명 | 예시 |
|------|------|------|
| `stats` | 도메인(또는 전체) 기준으로 Facts/Behaviors/Learnings 수량을 표시 | `evalvault domain memory stats --domain insurance` |
| `search` | FTS5 기반 사실 검색, 검증 점수 필터 지원 | `evalvault domain memory search "보험료" --domain insurance --min-score 0.6` |
| `behaviors` | 성공률 순 행동 패턴 조회 | `evalvault domain memory behaviors --min-success 0.8` |
| `learnings` | Experiential 학습 기록 조회 | `evalvault domain memory learnings --limit 10` |
| `evolve` | consolidate/forget/decay 실행 (확인 프롬프트 + `--dry-run`) | `evalvault domain memory evolve --domain insurance --yes` |

샘플 출력:

```bash
$ evalvault domain memory search "청약 철회" --domain insurance
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┓
┃ Fact ID                ┃ Subject      ┃ Predicate    ┃ Object       ┃ Score ┃ Verified┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━┩
│ fact_ba3d...           │ 청약         │ 가능 기간     │ 15일          │ 0.92  │ 4       │
└────────────────────────┴──────────────┴──────────────┴──────────────┴───────┴─────────┘
```

[phoenix] `--tracker phoenix` 또는 LangSmith 등에서 Phoenix를 선택하면 CLI가 `log_evaluation_run()`에 더해 개별 테스트 케이스별 RAG trace(`RetrievalData`, `GenerationData`)도 기록해줍니다. 기본 한계치는 20건이며, Langfuse/MLflow는 기존 동작 그대로 유지됩니다.

---

## 5. 도움말 템플릿

신규 명령을 추가할 때는 아래 패턴을 참고해 짧은 설명과 예시를 함께 문서화합니다.

```
COMMAND_NAME
────────────────────────────────────────────
요약 설명 (1줄)

Usage:
    evalvault <command> [ARGS] [OPTIONS]

자주 쓰는 옵션:
    --profile/-p   : 설명
    --db/-D        : 설명
예시:
    evalvault run dataset.json --metrics faithfulness
```

CLI 도움말을 문서화하면 온보딩 시간이 짧아지고, `docs/IMPROVEMENT_PLAN.md`에서 언급된 P2.1 목표(공통 콜백/도움말 템플릿)를 충족할 수 있습니다.
