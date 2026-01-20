import type { DateRangePreset } from "../utils/runAnalytics";

export const DEFAULT_DATE_RANGE_PRESET: DateRangePreset = "30d";
export const CUSTOM_RANGE_DEFAULT_DAYS = 30;

export const DATE_RANGE_OPTION_LABELS: Record<DateRangePreset, string> = {
    "7d": "Last 7 days",
    "30d": "Last 30 days",
    "90d": "Last 90 days",
    year: "This year",
    all: "All time",
    custom: "Custom range",
};

export const DATE_RANGE_DISPLAY_LABELS: Record<DateRangePreset, string> = {
    "7d": "Last 7 days",
    "30d": "Last 30 days",
    "90d": "Last 90 days",
    year: "This year",
    all: "All",
    custom: "Custom",
};

export const DATE_RANGE_OPTIONS: { value: DateRangePreset; label: string }[] = [
    { value: "7d", label: DATE_RANGE_OPTION_LABELS["7d"] },
    { value: "30d", label: DATE_RANGE_OPTION_LABELS["30d"] },
    { value: "90d", label: DATE_RANGE_OPTION_LABELS["90d"] },
    { value: "year", label: DATE_RANGE_OPTION_LABELS.year },
    { value: "all", label: DATE_RANGE_OPTION_LABELS.all },
    { value: "custom", label: DATE_RANGE_OPTION_LABELS.custom },
];

export const CHART_METRIC_COLORS = [
    "#38BDF8",
    "#A78BFA",
    "#F97316",
    "#22C55E",
    "#F59E0B",
    "#EF4444",
];

export const PASS_RATE_COLOR_BANDS = [
    {
        min: 0.9,
        className: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    },
    {
        min: 0.7,
        className: "text-blue-500 bg-blue-500/10 border-blue-500/20",
    },
    {
        min: 0.5,
        className: "text-amber-500 bg-amber-500/10 border-amber-500/20",
    },
    {
        min: 0,
        className: "text-rose-500 bg-rose-500/10 border-rose-500/20",
    },
];

export const SUMMARY_METRICS = [
    "summary_faithfulness",
    "summary_score",
    "entity_preservation",
    "summary_accuracy",
    "summary_risk_coverage",
    "summary_non_definitive",
    "summary_needs_followup",
] as const;

export const SUMMARY_METRICS_LLM = ["summary_faithfulness", "summary_score"] as const;
export const SUMMARY_METRICS_RULE = [
    "entity_preservation",
    "summary_accuracy",
    "summary_risk_coverage",
    "summary_non_definitive",
    "summary_needs_followup",
] as const;

export const SUMMARY_METRIC_THRESHOLDS: Record<string, number> = {
    summary_faithfulness: 0.9,
    summary_score: 0.85,
    entity_preservation: 0.9,
    summary_accuracy: 0.9,
    summary_risk_coverage: 0.9,
    summary_non_definitive: 0.8,
    summary_needs_followup: 0.8,
};

export type SummaryMetric = (typeof SUMMARY_METRICS)[number];

export const ANALYSIS_LARGE_REPORT_THRESHOLD = 5000;
export const ANALYSIS_LARGE_RAW_THRESHOLD = 8000;
export const ANALYSIS_REPORT_PREVIEW_LENGTH = 2000;
export const ANALYSIS_RAW_PREVIEW_LENGTH = 2000;

export const KNOWLEDGE_BASE_BUILD_WORKERS = 4;
