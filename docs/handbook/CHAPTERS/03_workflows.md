# 03. Workflows

## 목표

EvalVault의 주요 실행 흐름(평가→분석→비교→리포트)을 CLI/Web UI 관점에서 이해한다.

## 흐름(요약)

1) `evalvault run`으로 평가 실행
2) 결과를 DB/run_id로 저장
3) 필요 시 자동 분석/리포트 생성
4) history/compare로 재현 가능한 비교

## 참고

- 사용자 가이드: `../guides/USER_GUIDE.md`
- CLI 실행 시나리오: `../guides/RAG_CLI_WORKFLOW_TEMPLATES.md`
- API/웹: `../../src/evalvault/adapters/inbound/api/`
- CLI: `../../src/evalvault/adapters/inbound/cli/`
