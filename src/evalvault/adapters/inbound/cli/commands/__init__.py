"""Command registration helpers for the EvalVault CLI package."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import typer
from rich.console import Console

from .agent import register_agent_commands
from .analyze import register_analyze_commands
from .benchmark import create_benchmark_app
from .config import register_config_commands
from .domain import create_domain_app
from .experiment import register_experiment_commands
from .gate import register_gate_commands
from .generate import register_generate_commands
from .history import register_history_commands
from .kg import create_kg_app
from .langfuse import register_langfuse_commands
from .phoenix import create_phoenix_app
from .pipeline import register_pipeline_commands
from .run import register_run_commands
from .web import register_web_command

CommandFactory = Callable[[Console], typer.Typer]


class CommandRegistrar(Protocol):
    """Callable protocol for Typer command registrars."""

    def __call__(self, app: typer.Typer, console: Console, **kwargs: Any) -> None: ...


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
    CommandModule(register_run_commands, needs_metrics=True),
    CommandModule(register_pipeline_commands),
    CommandModule(register_history_commands),
    CommandModule(register_analyze_commands),
    CommandModule(register_generate_commands),
    CommandModule(register_gate_commands),
    CommandModule(register_agent_commands),
    CommandModule(register_experiment_commands),
    CommandModule(register_config_commands),
    CommandModule(register_langfuse_commands),
    CommandModule(register_web_command),
)


SUB_APPLICATIONS: tuple[SubAppModule, ...] = (
    SubAppModule("kg", create_kg_app),
    SubAppModule("domain", create_domain_app),
    SubAppModule("benchmark", create_benchmark_app),
    SubAppModule("phoenix", create_phoenix_app),
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
