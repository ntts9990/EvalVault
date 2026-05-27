import { useEffect, useMemo, useState } from "react";
import { fetchRuns, type RunSummary } from "../services/api";
import {
    Activity,
    AlertCircle,
    ArrowUpRight,
    Check,
    ChevronDown,
    ChevronUp,
    Clock,
    Cpu,
    Database,
    DollarSign,
    GitCompareArrows,
    Layers,
    Search,
    TrendingDown,
    TrendingUp,
    X,
} from "lucide-react";
import { Layout } from "../components/Layout";
/*
 * Phase 4 "Data-Dense Pro, Neutral-Cool Dark" Dashboard.
 *
 * STRUCTURAL CHANGE — not just a recolor:
 * Previous layout: stacked vertical (header → filters → KPIs → charts → card grid)
 * New layout: true multi-panel command center
 *   ┌─────────────────────────────────────────────────────────────┐
 *   │ Command bar: search · date · project · actions (full width) │
 *   ├──────────────┬──────────────────────────────────────────────┤
 *   │ Left rail    │ Chart zone (dominant, 2-up side-by-side)     │
 *   │ 4 KPI tiles  │                                              │
 *   │ (vertical)   ├──────────────────────────────────────────────┤
 *   │              │ Runs table (dense, sortable — not card grid) │
 *   └──────────────┴──────────────────────────────────────────────┘
 *
 * Key IA decisions:
 * - KPIs move to a persistent left rail — always visible while scrolling
 * - Charts are the dominant center-right zone, much larger than before
 * - Runs are a dense TABLE (not cards) — 8-10 columns, sortable headers
 * - Filters live in a compact command bar at the top, always accessible
 * - Floating compare bar retained but repositioned
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

// Tooltip style — cool dark surface
const TOOLTIP_STYLE = {
    borderRadius: "var(--radius)",
    border: "1px solid hsl(var(--border))",
    background: "hsl(228 12% 13%)",
    color: "hsl(220 14% 88%)",
    boxShadow: "var(--shadow-pop)",
    fontSize: "10px",
    fontFamily: "'JetBrains Mono', ui-monospace, monospace",
} as const;

// Chart grid color — cool neutral
const CHART_GRID = "hsl(228 10% 18%)";

// Dial color: status-semantic only, never brand indigo
function dialColor(rate: number): string {
    if (rate >= 0.7) return "hsl(var(--success))";
    if (rate >= 0.5) return "hsl(var(--warning))";
    return "hsl(var(--destructive))";
}

// Sortable column header
function SortHeader({
    label,
    sortKey,
    current,
    dir,
    onSort,
}: {
    label: string;
    sortKey: SortKey;
    current: SortKey;
    dir: SortDir;
    onSort: (k: SortKey) => void;
}) {
    const active = current === sortKey;
    return (
        <button
            type="button"
            onClick={() => onSort(sortKey)}
            className={`inline-flex items-center gap-1 font-mono text-[9px] uppercase tracking-[0.15em] transition-colors ${
                active ? "text-primary" : "text-muted-foreground hover:text-foreground"
            }`}
        >
            {label}
            {active ? (
                dir === "desc" ? (
                    <ChevronDown className="h-2.5 w-2.5" />
                ) : (
                    <ChevronUp className="h-2.5 w-2.5" />
                )
            ) : (
                <ChevronDown className="h-2.5 w-2.5 opacity-30" />
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
                passRate: pt.totalCases > 0 ? Number((pt.passRate * 100).toFixed(2)) : null,
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
                row[m] = typeof v === "number" ? Number((v * 100).toFixed(2)) : null;
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
    //  Main render — multi-panel command center layout
    // ------------------------------------------------------------------ //

    return (
        <Layout>
            <div className="flex h-full flex-col">

                {/* ══════════════════════════════════════════════════════
                 *  COMMAND BAR — full-width, sticky, compact
                 *  Contains: page title + search + date + project + actions
                 *  Replaces the old stacked header + separate filter section
                 * ══════════════════════════════════════════════════════ */}
                <div className="reveal reveal-1 sticky top-0 z-30 border-b border-border bg-background/95 backdrop-blur-sm">
                    <div className="flex items-center gap-3 px-5 py-2.5">
                        {/* Title block */}
                        <div className="shrink-0">
                            <h1 className="font-display text-sm font-semibold text-foreground leading-tight">
                                Evaluation Overview
                            </h1>
                            <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
                                eval dashboard
                            </p>
                        </div>

                        <div className="mx-1 h-8 w-px bg-border/60 shrink-0" />

                        {/* Search */}
                        <div className="relative w-48 shrink-0">
                            <Search className="pointer-events-none absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground" />
                            <input
                                type="text"
                                placeholder="dataset · model · run-id"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="field-control pl-6 py-1 text-xs h-7"
                            />
                        </div>

                        {/* Date range */}
                        <select
                            value={rangePreset}
                            onChange={(e) => setRangePreset(e.target.value as DateRangePreset)}
                            className="field-control h-7 py-0 text-xs w-36 shrink-0"
                        >
                            {DATE_RANGE_OPTIONS.map((o) => (
                                <option key={o.value} value={o.value}>
                                    {o.label}
                                </option>
                            ))}
                        </select>

                        {/* Custom range inline */}
                        {rangePreset === "custom" && (
                            <>
                                <input
                                    type="date"
                                    value={customStart}
                                    onChange={(e) => setCustomStart(e.target.value)}
                                    className="field-control h-7 py-0 text-xs w-32 shrink-0"
                                />
                                <span className="font-mono text-[9px] text-muted-foreground shrink-0">→</span>
                                <input
                                    type="date"
                                    value={customEnd}
                                    onChange={(e) => setCustomEnd(e.target.value)}
                                    className="field-control h-7 py-0 text-xs w-32 shrink-0"
                                />
                            </>
                        )}

                        {/* Project chips — compact, inline */}
                        <div className="flex items-center gap-1 flex-wrap">
                            {[PROJECT_ALL, ...projectOptions.slice(0, 4)].map((p) => {
                                const active = selectedProjects.includes(p);
                                return (
                                    <button
                                        key={p}
                                        type="button"
                                        onClick={() => toggleProject(p)}
                                        aria-pressed={active}
                                        className={`filter-chip py-0.5 text-[10px] h-6 ${
                                            active ? "filter-chip-active" : "filter-chip-inactive"
                                        }`}
                                    >
                                        {projectLabel(p)}
                                    </button>
                                );
                            })}
                            {projectOptions.length > 4 && (
                                <button
                                    type="button"
                                    onClick={() => toggleProject(PROJECT_UNASSIGNED)}
                                    className="filter-chip py-0.5 text-[10px] h-6 filter-chip-inactive"
                                >
                                    +{projectOptions.length - 4}
                                </button>
                            )}
                        </div>

                        {/* Scope badge */}
                        <span className="inline-flex items-center gap-1 rounded-[var(--radius-sm)] border border-primary/20 bg-primary/8 px-1.5 py-px font-mono text-[9px] text-primary shrink-0">
                            <Layers className="h-2.5 w-2.5" />
                            {filteredRuns.length}
                        </span>

                        {/* Actions — pushed right */}
                        <div className="ml-auto flex shrink-0 items-center gap-2">
                            <Button
                                variant="secondary"
                                size="sm"
                                leading={<GitCompareArrows className="h-3 w-3" />}
                                disabled={selectedRuns.size !== 2}
                                onClick={handleCompare}
                                title={
                                    selectedRuns.size === 2
                                        ? "Compare selected runs"
                                        : "Select exactly 2 runs"
                                }
                            >
                                Compare
                            </Button>
                            <Button
                                variant="primary"
                                size="sm"
                                leading={<ArrowUpRight className="h-3 w-3" />}
                                onClick={() => navigate("/studio")}
                            >
                                New run
                            </Button>
                        </div>
                    </div>
                </div>

                {/* ══════════════════════════════════════════════════════
                 *  BODY — two-column: left rail + main content
                 * ══════════════════════════════════════════════════════ */}
                <div className="flex flex-1 min-h-0">

                    {/* ─── LEFT RAIL — persistent KPI column ──────────── */}
                    <aside className="reveal reveal-2 w-44 shrink-0 border-r border-border bg-card/50 flex flex-col gap-0 overflow-y-auto">
                        {/* Rail header */}
                        <div className="px-3 pt-3 pb-2 border-b border-border/60">
                            <p className="font-mono text-[8px] uppercase tracking-[0.25em] text-muted-foreground/60">
                                Metrics
                            </p>
                        </div>

                        {/* KPI tiles — stacked vertically */}
                        <div className="flex flex-col gap-px p-2">
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
                                                        <stop offset="0%" stopColor={CHART_PASS_RATE_COLOR} stopOpacity={0.35} />
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

                            <StatCard
                                label="Runs"
                                value={stats.totalRuns.toLocaleString()}
                                delta={fmtCountDelta(deltas?.totalRuns)}
                                deltaDirection={deltaDir(deltas?.totalRuns)}
                                deltaIsPositiveGood
                                authority="T1"
                                icon={<Database className="h-2.5 w-2.5" />}
                                caption="in scope"
                            />

                            <StatCard
                                label="Test Cases"
                                value={stats.totalTestCases.toLocaleString()}
                                delta={fmtCountDelta(deltas?.totalTestCases)}
                                deltaDirection={deltaDir(deltas?.totalTestCases)}
                                deltaIsPositiveGood
                                authority="T1"
                                icon={<Activity className="h-2.5 w-2.5" />}
                                caption="evaluated"
                            />

                            <StatCard
                                label="LLM Cost"
                                value={`$${stats.totalCost.toFixed(2)}`}
                                delta={fmtCostDelta(deltas?.totalCost)}
                                deltaDirection={deltaDir(deltas?.totalCost)}
                                deltaIsPositiveGood={false}
                                authority="T1"
                                icon={<DollarSign className="h-2.5 w-2.5" />}
                                caption="USD in scope"
                            />
                        </div>

                        {/* Rail divider */}
                        <div className="mt-2 mx-3 border-t border-border/40" />

                        {/* Metric filter — inline in rail */}
                        <div className="px-3 pt-3 pb-2">
                            <p className="mb-2 font-mono text-[8px] uppercase tracking-[0.25em] text-muted-foreground/60">
                                Chart metrics
                            </p>
                            <div className="flex flex-col gap-1">
                                {availableMetrics.length === 0 ? (
                                    <span className="font-mono text-[9px] text-muted-foreground">none</span>
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
                                                        ? "bg-secondary/80 text-foreground"
                                                        : "text-muted-foreground hover:bg-secondary/40 hover:text-foreground"
                                                }`}
                                            >
                                                <span
                                                    className="h-1.5 w-1.5 shrink-0 rounded-full"
                                                    style={{
                                                        background: sel ? swatch : "hsl(var(--border))",
                                                    }}
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

                        {/* ── CHART ZONE — dominant, side-by-side ──────── */}
                        <section className="reveal reveal-3 border-b border-border">
                            <div className="grid grid-cols-1 gap-0 xl:grid-cols-2">

                                {/* Pass rate chart */}
                                <div className="border-r border-border p-5">
                                    <div className="mb-3 flex items-center justify-between gap-2">
                                        <div>
                                            <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">
                                                Pass Rate Trend
                                            </p>
                                            <p className="mt-0.5 font-mono text-[9px] text-muted-foreground/60">
                                                weighted by test cases / day
                                            </p>
                                        </div>
                                        <AuthorityBadge level="T2" scope="evaluation_gate" />
                                    </div>
                                    <div className="h-[220px]">
                                        {passRateSeries.length === 0 ? (
                                            <div className="flex h-full items-center justify-center font-mono text-[10px] text-muted-foreground">
                                                no data for selected filters
                                            </div>
                                        ) : (
                                            <ResponsiveContainer width="100%" height="100%">
                                                <AreaChart
                                                    data={passRateSeries}
                                                    margin={{ top: 4, right: 8, left: -12, bottom: 0 }}
                                                >
                                                    <defs>
                                                        <linearGradient id="passGrad" x1="0" y1="0" x2="0" y2="1">
                                                            <stop offset="5%" stopColor={CHART_PASS_RATE_COLOR} stopOpacity={0.2} />
                                                            <stop offset="95%" stopColor={CHART_PASS_RATE_COLOR} stopOpacity={0.01} />
                                                        </linearGradient>
                                                    </defs>
                                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={CHART_GRID} />
                                                    <XAxis
                                                        dataKey="date"
                                                        stroke="transparent"
                                                        tick={{ fill: "hsl(220 8% 50%)", fontSize: 9, fontFamily: "'JetBrains Mono', monospace" }}
                                                        tickLine={false}
                                                        axisLine={false}
                                                        tickFormatter={formatShortDate}
                                                    />
                                                    <YAxis
                                                        tick={{ fill: "hsl(220 8% 50%)", fontSize: 9, fontFamily: "'JetBrains Mono', monospace" }}
                                                        tickLine={false}
                                                        axisLine={false}
                                                        domain={[0, 100]}
                                                        tickFormatter={(v) => `${v}%`}
                                                        width={32}
                                                    />
                                                    <Tooltip
                                                        formatter={(v: number | undefined) =>
                                                            v == null ? "—" : `${v.toFixed(1)}%`
                                                        }
                                                        labelFormatter={(l) => `${l}`}
                                                        contentStyle={TOOLTIP_STYLE}
                                                        cursor={{ stroke: "hsl(228 10% 25%)", strokeWidth: 1 }}
                                                    />
                                                    <Area
                                                        type="monotone"
                                                        dataKey="passRate"
                                                        stroke={CHART_PASS_RATE_COLOR}
                                                        strokeWidth={1.75}
                                                        fill="url(#passGrad)"
                                                        name="pass rate"
                                                        dot={false}
                                                        activeDot={{ r: 2.5, strokeWidth: 0, fill: CHART_PASS_RATE_COLOR }}
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
                                            <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">
                                                Metric Trends
                                            </p>
                                            <p className="mt-0.5 font-mono text-[9px] text-muted-foreground/60">
                                                average scores over time
                                            </p>
                                        </div>
                                        <AuthorityBadge level="T1" scope="metric_evidence" />
                                    </div>
                                    <div className="h-[220px]">
                                        {metricSeries.length === 0 || selectedMetrics.length === 0 ? (
                                            <div className="flex h-full items-center justify-center font-mono text-[10px] text-muted-foreground">
                                                select metrics in the left rail
                                            </div>
                                        ) : (
                                            <ResponsiveContainer width="100%" height="100%">
                                                <LineChart
                                                    data={metricSeries}
                                                    margin={{ top: 4, right: 8, left: -12, bottom: 0 }}
                                                >
                                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={CHART_GRID} />
                                                    <XAxis
                                                        dataKey="date"
                                                        stroke="transparent"
                                                        tick={{ fill: "hsl(220 8% 50%)", fontSize: 9, fontFamily: "'JetBrains Mono', monospace" }}
                                                        tickLine={false}
                                                        axisLine={false}
                                                        tickFormatter={formatShortDate}
                                                    />
                                                    <YAxis
                                                        tick={{ fill: "hsl(220 8% 50%)", fontSize: 9, fontFamily: "'JetBrains Mono', monospace" }}
                                                        tickLine={false}
                                                        axisLine={false}
                                                        domain={[0, 100]}
                                                        tickFormatter={(v) => `${v}%`}
                                                        width={32}
                                                    />
                                                    <Tooltip
                                                        formatter={(v: number | undefined) =>
                                                            v == null ? "—" : `${v.toFixed(1)}%`
                                                        }
                                                        labelFormatter={(l) => `${l}`}
                                                        contentStyle={TOOLTIP_STYLE}
                                                        cursor={{ stroke: "hsl(228 10% 25%)", strokeWidth: 1 }}
                                                    />
                                                    {selectedMetrics.map((metric, idx) => (
                                                        <Line
                                                            key={metric}
                                                            type="monotone"
                                                            dataKey={metric}
                                                            stroke={CHART_METRIC_COLORS[idx % CHART_METRIC_COLORS.length]}
                                                            strokeWidth={1.5}
                                                            dot={false}
                                                            activeDot={{ r: 2.5, strokeWidth: 0 }}
                                                            connectNulls
                                                        />
                                                    ))}
                                                </LineChart>
                                            </ResponsiveContainer>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* ── RUNS TABLE — dense, sortable, not card grid ── */}
                        <section className="reveal reveal-4 flex-1 min-h-0">
                            {/* Table header bar */}
                            <div className="flex items-center justify-between border-b border-border px-5 py-2 bg-secondary/30">
                                <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">
                                    Recent Runs
                                </p>
                                <span className="font-mono text-[9px] text-muted-foreground/60">
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
                                    <table className="w-full min-w-[800px] border-collapse">
                                        <thead>
                                            <tr className="border-b border-border bg-secondary/20">
                                                {/* Select col */}
                                                <th className="w-8 px-3 py-2 text-left" />
                                                <th className="px-3 py-2 text-left">
                                                    <SortHeader
                                                        label="Dataset"
                                                        sortKey="dataset_name"
                                                        current={sortKey}
                                                        dir={sortDir}
                                                        onSort={handleSort}
                                                    />
                                                </th>
                                                <th className="px-3 py-2 text-left">
                                                    <SortHeader
                                                        label="Model"
                                                        sortKey="model_name"
                                                        current={sortKey}
                                                        dir={sortDir}
                                                        onSort={handleSort}
                                                    />
                                                </th>
                                                <th className="px-3 py-2 text-right">
                                                    <SortHeader
                                                        label="Pass Rate"
                                                        sortKey="pass_rate"
                                                        current={sortKey}
                                                        dir={sortDir}
                                                        onSort={handleSort}
                                                    />
                                                </th>
                                                <th className="px-3 py-2 text-right">
                                                    <SortHeader
                                                        label="Cases"
                                                        sortKey="total_test_cases"
                                                        current={sortKey}
                                                        dir={sortDir}
                                                        onSort={handleSort}
                                                    />
                                                </th>
                                                <th className="px-3 py-2 text-left">
                                                    <span className="font-mono text-[9px] uppercase tracking-[0.15em] text-muted-foreground">
                                                        Metrics
                                                    </span>
                                                </th>
                                                <th className="px-3 py-2 text-left">
                                                    <span className="font-mono text-[9px] uppercase tracking-[0.15em] text-muted-foreground">
                                                        Verdict
                                                    </span>
                                                </th>
                                                <th className="px-3 py-2 text-right">
                                                    <SortHeader
                                                        label="Started"
                                                        sortKey="started_at"
                                                        current={sortKey}
                                                        dir={sortDir}
                                                        onSort={handleSort}
                                                    />
                                                </th>
                                                <th className="w-8 px-3 py-2" />
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {filteredRuns.map((run) => {
                                                const isSelected = selectedRuns.has(run.run_id);
                                                const passed = run.pass_rate >= 0.7;
                                                return (
                                                    <tr
                                                        key={run.run_id}
                                                        onClick={() => navigate(`/runs/${run.run_id}`)}
                                                        className={`group border-b border-border/40 transition-colors cursor-pointer ${
                                                            isSelected
                                                                ? "bg-primary/8 border-b-primary/20"
                                                                : "hover:bg-secondary/50"
                                                        }`}
                                                    >
                                                        {/* Select checkbox */}
                                                        <td className="px-3 py-2.5">
                                                            <button
                                                                type="button"
                                                                aria-pressed={isSelected}
                                                                aria-label={isSelected ? "Deselect run" : "Select for compare"}
                                                                onClick={(e) => toggleRunSelection(run.run_id, e)}
                                                                className={`flex h-4 w-4 items-center justify-center rounded-[var(--radius-sm)] border transition-colors ${
                                                                    isSelected
                                                                        ? "border-primary bg-primary text-primary-foreground"
                                                                        : "border-border/60 bg-muted/40 text-transparent hover:border-primary/40"
                                                                }`}
                                                            >
                                                                <Check className="h-2.5 w-2.5" />
                                                            </button>
                                                        </td>

                                                        {/* Dataset + project */}
                                                        <td className="px-3 py-2.5 max-w-[200px]">
                                                            <div className="flex items-center gap-1.5">
                                                                <Database className="h-3 w-3 shrink-0 text-muted-foreground" />
                                                                <span className="font-medium text-xs text-foreground truncate group-hover:text-primary transition-colors">
                                                                    {run.dataset_name}
                                                                </span>
                                                            </div>
                                                            {run.project_name && (
                                                                <span className="mt-0.5 block font-mono text-[9px] text-muted-foreground/60 truncate pl-4">
                                                                    {run.project_name}
                                                                </span>
                                                            )}
                                                        </td>

                                                        {/* Model */}
                                                        <td className="px-3 py-2.5 max-w-[160px]">
                                                            <div className="flex items-center gap-1">
                                                                <Cpu className="h-3 w-3 shrink-0 text-muted-foreground" />
                                                                <span className="font-mono text-[10px] text-muted-foreground truncate">
                                                                    {run.model_name}
                                                                </span>
                                                            </div>
                                                        </td>

                                                        {/* Pass rate — dial + bar */}
                                                        <td className="px-3 py-2.5 text-right">
                                                            <div className="flex items-center justify-end gap-2">
                                                                <div className="w-16 hidden sm:block">
                                                                    <div className="h-1 w-full overflow-hidden rounded-full bg-secondary">
                                                                        <div
                                                                            className="h-full rounded-full"
                                                                            style={{
                                                                                width: `${run.pass_rate * 100}%`,
                                                                                background: dialColor(run.pass_rate),
                                                                            }}
                                                                        />
                                                                    </div>
                                                                </div>
                                                                <Dial
                                                                    value={run.pass_rate}
                                                                    size={36}
                                                                    thickness={3}
                                                                    color={dialColor(run.pass_rate)}
                                                                    label={`Pass rate ${(run.pass_rate * 100).toFixed(0)}%`}
                                                                />
                                                            </div>
                                                        </td>

                                                        {/* Test cases */}
                                                        <td className="px-3 py-2.5 text-right">
                                                            <span className="font-mono text-[10px] text-foreground tabular-nums">
                                                                {run.passed_test_cases}
                                                                <span className="text-muted-foreground">/{run.total_test_cases}</span>
                                                            </span>
                                                        </td>

                                                        {/* Metric tags */}
                                                        <td className="px-3 py-2.5">
                                                            <div className="flex flex-wrap gap-0.5">
                                                                {run.metrics_evaluated.slice(0, 3).map((m) => (
                                                                    <span
                                                                        key={m}
                                                                        className="rounded-[var(--radius-sm)] border border-border/40 bg-muted/50 px-1 py-px font-mono text-[8px] text-muted-foreground"
                                                                    >
                                                                        {m}
                                                                    </span>
                                                                ))}
                                                                {run.metrics_evaluated.length > 3 && (
                                                                    <span className="rounded-[var(--radius-sm)] border border-border/40 bg-muted/50 px-1 py-px font-mono text-[8px] text-muted-foreground">
                                                                        +{run.metrics_evaluated.length - 3}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </td>

                                                        {/* Authority verdict */}
                                                        <td className="px-3 py-2.5">
                                                            <AuthorityBadge
                                                                level="T2"
                                                                verdict={passed ? "eval-pass" : "hold"}
                                                            />
                                                        </td>

                                                        {/* Timestamp */}
                                                        <td className="px-3 py-2.5 text-right">
                                                            <div className="flex items-center justify-end gap-1 text-muted-foreground">
                                                                <Clock className="h-2.5 w-2.5 shrink-0" />
                                                                <span className="font-mono text-[9px]">
                                                                    {new Date(run.started_at).toLocaleDateString()}
                                                                </span>
                                                            </div>
                                                        </td>

                                                        {/* Arrow */}
                                                        <td className="px-3 py-2.5">
                                                            <ArrowUpRight
                                                                className="h-3 w-3 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 group-hover:text-primary"
                                                            />
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

            {/* ── Floating compare bar ──────────────────────────────── */}
            {selectedRuns.size > 0 && (
                <div
                    className="fixed bottom-5 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3
                        rounded-[var(--radius)] border border-border bg-card px-4 py-2
                        animate-in slide-in-from-bottom-4 duration-200"
                    style={{ boxShadow: "var(--shadow-pop)" }}
                >
                    <span className="font-mono text-xs font-medium text-foreground">
                        {selectedRuns.size} selected
                    </span>
                    <div className="h-3 w-px bg-border" />
                    <button
                        onClick={() => setSelectedRuns(new Set())}
                        className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-wide text-muted-foreground transition-colors hover:text-foreground"
                    >
                        <X className="h-2.5 w-2.5" />
                        clear
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
