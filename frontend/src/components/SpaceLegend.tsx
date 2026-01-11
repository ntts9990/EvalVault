const COLOR_ITEMS = [
    { label: "정상", color: "#10b981" },
    { label: "커버리지 위험", color: "#f59e0b" },
    { label: "환각 위험", color: "#f43f5e" },
];

const SHAPE_ITEMS = [
    { label: "회귀", shape: "triangle" },
    { label: "개선", shape: "diamond" },
    { label: "실패", shape: "square" },
    { label: "안정", shape: "circle" },
    { label: "클러스터", shape: "hexagon" },
];

const QUADRANT_ITEMS = [
    { label: "확장", hint: "검색·생성 모두 안정" },
    { label: "검색 강화", hint: "검색 커버리지 개선" },
    { label: "생성 개선", hint: "답변 정합성 개선" },
    { label: "재점검", hint: "파이프라인 점검" },
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
                    색상
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
                    형태
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
                    사분면
                </p>
                {QUADRANT_ITEMS.map((item) => (
                    <div key={item.label} className="flex items-start gap-2">
                        <span className="text-foreground">{item.label}</span>
                        <span className="text-muted-foreground">· {item.hint}</span>
                    </div>
                ))}
                <div className="text-[11px] text-muted-foreground">
                    크기는 케이스 규모/비용을 의미합니다.
                </div>
            </div>
        </div>
    );
}
