import type { HTMLAttributes, ReactNode, TableHTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from "react";
import { forwardRef } from "react";

/**
 * Phase 4 W-S1 Table — accessible primitive set.
 *
 * Korean text support: avoids forcing latin font; inherits parent font-family
 * which includes IBM Plex Sans KR fallback (configured in tailwind.config.js).
 */

export const Table = forwardRef<
    HTMLTableElement,
    TableHTMLAttributes<HTMLTableElement>
>(function Table({ className = "", ...rest }, ref) {
    return (
        <div className="w-full overflow-auto rounded-[var(--radius)] border border-border">
            <table
                ref={ref}
                className={`w-full caption-bottom text-sm ${className}`}
                {...rest}
            />
        </div>
    );
});

export function TableHeader({
    className = "",
    ...rest
}: HTMLAttributes<HTMLTableSectionElement>) {
    return (
        <thead
            className={`border-b border-border bg-muted/50 ${className}`}
            {...rest}
        />
    );
}

export function TableBody({
    className = "",
    ...rest
}: HTMLAttributes<HTMLTableSectionElement>) {
    return (
        <tbody
            className={`[&_tr:last-child]:border-0 ${className}`}
            {...rest}
        />
    );
}

export function TableFooter({
    className = "",
    ...rest
}: HTMLAttributes<HTMLTableSectionElement>) {
    return (
        <tfoot
            className={`border-t border-border bg-muted/50 font-medium ${className}`}
            {...rest}
        />
    );
}

export function TableRow({
    className = "",
    ...rest
}: HTMLAttributes<HTMLTableRowElement>) {
    return (
        <tr
            className={`border-b border-border transition-colors hover:bg-accent/40 data-[state=selected]:bg-accent ${className}`}
            {...rest}
        />
    );
}

export function TableHead({
    className = "",
    ...rest
}: ThHTMLAttributes<HTMLTableCellElement>) {
    return (
        <th
            className={`h-10 px-4 text-left align-middle text-xs font-semibold uppercase tracking-wide text-muted-foreground [&:has([role=checkbox])]:pr-0 ${className}`}
            {...rest}
        />
    );
}

export function TableCell({
    className = "",
    ...rest
}: TdHTMLAttributes<HTMLTableCellElement>) {
    return (
        <td
            className={`p-4 align-middle [&:has([role=checkbox])]:pr-0 ${className}`}
            {...rest}
        />
    );
}

export function TableCaption({
    className = "",
    children,
    ...rest
}: HTMLAttributes<HTMLTableCaptionElement> & { children?: ReactNode }) {
    return (
        <caption
            className={`mt-4 text-sm text-muted-foreground ${className}`}
            {...rest}
        >
            {children}
        </caption>
    );
}
