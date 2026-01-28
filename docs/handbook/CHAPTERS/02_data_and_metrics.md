# 02. Data & Metrics

## 목표

데이터셋 포맷, 메트릭, 임계값(threshold), 산출물(artifacts)이 어떻게 연결되는지 이해한다.

## 데이터셋 스키마

- 표준 스키마: `../../src/evalvault/domain/entities/dataset.py`
- 템플릿: `../templates/` 및 `../../dataset_templates/`

핵심 필드:
- `test_cases[].question`, `test_cases[].answer`, `test_cases[].contexts`
- 선택 필드: `test_cases[].ground_truth`, `test_cases[].metadata`
- 데이터셋 전체 `thresholds`: 메트릭별 합격 기준

샘플 데이터:
- `../../tests/fixtures/sample_dataset.json`
- `../../tests/fixtures/e2e/insurance_qa_korean.json`

예시 명령:
- `uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --metrics faithfulness --profile dev --db data/db/evalvault.db --auto-analyze`

## 임계값(Threshold) 처리

우선순위(높음 -> 낮음):
1) CLI override (`--thresholds`)
2) Dataset `thresholds`
3) 프로필 기본값 (`threshold_profiles.py`)
4) 기본 fallback (도메인 서비스)

관련 파일:
- 프로필: `../../src/evalvault/domain/services/threshold_profiles.py`
- CSV/Excel threshold 컬럼 매핑: `../../src/evalvault/adapters/outbound/dataset/thresholds.py`
- 결과 엔티티: `../../src/evalvault/domain/entities/result.py`

## 메트릭 체계

- 레지스트리: `../../src/evalvault/domain/metrics/registry.py`
- 메트릭 API 문서: `../api/domain/metrics.md`
- 요약/도메인 메트릭: `../../src/evalvault/domain/metrics/`

구성 차원:
- source: ragas/custom
- category: qa/summary/retrieval/domain
- requirement: ground_truth/embeddings 여부

예시:
- QA: faithfulness, answer_relevancy, context_precision
- Summary: summary_score, summary_faithfulness, entity_preservation
- Retrieval: mrr, ndcg, hit_rate

## 산출물(Artifacts)와 index.json

분석 파이프라인은 `artifacts/` 아래에 노드별 JSON과 `index.json`을 생성한다.

관련 파일:
- 아티팩트 IO: `../../src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
- FS 포트: `../../src/evalvault/ports/outbound/artifact_fs_port.py`
- FS 구현: `../../src/evalvault/adapters/outbound/artifact_fs.py`
- 아티팩트 린트: `../../src/evalvault/domain/services/artifact_lint_service.py`

## Excel/리포트

- Excel export 스펙: `../guides/EVALVAULT_RUN_EXCEL_SHEETS.md`
- DB export 구현: `../../src/evalvault/adapters/outbound/storage/base_sql.py`
- 보고서 템플릿: `../templates/eval_report_templates.md`

## 참고 경로

- 사용자 가이드: `../guides/USER_GUIDE.md`
- CLI 워크플로우: `../guides/RAG_CLI_WORKFLOW_TEMPLATES.md`
- 도메인 엔티티: `../../src/evalvault/domain/entities/`
- 메트릭 구현: `../../src/evalvault/domain/metrics/`
