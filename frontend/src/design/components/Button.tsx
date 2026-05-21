import type { ButtonHTMLAttributes, ReactNode } from "react";
import { forwardRef } from "react";

/**
 * Phase 4 W-S1 Button — Claude design language.
 *
 * Restraint with color: primary uses the single warm accent. ghost is the
 * default for most actions. destructive is rare and intentional.
 */

export type ButtonVariant = "primary" | "secondary" | "ghost" | "destructive";
export type ButtonSize = "sm" | "md" | "lg";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
    primary:
        "bg-primary text-primary-foreground hover:bg-primary/90 border border-primary",
    secondary:
        "bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border",
    ghost:
        "bg-transparent text-foreground hover:bg-muted border border-transparent",
    destructive:
        "bg-destructive text-destructive-foreground hover:bg-destructive/90 border border-destructive",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
    sm: "h-8 px-3 text-sm gap-1.5",
    md: "h-10 px-4 text-sm gap-2",
    lg: "h-12 px-6 text-base gap-2",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: ButtonVariant;
    size?: ButtonSize;
    leading?: ReactNode;
    trailing?: ReactNode;
    loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    function Button(
        {
            variant = "ghost",
            size = "md",
            leading,
            trailing,
            loading = false,
            disabled,
            className = "",
            children,
            ...rest
        },
        ref,
    ) {
        const merged = [
            "inline-flex items-center justify-center rounded-[var(--radius-sm)]",
            "font-medium transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            "disabled:pointer-events-none disabled:opacity-50",
            VARIANT_CLASSES[variant],
            SIZE_CLASSES[size],
            className,
        ]
            .filter(Boolean)
            .join(" ");
        return (
            <button
                ref={ref}
                className={merged}
                disabled={disabled || loading}
                aria-busy={loading || undefined}
                {...rest}
            >
                {loading ? (
                    <span
                        className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent"
                        aria-hidden
                    />
                ) : (
                    leading
                )}
                {children}
                {!loading && trailing}
            </button>
        );
    },
);
