# Inbound Adapters

Inbound adapters implement the interfaces defined by inbound ports, providing concrete entry points for users and systems.

## CLI Adapter

Command-line interface built with Typer.

The CLI provides various commands for evaluation, analysis, and management:

- **run** - Execute RAG evaluations with various options
- **history** - View evaluation history
- **config** - Manage configuration
- **generate** - Generate test cases
- **pipeline** - Run analysis pipelines
- **benchmark** - Performance benchmarking
- **domain** - Domain memory management
- **phoenix** - Phoenix integration
- **gate** - Quality gates
- **experiment** - A/B testing

For detailed CLI usage, see the [Handbook](../../handbook/INDEX.md).

## Web API Adapter + React Frontend

FastAPI endpoints power the React UI for interactive evaluation and analysis.

The web UI provides:

- **Evaluation Studio**: Run evaluations with real-time progress
- **History**: View past evaluation runs
- **Analysis Lab**: Save and reload analysis results
- **Settings**: Configure LLM providers and trackers

The FastAPI routes live in `src/evalvault/adapters/inbound/api/`, and the web adapter implementation is in `src/evalvault/adapters/inbound/api/adapter.py`. The React frontend is under `frontend/`.

### 주요 API 엔드포인트 (발췌)

Runs:
- `GET /api/v1/runs` 평가 실행 목록
- `GET /api/v1/runs/{run_id}` 실행 상세
- `GET /api/v1/runs/{run_id}/report` LLM 보고서
- `GET /api/v1/runs/{run_id}/analysis-report` 분석 보고서 (markdown/html)
- `GET /api/v1/runs/{run_id}/dashboard` 대시보드 이미지 (png/svg/pdf)
- `GET /api/v1/runs/{run_id}/quality-gate` 품질 게이트
- `GET /api/v1/runs/{run_id}/debug-report` 디버그 리포트
- `GET /api/v1/runs/{run_id}/improvement` 개선 가이드
- `GET /api/v1/runs/prompt-diff` 프롬프트 비교

Calibration:
- `POST /api/v1/calibration/judge`
- `GET /api/v1/calibration/judge/{calibration_id}`
- `GET /api/v1/calibration/judge/history`

참고:
- `/dashboard` 엔드포인트는 `dashboard` extra(matplotlib)가 필요합니다.

## Usage Examples

### CLI

```bash
# Run evaluation
uv run evalvault run data.csv --metrics faithfulness,answer_relevancy

# View metrics
uv run evalvault metrics

# Compare runs
uv run evalvault compare RUN_ID_A RUN_ID_B
```

### Web UI (React + FastAPI)

```bash
# Start the API
uv run evalvault serve-api --reload

# Start the frontend
cd frontend
npm install
npm run dev
```

For detailed CLI usage, see the [Handbook](../../handbook/INDEX.md).
