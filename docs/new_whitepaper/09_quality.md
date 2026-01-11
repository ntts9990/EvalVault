# 09. 테스트/품질 보증(Quality)

## 이 장의 목적 / 독자 / 선행 지식

- **목적**: 내부 개발자가 EvalVault 품질을 유지하는 실행 규칙(테스트/린트/CI/릴리스)을 이해하고, 변경을 안전하게 배포할 수 있게 한다.
- **독자**: 내부 개발자
- **선행 지식**: pytest/ruff 기본 사용

---

## TL;DR

- 기본 품질 루틴: `pytest` + `ruff check/format`.
- 테스트는 `tests/unit`, `tests/integration`로 역할을 분리한다.
- 외부 의존성(OpenAI/Ollama/Phoenix/Langfuse)이 있는 테스트는 CI에서 스킵될 수 있게 작성한다.
- 릴리스 버전은 `pyproject.toml`이 아니라 **git tag** 기준이다.
- `.env`/실서비스 키는 커밋 금지.

---

## 1) 로컬 개발 품질 루틴

### 1.1 설치

```bash
uv sync --extra dev
```

### 1.2 테스트

```bash
uv run pytest tests -v
```

> **NOTE**: 외부 API가 필요한 시나리오 테스트는 환경 변수가 없으면 스킵될 수 있다.

### 1.3 린트/포맷

```bash
uv run ruff check src/ tests/ && uv run ruff format src/ tests/
```

---

## 2) 테스트 구조(리포지토리 규칙)

- 단위 테스트: `tests/unit/`
- 통합 테스트: `tests/integration/`
- 픽스처: `tests/fixtures/`

권장:
- 테스트 이름은 `test_<behavior>` 형태로
- 외부 의존성이 필요한 테스트는 “없으면 스킵” 가능한 형태로(환경 없는 CI 보호)

---

## 3) CI/CD 및 릴리스

- CI는 여러 OS/여러 Python 버전에서 테스트를 수행한다.
- 릴리스는 main 머지 시 워크플로가 Conventional Commits 규칙에 따라 버전 태그를 결정한다.
  - 즉, `pyproject.toml`의 버전이 단일 진실이 아니다.

---

## 4) 변경 유형별 “품질 기대치”(실무 체크리스트)

### 4.1 도메인 평가/점수 로직 변경

대상 예:
- Ragas/커스텀 메트릭 추가/수정
- threshold 정책 변경

권장 검증:
- [ ] 관련 단위 테스트 추가/갱신 (`tests/unit/`)
- [ ] 최소 1개 fixture로 스모크 실행 가능해야 함
- [ ] (가능하면) 결과 해석이 바뀌는 경우 문서/가이드 갱신

근거:
- `src/evalvault/domain/services/evaluator.py`

### 4.2 분석(DAG 파이프라인) 변경

대상 예:
- 새 분석 모듈 추가
- 템플릿 DAG 변경(의존성/노드 연결)
- 아티팩트 출력 스키마 변경

권장 검증:
- [ ] `evalvault pipeline templates`로 템플릿 구조가 의도대로인지 확인
- [ ] `evalvault pipeline analyze "<query>"`가 최소 1개 run_id에서 완주하는지 확인
- [ ] 아티팩트 저장 경로/인덱스(`index.json`)가 깨지지 않는지 확인

근거:
- `src/evalvault/domain/services/pipeline_orchestrator.py`
- `src/evalvault/domain/services/pipeline_template_registry.py`
- `src/evalvault/adapters/outbound/analysis/pipeline_factory.py`
- `src/evalvault/adapters/inbound/cli/commands/pipeline.py`
- `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`

### 4.3 Domain Memory 변경

대상 예:
- 포트(계약) 변경
- SQLite 스키마/FTS 변경
- Formation/Evolution/Retrieval 알고리즘 변경

권장 검증:
- [ ] 새 스키마가 “기존 DB”에서 초기화/마이그레이션 이슈 없이 동작하는지 확인
- [ ] FTS5 인덱스가 깨졌을 때 복구 루틴이 존재/유효한지 확인
- [ ] 메모리 결과가 “다음 실행에서” 실제로 재사용되는지(예: threshold 조정, fact 주입)

근거:
- `src/evalvault/ports/outbound/domain_memory_port.py`
- `src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py`
- `src/evalvault/adapters/outbound/domain_memory/domain_memory_schema.sql`
- `src/evalvault/domain/services/domain_learning_hook.py`
- `src/evalvault/domain/services/memory_aware_evaluator.py`

### 4.4 관측성/트레이싱 변경

대상 예:
- StageEvent/StageMetric 구조 변경
- Phoenix/OTel 전송/계측 변경
- Open RAG Trace 표준 필드 변경

권장 검증:
- [ ] StageEvent 생성이 예상하는 속성/타이밍을 유지하는지 확인
- [ ] Phoenix instrumentation 토글이 예상대로 동작하는지 확인(활성/비활성 모두)
- [ ] OTel 속성 제한(스칼라/배열) 위반이 없는지 확인(복합 구조는 JSON 문자열)

근거:
- `src/evalvault/domain/services/stage_event_builder.py`
- `src/evalvault/domain/services/stage_metric_service.py`
- `src/evalvault/adapters/outbound/tracker/phoenix_adapter.py`
- `src/evalvault/config/phoenix_support.py`
- `src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py`
- `src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py`

### 4.5 CLI/API 변경

대상 예:
- CLI 옵션/명령 추가
- 출력 포맷(보고서/JSON) 변경

권장 검증:
- [ ] `--help`가 의미 있게 유지되는지 확인(Typer help)
- [ ] 최소 1개 fixture로 스모크 실행(기본 run + 필요 시 auto analyze)

근거:
- `src/evalvault/adapters/inbound/cli/app.py`
- `src/evalvault/adapters/inbound/cli/commands/`

### 4.6 문서 변경

대상 예:
- 백서/가이드/SSoT 문서 업데이트

권장 검증:
- [ ] 실행 명령/경로가 실제 코드/구조와 일치하는지 확인
- [ ] 링크(상대 경로)가 깨지지 않는지 확인

근거:
- `docs/new_whitepaper/STYLE_GUIDE.md`

---

## Evidence

- `AGENTS.md` (개발 명령/테스트/품질 규칙)
- `CONTRIBUTING.md` (테스트/린트/커밋 가이드)
- `docs/ROADMAP.md` (품질/운영 개선 트랙)

---

## 전문가 관점 체크리스트

- [ ] 신규 개발자가 “무엇을 실행해야 안전한지” 바로 알 수 있는가
- [ ] 품질 규칙이 현실적인 작업 흐름(uv/pytest/ruff)과 연결되는가
- [ ] 변경 유형별 최소 검증 루틴이 누락되지 않는가
- [ ] 릴리스 기준(git tag) 같은 중요한 운영 지식이 누락되지 않는가

---

## 향후 변경 시 업데이트 가이드

- 새 확장 포인트(메트릭/모듈/포트)가 추가되면, 이 장의 **4장(변경 유형별 기대치)**에
  “최소 검증 루틴”을 한 줄이라도 추가한다.
- CI/릴리스 정책이 바뀌면, `AGENTS.md`와 함께 이 장의 **3장**을 갱신한다.
