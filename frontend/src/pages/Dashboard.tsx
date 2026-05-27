import { useEffect, useMemo, useState } from "react";
import { fetchRuns, type RunSummary } from "../services/api";
import {
    Activity,
    AlertCircle,
    ArrowUpRight,
    Check,
    CheckCircle2,
    ChevronDown,
    ChevronUp,
    Clock,
    Cpu,
    Database,
    GitCompareArrows,
    Layers,
    MinusCircle,
    Search,
    TrendingDown,
    TrendingUp,
    XCircle,
} from "lucide-react";
import { Layout } from "../components/Layout";
/*
 * Phase 4 Evidence-Based Design pass — Dashboard.tsx
 *
 * STRUCTURE UNCHANGED: command bar + left rail + chart zone + runs table.
 * This pass applies 12 cognitive/UX principles as surgical refinements:
 *
 *  1. Von Restorff   — hero pass-rate KPI visually isolated (2rem vs 1.125rem)
 *  2. Miller         — rail KPIs grouped into "Quality" / "Throughput" clusters
 *  3. Gestalt        — clusters use rail-cluster region fills, not divider lines
 *  4. Hick's Law     — command bar: New Run is sole primary; Compare is icon-only
 *  5. Fitts's Law    — row py-3 (generous target); sort headers have -m-1 padding
 *  6. Pre-attentive  — verdict: icon shape + color + label (3 channels)
 *  7. Recognition    — active filters echoed in persistent state summary strip
 *  8. F-pattern      — numbers right-aligned; consistent 1-decimal precision
 *  9. Color-blind    — verdict uses icon+label redundant coding beyond hue alone
 * 10. Halation       — foreground #dcdee6 (off-white), primary desaturated 72%
 * 11. Prog. disc.    — metric tags collapsed to "+N"; detail behind row click
 * 12. Jakob's Law    — sort chevrons, sparklines, status pills all conventional
 *
 * Data hooks / logic UNCHANGED. See docs/frontend/W-PHASE4-DIRECTION.md.
 */
import { AuthorityBadge, Button, Dial, EmptyState, StatCard } from "../design";
import { useNavigate } from "react-router-dom";
import {
    Area,
    AreaChart,
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import {
    PROJECT_ALL,
    PROJECT_UNASSIGNED,
    addDays,
    buildDailyAggregates,
    collectProjectNames,
    computeStats,
    filterRunsByDate,
    filterRunsByProjects,
    formatShortDate,
    getPreviousRange,
    resolveDateRange,
    toDateInputValue,
    type DateRangePreset,
} from "../utils/runAnalytics";
import {
    CHART_METRIC_COLORS,
    CHART_PASS_RATE_COLOR,
    CUSTOM_RANGE_DEFAULT_DAYS,
    DATE_RANGE_OPTIONS,
    DEFAULT_DATE_RANGE_PRESET,
} from "../config/ui";

type MetricTrendRow = Record<string, number | string | null>;
type SortKey = "started_at" | "dataset_name" | "pass_rate" | "total_test_cases" | "model_name";
type SortDir = "asc" | "desc";

function projectLabel(value: string) {
    if (value === PROJECT_ALL) return "All";
    if (value === PROJECT_UNASSIGNED) return "—";
    return value;
}

function applySearchFilter(runs: RunSummary[], query: string) {
    const q = query.trim().toLowerCase();
    if (!q) return runs;
    return runs.filter(
        (r) =>
            r.dataset_name.toLowerCase().includes(q) ||
            r.model_name.toLowerCase().includes(q) ||
            r.run_id.toLowerCase().includes(q) ||
            (r.project_name || "").toLowerCase().includes(q),
    );
}

function deltaDir(delta: number | undefined, eps = 1e-6): "up" | "down" | "flat" {
    if (delta == null || Math.abs(delta) <= eps) return "flat";
    return delta > 0 ? "up" : "down";
}

function fmtCountDelta(d: number | undefined): string | null {
    if (d == null || d === 0) return null;
    return `${d > 0 ? "+" : ""}${d.toLocaleString()}`;
}

function fmtPctDelta(d: number | undefined): string | null {
    if (d == null || Math.abs(d) < 0.0005) return null;
    const pts = d * 100;
    return `${pts > 0 ? "+" : ""}${pts.toFixed(1)}pt`;
}

function fmtCostDelta(d: number | undefined): string | null {
    if (d == null || Math.abs(d) < 0.005) return null;
    return `${d > 0 ? "+" : "-"}$${Math.abs(d).toFixed(2)}`;
}

// Tooltip — cool dark surface, mono font (Jakob's Law: Grafana convention)
const TOOLTIP_STYLE = {
    borderRadius: "var(--radius)",
    border: "1px solid hsl(var(--border))",
    background: "hsl(228 12% 13%)",
    color: "hsl(220 10% 87%)",
    boxShadow: "var(--shadow-pop)",
    fontSize: "10px",
    fontFamily: "'JetBrains Mono', ui-monospace, monospace",
    padding: "6px 10px",
} as const;

// Tufte: minimal grid — very faint, just enough to anchor the axis
const CHART_GRID = "hsl(228 10% 20% / 0.6)";

// Dial/verdict color: status-semantic only, NEVER brand indigo
function dialColor(rate: number): string {
    if (rate >= 0.7) return "hsl(var(--success))";
    if (rate >= 0.5) return "hsl(var(--warning))";
    return "hsl(var(--destructive))";
}

/*
 * VerdictPill — pre-attentive processing + color-blind safety (principle 6 & 9):
 * Encodes verdict via THREE independent channels so hue alone is never the sole signal:
 *   1. Hue: green / amber / red
 *   2. Icon shape: CheckCircle2 / MinusCircle / XCircle  (shape distinguishable in B&W)
 *   3. Text label: "pass" / "hold" / "fail"
 */
function VerdictPill({ rate }: { rate: number }) {
    if (rate >= 0.7) {
        return (
            <span className="verdict-pass" title={`${(rate * 100).toFixed(1)}% — evaluation passed`}>
                <CheckCircle2 className="h-2.5 w-2.5 shrink-0" aria-hidden />
                pass
            </span>
        );
    }
    if (rate >= 0.5) {
        return (
            <span className="verdict-hold" title={`${(rate * 100).toFixed(1)}% — hold for review`}>
                <MinusCircle className="h-2.5 w-2.5 shrink-0" aria-hidden />
                hold
            </span>
        );
    }
    return (
        <span className="verdict-fail" title={`${(rate * 100).toFixed(1)}% — failed threshold`}>
            <XCircle className="h-2.5 w-2.5 shrink-0" aria-hidden />
            fail
        </span>
    );
}

/*
 * SortHeader — Fitts's Law: larger invisible hit area via p-1 -m-1.
 * Jakob's Law: chevron up/down is the canonical sort-direction pattern.
 */
function SortHeader({
    label,
    sortKey,
    current,
    dir,
    onSort,
    align = "left",
}: {
    label: string;
    sortKey: SortKey;
    current: SortKey;
    dir: SortDir;
    onSort: (k: SortKey) => void;
    align?: "left" | "right";
}) {
    const active = current === sortKey;
    return (
        <button
            type="button"
            onClick={() => onSort(sortKey)}
            // Fitts: generous hit area without visible size increase
            className={`inline-flex items-center gap-0.5 p-1 -m-1 font-mono text-[9px] uppercase tracking-[0.15em] transition-colors rounded-[var(--radius-sm)] ${
                align === "right" ? "flex-row-reverse" : ""
            } ${
                active
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
            }`}
            aria-sort={active ? (dir === "desc" ? "descending" : "ascending") : "none"}
        >
            {label}
            {active ? (
                dir === "desc" ? (
                    <ChevronDown className="h-2.5 w-2.5 shrink-0" />
                ) : (
                    <ChevronUp className="h-2.5 w-2.5 shrink-0" />
                )
            ) : (
                <ChevronDown className="h-2.5 w-2.5 shrink-0 opacity-25" />
            )}
        </button>
    );
}

export function Dashboard() {
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const [selectedRuns, setSelectedRuns] = useState<Set<string>>(new Set());
    const [searchQuery, setSearchQuery] = useState("");
    const [rangePreset, setRangePreset] = useState<DateRangePreset>(DEFAULT_DATE_RANGE_PRESET);
    const [customStart, setCustomStart] = useState(() =>
        toDateInputValue(addDays(new Date(), -(CUSTOM_RANGE_DEFAULT_DAYS - 1))),
    );
    const [customEnd, setCustomEnd] = useState(() => toDateInputValue(new Date()));
    const [selectedProjects, setSelectedProjects] = useState<string[]>([PROJECT_ALL]);
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
    const [sortKey, setSortKey] = useState<SortKey>("started_at");
    const [sortDir, setSortDir] = useState<SortDir>("desc");

    useEffect(() => {
        fetchRuns()
            .then(setRuns)
            .catch((err) => setError(err instanceof Error ? err.message : "Failed to load runs"))
            .finally(() => setLoading(false));
    }, []);

    const toggleRunSelection = (runId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setSelectedRuns((prev) => {
            const next = new Set(prev);
            next.has(runId) ? next.delete(runId) : next.add(runId);
            return next;
        });
    };

    const toggleProject = (value: string) => {
        setSelectedProjects((prev) => {
            if (value === PROJECT_ALL) return [PROJECT_ALL];
            const next = new Set(prev.filter((p) => p !== PROJECT_ALL));
            next.has(value) ? next.delete(value) : next.add(value);
            return next.size === 0 ? [PROJECT_ALL] : Array.from(next);
        });
    };

    const toggleMetric = (value: string) => {
        setSelectedMetrics((prev) =>
            prev.includes(value) ? prev.filter((m) => m !== value) : [...prev, value],
        );
    };

    const handleSort = (key: SortKey) => {
        if (sortKey === key) {
            setSortDir((d) => (d === "desc" ? "asc" : "desc"));
        } else {
            setSortKey(key);
            setSortDir("desc");
        }
    };

    const handleCompare = () => {
        if (selectedRuns.size !== 2) return;
        const [base, target] = Array.from(selectedRuns);
        navigate(`/compare?base=${base}&target=${target}`);
    };

    const projectOptions = useMemo(() => collectProjectNames(runs), [runs]);
    const dateRange = useMemo(
        () => resolveDateRange(rangePreset, customStart, customEnd),
        [rangePreset, customStart, customEnd],
    );
    const previousRange = useMemo(
        () => getPreviousRange(dateRange.from, dateRange.to),
        [dateRange.from, dateRange.to],
    );
    const projectFiltered = useMemo(
        () => filterRunsByProjects(runs, selectedProjects),
        [runs, selectedProjects],
    );
    const dateFiltered = useMemo(
        () => filterRunsByDate(projectFiltered, dateRange.from, dateRange.to),
        [projectFiltered, dateRange.from, dateRange.to],
    );
    const filteredRuns = useMemo(() => {
        const searched = applySearchFilter(dateFiltered, searchQuery);
        return [...searched].sort((a, b) => {
            let cmp = 0;
            switch (sortKey) {
                case "started_at":
                    cmp = new Date(a.started_at).getTime() - new Date(b.started_at).getTime();
                    break;
                case "dataset_name":
                    cmp = a.dataset_name.localeCompare(b.dataset_name);
                    break;
                case "pass_rate":
                    cmp = a.pass_rate - b.pass_rate;
                    break;
                case "total_test_cases":
                    cmp = a.total_test_cases - b.total_test_cases;
                    break;
                case "model_name":
                    cmp = a.model_name.localeCompare(b.model_name);
                    break;
            }
            return sortDir === "desc" ? -cmp : cmp;
        });
    }, [dateFiltered, searchQuery, sortKey, sortDir]);

    const stats = useMemo(() => computeStats(filteredRuns), [filteredRuns]);
    const previousStats = useMemo(() => {
        if (!previousRange.from || !previousRange.to) return null;
        return computeStats(
            applySearchFilter(
                filterRunsByDate(projectFiltered, previousRange.from, previousRange.to),
                searchQuery,
            ),
        );
    }, [previousRange.from, previousRange.to, projectFiltered, searchQuery]);

    const deltas = useMemo(() => {
        if (!previousStats) return null;
        return {
            totalRuns: stats.totalRuns - previousStats.totalRuns,
            totalTestCases: stats.totalTestCases - previousStats.totalTestCases,
            avgPassRate: stats.avgPassRate - previousStats.avgPassRate,
            totalCost: stats.totalCost - previousStats.totalCost,
        };
    }, [previousStats, stats]);

    const trendSeries = useMemo(
        () => buildDailyAggregates(filteredRuns, dateRange.from, dateRange.to),
        [filteredRuns, dateRange.from, dateRange.to],
    );

    const passRateSeries = useMemo(
        () =>
            trendSeries.map((pt) => ({
                date: pt.date,
                passRate: pt.totalCases > 0 ? Number((pt.passRate * 100).toFixed(1)) : null,
                totalCases: pt.totalCases,
            })),
        [trendSeries],
    );

    const availableMetrics = useMemo(() => {
        const set = new Set<string>();
        filteredRuns.forEach((r) =>
            Object.keys(r.avg_metric_scores || {}).forEach((m) => set.add(m)),
        );
        return Array.from(set).sort((a, b) => a.localeCompare(b));
    }, [filteredRuns]);

    useEffect(() => {
        setSelectedMetrics((prev) => {
            const valid = prev.filter((m) => availableMetrics.includes(m));
            return valid.length > 0 ? valid : availableMetrics.slice(0, 2);
        });
    }, [availableMetrics]);

    const metricSeries: MetricTrendRow[] = useMemo(() => {
        if (selectedMetrics.length === 0) return [];
        return trendSeries.map((pt) => {
            const row: MetricTrendRow = { date: pt.date };
            selectedMetrics.forEach((m) => {
                const v = pt.metricAverages[m];
                row[m] = typeof v === "number" ? Number((v * 100).toFixed(1)) : null;
            });
            return row;
        });
    }, [trendSeries, selectedMetrics]);

    useEffect(() => {
        const allowed = new Set(filteredRuns.map((r) => r.run_id));
        setSelectedRuns((prev) => {
            const next = new Set(Array.from(prev).filter((id) => allowed.has(id)));
            return next.size === prev.size ? prev : next;
        });
    }, [filteredRuns]);

    // Active filter summary — recognition over recall (principle 7)
    const activeFilterSummary = useMemo(() => {
        const parts: string[] = [];
        const rangeLabel = DATE_RANGE_OPTIONS.find((o) => o.value === rangePreset)?.label ?? rangePreset;
        parts.push(rangeLabel);
        if (!selectedProjects.includes(PROJECT_ALL)) {
            parts.push(selectedProjects.join(", "));
        }
        if (searchQuery.trim()) parts.push(`"${searchQuery.trim()}"`);
        return parts.join(" · ");
    }, [rangePreset, selectedProjects, searchQuery]);

    // ------------------------------------------------------------------ //
    //  Loading / error states
    // ------------------------------------------------------------------ //

    if (loading) {
        return (
            <Layout>
                <div className="flex h-[60vh] flex-col items-center justify-center gap-3">
                    <div className="relative">
                        <div className="h-8 w-8 animate-pulse rounded-[var(--radius)] bg-primary/20" />
                        <Activity className="absolute left-2 top-2 h-4 w-4 animate-spin text-primary" />
                    </div>
                    <p className="font-mono text-[10px] text-muted-foreground">loading workspace…</p>
                </div>
            </Layout>
        );
    }

    if (error) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-background px-6">
                <div className="w-full max-w-sm rounded-[var(--radius)] border border-destructive/30 bg-card px-6">
                    <EmptyState
                        icon={<AlertCircle size={18} className="text-[hsl(var(--destructive))]" />}
                        title="Connection error"
                        description={error}
                        action={
                            <Button variant="destructive" size="sm" onClick={() => window.location.reload()}>
                                Retry
                            </Button>
                        }
                    />
                </div>
            </div>
        );
    }

    // ------------------------------------------------------------------ //
    //  Main render — same structure, evidence-based refinements applied
    // ------------------------------------------------------------------ //

    return (
        <Layout>
            <div className="flex h-full flex-col">

                {/* ══════════════════════════════════════════════════════
                 *  COMMAND BAR — Hick's Law: single primary action (New Run);
                 *  Compare demoted to icon-only with tooltip.
                 *  Recognition: active filter summary echoed below controls.
                 * ══════════════════════════════════════════════════════ */}
                <div className="reveal reveal-1 sticky top-0 z-30 border-b border-border bg-background/95 backdrop-blur-sm">
                    {/* Main controls row */}
                    <div className="flex items-center gap-2.5 px-5 py-2">
                        {/* Title — 3-level type hierarchy L2 */}
                        <div className="shrink-0">
                            <h1 className="font-display text-sm font-semibold leading-tight text-foreground">
                                Evaluation Overview
                            </h1>
                        </div>

                        <div className="mx-1 h-6 w-px bg-border/50 shrink-0" />

                        {/* Search */}
                        <div className="relative w-44 shrink-0">
                            <Search className="pointer-events-none absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground/60" />
                            <input
                                type="text"
                                placeholder="dataset · model · run-id"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="field-control pl-6 py-1 text-[11px] h-7"
                                aria-label="Search runs"
                            />
                        </div>

                        {/* Date range */}
                        <select
                            value={rangePreset}
                            onChange={(e) => setRangePreset(e.target.value as DateRangePreset)}
                            className="field-control h-7 py-0 text-[11px] w-34 shrink-0"
                            aria-label="Date range"
                            style={{ width: "8.5rem" }}
                        >
                            {DATE_RANGE_OPTIONS.map((o) => (
                                <option key={o.value} value={o.value}>
                                    {o.label}
                                </option>
                            ))}
                        </select>

                        {rangePreset === "custom" && (
                            <>
                                <input
                                    type="date"
                                    value={customStart}
                                    onChange={(e) => setCustomStart(e.target.value)}
                                    className="field-control h-7 py-0 text-[11px] w-32 shrink-0"
                                    aria-label="Start date"
                                />
                                <span className="font-mono text-[9px] text-muted-foreground/50 shrink-0">→</span>
                                <input
                                    type="date"
                                    value={customEnd}
                                    onChange={(e) => setCustomEnd(e.target.value)}
                                    className="field-control h-7 py-0 text-[11px] w-32 shrink-0"
                                    aria-label="End date"
                                />
                            </>
                        )}

                        {/* Project chips — reduced visual weight (Hick's Law) */}
                        <div className="flex items-center gap-1" role="group" aria-label="Project filter">
                            {[PROJECT_ALL, ...projectOptions.slice(0, 3)].map((p) => {
                                const active = selectedProjects.includes(p);
                                return (
                                    <button
                                        key={p}
                                        type="button"
                                        onClick={() => toggleProject(p)}
                                        aria-pressed={active}
                                        className={`filter-chip ${active ? "filter-chip-active" : "filter-chip-inactive"}`}
                                    >
                                        {projectLabel(p)}
                                    </button>
                                );
                            })}
                            {projectOptions.length > 3 && (
                                <span className="font-mono text-[9px] text-muted-foreground/50 px-1">
                                    +{projectOptions.length - 3}
                                </span>
                            )}
                        </div>

                        {/* Scope count — low-weight, right of chips (recognition) */}
                        <span
                            className="inline-flex items-center gap-1 font-mono text-[9px] text-muted-foreground/60 shrink-0"
                            aria-live="polite"
                            aria-label={`${filteredRuns.length} runs in scope`}
                        >
                            <Layers className="h-2.5 w-2.5" />
                            {filteredRuns.length}
                        </span>

                        {/* Actions — Hick's Law: one clear primary, one demoted secondary */}
                        <div className="ml-auto flex shrink-0 items-center gap-1.5">
                            {/* Compare: icon-only, demoted — only relevant when 2 selected */}
                            <button
                                type="button"
                                onClick={handleCompare}
                                disabled={selectedRuns.size !== 2}
                                title={
                                    selectedRuns.size === 2
                                        ? "Compare selected runs"
                                        : "Select exactly 2 runs to compare"
                                }
                                aria-label="Compare selected runs"
                                className={`flex h-7 w-7 items-center justify-center rounded-[var(--radius)] border transition-colors ${
                                    selectedRuns.size === 2
                                        ? "border-border text-foreground hover:bg-secondary/60 hover:border-border"
                                        : "border-border/30 text-muted-foreground/30 cursor-not-allowed"
                                }`}
                            >
                                <GitCompareArrows className="h-3.5 w-3.5" />
                            </button>
                            {/* New Run: sole primary CTA — Hick's Law, Fitts's Law */}
                            <Button
                                variant="primary"
                                size="sm"
                                leading={<ArrowUpRight className="h-3.5 w-3.5" />}
                                onClick={() => navigate("/studio")}
                            >
                                New run
                            </Button>
                        </div>
                    </div>

                    {/* Recognition over recall: active-filter summary strip (principle 7) */}
                    <div className="flex items-center gap-2 border-t border-border/30 px-5 py-1">
                        <span className="font-mono text-[9px] text-muted-foreground/40 uppercase tracking-[0.15em] shrink-0">
                            scope
                        </span>
                        <span className="font-mono text-[9px] text-muted-foreground/60 truncate">
                            {activeFilterSummary}
                        </span>
                    </div>
                </div>

                {/* ══════════════════════════════════════════════════════
                 *  BODY — same two-column: left rail + main content
                 * ══════════════════════════════════════════════════════ */}
                <div className="flex flex-1 min-h-0">

                    {/* ─── LEFT RAIL — KPIs chunked into labeled clusters ── */}
                    <aside className="reveal reveal-2 w-44 shrink-0 border-r border-border bg-card/30 flex flex-col overflow-y-auto">

                        {/*
                         * Miller's Law / chunking (principle 2):
                         * Cluster 1 — QUALITY: the single decision-relevant KPI.
                         * Von Restorff: isolated by its own region fill + hero tone.
                         * Gestalt: rail-cluster uses bg fill, not a divider line.
                         */}
                        <div className="px-2.5 pt-3 pb-1">
                            {/* Cluster label — 3-level hierarchy L3 */}
                            <p className="mb-1.5 font-mono text-[8px] uppercase tracking-[0.25em] text-muted-foreground/40">
                                Quality
                            </p>
                            <div className="rail-cluster">
                                <StatCard
                                    tone="hero"
                                    label="Pass Rate"
                                    value={`${(stats.avgPassRate * 100).toFixed(1)}%`}
                                    delta={fmtPctDelta(deltas?.avgPassRate)}
                                    deltaDirection={deltaDir(deltas?.avgPassRate)}
                                    deltaIsPositiveGood
                                    authority="T2"
                                    icon={
                                        deltas && deltas.avgPassRate < 0
                                            ? <TrendingDown className="h-2.5 w-2.5" />
                                            : <TrendingUp className="h-2.5 w-2.5" />
                                    }
                                    spark={
                                        passRateSeries.length > 1 ? (
                                            <ResponsiveContainer width="100%" height="100%">
                                                <AreaChart data={passRateSeries} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                                                    <defs>
                                                        <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
                                                            <stop offset="0%" stopColor={CHART_PASS_RATE_COLOR} stopOpacity={0.3} />
                                                            <stop offset="100%" stopColor={CHART_PASS_RATE_COLOR} stopOpacity={0} />
                                                        </linearGradient>
                                                    </defs>
                                                    <Area
                                                        type="monotone"
                                                        dataKey="passRate"
                                                        stroke={CHART_PASS_RATE_COLOR}
                                                        strokeWidth={1.5}
                                                        fill="url(#sparkGrad)"
                                                        connectNulls
                                                        isAnimationActive={false}
                                                        dot={false}
                                                    />
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        ) : null
                                    }
                                    caption="vs prev period"
                                />
                            </div>
                        </div>

                        {/*
                         * Miller / chunking — Cluster 2: THROUGHPUT
                         * Gestalt: separate region fill, no divider line between clusters.
                         * Three subordinate KPIs grouped logically (runs + cases + cost).
                         */}
                        <div className="px-2.5 pt-2 pb-3">
                            <p className="mb-1.5 font-mono text-[8px] uppercase tracking-[0.25em] text-muted-foreground/40">
                                Throughput
                            </p>
                            <div className="rail-cluster flex flex-col gap-px">
                                <StatCard
                                    label="Runs"
                                    value={stats.totalRuns.toLocaleString()}
                                    delta={fmtCountDelta(deltas?.totalRuns)}
                                    deltaDirection={deltaDir(deltas?.totalRuns)}
                                    deltaIsPositiveGood
                                    authority="T1"
                                    caption="in scope"
                                />
                                <StatCard
                                    label="Test Cases"
                                    value={stats.totalTestCases.toLocaleString()}
                                    delta={fmtCountDelta(deltas?.totalTestCases)}
                                    deltaDirection={deltaDir(deltas?.totalTestCases)}
                                    deltaIsPositiveGood
                                    authority="T1"
                                    caption="evaluated"
                                />
                                <StatCard
                                    label="LLM Cost"
                                    value={`$${stats.totalCost.toFixed(2)}`}
                                    delta={fmtCostDelta(deltas?.totalCost)}
                                    deltaDirection={deltaDir(deltas?.totalCost)}
                                    deltaIsPositiveGood={false}
                                    authority="T1"
                                    caption="USD"
                                />
                            </div>
                        </div>

                        {/* Divider */}
                        <div className="mx-3 border-t border-border/30" />

                        {/* Chart metric selector — co-located with KPIs (Gestalt proximity) */}
                        <div className="px-2.5 pt-2.5 pb-3 flex-1">
                            <p className="mb-1.5 font-mono text-[8px] uppercase tracking-[0.25em] text-muted-foreground/40">
                                Chart metrics
                            </p>
                            <div className="flex flex-col gap-0.5">
                                {availableMetrics.length === 0 ? (
                                    <span className="font-mono text-[9px] text-muted-foreground/50 px-1.5">none</span>
                                ) : (
                                    availableMetrics.map((metric, idx) => {
                                        const sel = selectedMetrics.includes(metric);
                                        const selIdx = selectedMetrics.indexOf(metric);
                                        const swatch =
                                            CHART_METRIC_COLORS[
                                                selIdx >= 0
                                                    ? selIdx % CHART_METRIC_COLORS.length
                                                    : idx % CHART_METRIC_COLORS.length
                                            ];
                                        return (
                                            <button
                                                key={metric}
                                                type="button"
                                                onClick={() => toggleMetric(metric)}
                                                aria-pressed={sel}
                                                className={`flex items-center gap-1.5 rounded-[var(--radius-sm)] px-1.5 py-1 text-left transition-colors ${
                                                    sel
                                                        ? "bg-secondary/70 text-foreground"
                                                        : "text-muted-foreground/70 hover:bg-secondary/40 hover:text-foreground"
                                                }`}
                                            >
                                                {/*
                                                 * Color-blind safety (principle 9): swatch dot is a
                                                 * redundant encoding — chart color is also the line label.
                                                 * When unselected the dot is gray (border color only).
                                                 */}
                                                <span
                                                    className="h-1.5 w-1.5 shrink-0 rounded-full border"
                                                    style={{
                                                        background: sel ? swatch : "transparent",
                                                        borderColor: sel ? swatch : "hsl(var(--border))",
                                                    }}
                                                    aria-hidden
                                                />
                                                <span className="font-mono text-[9px] truncate">{metric}</span>
                                            </button>
                                        );
                                    })
                                )}
                            </div>
                        </div>
                    </aside>

                    {/* ─── MAIN CONTENT — charts + table ──────────────── */}
                    <div className="flex-1 min-w-0 flex flex-col overflow-y-auto">

                        {/* ── CHART ZONE ───────────────────────────────── */}
                        <section className="reveal reveal-3 border-b border-border">
                            <div className="grid grid-cols-1 gap-0 xl:grid-cols-2">

                                {/* Pass rate chart */}
                                <div className="border-r border-border p-5">
                                    <div className="mb-3 flex items-center justify-between gap-2">
                                        <div>
                                            {/* 3-level hierarchy: L2 chart title */}
                                            <p className="font-display text-sm font-semibold tracking-tight text-foreground">
                                                Pass Rate
                                            </p>
                                            {/* L3 kicker */}
                                            <p className="mt-0.5 font-mono text-[9px] text-muted-foreground/50">
                                                weighted avg · {dateRange.label}
                                            </p>
                                        </div>
                                        <AuthorityBadge level="T2" scope="evaluation_gate" />
                                    </div>
                                    <div className="h-[220px]">
                                        {passRateSeries.length === 0 ? (
                                            <div className="flex h-full items-center justify-center font-mono text-[10px] text-muted-foreground/50">
                                                no data for selected filters
                                            </div>
                                        ) : (
                                            <ResponsiveContainer width="100%" height="100%">
                                                <AreaChart
                                                    data={passRateSeries}
                                                    margin={{ top: 4, right: 4, left: -16, bottom: 0 }}
                                                >
                                                    <defs>
                                                        <linearGradient id="passGrad" x1="0" y1="0" x2="0" y2="1">
                                                            <stop offset="5%" stopColor={CHART_PASS_RATE_COLOR} stopOpacity={0.18} />
                                                            <stop offset="95%" stopColor={CHART_PASS_RATE_COLOR} stopOpacity={0} />
                                                        </linearGradient>
                                                    </defs>
                                                    {/* Tufte: faint grid at 60% opacity — just enough to anchor axis */}
                                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={CHART_GRID} />
                                                    <XAxis
                                                        dataKey="date"
                                                        stroke="transparent"
                                                        tick={{ fill: "hsl(220 8% 48%)", fontSize: 9, fontFamily: "'JetBrains Mono', monospace" }}
                                                        tickLine={false}
                                                        axisLine={false}
                                                        tickFormatter={formatShortDate}
                                                        interval="preserveStartEnd"
                                                    />
                                                    <YAxis
                                                        tick={{ fill: "hsl(220 8% 48%)", fontSize: 9, fontFamily: "'JetBrains Mono', monospace" }}
                                                        tickLine={false}
                                                        axisLine={false}
                                                        domain={[0, 100]}
                                                        tickFormatter={(v) => `${v}%`}
                                                        width={30}
                                                        tickCount={5}
                                                    />
                                                    <Tooltip
                                                        formatter={(v: number | undefined) =>
                                                            v == null ? "—" : `${v.toFixed(1)}%`
                                                        }
                                                        labelFormatter={(l) => `${l}`}
                                                        contentStyle={TOOLTIP_STYLE}
                                                        cursor={{ stroke: "hsl(228 10% 28%)", strokeWidth: 1 }}
                                                    />
                                                    <Area
                                                        type="monotone"
                                                        dataKey="passRate"
                                                        stroke={CHART_PASS_RATE_COLOR}
                                                        strokeWidth={1.75}
                                                        fill="url(#passGrad)"
                                                        name="pass rate"
                                                        dot={false}
                                                        activeDot={{ r: 3, strokeWidth: 0, fill: CHART_PASS_RATE_COLOR }}
                                                    />
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        )}
                                    </div>
                                </div>

                                {/* Metric trend chart */}
                                <div className="p-5">
                                    <div className="mb-3 flex items-center justify-between gap-2">
                                        <div>
                                            <p className="font-display text-sm font-semibold tracking-tight text-foreground">
                                                Metric Trends
                                            </p>
                                            <p className="mt-0.5 font-mono text-[9px] text-muted-foreground/50">
                                                daily avg · select in rail
                                            </p>
                                        </div>
                                        <AuthorityBadge level="T1" scope="metric_evidence" />
                                    </div>
                                    <div className="h-[220px]">
                                        {metricSeries.length === 0 || selectedMetrics.length === 0 ? (
                                            <div className="flex h-full items-center justify-center font-mono text-[10px] text-muted-foreground/50">
                                                select metrics in the left rail
                                            </div>
                                        ) : (
                                            <ResponsiveContainer width="100%" height="100%">
                                                <LineChart
                                                    data={metricSeries}
                                                    margin={{ top: 4, right: 4, left: -16, bottom: 0 }}
                                                >
                                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={CHART_GRID} />
                                                    <XAxis
                                                        dataKey="date"
                                                        stroke="transparent"
                                                        tick={{ fill: "hsl(220 8% 48%)", fontSize: 9, fontFamily: "'JetBrains Mono', monospace" }}
                                                        tickLine={false}
                                                        axisLine={false}
                                                        tickFormatter={formatShortDate}
                                                        interval="preserveStartEnd"
                                                    />
                                                    <YAxis
                                                        tick={{ fill: "hsl(220 8% 48%)", fontSize: 9, fontFamily: "'JetBrains Mono', monospace" }}
                                                        tickLine={false}
                                                        axisLine={false}
                                                        domain={[0, 100]}
                                                        tickFormatter={(v) => `${v}%`}
                                                        width={30}
                                                        tickCount={5}
                                                    />
                                                    <Tooltip
                                                        formatter={(v: number | undefined, name) =>
                                                            [v == null ? "—" : `${v.toFixed(1)}%`, name]
                                                        }
                                                        labelFormatter={(l) => `${l}`}
                                                        contentStyle={TOOLTIP_STYLE}
                                                        cursor={{ stroke: "hsl(228 10% 28%)", strokeWidth: 1 }}
                                                    />
                                                    {selectedMetrics.map((metric, idx) => (
                                                        <Line
                                                            key={metric}
                                                            type="monotone"
                                                            dataKey={metric}
                                                            stroke={CHART_METRIC_COLORS[idx % CHART_METRIC_COLORS.length]}
                                                            strokeWidth={1.5}
                                                            dot={false}
                                                            activeDot={{ r: 3, strokeWidth: 0 }}
                                                            connectNulls
                                                            // Jakob's Law: name shown in tooltip (recognition)
                                                            name={metric}
                                                        />
                                                    ))}
                                                </LineChart>
                                            </ResponsiveContainer>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* ── RUNS TABLE ───────────────────────────────── */}
                        <section className="reveal reveal-4 flex-1 min-h-0">
                            {/* Table header bar */}
                            <div className="flex items-center justify-between border-b border-border px-5 py-2 bg-secondary/20">
                                <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground/60">
                                    Runs
                                </p>
                                {/* Numerical cognition: right-aligned count */}
                                <span className="font-mono text-[9px] tabular-nums text-muted-foreground/40">
                                    {filteredRuns.length} shown
                                </span>
                            </div>

                            {filteredRuns.length === 0 ? (
                                <div className="surface-card m-4">
                                    <EmptyState
                                        compact
                                        icon={<Database size={16} />}
                                        title="No runs in scope"
                                        description="Adjust the date range, project, or search query."
                                    />
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    {/*
                                     * F-pattern scanning: primary column (Dataset) left-anchored.
                                     * Numbers right-aligned for column-level comparison.
                                     * Gestalt: column groups separated by slight header spacing
                                     * (no explicit border lines between groups — proximity alone).
                                     *
                                     * Column conceptual groups:
                                     *   Identity: [✓] Dataset  Model
                                     *   Quality:  Pass Rate  Verdict
                                     *   Volume:   Cases
                                     *   Detail:   Metrics  (progressive disclosure — muted)
                                     *   Time:     Started
                                     */}
                                    <table className="w-full min-w-[760px] border-collapse">
                                        <thead>
                                            <tr className="border-b border-border/60 bg-secondary/15">
                                                {/* Select */}
                                                <th className="w-8 px-3 py-2" />

                                                {/* Identity group */}
                                                <th className="px-3 py-2 text-left">
                                                    <SortHeader label="Dataset" sortKey="dataset_name" current={sortKey} dir={sortDir} onSort={handleSort} />
                                                </th>
                                                <th className="px-3 py-2 text-left">
                                                    <SortHeader label="Model" sortKey="model_name" current={sortKey} dir={sortDir} onSort={handleSort} />
                                                </th>

                                                {/* Quality group — primary sorting target */}
                                                <th className="px-3 py-2 text-right">
                                                    <SortHeader label="Pass %" sortKey="pass_rate" current={sortKey} dir={sortDir} onSort={handleSort} align="right" />
                                                </th>
                                                <th className="px-3 py-2 text-left">
                                                    <span className="font-mono text-[9px] uppercase tracking-[0.15em] text-muted-foreground/50">
                                                        Verdict
                                                    </span>
                                                </th>

                                                {/* Volume group */}
                                                <th className="px-3 py-2 text-right">
                                                    <SortHeader label="Cases" sortKey="total_test_cases" current={sortKey} dir={sortDir} onSort={handleSort} align="right" />
                                                </th>

                                                {/* Detail — muted, progressive disclosure */}
                                                <th className="px-3 py-2 text-left">
                                                    <span className="font-mono text-[9px] uppercase tracking-[0.15em] text-muted-foreground/40">
                                                        Metrics
                                                    </span>
                                                </th>

                                                {/* Time */}
                                                <th className="px-3 py-2 text-right">
                                                    <SortHeader label="Started" sortKey="started_at" current={sortKey} dir={sortDir} onSort={handleSort} align="right" />
                                                </th>

                                                <th className="w-6 px-2 py-2" />
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {filteredRuns.map((run) => {
                                                const isSelected = selectedRuns.has(run.run_id);
                                                return (
                                                    <tr
                                                        key={run.run_id}
                                                        onClick={() => navigate(`/runs/${run.run_id}`)}
                                                        className={`group border-b border-border/30 transition-colors cursor-pointer ${
                                                            isSelected
                                                                ? "bg-primary/6"
                                                                : "hover:bg-secondary/40"
                                                        }`}
                                                    >
                                                        {/* Select — Fitts: py-3 generous row height */}
                                                        <td className="px-3 py-3">
                                                            <button
                                                                type="button"
                                                                aria-pressed={isSelected}
                                                                aria-label={isSelected ? "Deselect run" : "Select for compare"}
                                                                onClick={(e) => toggleRunSelection(run.run_id, e)}
                                                                className={`flex h-4 w-4 items-center justify-center rounded-[var(--radius-sm)] border transition-colors ${
                                                                    isSelected
                                                                        ? "border-primary bg-primary text-primary-foreground"
                                                                        : "border-border/50 bg-transparent text-transparent hover:border-primary/50"
                                                                }`}
                                                            >
                                                                <Check className="h-2.5 w-2.5" />
                                                            </button>
                                                        </td>

                                                        {/* Dataset — F-pattern: left anchor, text label */}
                                                        <td className="px-3 py-3 max-w-[180px]">
                                                            <div className="flex items-center gap-1.5">
                                                                <Database className="h-3 w-3 shrink-0 text-muted-foreground/40" />
                                                                <span className="text-xs font-medium text-foreground truncate transition-colors group-hover:text-primary">
                                                                    {run.dataset_name}
                                                                </span>
                                                            </div>
                                                            {run.project_name && (
                                                                <span className="mt-0.5 block pl-4 font-mono text-[9px] text-muted-foreground/40 truncate">
                                                                    {run.project_name}
                                                                </span>
                                                            )}
                                                        </td>

                                                        {/* Model */}
                                                        <td className="px-3 py-3 max-w-[140px]">
                                                            <div className="flex items-center gap-1">
                                                                <Cpu className="h-3 w-3 shrink-0 text-muted-foreground/30" />
                                                                <span className="font-mono text-[10px] text-muted-foreground/70 truncate">
                                                                    {run.model_name}
                                                                </span>
                                                            </div>
                                                        </td>

                                                        {/*
                                                         * Pass % — right-aligned, consistent 1 decimal (numerical cognition).
                                                         * Dial provides pre-attentive status encoding (hue + arc fill).
                                                         * F-pattern: primary numeric column for scanning.
                                                         */}
                                                        <td className="px-3 py-3 text-right">
                                                            <div className="flex items-center justify-end gap-2">
                                                                {/* Mini bar — pre-attentive position cue */}
                                                                <div className="w-12 hidden sm:block">
                                                                    <div className="h-1 w-full overflow-hidden rounded-full bg-secondary/80">
                                                                        <div
                                                                            className="h-full rounded-full transition-all duration-[var(--duration-slow)]"
                                                                            style={{
                                                                                width: `${run.pass_rate * 100}%`,
                                                                                background: dialColor(run.pass_rate),
                                                                            }}
                                                                        />
                                                                    </div>
                                                                </div>
                                                                <Dial
                                                                    value={run.pass_rate}
                                                                    size={34}
                                                                    thickness={3}
                                                                    color={dialColor(run.pass_rate)}
                                                                    label={`Pass rate: ${(run.pass_rate * 100).toFixed(1)}%`}
                                                                />
                                                            </div>
                                                        </td>

                                                        {/*
                                                         * Verdict — VerdictPill: 3 redundant channels
                                                         * (hue + icon shape + text) for color-blind safety.
                                                         * AuthorityBadge preserved for T2 signal.
                                                         */}
                                                        <td className="px-3 py-3">
                                                            <div className="flex flex-col gap-1">
                                                                <VerdictPill rate={run.pass_rate} />
                                                                <AuthorityBadge level="T2" />
                                                            </div>
                                                        </td>

                                                        {/*
                                                         * Cases — right-aligned tabular-nums.
                                                         * passed/total: consistent format, muted denominator.
                                                         */}
                                                        <td className="px-3 py-3 text-right">
                                                            <span className="font-mono text-[10px] tabular-nums text-foreground/80">
                                                                {run.passed_test_cases}
                                                            </span>
                                                            <span className="font-mono text-[10px] tabular-nums text-muted-foreground/40">
                                                                /{run.total_test_cases}
                                                            </span>
                                                        </td>

                                                        {/*
                                                         * Metrics — progressive disclosure (principle 11):
                                                         * show at most 2 tags + count; full list behind row click.
                                                         */}
                                                        <td className="px-3 py-3">
                                                            <div className="flex items-center gap-0.5">
                                                                {run.metrics_evaluated.slice(0, 2).map((m) => (
                                                                    <span
                                                                        key={m}
                                                                        className="rounded-[var(--radius-sm)] border border-border/30 bg-muted/30 px-1 py-px font-mono text-[8px] text-muted-foreground/50"
                                                                    >
                                                                        {m}
                                                                    </span>
                                                                ))}
                                                                {run.metrics_evaluated.length > 2 && (
                                                                    <span className="font-mono text-[8px] text-muted-foreground/40 pl-0.5">
                                                                        +{run.metrics_evaluated.length - 2}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </td>

                                                        {/* Timestamp — right-aligned, mono, muted */}
                                                        <td className="px-3 py-3 text-right">
                                                            <div className="flex items-center justify-end gap-1 text-muted-foreground/50">
                                                                <Clock className="h-2.5 w-2.5 shrink-0" />
                                                                <span className="font-mono text-[9px] tabular-nums">
                                                                    {new Date(run.started_at).toLocaleDateString()}
                                                                </span>
                                                            </div>
                                                        </td>

                                                        {/* Row nav arrow — revealed on hover (progressive disclosure) */}
                                                        <td className="px-2 py-3">
                                                            <ArrowUpRight className="h-3 w-3 text-muted-foreground/30 opacity-0 transition-all group-hover:opacity-100 group-hover:text-primary" />
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </section>
                    </div>
                </div>
            </div>

            {/* ── Floating compare bar — appears only when 2 selected ── */}
            {selectedRuns.size > 0 && (
                <div
                    className="fixed bottom-5 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3
                        rounded-[var(--radius)] border border-border bg-card px-4 py-2
                        animate-in slide-in-from-bottom-4 duration-200"
                    style={{ boxShadow: "var(--shadow-pop)" }}
                >
                    <span className="font-mono text-xs font-medium tabular-nums text-foreground">
                        {selectedRuns.size} selected
                    </span>
                    <div className="h-3 w-px bg-border/60" />
                    <button
                        type="button"
                        onClick={() => setSelectedRuns(new Set())}
                        className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-wide text-muted-foreground transition-colors hover:text-foreground"
                        aria-label="Clear selection"
                    >
                        <span aria-hidden>×</span> clear
                    </button>
                    <Button
                        variant="primary"
                        size="sm"
                        disabled={selectedRuns.size !== 2}
                        onClick={handleCompare}
                        leading={<GitCompareArrows className="h-3 w-3" />}
                    >
                        Compare
                    </Button>
                </div>
            )}
        </Layout>
    );
}
