"""Retrieval analyzer module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output, safe_mean
from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer, KoreanFaithfulnessChecker
from evalvault.domain.entities import EvaluationRun


class RetrievalAnalyzerModule(BaseAnalysisModule):
    """Compute retrieval quality statistics from run data."""

    module_id = "retrieval_analyzer"
    name = "Retrieval Analyzer"
    description = "Summarize retrieval context coverage and keyword overlap."
    input_types = ["run"]
    output_types = ["retrieval_summary", "statistics"]
    requires = ["data_loader"]
    tags = ["verification", "retrieval"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")
        if not isinstance(run, EvaluationRun):
            return {
                "summary": {},
                "statistics": {},
                "insights": ["No run data available for retrieval analysis."],
            }

        params = params or {}
        max_cases = int(params.get("max_cases", 150))
        max_examples = int(params.get("max_examples", 5))
        max_graphrag_docs = int(params.get("max_graphrag_docs", 5))

        context_counts: list[int] = []
        context_token_counts: list[int] = []
        keyword_overlap_scores: list[float] = []
        ground_truth_hits = 0
        faithfulness_scores: list[float] = []

        tokenizer = None
        checker = None
        try:
            tokenizer = KiwiTokenizer()
            checker = KoreanFaithfulnessChecker(tokenizer)
        except Exception:
            tokenizer = None
            checker = None

        cases = run.results[:max_cases]
        for result in cases:
            contexts = result.contexts or []
            context_counts.append(len(contexts))
            for context in contexts:
                context_token_counts.append(len(context.split()))

            context_text = " ".join(contexts)
            question = result.question or ""
            ground_truth = result.ground_truth or ""

            if ground_truth and any(ground_truth in ctx for ctx in contexts):
                ground_truth_hits += 1

            if tokenizer and question and context_text:
                keywords = tokenizer.extract_keywords(question)
                if keywords:
                    hits = sum(1 for kw in keywords if kw in context_text)
                    keyword_overlap_scores.append(hits / len(keywords))
            elif question and context_text:
                words = [part for part in question.split() if part]
                if words:
                    hits = sum(1 for kw in words if kw in context_text)
                    keyword_overlap_scores.append(hits / len(words))

            if checker and result.answer and contexts:
                try:
                    faithfulness = checker.check_faithfulness(
                        answer=result.answer,
                        contexts=contexts,
                    )
                    if faithfulness:
                        faithfulness_scores.append(faithfulness.score)
                except Exception:
                    pass

        total_cases = len(cases)
        empty_contexts = sum(1 for count in context_counts if count == 0)
        empty_rate = empty_contexts / total_cases if total_cases else 0.0

        retrieval_meta = run.retrieval_metadata or {}
        retrieval_times: list[float] = []
        retrieval_scores: list[float] = []
        graph_nodes: list[int] = []
        graph_edges: list[int] = []
        subgraph_sizes: list[int] = []
        graphrag_cases = 0
        graphrag_examples: list[dict[str, Any]] = []
        for item in retrieval_meta.values():
            if isinstance(item, dict):
                if "retrieval_time_ms" in item:
                    retrieval_times.append(float(item["retrieval_time_ms"]))
                scores = item.get("scores")
                if isinstance(scores, list) and scores:
                    retrieval_scores.append(safe_mean([float(s) for s in scores]))
                if "graph_nodes" in item:
                    graph_nodes.append(int(item["graph_nodes"]))
                if "graph_edges" in item:
                    graph_edges.append(int(item["graph_edges"]))
                if "subgraph_size" in item:
                    subgraph_sizes.append(int(item["subgraph_size"]))
                if item.get("retriever") == "graphrag":
                    graphrag_cases += 1
                    if len(graphrag_examples) < max_examples:
                        graphrag_details = item.get("graphrag")
                        if isinstance(graphrag_details, dict):
                            graphrag_examples.append(
                                _trim_graphrag_example(graphrag_details, max_docs=max_graphrag_docs)
                            )

        summary = {
            "total_cases": total_cases,
            "avg_contexts": round(safe_mean(context_counts), 2),
            "empty_context_rate": round(empty_rate, 4),
            "avg_context_tokens": round(safe_mean(context_token_counts), 2),
            "avg_keyword_overlap": round(safe_mean(keyword_overlap_scores), 4),
            "ground_truth_hit_rate": round(
                (ground_truth_hits / total_cases) if total_cases else 0.0,
                4,
            ),
            "avg_faithfulness": round(safe_mean(faithfulness_scores), 4),
            "has_retrieval_metadata": bool(retrieval_meta),
        }

        if retrieval_times:
            summary["avg_retrieval_time_ms"] = round(safe_mean(retrieval_times), 2)
        if retrieval_scores:
            summary["avg_retrieval_score"] = round(safe_mean(retrieval_scores), 4)
        if graph_nodes:
            summary["avg_graph_nodes"] = round(safe_mean(graph_nodes), 2)
        if graph_edges:
            summary["avg_graph_edges"] = round(safe_mean(graph_edges), 2)
        if subgraph_sizes:
            summary["avg_subgraph_size"] = round(safe_mean(subgraph_sizes), 2)
        if total_cases:
            summary["graphrag_case_rate"] = round(graphrag_cases / total_cases, 4)
        summary["graphrag_case_count"] = graphrag_cases

        insights = []
        if summary["avg_contexts"] < 1:
            insights.append("Average context count is below 1 per query.")
        if summary["empty_context_rate"] > 0.2:
            insights.append("Many queries are missing retrieval contexts.")
        if summary["avg_keyword_overlap"] < 0.3:
            insights.append("Keyword overlap between queries and contexts is low.")

        return {
            "summary": summary,
            "statistics": {
                "context_counts": context_counts[:100],
                "context_token_counts": context_token_counts[:100],
                "keyword_overlap_scores": keyword_overlap_scores[:100],
                "faithfulness_scores": faithfulness_scores[:100],
                "graph_nodes": graph_nodes[:100],
                "graph_edges": graph_edges[:100],
                "subgraph_sizes": subgraph_sizes[:100],
                "graphrag_examples": graphrag_examples,
            },
            "insights": insights,
        }


def _trim_graphrag_example(payload: dict[str, Any], *, max_docs: int) -> dict[str, Any]:
    docs = payload.get("docs")
    if isinstance(docs, list):
        trimmed_docs = []
        for entry in docs[:max_docs]:
            if not isinstance(entry, dict):
                continue
            trimmed_docs.append(_trim_graphrag_doc(entry))
        docs = trimmed_docs
    else:
        docs = []
    return {
        "docs": docs,
        "max_docs": max_docs,
    }


def _trim_graphrag_doc(entry: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key in ("doc_id", "rank", "score"):
        if key in entry:
            output[key] = entry[key]
    sources = entry.get("sources")
    if isinstance(sources, dict):
        output["sources"] = sources
    return output
