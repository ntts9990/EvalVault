"""Prompt snapshot commands for the EvalVault CLI."""

from __future__ import annotations

import asyncio
import difflib
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.llm import SettingsLLMFactory, get_llm_adapter
from evalvault.adapters.outbound.nlp.korean.toolkit_factory import try_create_korean_toolkit
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.entities import Dataset, EvaluationRun, PromptSetBundle, TestCase
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.ports.outbound.llm_port import GenerationOptions

from ..utils.analysis_io import resolve_artifact_dir, resolve_output_paths
from ..utils.console import print_cli_error, print_cli_warning, progress_spinner
from ..utils.options import db_option
from ..utils.validators import parse_csv_option
from .run_helpers import _is_oss_open_model


def _bundle_to_role_map(bundle: PromptSetBundle) -> dict[str, dict[str, str]]:
    prompt_map = {prompt.prompt_id: prompt for prompt in bundle.prompts}
    roles: dict[str, dict[str, str]] = {}
    for item in bundle.items:
        prompt = prompt_map.get(item.prompt_id)
        if not prompt:
            continue
        roles[item.role] = {
            "checksum": prompt.checksum,
            "content": prompt.content,
            "name": prompt.name,
            "kind": prompt.kind,
        }
    return roles


def _default_role(bundle: PromptSetBundle) -> str | None:
    for item in bundle.items:
        if item.role == "system":
            return item.role
    return bundle.items[0].role if bundle.items else None


def _build_dataset_from_run(run: EvaluationRun, console: Console) -> Dataset:
    test_cases: list[TestCase] = []
    skipped = 0
    for result in run.results:
        if not result.question or result.answer is None or result.contexts is None:
            skipped += 1
            continue
        test_cases.append(
            TestCase(
                id=result.test_case_id,
                question=result.question,
                answer=result.answer,
                contexts=result.contexts,
                ground_truth=result.ground_truth,
            )
        )
    if skipped:
        print_cli_warning(
            console,
            f"{skipped}개 테스트 케이스에 질문/답변/컨텍스트가 없어 제외했습니다.",
        )
    return Dataset(
        name=run.dataset_name,
        version=run.dataset_version,
        test_cases=test_cases,
        thresholds=dict(run.thresholds),
    )


def _parse_weights(
    console: Console,
    weights_raw: str | None,
    metrics: list[str],
) -> dict[str, float]:
    if not metrics:
        return {}
    if not weights_raw:
        base = 1.0 / len(metrics)
        return dict.fromkeys(metrics, base)
    entries = parse_csv_option(weights_raw)
    weights: dict[str, float] = {}
    for entry in entries:
        if "=" not in entry:
            print_cli_error(
                console,
                "--weights 형식이 올바르지 않습니다.",
                fixes=["예: --weights faithfulness=0.5,answer_relevancy=0.5"],
                details=entry,
            )
            raise typer.Exit(1)
        key, raw_value = entry.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        try:
            value = float(raw_value)
        except ValueError:
            print_cli_error(
                console,
                "--weights 값은 숫자여야 합니다.",
                details=entry,
            )
            raise typer.Exit(1)
        if value < 0:
            print_cli_error(
                console,
                "--weights 값은 0 이상이어야 합니다.",
                details=entry,
            )
            raise typer.Exit(1)
        weights[key] = value

    missing = [metric for metric in metrics if metric not in weights]
    if missing:
        print_cli_error(
            console,
            "--weights에 모든 메트릭을 포함해야 합니다.",
            fixes=["누락된 메트릭을 추가하거나 --weights 옵션을 제거하세요."],
            details=", ".join(missing),
        )
        raise typer.Exit(1)

    total = sum(weights.values())
    if total <= 0:
        print_cli_error(
            console,
            "--weights 합계는 0보다 커야 합니다.",
        )
        raise typer.Exit(1)
    return {metric: weights[metric] / total for metric in metrics}


def _rank_candidates(scores: list[Any]) -> list[str]:
    return [
        score.candidate_id
        for score in sorted(scores, key=lambda entry: entry.weighted_score, reverse=True)
    ]


def _resolve_llm_config(
    *,
    settings: Settings,
    run_model: str,
    model_override: str | None,
    provider_override: str | None,
    console: Console,
) -> tuple[Settings, str, str]:
    resolved_model = model_override or run_model
    if not resolved_model:
        print_cli_error(
            console,
            "LLM 모델을 결정할 수 없습니다.",
            fixes=["--model 옵션을 지정하세요."],
        )
        raise typer.Exit(1)

    provider = provider_override
    if "/" in resolved_model:
        provider, resolved_model = resolved_model.split("/", 1)
    elif not provider:
        if "/" in run_model:
            provider, run_model = run_model.split("/", 1)
            resolved_model = model_override or run_model
        else:
            provider = settings.llm_provider

    if provider is None:
        provider = settings.llm_provider

    provider = provider.strip().lower()
    if _is_oss_open_model(resolved_model) and provider != "vllm":
        provider = "ollama"

    settings.llm_provider = provider
    if provider == "ollama":
        settings.ollama_model = resolved_model
    elif provider == "vllm":
        settings.vllm_model = resolved_model
    elif provider == "azure":
        settings.azure_deployment = resolved_model
    elif provider == "anthropic":
        settings.anthropic_model = resolved_model
    else:
        settings.openai_model = resolved_model

    if settings.llm_provider == "openai" and not settings.openai_api_key:
        print_cli_error(
            console,
            "OPENAI_API_KEY가 설정되지 않았습니다.",
            fixes=[
                ".env 파일 또는 환경 변수에 OPENAI_API_KEY=... 값을 추가하세요.",
                "--provider ollama 같이 로컬 모델을 사용하세요.",
            ],
        )
        raise typer.Exit(1)

    return settings, provider, resolved_model


def create_prompts_app(console: Console) -> typer.Typer:
    """Create the `prompts` sub-application."""

    app = typer.Typer(help="Prompt snapshots and diffs.")

    @app.command("show")
    def show_prompt_set(
        run_id: str = typer.Argument(..., help="Run ID to inspect."),
        db_path: Path | None = db_option(help_text="Path to database file."),
    ) -> None:
        """Show prompt snapshots attached to a run."""
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        bundle = storage.get_prompt_set_for_run(run_id)
        if not bundle:
            console.print("[yellow]No prompt set found for this run.[/yellow]")
            raise typer.Exit(0)

        console.print(f"\n[bold]Prompt Set[/bold] {bundle.prompt_set.name}\n")
        prompt_map = {prompt.prompt_id: prompt for prompt in bundle.prompts}
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Role")
        table.add_column("Kind")
        table.add_column("Name")
        table.add_column("Checksum", style="dim")
        for item in bundle.items:
            prompt = prompt_map.get(item.prompt_id)
            if not prompt:
                continue
            table.add_row(
                item.role,
                prompt.kind,
                prompt.name,
                prompt.checksum[:12],
            )
        console.print(table)
        console.print()

    @app.command("diff")
    def diff_prompt_sets(
        run_id_a: str = typer.Argument(..., help="Base run ID."),
        run_id_b: str = typer.Argument(..., help="Target run ID."),
        db_path: Path | None = db_option(help_text="Path to database file."),
        max_lines: int = typer.Option(
            40,
            "--max-lines",
            help="Maximum diff lines per prompt.",
        ),
        show_diff: bool = typer.Option(
            True,
            "--show-diff/--no-show-diff",
            help="Print unified diffs for changed prompts.",
        ),
    ) -> None:
        """Compare prompt snapshots between two runs."""
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        bundle_a = storage.get_prompt_set_for_run(run_id_a)
        bundle_b = storage.get_prompt_set_for_run(run_id_b)

        if not bundle_a or not bundle_b:
            console.print("[yellow]Prompt set not found for one or both runs.[/yellow]")
            raise typer.Exit(0)

        roles_a = _bundle_to_role_map(bundle_a)
        roles_b = _bundle_to_role_map(bundle_b)
        all_roles = sorted(set(roles_a) | set(roles_b))

        console.print("\n[bold]Prompt Diff Summary[/bold]\n")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Role")
        table.add_column("Run A", justify="left")
        table.add_column("Run B", justify="left")
        table.add_column("Status", justify="center")

        for role in all_roles:
            a = roles_a.get(role)
            b = roles_b.get(role)
            if not a and not b:
                continue
            if not a:
                if not b:
                    continue
                table.add_row(role, "-", b["checksum"][:12], "[yellow]missing[/yellow]")
                continue
            if not b:
                table.add_row(role, a["checksum"][:12], "-", "[yellow]missing[/yellow]")
                continue
            status = "same" if a["checksum"] == b["checksum"] else "diff"
            status_color = "green" if status == "same" else "red"
            table.add_row(
                role,
                a["checksum"][:12],
                b["checksum"][:12],
                f"[{status_color}]{status}[/{status_color}]",
            )

        console.print(table)

        if not show_diff:
            console.print()
            return

        for role in all_roles:
            a = roles_a.get(role)
            b = roles_b.get(role)
            if not a or not b or a["checksum"] == b["checksum"]:
                continue
            diff_lines = list(
                difflib.unified_diff(
                    a["content"].splitlines(),
                    b["content"].splitlines(),
                    fromfile=f"{run_id_a[:8]}:{role}",
                    tofile=f"{run_id_b[:8]}:{role}",
                    lineterm="",
                )
            )
            if not diff_lines:
                continue
            console.print(f"\n[bold]{role}[/bold]")
            for line in diff_lines[:max_lines]:
                console.print(line, markup=False)
            if len(diff_lines) > max_lines:
                console.print("[dim]... diff truncated ...[/dim]")
        console.print()

    @app.command("suggest")
    def suggest_prompt_candidates(
        run_id: str = typer.Argument(..., help="Run ID to analyze."),
        role: str | None = typer.Option(
            None,
            "--role",
            help="Prompt role to improve (system or metric name).",
        ),
        metrics: str | None = typer.Option(
            None,
            "--metrics",
            "-m",
            help="Comma-separated list of metrics to score (default: run metrics).",
        ),
        model: str | None = typer.Option(
            None,
            "--model",
            help="Override LLM model for regeneration/scoring.",
        ),
        provider: str | None = typer.Option(
            None,
            "--provider",
            help="Override LLM provider (openai|ollama|vllm|azure|anthropic).",
        ),
        temperature: float | None = typer.Option(
            None,
            "--temperature",
            help="Sampling temperature for regeneration.",
        ),
        top_p: float | None = typer.Option(
            None,
            "--top-p",
            help="Nucleus sampling top-p for regeneration.",
        ),
        max_tokens: int | None = typer.Option(
            None,
            "--max-tokens",
            help="Max completion tokens for regeneration.",
        ),
        generation_n: int | None = typer.Option(
            None,
            "--generation-n",
            help="Number of samples per regeneration.",
        ),
        generation_seed: int | None = typer.Option(
            None,
            "--generation-seed",
            help="Seed for regeneration sampling.",
        ),
        selection_policy: str = typer.Option(
            "best",
            "--selection-policy",
            help="Sample selection policy (best|index).",
        ),
        selection_index: int | None = typer.Option(
            None,
            "--selection-index",
            help="Sample index when using selection-policy=index.",
        ),
        weights: str | None = typer.Option(
            None,
            "--weights",
            help="Comma-separated metric weights (e.g. faithfulness=0.5,answer_relevancy=0.5).",
        ),
        candidates: int = typer.Option(
            5,
            "--candidates",
            help="Number of auto-generated candidates (default: 5).",
        ),
        manual_prompts: list[str] = typer.Option(
            [],
            "--prompt",
            help="Manual prompt candidate (repeatable).",
            show_default=False,
        ),
        manual_prompt_files: list[Path] = typer.Option(
            [],
            "--prompt-file",
            help="Manual prompt candidate file (repeatable).",
            exists=True,
            readable=True,
            show_default=False,
        ),
        auto: bool = typer.Option(
            True,
            "--auto/--no-auto",
            help="Enable auto candidate generation.",
        ),
        holdout_ratio: float = typer.Option(
            0.2,
            "--holdout-ratio",
            help="Holdout ratio for scoring (default: 0.2).",
        ),
        seed: int | None = typer.Option(
            None,
            "--seed",
            help="Random seed for holdout split.",
        ),
        output_path: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output JSON path.",
        ),
        report_path: Path | None = typer.Option(
            None,
            "--report",
            help="Markdown report path.",
        ),
        analysis_dir: Path | None = typer.Option(
            None,
            "--analysis-dir",
            help="Base directory for analysis outputs.",
        ),
        db_path: Path | None = db_option(help_text="Path to database file."),
    ) -> None:
        """Suggest prompt improvements by scoring candidate prompts."""

        storage = build_storage_adapter(settings=Settings(), db_path=db_path)

        try:
            run = storage.get_run(run_id)
        except KeyError as exc:
            print_cli_error(
                console,
                "Run을 찾지 못했습니다.",
                details=str(exc),
            )
            raise typer.Exit(1)

        bundle = storage.get_prompt_set_for_run(run_id)
        if not bundle:
            print_cli_error(
                console,
                "이 run에 연결된 프롬프트 스냅샷이 없습니다.",
                fixes=["`evalvault run` 실행 시 --db 옵션을 지정했는지 확인하세요."],
            )
            raise typer.Exit(1)

        roles = _bundle_to_role_map(bundle)
        resolved_role = role or _default_role(bundle)
        if not resolved_role:
            print_cli_error(
                console,
                "프롬프트 role을 결정할 수 없습니다.",
            )
            raise typer.Exit(1)
        if resolved_role not in roles:
            print_cli_error(
                console,
                "지정한 role의 프롬프트를 찾을 수 없습니다.",
                details=resolved_role,
                fixes=[f"사용 가능한 role: {', '.join(sorted(roles))}"],
            )
            raise typer.Exit(1)

        metric_list = parse_csv_option(metrics) or list(run.metrics_evaluated)
        if not metric_list:
            print_cli_error(
                console,
                "평가 메트릭이 없습니다.",
                fixes=["--metrics 옵션을 지정하세요."],
            )
            raise typer.Exit(1)

        if candidates <= 0:
            print_cli_error(
                console,
                "--candidates 값은 1 이상이어야 합니다.",
            )
            raise typer.Exit(1)

        if holdout_ratio <= 0 or holdout_ratio >= 1:
            print_cli_error(
                console,
                "--holdout-ratio 값은 0과 1 사이여야 합니다.",
            )
            raise typer.Exit(1)

        if not auto and not manual_prompts and not manual_prompt_files:
            print_cli_error(
                console,
                "자동 후보를 끌 경우 수동 후보가 필요합니다.",
                fixes=["--prompt 또는 --prompt-file을 추가하세요."],
            )
            raise typer.Exit(1)

        if temperature is not None and temperature < 0:
            print_cli_error(
                console,
                "--temperature 값은 0 이상이어야 합니다.",
            )
            raise typer.Exit(1)
        if top_p is not None and (top_p <= 0 or top_p > 1):
            print_cli_error(
                console,
                "--top-p 값은 0보다 크고 1 이하여야 합니다.",
            )
            raise typer.Exit(1)
        if max_tokens is not None and max_tokens <= 0:
            print_cli_error(
                console,
                "--max-tokens 값은 1 이상이어야 합니다.",
            )
            raise typer.Exit(1)
        if generation_n is not None and generation_n <= 0:
            print_cli_error(
                console,
                "--generation-n 값은 1 이상이어야 합니다.",
            )
            raise typer.Exit(1)
        if generation_seed is not None and generation_seed < 0:
            print_cli_error(
                console,
                "--generation-seed 값은 0 이상이어야 합니다.",
            )
            raise typer.Exit(1)

        selection_policy = selection_policy.strip().lower()
        if selection_policy not in {"best", "index"}:
            print_cli_error(
                console,
                "--selection-policy 값이 올바르지 않습니다.",
                fixes=["best 또는 index로 지정하세요."],
            )
            raise typer.Exit(1)

        sample_count = generation_n or 1
        if selection_policy == "index":
            if selection_index is None:
                print_cli_error(
                    console,
                    "--selection-index 값이 필요합니다.",
                )
                raise typer.Exit(1)
            if selection_index < 0 or selection_index >= sample_count:
                print_cli_error(
                    console,
                    "--selection-index 값이 범위를 벗어났습니다.",
                    fixes=[f"0부터 {sample_count - 1} 사이로 지정하세요."],
                )
                raise typer.Exit(1)
        elif selection_index is not None:
            print_cli_error(
                console,
                "--selection-index는 selection-policy=index에서만 사용됩니다.",
            )
            raise typer.Exit(1)

        weights_map = _parse_weights(console, weights, metric_list)
        base_prompt = roles[resolved_role]["content"]

        dataset = _build_dataset_from_run(run, console)
        if not dataset.test_cases:
            print_cli_error(
                console,
                "평가 데이터셋이 비어 있어 추천을 생성할 수 없습니다.",
            )
            raise typer.Exit(1)

        try:
            from evalvault.domain.entities.prompt_suggestion import PromptSuggestionResult
            from evalvault.domain.services.holdout_splitter import split_dataset_holdout
            from evalvault.domain.services.prompt_candidate_service import PromptCandidateService
            from evalvault.domain.services.prompt_scoring_service import PromptScoringService
            from evalvault.domain.services.prompt_suggestion_reporter import (
                PromptSuggestionReporter,
            )
        except ModuleNotFoundError as exc:
            print_cli_error(
                console,
                "프롬프트 추천 모듈을 찾을 수 없습니다.",
                details=str(exc),
            )
            raise typer.Exit(1)

        settings = Settings()
        if settings.evalvault_profile:
            settings = apply_profile(settings, settings.evalvault_profile)

        settings, resolved_provider, resolved_model = _resolve_llm_config(
            settings=settings,
            run_model=run.model_name,
            model_override=model,
            provider_override=provider,
            console=console,
        )

        llm_adapter = get_llm_adapter(settings)
        llm_factory = SettingsLLMFactory(settings)
        korean_toolkit = try_create_korean_toolkit()
        evaluator = RagasEvaluator(korean_toolkit=korean_toolkit, llm_factory=llm_factory)
        generation_options = GenerationOptions(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            n=generation_n,
            seed=generation_seed,
        )

        dev_dataset, holdout_dataset = split_dataset_holdout(
            dataset=dataset,
            holdout_ratio=holdout_ratio,
            seed=seed,
        )

        prefix = f"prompt_suggestions_{run_id}"
        output_path, report_path = resolve_output_paths(
            base_dir=analysis_dir,
            output_path=output_path,
            report_path=report_path,
            prefix=prefix,
        )
        artifacts_dir = resolve_artifact_dir(
            base_dir=analysis_dir,
            output_path=output_path,
            report_path=report_path,
            prefix=prefix,
        )

        candidate_service = PromptCandidateService()
        scoring_service = PromptScoringService(evaluator=evaluator, llm=llm_adapter)
        reporter = PromptSuggestionReporter()

        with progress_spinner(console, "후보 생성 중...") as update:
            candidates_list = candidate_service.build_candidates(
                base_prompt=base_prompt,
                role=resolved_role,
                metrics=metric_list,
                manual_prompts=list(manual_prompts),
                manual_prompt_files=list(manual_prompt_files),
                auto=auto,
                auto_count=candidates,
                metadata={"run_id": run_id},
            )
            if not candidates_list:
                print_cli_error(
                    console,
                    "후보 프롬프트가 생성되지 않았습니다.",
                )
                raise typer.Exit(1)

            update("후보 평가 중...")
            scores = asyncio.run(
                scoring_service.score_candidates(
                    base_run=run,
                    dev_dataset=dev_dataset,
                    holdout_dataset=holdout_dataset,
                    candidates=candidates_list,
                    metrics=metric_list,
                    weights=weights_map,
                    generation_options=generation_options,
                    selection_policy=selection_policy,
                    selection_index=selection_index,
                )
            )

            ranking = _rank_candidates(scores)
            result = PromptSuggestionResult(
                run_id=run_id,
                role=resolved_role,
                metrics=metric_list,
                weights=weights_map,
                candidates=candidates_list,
                scores=scores,
                ranking=ranking,
                holdout_ratio=holdout_ratio,
                metadata={
                    "seed": seed,
                    "model": resolved_model,
                    "provider": resolved_provider,
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_tokens": max_tokens,
                    "generation_n": generation_n,
                    "generation_seed": generation_seed,
                    "selection_policy": selection_policy,
                    "selection_index": selection_index,
                },
            )

            update("결과 저장 중...")
            reporter.write_outputs(
                result=result,
                output_path=output_path,
                report_path=report_path,
                artifacts_dir=artifacts_dir,
                storage=storage,
            )

        score_map = {score.candidate_id: score for score in scores}
        candidate_map = {candidate.candidate_id: candidate for candidate in candidates_list}
        console.print("\n[bold]추천 결과[/bold]")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Rank", justify="right")
        table.add_column("Candidate", style="dim")
        table.add_column("Source")
        table.add_column("Score", justify="right")
        for idx, candidate_id in enumerate(ranking[:5], start=1):
            candidate = candidate_map.get(candidate_id)
            score = score_map.get(candidate_id)
            if not candidate or not score:
                continue
            preview = candidate.content.replace("\n", " ")[:60]
            table.add_row(
                str(idx),
                preview,
                candidate.source,
                f"{score.weighted_score:.4f}",
            )
        console.print(table)
        console.print(f"\n[green]JSON[/green] {output_path}")
        console.print(f"[green]Report[/green] {report_path}\n")

    return app


__all__ = ["create_prompts_app"]
