# Test Coverage Improvement Plan

최근 커버리지 리포트(총 53%)를 바탕으로, 우선순위에 따라 테스트를 확장하여 핵심 CLI·데이터
로드·지식 그래프·외부 어댑터 경로를 검증하기 위한 계획을 정리했습니다.

## 1. 커버리지 현황 요약

- **CLI (src/evalvault/adapters/inbound/cli.py)**: 다수의 Typer 커맨드가 0%로, `_save_to_db`,
  `history`, `generate`, `experiment_*`, `run`, `kg_stats` 등 사용자 인터페이스의 신뢰도가
  낮음.
- **Dataset Loaders**: `BaseDatasetLoader`, `CSV/JSON/Excel` 구체 구현이 0~82%로 산재하며,
  경로 정규화·컨텍스트 파싱·엔코딩 폴백 등이 미검증.
- **Knowledge Graph & KG Generator**: `_generate_*` 계열과 `KnowledgeGraph` 메서드가
  55–95%로 편차가 큼. 멀티홉/비교 질문 로직과 relation augmentation 경로 필요.
- **Langfuse/Storage/LLM 어댑터**: LangfuseAdapter, SQLite/PostgreSQL adapter, Anthropic /
  OpenAI 어댑터의 API 래핑 함수 다수가 0%. 외부 의존성을 모킹해 검증해야 함.
- **기타**: `LanguageDetector`, `settings.apply_profile`, `ExperimentManager` 등도 80% 미만.

## 2. 목표

1. **단기 (Sprint 1)**: 사용자 노출이 큰 CLI와 Dataset Loader 커맨드를 80%+로 끌어올림.
2. **중기 (Sprint 2)**: KnowledgeGraphGenerator, ExperimentManager, RagasEvaluator 주요 경로
   85% 이상 확보.
3. **장기 (Sprint 3)**: Langfuse/Storage/LLM 어댑터, PromptTemplate, TokenUsage 등
   인프라 모듈에 계약 테스트 추가하여 전체 커버리지를 75% 이상까지 확장.

## 3. 영역별 실행 계획

### 3.1 CLI 커맨드 (Typer)

- **전략**: `typer.testing.CliRunner`를 사용해 `run`, `kg_stats`, `compare`, `experiment_*`,
  `generate` 등을 시나리오별로 호출.
- **필요한 준비**:
  - `tests/fixtures/cli/`에 최소 데이터셋/모델 설정/랭퓨즈 모의 응답 추가.
  - `_save_to_db`, `_save_results`, `_log_to_langfuse` 등 내부 함수는 patching으로 단위 테스트.
- **완료 조건**: CLI 파일 전체 커버리지를 80% 이상으로 상향.

### 3.2 Dataset Loaders

- **전략**: `tests/unit/adapters/dataset/test_loaders.py` (신규)에서
  `BaseDatasetLoader._normalize_path`, `_parse_contexts`, `_validate_file_exists`를 개별 검증.
- **시나리오**:
  - CSV/JSON/Excel 정상 로딩, 존재하지 않는 경로, 잘못된 인코딩.
  - Excel 엔진 선택 로직 (`_get_excel_engine`)을 `pytest.mark.parametrize`로 분기 검증.
- **완료 조건**: 각 loader 클래스 85% 이상, `BaseDatasetLoader` 서브루틴 80% 이상.

### 3.3 Knowledge Graph & Generator

- **전략**: `tests/unit/domain/kg/`에 그래프 빌드/경로 탐색/질문 생성 테스트 추가.
  - `build_graph`, `_find_path`, `_generate_simple/ multi_hop / comparison_question`,
    `_maybe_augment_relations`, `generate_questions_by_type` 등.
  - `LLMRelationAugmenter`는 `RelationAugmenterPort` 모킹으로 독립 검증.
- **완료 조건**: `kg_generator.py` 주요 퍼블릭 메서드 90% 이상, `KnowledgeGraph` 보조
  메서드는 80% 이상.

### 3.4 Langfuse / Storage / LLM Adapters

- **전략**:
  - LangfuseAdapter: `langfuse` SDK 객체를 `MagicMock` 처리해 `start_trace`, `add_span`,
    `save_artifact`, `log_score` 등 호출 인자 검증.
  - Storage adapters: `sqlite3`/`psycopg` 커넥션을 모킹해 `save_experiment`, `update_*`,
    `list_experiments` 호출이 올바른 SQL을 실행하는지 확인.
  - LLM adapters (OpenAI/Anthropic): 토큰 트래킹 객체를 모킹하고 `as_ragas_llm`,
    `get_thinking_config` 등 단순 getter를 smoke 테스트.
- **완료 조건**: 각 어댑터 모듈 70% 이상, 특히 현재 0% 영역 제거.

### 3.5 Config, Utils, Metrics

- `config/settings.apply_profile`, `config/model_config.load_model_config`:
  - `.env`/`config/models.yaml` 샘플을 fixture로 생성하여 프로필 적용 경로를 테스트.
- `LanguageDetector`:
  - 다양한 텍스트 입력으로 `detect`와 `detect_with_confidence`의 분기 검증.
- `InsuranceTermAccuracy`, `EntityExtractor`, `Dataset.get_threshold`: 간단한 단위 테스트 추가.

## 4. 이터레이션 타임라인

| Sprint | 범위 | 담당 제안 | 산출물 |
|--------|------|-----------|--------|
| 1주차 | CLI + Dataset Loaders | Core maintainers + QA | `tests/unit/adapters/test_cli.py`, `tests/unit/adapters/test_dataset_loaders.py` |
| 2주차 | KG Generator + Experiment Manager | Domain 팀 | `tests/unit/domain/kg/test_generator.py`, `tests/unit/domain/test_experiment_manager.py` |
| 3주차 | Langfuse/Storage/LLM + Config/Utils | Infra 팀 | `tests/unit/adapters/test_langfuse.py`, `tests/unit/adapters/test_sqlite.py`, `tests/unit/config/test_settings.py` 등 |

각 스프린트 종료 시 `pytest --cov` 리포트를 공유하고, 0% 함수가 남아 있으면 백로그에 이슈를
등록합니다.

## 5. 추적 방법

- `reports/` 디렉터리에 스프린트별 `coverage-YYYYMMDD.md`를 저장해 커버리지 추이를
  시각화합니다.
- GitHub Projects 또는 Issue 템플릿을 사용해 각 테스트 작업을 태그(`coverage:cli`,
  `coverage:kg` 등)로 관리합니다.

이 계획에 따라 테스트를 보강하면 사용자 명령과 핵심 평가 로직의 회귀 리스크를 줄이고,
추후 리팩터링 시 안정성을 확보할 수 있습니다.
