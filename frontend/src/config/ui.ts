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

/**
 * Phase 4 "Data-Dense Pro, Neutral-Cool Dark" — high-separation chart ramp.
 *
 * Tuned for the cool card surface (#16171c). All colors 5:1+ on dark card.
 * Ordered: amber · cyan · violet · rose · sky · lime.
 * Max perceptual distance between adjacent series; none conflicts with
 * indigo accent (239°) or T2-green authority token (148°).
 *
 * Contrast on #16171c:
 *   amber  #f59e0b  8.14:1 AA
 *   cyan   #22d3ee  9.61:1 AA
 *   violet #a78bfa  6.41:1 AA
 *   rose   #fb7185  6.48:1 AA
 *   sky    #38bdf8  8.22:1 AA
 *   lime   #a3e635  9.88:1 AA
 *
 * Follow-up (other 16 pages): migrate hardcoded chart hexes to this ramp.
 */
export const CHART_METRIC_COLORS = [
    "#f59e0b", // amber   — primary series
    "#22d3ee", // cyan    — secondary series
    "#a78bfa", // violet  — tertiary
    "#fb7185", // rose    — quaternary
    "#38bdf8", // sky     — quinary
    "#a3e635", // lime    — senary
];

/** Pass-rate area chart color — cyan, distinct from indigo accent and T2 authority green. */
export const CHART_PASS_RATE_COLOR = "#22d3ee";

/*
 * Pass-rate bands map to STATUS semantics, not the brand accent and not T1
 * metric-blue — so a "pass" dial never reads as "branded" or as a metric chip.
 * Strong pass = success green (== T2 eval-pass family), marginal = warning amber,
 * fail = destructive red. (Anti-conflation, see W-PHASE4-DIRECTION §2.)
 */
export const PASS_RATE_COLOR_BANDS = [
    {
        min: 0.9,
        className:
            "text-[hsl(var(--success))] bg-[hsl(var(--success)/0.1)] border-[hsl(var(--success)/0.25)]",
    },
    {
        min: 0.7,
        className:
            "text-[hsl(var(--success))] bg-[hsl(var(--success)/0.08)] border-[hsl(var(--success)/0.2)]",
    },
    {
        min: 0.5,
        className:
            "text-[hsl(var(--warning))] bg-[hsl(var(--warning)/0.1)] border-[hsl(var(--warning)/0.25)]",
    },
    {
        min: 0,
        className:
            "text-[hsl(var(--destructive))] bg-[hsl(var(--destructive)/0.1)] border-[hsl(var(--destructive)/0.25)]",
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
