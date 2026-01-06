# EvalVault 소스 가이드

> 작성일: 2026-01-06
> 목적: 소스 레벨 관점에서 구성과 확장 지점을 명확히 정리한다.

---

## 작성 규칙

- 각 섹션은 5~9문장 내에서 요약
- 섹션 말미에 근거 경로 2~5개 기입
- 불확실한 내용은 "검증 필요"에만 기록

---

## 1) 레포 구조 요약

요약
- EvalVault의 핵심 패키지는 `src/evalvault/` 아래에 위치하며 domain/ports/adapters/config로 계층이 분리되어 있다.
- 도메인 계층은 엔티티/서비스 중심으로 구성되고, 포트는 inbound/outbound 계약을 통해 외부 의존성을 분리한다.
- 문서 허브는 `docs/`를 배포용과 내부용으로 구분해 운영하며 용어와 구조 기준을 제공한다.
- 테스트는 `tests/fixtures/`에 샘플 데이터셋과 벤치마크 기준 데이터를 모아 재사용한다.
- 패키지 메타데이터와 실행 스크립트는 `pyproject.toml`에 정의되어 CLI와 웹 엔트리포인트를 제공한다.

근거
- docs/INDEX.md
- docs/internal/reference/CLASS_CATALOG.md
- src/evalvault/config/__init__.py
- tests/fixtures/README.md
- pyproject.toml

---

## 2) 도메인/포트/어댑터 구조와 의존 방향

요약
- 도메인 레이어는 평가/분석/메모리 등 핵심 업무를 모델과 서비스로 정의하며 헥사고날 구조의 중심에 위치한다.
- 인바운드 포트는 분석 파이프라인 실행과 같은 유스케이스 인터페이스를 정의해 서비스 호출을 표준화한다.
- 아웃바운드 포트는 LLM 호출, 트래킹 등 외부 시스템 의존성을 인터페이스로 분리한다.
- 인바운드 어댑터는 Typer 기반 CLI를 통해 사용자 입력을 받아 도메인 서비스로 전달한다.
- 의존 방향은 도메인 → 포트(계약) → 어댑터(구현) 흐름으로 설명되며, 이는 클래스 카탈로그의 헥사고날 분류와 일치한다.

근거
- docs/internal/reference/CLASS_CATALOG.md
- src/evalvault/ports/inbound/analysis_pipeline_port.py
- src/evalvault/ports/outbound/llm_port.py
- src/evalvault/ports/outbound/tracker_port.py
- src/evalvault/adapters/inbound/cli/app.py

---

## 3) 주요 실행 플로우 (CLI/파이프라인/평가)

요약
- CLI는 `run`, `pipeline`, `domain`, `benchmark`, `stage` 등 주요 실행 흐름을 제공하고 공통 옵션으로 프로필/DB/메모리를 제어한다.
- 평가 입력은 JSON/CSV/XLSX 데이터셋을 받아 테스트 케이스 단위로 변환되며 질문/답변/컨텍스트/정답 정보를 포함한다.
- `run` 경로에서는 Ragas 기반 메트릭과 커스텀 메트릭을 계산해 `EvaluationRun`으로 집계하며 임계값은 데이터셋 → 기본값(0.7) 순으로 결정되고, API/Domain Memory가 있을 때만 오버라이드된다.
- Domain Memory는 `--use-domain-memory` 등의 옵션으로 활성화되며 threshold 조정과 컨텍스트 보강 흐름을 평가 실행에 주입한다.
- `pipeline analyze` 흐름은 사용자 쿼리에서 의도를 분류하고 DAG 파이프라인을 구성해 모듈 실행 결과를 보고서로 연결한다.
- 벤치마크 및 스테이지 명령은 별도 서브플로우로 정의되어 평가 결과 비교와 이벤트 집계를 지원한다.

근거
- docs/guides/CLI_GUIDE.md
- docs/tutorials/02-basic-evaluation.md
- src/evalvault/domain/services/evaluator.py
- docs/tutorials/07-domain-memory.md
- docs/internal/reference/QUERY_BASED_ANALYSIS_PIPELINE.md

---

## 4) 설정/프로파일/환경 변수

요약
- 모델 프로필은 `config/models.yaml`에 정의되며 dev/prod/openai 같은 프로필별 LLM/임베딩 설정을 포함한다.
- `model_config.py`는 프로필 YAML을 탐색/로드해 Pydantic 모델로 검증하고 코드에서 재사용할 수 있게 한다.
- `Settings`는 `.env`를 기본으로 읽고 API 키, 엔드포인트, 트래커 설정 등 런타임 환경 변수를 관리한다.
- `EVALVAULT_PROFILE`이 지정되면 Settings에서 해당 프로필을 적용해 모델명을 덮어쓴다.
- CLI `--profile` 옵션은 프로필 선택을 런타임에 노출하며 문서에서도 동일한 사용법을 안내한다.
- `pyproject.toml`의 optional-dependencies는 docs/web/korean/analysis/phoenix 등 기능 단위 설치 구성을 제공한다.

근거
- config/models.yaml
- src/evalvault/config/model_config.py
- src/evalvault/config/settings.py
- docs/guides/CLI_GUIDE.md
- pyproject.toml

---

## 5) 확장 지점 (메트릭/리트리버/추적)

요약
- 커스텀 메트릭은 `src/evalvault/domain/metrics/`에 구현하고 `RagasEvaluator`의 매핑 테이블로 등록해 확장한다.
- 표준 Ragas 메트릭 외에도 보험 용어 정확도와 같은 도메인 특화 메트릭이 기본 포함된다.
- 커스텀 메트릭 추가 절차와 파일 구조는 튜토리얼에서 예제로 안내한다.
- 리트리버는 CLI 옵션으로 `bm25/dense/hybrid/graphrag`를 선택할 수 있으며, 한국어 BM25 등은 outbound NLP 어댑터로 구현되어 있다.
- 트래킹/관측은 `TrackerPort` 기반으로 외부 시스템과 연결되며 CLI에서 Phoenix/Langfuse/MLflow 연동 옵션을 제공한다.
- 포트 기반 설계를 따르므로 새로운 통합은 포트 인터페이스를 구현하는 어댑터 형태로 추가된다.

근거
- src/evalvault/domain/services/evaluator.py
- docs/tutorials/03-custom-metrics.md
- docs/guides/CLI_GUIDE.md
- src/evalvault/adapters/outbound/nlp/korean/bm25_retriever.py
- src/evalvault/ports/outbound/tracker_port.py

---

## 6) 테스트 구조 및 주요 픽스처

요약
- 테스트는 pytest 기준으로 `tests/` 아래에 수집되도록 설정되어 있으며 기본 테스트 루트를 명시한다.
- 통합 테스트는 데이터 로딩 플로우 등 주요 경로를 검증하며 CSV/JSON/XLSX 로더의 일관성을 확인한다.
- 단위 테스트는 CLI 명령과 옵션 동작을 확인하는 형태로 작성되어 있다.
- `tests/fixtures/`는 샘플 데이터셋(JSON/CSV/XLSX)과 벤치마크 ground truth, e2e 데이터셋을 제공한다.
- 픽스처 README에 예시 경로와 스키마가 정리되어 있어 테스트 데이터 재사용 방식이 명확하다.

근거
- pyproject.toml
- tests/integration/test_data_flow.py
- tests/unit/test_cli_init.py
- tests/fixtures/README.md

---

## 7) 검증 완료

다음 항목들은 2026-01-04 검증되어 설계 문서에 정책이 명시되었다:

- ✅ Query 기반 파이프라인 설계 문서의 의도/노드 정의가 `PipelineTemplateRegistry` 기본 템플릿과 일치함을 확인했다. 12개 `AnalysisIntent` 모두 문서와 코드가 동일하다.
- ✅ `PipelineOrchestrator`의 빈 파이프라인 정책이 설계 문서 섹션 3.5에 명시되었다. 빈 파이프라인은 허용되며, 점진적 구현과 테스트 용도로 사용된다.
- ✅ 모듈 미등록 시 `FAILED` 처리 동작이 설계 문서 섹션 3.5에 명시되었다. 실패 전파 방식(후속 노드 SKIPPED)과 에러 메시지 형식이 문서화되었다.

근거
- docs/internal/reference/QUERY_BASED_ANALYSIS_PIPELINE.md (섹션 3.5 파이프라인 정책)
- src/evalvault/domain/services/pipeline_template_registry.py
- src/evalvault/domain/services/pipeline_orchestrator.py
