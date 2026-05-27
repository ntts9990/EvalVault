import type { ReactNode } from "react";

/**
 * Phase 4 Evidence-Based Design pass — StatCard.
 *
 * Von Restorff / isolation: hero tone creates clear visual dominance via
 * larger value (2rem vs 1rem), indigo tint, sparkline slot, and explicit
 * group separation in the rail. Non-hero cards are intentionally subordinate.
 *
 * Miller / chunking: authority tag preserved for honest evidence level.
 * Progressive disclosure: spark + caption available but not forced.
 * Dark ergonomics: value color is var(--foreground) = #dcdee6, not pure white.
 * Numerical cognition: value always JetBrains Mono tabular-nums.
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
        "relative flex flex-col overflow-hidden rounded-[var(--radius)] border",
        "transition-colors duration-[var(--duration-base)]",
        isHero
            // Von Restorff: hero is visually isolated — tinted border + bg wash
            ? "gap-2.5 p-3 border-primary/35 bg-[hsl(var(--primary)/0.07)] hover:bg-[hsl(var(--primary)/0.1)]"
            // Subordinate cards: neutral, no tint, no glow — clearly secondary
            : "gap-1.5 p-3 border-border/50 bg-transparent hover:bg-secondary/40",
        className,
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <div className={containerCls} style={{ boxShadow: isHero ? "var(--shadow-card)" : "none" }}>
            {/* Label row: icon stripped from non-hero cards (Tufte: remove redundant encoding) */}
            <div className="flex items-center justify-between gap-1.5">
                <div className="flex items-center gap-1.5 min-w-0">
                    {/* Icon only shown on hero (Von Restorff isolation) */}
                    {icon && isHero && (
                        <span className="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-[var(--radius-sm)] bg-primary/20 text-primary">
                            {icon}
                        </span>
                    )}
                    {/* 3-level hierarchy level 3: kicker label — smallest, muted */}
                    <span className="font-mono text-[9px] font-medium uppercase tracking-[0.15em] text-muted-foreground truncate">
                        {label}
                    </span>
                </div>
                {authority && (
                    <span
                        className="shrink-0 rounded-[var(--radius-sm)] border border-border/40 px-1 py-px font-mono text-[8px] text-muted-foreground/50"
                        title={`Authority: ${authority} — ${AUTHORITY_LABEL[authority]}`}
                    >
                        {authority}
                    </span>
                )}
            </div>

            {/*
             * 3-level hierarchy:
             *   L1 hero value: 2rem — dominant, draws the eye first (Von Restorff)
             *   L2 subordinate value: 1.125rem — clearly smaller, scannable
             *   L3 label/caption: 9px mono kicker — lowest
             *
             * All values: JetBrains Mono tabular-nums (numerical cognition, column alignment)
             */}
            <span
                className={`font-mono font-semibold leading-none tabular-nums ${
                    isHero
                        ? "text-[2rem] text-foreground"
                        : "text-[1.125rem] text-foreground/80"
                }`}
            >
                {value}
            </span>

            {/* Delta — color + direction (redundant coding) */}
            {delta != null && delta !== "" && (
                <span
                    className={`font-mono text-[10px] font-medium tabular-nums ${deltaColor(
                        deltaDirection,
                        deltaIsPositiveGood,
                    )}`}
                >
                    {deltaDirection === "up" ? "↑ " : deltaDirection === "down" ? "↓ " : ""}
                    {delta}
                </span>
            )}

            {/* Sparkline slot — hero only (progressive disclosure, Tufte) */}
            {spark && isHero && <div className="h-7 w-full">{spark}</div>}

            {/* Caption — lowest hierarchy, muted */}
            {caption && (
                <span className="font-mono text-[9px] text-muted-foreground/50">{caption}</span>
            )}
        </div>
    );
}
