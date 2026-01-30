"""CLI commands for method plugins."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import typer
import yaml
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.dataset.method_input_loader import MethodInputDatasetLoader
from evalvault.adapters.outbound.llm import SettingsLLMFactory, get_llm_adapter
from evalvault.adapters.outbound.methods import ExternalCommandMethod, MethodRegistry
from evalvault.adapters.outbound.nlp.korean.toolkit_factory import try_create_korean_toolkit
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.entities import Dataset
from evalvault.domain.entities.method import MethodOutput
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.domain.services.method_runner import MethodRunnerService
from evalvault.ports.outbound.method_port import MethodRuntime

from ..utils.console import print_cli_error, print_cli_warning, progress_spinner
from ..utils.options import db_option, profile_option
from ..utils.validators import parse_csv_option, validate_choices
from .run_helpers import (
    _display_results,
    _is_oss_open_model,
    _log_to_trackers,
    _resolve_thresholds,
    _save_results,
    _save_to_db,
    load_retriever_documents,
)


def create_method_app(console: Console) -> typer.Typer:
    """Create the Typer sub-application for method plugins."""

    method_app = typer.Typer(name="method", help="Method plugin utilities.")

    @method_app.command("list")
    def list_methods(
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed status."),
    ) -> None:
        registry = MethodRegistry()
        specs = registry.list_methods(load_details=True)

        if not specs:
            console.print("[yellow]No methods found.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name", style="bold")
        table.add_column("Source")
        table.add_column("Version")
        table.add_column("Status")
        table.add_column("Description")

        for spec in specs:
            status = "[green]ok[/green]"
            if spec.error:
                status = "[red]error[/red]"
            description = spec.description or ""
            if spec.error and verbose:
                description = f"{description} ({spec.error})".strip()
            table.add_row(
                spec.name,
                spec.source,
                spec.version or "-",
                status,
                description,
            )

        console.print(table)

    @method_app.command("run")
    def run_method(  # noqa: PLR0913 - CLI arguments intentionally flat
        dataset: Path = typer.Argument(
            ...,
            help="Path to base question dataset (JSON).",
            exists=True,
            readable=True,
        ),
        method: str = typer.Option(
            ...,
            "--method",
            "-m",
            help="Method plugin name to execute.",
        ),
        docs: Path | None = typer.Option(
            None,
            "--docs",
            help="Optional corpus file for retrieval (json/jsonl/txt).",
        ),
        method_config: str | None = typer.Option(
            None,
            "--method-config",
            help="Method config as JSON string.",
        ),
        method_config_file: Path | None = typer.Option(
            None,
            "--method-config-file",
            help="Method config file (json/yaml).",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output path for generated dataset JSON.",
        ),
        save_dataset: bool = typer.Option(
            True,
            "--save-dataset/--no-save-dataset",
            help="Persist generated dataset JSON.",
        ),
        evaluate: bool = typer.Option(
            True,
            "--evaluate/--no-evaluate",
            help="Evaluate the generated dataset after method execution.",
        ),
        metrics: str = typer.Option(
            "faithfulness,answer_relevancy",
            "--metrics",
            help="Comma-separated list of metrics for evaluation.",
        ),
        profile: str | None = profile_option(
            help_text="Model profile (dev, prod, openai). Overrides .env setting.",
        ),
        model: str | None = typer.Option(
            None,
            "--model",
            help="Model to use for evaluation (overrides profile).",
        ),
        tracker: str = typer.Option(
            "none",
            "--tracker",
            "-t",
            help="Tracker to log results: 'langfuse', 'mlflow', 'phoenix', or 'none'.",
        ),
        db_path: Path | None = db_option(),
        eval_output: Path | None = typer.Option(
            None,
            "--eval-output",
            help="Output file for evaluation summary (JSON).",
        ),
        parallel: bool = typer.Option(
            False,
            "--parallel/--no-parallel",
            help="Enable parallel evaluation.",
        ),
        batch_size: int = typer.Option(
            5,
            "--batch-size",
            help="Parallel batch size.",
        ),
    ) -> None:
        registry = MethodRegistry()

        try:
            spec = registry.get_spec(method, load_details=True)
        except Exception as exc:
            print_cli_error(
                console,
                "메서드 로딩에 실패했습니다.",
                details=str(exc),
                fixes=[
                    "등록된 메서드 이름을 확인하세요.",
                    "evalvault method list로 목록을 확인하세요.",
                ],
            )
            raise typer.Exit(1) from exc

        if spec.error:
            print_cli_error(
                console,
                "메서드 로딩 중 오류가 발생했습니다.",
                details=spec.error,
            )
            raise typer.Exit(1)
        if spec.runner == "external" and not spec.command:
            print_cli_error(
                console,
                "외부 실행 메서드는 command 설정이 필요합니다.",
                fixes=["config/methods.yaml에 command를 추가하세요."],
            )
            raise typer.Exit(1)

        method_instance = None
        if spec.command:
            method_instance = ExternalCommandMethod(
                command=spec.command,
                workdir=spec.workdir,
                env=spec.env,
                timeout_seconds=spec.timeout_seconds,
                shell=spec.shell,
            )
            method_instance.name = spec.name
            if spec.description:
                method_instance.description = spec.description
        else:
            try:
                method_instance = registry.get_method(method)
            except Exception as exc:
                print_cli_error(
                    console,
                    "메서드 로딩에 실패했습니다.",
                    details=str(exc),
                    fixes=[
                        "등록된 메서드 이름을 확인하세요.",
                        "evalvault method list로 목록을 확인하세요.",
                    ],
                )
                raise typer.Exit(1) from exc

        config = _load_method_config(method_config, method_config_file, console)
        if spec.default_config:
            merged = dict(spec.default_config)
            if config:
                merged.update(config)
            config = merged

        loader = MethodInputDatasetLoader()
        try:
            input_dataset = loader.load(dataset)
        except Exception as exc:
            print_cli_error(
                console,
                "베이스 데이터셋 로딩에 실패했습니다.",
                details=str(exc),
            )
            raise typer.Exit(1) from exc

        documents = None
        doc_ids = None
        if docs:
            try:
                documents, doc_ids = load_retriever_documents(docs)
            except Exception as exc:
                print_cli_error(
                    console,
                    "도메인 문서 로딩에 실패했습니다.",
                    details=str(exc),
                    fixes=["--docs 파일 경로와 포맷을 확인하세요."],
                )
                raise typer.Exit(1) from exc

        settings = Settings()
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        run_id = str(uuid4())
        safe_name = method_instance.name.replace("/", "_")
        artifacts_dir = Path("reports") / "experiments" / safe_name / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        method_output_path = artifacts_dir / "method_outputs.json"
        config_path = _write_method_config(config, artifacts_dir) if config else None

        runtime_metadata: dict[str, Any] = {"source": spec.source}
        if spec.command:
            runtime_metadata.update(
                {
                    "command": spec.command,
                    "workdir": spec.workdir,
                    "shell": spec.shell,
                    "timeout_seconds": spec.timeout_seconds,
                }
            )

        runtime = MethodRuntime(
            run_id=run_id,
            settings=settings,
            documents=documents,
            document_ids=doc_ids,
            input_path=str(dataset),
            docs_path=str(docs) if docs else None,
            output_path=str(method_output_path),
            config_path=str(config_path) if config_path else None,
            artifacts_dir=str(artifacts_dir),
            metadata=runtime_metadata,
        )

        method_runner = MethodRunnerService()
        method_started_at = datetime.now()
        with progress_spinner(console, "🧩 Method 실행 중...") as update_progress:
            try:
                update_progress("🧩 Method 실행 중...")
                method_result = asyncio.run(
                    method_runner.run(
                        method=method_instance,
                        input_dataset=input_dataset,
                        runtime=runtime,
                        config=config,
                    )
                )
            except Exception as exc:
                print_cli_error(
                    console,
                    "메서드 실행 중 오류가 발생했습니다.",
                    details=str(exc),
                    fixes=["메서드 의존성과 설정을 확인하세요."],
                )
                raise typer.Exit(1) from exc
        method_finished_at = datetime.now()

        _write_method_outputs(method_result.outputs, method_output_path, console)
        output_path = output
        if save_dataset and output_path is None:
            output_path = artifacts_dir / "dataset.json"

        if save_dataset and output_path is not None:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                payload = _serialize_dataset(
                    method_result.dataset,
                    retrieval_metadata=method_result.retrieval_metadata,
                )
                output_path.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                console.print(f"[green]Dataset saved to {output_path}[/green]")
            except Exception as exc:
                print_cli_warning(
                    console,
                    "생성된 데이터셋 저장에 실패했습니다.",
                    tips=[str(exc)],
                )

        if not evaluate:
            return

        metric_list = parse_csv_option(metrics)
        if not metric_list:
            print_cli_error(
                console,
                "평가할 메트릭이 없습니다.",
                fixes=["--metrics 옵션을 확인하세요."],
            )
            raise typer.Exit(1)

        available_metrics = list(RagasEvaluator.METRIC_MAP.keys()) + list(
            RagasEvaluator.CUSTOM_METRIC_MAP.keys()
        )
        validate_choices(metric_list, available_metrics, console, value_label="metric")

        if model:
            if _is_oss_open_model(model) and settings.llm_provider != "vllm":
                settings.llm_provider = "ollama"
                settings.ollama_model = model
                console.print(
                    "[dim]OSS model detected. Routing request through Ollama backend.[/dim]"
                )
            elif settings.llm_provider == "ollama":
                settings.ollama_model = model
            elif settings.llm_provider == "vllm":
                settings.vllm_model = model
            else:
                settings.openai_model = model

        if settings.llm_provider == "openai" and not settings.openai_api_key:
            print_cli_error(
                console,
                "OPENAI_API_KEY가 설정되지 않았습니다.",
                fixes=[
                    ".env 파일 또는 환경 변수에 OPENAI_API_KEY=... 값을 추가하세요.",
                    "--profile dev 같이 Ollama 기반 프로필을 사용해 로컬 모델을 실행하세요.",
                ],
            )
            raise typer.Exit(1)

        llm_adapter = get_llm_adapter(settings)
        llm_factory = SettingsLLMFactory(settings)
        korean_toolkit = try_create_korean_toolkit()
        evaluator = RagasEvaluator(korean_toolkit=korean_toolkit, llm_factory=llm_factory)
        resolved_thresholds = _resolve_thresholds(metric_list, method_result.dataset)

        with progress_spinner(console, "🤖 Evaluation in progress") as update_progress:
            try:
                update_progress("🤖 Evaluation in progress")
                result = asyncio.run(
                    evaluator.evaluate(
                        dataset=method_result.dataset,
                        metrics=metric_list,
                        llm=llm_adapter,
                        thresholds=resolved_thresholds,
                        parallel=parallel,
                        batch_size=batch_size,
                    )
                )
            except Exception as exc:
                print_cli_error(
                    console,
                    "평가 실행 중 오류가 발생했습니다.",
                    details=str(exc),
                )
                raise typer.Exit(1) from exc

        result.retrieval_metadata = method_result.retrieval_metadata
        result.tracker_metadata.setdefault("method", method_result.method_metadata)
        if output_path is not None:
            result.tracker_metadata.setdefault("method_output_path", str(output_path))
        result.tracker_metadata.setdefault("method_outputs_path", str(method_output_path))
        result.tracker_metadata.setdefault("method_base_dataset", str(dataset))
        result.tracker_metadata.setdefault("method_run_started_at", method_started_at.isoformat())
        result.tracker_metadata.setdefault("method_run_finished_at", method_finished_at.isoformat())
        result.tracker_metadata.setdefault(
            "method_run_duration_ms",
            int((method_finished_at - method_started_at).total_seconds() * 1000),
        )

        _display_results(result, console)

        if tracker and tracker != "none":
            _log_to_trackers(settings, result, console, tracker_type=tracker)

        if eval_output:
            _save_results(eval_output, result, console)

        _save_to_db(db_path, result, console)

    return method_app


def _load_method_config(
    inline: str | None,
    path: Path | None,
    console: Console,
) -> dict[str, Any] | None:
    if inline and path:
        print_cli_error(
            console,
            "method-config와 method-config-file을 동시에 사용할 수 없습니다.",
            fixes=["둘 중 하나만 지정하세요."],
        )
        raise typer.Exit(1)

    if inline:
        try:
            return json.loads(inline)
        except json.JSONDecodeError as exc:
            print_cli_error(
                console,
                "method-config JSON 파싱에 실패했습니다.",
                details=str(exc),
            )
            raise typer.Exit(1) from exc

    if path:
        try:
            content = path.read_text(encoding="utf-8")
            if path.suffix.lower() in {".json"}:
                return json.loads(content)
            return yaml.safe_load(content) or {}
        except Exception as exc:
            print_cli_error(
                console,
                "method-config-file 로딩에 실패했습니다.",
                details=str(exc),
            )
            raise typer.Exit(1) from exc

    return None


def _serialize_dataset(
    dataset: Dataset,
    *,
    retrieval_metadata: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload = {
        "name": dataset.name,
        "version": dataset.version,
        "metadata": dataset.metadata,
        "thresholds": dataset.thresholds,
        "test_cases": [
            {
                "id": tc.id,
                "question": tc.question,
                "answer": tc.answer,
                "contexts": tc.contexts,
                "ground_truth": tc.ground_truth,
                "metadata": tc.metadata,
            }
            for tc in dataset.test_cases
        ],
    }
    if retrieval_metadata:
        payload["retrieval_metadata"] = retrieval_metadata
    return payload


def _write_method_config(config: dict[str, Any], artifacts_dir: Path) -> Path:
    path = artifacts_dir / "method_config.json"
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_method_outputs(
    outputs: list[MethodOutput],
    output_path: Path,
    console: Console,
) -> None:
    try:
        payload = {
            "outputs": [
                {
                    "id": output.id,
                    "answer": output.answer,
                    "contexts": output.contexts,
                    "metadata": output.metadata,
                    "retrieval_metadata": output.retrieval_metadata,
                }
                for output in outputs
            ]
        }
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        console.print(f"[green]Method outputs saved to {output_path}[/green]")
    except Exception as exc:
        print_cli_warning(
            console,
            "메서드 출력 저장에 실패했습니다.",
            tips=[str(exc)],
        )


__all__ = ["create_method_app"]
