import type { ReactNode } from "react";

/**
 * Phase 4 "Data-Dense Pro, Neutral-Cool Dark" StatCard.
 *
 * Compact KPI tile for the left rail instrument panel.
 * - p-3 padding: tighter than before — fits more KPIs in a vertical rail
 * - value at 1.5rem: rail-appropriate, not hero-oversized
 * - label: mono 9px ALL CAPS kicker
 * - hero tone: restrained indigo wash (8% opacity), no bloom
 * - Numbers always JetBrains Mono tabular-nums — instruments
 * - Authority tag: honest evidence level, NOT verdict
 */

export type StatTone = "default" | "hero";

export interface StatCardProps {
    label: ReactNode;
    value: ReactNode;
    delta?: string | null;
    deltaDirection?: "up" | "down" | "flat";
    deltaIsPositiveGood?: boolean;
    authority?: "T0" | "T1" | "T2" | "T3" | "T4";
    icon?: ReactNode;
    spark?: ReactNode;
    caption?: ReactNode;
    tone?: StatTone;
    className?: string;
}

const AUTHORITY_LABEL: Record<NonNullable<StatCardProps["authority"]>, string> = {
    T0: "diagnostic",
    T1: "metric",
    T2: "eval-gate",
    T3: "release-gate",
    T4: "arbitration",
};

function deltaColor(direction: StatCardProps["deltaDirection"], positiveGood: boolean): string {
    if (!direction || direction === "flat") return "text-muted-foreground";
    const good = direction === "up" ? positiveGood : !positiveGood;
    return good ? "text-[hsl(var(--success))]" : "text-[hsl(var(--destructive))]";
}

export function StatCard({
    label,
    value,
    delta,
    deltaDirection = "flat",
    deltaIsPositiveGood = true,
    authority,
    icon,
    spark,
    caption,
    tone = "default",
    className = "",
}: StatCardProps) {
    const isHero = tone === "hero";
    const containerCls = [
        "group relative flex flex-col gap-2 overflow-hidden rounded-[var(--radius)] border p-3",
        "transition-colors duration-[var(--duration-base)]",
        isHero
            ? "border-primary/30 bg-[hsl(var(--primary)/0.08)] hover:bg-[hsl(var(--primary)/0.12)]"
            : "border-border bg-card hover:bg-secondary/60",
        className,
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <div className={containerCls} style={{ boxShadow: "var(--shadow-card)" }}>
            {/* Label row */}
            <div className="flex items-center justify-between gap-1.5">
                <div className="flex items-center gap-1.5 min-w-0">
                    {icon && (
                        <span
                            className={`inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-[var(--radius-sm)] ${
                                isHero
                                    ? "bg-primary/20 text-primary"
                                    : "bg-muted text-muted-foreground"
                            }`}
                        >
                            {icon}
                        </span>
                    )}
                    <span className="font-mono text-[9px] font-medium uppercase tracking-[0.15em] text-muted-foreground truncate">
                        {label}
                    </span>
                </div>
                {authority && (
                    <span
                        className="shrink-0 rounded-[var(--radius-sm)] border border-border/50 px-1 py-px font-mono text-[8px] font-medium text-muted-foreground/60"
                        title={`Authority: ${authority} (${AUTHORITY_LABEL[authority]})`}
                    >
                        {authority}
                    </span>
                )}
            </div>

            {/* Value */}
            <span
                className={`font-mono font-semibold leading-none tabular-nums text-foreground ${
                    isHero ? "text-[1.5rem]" : "text-[1.25rem]"
                }`}
            >
                {value}
            </span>

            {/* Delta */}
            {delta != null && delta !== "" && (
                <span
                    className={`font-mono text-[10px] font-medium tabular-nums ${deltaColor(
                        deltaDirection,
                        deltaIsPositiveGood,
                    )}`}
                >
                    {delta}
                </span>
            )}

            {/* Sparkline slot */}
            {spark && <div className="h-6 w-full">{spark}</div>}

            {/* Caption */}
            {caption && (
                <span className="font-mono text-[9px] text-muted-foreground/60">{caption}</span>
            )}
        </div>
    );
}
