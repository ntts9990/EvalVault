import { useEffect, useMemo, useRef, useState } from "react";
import type { VisualSpacePoint } from "../services/api";

type PlotlyType = typeof import("plotly.js-dist-min");

const COLOR_MAP: Record<string, string> = {
    "risk.ok": "#10b981",
    "risk.coverage": "#f59e0b",
    "risk.hallucination": "#f43f5e",
    "risk.regression": "#ef4444",
    "risk.improvement": "#22c55e",
    "risk.fail": "#ef4444",
    "risk.unknown": "#94a3b8",
};

const SYMBOL_MAP: Record<string, string> = {
    regression: "triangle-up",
    improvement: "diamond",
    same_fail: "square",
    same_pass: "circle",
    cluster: "hexagon",
    stable: "circle",
    case: "circle",
};

export function SpacePlot3D({ points }: { points: VisualSpacePoint[] }) {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const plotlyRef = useRef<PlotlyType | null>(null);
    const [ready, setReady] = useState(false);
    const [loadError, setLoadError] = useState(false);

    const plotPoints = useMemo(
        () =>
            points.filter(
                (point) =>
                    typeof point.coords.x === "number" &&
                    typeof point.coords.y === "number" &&
                    typeof point.coords.z === "number"
            ),
        [points]
    );

    useEffect(() => {
        let active = true;
        if (plotlyRef.current) {
            setReady(true);
            return;
        }
        import("plotly.js-dist-min")
            .then((module) => {
                if (!active) return;
                const resolved = (module as unknown as { default?: PlotlyType }).default ?? module;
                plotlyRef.current = resolved as PlotlyType;
                setReady(true);
            })
            .catch(() => {
                if (!active) return;
                setLoadError(true);
            });
        return () => {
            active = false;
        };
    }, []);

    useEffect(() => {
        if (!ready || !plotlyRef.current || !containerRef.current) return;

        const x = plotPoints.map((point) => point.coords.x ?? 0);
        const y = plotPoints.map((point) => point.coords.y ?? 0);
        const z = plotPoints.map((point) => point.coords.z ?? 0);
        const labels = plotPoints.map((point) => point.labels?.name || point.id);
        const colors = plotPoints.map(
            (point) => COLOR_MAP[point.encoding?.color || "risk.unknown"] || "#94a3b8"
        );
        const sizes = plotPoints.map((point) => 6 + (point.encoding?.size ?? 0.6) * 10);
        const opacities = plotPoints.map((point) => point.encoding?.opacity ?? 0.85);
        const symbols = plotPoints.map(
            (point) =>
                SYMBOL_MAP[point.encoding?.shape || "circle"] ||
                SYMBOL_MAP["case"] ||
                "circle"
        );

        const data = [
            {
                type: "scatter3d",
                mode: "markers",
                x,
                y,
                z,
                text: labels,
                hovertemplate: "%{text}<br>X %{x:.2f}<br>Y %{y:.2f}<br>Z %{z:.2f}<extra></extra>",
                marker: {
                    color: colors,
                    size: sizes,
                    symbol: symbols,
                    opacity: opacities,
                    line: { color: "rgba(15, 23, 42, 0.35)", width: 1 },
                },
            },
        ];

        const layout = {
            margin: { l: 0, r: 0, t: 0, b: 0 },
            scene: {
                xaxis: {
                    title: "근거 충족도",
                    range: [-1, 1],
                    zeroline: true,
                    zerolinecolor: "#94a3b8",
                    gridcolor: "rgba(148, 163, 184, 0.2)",
                },
                yaxis: {
                    title: "답변 정합성",
                    range: [-1, 1],
                    zeroline: true,
                    zerolinecolor: "#94a3b8",
                    gridcolor: "rgba(148, 163, 184, 0.2)",
                },
                zaxis: {
                    title: "견고성",
                    range: [-1, 1],
                    zeroline: true,
                    zerolinecolor: "#94a3b8",
                    gridcolor: "rgba(148, 163, 184, 0.2)",
                },
                bgcolor: "rgba(0,0,0,0)",
            },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            showlegend: false,
        };

        const plotly = plotlyRef.current;
        if (typeof plotly.react === "function") {
            plotly.react(containerRef.current, data, layout, {
                displayModeBar: false,
                responsive: true,
            });
        } else {
            plotly.newPlot(containerRef.current, data, layout, {
                displayModeBar: false,
                responsive: true,
            });
        }
    }, [ready, plotPoints]);

    useEffect(() => {
        const plotly = plotlyRef.current;
        const container = containerRef.current;
        return () => {
            if (plotly && container) {
                plotly.purge(container);
            }
        };
    }, []);

    if (loadError) {
        return (
            <div
                className={
                    "h-[360px] w-full flex items-center justify-center text-rose-500"
                }
            >
                3D 렌더러를 불러오지 못했습니다
            </div>
        );
    }

    if (!ready) {
        return (
            <div
                className={
                    "h-[360px] w-full flex items-center justify-center text-muted-foreground"
                }
            >
                3D 플롯 로딩 중...
            </div>
        );
    }

    if (plotPoints.length === 0) {
        return (
            <div
                className={
                    "h-[360px] w-full flex items-center justify-center text-muted-foreground"
                }
            >
                표시할 포인트가 없습니다
            </div>
        );
    }

    return <div ref={containerRef} className="h-[360px] w-full" />;
}
