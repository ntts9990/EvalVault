# EvalVault 아키텍처 & 개발 정책 점검 리포트

> 작성일: 2026-01-01
> 작성자: 코딩 에이전트 (Codex)
> 목적: 추가 개발/리팩토링 착수 전 Hexagonal + Clean Architecture 준수 여부와 TDD·YAGNI 정책 실행 현황 점검

---

## 1. 점검 범위와 수행 방식

- **소스 구조 조사**: `src/evalvault/domain`, `src/evalvault/ports`, `src/evalvault/adapters`, `config/`, `docs/`, `scripts/` 전수 확인. 툴 전용 `./agent` 디렉터리는 범위에서 제외.
- **의존성 역전 검증**: `rg "from evalvault.adapters" src/evalvault/domain` → 결과 0건으로 도메인이 어댑터를 참조하지 않음을 확인.
- **테스트 실행**
  1. `uv run pytest tests/unit/domain/services/test_improvement_guide_service.py tests/unit/test_evaluator.py tests/integration/test_full_workflow.py -v`
  2. `uv run pytest tests/unit/test_sqlite_storage.py tests/unit/test_postgres_storage.py -v`
  → 총 91개 케이스 green, P0/P1.2 안전망 확보.
- **문서/템플릿 점검**: `docs/ARCHITECTURE.md`, `docs/QUERY_BASED_ANALYSIS_PIPELINE.md`, `scripts/pipeline_template_inspect.py`의 최신성 확인.

---

## 2. Hexagonal & Clean Architecture 준수 현황

### 2.1 Domain 계층

- `src/evalvault/domain/services`는 서비스 클래스만 포함하며 각 서비스는 포트 인터페이스만 의존. 예: `ImprovementGuideService`가 `PatternDetectorPort`/`InsightGeneratorPort`만 주입받아 사용 (`src/evalvault/domain/services/improvement_guide_service.py:22-64`).
- 실험, 평가, 분석 등 핵심 엔터티가 `src/evalvault/domain/entities`에 분리되어 있으며, metrics, NLP 분석 타입도 전용 모듈로 분리 (`entities/analysis`, `entities/experiment`).
- 규칙: 서비스는 입력/출력 DTO와 포트만 다루고 외부 구현체를 몰라 Clean Architecture 경계가 유지됨.

### 2.2 Ports 계층

- **Outbound**: LLM, 저장소, 개선 가이드, 한국어 NLP, 분석 모듈 등 15개 포트가 `src/evalvault/ports/outbound/*.py`에 정의. 각 포트는 `typing.Protocol` 기반으로 설계되어 의존성 주입이 용이.
- **Inbound**: CLI/Web/파이프라인 진입점은 `ports/inbound`에서 요구하는 계약(예: `AnalysisPipelinePort`)만 의존.

### 2.3 Adapter 계층

- **LLM 어댑터 공통화**: `BaseLLMAdapter`와 `TokenUsage`가 `src/evalvault/adapters/outbound/llm/base.py`에 위치해 OpenAI/Azure/Anthropic/Ollama가 동일한 토큰 추적·ThinkingConfig 로직을 공유함.
- **저장소 어댑터 공통화 (신규)**: `src/evalvault/adapters/outbound/storage/base_sql.py`에 `SQLQueries` + `BaseSQLStorageAdapter`를 추가해 SQLite/PostgreSQL 어댑터가 동일한 직렬화/쿼리 흐름을 재사용.
  - 플레이스홀더/RETURNING 차이를 `SQLQueries` 파라미터로 흡수.
  - 도메인 엔터티 직렬화/역직렬화는 단일 지점에서 수행.
  - `tests/unit/test_sqlite_storage.py`와 `tests/unit/test_postgres_storage.py`가 양쪽 동작을 보증.
- **PostgreSQL 분석 저장 지원 (신규)**: `postgres_schema.sql`에 `analysis_results`/`analysis_reports` 스키마를 추가하고, PostgreSQL 어댑터에 `save_analysis`, `get_analysis`, `save_nlp_analysis` 등 SQLite와 동일한 API를 구현해 모든 분석 타입을 DB 간 일관되게 보존.
- **파이프라인 모듈 ↔ 분석 어댑터 연동 (신규)**: `DataLoaderModule`이 StoragePort를 주입받아 `run_id` 기준으로 `EvaluationRun`을 로드하고, `StatisticalAnalyzerModule`이 `StatisticalAnalysisAdapter.analyze()`를 직접 호출해 통계 요약을 생성. CLI 파이프라인 명령은 SQLiteStorageAdapter를 전달하여 실제 평가 실행을 기반으로 DAG를 실행함.
- **분석 파이프라인 경계**: `docs/QUERY_BASED_ANALYSIS_PIPELINE.md`와 `scripts/pipeline_template_inspect.py`가 `Intent → ModuleCatalog → DAG` 순서를 텍스트/코드 양측에서 명문화하여 AI/휴먼이 동일한 플로우를 따를 수 있음.

### 2.4 의존성 방향 & 검증

- 모든 도메인 서비스가 `evalvault.adapters`로 import하지 않음을 `rg`로 검증.
- `pyproject.toml`와 `src/evalvault/__init__.py`에서 사이클을 일으키는 import 없음.
- `src/evalvault/adapters/inbound/cli.py`는 3,220 LOC로 여전히 크지만 Typer 콜백 내부에서 도메인 서비스/포트를 주입하는 방식은 유지되어 모듈러한 리팩토링만 남음.

---

## 3. 개발 정책 준수 (TDD & YAGNI)

### 3.1 테스트 주도 개발 (TDD) 지표

- **단위 테스트**:
  - 도메인 서비스 테스트 (`tests/unit/domain/services/test_improvement_guide_service.py`)가 하이브리드 개선 로직을 포트 mock으로 검증.
  - 평가기(`tests/unit/test_evaluator.py`)는 메트릭 평균, 병렬 옵션, threshold 적용 로직을 모두 커버.
  - 저장소 어댑터 테스트는 SQL 경계부터 NLP 분석 직렬화까지 관통.
- **통합 테스트**: `tests/integration/test_full_workflow.py`가 CLI→LLM→Langfuse→저장소까지 E2E 흐름을 8단계로 검증.
- **자동화 명령**: `pyproject.toml:74-106`에 `pytest`/`pytest-asyncio`/`pytest-xdist`/`pytest-rerunfailures` 설정이 명시되어 CI에서 동일한 구성을 재사용 가능.

### 3.2 YAGNI 및 의존성 다이어트

- `pyproject.toml:34-96`에서 기본 dependencies는 경량 라이브러리로 제한되고, `analysis`, `korean`, `web`, `postgres`, `mlflow` extras로 무거운 NLP/웹 의존성이 분리. `uv sync --extra ...` 전략으로 필요한 기능만 설치하도록 안내.
- 모듈 설계도 필요 이상의 기능을 미리 넣지 않음. 예: `BaseLLMAdapter`는 토큰 추적/ThinkingConfig만 제공하고 모델별 세부 API 연결은 concrete adapter가 담당.
- `scripts/` 및 `docs/`에 AI/휴먼 공용 템플릿(예: `scripts/pipeline_template_inspect.py`)만 배치하여 새로운 분석 모듈을 생성할 때 필요한 최소한의 가이드만 제공.

---

## 4. 주요 리팩토링/개선 결과 & 남은 과제

| 영역 | 상태 | 세부 내용 |
|------|------|-----------|
| **P0 안전망** | ✅ 완료 | 도메인↔어댑터 의존성 역전, extras 재구성, 분석 파이프라인 문서화 완료. 관련 테스트(도메인 서비스/통합) 통과. |
| **P1.1 LLM 어댑터 통합** | ✅ 완료 | `BaseLLMAdapter`와 `TokenUsage`로 공통 로직 집중 (`src/evalvault/adapters/outbound/llm/base.py`). |
| **P1.2 저장소 어댑터 통합** | ✅ 완료 | 본 작업. `BaseSQLStorageAdapter` + `SQLQueries` 도입, SQLite/Postgres 테스트 green. |
| **P1.3 분석 어댑터 통합** | ⏳ 미착수 | NLP/통계/인과 분석 어댑터는 여전히 중복 직렬화 로직을 포함. `AnalysisDataProcessor` 기반의 공용 계층 필요. |
| **Postgres 분석 저장** | ⚠️ Gap | PostgreSQL 어댑터(`src/evalvault/adapters/outbound/storage/postgres_adapter.py`)는 아직 `analysis_results` 테이블/메서드가 없다. 향후 분석/리포트도 동일한 베이스 클래스로 이동 필요. |
| **CLI 모듈화 (P2)** | ⚠️ Gap | `src/evalvault/adapters/inbound/cli.py`가 3k LOC. 구조 분할(명령/유틸/검증) 작업을 P2에서 시급히 진행해야 함. |
| **Langfuse/Web 통합** | 🙂 우수 | `docs/QUERY_BASED_ANALYSIS_PIPELINE.md` + `Streamlit` 어댑터가 Hexagonal 패턴을 유지하며 Langfuse/웹 UI 기능과 독립적인 테스트 가능 구조를 유지. |

---

## 5. 권장 액션 요약

1. **분석 어댑터 공용 계층 (P1.3)**
   - `src/evalvault/adapters/outbound/analysis/*`에서 데이터프레임 추출/집계 로직을 `AnalysisDataProcessor`로 이동.
   - NLP/통계/인과 어댑터 테스트를 `tests/unit/test_analysis_*`로 보강.
2. **PostgreSQL 분석 저장 지원**
   - `postgres_schema.sql`에 `analysis_results`/`analysis_reports` 테이블 추가 후 `PostgreSQLStorageAdapter`에 대응 메서드 구현.
   - SQLite와 동일한 직렬화 유틸을 활용하도록 `BaseSQLStorageAdapter` 확장.
3. **CLI 모듈 분리 (P2)**
   - Typer 앱을 `adapters/inbound/cli/app.py` + `commands/*.py` 구조로 나누고, 공통 포맷터/검증기를 `cli/utils`에 배치.
   - `tests/unit/test_cli.py`를 서브커맨드 단위로 재구성하여 회귀를 즉시 감지.
4. **분석 Pipeline 문서 → 실행 스크립트 싱크 유지**
   - `scripts/pipeline_template_inspect.py` 실행 결과를 `docs/QUERY_BASED_ANALYSIS_PIPELINE.md`와 연동하는 자동 체크(예: pre-commit script) 도입을 고려.

이상의 점검 결과를 기반으로, 추가 리팩토링·신규 기능을 Hexagonal + Clean 규율 안에서 안전하게 확장할 수 있습니다. P1.3 이후에는 P2 모듈 분리, P3 성능 최적화 순서대로 `docs/IMPROVEMENT_PLAN.md` 로드맵을 따라가면 됩니다.
