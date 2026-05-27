import { useEffect, useMemo, useState } from "react";
import { fetchRuns, type RunSummary } from "../services/api";
import {
    Activity,
    AlertCircle,
    ArrowUpRight,
    Check,
    Clock,
    Cpu,
    Database,
    DollarSign,
    GitCompareArrows,
    Layers,
    Search,
    SlidersHorizontal,
    TrendingDown,
    TrendingUp,
    X,
} from "lucide-react";
import { Layout } from "../components/Layout";
/*
 * Phase 4 "Data-Dense Pro × Warm" Dashboard.
 * Direction change from editorial Warm Console → dark-first instrument panel.
 * Data hooks / logic UNCHANGED. Full presentation rewrite for density + dark.
 * See docs/frontend/W-PHASE4-DIRECTION.md.
 */
import { AuthorityBadge, Button, Dial, EmptyState, StatCard } from "../design";
import { useNavigate } from "react-router-dom";
import {
    Area,
    AreaChart,
    CartesianGrid,
    Line,
    LineChart,
    Legend,
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

function projectLabel(value: string) {
    if (value === PROJECT_ALL) return "All";
    if (value === PROJECT_UNASSIGNED) return "Unassigned";
    return value;
}

function formatThresholdProfileLabel(profile?: string | null) {
    if (!profile) return "default";
    if (profile.toLowerCase() === "qa") return "QA";
    return profile.toLowerCase();
}

function applySearchFilter(runs: RunSummary[], query: string) {
    const q = query.trim().toLowerCase();
    if (!q) return runs;
    return runs.filter(
        (r) =>
            r.dataset_name.toLowerCase().includes(q) ||
            r.model_name.toLowerCase().includes(q) ||
            r.run_id.toLowerCase().includes(q) ||
            (r.project_name || "").toLowerCase().includes(q) ||
            (r.threshold_profile || "").toLowerCase().includes(q),
    );
}

// --- Delta helpers -------------------------------------------------------

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

// Tooltip style — dark instrument panel surface.
const TOOLTIP_STYLE = {
    borderRadius: "var(--radius)",
    border: "1px solid hsl(var(--border))",
    background: "hsl(32 18% 12%)",   // slightly lighter than card for pop
    color: "hsl(36 28% 88%)",
    boxShadow: "var(--shadow-pop)",
    fontSize: "11px",
    fontFamily: "'JetBrains Mono', ui-monospace, monospace",
} as const;

// Dial color: status-semantic, never brand clay.
function dialColor(rate: number): string {
    if (rate >= 0.7) return "hsl(var(--success))";
    if (rate >= 0.5) return "hsl(var(--warning))";
    return "hsl(var(--destructive))";
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
        return [...searched].sort(
            (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime(),
        );
    }, [dateFiltered, searchQuery]);

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
                        <div className="h-10 w-10 animate-pulse rounded-[var(--radius)] bg-primary/20" />
                        <Activity className="absolute left-3 top-3 h-4 w-4 animate-spin text-primary" />
                    </div>
                    <p className="font-mono text-xs text-muted-foreground">loading workspace…</p>
                </div>
            </Layout>
        );
    }

    if (error) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-background px-6">
                <div className="w-full max-w-sm rounded-[var(--radius)] border border-destructive/30 bg-card px-6">
                    <EmptyState
                        icon={<AlertCircle size={20} className="text-[hsl(var(--destructive))]" />}
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
    //  Main render
    // ------------------------------------------------------------------ //

    return (
        <Layout>
            {/* ── Page header ─────────────────────────────────────────── */}
            <header className="reveal reveal-1 mb-6 flex items-center justify-between gap-4">
                <div className="min-w-0">
                    {/* Mono kicker — instrument panel style */}
                    <p className="section-kicker mb-1 flex items-center gap-1.5">
                        <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary" />
                        eval dashboard
                    </p>
                    <h1 className="font-display text-2xl font-semibold tracking-tight text-foreground">
                        Evaluation Overview
                    </h1>
                    <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
                        Quality metrics across runs, by date range and project.
                        <span className="inline-flex items-center gap-1 rounded-[var(--radius-sm)] border border-primary/20 bg-primary/8 px-1.5 py-px font-mono text-[10px] text-primary">
                            <Layers className="h-2.5 w-2.5" />
                            {filteredRuns.length} in scope
                        </span>
                    </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                    <Button
                        variant="secondary"
                        size="sm"
                        leading={<GitCompareArrows className="h-3.5 w-3.5" />}
                        disabled={selectedRuns.size !== 2}
                        onClick={handleCompare}
                        title={
                            selectedRuns.size === 2
                                ? "Compare the two selected runs"
                                : "Select exactly 2 runs to compare"
                        }
                    >
                        Compare
                    </Button>
                    <Button
                        variant="primary"
                        size="sm"
                        leading={<ArrowUpRight className="h-3.5 w-3.5" />}
                        onClick={() => navigate("/studio")}
                    >
                        New run
                    </Button>
                </div>
            </header>

            {/* ── Filter bar ──────────────────────────────────────────── */}
            <section className="surface-panel reveal reveal-2 mb-5 p-4">
                <div className="mb-3 flex items-center gap-1.5 font-mono text-[10px] font-medium uppercase tracking-[0.15em] text-muted-foreground">
                    <SlidersHorizontal className="h-3 w-3 text-primary/80" />
                    Filters
                </div>
                <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
                    {/* Date range */}
                    <div className="space-y-2">
                        <label className="section-kicker block">Date range</label>
                        <select
                            value={rangePreset}
                            onChange={(e) => setRangePreset(e.target.value as DateRangePreset)}
                            className="field-control"
                        >
                            {DATE_RANGE_OPTIONS.map((o) => (
                                <option key={o.value} value={o.value}>
                                    {o.label}
                                </option>
                            ))}
                        </select>
                        {rangePreset === "custom" && (
                            <div className="grid grid-cols-2 gap-1.5">
                                <input
                                    type="date"
                                    value={customStart}
                                    onChange={(e) => setCustomStart(e.target.value)}
                                    className="field-control"
                                />
                                <input
                                    type="date"
                                    value={customEnd}
                                    onChange={(e) => setCustomEnd(e.target.value)}
                                    className="field-control"
                                />
                            </div>
                        )}
                        <div className="font-mono text-[10px] text-muted-foreground">
                            active:{" "}
                            <span className="text-foreground/80">{dateRange.label}</span>
                        </div>
                    </div>

                    {/* Projects */}
                    <div className="space-y-2">
                        <label className="section-kicker block">Projects</label>
                        <div className="flex flex-wrap gap-1.5">
                            {[PROJECT_ALL, PROJECT_UNASSIGNED, ...projectOptions].map((p) => {
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
                        </div>
                    </div>

                    {/* Search */}
                    <div className="space-y-2">
                        <label className="section-kicker block">Search</label>
                        <div className="relative">
                            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                            <input
                                type="text"
                                placeholder="dataset, model, run-id…"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="field-control pl-8"
                            />
                        </div>
                    </div>
                </div>
            </section>

            {/*
             * ── KPI row ──────────────────────────────────────────────
             * Four StatCards. Pass-rate is the hero (one clay-wash card).
             * All other cards are neutral dark. Authority hints tag evidence
             * level (T1 metric / T2 eval-gate) honestly — not verdicts.
             * Sparkline in the hero card uses teal (distinct from clay + T2-green).
             */}
            <section className="reveal reveal-3 mb-5 grid grid-cols-2 gap-3 xl:grid-cols-4">
                <StatCard
                    tone="hero"
                    label="Avg Pass Rate"
                    value={`${(stats.avgPassRate * 100).toFixed(1)}%`}
                    delta={fmtPctDelta(deltas?.avgPassRate)}
                    deltaDirection={deltaDir(deltas?.avgPassRate)}
                    deltaIsPositiveGood
                    authority="T2"
                    icon={
                        deltas && deltas.avgPassRate < 0
                            ? <TrendingDown className="h-3 w-3" />
                            : <TrendingUp className="h-3 w-3" />
                    }
                    spark={
                        passRateSeries.length > 1 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={passRateSeries} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor={CHART_PASS_RATE_COLOR} stopOpacity={0.4} />
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
                    caption="vs previous period"
                />
                <StatCard
                    label="Runs"
                    value={stats.totalRuns.toLocaleString()}
                    delta={fmtCountDelta(deltas?.totalRuns)}
                    deltaDirection={deltaDir(deltas?.totalRuns)}
                    deltaIsPositiveGood
                    authority="T1"
                    icon={<Database className="h-3 w-3" />}
                    caption="in scope"
                />
                <StatCard
                    label="Test Cases"
                    value={stats.totalTestCases.toLocaleString()}
                    delta={fmtCountDelta(deltas?.totalTestCases)}
                    deltaDirection={deltaDir(deltas?.totalTestCases)}
                    deltaIsPositiveGood
                    authority="T1"
                    icon={<Activity className="h-3 w-3" />}
                    caption="evaluated"
                />
                <StatCard
                    label="LLM Cost"
                    value={`$${stats.totalCost.toFixed(2)}`}
                    delta={fmtCostDelta(deltas?.totalCost)}
                    deltaDirection={deltaDir(deltas?.totalCost)}
                    deltaIsPositiveGood={false}
                    authority="T1"
                    icon={<DollarSign className="h-3 w-3" />}
                    caption="USD in scope"
                />
            </section>

            {/*
             * ── Charts — the hero section ────────────────────────────
             * Charts are prominent (taller panels, 300px / 280px height).
             * Grid lines visible (dark ground makes them readable without noise).
             * Pass-rate uses teal area; metric lines use the high-sep ramp.
             */}
            <section className="reveal reveal-4 mb-5 grid grid-cols-1 gap-4 xl:grid-cols-2">
                {/* Pass rate trend */}
                <div className="chart-panel p-5">
                    <div className="mb-4 flex items-center justify-between gap-3">
                        <div>
                            <h2 className="section-title">Pass Rate Trend</h2>
                            <p className="mt-px font-mono text-[10px] text-muted-foreground">
                                weighted by test cases / day
                            </p>
                        </div>
                        <AuthorityBadge level="T2" scope="evaluation_gate" />
                    </div>
                    <div className="h-[300px]">
                        {passRateSeries.length === 0 ? (
                            <div className="flex h-full items-center justify-center font-mono text-xs text-muted-foreground">
                                no data for selected filters
                            </div>
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart
                                    data={passRateSeries}
                                    margin={{ top: 8, right: 16, left: -8, bottom: 0 }}
                                >
                                    <defs>
                                        <linearGradient id="passGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={CHART_PASS_RATE_COLOR} stopOpacity={0.25} />
                                            <stop offset="95%" stopColor={CHART_PASS_RATE_COLOR} stopOpacity={0.02} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid
                                        strokeDasharray="4 4"
                                        vertical={false}
                                        stroke="hsl(32 12% 20%)"
                                    />
                                    <XAxis
                                        dataKey="date"
                                        stroke="hsl(var(--muted-foreground))"
                                        fontSize={10}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={formatShortDate}
                                        fontFamily="'JetBrains Mono', monospace"
                                    />
                                    <YAxis
                                        stroke="hsl(var(--muted-foreground))"
                                        fontSize={10}
                                        tickLine={false}
                                        axisLine={false}
                                        domain={[0, 100]}
                                        tickFormatter={(v) => `${v}%`}
                                        fontFamily="'JetBrains Mono', monospace"
                                        width={36}
                                    />
                                    <Tooltip
                                        formatter={(v: number | undefined) =>
                                            v == null ? "—" : `${v.toFixed(1)}%`
                                        }
                                        labelFormatter={(l) => `date: ${l}`}
                                        contentStyle={TOOLTIP_STYLE}
                                        cursor={{ stroke: "hsl(32 20% 28%)", strokeWidth: 1 }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="passRate"
                                        stroke={CHART_PASS_RATE_COLOR}
                                        strokeWidth={2}
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

                {/* Metric trend */}
                <div className="chart-panel p-5">
                    <div className="mb-3 flex items-center justify-between gap-3">
                        <div>
                            <h2 className="section-title">Metric Trends</h2>
                            <p className="mt-px font-mono text-[10px] text-muted-foreground">
                                average scores over time
                            </p>
                        </div>
                        <AuthorityBadge level="T1" scope="metric_evidence" />
                    </div>
                    {/* Metric selector chips */}
                    <div className="mb-3 flex flex-wrap gap-1.5">
                        {availableMetrics.length === 0 ? (
                            <span className="font-mono text-[10px] text-muted-foreground">
                                no metrics available
                            </span>
                        ) : (
                            availableMetrics.map((metric, idx) => {
                                const sel = selectedMetrics.includes(metric);
                                const selIdx = selectedMetrics.indexOf(metric);
                                const swatch =
                                    CHART_METRIC_COLORS[
                                        selIdx >= 0 ? selIdx % CHART_METRIC_COLORS.length : idx % CHART_METRIC_COLORS.length
                                    ];
                                return (
                                    <button
                                        key={metric}
                                        type="button"
                                        onClick={() => toggleMetric(metric)}
                                        aria-pressed={sel}
                                        className={`filter-chip inline-flex items-center gap-1 font-mono ${
                                            sel ? "filter-chip-active" : "filter-chip-inactive"
                                        }`}
                                    >
                                        {sel && (
                                            <span
                                                className="h-1.5 w-1.5 shrink-0 rounded-full"
                                                style={{ background: swatch }}
                                            />
                                        )}
                                        {metric}
                                    </button>
                                );
                            })
                        )}
                    </div>
                    <div className="h-[268px]">
                        {metricSeries.length === 0 || selectedMetrics.length === 0 ? (
                            <div className="flex h-full items-center justify-center font-mono text-xs text-muted-foreground">
                                select metrics above
                            </div>
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart
                                    data={metricSeries}
                                    margin={{ top: 8, right: 16, left: -8, bottom: 0 }}
                                >
                                    <CartesianGrid
                                        strokeDasharray="4 4"
                                        vertical={false}
                                        stroke="hsl(32 12% 20%)"
                                    />
                                    <XAxis
                                        dataKey="date"
                                        stroke="hsl(var(--muted-foreground))"
                                        fontSize={10}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={formatShortDate}
                                        fontFamily="'JetBrains Mono', monospace"
                                    />
                                    <YAxis
                                        stroke="hsl(var(--muted-foreground))"
                                        fontSize={10}
                                        tickLine={false}
                                        axisLine={false}
                                        domain={[0, 100]}
                                        tickFormatter={(v) => `${v}%`}
                                        fontFamily="'JetBrains Mono', monospace"
                                        width={36}
                                    />
                                    <Tooltip
                                        formatter={(v: number | undefined) =>
                                            v == null ? "—" : `${v.toFixed(1)}%`
                                        }
                                        labelFormatter={(l) => `date: ${l}`}
                                        contentStyle={TOOLTIP_STYLE}
                                        cursor={{ stroke: "hsl(32 20% 28%)", strokeWidth: 1 }}
                                    />
                                    <Legend
                                        wrapperStyle={{
                                            fontSize: "10px",
                                            fontFamily: "'JetBrains Mono', monospace",
                                            paddingTop: "6px",
                                            color: "hsl(var(--muted-foreground))",
                                        }}
                                    />
                                    {selectedMetrics.map((metric, idx) => (
                                        <Line
                                            key={metric}
                                            type="monotone"
                                            dataKey={metric}
                                            stroke={CHART_METRIC_COLORS[idx % CHART_METRIC_COLORS.length]}
                                            strokeWidth={1.75}
                                            dot={false}
                                            activeDot={{ r: 3, strokeWidth: 0 }}
                                            connectNulls
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>
            </section>

            {/* ── Run grid ────────────────────────────────────────────── */}
            <section className="reveal reveal-5">
                <div className="mb-3 flex items-center justify-between">
                    <h2 className="section-title">Recent Runs</h2>
                    <span className="font-mono text-[10px] text-muted-foreground">
                        {filteredRuns.length} shown
                    </span>
                </div>

                {filteredRuns.length === 0 ? (
                    <div className="surface-card">
                        <EmptyState
                            compact
                            icon={<Database size={18} />}
                            title="No runs in scope"
                            description="Adjust the date range, project, or search query."
                        />
                    </div>
                ) : (
                    <div className="grid grid-cols-1 gap-3 pb-24 md:grid-cols-2 xl:grid-cols-3">
                        {filteredRuns.map((run) => {
                            const isSelected = selectedRuns.has(run.run_id);
                            const passed = run.pass_rate >= 0.7;
                            return (
                                <article
                                    key={run.run_id}
                                    onClick={() => navigate(`/runs/${run.run_id}`)}
                                    className={`group relative cursor-pointer overflow-hidden rounded-[var(--radius)] border bg-card p-4
                                        transition-all duration-[var(--duration-base)]
                                        hover:border-primary/30 hover:bg-[hsl(32_14%_12%)]
                                        ${isSelected
                                            ? "border-primary/50 ring-1 ring-primary/30"
                                            : "border-border"
                                        }`}
                                    style={{ boxShadow: "var(--shadow-card)" }}
                                >
                                    {/* Top accent line — clay on hover/select */}
                                    <div
                                        className={`absolute inset-x-0 top-0 h-px transition-opacity duration-[var(--duration-base)]
                                            ${isSelected ? "opacity-100" : "opacity-0 group-hover:opacity-100"}`}
                                        style={{
                                            background: `linear-gradient(90deg, transparent, hsl(var(--primary)/0.7), transparent)`,
                                        }}
                                    />

                                    {/* Selection toggle */}
                                    <button
                                        type="button"
                                        aria-pressed={isSelected}
                                        aria-label={isSelected ? "Deselect run" : "Select for compare"}
                                        onClick={(e) => toggleRunSelection(run.run_id, e)}
                                        className={`absolute right-3 top-3 z-10 flex h-5 w-5 items-center justify-center
                                            rounded-[var(--radius-sm)] border transition-colors
                                            ${isSelected
                                                ? "border-primary bg-primary text-[hsl(30_26%_7%)]"
                                                : "border-border/60 bg-muted/40 text-transparent hover:border-primary/40"
                                            }`}
                                    >
                                        <Check className="h-3 w-3" />
                                    </button>

                                    {/* Header: dataset + dial */}
                                    <div className="mb-3 flex items-start justify-between gap-3">
                                        <div className="min-w-0 space-y-1.5 pr-5">
                                            <div className="flex items-center gap-1.5">
                                                <Database className="h-3 w-3 shrink-0 text-muted-foreground" />
                                                <h3 className="truncate text-sm font-semibold text-foreground transition-colors group-hover:text-primary">
                                                    {run.dataset_name}
                                                </h3>
                                            </div>
                                            <div className="flex flex-wrap items-center gap-1">
                                                <span className="rounded-[var(--radius-sm)] border border-border/60 bg-secondary/60 px-1.5 py-px font-mono text-[9px] text-muted-foreground">
                                                    {run.project_name || "unassigned"}
                                                </span>
                                                <span className="rounded-[var(--radius-sm)] border border-border/60 bg-secondary/60 px-1.5 py-px font-mono text-[9px] text-muted-foreground">
                                                    {formatThresholdProfileLabel(run.threshold_profile)}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-1 text-muted-foreground">
                                                <Cpu className="h-3 w-3 shrink-0" />
                                                <span className="truncate font-mono text-[9px]">
                                                    {run.model_name}
                                                </span>
                                            </div>
                                        </div>

                                        <Dial
                                            value={run.pass_rate}
                                            size={48}
                                            thickness={4}
                                            color={dialColor(run.pass_rate)}
                                            label={`Pass rate ${(run.pass_rate * 100).toFixed(0)}%`}
                                            className="shrink-0 transition-transform duration-[var(--duration-base)] group-hover:scale-105"
                                        />
                                    </div>

                                    {/* Progress + authority + metric tags */}
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="font-mono text-[10px] text-muted-foreground">
                                                {run.passed_test_cases}/{run.total_test_cases} passed
                                            </span>
                                            {/* T2 verdict — honest authority surfacing, never implies T3 promote */}
                                            <AuthorityBadge
                                                level="T2"
                                                verdict={passed ? "eval-pass" : "hold"}
                                            />
                                        </div>

                                        {/* Progress bar */}
                                        <div className="h-1 w-full overflow-hidden rounded-full bg-secondary">
                                            <div
                                                className="h-full rounded-full transition-all duration-[var(--duration-slow)]"
                                                style={{
                                                    width: `${run.pass_rate * 100}%`,
                                                    background: dialColor(run.pass_rate),
                                                }}
                                            />
                                        </div>

                                        {/* Metric tags */}
                                        <div className="flex flex-wrap gap-1">
                                            {run.metrics_evaluated.slice(0, 4).map((m) => (
                                                <span
                                                    key={m}
                                                    className="rounded-[var(--radius-sm)] border border-border/40 bg-muted/50 px-1.5 py-px font-mono text-[9px] text-muted-foreground"
                                                >
                                                    {m}
                                                </span>
                                            ))}
                                            {run.metrics_evaluated.length > 4 && (
                                                <span className="rounded-[var(--radius-sm)] border border-border/40 bg-muted/50 px-1.5 py-px font-mono text-[9px] text-muted-foreground">
                                                    +{run.metrics_evaluated.length - 4}
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Footer: timestamp + arrow */}
                                    <div className="mt-3 flex items-center justify-between border-t border-border/40 pt-2.5 text-muted-foreground">
                                        <div className="flex items-center gap-1">
                                            <Clock className="h-3 w-3" />
                                            <span className="font-mono text-[9px]">
                                                {new Date(run.started_at).toLocaleDateString()}
                                            </span>
                                            {run.finished_at && (
                                                <span className="font-mono text-[9px] opacity-50">
                                                    {" · "}
                                                    {new Date(run.finished_at).toLocaleTimeString([], {
                                                        hour: "2-digit",
                                                        minute: "2-digit",
                                                    })}
                                                </span>
                                            )}
                                        </div>
                                        <ArrowUpRight
                                            className="h-3.5 w-3.5 -translate-x-1 opacity-0 transition-all
                                                duration-[var(--duration-base)] group-hover:translate-x-0
                                                group-hover:text-primary group-hover:opacity-100"
                                        />
                                    </div>
                                </article>
                            );
                        })}
                    </div>
                )}
            </section>

            {/* ── Floating compare bar ────────────────────────────────── */}
            {selectedRuns.size > 0 && (
                <div
                    className="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3
                        rounded-[var(--radius)] border border-border bg-card px-4 py-2.5
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
                        <X className="h-3 w-3" />
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
