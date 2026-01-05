export function normalizeScore(value: number | null | undefined): number {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        return 0;
    }
    return value;
}

export function safeAverage(values: Array<number | null | undefined>): number {
    if (values.length === 0) {
        return 0;
    }
    const normalized = values.map(normalizeScore);
    const sum = normalized.reduce((acc, val) => acc + val, 0);
    return normalized.length ? sum / normalized.length : 0;
}

export function formatScore(value: number | null | undefined, digits: number = 2): string {
    return normalizeScore(value).toFixed(digits);
}
