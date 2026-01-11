# 13. 표준/생태계(Standards)

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: EvalVault가 “팀 내부 도구”를 넘어 확장 가능한 평가/관측 생태계를 구성하기 위해 따르는 표준과 규약을 정리한다.
- **독자**: 고급 내부 개발자
- **선행 지식**: OpenTelemetry 기본 개념(있으면 도움)

---

## TL;DR

- EvalVault는 OpenTelemetry를 기반으로, Open RAG Trace 형태의 **표준 계측 어댑터**를 제공한다.
- 표준 연동은 “스키마(필드) 고정 → Collector 구성 → 내보내기/검증” 순서로 접근한다.
- 데이터/산출물의 표준화는 재현성과 비교를 위한 핵심이며, 파이프라인 아티팩트 인덱스가 그 역할을 한다.
- 개발 프로세스는 Conventional Commits 기반 자동 버저닝/릴리스와 연결된다.

---

## 1) Open RAG Trace (표준 계측)

### 1.1 최소 스키마(코드 기준)

- 표준 어댑터: `src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py`
  - 표준 속성:
    - `spec.version` (기본 `0.1`)
    - `rag.module` (RAG 모듈/단계 식별자)
  - OTel이 없으면 `_NoOpSpan`으로 안전하게 동작한다.

- 커스텀 확장 규약:
  - `OpenRagTraceConfig.custom_prefix` 기본값이 `custom.`이다.
  - 표준 필드로 커버하기 어려운 데이터는 `custom.<key>`로 확장한다.

### 1.2 OTel 속성 제약과 직렬화 규칙

- 속성 직렬화 도우미: `src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py`
  - `build_retrieval_attributes(...)`는 문서 목록 같은 복합 구조를
    `retrieval.documents_json`(JSON 문자열)로 저장한다.
  - 원칙: “스칼라/스칼라 배열”을 넘어가는 값은 JSON 문자열로 보낸다.

---

## 2) Collector (스키마 강제/보강)

- 로컬 Collector 설정: `scripts/dev/otel-collector-config.yaml`
  - traces pipeline에서 `spec.version=0.1`을 강제로 삽입한다.

- 로컬 Phoenix+Collector 구성: `docker-compose.phoenix.yaml`

운영 표준:
- “어떤 서비스가 trace를 보내든” 최소한 `spec.version`은 붙어 있어야 한다.

---

## 3) 데이터/산출물 표준화

### 3.1 StageEvent/StageMetric

- StageEvent는 “단계별 관측”의 공통 단위다.
  - 근거: `src/evalvault/domain/services/stage_event_builder.py`
- StageMetric은 “단계별 지표”의 공통 단위다.
  - 근거: `src/evalvault/domain/services/stage_metric_service.py`

표준화 원칙:
- stage_type은 시스템 전반에서 동일 의미를 유지해야 한다(`retrieval`, `output` 등).
- latency는 `<stage_type>.latency_ms`로 통일한다.

### 3.2 분석 파이프라인(DAG) 아티팩트

- 분석 엔티티 표준: `src/evalvault/domain/entities/analysis_pipeline.py`
  - 의도(`AnalysisIntent`)는 안정적인 키여야 하며, 사용자 질의에서 분류/템플릿에 연결된다.

- 아티팩트 인덱스: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
  - `write_pipeline_artifacts(...)`는
    - 노드별 `<node_id>.json`
    - 파이프라인 `index.json` (duration, nodes[], final_output_path)
    를 생성한다.

표준화 원칙:
- 보고서(md)와 원본 JSON을 분리한다.
- `index.json`은 “재현/디버깅의 단일 진실”로 취급한다.

---

## 4) 개발 프로세스 규약

- 커밋 메시지: Conventional Commits (`feat:`, `fix:`, `docs:` 등)
- 릴리스/버전: main 머지 시 자동 버저닝(태그 기반)

근거:
- `AGENTS.md`

---

## Evidence

- Open RAG Trace:
  - `src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py`
  - `src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py`
- Collector/Compose:
  - `scripts/dev/otel-collector-config.yaml`
  - `docker-compose.phoenix.yaml`
- Stage 표준:
  - `src/evalvault/domain/services/stage_event_builder.py`
  - `src/evalvault/domain/services/stage_metric_service.py`
- 아티팩트 표준:
  - `src/evalvault/domain/entities/analysis_pipeline.py`
  - `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
- 프로세스:
  - `AGENTS.md`

---

## 전문가 관점 체크리스트

- [ ] 표준 문서가 “어디에 어떤 근거가 있는지”로 연결되는가
- [ ] 팀 외부 시스템과의 연결을 고려한 스키마/검증 절차가 명시되는가
- [ ] 산출물(JSON/인덱스)이 장기적으로 비교 가능한 형태로 유지되는가
- [ ] 개발 프로세스 규약이 실제 릴리스 파이프라인과 일치하는가

---

## 향후 변경 시 업데이트 가이드

- Open RAG Trace의 표준 필드를 변경/추가했다면:
  - `open_rag_trace_adapter.py` + `open_rag_trace_helpers.py` 근거로
    이 장의 **1장**을 업데이트한다.

- Collector가 추가로 강제해야 할 속성이 생기면:
  - `scripts/dev/otel-collector-config.yaml` 근거로
    이 장의 **2장**에 추가한다.

- 아티팩트 인덱스 포맷이 바뀌면:
  - `analysis_io.py` 근거로
    이 장의 **3.2**를 업데이트하고, 기존 인덱스와의 호환성/마이그레이션 방침을 명시한다.
