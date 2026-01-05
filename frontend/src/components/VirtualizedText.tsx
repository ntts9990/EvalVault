import { useEffect, useMemo, useRef, useState } from "react";

type VirtualizedTextProps = {
    text: string;
    height?: number | string;
    lineHeight?: number;
    className?: string;
    overscan?: number;
    minLinesForVirtualization?: number;
};

export function VirtualizedText({
    text,
    height = "20rem",
    lineHeight = 18,
    className = "",
    overscan = 6,
    minLinesForVirtualization = 200,
}: VirtualizedTextProps) {
    const lines = useMemo(() => text.split("\n"), [text]);
    const containerRef = useRef<HTMLDivElement | null>(null);
    const [scrollTop, setScrollTop] = useState(0);
    const [containerHeight, setContainerHeight] = useState(0);

    useEffect(() => {
        const node = containerRef.current;
        if (!node) return;

        const updateSize = () => {
            setContainerHeight(node.clientHeight || 0);
        };
        updateSize();

        if (typeof ResizeObserver === "undefined") return;
        const observer = new ResizeObserver(() => updateSize());
        observer.observe(node);
        return () => observer.disconnect();
    }, [height]);

    if (lines.length < minLinesForVirtualization) {
        return (
            <pre className={`whitespace-pre ${className}`.trim()}>
                {text}
            </pre>
        );
    }

    const totalHeight = lines.length * lineHeight;
    const visibleCount = containerHeight
        ? Math.ceil(containerHeight / lineHeight)
        : 0;
    const startIndex = Math.max(0, Math.floor(scrollTop / lineHeight) - overscan);
    const endIndex = Math.min(lines.length, startIndex + visibleCount + overscan * 2);
    const offsetY = startIndex * lineHeight;
    const visibleLines = lines.slice(startIndex, endIndex).join("\n");
    const heightStyle = typeof height === "number" ? `${height}px` : height;

    return (
        <div
            ref={containerRef}
            onScroll={(event) => setScrollTop(event.currentTarget.scrollTop)}
            className={`overflow-auto ${className}`.trim()}
            style={{ height: heightStyle }}
        >
            <div style={{ height: totalHeight, position: "relative" }}>
                <pre
                    className="whitespace-pre"
                    style={{
                        position: "absolute",
                        top: offsetY,
                        left: 0,
                        right: 0,
                        lineHeight: `${lineHeight}px`,
                    }}
                >
                    {visibleLines}
                </pre>
            </div>
        </div>
    );
}
