export function formatDurationMs(value: number | null | undefined): string {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        return "N/A";
    }
    return `${value.toFixed(0)}ms`;
}

export function formatDateTime(value: string | null | undefined): string {
    if (!value) {
        return "N/A";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "N/A";
    }
    return date.toLocaleString();
}
