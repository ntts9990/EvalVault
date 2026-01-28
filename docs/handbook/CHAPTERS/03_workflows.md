# 03. Workflows

## 목표

EvalVault의 주요 실행 흐름(평가→분석→비교→리포트)을 CLI/Web UI 관점에서 이해한다.

## 기본 실행 흐름

1) `evalvault run`으로 평가 실행
2) 결과를 DB/run_id로 저장
3) `--auto-analyze` 또는 `evalvault analyze`로 분석/리포트 생성
4) `history`/`compare`/`analyze-compare`로 재현 가능한 비교

핵심 키:
- `run_id`: 평가/분석/아티팩트가 묶이는 단일 식별자
- `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`: 분석 근거 인덱스

## CLI 중심 워크플로우

평가 실행:
- `evalvault run <DATASET> --metrics ... --profile dev --db data/db/evalvault.db --auto-analyze`

분석:
- `evalvault analyze <RUN_ID> --profile dev --db data/db/evalvault.db --nlp --causal --playbook`
- `evalvault pipeline analyze "<query>" --run-id <RUN_ID> --profile dev --db data/db/evalvault.db`

비교:
- `evalvault compare <RUN_A> <RUN_B> --profile dev --db data/db/evalvault.db`
- `evalvault analyze-compare <RUN_A> <RUN_B> --profile dev --db data/db/evalvault.db --test t-test|mann-whitney`

아티팩트/검증:
- `evalvault artifacts lint reports/analysis/artifacts/analysis_<RUN_ID>`

## 분석 파이프라인 구조

- 엔티티/의도: `../../src/evalvault/domain/entities/analysis_pipeline.py`
- 템플릿 레지스트리: `../../src/evalvault/domain/services/pipeline_template_registry.py`
- 오케스트레이션: `../../src/evalvault/domain/services/pipeline_orchestrator.py`
- 모듈 등록: `../../src/evalvault/adapters/outbound/analysis/pipeline_factory.py`
- CLI 진입점: `../../src/evalvault/adapters/inbound/cli/commands/pipeline.py`

## Web UI 연동 흐름

- Web UI는 동일 DB를 사용하며 `run_id`로 CLI와 동기화된다.
- 주요 API:
  - `GET /api/v1/runs/{run_id}`
  - `GET /api/v1/runs/{run_id}/report`
  - `GET /api/v1/runs/{run_id}/analysis-report`
  - `GET /api/v1/runs/{run_id}/dashboard`

## 참고

- 사용자 가이드: `../guides/USER_GUIDE.md`
- 워크플로우 템플릿: `../guides/RAG_CLI_WORKFLOW_TEMPLATES.md`
- 진단 플레이북: `../guides/EVALVAULT_DIAGNOSTIC_PLAYBOOK.md`
- 데이터 흐름 백서: `../new_whitepaper/03_data_flow.md`
- API/웹: `../../src/evalvault/adapters/inbound/api/`
- CLI: `../../src/evalvault/adapters/inbound/cli/`
