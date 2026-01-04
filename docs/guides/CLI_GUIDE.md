# EvalVault CLI 가이드

EvalVault CLI는 `src/evalvault/adapters/inbound/cli/commands/` 패키지에 있는 Typer 모듈이 자동으로 등록되도록 구성되었습니다. `commands/__init__.py`가 루트 앱에 커맨드를 주입하고, `attach_sub_apps()`가 `domain`, `kg`, `benchmark` 서브앱을 연결합니다. 이 문서는 반복적으로 사용되는 패턴과 도움말 템플릿을 요약합니다.

---

## 1. 공통 구조

| 영역 | 설명 | 엔트리 포인트 |
|------|------|---------------|
| 루트 명령 | `init`, `run`, `gate`, `generate`, `pipeline`, `analyze`, `experiment`, `agent`, `config`, `web`, `langfuse`, `stage` | `register_all_commands()` |
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

### 3.0 `init` (프로젝트 초기화)
```bash
uv run evalvault init
uv run evalvault init --output-dir ./my-project
uv run evalvault init --skip-env --skip-sample
```
- `.env` 템플릿과 `sample_dataset.json`을 생성해 빠르게 시작할 수 있게 합니다.
- `--output-dir`로 생성 위치를 지정할 수 있습니다.
- `--skip-env` 또는 `--skip-sample`로 단계별 생성을 끌 수 있습니다.

### 3.1 `run`
```bash
evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness answer_relevancy \
  --llm openai \
  --tracker phoenix \
  --profile dev
```
- `run-simple` / `run-full` 별칭: `evalvault run --mode simple/full`과 동일하며 초보자가 dataset + profile만으로 실행할 수 있도록 안내용 도움말을 별도 섹션으로 분리했습니다.

#### Run Modes

| 모드 | 명령 | 동작 |
|------|------|------|
| Simple | `evalvault run --mode simple DATASET.json`<br>`evalvault run-simple DATASET.json` | `faithfulness,answer_relevancy` 메트릭, Phoenix tracker, Domain Memory/Prompt OFF, Quick Fix 메시지를 자동 출력 |
| Full | `evalvault run --mode full DATASET.json`<br>`evalvault run-full DATASET.json` | 모든 Typer 옵션(프로파일, Prompt manifest, Phoenix dataset/experiment, Domain Memory, streaming)을 노출 |

- `evalvault history --mode simple/full`로 CLI 결과를 필터링할 수 있습니다.
- Streamlit Evaluate/Reports 페이지 역시 동일한 모드 토글/Pill을 사용해 UI와 CLI가 같은 메타데이터(`tracker_metadata.run_mode`)를 공유합니다.

- `--thresholds`, `--db`, `--profile`, `--tracker`를 조합해 CI나 실험용 러너를 구성합니다.
- Domain Memory 연동:
  - `--use-domain-memory`: 학습된 신뢰도로 임계값을 자동 보정합니다.
  - `--memory-domain` / `--memory-language`: 도메인·언어를 강제 지정합니다.
  - `--augment-context`: 평가 전 각 테스트 케이스에 `[관련 사실]` 블록을 추가해 컨텍스트를 확장합니다.
  - `--memory-db/-M`: 메모리 DB 경로를 재지정합니다.
- Retriever 연동:
  - `--retriever`: `bm25`, `dense`, `hybrid`, `graphrag` 중 컨텍스트 자동 생성용 검색기를 선택합니다.
  - `--retriever-docs`: 검색에 사용할 문서 파일(.json/.jsonl/.txt)을 지정합니다.
  - `--retriever-top-k`: 검색 결과 상위 k개를 컨텍스트로 사용합니다.
  - `--kg`: GraphRAG용 Knowledge Graph JSON 파일을 지정합니다.
  - `--stream` 모드에서는 retriever 적용을 건너뜁니다.
- `run-simple`/`run-full`에서도 동일한 retriever 옵션을 사용할 수 있습니다.

#### Evaluation Presets

| 프리셋 | 설명 | 기본 메트릭 |
|--------|------|-------------|
| `quick` | 빠른 반복 평가 | `faithfulness` |
| `production` | 프로덕션 밸런스 | `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall` |
| `comprehensive` | 전체 메트릭 평가 | `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`, `factual_correctness`, `semantic_similarity` |

- `--preset`을 지정하면 메트릭/병렬 처리 설정을 기본값으로 적용합니다.
- `--metrics`를 명시하면 프리셋 메트릭을 덮어씁니다.
- `--batch-size`는 `-b` 단축 옵션을 지원합니다.

예시:

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --retriever hybrid \
  --retriever-docs examples/benchmarks/korean_rag/retrieval_test.json \
  --retriever-top-k 5

uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --retriever graphrag \
  --retriever-docs examples/benchmarks/korean_rag/retrieval_test.json \
  --kg tests/fixtures/kg/minimal_graph.json \
  --retriever-top-k 5
```

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

### 3.5 `stage`
```bash
evalvault stage ingest stage_events.jsonl --db evalvault.db
evalvault stage summary run_20260103_001 --db evalvault.db
evalvault stage compute-metrics run_20260103_001 --thresholds-json config/stage_metric_thresholds.json
```
- `ingest`: JSON/JSONL stage events를 저장합니다.
- `summary`: 단계별 카운트/평균 지연과 필수 단계 누락 여부를 확인합니다.
- `compute-metrics`: stage events로 StageMetric을 계산해 저장합니다.
  - `--thresholds-json` 미지정 시 `config/stage_metric_thresholds.json`이 존재하면 자동 적용
  - `--thresholds-profile` 미지정 시 `Settings.evalvault_profile` 사용

### 3.6 `benchmark`
```bash
evalvault benchmark run --name korean-rag
evalvault benchmark retrieval tests/fixtures/benchmark/retrieval_ground_truth_min.json \
  --methods bm25,dense,hybrid \
  --top-k 5 \
  --ndcg-k 10 \
  --output reports/retrieval_benchmark.json
```
- `run`: 한국어 RAG 벤치마크 스위트를 실행합니다.
- `retrieval`: 검색 방식별 Recall/MRR/nDCG를 비교하고 JSON/CSV로 저장합니다.
  - `--methods`: `bm25,dense,hybrid,graphrag` 중 복수 지정
  - `--embedding-profile`: `dev/prod` (Ollama Qwen3-Embedding 사용)
  - `--embedding-model`: Dense/Hybrid 임베딩 모델명 오버라이드
  - `--kg`: GraphRAG 선택 시 필수
  - `--output`: `.json` 또는 `.csv` 저장

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

[phoenix]

- `--tracker phoenix`: OpenInference 스팬과 Phoenix 트레이스(`RetrievalData`, `GenerationData`)를 전송합니다.
- `--phoenix-max-traces`: 전송할 테스트 케이스 상한(기본 전체)을 조정합니다.
- `--phoenix-dataset` / `--phoenix-dataset-description`: EvalVault 데이터셋을 Phoenix Dataset으로 업로드합니다. 설명 미지정 시 `"{name} v{version}"` 또는 데이터셋 메타데이터를 사용합니다.
- `--phoenix-experiment` / `--phoenix-experiment-description`: 업로드된 Dataset과 연결된 Phoenix Experiment를 생성하고 EvalVault 메트릭/Domain Memory 신호를 메타데이터로 저장합니다. Experiment만 지정하면 Dataset 이름은 `"{dataset}:{version}"`으로 자동 생성됩니다.
- Phoenix 업로드 결과는 `tracker_metadata["phoenix"]`에 dataset/experiment URL로 저장되며 JSON 출력에서도 확인할 수 있습니다.

예시:

```bash
uv run evalvault run dataset.json --metrics faithfulness \
  --tracker phoenix --phoenix-dataset insurance-qa \
  --phoenix-experiment gemma3-baseline
```

Phoenix Embeddings export:

```bash
uv run evalvault phoenix export-embeddings \
  --dataset insurance-qa \
  --embedding-mode model \
  --embedding-model text-embedding-3-small \
  --batch-size 64 \
  --output reports/phoenix_embeddings.csv
```

- `--embedding-mode`: `model`(실제 임베딩 모델) 또는 `tfidf`
- `--embedding-model`: 모델 이름 오버라이드 (프로필/환경변수 대신 사용)
- `--batch-size`: 임베딩 요청 배치 크기
- `--max-chars`: 예제 텍스트를 지정 길이로 잘라 전송

Langfuse/MLflow 플래그는 기존 동작 그대로 유지되며, Phoenix 전송이 실패해도 평가 실행은 계속됩니다.

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

CLI 도움말을 문서화하면 온보딩 시간이 짧아지고, `docs/internal/archive/IMPROVEMENT_PLAN.md`에서 언급된 P2.1 목표(공통 콜백/도움말 템플릿)를 충족할 수 있습니다.
