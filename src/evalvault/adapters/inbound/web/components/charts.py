"""Dashboard chart components using Plotly."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go

if TYPE_CHECKING:
    from evalvault.ports.inbound.web_port import RunSummary


def create_pass_rate_chart(runs: list[RunSummary]) -> go.Figure:
    """통과율 막대 차트 생성.

    Args:
        runs: 평가 실행 요약 목록

    Returns:
        Plotly Figure 객체
    """
    if not runs:
        # 빈 차트
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 14, "color": "#94A3B8"},
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=300,
        )
        return fig

    # 데이터 준비
    dates = [run.started_at.strftime("%m/%d") for run in runs]
    pass_rates = [run.pass_rate * 100 for run in runs]
    dataset_names = [run.dataset_name for run in runs]

    # 색상 결정 (통과율에 따라)
    colors = []
    for rate in pass_rates:
        if rate >= 80:
            colors.append("#22C55E")  # green
        elif rate >= 60:
            colors.append("#F59E0B")  # yellow
        else:
            colors.append("#EF4444")  # red

    fig = go.Figure(
        data=[
            go.Bar(
                x=dates,
                y=pass_rates,
                marker_color=colors,
                text=[f"{r:.1f}%" for r in pass_rates],
                textposition="outside",
                hovertemplate="<b>%{customdata}</b><br>Pass Rate: %{y:.1f}%<extra></extra>",
                customdata=dataset_names,
            )
        ]
    )

    fig.update_layout(
        title={"text": "Recent Pass Rates", "font": {"size": 16}},
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin={"l": 40, "r": 40, "t": 50, "b": 40},
        yaxis={
            "title": "Pass Rate (%)",
            "range": [0, 110],
            "gridcolor": "rgba(255,255,255,0.1)",
        },
        xaxis={
            "title": "Date",
            "gridcolor": "rgba(255,255,255,0.1)",
        },
    )

    return fig


def create_metric_breakdown_chart(metric_scores: dict[str, float]) -> go.Figure:
    """메트릭별 점수 분포 차트 생성.

    Args:
        metric_scores: 메트릭별 평균 점수

    Returns:
        Plotly Figure 객체
    """
    if not metric_scores:
        fig = go.Figure()
        fig.add_annotation(
            text="No metrics available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 14, "color": "#94A3B8"},
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=300,
        )
        return fig

    metrics = list(metric_scores.keys())
    scores = [v * 100 for v in metric_scores.values()]

    # 레이더 차트
    fig = go.Figure(
        data=[
            go.Scatterpolar(
                r=scores + [scores[0]],  # 닫힌 다각형
                theta=metrics + [metrics[0]],
                fill="toself",
                fillcolor="rgba(59, 130, 246, 0.3)",
                line={"color": "#3B82F6", "width": 2},
                name="Scores",
            )
        ]
    )

    fig.update_layout(
        title={"text": "Metric Breakdown", "font": {"size": 16}},
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin={"l": 60, "r": 60, "t": 50, "b": 40},
        polar={
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "gridcolor": "rgba(255,255,255,0.1)",
            },
            "angularaxis": {
                "gridcolor": "rgba(255,255,255,0.1)",
            },
            "bgcolor": "rgba(0,0,0,0)",
        },
    )

    return fig


def create_trend_chart(runs: list[RunSummary], *, title: str = "Pass Rate Trend") -> go.Figure:
    """통과율 트렌드 라인 차트 생성.

    Args:
        runs: 평가 실행 요약 목록 (날짜순 정렬 권장)

    Returns:
        Plotly Figure 객체
    """
    if not runs:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 14, "color": "#94A3B8"},
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=300,
        )
        return fig

    # 날짜순 정렬
    sorted_runs = sorted(runs, key=lambda r: r.started_at)
    dates = [run.started_at for run in sorted_runs]
    pass_rates = [run.pass_rate * 100 for run in sorted_runs]

    fig = go.Figure(
        data=[
            go.Scatter(
                x=dates,
                y=pass_rates,
                mode="lines+markers",
                line={"color": "#3B82F6", "width": 2},
                marker={"size": 8, "color": "#3B82F6"},
                fill="tozeroy",
                fillcolor="rgba(59, 130, 246, 0.2)",
                hovertemplate="Date: %{x|%Y-%m-%d}<br>Pass Rate: %{y:.1f}%<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title={"text": title, "font": {"size": 16}},
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin={"l": 40, "r": 40, "t": 50, "b": 40},
        yaxis={
            "title": "Pass Rate (%)",
            "range": [0, 105],
            "gridcolor": "rgba(255,255,255,0.1)",
        },
        xaxis={
            "title": "Date",
            "gridcolor": "rgba(255,255,255,0.1)",
        },
    )

    return fig


def create_metric_trend_chart(
    runs: list[RunSummary],
    metrics: list[str],
    *,
    title: str = "Metric Trend",
) -> go.Figure:
    """메트릭별 평균 점수 트렌드 라인 차트 생성."""
    if not runs or not metrics:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 14, "color": "#94A3B8"},
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=300,
        )
        return fig

    sorted_runs = sorted(runs, key=lambda r: r.started_at)
    dates = [run.started_at for run in sorted_runs]
    palette = [
        "#38BDF8",
        "#A78BFA",
        "#F97316",
        "#22C55E",
        "#F59E0B",
        "#EF4444",
    ]

    fig = go.Figure()
    for idx, metric in enumerate(metrics):
        scores = []
        for run in sorted_runs:
            avg_scores = getattr(run, "avg_metric_scores", {}) or {}
            score = avg_scores.get(metric)
            scores.append(score * 100 if score is not None else None)

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=scores,
                mode="lines+markers",
                name=metric,
                line={"width": 2, "color": palette[idx % len(palette)]},
                marker={"size": 6, "color": palette[idx % len(palette)]},
                hovertemplate=(f"Date: %{{x|%Y-%m-%d}}<br>{metric}: %{{y:.1f}}%<extra></extra>"),
            )
        )

    fig.update_layout(
        title={"text": title, "font": {"size": 16}},
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320,
        margin={"l": 40, "r": 40, "t": 50, "b": 40},
        yaxis={
            "title": "Score (%)",
            "range": [0, 105],
            "gridcolor": "rgba(255,255,255,0.1)",
        },
        xaxis={
            "title": "Date",
            "gridcolor": "rgba(255,255,255,0.1)",
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )

    return fig
