# 07. UX & Product

## 목표

사용자 관점(제품)에서 EvalVault의 경험을 정리하고, Web UI/CLI의 의도와 사용 흐름을 통합한다.

## 제품 관점 요약

- 기본 사용자 흐름은 `run_id`를 중심으로 평가→분석→비교가 연결된다.
- Web UI는 CLI의 핵심 워크플로를 시각적으로 재구성한다.

## CLI <-> Web UI 매핑

- 실행 목록: `history` -> Web UI 실행 리스트
- 분석 실험실: `analyze`, `analyze-compare`, `pipeline` -> 분석 페이지
- 비교 화면: `compare`, `analyze-compare` -> 비교 페이지
- 산출물 확인: `artifacts lint`, `report` -> 리포트/아티팩트 뷰

예시 흐름:
- CLI 실행: `uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness --profile dev --db data/db/evalvault.db --auto-analyze`
- Web UI 확인: `http://localhost:5173` -> Dashboard -> Run Details -> Report/Dashboard

## Web UI 범위

- 계획/롤아웃: `../guides/WEBUI_CLI_ROLLOUT_PLAN.md`
- 분석 이관: `../web_ui_analysis_migration_plan.md`
- 프론트엔드 구현: `../../frontend/src/`

주요 위치:
- 페이지: `../../frontend/src/pages/`
- 컴포넌트: `../../frontend/src/components/`
- API 연동: `../../frontend/src/services/api.ts`

대표 페이지:
- Dashboard: 실행 리스트/필터/요약
- Evaluation Studio: 실행 설정/프리셋
- Analysis Lab: 인텐트 기반 분석 실행
- Compare Runs: A/B 비교 및 메트릭 변화
- Settings: 프로필/DB 경로 설정

## CLI 전용 기능(현 상태)

- Web UI는 `top_k`가 고정되어 있으며 고급 조정은 CLI/API 필요
- 데이터셋/실험 업로드 및 프롬프트 매니페스트는 CLI 우선

## CLI UX 개선 포인트

- 비교 명령 중복 정리: `../guides/CLI_UX_REDESIGN.md`
- 도움말/별칭 정비: `compare`/`analyze-compare`

## 참고

- Web UI 계획/확장: `../guides/WEBUI_CLI_ROLLOUT_PLAN.md`
- CLI UX 개선: `../guides/CLI_UX_REDESIGN.md`
- 사용자 가이드: `../guides/USER_GUIDE.md`
- 프론트엔드: `../../frontend/src/`
