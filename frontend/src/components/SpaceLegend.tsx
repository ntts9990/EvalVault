const COLOR_ITEMS = [
    { label: "Healthy", color: "#10b981" },
    { label: "Coverage Risk", color: "#f59e0b" },
    { label: "Hallucination Risk", color: "#f43f5e" },
];

const SHAPE_ITEMS = [
    { label: "Regression", shape: "triangle" },
    { label: "Improvement", shape: "diamond" },
    { label: "Failure", shape: "square" },
    { label: "Stable", shape: "circle" },
    { label: "Cluster", shape: "hexagon" },
];

const QUADRANT_ITEMS = [
    { label: "Expand", hint: "Strong search & generation" },
    { label: "Search Boost", hint: "Improve retrieval coverage" },
    { label: "Generation Fix", hint: "Improve answer integrity" },
    { label: "Reset", hint: "Recheck pipeline" },
];

const renderShape = (shape: string) => {
    const size = 12;
    const half = size / 2;
    if (shape === "square") {
        return <rect x={2} y={2} width={size - 4} height={size - 4} rx={2} />;
    }
    if (shape === "triangle") {
        return <polygon points={`${half},2 ${size - 2},${size - 2} 2,${size - 2}`} />;
    }
    if (shape === "diamond") {
        return (
            <polygon points={`${half},2 ${size - 2},${half} ${half},${size - 2} 2,${half}`} />
        );
    }
    if (shape === "hexagon") {
        return (
            <polygon
                points={
                    `${half},2 ${size - 2},${half - 2} ${size - 2},${half + 2} ` +
                    `${half},${size - 2} 2,${half + 2} 2,${half - 2}`
                }
            />
        );
    }
    return <circle cx={half} cy={half} r={half - 2} />;
};

export function SpaceLegend() {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-muted-foreground">
            <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
                    Color
                </p>
                {COLOR_ITEMS.map((item) => (
                    <div key={item.label} className="flex items-center gap-2">
                        <span
                            className="h-2.5 w-2.5 rounded-full"
                            style={{ backgroundColor: item.color }}
                        />
                        <span>{item.label}</span>
                    </div>
                ))}
            </div>
            <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
                    Shape
                </p>
                {SHAPE_ITEMS.map((item) => (
                    <div key={item.label} className="flex items-center gap-2">
                        <svg width="14" height="14" className="text-foreground">
                            <g fill="currentColor">{renderShape(item.shape)}</g>
                        </svg>
                        <span>{item.label}</span>
                    </div>
                ))}
            </div>
            <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
                    Quadrant
                </p>
                {QUADRANT_ITEMS.map((item) => (
                    <div key={item.label} className="flex items-start gap-2">
                        <span className="text-foreground">{item.label}</span>
                        <span className="text-muted-foreground">· {item.hint}</span>
                    </div>
                ))}
                <div className="text-[11px] text-muted-foreground">
                    Size encodes case volume or cost.
                </div>
            </div>
        </div>
    );
}
