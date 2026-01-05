export function formatDurationMs(value: number | null | undefined): string {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        return "N/A";
    }
    return `${value.toFixed(0)}ms`;
}
