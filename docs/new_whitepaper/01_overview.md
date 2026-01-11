# 01. 프로젝트 개요

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: EvalVault가 무엇을 해결하고, 어떤 구성요소(평가/관측/표준/학습/분석)로 시스템을 구성하는지 “공통 언어”를 만든다.
- **독자**: 내부 개발자(온보딩 포함)
- **선행 지식**: RAG 기본 개념(질문→검색→생성), Python 프로젝트 실행 경험

---

## TL;DR

- EvalVault는 RAG 시스템을 **평가(Evaluation)**하고, 실행 단위를 `run_id`로 묶어 **분석(Analysis)**과 **비교(Compare)**를 가능하게 하는 플랫폼이다.
- CLI와 Web UI는 **동일한 DB**를 공유하면 실행 결과를 이어서 볼 수 있다.
- 시스템은 5대 축으로 설명한다: **평가 · 관측 · 표준 연동 · 학습(Domain Memory) · 분석 파이프라인**.
- 설계 원칙은 `domain`의 순수성(외부 의존성 격리)이며, 이를 위해 **Hexagonal Architecture(Ports & Adapters)**를 채택한다.

---

## 1) 해결하려는 문제(내부 개발자의 실제 고통)

RAG 시스템 개발/운영에서 반복되는 문제는 대체로 아래 세 가지로 수렴한다.

1. **개선이 ‘좋아진 것 같은데’ 수치로 말하기 어렵다**
   - 모델/프롬프트/리트리버를 바꿔도, 결과가 안정적으로 비교되지 않으면 개선이 누적되지 않는다.
2. **로그/트레이스/메트릭이 흩어져 원인 추적이 어렵다**
   - Retrieval/Output 단계별 병목과 품질 문제를 한 눈에 보기 어렵다.
3. **ad-hoc 스크립트가 늘어나 재현성과 품질 게이트가 깨진다**
   - 팀이 커질수록 동일한 기준으로 평가·운영하기가 어려워진다.

EvalVault는 이를 “실행 단위(run_id) + 표준 산출물 + 분석 파이프라인 + 옵저버빌리티 연결”로 해결하는 것을 목표로 한다.

---

## 2) 5대 핵심 축(공통 언어)

> 아래 항목은 이후 모든 장에서 동일한 용어로 반복된다.

### 2.1 평가(Evaluation)

- 데이터셋 기반으로 메트릭을 계산하고, 데이터셋에 포함된 threshold 또는 CLI threshold를 기준으로 “합격/위험”을 판단한다.
- 평가 엔진의 근거: `src/evalvault/domain/services/evaluator.py` (`class RagasEvaluator`)

### 2.2 관측(Observability)

- 실행을 단계별(Stage)로 분해해 “어디서 느렸는지/어디서 깨졌는지”를 추적한다.
- Stage 이벤트 생성 근거: `src/evalvault/domain/services/stage_event_builder.py` (`class StageEventBuilder`)

### 2.3 표준 연동(Open RAG Trace)

- OpenTelemetry 기반의 최소 계측을 제공해, EvalVault 외부의 RAG 시스템도 동일한 방식으로 수집/분석할 수 있게 한다.
- 최소 어댑터 근거: `src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py`

### 2.4 학습(Domain Memory)

- 평가 결과로부터 사실/패턴/행동을 축적하고, 다음 평가에서 threshold 조정/컨텍스트 보강에 반영할 수 있게 한다.
- 핵심 근거:
  - `src/evalvault/domain/services/memory_aware_evaluator.py` (`class MemoryAwareEvaluator`)
  - `src/evalvault/domain/services/domain_learning_hook.py` (`class DomainLearningHook`)
  - `src/evalvault/domain/entities/memory.py` (FactualFact/LearningMemory/BehaviorEntry)

### 2.5 분석 파이프라인(Analysis Pipelines)

- “왜 점수가 낮았는지”를 답하기 위해 모듈을 DAG로 실행하고, 노드별 산출물을 아티팩트로 남긴다.
- 핵심 근거:
  - `src/evalvault/domain/entities/analysis_pipeline.py` (AnalysisIntent/AnalysisPipeline)
  - `src/evalvault/domain/services/pipeline_orchestrator.py` (PipelineOrchestrator/AnalysisPipelineService)
  - `src/evalvault/adapters/inbound/cli/utils/analysis_io.py` (artifacts/index.json)

---

## 3) 내부 개발자 관점의 최소 사용 시나리오

### 3.1 1회 실행(스모크)

```bash
uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db \
  --auto-analyze
```

> **NOTE**: `--mode simple`은 기본적으로 “간편 실행”을 목표로 하며, 프리셋 정의는 `src/evalvault/adapters/inbound/cli/commands/run_helpers.py`의 `RUN_MODE_PRESETS`를 기준으로 한다.

### 3.2 결과 확인(로컬 파일)

- 분석 요약 JSON: `reports/analysis/analysis_<RUN_ID>.json`
- 분석 리포트(Markdown): `reports/analysis/analysis_<RUN_ID>.md`
- 분석 아티팩트 인덱스: `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`

### 3.3 CLI ↔ Web UI 연결(동일 DB 사용)

```bash
# Terminal 1
uv run evalvault serve-api --reload

# Terminal 2
cd frontend
npm install
npm run dev
```

> **NOTE**: 동일 DB를 공유하면, CLI로 만든 실행 결과를 Web UI에서 바로 조회할 수 있다.

---

## 4) 문서 지도(다른 장에서 무엇을 얻는가)

- 아키텍처 경계/의존성 규칙이 궁금하면: [`02_architecture.md`](02_architecture.md)
- `run_id` 기준 실행/분석 흐름이 궁금하면: [`03_data_flow.md`](03_data_flow.md)
- CLI/API/LLM/Storage 등 구성요소를 빠르게 찾으려면: [`04_components.md`](04_components.md)
- 전문가 관점으로 문서를 읽는 프레임이 필요하면: [`05_expert_lenses.md`](05_expert_lenses.md)

---

## 5) 향후 변경 시 업데이트 가이드

- 평가 메트릭/프리셋이 바뀌면: 01장의 5대 축 설명과 06장의 “근거 매핑 표”를 함께 갱신한다.
- 관측/트레이싱이 바뀌면: 01장(요약) + 12장(운영/모니터링) + 13장(표준)에서 근거 링크를 최신화한다.
- Domain Memory 스키마/동작이 바뀌면: 07장(고급 기능)과 08장(커스터마이징)의 가이드를 갱신한다.

---

## Evidence

- `README.md` (5대 축, 빠른 시작, 산출물 경로)
- `docs/guides/USER_GUIDE.md` (워크플로/설치/CLI/Web 상세)
- `docs/new_whitepaper/02_architecture.md` (미션/구조/원칙)
- `src/evalvault/adapters/inbound/cli/commands/run.py` (CLI 관점 워크플로)
- `src/evalvault/adapters/inbound/cli/commands/run_helpers.py` (실행 모드 프리셋)

---

## 전문가 관점 체크리스트

- [ ] 용어(평가/관측/표준/학습/분석)가 이후 장과 충돌하지 않는가
- [ ] 초급 독자가 실행 성공 경험(스모크)을 먼저 얻는가
- [ ] 문장이 과도하게 길거나, 모호한 추상 표현이 남발되지 않는가
