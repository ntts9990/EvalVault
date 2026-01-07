export const SUMMARY_METRICS = [
    "summary_faithfulness",
    "summary_score",
    "entity_preservation",
] as const;

export const SUMMARY_METRIC_THRESHOLDS: Record<string, number> = {
    summary_faithfulness: 0.9,
    summary_score: 0.85,
    entity_preservation: 0.9,
};

export type SummaryMetric = (typeof SUMMARY_METRICS)[number];
