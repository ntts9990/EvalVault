"""Command registration helpers for the EvalVault CLI package."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import typer
from rich.console import Console

from .agent import register_agent_commands
from .analyze import register_analyze_commands
from .api import register_api_command
from .artifacts import create_artifacts_app
from .benchmark import create_benchmark_app
from .calibrate import register_calibrate_commands
from .calibrate_judge import register_calibrate_judge_commands
from .compare import register_compare_commands
from .config import register_config_commands
from .debug import create_debug_app
from .domain import create_domain_app
from .experiment import register_experiment_commands
from .gate import register_gate_commands
from .generate import register_generate_commands
from .graph_rag import create_graph_rag_app
from .history import register_history_commands
from .init import register_init_command
from .kg import create_kg_app
from .langfuse import register_langfuse_commands
from .method import create_method_app
from .ops import create_ops_app
from .phoenix import create_phoenix_app
from .pipeline import register_pipeline_commands
from .profile_difficulty import register_profile_difficulty_commands
from .prompts import create_prompts_app
from .regress import register_regress_commands
from .run import register_run_commands
from .stage import create_stage_app

CommandFactory = Callable[[Console], typer.Typer]
CommandRegistrar = Callable[..., Any]


@dataclass(frozen=True)
class CommandModule:
    """Descriptor that captures how to register a CLI module."""

    registrar: CommandRegistrar
    needs_metrics: bool = False


@dataclass(frozen=True)
class SubAppModule:
    """Descriptor for Typer sub-applications."""

    name: str
    factory: CommandFactory


COMMAND_MODULES: tuple[CommandModule, ...] = (
    CommandModule(register_init_command),
    CommandModule(register_run_commands, needs_metrics=True),
    CommandModule(register_pipeline_commands),
    CommandModule(register_history_commands),
    CommandModule(register_compare_commands),
    CommandModule(register_analyze_commands),
    CommandModule(register_calibrate_commands),
    CommandModule(register_calibrate_judge_commands),
    CommandModule(register_generate_commands),
    CommandModule(register_gate_commands),
    CommandModule(register_profile_difficulty_commands, needs_metrics=True),
    CommandModule(register_regress_commands),
    CommandModule(register_agent_commands),
    CommandModule(register_experiment_commands),
    CommandModule(register_config_commands),
    CommandModule(register_langfuse_commands),
    CommandModule(register_api_command),
)


SUB_APPLICATIONS: tuple[SubAppModule, ...] = (
    SubAppModule("kg", create_kg_app),
    SubAppModule("domain", create_domain_app),
    SubAppModule("benchmark", create_benchmark_app),
    SubAppModule("graphrag", create_graph_rag_app),
    SubAppModule("method", create_method_app),
    SubAppModule("ops", create_ops_app),
    SubAppModule("phoenix", create_phoenix_app),
    SubAppModule("prompts", create_prompts_app),
    SubAppModule("stage", create_stage_app),
    SubAppModule("artifacts", create_artifacts_app),
    SubAppModule("debug", create_debug_app),
)


def register_all_commands(
    app: typer.Typer,
    console: Console,
    *,
    available_metrics: list[str] | tuple[str, ...],
) -> None:
    """Register every root-level command module."""

    for module in COMMAND_MODULES:
        kwargs: dict[str, Any] = {}
        if module.needs_metrics:
            kwargs["available_metrics"] = available_metrics
        module.registrar(app, console, **kwargs)


def attach_sub_apps(app: typer.Typer, console: Console) -> None:
    """Attach every Typer sub-app under its prefix."""

    for sub_app in SUB_APPLICATIONS:
        app.add_typer(sub_app.factory(console), name=sub_app.name)


__all__ = [
    "register_all_commands",
    "attach_sub_apps",
    "COMMAND_MODULES",
    "SUB_APPLICATIONS",
]
