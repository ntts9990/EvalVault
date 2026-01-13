import {
    ResponsiveContainer,
    ScatterChart,
    Scatter,
    XAxis,
    YAxis,
    Tooltip,
    ReferenceLine,
} from "recharts";
import type { ReactElement } from "react";
import type { VisualSpacePoint } from "../services/api";

type PlotPoint = {
    id: string;
    x: number;
    y: number;
    color?: string;
    size?: number;
    shape?: string;
    opacity?: number;
    quadrant?: string | null;
    hint?: string | null;
};

type ScatterShapeProps = {
    cx?: number;
    cy?: number;
    payload?: PlotPoint;
};

const hasCoordinates = (
    point: VisualSpacePoint
): point is VisualSpacePoint & { coords: { x: number; y: number } } =>
    typeof point.coords.x === "number"
    && Number.isFinite(point.coords.x)
    && typeof point.coords.y === "number"
    && Number.isFinite(point.coords.y);

const COLOR_MAP: Record<string, string> = {
    "risk.ok": "#10b981",
    "risk.coverage": "#f59e0b",
    "risk.hallucination": "#f43f5e",
    "risk.regression": "#ef4444",
    "risk.improvement": "#22c55e",
    "risk.fail": "#ef4444",
    "risk.unknown": "#94a3b8",
};

const SHAPE_MAP: Record<string, "circle" | "triangle" | "diamond" | "square" | "hexagon"> = {
    regression: "triangle",
    improvement: "diamond",
    same_fail: "square",
    same_pass: "circle",
    cluster: "hexagon",
    stable: "circle",
    case: "circle",
};

const formatAxis = (value: number) => value.toFixed(2);

const polygonPoints = (
    cx: number,
    cy: number,
    radius: number,
    sides: number,
    rotation: number = 0
) => {
    const step = (Math.PI * 2) / sides;
    const points = Array.from({ length: sides }, (_, index) => {
        const angle = rotation + step * index;
        const x = cx + radius * Math.cos(angle);
        const y = cy + radius * Math.sin(angle);
        return `${x},${y}`;
    });
    return points.join(" ");
};

const renderShape = (
    shape: string | undefined,
    cx: number,
    cy: number,
    radius: number,
    color: string,
    opacity: number
) => {
    const symbol = SHAPE_MAP[shape || "case"] || "circle";
    if (symbol === "square") {
        return (
            <rect
                x={cx - radius}
                y={cy - radius}
                width={radius * 2}
                height={radius * 2}
                fill={color}
                fillOpacity={opacity}
                stroke="#0f172a"
                strokeOpacity={0.15}
                strokeWidth={1}
            />
        );
    }
    if (symbol === "triangle") {
        return (
            <polygon
                points={polygonPoints(cx, cy, radius, 3, -Math.PI / 2)}
                fill={color}
                fillOpacity={opacity}
                stroke="#0f172a"
                strokeOpacity={0.15}
                strokeWidth={1}
            />
        );
    }
    if (symbol === "diamond") {
        return (
            <polygon
                points={polygonPoints(cx, cy, radius, 4, Math.PI / 4)}
                fill={color}
                fillOpacity={opacity}
                stroke="#0f172a"
                strokeOpacity={0.15}
                strokeWidth={1}
            />
        );
    }
    if (symbol === "hexagon") {
        return (
            <polygon
                points={polygonPoints(cx, cy, radius, 6, Math.PI / 6)}
                fill={color}
                fillOpacity={opacity}
                stroke="#0f172a"
                strokeOpacity={0.15}
                strokeWidth={1}
            />
        );
    }
    return (
        <circle
            cx={cx}
            cy={cy}
            r={radius}
            fill={color}
            fillOpacity={opacity}
            stroke="#0f172a"
            strokeOpacity={0.15}
            strokeWidth={1}
        />
    );
};

export function SpacePlot2D({ points }: { points: VisualSpacePoint[] }) {
    const plotPoints: PlotPoint[] = points
        .filter(hasCoordinates)
        .map((point) => ({
            id: point.id,
            x: point.coords.x,
            y: point.coords.y,
            color: point.encoding?.color,
            size: point.encoding?.size,
            shape: point.encoding?.shape,
            opacity: point.encoding?.opacity,
            quadrant: point.labels?.quadrant,
            hint: point.labels?.guide_hint,
        }));

    const renderScatterShape = (props: unknown): ReactElement => {
        const { cx, cy, payload } = props as ScatterShapeProps;
        if (cx == null || cy == null || !payload) return <g />;
        const color = COLOR_MAP[payload.color || "risk.unknown"] || COLOR_MAP["risk.unknown"];
        const radius = 4 + Math.max(0, Math.min(1, payload.size ?? 0.6)) * 6;
        const opacity = payload.opacity ?? 0.85;
        return renderShape(payload.shape, cx, cy, radius, color, opacity);
    };

    return (
        <div className="h-[360px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 16, right: 24, bottom: 24, left: 24 }}>
                    <XAxis
                        type="number"
                        dataKey="x"
                        domain={[-1, 1]}
                        tickFormatter={formatAxis}
                        label={{
                            value: "근거 충족도",
                            position: "insideBottom",
                            offset: -8,
                        }}
                    />
                    <YAxis
                        type="number"
                        dataKey="y"
                        domain={[-1, 1]}
                        tickFormatter={formatAxis}
                        label={{
                            value: "답변 정합성",
                            angle: -90,
                            position: "insideLeft",
                            offset: -8,
                        }}
                    />
                    <ReferenceLine x={0} stroke="#94a3b8" strokeDasharray="4 4" />
                    <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 4" />
                    <Tooltip
                        cursor={{ strokeDasharray: "4 4" }}
                        content={({ active, payload }) => {
                            if (!active || !payload?.length) return null;
                            const item = payload[0].payload as PlotPoint;
                            return (
                                <div
                                    className={
                                        "rounded-lg border border-border bg-card px-3 py-2 " +
                                        "text-xs shadow-sm"
                                    }
                                >
                                    <div className="font-semibold text-foreground">{item.id}</div>
                                    <div className="text-muted-foreground">
                                        X {item.x.toFixed(2)} · Y {item.y.toFixed(2)}
                                    </div>
                                    {item.quadrant && (
                                        <div className="text-muted-foreground">
                                            Quadrant: {item.quadrant}
                                        </div>
                                    )}
                                    {item.hint && (
                                        <div className="text-muted-foreground">
                                            Hint: {item.hint}
                                        </div>
                                    )}
                                </div>
                            );
                        }}
                    />
                    <Scatter data={plotPoints} shape={renderScatterShape} />
                </ScatterChart>
            </ResponsiveContainer>
        </div>
    );
}
