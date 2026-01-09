export function formatDurationMs(value: number | null | undefined): string {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        return "N/A";
    }
    return `${value.toFixed(0)}ms`;
}

const KOREAN_DATETIME_FORMATTER = new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
});

export function formatDateTime(value: string | null | undefined): string {
    if (!value) {
        return "N/A";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "N/A";
    }
    const parts = KOREAN_DATETIME_FORMATTER.formatToParts(date);
    const lookup: Record<string, string> = {};
    for (const part of parts) {
        lookup[part.type] = part.value;
    }
    if (lookup.year && lookup.month && lookup.day && lookup.hour && lookup.minute && lookup.second) {
        return `${lookup.year}.${lookup.month}.${lookup.day} ${lookup.hour}:${lookup.minute}:${lookup.second}`;
    }
    return KOREAN_DATETIME_FORMATTER.format(date);
}
