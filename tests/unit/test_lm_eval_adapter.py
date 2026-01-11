"""Unit tests for LMEvalAdapter."""

from unittest.mock import MagicMock, patch

import pytest

from evalvault.ports.outbound.benchmark_port import (
    BenchmarkBackend,
    BenchmarkRequest,
    BenchmarkResponse,
    BenchmarkTaskResult,
)


class TestBenchmarkPort:
    """BenchmarkPort 데이터 클래스 테스트."""

    def test_benchmark_request_defaults(self):
        request = BenchmarkRequest(tasks=["kmmlu_insurance"])

        assert request.tasks == ["kmmlu_insurance"]
        assert request.backend == BenchmarkBackend.VLLM
        assert request.num_fewshot == 0
        assert request.batch_size == "auto"
        assert request.limit is None

    def test_benchmark_request_custom(self):
        request = BenchmarkRequest(
            tasks=["kmmlu_insurance", "kmmlu_finance"],
            backend=BenchmarkBackend.HF,
            model_args={"pretrained": "gpt2"},
            num_fewshot=5,
            limit=100,
        )

        assert len(request.tasks) == 2
        assert request.backend == BenchmarkBackend.HF
        assert request.model_args["pretrained"] == "gpt2"
        assert request.num_fewshot == 5
        assert request.limit == 100

    def test_benchmark_response_success(self):
        response = BenchmarkResponse(
            results={
                "kmmlu_insurance": BenchmarkTaskResult(
                    task_name="kmmlu_insurance",
                    metrics={"acc,none": 0.75, "acc_stderr,none": 0.02},
                )
            },
            model_name="llama2",
            total_time_seconds=120.5,
        )

        assert response.success is True
        assert response.get_main_score("kmmlu_insurance") == 0.75
        assert response.get_main_score("kmmlu_insurance", "acc") == 0.75

    def test_benchmark_response_error(self):
        response = BenchmarkResponse(error="Model not found")

        assert response.success is False
        assert response.error == "Model not found"

    def test_benchmark_response_missing_task(self):
        response = BenchmarkResponse(
            results={"kmmlu_insurance": BenchmarkTaskResult(task_name="kmmlu_insurance")}
        )

        assert response.get_main_score("kmmlu_finance") is None

    def test_to_breakdown_dict(self):
        response = BenchmarkResponse(
            results={
                "kmmlu_insurance": BenchmarkTaskResult(
                    task_name="kmmlu_insurance",
                    metrics={"acc,none": 0.80},
                ),
                "kmmlu_finance": BenchmarkTaskResult(
                    task_name="kmmlu_finance",
                    metrics={"acc,none": 0.70},
                ),
            },
            model_name="test-model",
            backend=BenchmarkBackend.VLLM,
            total_time_seconds=60.0,
        )

        breakdown = response.to_breakdown_dict()

        assert breakdown["kmmlu_accuracy"] == 0.75
        assert "Insurance" in breakdown["kmmlu_subject_accuracy"]
        assert "Finance" in breakdown["kmmlu_subject_accuracy"]
        assert breakdown["model"] == "test-model"
        assert breakdown["backend"] == "vllm"


class TestLMEvalAdapter:
    """LMEvalAdapter 단위 테스트."""

    @pytest.fixture
    def mock_lm_eval_not_installed(self):
        with patch.dict("sys.modules", {"lm_eval": None}):
            yield

    def test_adapter_import_without_lm_eval(self):
        pass

    def test_adapter_initialization(self):
        from evalvault.adapters.outbound.benchmark.lm_eval_adapter import LMEvalAdapter

        adapter = LMEvalAdapter(settings=None)
        assert adapter._settings is None
        assert adapter._custom_task_paths == []

    def test_adapter_with_custom_paths(self):
        from evalvault.adapters.outbound.benchmark.lm_eval_adapter import LMEvalAdapter

        adapter = LMEvalAdapter(
            settings=None,
            custom_task_paths=["./custom_tasks", "./my_benchmarks"],
        )
        assert len(adapter._custom_task_paths) == 2

    def test_get_model_type_mapping(self):
        from evalvault.adapters.outbound.benchmark.lm_eval_adapter import LMEvalAdapter

        adapter = LMEvalAdapter()

        assert adapter._get_model_type(BenchmarkBackend.HF) == "hf"
        assert adapter._get_model_type(BenchmarkBackend.VLLM) == "local-completions"
        assert adapter._get_model_type(BenchmarkBackend.OPENAI) == "openai-chat-completions"
        assert adapter._get_model_type(BenchmarkBackend.API) == "local-completions"
        assert adapter._get_model_type(BenchmarkBackend.OLLAMA) == "local-chat-completions"

    def test_build_model_args_string(self):
        from evalvault.adapters.outbound.benchmark.lm_eval_adapter import LMEvalAdapter

        adapter = LMEvalAdapter()

        result = adapter._build_model_args_string(
            BenchmarkBackend.VLLM,
            {"model": "llama2", "base_url": "http://localhost:8000/v1", "empty": None},
        )

        assert "model=llama2" in result
        assert "base_url=http://localhost:8000/v1" in result
        assert "empty" not in result

    def test_supports_backend(self):
        from evalvault.adapters.outbound.benchmark.lm_eval_adapter import LMEvalAdapter

        adapter = LMEvalAdapter()

        assert adapter.supports_backend(BenchmarkBackend.HF) is True
        assert adapter.supports_backend(BenchmarkBackend.VLLM) is True
        assert adapter.supports_backend(BenchmarkBackend.OPENAI) is True
        assert adapter.supports_backend(BenchmarkBackend.API) is True

    def test_parse_results(self):
        from evalvault.adapters.outbound.benchmark.lm_eval_adapter import LMEvalAdapter

        adapter = LMEvalAdapter()
        response = BenchmarkResponse()

        raw_results = {
            "results": {
                "kmmlu_insurance": {
                    "acc,none": 0.75,
                    "acc_stderr,none": 0.02,
                    "alias": "KMMLU Insurance",
                }
            },
            "versions": {"kmmlu_insurance": "1.0"},
        }

        adapter._parse_results(raw_results, response)

        assert "kmmlu_insurance" in response.results
        result = response.results["kmmlu_insurance"]
        assert result.metrics["acc,none"] == 0.75
        assert result.version == "1.0"
        assert result.config["alias"] == "KMMLU Insurance"

    def test_parse_results_empty(self):
        from evalvault.adapters.outbound.benchmark.lm_eval_adapter import LMEvalAdapter

        adapter = LMEvalAdapter()
        response = BenchmarkResponse()

        adapter._parse_results(None, response)
        assert len(response.results) == 0

        adapter._parse_results({}, response)
        assert len(response.results) == 0


class TestLMEvalAdapterWithMockedEvaluator:
    """lm_eval.evaluator를 모킹한 테스트."""

    @pytest.fixture
    def mock_lm_eval(self):
        mock_evaluator = MagicMock()
        mock_evaluator.simple_evaluate.return_value = {
            "results": {
                "kmmlu_insurance": {
                    "acc,none": 0.78,
                    "acc_stderr,none": 0.015,
                }
            },
            "versions": {"kmmlu_insurance": "1.0"},
            "config": {"model": "local-chat-completions"},
        }

        with (
            patch(
                "evalvault.adapters.outbound.benchmark.lm_eval_adapter.LM_EVAL_AVAILABLE",
                True,
            ),
            patch(
                "evalvault.adapters.outbound.benchmark.lm_eval_adapter.evaluator",
                mock_evaluator,
            ),
        ):
            yield mock_evaluator

    def test_run_benchmark_success(self, mock_lm_eval):
        from evalvault.adapters.outbound.benchmark.lm_eval_adapter import LMEvalAdapter

        adapter = LMEvalAdapter()
        request = BenchmarkRequest(
            tasks=["kmmlu_insurance"],
            backend=BenchmarkBackend.VLLM,
            model_args={"model": "llama2", "base_url": "http://localhost:8000/v1"},
            num_fewshot=5,
        )

        response = adapter.run_benchmark(request)

        assert response.success is True
        assert response.error is None
        assert "kmmlu_insurance" in response.results
        assert response.results["kmmlu_insurance"].metrics["acc,none"] == 0.78
        assert response.total_time_seconds >= 0

        mock_lm_eval.simple_evaluate.assert_called_once()
        call_kwargs = mock_lm_eval.simple_evaluate.call_args.kwargs
        assert call_kwargs["tasks"] == ["kmmlu_insurance"]
        assert call_kwargs["num_fewshot"] == 5

    def test_run_benchmark_with_limit(self, mock_lm_eval):
        from evalvault.adapters.outbound.benchmark.lm_eval_adapter import LMEvalAdapter

        adapter = LMEvalAdapter()
        request = BenchmarkRequest(
            tasks=["kmmlu_insurance"],
            limit=10,
        )

        adapter.run_benchmark(request)

        call_kwargs = mock_lm_eval.simple_evaluate.call_args.kwargs
        assert call_kwargs["limit"] == 10


class TestLMEvalAdapterNotInstalled:
    """lm-eval 미설치 시 테스트."""

    def test_ensure_lm_eval_raises(self):
        from evalvault.adapters.outbound.benchmark.lm_eval_adapter import (
            LM_EVAL_AVAILABLE,
            LMEvalAdapter,
        )

        if LM_EVAL_AVAILABLE:
            pytest.skip("lm-eval is installed")

        adapter = LMEvalAdapter()

        with pytest.raises(ImportError, match="lm-evaluation-harness not installed"):
            adapter._ensure_lm_eval()

    def test_run_benchmark_not_installed(self):
        from evalvault.adapters.outbound.benchmark.lm_eval_adapter import (
            LM_EVAL_AVAILABLE,
            LMEvalAdapter,
        )

        if LM_EVAL_AVAILABLE:
            pytest.skip("lm-eval is installed")

        adapter = LMEvalAdapter()

        with pytest.raises(ImportError, match="not installed"):
            adapter._ensure_lm_eval()
