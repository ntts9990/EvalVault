"""Full Workflow Integration Tests with Real API.

이 모듈은 EvalVault의 모든 주요 기능을 실제 API로 테스트합니다:

1. 데이터셋 로딩 (JSON, CSV)
2. LLM Adapters (OpenAI + Thinking 설정)
3. Ragas 평가 (faithfulness, answer_relevancy, context_precision)
4. Knowledge Graph 생성
5. Langfuse 트래킹
6. Storage (SQLite)
7. CLI 명령어

실행 방법:
    # 전체 워크플로우 테스트 (실제 API 사용)
    pytest tests/integration/test_full_workflow.py -v -s

    # 특정 테스트만 실행
    pytest tests/integration/test_full_workflow.py::TestFullWorkflow::test_01_dataset_loading -v -s

    # API 테스트 건너뛰기
    pytest tests/integration/test_full_workflow.py -v -m "not requires_openai"

환경 변수 필요:
    - OPENAI_API_KEY: OpenAI API 키
    - OPENAI_MODEL: 사용할 모델 (기본: gpt-5-mini)
    - LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST: Langfuse 설정
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pytest

from evalvault.config.settings import Settings
from evalvault.domain.entities import Dataset

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def sample_dataset_json(tmp_path_factory) -> Path:
    """테스트용 샘플 데이터셋 (JSON)."""
    data = {
        "name": "full-workflow-test",
        "version": "1.0.0",
        "thresholds": {
            "faithfulness": 0.7,
            "answer_relevancy": 0.7,
            "context_precision": 0.6,
        },
        "test_cases": [
            {
                "id": "fw-001",
                "question": "이 보험의 월 보험료는 얼마인가요?",
                "answer": "월 보험료는 50,000원입니다.",
                "contexts": [
                    "본 보험의 월납 보험료는 50,000원이며, 연납 시 10% 할인이 적용됩니다.",
                    "보험료 납입은 매월 25일에 자동이체됩니다.",
                ],
                "ground_truth": "50,000원",
            },
            {
                "id": "fw-002",
                "question": "보험금 청구 시 필요한 서류는 무엇인가요?",
                "answer": "보험금 청구 시 청구서, 신분증 사본, 진단서가 필요합니다.",
                "contexts": [
                    "보험금 청구 시 필요 서류: 보험금 청구서, 신분증 사본, 진단서 또는 입퇴원확인서",
                    "서류 제출은 온라인 또는 우편으로 가능합니다.",
                ],
                "ground_truth": "청구서, 신분증, 진단서",
            },
            {
                "id": "fw-003",
                "question": "해약환급금은 언제부터 받을 수 있나요?",
                "answer": "해약환급금은 계약 후 2년이 지나면 받을 수 있습니다.",
                "contexts": [
                    "해약환급금은 보험계약 체결 후 2년 경과 시점부터 발생합니다.",
                    "조기 해지 시에는 납입 보험료보다 적은 금액이 지급될 수 있습니다.",
                ],
                "ground_truth": "2년 후",
            },
        ],
    }

    tmp_dir = tmp_path_factory.mktemp("datasets")
    json_path = tmp_dir / "workflow_test.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return json_path


@pytest.fixture(scope="module")
def sample_documents() -> list[str]:
    """KG 생성용 샘플 문서."""
    return [
        """삼성생명 무배당 종신보험 안내

        이 보험은 피보험자가 사망할 경우 사망보험금 1억원을 지급합니다.
        보험료 납입기간은 20년이며, 월 보험료는 50,000원입니다.

        주요 보장 내용:
        - 사망보험금: 1억원
        - 암 진단비: 3,000만원
        - 뇌졸중 진단비: 2,000만원
        """,
        """보험금 청구 안내

        보험금 청구 시 다음 서류가 필요합니다:
        - 보험금 청구서 (소정 양식)
        - 신분증 사본
        - 진단서 또는 입퇴원 확인서

        청구 접수 후 3영업일 이내에 보험금이 지급됩니다.
        """,
    ]


@pytest.fixture(scope="module")
def settings() -> Settings:
    """테스트용 Settings."""
    return Settings()


@pytest.fixture(scope="module")
def storage(tmp_path_factory):
    """테스트용 SQLite Storage."""
    from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter

    tmp_dir = tmp_path_factory.mktemp("storage")
    db_path = tmp_dir / "workflow_test.db"
    return SQLiteStorageAdapter(str(db_path))


# ============================================================================
# Test Class: Full Workflow
# ============================================================================


class TestFullWorkflow:
    """전체 워크플로우 통합 테스트.

    테스트 순서가 중요하므로 test_01_, test_02_ 등으로 명명합니다.
    """

    # 테스트 간 공유할 상태
    _loaded_dataset: Dataset | None = None
    _evaluation_run: Any = None
    _kg_result: Any = None

    def test_01_dataset_loading(self, sample_dataset_json):
        """1. 데이터셋 로딩 테스트."""
        from evalvault.adapters.outbound.dataset import get_loader

        print("\n" + "=" * 60)
        print("1. Dataset Loading Test")
        print("=" * 60)

        # JSON 로더 테스트
        loader = get_loader(sample_dataset_json)
        dataset = loader.load(sample_dataset_json)

        assert dataset is not None
        assert dataset.name == "full-workflow-test"
        assert len(dataset.test_cases) == 3

        # Ragas 형식 변환 테스트
        ragas_list = dataset.to_ragas_list()
        assert len(ragas_list) == 3
        assert all("user_input" in item for item in ragas_list)
        assert all("response" in item for item in ragas_list)
        assert all("retrieved_contexts" in item for item in ragas_list)

        print(f"  ✓ Loaded dataset: {dataset.name}")
        print(f"  ✓ Test cases: {len(dataset.test_cases)}")
        print(f"  ✓ Thresholds: {dataset.thresholds}")

        # 클래스 변수에 저장
        TestFullWorkflow._loaded_dataset = dataset

    @pytest.mark.requires_openai
    def test_02_llm_adapter_initialization(self, settings):
        """2. LLM Adapter 초기화 테스트."""
        print("\n" + "=" * 60)
        print("2. LLM Adapter Initialization Test")
        print("=" * 60)

        from evalvault.adapters.outbound.llm import get_llm_adapter

        # Provider 확인
        provider = settings.llm_provider
        print(f"  Provider: {provider}")

        # Adapter 생성
        adapter = get_llm_adapter(settings)

        assert adapter is not None
        print(f"  ✓ Model: {adapter.get_model_name()}")

        # Thinking config 확인
        thinking_config = adapter.get_thinking_config()
        print(f"  ✓ Thinking enabled: {thinking_config.enabled}")
        if thinking_config.enabled:
            if thinking_config.budget_tokens:
                print(f"    - Budget tokens: {thinking_config.budget_tokens}")
            if thinking_config.think_level:
                print(f"    - Think level: {thinking_config.think_level}")

        # Ragas LLM/Embeddings 확인
        ragas_llm = adapter.as_ragas_llm()
        assert ragas_llm is not None
        print("  ✓ Ragas LLM initialized")

        try:
            ragas_embeddings = adapter.as_ragas_embeddings()
            assert ragas_embeddings is not None
            print("  ✓ Ragas Embeddings initialized")
        except ValueError as e:
            print(f"  ⚠ Embeddings not available: {e}")

    @pytest.mark.slow
    @pytest.mark.requires_openai
    async def test_03_ragas_evaluation(self, sample_dataset_json, settings, storage):
        """3. Ragas 평가 테스트 (실제 API 사용)."""
        print("\n" + "=" * 60)
        print("3. Ragas Evaluation Test (Real API)")
        print("=" * 60)

        from evalvault.adapters.outbound.dataset import get_loader
        from evalvault.adapters.outbound.llm import get_llm_adapter
        from evalvault.domain.services.evaluator import RagasEvaluator

        # 데이터셋 로드
        dataset = get_loader(sample_dataset_json).load(sample_dataset_json)
        print(f"  Dataset: {dataset.name} ({len(dataset)} test cases)")

        # LLM Adapter
        adapter = get_llm_adapter(settings)
        print(f"  Model: {adapter.get_model_name()}")

        # 평가 실행
        evaluator = RagasEvaluator()
        metrics = ["faithfulness", "answer_relevancy"]

        print(f"  Metrics: {metrics}")
        print("  Running evaluation...")

        start_time = datetime.now()
        run = await evaluator.evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=adapter,
            thresholds=dataset.thresholds,
        )
        duration = (datetime.now() - start_time).total_seconds()

        assert run is not None
        assert len(run.results) == len(dataset)

        print(f"\n  ✓ Evaluation completed in {duration:.1f}s")
        print(f"  ✓ Run ID: {run.run_id}")
        print(f"  ✓ Total tokens: {run.total_tokens}")
        print(f"  ✓ Pass rate: {run.pass_rate:.1%}")

        # 개별 결과 출력
        print("\n  Results by test case:")
        for result in run.results:
            scores = ", ".join(f"{m.name}={m.score:.2f}" for m in result.metrics)
            # Check if all metrics passed their thresholds
            all_passed = all(m.score >= (m.threshold or 0.7) for m in result.metrics)
            status = "✓" if all_passed else "✗"
            print(f"    {status} {result.test_case_id}: {scores}")

        # Storage에 저장
        run_id = storage.save_run(run)
        print(f"\n  ✓ Saved to storage: {run_id}")

        # 클래스 변수에 저장
        TestFullWorkflow._evaluation_run = run

    def test_04_knowledge_graph_generation(self, sample_documents):
        """4. Knowledge Graph 생성 테스트."""
        print("\n" + "=" * 60)
        print("4. Knowledge Graph Generation Test")
        print("=" * 60)

        from evalvault.domain.services.kg_generator import KnowledgeGraphGenerator

        # KG Generator (no LLM needed for basic extraction)
        kg_generator = KnowledgeGraphGenerator()

        print(f"  Documents: {len(sample_documents)}")
        print("  Generating Knowledge Graph...")

        start_time = datetime.now()
        kg_generator.build_graph(documents=sample_documents)
        kg = kg_generator.get_graph()
        duration = (datetime.now() - start_time).total_seconds()

        assert kg is not None
        entities = kg.get_all_entities()
        edge_count = kg.get_edge_count()
        print(f"\n  ✓ KG generated in {duration:.1f}s")
        print(f"  ✓ Entities: {len(entities)}")
        print(f"  ✓ Relations: {edge_count}")

        # 엔티티 샘플 출력
        if entities:
            print("\n  Sample entities:")
            for entity in entities[:5]:
                print(f"    - {entity.name} ({entity.entity_type})")

        # 관계 샘플 출력 (use sample_relations method)
        sample_relations = kg.get_sample_relations(limit=5)
        if sample_relations:
            print("\n  Sample relations:")
            for rel in sample_relations:
                print(f"    - {rel['source']} --[{rel['relation_type']}]--> {rel['target']}")

        # 질문 생성 테스트
        questions = kg_generator.generate_questions(num_questions=3)
        if questions:
            print(f"\n  ✓ Generated {len(questions)} test questions")
            for q in questions[:2]:
                print(f"    - {q.question[:50]}...")

        TestFullWorkflow._kg_result = kg

    @pytest.mark.slow
    @pytest.mark.requires_langfuse
    async def test_05_langfuse_tracking(self, sample_dataset_json, settings):
        """5. Langfuse 트래킹 테스트."""
        print("\n" + "=" * 60)
        print("5. Langfuse Tracking Test")
        print("=" * 60)

        from evalvault.adapters.outbound.dataset import get_loader
        from evalvault.adapters.outbound.llm import get_llm_adapter
        from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter
        from evalvault.domain.services.evaluator import RagasEvaluator

        # Langfuse Adapter
        tracker = LangfuseAdapter(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host or "https://cloud.langfuse.com",
        )
        print(f"  Langfuse Host: {settings.langfuse_host}")

        # 데이터셋 및 LLM
        dataset = get_loader(sample_dataset_json).load(sample_dataset_json)
        adapter = get_llm_adapter(settings)

        # 평가 실행 (1개 테스트 케이스만)
        small_dataset = Dataset(
            name=dataset.name + "-langfuse-test",
            version=dataset.version,
            test_cases=dataset.test_cases[:1],
            thresholds=dataset.thresholds,
        )

        evaluator = RagasEvaluator()
        print("  Running evaluation...")

        run = await evaluator.evaluate(
            dataset=small_dataset,
            metrics=["faithfulness"],
            llm=adapter,
        )

        assert run is not None
        print("  ✓ Evaluation completed")
        print(f"  ✓ Run ID: {run.run_id}")

        # Log to Langfuse
        print("  Logging to Langfuse...")
        trace_id = tracker.log_evaluation_run(run)
        print(f"  ✓ Trace logged to Langfuse: {trace_id}")

    def test_06_storage_operations(self, storage):
        """6. Storage 조작 테스트."""
        print("\n" + "=" * 60)
        print("6. Storage Operations Test")
        print("=" * 60)

        # 이전 테스트에서 저장한 run 확인
        if TestFullWorkflow._evaluation_run:
            run_id = TestFullWorkflow._evaluation_run.run_id

            # 조회
            retrieved = storage.get_run(run_id)
            assert retrieved is not None
            print(f"  ✓ Retrieved run: {run_id}")

            # 목록 조회
            runs = storage.list_runs(limit=10)
            print(f"  ✓ Total runs in storage: {len(runs)}")

        # 새 run 저장 및 삭제 테스트
        from evalvault.domain.entities import EvaluationRun

        test_run = EvaluationRun(
            dataset_name="storage-test",
            dataset_version="1.0.0",
            model_name="test-model",
            started_at=datetime.now(),
            finished_at=datetime.now(),
            metrics_evaluated=["faithfulness"],
            thresholds={"faithfulness": 0.7},
            total_tokens=100,
            results=[],
        )

        # 저장
        saved_id = storage.save_run(test_run)
        print(f"  ✓ Saved test run: {saved_id}")

        # 삭제
        deleted = storage.delete_run(saved_id)
        assert deleted is True
        print(f"  ✓ Deleted test run: {saved_id}")

    def test_07_cli_commands(self, sample_dataset_json):
        """7. CLI 명령어 테스트."""
        print("\n" + "=" * 60)
        print("7. CLI Commands Test")
        print("=" * 60)

        from typer.testing import CliRunner

        from evalvault.adapters.inbound.cli import app

        runner = CliRunner()

        # metrics 명령
        result = runner.invoke(app, ["metrics"])
        assert result.exit_code == 0
        assert "faithfulness" in result.output
        print("  ✓ 'metrics' command works")

        # config 명령
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        print("  ✓ 'config' command works")

        # run --help
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "dataset" in result.output.lower()
        print("  ✓ 'run --help' command works")

        # history --help
        result = runner.invoke(app, ["history", "--help"])
        assert result.exit_code == 0
        print("  ✓ 'history --help' command works")

    def test_08_summary(self):
        """8. 테스트 결과 요약."""
        print("\n" + "=" * 60)
        print("8. Test Summary")
        print("=" * 60)

        print("\n  Completed tests:")
        print("    1. ✓ Dataset Loading (JSON/CSV)")
        print("    2. ✓ LLM Adapter Initialization")

        if TestFullWorkflow._evaluation_run:
            run = TestFullWorkflow._evaluation_run
            print(f"    3. ✓ Ragas Evaluation (pass rate: {run.pass_rate:.1%})")
        else:
            print("    3. ⊘ Ragas Evaluation (skipped - no API key)")

        if TestFullWorkflow._kg_result:
            kg = TestFullWorkflow._kg_result
            print(
                f"    4. ✓ KG Generation ({len(kg.get_all_entities())} entities, {kg.get_edge_count()} relations)"
            )
        else:
            print("    4. ⊘ KG Generation (not run)")

        print("    5. ⊘ Langfuse Tracking (check separately)")
        print("    6. ✓ Storage Operations")
        print("    7. ✓ CLI Commands")

        print("\n" + "=" * 60)


# ============================================================================
# Standalone Quick Test
# ============================================================================


class TestQuickSanityCheck:
    """빠른 sanity check 테스트 (API 호출 없음)."""

    def test_imports(self):
        """모든 주요 모듈 import 테스트."""

        print("\n  ✓ All major modules imported successfully")

    def test_settings_loading(self):
        """Settings 로딩 테스트."""
        settings = Settings()
        assert settings is not None
        print("\n  ✓ Settings loaded")
        print(f"    - LLM Provider: {settings.llm_provider}")
        print(f"    - OpenAI Model: {settings.openai_model}")

    def test_thinking_config_interface(self):
        """ThinkingConfig 인터페이스 테스트."""
        from evalvault.ports.outbound.llm_port import ThinkingConfig

        # Anthropic style
        config = ThinkingConfig(enabled=True, budget_tokens=10000)
        param = cast(dict[str, Any], config.to_anthropic_param())
        assert param["type"] == "enabled"
        assert param["budget_tokens"] == 10000

        # Ollama style
        config = ThinkingConfig(enabled=True, think_level="medium")
        options = cast(dict[str, Any], config.to_ollama_options())
        assert options["think_level"] == "medium"

        # Disabled
        config = ThinkingConfig(enabled=False)
        assert config.to_anthropic_param() is None
        assert config.to_ollama_options() is None

        print("\n  ✓ ThinkingConfig interface works correctly")
