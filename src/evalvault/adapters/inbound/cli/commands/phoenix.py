"""Phoenix helper commands (dataset exports, observability tooling)."""

from __future__ import annotations

import asyncio
import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.llm import get_llm_adapter
from evalvault.adapters.outbound.llm.base import LLMConfigurationError
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.services.prompt_manifest import (
    load_prompt_manifest,
    record_prompt_entry,
    save_prompt_manifest,
    summarize_prompts,
)

PhoenixApp = typer.Typer(
    help="Utilities for working with Phoenix datasets and experiments.",
    add_completion=False,
)


def _import_phoenix_client() -> Any:
    try:
        from phoenix.client import Client
    except ImportError as exc:  # pragma: no cover - defensive path
        raise typer.BadParameter(
            "Phoenix client not installed. Run `uv sync --extra phoenix` and retry."
        ) from exc
    return Client


def _flatten_accessors(payload: dict[str, Any] | None) -> str:
    if not payload:
        return ""
    try:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return str(payload)


def _join_contexts(input_block: dict[str, Any]) -> str:
    contexts = input_block.get("contexts")
    if isinstance(contexts, list | tuple):
        return " ".join(str(item) for item in contexts if item)
    if isinstance(contexts, str):
        return contexts
    return ""


def _extract_question(input_block: dict[str, Any]) -> str:
    for candidate in ("question", "prompt", "query"):
        value = input_block.get(candidate)
        if isinstance(value, str):
            return value
    # fallback: first string value
    for value in input_block.values():
        if isinstance(value, str):
            return value
    return ""


def _extract_answer(output_block: dict[str, Any]) -> str:
    for candidate in ("answer", "response", "completion"):
        value = output_block.get(candidate)
        if isinstance(value, str):
            return value
    for value in output_block.values():
        if isinstance(value, str):
            return value
    return ""


def _reduce_to_2d(features):
    try:
        import umap  # type: ignore

        reducer = umap.UMAP(n_components=2, random_state=42)
        return reducer.fit_transform(features)
    except ImportError:
        from sklearn.decomposition import PCA

        matrix = features.toarray() if hasattr(features, "toarray") else features
        reducer = PCA(n_components=2, random_state=42)
        return reducer.fit_transform(matrix)


def _cluster_points(points):
    try:
        import hdbscan  # type: ignore

        clusterer = hdbscan.HDBSCAN(min_cluster_size=max(5, len(points) // 20 or 1))
        return clusterer.fit_predict(points)
    except ImportError:
        from sklearn.cluster import DBSCAN

        clusterer = DBSCAN(eps=0.5, min_samples=min(5, len(points)))
        return clusterer.fit_predict(points)


def _export_rows_to_csv(rows: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _export_rows_to_parquet(rows: list[dict[str, Any]], output: Path) -> None:
    try:
        import pandas as pd  # type: ignore
    except ImportError as exc:  # pragma: no cover - defensive
        raise typer.BadParameter(
            "Saving as Parquet requires pandas. Install via `uv pip install pandas pyarrow`."
        ) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_parquet(output, index=False)


def _apply_profile_from_env(settings: Settings) -> Settings:
    profile_name = settings.evalvault_profile
    if profile_name:
        return apply_profile(settings, profile_name)
    return settings


def _resolve_embedding_model_name(settings: Settings) -> str:
    provider = settings.llm_provider
    if provider == "ollama":
        return settings.ollama_embedding_model
    if provider == "azure":
        return settings.azure_embedding_deployment or ""
    return settings.openai_embedding_model


def _override_embedding_model(settings: Settings, embedding_model: str) -> None:
    provider = settings.llm_provider
    if provider == "ollama":
        settings.ollama_embedding_model = embedding_model
    elif provider == "azure":
        settings.azure_embedding_deployment = embedding_model
    else:
        settings.openai_embedding_model = embedding_model


def _run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError as exc:
        raise typer.BadParameter(
            "Async embeddings require a standalone event loop. "
            "Run this command from the CLI or use --embedding-mode tfidf."
        ) from exc


def _embed_texts(embeddings: Any, texts: list[str]) -> list[list[float]]:
    if hasattr(embeddings, "embed_texts"):
        return embeddings.embed_texts(texts)
    if hasattr(embeddings, "embed_documents"):
        return embeddings.embed_documents(texts)
    if hasattr(embeddings, "aembed_texts"):
        return _run_async(embeddings.aembed_texts(texts))
    if hasattr(embeddings, "aembed_documents"):
        return _run_async(embeddings.aembed_documents(texts))
    raise typer.BadParameter("Embedding backend does not support embed_texts().")


def _truncate_text(text: str, max_chars: int | None) -> str:
    if max_chars is None or max_chars <= 0:
        return text
    return text[:max_chars]


@PhoenixApp.command("export-embeddings")
def export_embeddings(  # noqa: PLR0913
    dataset: str = typer.Option(..., "--dataset", "-d", help="Phoenix dataset ID or name."),
    endpoint: str = typer.Option(
        "http://localhost:6006",
        "--endpoint",
        help="Phoenix REST endpoint (base URL, without /v1/traces).",
    ),
    api_token: str | None = typer.Option(
        None, "--api-token", help="Phoenix API token (Phoenix Cloud only)."
    ),
    output: Path = typer.Option(
        Path("phoenix_embeddings.csv"),
        "--output",
        "-o",
        help="Destination file (CSV or Parquet).",
    ),
    embedding_mode: str = typer.Option(
        "model",
        "--embedding-mode",
        help="Embedding backend: model or tfidf.",
        case_sensitive=False,
    ),
    embedding_model: str | None = typer.Option(
        None,
        "--embedding-model",
        help="Override the embedding model name for model mode.",
    ),
    batch_size: int = typer.Option(
        64,
        "--batch-size",
        "-b",
        help="Batch size for embedding requests (model mode).",
    ),
    max_chars: int | None = typer.Option(
        None,
        "--max-chars",
        help="Optional max characters per example (truncate before embedding).",
    ),
    fmt: str = typer.Option(
        "csv",
        "--format",
        "-f",
        help="Output format: csv or parquet.",
        case_sensitive=False,
    ),
) -> None:
    """Export Phoenix dataset examples with 2D projections for offline analysis."""

    console = Console()
    client_cls = _import_phoenix_client()
    client = client_cls(base_url=endpoint, api_key=api_token)
    fmt_lower = fmt.lower()
    embedding_mode_value = embedding_mode.lower()
    if embedding_mode_value not in {"model", "tfidf"}:
        raise typer.BadParameter("Embedding mode must be 'model' or 'tfidf'.")

    with console.status("[bold green]Fetching dataset from Phoenix..."):
        dataset_obj = client.datasets.get_dataset(dataset=dataset)
        examples = list(dataset_obj.examples)
    if not examples:
        console.print("[yellow]Dataset contains no examples.[/yellow]")
        raise typer.Exit(0)

    texts = []
    rows: list[dict[str, Any]] = []
    for idx, example in enumerate(examples):
        input_block = dict(example.get("input") or {})
        output_block = dict(example.get("output") or {})
        metadata = example.get("metadata") or {}
        question = _extract_question(input_block)
        answer = _extract_answer(output_block)
        contexts = _join_contexts(input_block)
        text_blob = " ".join(
            part for part in (question, answer, contexts, _flatten_accessors(metadata)) if part
        )
        text_blob = text_blob or f"{question} {answer} {contexts}"
        text_blob = _truncate_text(text_blob.strip(), max_chars)
        texts.append(text_blob or "empty")
        rows.append(
            {
                "example_id": example.get("example_id")
                or example.get("id")
                or f"{dataset_obj.name}-{idx}",
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "metadata": _flatten_accessors(metadata),
            }
        )

    if embedding_mode_value == "tfidf":
        console.print(f"[dim]Computing TF-IDF vectors for {len(texts)} examples...[/dim]")
        from sklearn.feature_extraction.text import TfidfVectorizer

        vectorizer = TfidfVectorizer(max_features=4096)
        vectors = vectorizer.fit_transform(texts)
    else:
        settings = _apply_profile_from_env(Settings())
        if embedding_model:
            _override_embedding_model(settings, embedding_model)

        try:
            llm_adapter = get_llm_adapter(settings)
            embeddings_backend = llm_adapter.as_ragas_embeddings()
        except (LLMConfigurationError, ValueError) as exc:
            raise typer.BadParameter(
                "Embedding model is not configured. Check provider settings and API keys in .env."
            ) from exc

        resolved_model = _resolve_embedding_model_name(settings)
        model_label = resolved_model or settings.llm_provider
        console.print(
            f"[dim]Computing embeddings for {len(texts)} examples (model: {model_label})...[/dim]"
        )

        if batch_size <= 0:
            raise typer.BadParameter("Batch size must be a positive integer.")

        vectors = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            batch_vectors = _embed_texts(embeddings_backend, batch)
            vectors.extend(batch_vectors)

        if len(vectors) != len(texts):
            raise typer.BadParameter("Embedding backend returned unexpected vector counts.")

    console.print("[dim]Running dimensionality reduction (UMAP/PCA)...[/dim]")
    projected = _reduce_to_2d(vectors)

    console.print("[dim]Clustering embeddings (HDBSCAN/DBSCAN)...[/dim]")
    clusters = _cluster_points(projected)

    for idx, row in enumerate(rows):
        row["umap_x"] = float(projected[idx, 0])
        row["umap_y"] = float(projected[idx, 1])
        row["cluster_id"] = int(clusters[idx])

    if fmt_lower == "csv":
        _export_rows_to_csv(rows, output)
    elif fmt_lower == "parquet":
        _export_rows_to_parquet(rows, output)
    else:
        raise typer.BadParameter("Unsupported format. Use 'csv' or 'parquet'.")

    console.print(
        f"[green]Exported {len(rows)} embeddings[/green] → [cyan]{output}[/cyan] "
        f"(dataset: {dataset_obj.name} / {dataset_obj.version_id})"
    )


_DEFAULT_PROMPT_MANIFEST = Path("agent/prompts/prompt_manifest.json")


@PhoenixApp.command("prompt-link")
def prompt_link(
    prompt_file: Path = typer.Argument(
        ...,
        help="Prompt file to associate with a Phoenix prompt entry.",
        readable=True,
    ),
    prompt_id: str = typer.Option(
        ...,
        "--prompt-id",
        "-p",
        help="Phoenix prompt identifier to store in the manifest.",
    ),
    experiment_id: str | None = typer.Option(
        None,
        "--experiment-id",
        "-e",
        help="Optional Phoenix experiment ID for traceability.",
    ),
    manifest: Path = typer.Option(
        _DEFAULT_PROMPT_MANIFEST,
        "--manifest",
        "-m",
        help="Prompt manifest JSON path (default: agent/prompts/prompt_manifest.json).",
    ),
    notes: str | None = typer.Option(
        None,
        "--notes",
        help="Optional notes about how this prompt is used.",
    ),
) -> None:
    """Record a Phoenix prompt linkage in the local manifest."""

    console = Console()
    manifest = manifest.expanduser()
    manifest_data = load_prompt_manifest(manifest)
    try:
        content = prompt_file.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise typer.BadParameter(f"Prompt file not found: {prompt_file}") from exc

    record_prompt_entry(
        manifest_data,
        prompt_path=prompt_file,
        content=content,
        phoenix_prompt_id=prompt_id,
        phoenix_experiment_id=experiment_id,
        notes=notes,
    )
    save_prompt_manifest(manifest, manifest_data)

    console.print(
        f"[green]Linked prompt[/green] [cyan]{prompt_file}[/cyan] → [magenta]{prompt_id}[/magenta]"
    )
    console.print(f"[dim]Manifest updated: {manifest}[/dim]")


@PhoenixApp.command("prompt-diff")
def prompt_diff(
    prompt_files: list[Path] = typer.Argument(
        ...,
        help="Prompt files to diff against the Phoenix manifest.",
    ),
    manifest: Path = typer.Option(
        _DEFAULT_PROMPT_MANIFEST,
        "--manifest",
        "-m",
        help="Prompt manifest JSON path (default: agent/prompts/prompt_manifest.json).",
    ),
    fmt: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table or json.",
        case_sensitive=False,
    ),
) -> None:
    """Show how local prompts differ from the manifest snapshot."""

    console = Console()
    manifest = manifest.expanduser()
    fmt_value = fmt.lower()
    if fmt_value not in {"table", "json"}:
        raise typer.BadParameter("Format must be 'table' or 'json'.")

    manifest_data = load_prompt_manifest(manifest)
    summaries = summarize_prompts(manifest_data, prompt_paths=list(prompt_files))
    summary_dicts = [asdict(summary) for summary in summaries]

    if fmt_value == "json":
        console.print_json(data=summary_dicts)
        return

    table = Table(
        title="Phoenix Prompt Status",
        show_lines=False,
        header_style="bold cyan",
    )
    table.add_column("Prompt", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Prompt ID", style="magenta")
    table.add_column("Experiment ID", style="magenta")
    table.add_column("Notes", style="dim")

    for summary in summaries:
        table.add_row(
            summary.path,
            summary.status,
            summary.phoenix_prompt_id or "-",
            summary.phoenix_experiment_id or "-",
            summary.notes or "-",
        )

    console.print(table)

    for summary in summaries:
        if not summary.diff:
            continue
        console.print(f"[bold]{summary.path} diff[/bold]")
        console.print(f"[dim]{summary.diff}[/dim]")


def create_phoenix_app(console: Console) -> typer.Typer:
    """Factory to attach Phoenix helper commands as sub-app."""

    app = typer.Typer(
        name="phoenix",
        help="Phoenix observability utilities.",
        add_completion=False,
    )
    app.add_typer(PhoenixApp)
    return app


__all__ = ["create_phoenix_app"]
