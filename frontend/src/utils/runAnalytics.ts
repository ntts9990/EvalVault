import type { RunSummary } from "../services/api";
import { DATE_RANGE_DISPLAY_LABELS } from "../config/ui";

export const PROJECT_ALL = "__all__";
export const PROJECT_UNASSIGNED = "__unassigned__";

export type DateRangePreset = "7d" | "30d" | "90d" | "year" | "all" | "custom";

export type DateRange = {
    from: Date | null;
    to: Date | null;
    label: string;
};

export type RunStats = {
    totalRuns: number;
    totalTestCases: number;
    passedTestCases: number;
    avgPassRate: number;
    totalCost: number;
};

export type DailyAggregate = {
    date: string;
    totalCases: number;
    passedCases: number;
    passRate: number;
    metricAverages: Record<string, number>;
};

const ONE_DAY_MS = 24 * 60 * 60 * 1000;

function startOfDay(value: Date): Date {
    return new Date(value.getFullYear(), value.getMonth(), value.getDate());
}

function endOfDay(value: Date): Date {
    return new Date(value.getFullYear(), value.getMonth(), value.getDate(), 23, 59, 59, 999);
}

function parseDate(value: string | null | undefined): Date | null {
    if (!value) return null;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return null;
    return parsed;
}

function toLocalDateKey(value: Date): string {
    const year = value.getFullYear();
    const month = String(value.getMonth() + 1).padStart(2, "0");
    const day = String(value.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

export function formatShortDate(dateKey: string): string {
    const parts = dateKey.split("-");
    if (parts.length !== 3) return dateKey;
    return `${parts[1]}/${parts[2]}`;
}

export function normalizeProjectName(value: string | null | undefined): string | null {
    if (!value) return null;
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
}

export function collectProjectNames(runs: RunSummary[]): string[] {
    const names = new Set<string>();
    runs.forEach((run) => {
        const normalized = normalizeProjectName(run.project_name);
        if (normalized) {
            names.add(normalized);
        }
    });
    return Array.from(names).sort((a, b) => a.localeCompare(b));
}

export function filterRunsByProjects(
    runs: RunSummary[],
    selected: string[],
): RunSummary[] {
    if (selected.includes(PROJECT_ALL)) {
        return runs;
    }

    const allowUnassigned = selected.includes(PROJECT_UNASSIGNED);
    const selectedNames = new Set(selected.filter((value) => value !== PROJECT_UNASSIGNED));

    return runs.filter((run) => {
        const normalized = normalizeProjectName(run.project_name);
        if (!normalized) {
            return allowUnassigned;
        }
        return selectedNames.has(normalized);
    });
}

export function resolveDateRange(
    preset: DateRangePreset,
    customStart: string,
    customEnd: string,
): DateRange {
    const today = startOfDay(new Date());

    if (preset === "all") {
        return { from: null, to: null, label: DATE_RANGE_DISPLAY_LABELS.all };
    }

    if (preset === "custom") {
        if (!customStart || !customEnd) {
            return { from: null, to: null, label: DATE_RANGE_DISPLAY_LABELS.custom };
        }
        const from = new Date(`${customStart}T00:00:00`);
        const to = new Date(`${customEnd}T23:59:59`);
        if (Number.isNaN(from.getTime()) || Number.isNaN(to.getTime())) {
            return { from: null, to: null, label: DATE_RANGE_DISPLAY_LABELS.custom };
        }
        return {
            from: startOfDay(from),
            to: endOfDay(to),
            label: `${customStart} ~ ${customEnd}`,
        };
    }

    let startOffset = 0;
    let label = DATE_RANGE_DISPLAY_LABELS.all;
    if (preset === "7d") {
        startOffset = 6;
        label = DATE_RANGE_DISPLAY_LABELS["7d"];
    } else if (preset === "30d") {
        startOffset = 29;
        label = DATE_RANGE_DISPLAY_LABELS["30d"];
    } else if (preset === "90d") {
        startOffset = 89;
        label = DATE_RANGE_DISPLAY_LABELS["90d"];
    } else if (preset === "year") {
        const from = new Date(today.getFullYear(), 0, 1);
        return { from, to: endOfDay(today), label: DATE_RANGE_DISPLAY_LABELS.year };
    }

    const from = new Date(today.getTime() - startOffset * ONE_DAY_MS);
    return { from: startOfDay(from), to: endOfDay(today), label };
}

export function filterRunsByDate(
    runs: RunSummary[],
    from: Date | null,
    to: Date | null,
): RunSummary[] {
    if (!from && !to) return runs;
    return runs.filter((run) => {
        const startedAt = parseDate(run.started_at);
        if (!startedAt) return false;
        if (from && startedAt < from) return false;
        if (to && startedAt > to) return false;
        return true;
    });
}

export function getPreviousRange(from: Date | null, to: Date | null): DateRange {
    if (!from || !to) {
        return { from: null, to: null, label: "Previous period" };
    }

    const start = startOfDay(from);
    const end = endOfDay(to);
    const days = Math.round((end.getTime() - start.getTime()) / ONE_DAY_MS) + 1;
    const prevEnd = new Date(start.getTime() - ONE_DAY_MS);
    const prevStart = new Date(prevEnd.getTime() - (days - 1) * ONE_DAY_MS);
    return {
        from: startOfDay(prevStart),
        to: endOfDay(prevEnd),
        label: "Previous period",
    };
}

export function computeStats(runs: RunSummary[]): RunStats {
    const totalRuns = runs.length;
    const totalTestCases = runs.reduce((sum, run) => sum + run.total_test_cases, 0);
    const passedTestCases = runs.reduce((sum, run) => sum + run.passed_test_cases, 0);
    const totalCost = runs.reduce((sum, run) => sum + (run.total_cost_usd || 0), 0);
    const avgPassRate = totalTestCases > 0 ? passedTestCases / totalTestCases : 0;

    return {
        totalRuns,
        totalTestCases,
        passedTestCases,
        avgPassRate,
        totalCost,
    };
}

export function buildDailyAggregates(
    runs: RunSummary[],
    from: Date | null,
    to: Date | null,
): DailyAggregate[] {
    if (runs.length === 0) return [];

    const parsedRuns = runs
        .map((run) => {
            const startedAt = parseDate(run.started_at);
            if (!startedAt) return null;
            return { run, date: startOfDay(startedAt) };
        })
        .filter((item): item is { run: RunSummary; date: Date } => item !== null);

    if (parsedRuns.length === 0) return [];

    const minDate = parsedRuns.reduce((min, item) => (item.date < min ? item.date : min), parsedRuns[0].date);
    const maxDate = parsedRuns.reduce((max, item) => (item.date > max ? item.date : max), parsedRuns[0].date);

    const rangeStart = from ? startOfDay(from) : minDate;
    const rangeEnd = to ? endOfDay(to) : endOfDay(maxDate);

    const buckets = new Map<string, {
        date: string;
        totalCases: number;
        passedCases: number;
        metricSums: Record<string, number>;
        metricCases: Record<string, number>;
    }>();

    for (
        let cursor = new Date(rangeStart.getTime());
        cursor <= rangeEnd;
        cursor = new Date(cursor.getTime() + ONE_DAY_MS)
    ) {
        const dateKey = toLocalDateKey(cursor);
        buckets.set(dateKey, {
            date: dateKey,
            totalCases: 0,
            passedCases: 0,
            metricSums: {},
            metricCases: {},
        });
    }

    parsedRuns.forEach(({ run, date }) => {
        if (date < rangeStart || date > rangeEnd) return;
        const dateKey = toLocalDateKey(date);
        const bucket = buckets.get(dateKey);
        if (!bucket) return;

        bucket.totalCases += run.total_test_cases;
        bucket.passedCases += run.passed_test_cases;

        const metrics = run.avg_metric_scores || {};
        Object.entries(metrics).forEach(([metric, score]) => {
            if (typeof score !== "number") return;
            bucket.metricSums[metric] = (bucket.metricSums[metric] || 0) + score * run.total_test_cases;
            bucket.metricCases[metric] = (bucket.metricCases[metric] || 0) + run.total_test_cases;
        });
    });

    return Array.from(buckets.values())
        .sort((a, b) => a.date.localeCompare(b.date))
        .map((bucket) => {
            const metricAverages: Record<string, number> = {};
            Object.entries(bucket.metricSums).forEach(([metric, sum]) => {
                const cases = bucket.metricCases[metric] || 0;
                if (cases > 0) {
                    metricAverages[metric] = sum / cases;
                }
            });

            return {
                date: bucket.date,
                totalCases: bucket.totalCases,
                passedCases: bucket.passedCases,
                passRate: bucket.totalCases > 0 ? bucket.passedCases / bucket.totalCases : 0,
                metricAverages,
            };
        });
}

export function addDays(date: Date, days: number): Date {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);
}

export function toDateInputValue(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}
