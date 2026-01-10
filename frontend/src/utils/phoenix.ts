export const getPhoenixUiUrl = (endpoint: unknown): string | null => {
    if (typeof endpoint !== "string") return null;
    const trimmed = endpoint.trim();
    if (!trimmed) return null;
    const normalized = trimmed.replace(/\/+$/, "");
    const suffix = "/v1/traces";
    if (normalized.endsWith(suffix)) {
        return normalized.slice(0, -suffix.length);
    }
    return normalized;
};
