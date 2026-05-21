import type { HTMLAttributes, ReactNode } from "react";
import { forwardRef } from "react";

/**
 * Phase 4 W-S1 Card — minimal container with optional header / footer.
 *
 * Generous whitespace (--space-6 default padding). Subtle border, no shadow
 * by default. Claude design avoids heavy elevation.
 */

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    interactive?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
    { interactive = false, className = "", ...rest },
    ref,
) {
    const cls = [
        "rounded-[var(--radius)] border border-border bg-card text-card-foreground",
        interactive
            ? "transition-colors hover:bg-accent/40 cursor-pointer focus-within:ring-2 focus-within:ring-ring"
            : "",
        className,
    ]
        .filter(Boolean)
        .join(" ");
    return <div ref={ref} className={cls} {...rest} />;
});

export function CardHeader({
    className = "",
    children,
    ...rest
}: HTMLAttributes<HTMLDivElement>) {
    return (
        <div
            className={`flex flex-col gap-1.5 p-6 pb-3 ${className}`}
            {...rest}
        >
            {children}
        </div>
    );
}

export function CardTitle({
    className = "",
    children,
    ...rest
}: HTMLAttributes<HTMLHeadingElement>) {
    return (
        <h3
            className={`text-lg font-semibold leading-snug tracking-tight text-foreground ${className}`}
            {...rest}
        >
            {children}
        </h3>
    );
}

export function CardDescription({
    className = "",
    children,
    ...rest
}: HTMLAttributes<HTMLParagraphElement>) {
    return (
        <p className={`text-sm text-muted-foreground ${className}`} {...rest}>
            {children}
        </p>
    );
}

export function CardContent({
    className = "",
    children,
    ...rest
}: HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={`p-6 pt-3 ${className}`} {...rest}>
            {children}
        </div>
    );
}

export function CardFooter({
    className = "",
    children,
    ...rest
}: HTMLAttributes<HTMLDivElement>) {
    return (
        <div
            className={`flex items-center justify-end gap-2 border-t border-border p-6 pt-3 ${className}`}
            {...rest}
        >
            {children}
        </div>
    );
}

export interface ComposedCardProps {
    title?: ReactNode;
    description?: ReactNode;
    footer?: ReactNode;
    interactive?: boolean;
    className?: string;
    children?: ReactNode;
}

/**
 * Convenience wrapper for the common Card layout.
 */
export function ComposedCard({
    title,
    description,
    footer,
    interactive,
    className,
    children,
}: ComposedCardProps) {
    return (
        <Card interactive={interactive} className={className}>
            {(title || description) && (
                <CardHeader>
                    {title && <CardTitle>{title}</CardTitle>}
                    {description && <CardDescription>{description}</CardDescription>}
                </CardHeader>
            )}
            {children && <CardContent>{children}</CardContent>}
            {footer && <CardFooter>{footer}</CardFooter>}
        </Card>
    );
}
