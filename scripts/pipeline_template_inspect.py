#!/usr/bin/env python
"""Utility script to inspect registered analysis pipeline templates."""

from __future__ import annotations

import argparse

from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
from evalvault.domain.services.pipeline_template_registry import PipelineTemplateRegistry


def resolve_intents(value: str | None) -> list[AnalysisIntent]:
    """Resolve user input into a list of AnalysisIntent values."""
    if value is None or value.lower() in {"all", "any"}:
        return list(AnalysisIntent)

    normalized = value.lower()
    for intent in AnalysisIntent:
        if intent.name.lower() == normalized or intent.value == normalized:
            return [intent]

    raise ValueError(
        f"Unknown intent '{value}'. "
        f"Valid values: {[intent.name.lower() for intent in AnalysisIntent]}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect DAG templates registered for analysis intents.",
    )
    parser.add_argument(
        "--intent",
        "-i",
        help="Intent name or value (e.g., GENERATE_SUMMARY, analyze_low_metrics, all).",
    )
    args = parser.parse_args()

    intents = resolve_intents(args.intent)
    registry = PipelineTemplateRegistry()

    for intent in intents:
        template = registry.get_template(intent)
        if not template:
            print(f"[{intent.value}] No template registered.")
            continue

        print(f"[{intent.value}] {len(template.nodes)} nodes / {len(template.edges)} edges")
        for node in template.nodes:
            deps = ", ".join(node.depends_on) if node.depends_on else "-"
            print(f"  • {node.name} ({node.module}) deps: {deps}")
        print()


if __name__ == "__main__":
    main()
