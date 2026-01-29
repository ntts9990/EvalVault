# RAG Performance Improvement Execution Log

## 목적
- RAG 성능 개선 제안서 기반 작업을 장기적으로 추적/관리한다.
- 단계별 계획, 근거, 실행 상태, 검증 결과를 한 문서에 축적한다.
- 최신 개발 현황의 실행 로그는 본 문서를 기준으로 한다.

## 업데이트 규칙
- 작업 단위(에픽/스프린트/모듈)가 끝날 때마다 이 문서를 갱신한다.
- 모든 변경은 run_id 또는 작업 ID에 연결한다.
- 검증 결과(테스트/진단/리포트 경로)를 필수로 기록한다.

---

## 아키텍처/현황 점검 요약 (2026-01-17)
- Hexagonal 구조 유지: `domain` 중심, `ports` 계약, `adapters` 통합.
- run_id 기반 실행 단위: `EvaluationRun`/`BenchmarkRun`.
- Artifacts-first: `analysis_io.py`의 `write_pipeline_artifacts` + `index.json`.
- Stage Events/Stage Metrics: `stage_event_builder.py`, `stage_metric_service.py`.
- Observability: Langfuse/Phoenix/MLflow Tracker + OpenTelemetry Tracer.
- GraphRAG: `GraphRAGRetriever` 존재, CLI `--retriever graphrag` 지원.
- 노이즈 저감 정리서: `docs/guides/RAG_NOISE_REDUCTION_GUIDE.md`

## 작업 티켓 백로그 (세분화)

## 우선순위 로드맵
1) EPIC-0 → 2) EPIC-1 → 3) EPIC-3 → 4) EPIC-2 → 5) EPIC-4

### EPIC-0 기준선/범위 고정 (P0)
- EV-RAG-001 KPI baseline 정의 및 threshold 우선순위 확정
  - 담당: Metrics
  - 예상: 2~3일
  - 리스크: 메트릭 간 threshold 충돌(정규화 필요)
  - 근거: `src/evalvault/domain/metrics/registry.py`, `src/evalvault/domain/services/evaluator.py`
  - 산출물: KPI 표(메트릭/임계값/설명) + 기준 run_id
  - 검증: `uv run evalvault run ... --auto-analyze` 1회 실행
- EV-RAG-002 표준 데이터셋 버전 고정 및 변동 이력 기록
  - 담당: Dataset
  - 예상: 1~2일
  - 리스크: 데이터셋 포맷 편차(JSON/CSV/XLSX)로 비교 불일치
  - 근거: `tests/fixtures/e2e/*`, `examples/benchmarks/*`
  - 산출물: 데이터셋 버전/해시/변경 로그
  - 검증: 데이터셋 로더(JSON/CSV/XLSX) 모두 로드 확인
- EV-RAG-003 run 비교 리포트 템플릿 확정
  - 담당: Analysis Pipeline
  - 예상: 1~2일
  - 리스크: 산출물 경로/인덱스 규칙 불일치
  - 근거: `src/evalvault/domain/services/pipeline_template_registry.py`, `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
  - 산출물: 비교 리포트 템플릿 + index.json 기준 경로
  - 검증: `evalvault analyze-compare <RUN_A> <RUN_B>` 결과 생성
- EV-RAG-004 Stage Events 최소 스키마 점검 및 문서 동기화
  - 담당: Observability
  - 예상: 1~2일
  - 리스크: stage_type 누락으로 분석 파이프라인 불안정
  - 근거: `src/evalvault/domain/entities/stage.py`, `src/evalvault/domain/services/stage_event_builder.py`
  - 산출물: stage_type 필수 목록 + 예시 JSONL
  - 검증: `evalvault stage ingest` → `stage summary` 성공

### EPIC-1 Retrieval 개선 체계화 (P1)
- EV-RAG-101 리랭킹 on/off 실험 플래그 및 stage metric 기준 확정
  - 담당: Retrieval
  - 예상: 2~3일
  - 리스크: rerank 메트릭 수집 누락 시 비교 불가
  - 근거: `src/evalvault/domain/services/stage_metric_service.py`
  - 산출물: rerank 메트릭 표 + threshold 기본값
  - 검증: rerank 포함/미포함 run 비교
- EV-RAG-102 GraphRAG 결과를 stage event + artifact로 저장
  - 담당: GraphRAG
  - 예상: 3~5일
  - 리스크: KG 데이터 품질 불안정으로 결과 변동
  - 근거: `src/evalvault/adapters/outbound/kg/graph_rag_retriever.py`, `src/evalvault/domain/entities/rag_trace.py`
  - 산출물: graphrag stage 이벤트 샘플 + artifact 경로
  - 검증: graphrag retriever 실행 후 artifact 생성 확인
- EV-RAG-103 Retrieval benchmark 파이프라인 확장(precision/recall/NDCG)
  - 담당: Benchmark
  - 예상: 2~4일
  - 리스크: ground_truth 부족으로 지표 신뢰도 저하
  - 근거: `src/evalvault/adapters/outbound/analysis/retrieval_benchmark_module.py`
  - 산출물: retrieval 리포트 템플릿
  - 검증: benchmark run + 리포트 생성

### EPIC-2 Grounding/환각 리스크 대응 (P3)
- EV-RAG-201 Grounding 관련 stage metric 추가 정의
  - 담당: Safety/Quality
  - 예상: 3~5일
  - 리스크: 메트릭 정의의 주관성/과적합
  - 근거: `src/evalvault/domain/services/stage_metric_service.py`
  - 산출물: grounding metric 스펙 + threshold
  - 검증: stage metrics 출력에 grounding 항목 노출
- EV-RAG-202 Improvement Guide에 환각 리스크 대응 레버 연결
  - 담당: Analysis/Report
  - 예상: 2~3일
  - 리스크: 리포트 해석 오류로 잘못된 개선 가이드
  - 근거: `src/evalvault/domain/services/improvement_guide_service.py`
  - 산출물: 리포트 내 “원인-레버” 매핑
  - 검증: 분석 리포트에 자동 포함 여부 확인
- EV-RAG-203 고위험 도메인 정책 플래그/워크플로 정의
  - 담당: Policy/Workflow
  - 예상: 2~4일
  - 리스크: 운영 정책과 CLI/API 옵션 불일치
  - 근거: CLI 옵션/설정(`config/`, `adapters/inbound/cli`)
  - 산출물: 정책 플래그 설계 + 사용 가이드
  - 검증: 플래그 활성화 시 경고/보류 문구 확인

### EPIC-3 Observability/운영 게이트 (P2)
- EV-RAG-301 운영 KPI(p95/cost/timeout) stage metric 표준화
  - 담당: Observability
  - 예상: 2~3일
  - 리스크: 비용/지연 데이터 부정확(수집 위치 불명확)
  - 근거: `src/evalvault/domain/services/stage_metric_service.py`
  - 산출물: 운영 KPI 스펙 + threshold
  - 검증: stage metrics summary에 운영 KPI 표시
- EV-RAG-302 Tracker metadata에 운영 KPI 주입
  - 담당: Tracker/Tracing
  - 예상: 2~4일
  - 리스크: Tracker별 스키마 불일치(Langfuse/Phoenix)
  - 근거: `src/evalvault/adapters/outbound/tracker/*`, `src/evalvault/adapters/inbound/cli/commands/run.py`
  - 산출물: tracker metadata 스키마
  - 검증: Langfuse/Phoenix trace metadata 확인
- EV-RAG-303 CI Gate에 baseline 비교 자동화 연결
  - 담당: CI/DevOps
  - 예상: 3~5일
  - 리스크: CI 환경에서 외부 의존성 실패
  - 근거: `scripts/verify_workflows.py`, CI workflow
  - 산출물: CI 로그에 비교 리포트 링크
  - 검증: CI에서 gate 실패 시 차단 동작 확인

### EPIC-4 Judge/난이도 프로파일링 (P4)
- EV-RAG-401 난이도 v0 휴리스틱 정의 및 데이터 수집
  - 담당: Data/Analytics
  - 예상: 3~5일
  - 리스크: 난이도 지표의 설명력 부족
  - 근거: `domain/entities/dataset.py`, `domain/services/dataset_preprocessor.py`
  - 산출물: 난이도 feature 스키마 + 로그
  - 검증: 난이도 분포 리포트 1회 생성
- EV-RAG-402 judge 캐스케이드 v0 설계(저비용→고비용)
  - 담당: Evaluation
  - 예상: 4~7일
  - 리스크: 평가 편향/일관성 저하
  - 근거: `domain/services/evaluator.py`, judge 관련 모듈
  - 산출물: cascade 정책/설정
  - 검증: 경계 케이스 승격 비율 리포트
- EV-RAG-403 calibration 리포트 자동화(휴먼 샘플링 포함)
  - 담당: QA/Calibration
  - 예상: 3~6일
  - 리스크: 인간 라벨 품질/샘플링 편향
  - 근거: `docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`
  - 산출물: calibration 리포트 템플릿
  - 검증: 분기 1회 생성 가능 상태 확인

## 진행 로그
- 2026-01-18: 병렬 스트림 동시 착수 계획 수립. 스트림별 담당/규칙/검증 기준은 `docs/guides/RAG_NOISE_REDUCTION_GUIDE.md`의 병렬 작업 규칙 섹션을 따른다.
- 2026-01-18: 병렬 작업 진행 로그는 아래 섹션에 기록한다.

## 병렬 작업 로그 (Ralph Loop)
- 상태: 진행
- 스트림: A(데이터 전처리), B(평가 로직), C(Stage 메트릭), D(캘리브레이션 가이드), E(정책/로드맵)
- 공통 규칙: 서로 다른 파일에서 작업, 공유 스키마/출력 포맷 변경은 사전 합의, 문서 오너 지정, 겹치는 내용은 한쪽 문서만 관리
- 검증 기준: 변경 코드에 대한 `pytest` 범위 테스트 실행 및 관련 테스트 통과
- 스트림 A(데이터 전처리)
  - 변경: 노이즈 텍스트/플레이스홀더 제거, 레퍼런스 정규화
  - 파일: `src/evalvault/domain/services/dataset_preprocessor.py`, `tests/unit/domain/services/test_dataset_preprocessor.py`
  - 테스트: `uv run pytest tests/unit/domain/services/test_dataset_preprocessor.py` (6 passed)
- 스트림 B(평가 로직)
  - 변경: 프롬프트 언어 결정 고정(단일 결정) 및 테스트 추가
  - 파일: `src/evalvault/domain/services/evaluator.py`, `tests/unit/domain/services/test_evaluator_comprehensive.py`
  - 테스트: `uv run pytest tests/unit/domain/services/test_evaluator_comprehensive.py` (47 passed)
- 스트림 C(Stage 메트릭)
  - 변경: 평균 계산 안정화(`math.fsum`), 순서 복원/경고 메트릭(`retrieval.ordering_warning`) 추가
  - 파일: `src/evalvault/domain/services/stage_metric_service.py`, `tests/unit/test_stage_metric_service.py`
  - 테스트: `uv run pytest tests/unit/test_stage_metric_service.py` (10 passed)
  - 문서: ordering_warning 런북/strict 전환 기준/전처리 노이즈 규칙 정의 추가
- 스트림 D(캘리브레이션 가이드)
  - 변경: 운영 체크리스트/노이즈 가드레일 명시
  - 파일: `docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md`
  - 테스트: 문서 변경(실행 테스트 없음)
- 스트림 E(정책/로드맵)
  - 변경: 노이즈 저감 원칙 및 artifacts 추적 규칙 보강
- 파일: `docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md`, `docs/handbook/CHAPTERS/00_overview.md`
  - 테스트: 문서 변경(실행 테스트 없음)
