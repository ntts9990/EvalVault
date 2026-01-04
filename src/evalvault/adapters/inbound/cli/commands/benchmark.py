"""Benchmark subcommands for EvalVault CLI."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from evalvault.domain.services.retrieval_metrics import (
    average_retrieval_metrics,
    compute_retrieval_metrics,
    resolve_doc_id,
)

from ..utils.formatters import format_score, format_status


def create_benchmark_app(console: Console) -> typer.Typer:
    """Create the Typer sub-application for benchmark commands."""

    benchmark_app = typer.Typer(name="benchmark", help="Korean RAG benchmark utilities.")

    @benchmark_app.command("run")
    def benchmark_run(
        name: str = typer.Option(
            "korean-rag",
            "--name",
            "-n",
            help="Benchmark name to run.",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file for results (JSON format).",
        ),
        verbose: bool = typer.Option(
            False,
            "--verbose",
            "-v",
            help="Show detailed output.",
        ),
    ) -> None:
        """Run a benchmark suite."""

        console.print(f"\n[bold]Running Benchmark: {name}[/bold]\n")
        try:
            from evalvault.domain.services.benchmark_runner import KoreanRAGBenchmarkRunner

            toolkit = None
            if name == "korean-rag":
                try:
                    from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit

                    toolkit = KoreanNLPToolkit()
                except ImportError:
                    console.print(
                        "[yellow]Warning:[/yellow] Korean NLP extras not installed. "
                        "Falling back to baseline algorithms."
                    )

            runner = KoreanRAGBenchmarkRunner(nlp_toolkit=toolkit)

            with console.status("[bold green]Running benchmark..."):
                results = runner.run_all()

            table = Table(title="Benchmark Results", show_header=True, header_style="bold cyan")
            table.add_column("Test Case")
            table.add_column("Status")
            table.add_column("Score", justify="right")
            table.add_column("Details")

            passed = 0
            for result in results:
                status = format_status(result.passed)
                if result.passed:
                    passed += 1
                score = format_score(
                    result.score, result.passed if result.score is not None else None, precision=2
                )
                details = (
                    result.details[:40] + "..." if len(result.details) > 40 else result.details
                )
                table.add_row(result.name, status, score, details)

            console.print(table)
            console.print(f"\n[bold]Summary:[/bold] {passed}/{len(results)} tests passed")

            if output:
                data = {
                    "benchmark": name,
                    "total": len(results),
                    "passed": passed,
                    "results": [
                        {
                            "name": r.name,
                            "passed": r.passed,
                            "score": r.score,
                            "details": r.details,
                        }
                        for r in results
                    ],
                }
                with open(output, "w", encoding="utf-8") as file:
                    json.dump(data, file, ensure_ascii=False, indent=2)
                console.print(f"[green]Results saved to {output}[/green]")

        except ImportError as exc:
            console.print(f"[red]Error:[/red] Benchmark dependencies not available: {exc}")
            console.print(
                "[dim]Some benchmarks require additional packages (kiwipiepy, etc.)[/dim]"
            )
            raise typer.Exit(1)

        console.print()

    @benchmark_app.command("retrieval")
    def benchmark_retrieval(
        testset: Path = typer.Argument(..., help="Retrieval ground truth JSON file."),
        methods: str = typer.Option(
            "bm25,dense,hybrid",
            "--methods",
            help="Comma-separated retrieval methods (bm25,dense,hybrid,graphrag).",
        ),
        top_k: int = typer.Option(
            5,
            "--top-k",
            min=1,
            help="Top-K cutoff for Recall@K and MRR.",
        ),
        ndcg_k: int | None = typer.Option(
            None,
            "--ndcg-k",
            min=1,
            help="Top-K cutoff for nDCG (defaults to top-k).",
        ),
        embedding_profile: str | None = typer.Option(
            None,
            "--embedding-profile",
            help="Embedding profile for dense/hybrid (dev/prod, Ollama).",
        ),
        embedding_model: str | None = typer.Option(
            None,
            "--embedding-model",
            help="Embedding model override for dense/hybrid.",
        ),
        kg: Path | None = typer.Option(
            None,
            "--kg",
            help="Knowledge graph JSON for GraphRAG.",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file for results (.json or .csv).",
        ),
    ) -> None:
        """Run retrieval benchmark across multiple methods."""

        data = _load_retrieval_testset(testset)
        documents = data.get("documents", [])
        test_cases = _normalize_retrieval_test_cases(data.get("test_cases", []))
        if not documents or not test_cases:
            console.print("[red]Error:[/red] documents/test_cases are required.")
            raise typer.Exit(1)

        doc_ids, doc_contents = _normalize_documents(documents)
        doc_id_set = set(doc_ids)
        _warn_missing_relevance(console, test_cases, doc_id_set)

        method_list = _parse_methods(methods)
        if "graphrag" in method_list and kg is None:
            console.print("[red]Error:[/red] GraphRAG requires --kg.")
            raise typer.Exit(1)

        results: dict[str, dict[str, Any]] = {}
        recall_key = f"recall_at_{top_k}"
        precision_key = f"precision_at_{top_k}"
        ndcg_key = f"ndcg_at_{ndcg_k or top_k}"
        normalized_profile = _normalize_embedding_profile(embedding_profile)
        ollama_adapter = _build_ollama_adapter(
            embedding_profile=normalized_profile,
            embedding_model=embedding_model,
            console=console,
        )

        for method in method_list:
            search_fn, backend = _build_search_fn(
                method,
                doc_contents,
                doc_ids,
                console=console,
                kg_path=kg,
                embedding_profile=normalized_profile,
                embedding_model=embedding_model,
                ollama_adapter=ollama_adapter,
            )
            case_metrics = []
            for tc in test_cases:
                retrieved = search_fn(tc["query"], top_k)
                metrics = compute_retrieval_metrics(
                    retrieved,
                    tc["relevant_doc_ids"],
                    recall_k=top_k,
                    ndcg_k=ndcg_k,
                )
                case_metrics.append(metrics)

            summary = average_retrieval_metrics(case_metrics)
            summary["test_cases"] = len(case_metrics)
            if backend != method:
                summary["backend"] = backend
            results[method] = summary

        _print_retrieval_table(
            console,
            results,
            recall_key=recall_key,
            precision_key=precision_key,
            ndcg_key=ndcg_key,
        )

        if output:
            payload = {
                "methods_compared": method_list,
                "results": results,
                "overall": _build_overall_summary(
                    results,
                    recall_key,
                    precision_key,
                    ndcg_key,
                ),
            }
            _write_retrieval_output(
                output,
                payload,
                results,
                recall_key,
                precision_key,
                ndcg_key,
            )
            console.print(f"[green]Results saved to {output}[/green]")

    @benchmark_app.command("list")
    def benchmark_list() -> None:
        """List available benchmarks."""

        console.print("\n[bold]Available Benchmarks[/bold]\n")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name", style="bold")
        table.add_column("Description")
        table.add_column("Test Cases")
        table.add_column("Requirements")

        table.add_row(
            "korean-rag",
            "Korean RAG system benchmark",
            "~10",
            "kiwipiepy, rank-bm25, sentence-transformers (install with --extra korean)",
        )

        console.print(table)
        console.print(
            "\n[dim]Use 'evalvault benchmark run --name <name>' to run a benchmark.[/dim]\n"
        )

    return benchmark_app


def _load_retrieval_testset(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise typer.BadParameter(f"Testset file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise typer.BadParameter("Invalid retrieval testset JSON.") from exc


def _normalize_documents(documents: Sequence[dict[str, Any]]) -> tuple[list[str], list[str]]:
    doc_ids: list[str] = []
    contents: list[str] = []
    for idx, doc in enumerate(documents, start=1):
        doc_id = doc.get("doc_id") or doc.get("id") or f"doc_{idx}"
        content = doc.get("content") or doc.get("text") or doc.get("document") or ""
        doc_ids.append(str(doc_id))
        contents.append(str(content))
    return doc_ids, contents


def _normalize_retrieval_test_cases(
    test_cases: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for idx, tc in enumerate(test_cases, start=1):
        query = tc.get("query") or tc.get("question")
        if not query:
            continue
        if "relevant_doc_ids" in tc:
            relevant_doc_ids = tc.get("relevant_doc_ids", [])
        else:
            relevant_doc_ids = tc.get("relevant_docs", [])
        test_id = tc.get("test_id") or tc.get("id") or f"ret-{idx:03d}"
        normalized.append(
            {
                "test_id": str(test_id),
                "query": str(query),
                "relevant_doc_ids": [str(doc_id) for doc_id in relevant_doc_ids],
            }
        )
    return normalized


def _parse_methods(methods: str) -> list[str]:
    aliases = {"graph-rag": "graphrag", "graph": "graphrag"}
    supported = {"bm25", "dense", "hybrid", "graphrag"}
    resolved: list[str] = []
    for raw in methods.split(","):
        candidate = raw.strip().lower()
        if not candidate:
            continue
        method = aliases.get(candidate, candidate)
        if method not in supported:
            raise typer.BadParameter(f"Unsupported retrieval method: {candidate}")
        if method not in resolved:
            resolved.append(method)
    if not resolved:
        raise typer.BadParameter("At least one retrieval method is required.")
    return resolved


def _normalize_embedding_profile(profile: str | None) -> str | None:
    if profile is None:
        return None
    normalized = profile.strip().lower()
    if normalized not in {"dev", "prod"}:
        raise typer.BadParameter("Embedding profile must be 'dev' or 'prod'.")
    return normalized


def _resolve_ollama_embedding_model(
    *,
    embedding_profile: str | None,
    embedding_model: str | None,
) -> str | None:
    if embedding_model:
        return embedding_model
    if embedding_profile == "dev":
        return "qwen3-embedding:0.6b"
    if embedding_profile == "prod":
        return "qwen3-embedding:8b"
    return None


def _build_ollama_adapter(
    *,
    embedding_profile: str | None,
    embedding_model: str | None,
    console: Console,
) -> Any | None:
    resolved_model = _resolve_ollama_embedding_model(
        embedding_profile=embedding_profile,
        embedding_model=embedding_model,
    )
    if not resolved_model:
        return None
    if not _is_ollama_model(resolved_model):
        return None
    try:
        from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter
        from evalvault.config.settings import get_settings

        settings = get_settings()
        settings.ollama_embedding_model = resolved_model
        return OllamaAdapter(settings)
    except Exception as exc:
        console.print(
            f"[yellow]Warning:[/yellow] Ollama adapter 초기화 실패, 키워드 폴백 사용 ({exc})"
        )
        return None


def _is_ollama_model(model_name: str) -> bool:
    return model_name.startswith("qwen3-embedding:")


def _warn_missing_relevance(
    console: Console,
    test_cases: Sequence[dict[str, Any]],
    doc_id_set: set[str],
) -> None:
    missing: list[str] = []
    for tc in test_cases:
        for doc_id in tc["relevant_doc_ids"]:
            if doc_id not in doc_id_set:
                missing.append(doc_id)
                if len(missing) >= 3:
                    break
        if len(missing) >= 3:
            break
    if missing:
        preview = ", ".join(missing)
        console.print(
            f"[yellow]Warning:[/yellow] 일부 relevant_doc_ids가 documents에 없습니다: {preview}"
        )


def _build_search_fn(
    method: str,
    documents: Sequence[str],
    doc_ids: Sequence[str],
    *,
    console: Console,
    kg_path: Path | None,
    embedding_profile: str | None,
    embedding_model: str | None,
    ollama_adapter: Any | None,
) -> tuple[Callable[[str, int], list[str]], str]:
    if method in {"bm25", "hybrid"}:
        retriever = None
        try:
            from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit

            toolkit = KoreanNLPToolkit()
            retriever = toolkit.build_retriever(
                documents,
                use_hybrid=method == "hybrid",
                ollama_adapter=ollama_adapter,
                embedding_profile=embedding_profile,
                verbose=False,
            )
        except Exception as exc:
            console.print(
                f"[yellow]Warning:[/yellow] {method} retriever 초기화 실패, "
                f"키워드 폴백 사용 ({exc})"
            )
        if retriever:
            return (
                lambda query, top_k: _search_with_retriever(retriever, doc_ids, query, top_k),
                method,
            )
        return (
            lambda query, top_k: _keyword_search(documents, doc_ids, query, top_k),
            "keyword",
        )

    if method == "dense":
        retriever = None
        try:
            from evalvault.adapters.outbound.nlp.korean.dense_retriever import (
                KoreanDenseRetriever,
            )

            retriever = KoreanDenseRetriever()
            if embedding_profile or embedding_model or ollama_adapter:
                retriever = KoreanDenseRetriever(
                    model_name=embedding_model,
                    profile=embedding_profile,
                    ollama_adapter=ollama_adapter,
                )
            retriever.index(list(documents))
        except Exception as exc:
            console.print(
                f"[yellow]Warning:[/yellow] dense retriever 초기화 실패, 키워드 폴백 사용 ({exc})"
            )
        if retriever:
            return (
                lambda query, top_k: _search_with_retriever(retriever, doc_ids, query, top_k),
                method,
            )
        return (
            lambda query, top_k: _keyword_search(documents, doc_ids, query, top_k),
            "keyword",
        )

    if method == "graphrag":
        retriever = None
        try:
            if kg_path is None:
                raise ValueError("KG path is required for GraphRAG.")
            from evalvault.adapters.outbound.kg.graph_rag_retriever import GraphRAGRetriever

            from .run_helpers import load_knowledge_graph

            kg_graph = load_knowledge_graph(kg_path)

            bm25_retriever = None
            try:
                from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit

                toolkit = KoreanNLPToolkit()
                bm25_retriever = toolkit.build_retriever(
                    documents,
                    use_hybrid=False,
                    ollama_adapter=ollama_adapter,
                    embedding_profile=embedding_profile,
                    verbose=False,
                )
            except Exception:
                bm25_retriever = None

            dense_retriever = None
            try:
                from evalvault.adapters.outbound.nlp.korean.dense_retriever import (
                    KoreanDenseRetriever,
                )

                dense_retriever = KoreanDenseRetriever(
                    model_name=embedding_model,
                    profile=embedding_profile,
                    ollama_adapter=ollama_adapter,
                )
                dense_retriever.index(list(documents))
            except Exception:
                dense_retriever = None

            retriever = GraphRAGRetriever(
                kg_graph,
                bm25_retriever=bm25_retriever,
                dense_retriever=dense_retriever,
                documents=list(documents),
                document_ids=list(doc_ids),
            )
        except Exception as exc:
            console.print(
                "[yellow]Warning:[/yellow] graphrag retriever 초기화 실패, "
                f"키워드 폴백 사용 ({exc})"
            )
        if retriever:
            return (
                lambda query, top_k: _search_with_retriever(retriever, doc_ids, query, top_k),
                method,
            )
        return (
            lambda query, top_k: _keyword_search(documents, doc_ids, query, top_k),
            "keyword",
        )

    raise typer.BadParameter(f"Unsupported retrieval method: {method}")


def _search_with_retriever(
    retriever: Any,
    doc_ids: Sequence[str],
    query: str,
    top_k: int,
) -> list[str]:
    results = retriever.search(query, top_k=top_k)
    return [
        resolve_doc_id(getattr(result, "doc_id", None), doc_ids, idx)
        for idx, result in enumerate(results, start=1)
    ]


def _keyword_search(
    documents: Sequence[str],
    doc_ids: Sequence[str],
    query: str,
    top_k: int,
) -> list[str]:
    query_words = set(query.lower().split())
    scores: list[tuple[int, int, str]] = []
    for idx, doc in enumerate(documents):
        doc_words = set(doc.lower().split())
        overlap = len(query_words & doc_words)
        scores.append((overlap, idx, str(doc_ids[idx])))
    scores.sort(key=lambda item: (-item[0], item[1]))
    return [doc_id for _, _, doc_id in scores[:top_k]]


def _print_retrieval_table(
    console: Console,
    results: dict[str, dict[str, Any]],
    *,
    recall_key: str,
    precision_key: str,
    ndcg_key: str,
) -> None:
    table = Table(title="Retrieval Benchmark Results", show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    for method in results:
        table.add_column(method, justify="right")

    for metric_key in [recall_key, precision_key, "mrr", ndcg_key]:
        label = _format_metric_label(metric_key)
        row = [label]
        for method in results:
            value = results[method].get(metric_key)
            row.append(format_score(value, None, precision=3))
        table.add_row(*row)

    console.print(table)

    fallbacks = {m: r.get("backend") for m, r in results.items() if r.get("backend")}
    if fallbacks:
        details = ", ".join(f"{method}→{backend}" for method, backend in fallbacks.items())
        console.print(f"[dim]Fallbacks: {details}[/dim]")


def _format_metric_label(metric_key: str) -> str:
    if metric_key.startswith("precision_at_"):
        return f"Precision@{metric_key.split('_')[-1]}"
    if metric_key.startswith("recall_at_"):
        return f"Recall@{metric_key.split('_')[-1]}"
    if metric_key.startswith("ndcg_at_"):
        return f"nDCG@{metric_key.split('_')[-1]}"
    if metric_key == "mrr":
        return "MRR"
    return metric_key


def _build_overall_summary(
    results: dict[str, dict[str, Any]],
    recall_key: str,
    precision_key: str,
    ndcg_key: str,
) -> dict[str, Any]:
    best_by_metric: dict[str, dict[str, Any]] = {}
    for metric_key in [recall_key, precision_key, "mrr", ndcg_key]:
        best_method = max(
            results.keys(),
            key=lambda method: results[method].get(metric_key, float("-inf")),
        )
        best_by_metric[metric_key] = {
            "method": best_method,
            "score": results[best_method].get(metric_key, 0.0),
        }
    return {"best_by_metric": best_by_metric}


def _write_retrieval_output(
    path: Path,
    payload: dict[str, Any],
    results: dict[str, dict[str, Any]],
    recall_key: str,
    precision_key: str,
    ndcg_key: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".csv":
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["method", recall_key, precision_key, "mrr", ndcg_key, "test_cases", "backend"]
            )
            for method, metrics in results.items():
                writer.writerow(
                    [
                        method,
                        metrics.get(recall_key, 0.0),
                        metrics.get(precision_key, 0.0),
                        metrics.get("mrr", 0.0),
                        metrics.get(ndcg_key, 0.0),
                        metrics.get("test_cases", 0),
                        metrics.get("backend", ""),
                    ]
                )
        return

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


__all__ = ["create_benchmark_app"]
