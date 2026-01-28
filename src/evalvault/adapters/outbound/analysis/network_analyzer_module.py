from __future__ import annotations

import contextlib
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from importlib import import_module
from typing import Any

import networkx as nx

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import (
    get_upstream_output,
    to_serializable,
)


def _get_matplotlib_pyplot() -> Any | None:
    try:
        if "matplotlib.pyplot" in sys.modules:
            return import_module("matplotlib.pyplot")
        os.environ.setdefault("MPLBACKEND", "Agg")
        matplotlib = import_module("matplotlib")
        with contextlib.suppress(Exception):
            matplotlib.use("Agg", force=True)
        return import_module("matplotlib.pyplot")
    except ModuleNotFoundError:
        return None


@dataclass
class NetworkAnalysisResult:
    run_id: str
    node_count: int = 0
    edge_count: int = 0
    density: float = 0.0
    avg_clustering: float = 0.0
    communities: list[list[str]] = field(default_factory=list)
    hub_metrics: dict[str, float] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class NetworkAnalyzerModule(BaseAnalysisModule):
    module_id = "network_analyzer"
    name = "Network Analyzer"
    description = "Analyze correlation networks between metrics."
    input_types = ["statistics"]
    output_types = ["network"]
    requires = ["statistical_analyzer"]
    tags = ["analysis", "network"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        context = inputs.get("__context__", {})
        additional_params = context.get("additional_params", {}) or {}

        stats_output = get_upstream_output(inputs, "statistics", "statistical_analyzer") or {}
        correlations = stats_output.get("significant_correlations") or []
        min_correlation = additional_params.get("min_correlation") or params.get("min_correlation")
        if min_correlation is None:
            min_correlation = 0.5
        min_correlation = float(min_correlation)

        if not correlations:
            return {
                "summary": {
                    "node_count": 0,
                    "edge_count": 0,
                    "density": 0.0,
                    "avg_clustering": 0.0,
                },
                "graph": {"nodes": [], "edges": []},
                "analysis": None,
                "insights": ["No significant correlations for network analysis."],
            }

        graph = self.build_correlation_network(correlations, min_correlation=min_correlation)
        result = self.analyze_metric_network(graph)
        edges = [
            {
                "source": source,
                "target": target,
                **data,
            }
            for source, target, data in graph.edges(data=True)
        ]

        return {
            "summary": {
                "node_count": result.node_count,
                "edge_count": result.edge_count,
                "density": result.density,
                "avg_clustering": result.avg_clustering,
            },
            "graph": {
                "nodes": list(graph.nodes()),
                "edges": to_serializable(edges),
            },
            "analysis": to_serializable(result),
            "insights": result.insights,
        }

    def build_correlation_network(
        self,
        correlations: list[dict[str, Any]],
        min_correlation: float = 0.5,
    ) -> nx.Graph:
        graph = nx.Graph()

        for corr in correlations:
            variable1 = str(corr.get("variable1", ""))
            variable2 = str(corr.get("variable2", ""))
            correlation = float(corr.get("correlation", 0.0))
            p_value = float(corr.get("p_value", 1.0))
            is_significant = bool(corr.get("is_significant", False))

            if is_significant and abs(correlation) >= min_correlation:
                graph.add_edge(
                    variable1,
                    variable2,
                    weight=abs(correlation),
                    correlation=correlation,
                    p_value=p_value,
                )

        return graph

    def analyze_metric_network(self, graph: nx.Graph) -> NetworkAnalysisResult:
        if graph.number_of_nodes() == 0:
            return NetworkAnalysisResult(run_id="", insights=["No nodes in network"])

        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()
        density = nx.density(graph)

        betweenness = nx.betweenness_centrality(graph)
        degree = nx.degree_centrality(graph)
        closeness = nx.closeness_centrality(graph)

        hub_betweenness = sorted(betweenness.items(), key=lambda x: -x[1])[:3]
        hub_degree = sorted(degree.items(), key=lambda x: -x[1])[:3]
        hub_closeness = sorted(closeness.items(), key=lambda x: -x[1])[:3]

        hub_candidates: set[str] = set()
        hub_candidates.update([m[0] for m in hub_betweenness])
        hub_candidates.update([m[0] for m in hub_degree])
        hub_candidates.update([m[0] for m in hub_closeness])

        hub_metrics = dict.fromkeys(hub_candidates, 1.0)

        avg_clustering = nx.average_clustering(graph)

        communities_raw = list(nx.community.greedy_modularity_communities(graph))
        communities = [[str(node) for node in community] for community in communities_raw]

        insights = self._generate_network_insights(
            graph=graph,
            density=density,
            avg_clustering=avg_clustering,
            communities=communities,
            hub_metrics=hub_metrics,
        )

        return NetworkAnalysisResult(
            run_id="",
            node_count=node_count,
            edge_count=edge_count,
            density=density,
            avg_clustering=avg_clustering,
            communities=communities,
            hub_metrics=hub_metrics,
            insights=insights,
        )

    def visualize_network(
        self,
        graph: nx.Graph,
        output_path: str | None = None,
        figsize: tuple[int, int] = (12, 8),
    ) -> Any | None:
        plt = _get_matplotlib_pyplot()
        if plt is None:
            return None

        fig, ax = plt.subplots(figsize=figsize)
        pos = nx.spring_layout(graph, seed=42, k=1.0)

        degrees = dict(graph.degree())
        node_sizes = [degrees[node] * 100 for node in graph.nodes()]

        nx.draw(
            graph,
            pos=pos,
            ax=ax,
            with_labels=True,
            node_size=node_sizes,
            node_color="skyblue",
            font_size=10,
            font_weight="bold",
            edge_color="gray",
            width=1.5,
        )

        ax.set_title("Metric Correlation Network", fontweight="bold", fontsize=14)

        for spine in ax.spines.values():
            spine.set_visible(False)

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close(fig)

        return fig

    def _generate_network_insights(
        self,
        graph: nx.Graph,
        density: float,
        avg_clustering: float,
        communities: list[list[str]],
        hub_metrics: dict[str, float],
    ) -> list[str]:
        insights: list[str] = []

        if density > 0.8:
            insights.append("High network density detected - metrics are strongly interconnected")
        elif density < 0.3:
            insights.append("Low network density - metrics have weak correlations")

        if avg_clustering > 0.7:
            insights.append("Strong clustering - metrics form well-defined groups")
        elif avg_clustering < 0.3:
            insights.append("Weak clustering - metrics are independent")

        if communities:
            if len(communities) > 1:
                insights.append(
                    f"Detected {len(communities)} metric communities (groups of correlated metrics)"
                )
            for idx, community in enumerate(communities):
                if len(community) > 2:
                    insights.append(f"Community {idx + 1}: {', '.join(community)}")

        if hub_metrics:
            hub_list = ", ".join(sorted(hub_metrics.keys()))
            insights.append(f"Hub metrics (high centrality): {hub_list}")

        edge_correlations = [graph[u][v].get("correlation", 0.0) for u, v in graph.edges()]
        if edge_correlations:
            strong_edges = sum(1 for w in edge_correlations if abs(w) > 0.7)
            weak_edges = sum(1 for w in edge_correlations if abs(w) < 0.4)
            insights.append(
                f"Correlation strength: {strong_edges} strong edges, {weak_edges} weak edges"
            )

        return insights
