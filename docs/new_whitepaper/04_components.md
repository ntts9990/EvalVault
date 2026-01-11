# 04. 주요 컴포넌트 지도

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: “어디에 뭐가 있지?”를 5분 안에 해결한다. 컴포넌트와 파일 경로를 지도로 제공한다.
- **독자**: 내부 개발자 전원
- **선행 지식**: `src/evalvault/` 트리 탐색 경험

---

## TL;DR

- 진입점은 크게 **CLI(Typer)** 와 **API(FastAPI)** 두 가지다.
- 도메인 핵심 오케스트레이션(평가/분석/학습/시각화)은 `src/evalvault/domain/services/`에 있다.
- 외부 연동(LLM/Storage/Tracker/Tracer)은 `src/evalvault/adapters/outbound/`가 담당한다.
- 분석 파이프라인(DAG)은 “의도(AnalysisIntent) → 템플릿 → 모듈 실행 → artifacts/index.json” 흐름으로 작동한다.

---

## 1) Inbound (사용자/외부 요청)

### 1.1 CLI

> 내부 개발자에게 가장 중요한 것은 “어떤 커맨드가 어디서 구현되는지”다.

- 루트 앱: `src/evalvault/adapters/inbound/cli/app.py`
- 핵심 평가 실행: `src/evalvault/adapters/inbound/cli/commands/run.py`
  - `def run(...)`: 평가 실행 + 저장 + 추적 + 자동 분석
  - `run-simple`, `run-full`: 모드 별칭
- 분석/비교 관련(대표):
  - `src/evalvault/adapters/inbound/cli/commands/analyze.py`
  - `src/evalvault/adapters/inbound/cli/utils/analysis_io.py` (artifacts/index.json, 보고서 추출)

### 1.2 API (FastAPI)

- 앱 엔트리: `src/evalvault/adapters/inbound/api/main.py` (`create_app`)
- 주요 라우터:
  - Runs: `src/evalvault/adapters/inbound/api/routers/runs.py`
  - Pipeline: `src/evalvault/adapters/inbound/api/routers/pipeline.py`
  - Domain: `src/evalvault/adapters/inbound/api/routers/domain.py`
  - Knowledge: `src/evalvault/adapters/inbound/api/routers/knowledge.py`

> **NOTE**: 라우터 목록은 `create_app()`의 `app.include_router(...)`가 가장 빠른 진입점이다.

---

## 2) Domain (비즈니스 규칙)

> 도메인은 “평가/분석/학습/리포트/시각화”의 규칙을 가진다.

### 2.1 평가

- 평가 엔진: `src/evalvault/domain/services/evaluator.py` (`class RagasEvaluator`)
  - threshold 우선순위: CLI > dataset > default
  - retriever 기반 컨텍스트 채움(`apply_retriever_to_dataset`) 경로 포함

### 2.2 분석

- 통합 분석 서비스(통계/NLP/인과): `src/evalvault/domain/services/analysis_service.py` (`class AnalysisService`)
- DAG 분석 파이프라인(의도 기반):
  - `src/evalvault/domain/entities/analysis_pipeline.py` (AnalysisIntent/AnalysisPipeline)
  - `src/evalvault/domain/services/pipeline_orchestrator.py` (PipelineOrchestrator/AnalysisPipelineService)

### 2.3 학습(Domain Memory)

- 메모리 기반 평가 래퍼: `src/evalvault/domain/services/memory_aware_evaluator.py` (`class MemoryAwareEvaluator`)
- 메모리 인사이트: `src/evalvault/domain/services/memory_based_analysis.py`
- 평가 완료 후 학습 훅: `src/evalvault/domain/services/domain_learning_hook.py`
- 메모리 엔티티: `src/evalvault/domain/entities/memory.py`

### 2.4 관측 이벤트(Stage Events)

- Stage 이벤트 생성: `src/evalvault/domain/services/stage_event_builder.py` (`class StageEventBuilder`)

### 2.5 시각화(Visual Space)

- 좌표/클러스터 맵 계산: `src/evalvault/domain/services/visual_space_service.py`

---

## 3) Ports (계약)

> “도메인이 외부에 요구하는 것”과 “도메인이 외부에 제공하는 것”을 분리한다.

- Domain Memory 포트: `src/evalvault/ports/outbound/domain_memory_port.py`
- Tracing 포트: `src/evalvault/ports/outbound/tracer_port.py`
- 분석 모듈 포트: `src/evalvault/ports/outbound/analysis_module_port.py`

---

## 4) Outbound (외부 시스템 연동)

- LLM 어댑터: `src/evalvault/adapters/outbound/llm/`
- 저장소 어댑터: `src/evalvault/adapters/outbound/storage/`
- 트래커 어댑터: `src/evalvault/adapters/outbound/tracker/`
- 트레이서(Open RAG Trace): `src/evalvault/adapters/outbound/tracer/`
- 분석 모듈(파이프라인 노드): `src/evalvault/adapters/outbound/analysis/`

분석 모듈 등록(실제 등록 위치):
- `src/evalvault/adapters/outbound/analysis/pipeline_factory.py` (`build_analysis_pipeline_service`)

---

## 5) 설정/프로필

- 런타임 설정: `src/evalvault/config/`
- 모델 프로필: `config/models.yaml`
- 환경 변수: `.env` (커밋 금지)

---

## 6) 테스트/데이터

- 단위 테스트: `tests/unit/`
- 통합 테스트: `tests/integration/`
- e2e 데이터/픽스처: `tests/fixtures/`

---

## 7) ‘어디부터 보면 되나’ 빠른 레시피

- “`--auto-analyze` 결과가 이상하다” → `src/evalvault/adapters/inbound/cli/utils/analysis_io.py` (artifacts/index.json, 보고서 추출) → `src/evalvault/domain/services/pipeline_orchestrator.py`
- “threshold가 기대와 다르다” → `src/evalvault/domain/services/evaluator.py` (우선순위) → Domain Memory 사용 여부 확인
- “Domain Memory가 컨텍스트를 어떻게 바꾸나” → `src/evalvault/domain/services/memory_aware_evaluator.py` (`augment_context_with_facts`)
- “Phoenix/OTel 트레이싱 연결” → `src/evalvault/config/instrumentation.py` + `docker-compose.phoenix.yaml`

---

## 8) 향후 변경 시 업데이트 가이드

- 새 CLI 커맨드/옵션이 추가되면: 04장의 “Inbound CLI” 목록에 파일 경로를 추가하고, 관련 장(03/06/12)에 링크를 걸어준다.
- 새 API 라우터가 추가되면: 04장의 “API 라우터” 목록에 추가하고, `create_app()` 기준으로 검증한다.
- 분석 모듈이 추가되면: `pipeline_factory.py`에 등록되는지 확인하고, 04장에는 “모듈 등록 위치”만 유지하며 상세 설명은 07/08장으로 보낸다.

---

## Evidence

- `src/evalvault/adapters/inbound/cli/commands/run.py` (CLI 오케스트레이션)
- `src/evalvault/adapters/inbound/api/main.py` (FastAPI 라우터 연결)
- `src/evalvault/adapters/inbound/api/routers/runs.py` (Runs API)
- `src/evalvault/adapters/outbound/analysis/pipeline_factory.py` (분석 모듈 등록)
- `docs/new_whitepaper/02_architecture.md` (설계 원칙/구조)

---

## 전문가 관점 체크리스트

- [ ] 신규 합류자가 10분 내에 “진입점”과 “핵심 서비스”를 찾을 수 있는가
- [ ] 지도 역할에 맞게 과도한 세부 구현 설명을 피했는가
- [ ] 경로가 실제로 존재하는가(문서가 코드와 싱크되는가)
