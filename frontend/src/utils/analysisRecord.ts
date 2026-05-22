import type { PrioritySummary } from "../components/PrioritySummaryPanel";

export const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === "object" && value !== null;

export const isPlainRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === "object" && value !== null && !Array.isArray(value);

export const normalizeNumber = (value: unknown) => {
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string") {
        const parsed = Number(value);
        if (Number.isFinite(parsed)) return parsed;
    }
    return null;
};

export const getNestedValue = (record: Record<string, unknown>, path: string[]) => {
    let current: unknown = record;
    for (const key of path) {
        if (!isPlainRecord(current)) return null;
        current = current[key];
    }
    return normalizeNumber(current);
};

export const getNodeStatus = (node: unknown) => {
    if (!isRecord(node)) return "pending";
    const status = node.status;
    return typeof status === "string" ? status : "pending";
};

export const getNodeError = (node: unknown) => {
    if (!isRecord(node)) return null;
    const error = node.error;
    if (typeof error === "string") return error;
    return error ? String(error) : null;
};

export const getNodeOutput = (
    nodeResults: Record<string, unknown> | null | undefined,
    nodeId: string,
) => {
    if (!nodeResults) return null;
    const node = nodeResults[nodeId];
    if (!isRecord(node)) return null;
    return node.output;
};

export function isPrioritySummary(value: unknown): value is PrioritySummary {
    if (!isPlainRecord(value)) return false;
    return Array.isArray(value.bottom_cases) || Array.isArray(value.impact_cases);
}
