import type { ReactNode } from "react";

/**
 * Phase 4 Flagship Dial — radial gauge for a 0..1 ratio (e.g. run pass-rate).
 *
 * Pure SVG, no chart lib. The arc color is driven by the caller (status
 * semantics), NEVER the brand accent — a "pass" dial must not read as branded
 * or as a T1 metric (see docs/frontend/W-PHASE4-DIRECTION.md §2). The numeric
 * center renders in mono with tabular-nums because numbers are instruments.
 */

export interface DialProps {
    /** Ratio in 0..1. */
    value: number;
    /** Diameter in px. */
    size?: number;
    /** Stroke width in px. */
    thickness?: number;
    /** Track + arc color as a CSS color string (e.g. hsl(var(--success))). */
    color?: string;
    /** Center content; defaults to the value as a whole-number percentage. */
    children?: ReactNode;
    /** Accessible label. */
    label?: string;
    className?: string;
}

export function Dial({
    value,
    size = 56,
    thickness = 5,
    color = "hsl(var(--success))",
    children,
    label,
    className = "",
}: DialProps) {
    const clamped = Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0));
    const radius = (size - thickness) / 2;
    const circumference = 2 * Math.PI * radius;
    const dash = circumference * clamped;
    const center = size / 2;
    const pct = Math.round(clamped * 100);

    return (
        <div
            className={`relative inline-flex items-center justify-center ${className}`}
            style={{ width: size, height: size }}
            role="img"
            aria-label={label ?? `${pct} percent`}
        >
            <svg width={size} height={size} className="-rotate-90">
                <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="none"
                    stroke="hsl(var(--border))"
                    strokeWidth={thickness}
                />
                <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="none"
                    stroke={color}
                    strokeWidth={thickness}
                    strokeLinecap="round"
                    strokeDasharray={`${dash} ${circumference - dash}`}
                    style={{
                        transition:
                            "stroke-dasharray var(--duration-slow, 320ms) var(--ease-emphasis, ease-out)",
                    }}
                />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
                {children ?? (
                    <span className="font-mono text-xs font-semibold tabular-nums text-foreground">
                        {pct}
                        <span className="text-[9px] text-muted-foreground">%</span>
                    </span>
                )}
            </div>
        </div>
    );
}
