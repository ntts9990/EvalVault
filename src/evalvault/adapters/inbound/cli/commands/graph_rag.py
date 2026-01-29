"""GraphRAG experiment commands for the EvalVault CLI."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.analysis.statistical_adapter import StatisticalAnalysisAdapter
from evalvault.adapters.outbound.dataset import get_loader
from evalvault.adapters.outbound.llm import SettingsLLMFactory, get_llm_adapter
from evalvault.adapters.outbound.nlp.korean.toolkit_factory import try_create_korean_toolkit
from evalvault.adapters.outbound.retriever.graph_rag_adapter import GraphRAGAdapter
from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.services.analysis_service import AnalysisService
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.domain.services.graph_rag_experiment import GraphRAGExperiment
from evalvault.ports.outbound.korean_nlp_port import RetrieverPort

from ..utils.console import print_cli_error
from ..utils.options import db_option, profile_option
from ..utils.validators import parse_csv_option, validate_choice
from .run import _build_dense_retriever
from .run_helpers import _is_oss_open_model, load_knowledge_graph, load_retriever_documents


def create_graph_rag_app(console: Console) -> typer.Typer:
    app = typer.Typer(name="graphrag", help="GraphRAG experiment utilities.")

    @app.command("compare")
    def graphrag_compare(
        dataset: Path = typer.Argument(
            ...,
            help="Path to dataset file (CSV, Excel, or JSON).",
            exists=True,
            readable=True,
        ),
        metrics: str = typer.Option(
            "faithfulness,answer_relevancy",
            "--metrics",
            "-m",
            help="Comma-separated list of metrics to evaluate.",
        ),
        baseline_retriever: str = typer.Option(
            "bm25",
            "--baseline-retriever",
            help="Baseline retriever (bm25, dense, hybrid).",
        ),
        retriever_docs: Path = typer.Option(
            ...,
            "--retriever-docs",
            help="Retriever documents file (.json/.jsonl/.txt).",
            exists=True,
            readable=True,
        ),
        kg_path: Path = typer.Option(
            ...,
            "--kg",
            "-k",
            help="Knowledge graph JSON file for GraphRAG.",
            exists=True,
            readable=True,
        ),
        retriever_top_k: int = typer.Option(
            5,
            "--retriever-top-k",
            help="Retriever top-k to fill contexts.",
        ),
        graph_max_hops: int = typer.Option(
            2,
            "--graph-max-hops",
            help="GraphRAG max hop depth.",
        ),
        graph_max_nodes: int = typer.Option(
            20,
            "--graph-max-nodes",
            help="GraphRAG max nodes in subgraph.",
        ),
        model: str | None = typer.Option(
            None,
            "--model",
            help="Model to use for evaluation (overrides profile).",
        ),
        db_path: Path | None = db_option(help_text="DB 경로 (저장 시 사용)."),
        profile: str | None = profile_option(help_text="LLM 프로필"),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="JSON 출력 파일 경로",
        ),
        artifact_dir: Path = typer.Option(
            Path("reports/analysis/artifacts"),
            "--artifact-dir",
            help="GraphRAG 아티팩트 저장 경로",
        ),
    ) -> None:
        validate_choice(baseline_retriever, ["bm25", "dense", "hybrid"], console)

        settings = Settings()
        profile_name = profile or settings.evalvault_profile
        if profile_name:
            settings = apply_profile(settings, profile_name)

        if model:
            if _is_oss_open_model(model) and settings.llm_provider != "vllm":
                settings.llm_provider = "ollama"
                settings.ollama_model = model
            elif settings.llm_provider == "ollama":
                settings.ollama_model = model
            elif settings.llm_provider == "vllm":
                settings.vllm_model = model
            else:
                settings.openai_model = model

        if settings.llm_provider == "openai" and not settings.openai_api_key:
            print_cli_error(console, "OPENAI_API_KEY가 설정되지 않았습니다.")
            raise typer.Exit(1)

        try:
            llm_adapter = get_llm_adapter(settings)
        except Exception as exc:
            print_cli_error(console, "LLM 어댑터 초기화에 실패했습니다.", details=str(exc))
            raise typer.Exit(1) from exc

        loader = get_loader(dataset)
        ds = loader.load(dataset)

        documents, doc_ids = load_retriever_documents(retriever_docs)
        baseline = _build_baseline_retriever(
            baseline_retriever,
            documents=documents,
            settings=settings,
            profile_name=profile_name,
        )
        if baseline is None:
            print_cli_error(console, "Baseline retriever 초기화에 실패했습니다.")
            raise typer.Exit(1)

        kg_graph = load_knowledge_graph(kg_path)
        graph_adapter = GraphRAGAdapter(kg_graph)

        korean_toolkit = try_create_korean_toolkit()
        evaluator = RagasEvaluator(
            korean_toolkit=korean_toolkit,
            llm_factory=SettingsLLMFactory(settings),
        )
        analysis_service = AnalysisService(analysis_adapter=StatisticalAnalysisAdapter())
        experiment = GraphRAGExperiment(
            evaluator=evaluator,
            analysis_service=analysis_service,
        )

        metric_list = parse_csv_option(metrics)
        if not metric_list:
            print_cli_error(console, "평가 메트릭을 지정하세요.")
            raise typer.Exit(1)

        result = asyncio.run(
            experiment.run_comparison(
                dataset=ds,
                baseline_retriever=baseline,
                graph_retriever=graph_adapter,
                metrics=metric_list,
                llm=llm_adapter,
                retriever_top_k=retriever_top_k,
                graph_max_hops=graph_max_hops,
                graph_max_nodes=graph_max_nodes,
            )
        )

        artifacts_path = _write_graph_rag_artifacts(
            result=result,
            dataset=ds,
            graph_retriever=graph_adapter,
            artifact_root=artifact_dir,
        )
        console.print(f"[green]Saved GraphRAG artifacts:[/green] {artifacts_path}")

        if db_path is not None:
            storage = build_storage_adapter(settings=Settings(), db_path=db_path)
            storage.save_run(result.baseline_run)
            storage.save_run(result.graph_run)
            console.print(f"[green]Saved baseline run:[/green] {result.baseline_run.run_id}")
            console.print(f"[green]Saved graph run:[/green] {result.graph_run.run_id}")

        _render_comparison_table(console, result)

        if output:
            payload = _build_output_payload(result, doc_ids)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
            console.print(f"[green]Saved output:[/green] {output}")

    return app


def _build_baseline_retriever(
    mode: str,
    *,
    documents: list[str],
    settings: Settings,
    profile_name: str | None,
) -> RetrieverPort | None:
    if mode in {"bm25", "hybrid"}:
        toolkit = try_create_korean_toolkit()
        if toolkit is None:
            return None
        return toolkit.build_retriever(documents, use_hybrid=mode == "hybrid", verbose=False)
    return _build_dense_retriever(
        documents=documents,
        settings=settings,
        profile_name=profile_name,
    )


def _render_comparison_table(console: Console, result: Any) -> None:
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Baseline", justify="right")
    table.add_column("Graph", justify="right")
    table.add_column("Diff%", justify="right")
    table.add_column("P-Value", justify="right")

    for comp in result.comparisons:
        table.add_row(
            comp.metric,
            f"{comp.mean_a:.3f}",
            f"{comp.mean_b:.3f}",
            f"{comp.diff_percent:+.1f}%",
            f"{comp.p_value:.4f}",
        )

    console.print("\n[bold]GraphRAG Comparison[/bold]\n")
    console.print(table)
    console.print()


def _build_output_payload(result: Any, doc_ids: list[str]) -> dict[str, Any]:
    return {
        "baseline": result.baseline_run.to_summary_dict(),
        "graph": result.graph_run.to_summary_dict(),
        "comparisons": [asdict(comp) for comp in result.comparisons],
        "graph_contexts": result.graph_contexts,
        "graph_subgraphs": {key: asdict(value) for key, value in result.graph_subgraphs.items()},
        "retriever_doc_ids": doc_ids,
    }


def _write_graph_rag_artifacts(
    *,
    result: Any,
    dataset: Any,
    graph_retriever: GraphRAGAdapter,
    artifact_root: Path,
) -> Path:
    run_id = result.graph_run.run_id
    base_dir = artifact_root / f"analysis_{run_id}"
    graph_dir = base_dir / "graph_subgraphs"
    entity_dir = base_dir / "entity_extraction"
    graph_dir.mkdir(parents=True, exist_ok=True)
    entity_dir.mkdir(parents=True, exist_ok=True)

    graph_index: dict[str, str] = {}
    for case_id, subgraph in result.graph_subgraphs.items():
        safe_id = _safe_filename(case_id)
        file_name = f"{safe_id}_subgraph.json"
        file_path = graph_dir / file_name
        with file_path.open("w", encoding="utf-8") as handle:
            json.dump(asdict(subgraph), handle, ensure_ascii=False, indent=2)
        graph_index[case_id] = str(Path("graph_subgraphs") / file_name)

    entities_payload: dict[str, list[dict[str, object]]] = {}
    for case in dataset.test_cases:
        entities = graph_retriever.extract_entities(case.question)
        entities_payload[case.id] = [asdict(entity) for entity in entities]
    entities_path = entity_dir / "entities.json"
    with entities_path.open("w", encoding="utf-8") as handle:
        json.dump(entities_payload, handle, ensure_ascii=False, indent=2)

    index_payload = {
        "graph_subgraphs": graph_index,
        "entity_extraction": str(Path("entity_extraction") / "entities.json"),
    }
    with (base_dir / "index.json").open("w", encoding="utf-8") as handle:
        json.dump(index_payload, handle, ensure_ascii=False, indent=2)

    return base_dir


def _safe_filename(value: str) -> str:
    return value.replace("/", "_").replace("\\", "_").replace(" ", "_")


__all__ = ["create_graph_rag_app"]
