"""lm-evaluation-harness adapter for EvalVault benchmark integration."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from evalvault.ports.outbound.benchmark_port import (
    BenchmarkBackend,
    BenchmarkPort,
    BenchmarkRequest,
    BenchmarkResponse,
    BenchmarkTaskResult,
)

if TYPE_CHECKING:
    from evalvault.config.settings import Settings

logger = logging.getLogger(__name__)

LM_EVAL_AVAILABLE = False
try:
    import lm_eval
    from lm_eval import evaluator
    from lm_eval.tasks import TaskManager

    LM_EVAL_AVAILABLE = True
except ImportError:
    lm_eval = None  # type: ignore[assignment]
    evaluator = None  # type: ignore[assignment]
    TaskManager = None  # type: ignore[assignment]


class LMEvalAdapter(BenchmarkPort):
    """lm-evaluation-harness adapter.

    Supports multiple backends with proper loglikelihood support:
    - HF: Local HuggingFace models (full loglikelihood support)
    - VLLM: vLLM server via /v1/completions (loglikelihood via local-completions)
    - OLLAMA: Ollama server via /v1/completions (loglikelihood via local-completions)
    - OPENAI: OpenAI API (chat-completions only, use kmmlu_direct for MCQ)
    - API: Generic OpenAI-compatible API (local-completions for loglikelihood)
    """

    def __init__(
        self,
        settings: Settings | None = None,
        custom_task_paths: list[str] | None = None,
    ):
        self._settings = settings
        self._custom_task_paths = custom_task_paths or []
        self._task_manager: Any = None
        self._ollama_is_thinking: bool = False

    def _ensure_lm_eval(self) -> None:
        if not LM_EVAL_AVAILABLE:
            raise ImportError(
                "lm-evaluation-harness not installed. "
                'Install with: pip install "lm_eval[hf,vllm,api]"'
            )

    def _get_task_manager(self) -> Any:
        self._ensure_lm_eval()
        if self._task_manager is None:
            if self._custom_task_paths:
                self._task_manager = TaskManager(
                    include_path=self._custom_task_paths,
                    include_defaults=True,
                )
            else:
                self._task_manager = TaskManager()
        return self._task_manager

    def _is_ollama_thinking_model(self, base_url: str, model_name: str) -> bool:
        try:
            import requests

            response = requests.post(
                f"{base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "stream": False,
                },
                timeout=30,
            )
            if response.ok:
                data = response.json()
                message = data.get("message", {})
                return "thinking" in message
        except Exception as e:
            logger.debug("Failed to detect thinking model: %s", e)
        return False

    def _build_model_args_string(
        self,
        backend: BenchmarkBackend,
        model_args: dict[str, Any],
    ) -> str:
        parts = []
        for key, value in model_args.items():
            if value is not None:
                parts.append(f"{key}={value}")
        return ",".join(parts)

    def _get_model_type(self, backend: BenchmarkBackend) -> str:
        mapping = {
            BenchmarkBackend.HF: "hf",
            BenchmarkBackend.VLLM: "local-completions",
            BenchmarkBackend.OPENAI: "openai-chat-completions",
            BenchmarkBackend.API: "local-completions",
            BenchmarkBackend.OLLAMA: "local-chat-completions",
        }
        return mapping.get(backend, "hf")

    def _build_model_args_from_settings(
        self,
        backend: BenchmarkBackend,
    ) -> dict[str, Any]:
        if self._settings is None:
            return {}

        if backend == BenchmarkBackend.VLLM:
            base_url = self._settings.vllm_base_url.rstrip("/")
            if not base_url.endswith("/v1"):
                base_url = f"{base_url}/v1" if "/v1" not in base_url else base_url
            return {
                "model": self._settings.vllm_model,
                "base_url": f"{base_url}/completions",
                "tokenizer_backend": "remote",
                "num_concurrent": 4,
                "max_retries": 3,
            }
        elif backend == BenchmarkBackend.OPENAI:
            return {
                "model": self._settings.openai_model,
            }
        elif backend == BenchmarkBackend.OLLAMA:
            base_url = getattr(self._settings, "ollama_base_url", "http://localhost:11434")
            base_url = base_url.rstrip("/")
            model_name = self._settings.ollama_model
            is_thinking = self._is_ollama_thinking_model(base_url, model_name)
            max_gen_toks = 8192 if is_thinking else 256
            self._ollama_is_thinking = is_thinking
            return {
                "model": model_name,
                "base_url": f"{base_url}/v1/chat/completions",
                "tokenized_requests": False,
                "num_concurrent": 1,
                "max_retries": 3,
                "timeout": getattr(self._settings, "ollama_timeout", 600),
                "max_gen_toks": max_gen_toks,
            }
        elif backend == BenchmarkBackend.HF:
            return {}
        elif backend == BenchmarkBackend.API:
            return {
                "tokenizer_backend": "huggingface",
                "num_concurrent": 1,
                "max_retries": 3,
            }
        return {}

    def run_benchmark(self, request: BenchmarkRequest) -> BenchmarkResponse:
        self._ensure_lm_eval()

        start_time = time.time()
        response = BenchmarkResponse(backend=request.backend)

        try:
            model_type = self._get_model_type(request.backend)

            final_model_args = self._build_model_args_from_settings(request.backend)
            final_model_args.update(request.model_args)
            model_args_str = self._build_model_args_string(
                request.backend,
                final_model_args,
            )

            response.model_name = final_model_args.get("model", "unknown")

            logger.info(
                "Running lm-eval: tasks=%s, model=%s, backend=%s",
                request.tasks,
                response.model_name,
                model_type,
            )

            eval_kwargs: dict[str, Any] = {
                "model": model_type,
                "model_args": model_args_str,
                "tasks": request.tasks,
                "num_fewshot": request.num_fewshot,
                "batch_size": request.batch_size,
            }

            if model_type in ("local-chat-completions", "openai-chat-completions"):
                eval_kwargs["apply_chat_template"] = True

            if request.limit is not None:
                eval_kwargs["limit"] = request.limit

            if request.output_path:
                eval_kwargs["output_path"] = request.output_path

            if self._ollama_is_thinking and request.backend == BenchmarkBackend.OLLAMA:
                eval_kwargs["gen_kwargs"] = {"until": ["Q:", "\n\n\n"]}
                eval_kwargs["log_samples"] = True

            eval_kwargs.update(request.extra_args)

            if self._custom_task_paths:
                eval_kwargs["task_manager"] = self._get_task_manager()

            results = evaluator.simple_evaluate(**eval_kwargs)

            response.raw_output = results if isinstance(results, dict) else {}

            if self._ollama_is_thinking and request.backend == BenchmarkBackend.OLLAMA:
                self._parse_results_with_mcq_extraction(results, response)
            else:
                self._parse_results(results, response)

        except Exception as e:
            logger.exception("Benchmark evaluation failed")
            response.error = str(e)

        response.total_time_seconds = time.time() - start_time
        return response

    def _parse_results(
        self,
        raw_results: dict[str, Any] | None,
        response: BenchmarkResponse,
    ) -> None:
        if not raw_results:
            return

        results_dict = raw_results.get("results", {})
        n_samples_dict = raw_results.get("n-samples", {})

        for task_name, task_metrics in results_dict.items():
            if not isinstance(task_metrics, dict):
                continue

            task_result = BenchmarkTaskResult(
                task_name=task_name,
                metrics={},
            )

            for metric_key, value in task_metrics.items():
                if isinstance(value, int | float) and not metric_key.endswith("_stderr"):
                    task_result.metrics[metric_key] = float(value)

            if "alias" in task_metrics:
                task_result.config["alias"] = task_metrics["alias"]

            versions = raw_results.get("versions", {})
            if task_name in versions:
                task_result.version = str(versions[task_name])

            task_n_samples = n_samples_dict.get(task_name, {})
            task_result.num_samples = task_n_samples.get("effective", 0)

            response.results[task_name] = task_result

    def _parse_results_with_mcq_extraction(
        self,
        raw_results: dict[str, Any] | None,
        response: BenchmarkResponse,
    ) -> None:
        import re

        if not raw_results:
            return

        samples_dict = raw_results.get("samples", {})
        n_samples_dict = raw_results.get("n-samples", {})

        for task_name, samples in samples_dict.items():
            if not samples:
                continue

            correct = 0
            total = len(samples)

            for sample in samples:
                target = sample.get("target", "")
                raw_response = ""
                if sample.get("resps") and sample["resps"][0]:
                    raw_response = sample["resps"][0][0] or ""

                match = re.search(r"([A-D])", raw_response)
                extracted = match.group(1) if match else None

                if extracted and extracted.upper() == target.upper():
                    correct += 1

            accuracy = correct / total if total > 0 else 0.0

            task_result = BenchmarkTaskResult(
                task_name=task_name,
                metrics={"acc,none": accuracy, "acc": accuracy},
            )

            task_n_samples = n_samples_dict.get(task_name, {})
            task_result.num_samples = task_n_samples.get("effective", total)

            versions = raw_results.get("versions", {})
            if task_name in versions:
                task_result.version = str(versions[task_name])

            response.results[task_name] = task_result

            logger.info(
                "MCQ extraction for %s: %d/%d correct (%.2f%%)",
                task_name,
                correct,
                total,
                accuracy * 100,
            )

    def list_available_tasks(self) -> list[str]:
        self._ensure_lm_eval()
        task_manager = self._get_task_manager()
        return list(task_manager.all_tasks)

    def get_task_info(self, task_name: str) -> dict[str, Any]:
        self._ensure_lm_eval()
        task_manager = self._get_task_manager()

        if task_name not in task_manager.all_tasks:
            return {"error": f"Task '{task_name}' not found"}

        try:
            task_dict = task_manager.load_task_or_group(task_name)
            if isinstance(task_dict, dict) and task_name in task_dict:
                task = task_dict[task_name]
                return {
                    "name": task_name,
                    "version": getattr(task, "VERSION", "unknown"),
                    "description": getattr(task, "DATASET_NAME", ""),
                    "metrics": getattr(task, "METRIC_LIST", []),
                }
        except Exception as e:
            logger.warning("Failed to load task info for %s: %s", task_name, e)

        return {"name": task_name}

    def supports_backend(self, backend: BenchmarkBackend) -> bool:
        return backend in {
            BenchmarkBackend.HF,
            BenchmarkBackend.VLLM,
            BenchmarkBackend.OPENAI,
            BenchmarkBackend.API,
            BenchmarkBackend.OLLAMA,
        }


def create_lm_eval_adapter(settings: Settings | None = None) -> LMEvalAdapter:
    return LMEvalAdapter(settings=settings)
