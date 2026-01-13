"""End-to-End test scenarios for EvalVault.

This module provides comprehensive E2E tests covering:
1. Multi-format dataset loading (.json, .csv, .xlsx)
2. Format consistency verification
3. Full evaluation pipeline
4. Storage integration
5. CLI integration
6. Edge cases and error handling

Run with:
    pytest tests/integration/test_e2e_scenarios.py -v

For tests requiring API keys:
    pytest tests/integration/test_e2e_scenarios.py -v -m requires_openai
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from evalvault.adapters.outbound.dataset import get_loader
from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter
from evalvault.domain.entities import (
    Dataset,
    EvaluationRun,
    MetricScore,
    TestCaseResult,
)
from evalvault.domain.services.evaluator import RagasEvaluator


class TestE2EFixturePaths:
    """E2E 테스트 픽스처 경로 관리."""

    @pytest.fixture
    def e2e_fixtures_path(self) -> Path:
        """E2E 테스트 픽스처 경로."""
        return Path(__file__).parent.parent / "fixtures" / "e2e"

    @pytest.fixture
    def korean_json(self, e2e_fixtures_path) -> Path:
        return e2e_fixtures_path / "insurance_qa_korean.json"

    @pytest.fixture
    def korean_csv(self, e2e_fixtures_path) -> Path:
        return e2e_fixtures_path / "insurance_qa_korean.csv"

    @pytest.fixture
    def korean_xlsx(self, e2e_fixtures_path) -> Path:
        return e2e_fixtures_path / "insurance_qa_korean.xlsx"

    @pytest.fixture
    def english_json(self, e2e_fixtures_path) -> Path:
        return e2e_fixtures_path / "insurance_qa_english.json"

    @pytest.fixture
    def english_csv(self, e2e_fixtures_path) -> Path:
        return e2e_fixtures_path / "insurance_qa_english.csv"

    @pytest.fixture
    def english_xlsx(self, e2e_fixtures_path) -> Path:
        return e2e_fixtures_path / "insurance_qa_english.xlsx"

    @pytest.fixture
    def edge_cases_json(self, e2e_fixtures_path) -> Path:
        return e2e_fixtures_path / "edge_cases.json"

    @pytest.fixture
    def edge_cases_xlsx(self, e2e_fixtures_path) -> Path:
        return e2e_fixtures_path / "edge_cases.xlsx"


class TestFormatConsistency(TestE2EFixturePaths):
    """모든 형식이 동일한 데이터를 로드하는지 검증."""

    def test_korean_all_formats_load_same_data(self, korean_json, korean_csv, korean_xlsx):
        """Korean 데이터셋이 모든 형식에서 동일하게 로드되는지 검증."""
        # Load all formats
        json_dataset = get_loader(korean_json).load(korean_json)
        csv_dataset = get_loader(korean_csv).load(korean_csv)
        xlsx_dataset = get_loader(korean_xlsx).load(korean_xlsx)

        # Verify same number of test cases
        assert len(json_dataset) == len(csv_dataset) == len(xlsx_dataset) == 5

        # Verify same test case IDs
        json_ids = {tc.id for tc in json_dataset}
        csv_ids = {tc.id for tc in csv_dataset}
        xlsx_ids = {tc.id for tc in xlsx_dataset}
        assert json_ids == csv_ids == xlsx_ids

        # Verify content consistency
        for tc_id in json_ids:
            json_tc = next(tc for tc in json_dataset if tc.id == tc_id)
            csv_tc = next(tc for tc in csv_dataset if tc.id == tc_id)
            xlsx_tc = next(tc for tc in xlsx_dataset if tc.id == tc_id)

            assert json_tc.question == csv_tc.question == xlsx_tc.question
            assert json_tc.answer == csv_tc.answer == xlsx_tc.answer
            assert json_tc.ground_truth == csv_tc.ground_truth == xlsx_tc.ground_truth

    def test_english_all_formats_load_same_data(self, english_json, english_csv, english_xlsx):
        """English 데이터셋이 모든 형식에서 동일하게 로드되는지 검증."""
        json_dataset = get_loader(english_json).load(english_json)
        csv_dataset = get_loader(english_csv).load(english_csv)
        xlsx_dataset = get_loader(english_xlsx).load(english_xlsx)

        assert len(json_dataset) == len(csv_dataset) == len(xlsx_dataset) == 5

        json_ids = {tc.id for tc in json_dataset}
        csv_ids = {tc.id for tc in csv_dataset}
        xlsx_ids = {tc.id for tc in xlsx_dataset}
        assert json_ids == csv_ids == xlsx_ids

    def test_ragas_format_consistency_across_formats(self, korean_json, korean_csv, korean_xlsx):
        """Ragas 형식 변환이 모든 형식에서 일관되는지 검증."""
        json_dataset = get_loader(korean_json).load(korean_json)
        csv_dataset = get_loader(korean_csv).load(korean_csv)
        xlsx_dataset = get_loader(korean_xlsx).load(korean_xlsx)

        json_ragas = json_dataset.to_ragas_list()
        csv_ragas = csv_dataset.to_ragas_list()
        xlsx_ragas = xlsx_dataset.to_ragas_list()

        assert len(json_ragas) == len(csv_ragas) == len(xlsx_ragas)

        # Verify Ragas field names
        for ragas_data in [json_ragas, csv_ragas, xlsx_ragas]:
            for item in ragas_data:
                assert "user_input" in item
                assert "response" in item
                assert "retrieved_contexts" in item


class TestEdgeCasesE2E(TestE2EFixturePaths):
    """엣지 케이스 E2E 테스트."""

    def test_special_characters_in_dataset(self, edge_cases_json):
        """특수 문자가 포함된 데이터셋 로드 테스트."""
        dataset = get_loader(edge_cases_json).load(edge_cases_json)

        # Find the special characters test case
        special_tc = next(tc for tc in dataset if tc.id == "edge-001")
        assert "&" in special_tc.question
        assert "<" in special_tc.question
        assert '"' in special_tc.question

    def test_minimal_context(self, edge_cases_json):
        """최소 컨텍스트 테스트 케이스."""
        dataset = get_loader(edge_cases_json).load(edge_cases_json)

        minimal_tc = next(tc for tc in dataset if tc.id == "edge-002")
        assert len(minimal_tc.contexts) == 1
        assert minimal_tc.contexts[0] == "Minimal context."

    def test_unicode_characters(self, edge_cases_json):
        """유니코드 문자 처리 테스트."""
        dataset = get_loader(edge_cases_json).load(edge_cases_json)

        unicode_tc = next(tc for tc in dataset if tc.id == "edge-003")
        assert "Unicode" in unicode_tc.question

    def test_long_context_passages(self, edge_cases_json):
        """긴 컨텍스트 처리 테스트."""
        dataset = get_loader(edge_cases_json).load(edge_cases_json)

        long_tc = next(tc for tc in dataset if tc.id == "edge-004")
        # Verify long context is preserved
        total_context_len = sum(len(c) for c in long_tc.contexts)
        assert total_context_len > 500

    def test_null_ground_truth(self, edge_cases_json):
        """ground_truth가 null인 케이스 테스트."""
        dataset = get_loader(edge_cases_json).load(edge_cases_json)

        null_gt_tc = next(tc for tc in dataset if tc.id == "edge-006")
        assert null_gt_tc.ground_truth is None

    def test_multiple_contexts(self, edge_cases_json):
        """다중 컨텍스트 처리 테스트."""
        dataset = get_loader(edge_cases_json).load(edge_cases_json)

        multi_tc = next(tc for tc in dataset if tc.id == "edge-007")
        assert len(multi_tc.contexts) == 8


class TestEvaluationPipelineE2E(TestE2EFixturePaths):
    """평가 파이프라인 E2E 테스트."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for testing without API calls."""
        mock = MagicMock()
        mock.get_model_name.return_value = "mock-model"

        # Mock Ragas LLM
        mock_ragas_llm = MagicMock()
        mock.as_ragas_llm.return_value = mock_ragas_llm

        # Mock Ragas embeddings
        mock_embeddings = MagicMock()
        mock.as_ragas_embeddings.return_value = mock_embeddings

        # Token tracking
        mock.reset_token_usage = MagicMock()
        mock.get_and_reset_token_usage.return_value = (100, 50, 150)

        return mock

    @pytest.fixture
    def sample_dataset(self, korean_json) -> Dataset:
        """샘플 데이터셋 로드."""
        return get_loader(korean_json).load(korean_json)

    async def test_evaluation_run_structure(self, sample_dataset, mock_llm):
        """평가 결과 구조 검증."""
        evaluator = RagasEvaluator()

        # Mock the Ragas metric scores
        with patch.object(evaluator, "_evaluate_with_ragas") as mock_eval:
            # Return mock scores for each test case
            mock_results = {}
            for tc in sample_dataset.test_cases:
                from evalvault.domain.services.evaluator import TestCaseEvalResult

                mock_results[tc.id] = TestCaseEvalResult(
                    scores={"faithfulness": 0.85},
                    tokens_used=150,
                    started_at=datetime.now(),
                    finished_at=datetime.now() + timedelta(seconds=1),
                    latency_ms=1000,
                )
            mock_eval.return_value = (mock_results, {}, {})

            run = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
                thresholds={"faithfulness": 0.7},
            )

        # Verify run structure
        assert isinstance(run, EvaluationRun)
        assert run.dataset_name == sample_dataset.name
        assert len(run.results) == len(sample_dataset)
        assert run.metrics_evaluated == ["faithfulness"]

    async def test_evaluation_with_multiple_metrics(self, sample_dataset, mock_llm):
        """다중 메트릭 평가 테스트."""
        evaluator = RagasEvaluator()

        with patch.object(evaluator, "_evaluate_with_ragas") as mock_eval:
            mock_results = {}
            for tc in sample_dataset.test_cases:
                from evalvault.domain.services.evaluator import TestCaseEvalResult

                mock_results[tc.id] = TestCaseEvalResult(
                    scores={
                        "faithfulness": 0.9,
                        "answer_relevancy": 0.85,
                    },
                    tokens_used=200,
                    started_at=datetime.now(),
                    finished_at=datetime.now() + timedelta(seconds=2),
                    latency_ms=2000,
                )
            mock_eval.return_value = (mock_results, {}, {})

            run = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness", "answer_relevancy"],
                llm=mock_llm,
            )

        assert len(run.metrics_evaluated) == 2
        for result in run.results:
            assert len(result.metrics) == 2

    async def test_evaluation_timestamps(self, sample_dataset, mock_llm):
        """평가 시작/종료 시간 검증."""
        evaluator = RagasEvaluator()

        with patch.object(evaluator, "_evaluate_with_ragas") as mock_eval:
            mock_results = {}
            for tc in sample_dataset.test_cases:
                from evalvault.domain.services.evaluator import TestCaseEvalResult

                mock_results[tc.id] = TestCaseEvalResult(
                    scores={"faithfulness": 0.8},
                    tokens_used=100,
                    started_at=datetime.now(),
                    finished_at=datetime.now() + timedelta(seconds=1),
                    latency_ms=1000,
                )
            mock_eval.return_value = (mock_results, {}, {})

            before = datetime.now()
            run = await evaluator.evaluate(
                dataset=sample_dataset,
                metrics=["faithfulness"],
                llm=mock_llm,
            )
            after = datetime.now()

        assert run.started_at is not None
        assert run.finished_at is not None
        started_at = cast(datetime, run.started_at)
        finished_at = cast(datetime, run.finished_at)
        assert started_at >= before
        assert finished_at <= after
        duration = run.duration_seconds
        assert duration is not None
        assert duration >= 0


class TestStorageIntegrationE2E(TestE2EFixturePaths):
    """저장소 통합 E2E 테스트."""

    @pytest.fixture
    def storage(self, tmp_path):
        """임시 SQLite 저장소."""
        db_path = tmp_path / "test_e2e.db"
        return SQLiteStorageAdapter(str(db_path))

    @pytest.fixture
    def sample_run(self, korean_json) -> EvaluationRun:
        """샘플 평가 결과."""
        dataset = get_loader(korean_json).load(korean_json)
        started_at = datetime.now()
        finished_at = started_at + timedelta(seconds=30)

        results = []
        for i, tc in enumerate(dataset.test_cases):
            tc_started = started_at + timedelta(seconds=i * 5)
            tc_finished = tc_started + timedelta(seconds=4)
            results.append(
                TestCaseResult(
                    test_case_id=tc.id,
                    metrics=[
                        MetricScore(name="faithfulness", score=0.85 + i * 0.02, threshold=0.7),
                        MetricScore(name="answer_relevancy", score=0.80 + i * 0.03, threshold=0.7),
                    ],
                    tokens_used=150 + i * 10,
                    latency_ms=4000 + i * 100,
                    started_at=tc_started,
                    finished_at=tc_finished,
                    question=tc.question,
                    answer=tc.answer,
                    contexts=tc.contexts,
                    ground_truth=tc.ground_truth,
                )
            )

        return EvaluationRun(
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            model_name="gpt-5-nano",
            started_at=started_at,
            finished_at=finished_at,
            metrics_evaluated=["faithfulness", "answer_relevancy"],
            thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
            total_tokens=sum(r.tokens_used for r in results),
            results=results,
        )

    def test_save_and_retrieve_run(self, storage, sample_run):
        """저장 및 조회 테스트."""
        # Save
        run_id = storage.save_run(sample_run)
        assert run_id == sample_run.run_id

        # Retrieve
        retrieved = storage.get_run(run_id)
        assert retrieved.run_id == run_id
        assert retrieved.dataset_name == sample_run.dataset_name
        assert len(retrieved.results) == len(sample_run.results)

    def test_list_runs_with_filters(self, storage, sample_run):
        """필터링된 목록 조회 테스트."""
        storage.save_run(sample_run)

        # List all
        runs = storage.list_runs()
        assert len(runs) == 1

        # Filter by dataset
        runs = storage.list_runs(dataset_name=sample_run.dataset_name)
        assert len(runs) == 1

        # Filter by model
        runs = storage.list_runs(model_name="gpt-5-nano")
        assert len(runs) == 1

        # Filter with non-matching criteria
        runs = storage.list_runs(dataset_name="nonexistent")
        assert len(runs) == 0

    def test_delete_run(self, storage, sample_run):
        """삭제 테스트."""
        run_id = storage.save_run(sample_run)

        # Verify exists
        assert storage.get_run(run_id) is not None

        # Delete
        result = storage.delete_run(run_id)
        assert result is True

        # Verify deleted
        with pytest.raises(KeyError):
            storage.get_run(run_id)

    def test_multiple_runs_same_dataset(self, storage, korean_json):
        """동일 데이터셋의 다중 실행 저장 테스트."""
        dataset = get_loader(korean_json).load(korean_json)

        # Create multiple runs
        run_ids = []
        for i in range(3):
            started_at = datetime.now()
            run = EvaluationRun(
                dataset_name=dataset.name,
                dataset_version=dataset.version,
                model_name=f"model-{i}",
                started_at=started_at,
                finished_at=started_at + timedelta(seconds=10),
                metrics_evaluated=["faithfulness"],
                thresholds={"faithfulness": 0.7},
                total_tokens=100 * (i + 1),
                results=[],
            )
            run_ids.append(storage.save_run(run))

        # Verify all saved
        runs = storage.list_runs(dataset_name=dataset.name)
        assert len(runs) == 3


class TestCLIIntegrationE2E(TestE2EFixturePaths):
    """CLI 통합 E2E 테스트."""

    def test_cli_run_with_json_dataset(self, korean_json):
        """CLI run 명령 JSON 데이터셋 테스트."""
        from typer.testing import CliRunner

        from evalvault.adapters.inbound.cli import app

        runner = CliRunner()

        # Just test that the CLI can parse the arguments correctly
        # Actual evaluation requires API keys
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "dataset" in result.output.lower()

    def test_cli_metrics_command(self):
        """CLI metrics 명령 테스트."""
        from typer.testing import CliRunner

        from evalvault.adapters.inbound.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["metrics"])

        assert result.exit_code == 0
        assert "faithfulness" in result.output

    def test_cli_config_command(self):
        """CLI config 명령 테스트."""
        from typer.testing import CliRunner

        from evalvault.adapters.inbound.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["config"])

        assert result.exit_code == 0


class TestRealEvaluationE2E(TestE2EFixturePaths):
    """실제 API를 사용하는 E2E 테스트.

    이 테스트는 OPENAI_API_KEY가 설정되어 있을 때만 실행됩니다.
    """

    @pytest.mark.slow
    @pytest.mark.requires_openai
    async def test_real_evaluation_korean_dataset(self, korean_json, e2e_results_db):
        """실제 OpenAI API를 사용한 한국어 데이터셋 평가.

        결과는 data/e2e_results/e2e_evaluations.db에 저장됩니다.
        """
        from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter
        from evalvault.config.settings import Settings

        settings = Settings()
        llm = OpenAIAdapter(settings)
        evaluator = RagasEvaluator()

        dataset = get_loader(korean_json).load(korean_json)

        # Evaluate with single metric for speed
        run = await evaluator.evaluate(
            dataset=dataset,
            metrics=["faithfulness"],
            llm=llm,
            thresholds={"faithfulness": 0.7},
        )

        assert run is not None
        assert len(run.results) == len(dataset)
        assert run.total_tokens > 0

        # Verify scores are reasonable
        for result in run.results:
            faith_metric = result.get_metric("faithfulness")
            assert faith_metric is not None
            assert 0.0 <= faith_metric.score <= 1.0

        # Save to persistent storage
        run_id = e2e_results_db.save_run(run)
        print(f"\n  [Korean] Saved run: {run_id} | Pass rate: {run.pass_rate:.1%}")

    @pytest.mark.slow
    @pytest.mark.requires_openai
    async def test_real_evaluation_english_dataset(self, english_json, e2e_results_db):
        """실제 OpenAI API를 사용한 영어 데이터셋 평가.

        결과는 data/e2e_results/e2e_evaluations.db에 저장됩니다.
        """
        from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter
        from evalvault.config.settings import Settings

        settings = Settings()
        llm = OpenAIAdapter(settings)
        evaluator = RagasEvaluator()

        dataset = get_loader(english_json).load(english_json)

        run = await evaluator.evaluate(
            dataset=dataset,
            metrics=["faithfulness"],
            llm=llm,
        )

        assert run is not None
        assert len(run.results) == len(dataset)

        # Save to persistent storage
        run_id = e2e_results_db.save_run(run)
        print(f"\n  [English] Saved run: {run_id} | Pass rate: {run.pass_rate:.1%}")

    @pytest.mark.slow
    @pytest.mark.requires_openai
    async def test_real_evaluation_with_storage(self, korean_json, e2e_results_db):
        """실제 평가 후 영구 저장소에 저장.

        결과는 data/e2e_results/e2e_evaluations.db에 저장되어
        테스트 실행 간 히스토리가 유지됩니다.
        """
        from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter
        from evalvault.config.settings import Settings

        settings = Settings()
        llm = OpenAIAdapter(settings)
        evaluator = RagasEvaluator()

        dataset = get_loader(korean_json).load(korean_json)

        # Evaluate
        run = await evaluator.evaluate(
            dataset=dataset,
            metrics=["faithfulness"],
            llm=llm,
        )

        # Store to persistent database
        run_id = e2e_results_db.save_run(run)

        # Retrieve and verify
        retrieved = e2e_results_db.get_run(run_id)
        assert retrieved.dataset_name == run.dataset_name
        assert len(retrieved.results) == len(run.results)

        # Print saved run info for visibility
        print(f"\n  Saved evaluation run: {run_id}")
        print(f"  Dataset: {run.dataset_name}")
        print(f"  Pass rate: {run.pass_rate:.1%}")
        print(f"  Total tokens: {run.total_tokens}")


class TestDatasetValidationE2E(TestE2EFixturePaths):
    """데이터셋 유효성 검증 E2E 테스트."""

    def test_korean_dataset_has_all_required_fields(self, korean_json):
        """한국어 데이터셋 필수 필드 검증."""
        dataset = get_loader(korean_json).load(korean_json)

        for tc in dataset:
            assert tc.id is not None
            assert tc.question is not None and len(tc.question) > 0
            assert tc.answer is not None and len(tc.answer) > 0
            assert tc.contexts is not None and len(tc.contexts) > 0

    def test_english_dataset_has_all_required_fields(self, english_json):
        """영어 데이터셋 필수 필드 검증."""
        dataset = get_loader(english_json).load(english_json)

        for tc in dataset:
            assert tc.id is not None
            assert tc.question is not None and len(tc.question) > 0
            assert tc.answer is not None and len(tc.answer) > 0
            assert tc.contexts is not None and len(tc.contexts) > 0

    def test_dataset_ids_are_unique(self, korean_json, english_json, edge_cases_json):
        """모든 데이터셋의 ID가 고유한지 검증."""
        for json_path in [korean_json, english_json, edge_cases_json]:
            dataset = get_loader(json_path).load(json_path)
            ids = [tc.id for tc in dataset]
            assert len(ids) == len(set(ids)), f"Duplicate IDs found in {json_path}"


class TestPerformanceE2E(TestE2EFixturePaths):
    """성능 관련 E2E 테스트."""

    def test_large_dataset_loading(self, tmp_path):
        """대용량 데이터셋 로딩 테스트."""
        # Create a large dataset
        large_dataset = {
            "name": "large-test-dataset",
            "version": "1.0.0",
            "test_cases": [
                {
                    "id": f"tc-{i:04d}",
                    "question": f"Question {i}?",
                    "answer": f"Answer {i}.",
                    "contexts": [f"Context {i} part {j}" for j in range(5)],
                    "ground_truth": f"Ground truth {i}",
                }
                for i in range(100)
            ],
        }

        large_json = tmp_path / "large_dataset.json"
        with open(large_json, "w") as f:
            json.dump(large_dataset, f)

        # Time the loading
        import time

        start = time.time()
        dataset = get_loader(large_json).load(large_json)
        elapsed = time.time() - start

        assert len(dataset) == 100
        assert elapsed < 5.0  # Should load in under 5 seconds

    def test_storage_performance_multiple_runs(self, tmp_path):
        """다중 실행 저장 성능 테스트."""
        import sys
        import time

        storage = SQLiteStorageAdapter(str(tmp_path / "perf_test.db"))

        start = time.time()

        # Save 50 runs
        for i in range(50):
            run = EvaluationRun(
                dataset_name=f"dataset-{i}",
                dataset_version="1.0.0",
                model_name="test-model",
                started_at=datetime.now(),
                finished_at=datetime.now() + timedelta(seconds=10),
                metrics_evaluated=["faithfulness"],
                thresholds={"faithfulness": 0.7},
                total_tokens=1000,
                results=[],
            )
            storage.save_run(run)

        elapsed = time.time() - start

        # Verify all saved
        runs = storage.list_runs(limit=100)
        assert len(runs) == 50
        # Windows is slower due to filesystem differences
        timeout = 30.0 if sys.platform == "win32" else 10.0
        assert elapsed < timeout
