import type { ReactNode } from "react";

/**
 * Phase 4 W-S1 EmptyState — for empty lists, error states, "no data" surfaces.
 *
 * Generous vertical whitespace; muted foreground; optional icon + CTA.
 * Keep messages short and action-oriented (Claude design pattern).
 */

export interface EmptyStateProps {
    icon?: ReactNode;
    title: ReactNode;
    description?: ReactNode;
    action?: ReactNode;
    /** Compact mode tightens vertical spacing (for inline empties). */
    compact?: boolean;
    className?: string;
}

export function EmptyState({
    icon,
    title,
    description,
    action,
    compact = false,
    className = "",
}: EmptyStateProps) {
    const verticalSpacing = compact ? "py-6" : "py-16";
    return (
        <div
            className={`flex flex-col items-center justify-center text-center ${verticalSpacing} ${className}`}
            role="status"
        >
            {icon && (
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-muted text-muted-foreground">
                    {icon}
                </div>
            )}
            <h3 className="text-base font-semibold text-foreground">{title}</h3>
            {description && (
                <p className="mt-1 max-w-md text-sm text-muted-foreground">
                    {description}
                </p>
            )}
            {action && <div className="mt-4">{action}</div>}
        </div>
    );
}
