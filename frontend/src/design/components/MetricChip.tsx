import type { ReactNode } from "react";

/**
 * Phase 4 W-S1 MetricChip — single metric value with optional delta.
 *
 * Used for the dashboard / run-detail metric grids.
 * Delta is colored only when materially different; default is neutral.
 */

export interface MetricChipProps {
    label: ReactNode;
    value: number | string;
    /** Optional delta vs baseline; positive/negative auto-colored. */
    delta?: number;
    /** Format the value (e.g. percentage, fixed-precision). */
    format?: "number" | "percent" | "fixed2";
    /** Hint at the metric's authority level (T1 metric, T2 verdict, etc.). */
    authority?: "T0" | "T1" | "T2" | "T3" | "T4";
    /** Optional trailing slot (e.g. icon, sparkline). */
    trailing?: ReactNode;
    className?: string;
}

function formatValue(value: number | string, format: MetricChipProps["format"]) {
    if (typeof value === "string") return value;
    if (format === "percent") return `${(value * 100).toFixed(1)}%`;
    if (format === "fixed2") return value.toFixed(2);
    return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(3);
}

function deltaSign(delta: number): string {
    if (delta > 0) return `+${delta.toFixed(3)}`;
    if (delta < 0) return delta.toFixed(3);
    return "0";
}

function deltaClass(delta: number, threshold = 0.001) {
    if (delta > threshold) return "text-[hsl(var(--success))]";
    if (delta < -threshold) return "text-[hsl(var(--destructive))]";
    return "text-muted-foreground";
}

const AUTHORITY_LABEL: Record<NonNullable<MetricChipProps["authority"]>, string> = {
    T0: "diagnostic",
    T1: "metric",
    T2: "eval-gate",
    T3: "release-gate",
    T4: "arbitration",
};

export function MetricChip({
    label,
    value,
    delta,
    format = "number",
    authority,
    trailing,
    className = "",
}: MetricChipProps) {
    return (
        <div
            className={`flex flex-col gap-1 rounded-[var(--radius)] border border-border bg-card p-4 ${className}`}
        >
            <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    {label}
                </span>
                {authority && (
                    <span
                        className="rounded-full border border-border px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground"
                        title={`Authority: ${authority} (${AUTHORITY_LABEL[authority]})`}
                    >
                        {authority}
                    </span>
                )}
            </div>
            <div className="flex items-baseline gap-2">
                <span className="font-mono text-2xl font-semibold tabular-nums text-foreground">
                    {formatValue(value, format)}
                </span>
                {typeof delta === "number" && (
                    <span className={`font-mono text-xs tabular-nums ${deltaClass(delta)}`}>
                        {deltaSign(delta)}
                    </span>
                )}
                {trailing}
            </div>
        </div>
    );
}
