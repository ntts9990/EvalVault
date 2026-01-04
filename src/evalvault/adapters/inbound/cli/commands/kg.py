"""Knowledge graph utilities for the EvalVault CLI."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.kg.parallel_kg_builder import (
    KGBuilderStats,
    KGBuildResult,
    ParallelKGBuilder,
)
from evalvault.adapters.outbound.llm import LLMRelationAugmenter, get_llm_adapter
from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.services.kg_generator import KnowledgeGraphGenerator

from ..utils.options import profile_option


def create_kg_app(console: Console) -> typer.Typer:
    """Create the Typer sub-application for knowledge graph commands."""

    kg_app = typer.Typer(name="kg", help="Knowledge graph utilities.")

    @kg_app.command("stats")
    def kg_stats(
        source: Path = typer.Argument(
            ...,
            exists=True,
            readable=True,
            help="단일 파일 또는 디렉터리. 디렉터리는 .txt/.md 파일을 재귀적으로 읽습니다.",
        ),
        profile: str | None = profile_option(help_text="LLM 프로필 (필요 시)."),
        use_llm: bool = typer.Option(
            False,
            "--use-llm",
            "-L",
            help="LLM 보강기를 사용해 저신뢰 관계를 검증합니다.",
        ),
        threshold: float = typer.Option(
            0.6,
            "--threshold",
            "-T",
            help="LLM 보강을 트리거할 confidence 임계값 (0~1).",
        ),
        log_langfuse: bool = typer.Option(
            True,
            "--langfuse/--no-langfuse",
            help="Langfuse에 그래프 통계를 기록할지 여부.",
        ),
        report_file: Path | None = typer.Option(
            None,
            "--report-file",
            "-r",
            help="그래프 통계를 JSON 파일로 저장.",
        ),
    ) -> None:
        """문서 집합으로 지식그래프를 구축하고 통계를 출력."""

        if not 0 < threshold <= 1:
            console.print("[red]Error:[/red] threshold는 0~1 사이여야 합니다.")
            raise typer.Exit(1)

        settings = Settings()
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        relation_augmenter = None
        if use_llm:
            if settings.llm_provider == "openai" and not settings.openai_api_key:
                console.print("[red]Error:[/red] OPENAI_API_KEY not set for LLM augmentation.")
                raise typer.Exit(1)
            relation_augmenter = LLMRelationAugmenter(get_llm_adapter(settings))

        try:
            documents = _load_documents_from_source(source)
        except Exception as exc:  # pragma: no cover - defensive logging
            console.print(f"[red]Error loading documents:[/red] {exc}")
            raise typer.Exit(1) from exc

        if not documents:
            console.print("[red]Error:[/red] 문서를 읽을 수 없습니다. 파일 내용을 확인하세요.")
            raise typer.Exit(1)

        console.print(f"[bold]Building knowledge graph from {len(documents)} documents...[/bold]")
        generator = KnowledgeGraphGenerator(
            relation_augmenter=relation_augmenter,
            low_confidence_threshold=threshold,
        )
        generator.build_graph(documents)
        stats = generator.get_statistics()
        _display_kg_stats(stats, console)

        if report_file:
            _save_kg_report(report_file, stats, source, profile_name, use_llm)
            console.print(f"[green]Saved KG report to {report_file}[/green]")

        trace_id = None
        if log_langfuse:
            trace_id = _log_kg_stats_to_langfuse(
                settings=settings,
                stats=stats,
                source=source,
                profile=profile_name,
                use_llm=use_llm,
                console=console,
            )
        if trace_id:
            console.print(f"[cyan]Langfuse trace ID:[/cyan] {trace_id}")

    @kg_app.command("build")
    def kg_build(
        source: Path = typer.Argument(
            ...,
            exists=True,
            readable=True,
            help="문서 파일 또는 디렉터리 경로.",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="그래프를 JSON으로 저장할 경로.",
        ),
        workers: int = typer.Option(
            4,
            "--workers",
            "-w",
            min=1,
            help="병렬 처리 워커 수 (기본값: 4).",
        ),
        batch_size: int = typer.Option(
            32,
            "--batch-size",
            "-b",
            min=1,
            help="배치 크기 (기본값: 32).",
        ),
        store_documents: bool = typer.Option(
            False,
            "--store-documents",
            help="원본 문서를 결과에 포함할지 여부.",
        ),
        verbose: bool = typer.Option(
            False,
            "--verbose",
            "-v",
            help="상세 진행 메시지 표시.",
        ),
    ) -> None:
        """문서 집합으로 지식그래프를 병렬 구축합니다."""

        try:
            documents = _load_documents_from_source(source)
        except Exception as exc:  # pragma: no cover - defensive logging
            console.print(f"[red]Error loading documents:[/red] {exc}")
            raise typer.Exit(1) from exc

        if not documents:
            console.print("[red]Error:[/red] 문서를 읽을 수 없습니다. 파일 내용을 확인하세요.")
            raise typer.Exit(1)

        console.print(
            f"[bold]Building knowledge graph from {len(documents)} documents "
            f"(workers={workers}, batch_size={batch_size})...[/bold]"
        )

        def progress_callback(stats: KGBuilderStats) -> None:
            if verbose:
                console.print(
                    f"  [dim]Chunk {stats.chunks_processed}: "
                    f"{stats.documents_processed} docs, "
                    f"{stats.entities_added} entities, "
                    f"{stats.relations_added} relations[/dim]"
                )

        builder = ParallelKGBuilder(
            workers=workers,
            batch_size=batch_size,
            store_documents=store_documents,
            progress_callback=progress_callback if verbose else None,
        )

        result = builder.build(documents)
        _display_build_result(result, console)

        if output:
            _save_build_result(output, result, source, workers, batch_size, store_documents)
            console.print(f"[green]Saved KG build result to {output}[/green]")

    return kg_app


def _load_documents_from_source(source: Path) -> list[str]:
    """입력 경로에서 문서 리스트를 로드."""

    if source.is_dir():
        documents = []
        for path in sorted(source.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".txt", ".md"}:
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    documents.append(text)
        return documents

    text = source.read_text(encoding="utf-8").strip()
    suffix = source.suffix.lower()

    if suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            pass
        else:
            documents: list[str] = []
            if isinstance(data, list):
                documents.extend(_extract_texts_from_sequence(data))
            elif isinstance(data, dict):
                documents.extend(_extract_texts_from_mapping(data))
            if documents:
                return documents

    if suffix in {".csv", ".tsv"}:
        return [line for line in text.splitlines() if line.strip()]

    paragraphs = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    if len(paragraphs) > 1:
        return paragraphs
    return [text] if text else []


def _extract_texts_from_sequence(items: list[Any]) -> list[str]:
    """JSON 시퀀스에서 텍스트 필드 추출."""

    documents: list[str] = []
    for item in items:
        if isinstance(item, str):
            documents.append(item)
        elif isinstance(item, dict):
            for key in ("content", "text", "body"):
                value = item.get(key)
                if isinstance(value, str):
                    documents.append(value)
                    break
    return documents


def _extract_texts_from_mapping(data: dict[str, Any]) -> list[str]:
    """JSON 매핑에서 텍스트 필드 추출."""

    documents: list[str] = []
    for key in ("content", "text", "body"):
        value = data.get(key)
        if isinstance(value, str):
            documents.append(value)
    if "documents" in data and isinstance(data["documents"], list):
        documents.extend(_extract_texts_from_sequence(data["documents"]))
    return documents


def _display_kg_stats(stats: dict, console: Console | None = None) -> None:
    """Rich 테이블로 그래프 통계를 출력."""

    console = console or Console()

    summary = Table(title="Knowledge Graph Overview", show_header=False)
    summary.add_column("Metric", style="bold", justify="left")
    summary.add_column("Value", justify="right")

    summary.add_row("Entities", str(stats.get("num_entities", 0)))
    summary.add_row("Relations", str(stats.get("num_relations", 0)))
    isolated = stats.get("isolated_entities", [])
    summary.add_row("Isolated Entities", str(len(isolated)))

    build_metrics = stats.get("build_metrics", {})
    summary.add_row("Documents Processed", str(build_metrics.get("documents_processed", 0)))
    summary.add_row("Entities Added", str(build_metrics.get("entities_added", 0)))
    summary.add_row("Relations Added", str(build_metrics.get("relations_added", 0)))
    console.print(summary)

    if stats.get("entity_types"):
        entity_table = Table(title="Entity Types", show_header=True, header_style="bold cyan")
        entity_table.add_column("Type")
        entity_table.add_column("Count", justify="right")
        for entity_type, count in sorted(stats["entity_types"].items()):
            entity_table.add_row(entity_type, str(count))
        console.print(entity_table)

    if stats.get("relation_types"):
        relation_table = Table(title="Relation Types", show_header=True, header_style="bold cyan")
        relation_table.add_column("Type")
        relation_table.add_column("Count", justify="right")
        for relation_type, count in sorted(stats["relation_types"].items()):
            relation_table.add_row(relation_type, str(count))
        console.print(relation_table)

    if isolated:
        preview = ", ".join(isolated[:5])
        console.print(
            f"[yellow]Isolated entities ({len(isolated)}):[/yellow] "
            f"{preview}{'...' if len(isolated) > 5 else ''}"
        )

    if stats.get("sample_entities"):
        sample_table = Table(title="Sample Entities", show_header=True, header_style="bold magenta")
        sample_table.add_column("Name")
        sample_table.add_column("Type")
        sample_table.add_column("Confidence", justify="right")
        sample_table.add_column("Source")
        for entity in stats["sample_entities"]:
            sample_table.add_row(
                entity.get("name", ""),
                entity.get("entity_type", ""),
                f"{entity.get('confidence', 0):.2f}",
                entity.get("provenance", ""),
            )
        console.print(sample_table)

    if stats.get("sample_relations"):
        rel_table = Table(title="Sample Relations", show_header=True, header_style="bold magenta")
        rel_table.add_column("Source")
        rel_table.add_column("Relation")
        rel_table.add_column("Target")
        rel_table.add_column("Confidence", justify="right")
        for relation in stats["sample_relations"]:
            rel_table.add_row(
                relation.get("source", ""),
                relation.get("relation_type", ""),
                relation.get("target", ""),
                f"{relation.get('confidence', 0):.2f}",
            )
        console.print(rel_table)


def _log_kg_stats_to_langfuse(
    settings: Settings,
    stats: dict,
    source: Path,
    profile: str | None,
    use_llm: bool,
    console: Console | None = None,
) -> str | None:
    """Langfuse에 그래프 통계를 전송."""

    console = console or Console()

    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        console.print("[yellow]Langfuse credentials not set; skipping logging.[/yellow]")
        return None

    try:
        tracker = LangfuseAdapter(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        metadata = {
            "source": str(source),
            "profile": profile,
            "use_llm": use_llm,
            "num_entities": stats.get("num_entities"),
            "num_relations": stats.get("num_relations"),
            "documents_processed": stats.get("build_metrics", {}).get("documents_processed"),
            "event_type": "kg_stats",
        }
        trace_id = tracker.start_trace(name="kg_stats", metadata=metadata)
        payload = {
            "type": "kg_stats",
            "context": {
                "source": str(source),
                "profile": profile,
                "use_llm": use_llm,
            },
            "stats": stats,
        }
        tracker.save_artifact(trace_id, "kg_statistics", payload, artifact_type="json")
        tracker.add_span(
            trace_id=trace_id,
            name="entity_type_distribution",
            output_data=stats.get("entity_types"),
        )
        tracker.add_span(
            trace_id=trace_id,
            name="relation_type_distribution",
            output_data=stats.get("relation_types"),
        )
        if stats.get("isolated_entities"):
            tracker.add_span(
                trace_id=trace_id,
                name="isolated_entities",
                output_data=stats.get("isolated_entities"),
            )
        tracker.end_trace(trace_id)
        console.print("[green]Logged knowledge graph stats to Langfuse[/green]")
        return trace_id
    except Exception as exc:  # pragma: no cover - defensive logging
        console.print(f"[yellow]Warning:[/yellow] Failed to log to Langfuse: {exc}")
        return None


def _save_kg_report(
    output: Path,
    stats: dict,
    source: Path,
    profile: str | None,
    use_llm: bool,
) -> None:
    """kg stats 결과를 JSON 파일로 저장."""

    payload = {
        "type": "kg_stats_report",
        "generated_at": datetime.now().isoformat(),
        "source": str(source),
        "profile": profile,
        "use_llm": use_llm,
        "stats": stats,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _display_build_result(result: KGBuildResult, console: Console) -> None:
    """ParallelKGBuilder 결과를 Rich 테이블로 출력."""

    stats = result.stats
    graph_stats = result.graph.get_statistics()

    # Build summary table
    summary = Table(title="KG Build Summary", show_header=False)
    summary.add_column("Metric", style="bold", justify="left")
    summary.add_column("Value", justify="right")

    summary.add_row("Documents Processed", str(stats.documents_processed))
    summary.add_row("Entities Processed", str(stats.entities_processed))
    summary.add_row("Entities Added", str(stats.entities_added))
    summary.add_row("Relations Added", str(stats.relations_added))
    summary.add_row("Chunks Processed", str(stats.chunks_processed))
    summary.add_row("Elapsed Time (ms)", f"{stats.elapsed_ms:.2f}")
    console.print(summary)

    # Graph statistics
    graph_table = Table(title="Graph Statistics", show_header=False)
    graph_table.add_column("Metric", style="bold", justify="left")
    graph_table.add_column("Value", justify="right")

    graph_table.add_row("Total Entities", str(graph_stats.get("num_entities", 0)))
    graph_table.add_row("Total Relations", str(graph_stats.get("num_relations", 0)))
    # isolated_entities can be int (from NetworkXKnowledgeGraph) or list
    isolated = graph_stats.get("isolated_entities", 0)
    isolated_count = isolated if isinstance(isolated, int) else len(isolated)
    graph_table.add_row("Isolated Entities", str(isolated_count))
    console.print(graph_table)

    # Entity types
    entity_types = graph_stats.get("entity_types", {})
    if entity_types:
        entity_table = Table(title="Entity Types", show_header=True, header_style="bold cyan")
        entity_table.add_column("Type")
        entity_table.add_column("Count", justify="right")
        for entity_type, count in sorted(entity_types.items()):
            entity_table.add_row(entity_type, str(count))
        console.print(entity_table)

    # Relation types
    relation_types = graph_stats.get("relation_types", {})
    if relation_types:
        relation_table = Table(title="Relation Types", show_header=True, header_style="bold cyan")
        relation_table.add_column("Type")
        relation_table.add_column("Count", justify="right")
        for relation_type, count in sorted(relation_types.items()):
            relation_table.add_row(relation_type, str(count))
        console.print(relation_table)

    # Isolated entities preview (only if list is available)
    if isinstance(isolated, list) and isolated:
        preview = ", ".join(isolated[:5])
        console.print(
            f"[yellow]Isolated entities ({len(isolated)}):[/yellow] "
            f"{preview}{'...' if len(isolated) > 5 else ''}"
        )


def _save_build_result(
    output: Path,
    result: KGBuildResult,
    source: Path,
    workers: int,
    batch_size: int,
    store_documents: bool,
) -> None:
    """kg build 결과를 JSON 파일로 저장."""

    payload: dict[str, Any] = {
        "type": "kg_build_result",
        "generated_at": datetime.now().isoformat(),
        "source": str(source),
        "config": {
            "workers": workers,
            "batch_size": batch_size,
            "store_documents": store_documents,
        },
        "stats": result.stats.snapshot(),
        "graph": result.graph.to_dict(),
    }

    if store_documents and result.documents_by_id:
        payload["documents"] = result.documents_by_id

    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = [
    "create_kg_app",
    "_load_documents_from_source",
    "_extract_texts_from_sequence",
    "_extract_texts_from_mapping",
    "_display_kg_stats",
    "_log_kg_stats_to_langfuse",
    "_save_kg_report",
    "_display_build_result",
    "_save_build_result",
]
