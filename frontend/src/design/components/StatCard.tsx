import type { ReactNode } from "react";

/**
 * Phase 4 "Data-Dense Pro × Warm" StatCard — instrument-panel KPI tile.
 *
 * Tighter than the editorial build: p-4 not p-5, value at 1.75rem not 2rem,
 * smaller gap, mono label kicker in ALL CAPS tracking. The hero card gets a
 * restrained clay wash; the dark-ink CTA foreground rule applies here too
 * (icon on hero uses bg-primary/15 + text-primary, never cream-on-clay).
 *
 * Numbers are instruments: value always renders in JetBrains Mono tabular-nums.
 * Authority hint tags evidence level (T1/T2) — NOT a verdict.
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
        // Tighter padding + radius for instrument-panel density
        "group relative flex flex-col gap-2.5 overflow-hidden rounded-[var(--radius)] border p-4",
        "transition-transform duration-[var(--duration-base)] hover:-translate-y-px",
        isHero
            ? "border-primary/25 bg-[hsl(var(--primary)/0.08)]"
            : "border-border bg-card",
        className,
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <div className={containerCls} style={{ boxShadow: "var(--shadow-card)" }}>
            {/* Clay glow bloom — hero card only, subtle instrument accent */}
            {isHero && (
                <span
                    aria-hidden
                    className="pointer-events-none absolute -right-6 -top-6 h-20 w-20 rounded-full bg-primary/12 blur-xl"
                />
            )}

            {/* Label row */}
            <div className="relative flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                    {icon && (
                        <span
                            className={`inline-flex h-5 w-5 items-center justify-center rounded-[var(--radius-sm)] ${
                                isHero
                                    ? "bg-primary/15 text-primary"
                                    : "bg-muted text-muted-foreground"
                            }`}
                        >
                            {icon}
                        </span>
                    )}
                    <span className="font-mono text-[10px] font-medium uppercase tracking-[0.15em] text-muted-foreground">
                        {label}
                    </span>
                </div>
                {authority && (
                    <span
                        className="rounded-[var(--radius-sm)] border border-border/60 px-1 py-px font-mono text-[9px] font-medium text-muted-foreground/70"
                        title={`Authority: ${authority} (${AUTHORITY_LABEL[authority]})`}
                    >
                        {authority}
                    </span>
                )}
            </div>

            {/* Value + delta */}
            <div className="relative flex items-baseline justify-between gap-2">
                <span className="font-mono text-[1.75rem] font-semibold leading-none tabular-nums text-foreground">
                    {value}
                </span>
                {delta != null && delta !== "" && (
                    <span
                        className={`font-mono text-[11px] font-medium tabular-nums ${deltaColor(
                            deltaDirection,
                            deltaIsPositiveGood,
                        )}`}
                    >
                        {delta}
                    </span>
                )}
            </div>

            {/* Sparkline slot — compact 28px height for density */}
            {spark && <div className="relative h-7 w-full">{spark}</div>}

            {/* Caption */}
            {caption && (
                <span className="relative font-mono text-[10px] text-muted-foreground/70">
                    {caption}
                </span>
            )}
        </div>
    );
}
