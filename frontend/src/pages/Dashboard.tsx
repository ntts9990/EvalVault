import { useEffect, useMemo, useState } from "react";
import { fetchRuns, type RunSummary } from "../services/api";
import {
    Activity,
    AlertCircle,
    ArrowUpRight,
    Clock,
    Cpu,
    Database,
    DollarSign,
    Search,
    TrendingDown,
    TrendingUp,
} from "lucide-react";
import { Layout } from "../components/Layout";
import { useNavigate } from "react-router-dom";
import {
    Area,
    AreaChart,
    CartesianGrid,
    Legend,
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
    CUSTOM_RANGE_DEFAULT_DAYS,
    DATE_RANGE_OPTIONS,
    DEFAULT_DATE_RANGE_PRESET,
    PASS_RATE_COLOR_BANDS,
} from "../config/ui";

type MetricTrendRow = Record<string, number | string | null>;

function formatDelta(value: number, unit: string) {
    const sign = value > 0 ? "+" : value < 0 ? "-" : "";
    const absValue = Math.abs(value);
    return `${sign}${absValue.toFixed(1)}${unit}`;
}

function projectLabel(value: string) {
    if (value === PROJECT_ALL) return "All Projects";
    if (value === PROJECT_UNASSIGNED) return "Unassigned";
    return value;
}

function formatThresholdProfileLabel(profile?: string | null) {
    if (!profile) return "Default";
    if (profile.toLowerCase() === "qa") return "QA";
    return `${profile.charAt(0).toUpperCase()}${profile.slice(1)}`;
}

function applySearchFilter(runs: RunSummary[], query: string) {
    const trimmed = query.trim().toLowerCase();
    if (!trimmed) return runs;
    return runs.filter((run) => {
        return (
            run.dataset_name.toLowerCase().includes(trimmed) ||
            run.model_name.toLowerCase().includes(trimmed) ||
            run.run_id.toLowerCase().includes(trimmed) ||
            (run.project_name || "").toLowerCase().includes(trimmed) ||
            (run.threshold_profile || "").toLowerCase().includes(trimmed)
        );
    });
}

export function Dashboard() {
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const [selectedRuns, setSelectedRuns] = useState<Set<string>>(new Set());
    const [searchQuery, setSearchQuery] = useState("");
    const [rangePreset, setRangePreset] = useState<DateRangePreset>(DEFAULT_DATE_RANGE_PRESET);
    const [customStart, setCustomStart] = useState(() => {
        const offset = -(CUSTOM_RANGE_DEFAULT_DAYS - 1);
        return toDateInputValue(addDays(new Date(), offset));
    });
    const [customEnd, setCustomEnd] = useState(() => toDateInputValue(new Date()));
    const [selectedProjects, setSelectedProjects] = useState<string[]>([PROJECT_ALL]);
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);

    useEffect(() => {
        async function loadRuns() {
            try {
                const data = await fetchRuns();
                setRuns(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load runs");
            } finally {
                setLoading(false);
            }
        }
        loadRuns();
    }, []);

    const toggleRunSelection = (runId: string, event: React.MouseEvent) => {
        event.stopPropagation();
        const next = new Set(selectedRuns);
        if (next.has(runId)) {
            next.delete(runId);
        } else {
            next.add(runId);
        }
        setSelectedRuns(next);
    };

    const toggleProjectSelection = (value: string) => {
        setSelectedProjects((prev) => {
            if (value === PROJECT_ALL) {
                return [PROJECT_ALL];
            }
            const next = new Set(prev.filter((item) => item !== PROJECT_ALL));
            if (next.has(value)) {
                next.delete(value);
            } else {
                next.add(value);
            }
            if (next.size === 0) {
                return [PROJECT_ALL];
            }
            return Array.from(next);
        });
    };

    const toggleMetricSelection = (value: string) => {
        setSelectedMetrics((prev) => {
            if (prev.includes(value)) {
                return prev.filter((metric) => metric !== value);
            }
            return [...prev, value];
        });
    };

    const handleCompare = () => {
        if (selectedRuns.size !== 2) return;
        const [base, target] = Array.from(selectedRuns);
        navigate(`/compare?base=${base}&target=${target}`);
    };

    const getPassRateColor = (rate: number) => {
        const match = PASS_RATE_COLOR_BANDS.find((band) => rate >= band.min);
        return match ? match.className : PASS_RATE_COLOR_BANDS.at(-1)?.className ?? "";
    };

    const projectOptions = useMemo(() => collectProjectNames(runs), [runs]);
    const dateRange = useMemo(
        () => resolveDateRange(rangePreset, customStart, customEnd),
        [rangePreset, customStart, customEnd]
    );
    const previousRange = useMemo(
        () => getPreviousRange(dateRange.from, dateRange.to),
        [dateRange.from, dateRange.to]
    );

    const projectFilteredRuns = useMemo(
        () => filterRunsByProjects(runs, selectedProjects),
        [runs, selectedProjects]
    );
    const dateFilteredRuns = useMemo(
        () => filterRunsByDate(projectFilteredRuns, dateRange.from, dateRange.to),
        [projectFilteredRuns, dateRange.from, dateRange.to]
    );
    const filteredRuns = useMemo(() => {
        const searched = applySearchFilter(dateFilteredRuns, searchQuery);
        return [...searched].sort(
            (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
        );
    }, [dateFilteredRuns, searchQuery]);

    const stats = useMemo(() => computeStats(filteredRuns), [filteredRuns]);
    const previousStats = useMemo(() => {
        if (!previousRange.from || !previousRange.to) return null;
        const prevRuns = filterRunsByDate(projectFilteredRuns, previousRange.from, previousRange.to);
        return computeStats(applySearchFilter(prevRuns, searchQuery));
    }, [previousRange.from, previousRange.to, projectFilteredRuns, searchQuery]);

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
        [filteredRuns, dateRange.from, dateRange.to]
    );

    const passRateSeries = useMemo(
        () =>
            trendSeries.map((point) => ({
                date: point.date,
                passRate:
                    point.totalCases > 0 ? Number((point.passRate * 100).toFixed(2)) : null,
                totalCases: point.totalCases,
            })),
        [trendSeries]
    );

    const availableMetrics = useMemo(() => {
        const set = new Set<string>();
        filteredRuns.forEach((run) => {
            Object.keys(run.avg_metric_scores || {}).forEach((metric) => set.add(metric));
        });
        return Array.from(set).sort((a, b) => a.localeCompare(b));
    }, [filteredRuns]);

    useEffect(() => {
        setSelectedMetrics((prev) => {
            const valid = prev.filter((metric) => availableMetrics.includes(metric));
            if (valid.length > 0) return valid;
            return availableMetrics.slice(0, 2);
        });
    }, [availableMetrics]);

    const metricSeries: MetricTrendRow[] = useMemo(() => {
        if (selectedMetrics.length === 0) return [];
        return trendSeries.map((point) => {
            const row: MetricTrendRow = { date: point.date };
            selectedMetrics.forEach((metric) => {
                const value = point.metricAverages[metric];
                row[metric] = typeof value === "number" ? Number((value * 100).toFixed(2)) : null;
            });
            return row;
        });
    }, [trendSeries, selectedMetrics]);

    useEffect(() => {
        const allowedIds = new Set(filteredRuns.map((run) => run.run_id));
        setSelectedRuns((prev) => {
            const next = new Set(Array.from(prev).filter((id) => allowedIds.has(id)));
            return next.size === prev.size ? prev : next;
        });
    }, [filteredRuns]);

    if (loading) {
        return (
            <Layout>
                <div className="flex flex-col items-center justify-center h-[60vh] animate-in fade-in duration-500 gap-4">
                    <div className="relative">
                        <div className="w-12 h-12 rounded-xl bg-primary/20 animate-pulse"></div>
                        <Activity className="w-6 h-6 text-primary absolute top-3 left-3 animate-spin" />
                    </div>
                    <p className="text-muted-foreground font-medium animate-pulse">
                        Loading workspace...
                    </p>
                </div>
            </Layout>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-background text-foreground">
                <div className="flex flex-col items-center gap-4 text-destructive p-8 rounded-2xl bg-destructive/5 border border-destructive/20 max-w-md text-center">
                    <AlertCircle className="w-12 h-12" />
                    <div>
                        <p className="text-xl font-bold tracking-tight">System Error</p>
                        <p className="text-sm opacity-80 mt-1">{error}</p>
                    </div>
                    <button
                        onClick={() => window.location.reload()}
                        className="mt-4 px-4 py-2 bg-destructive text-destructive-foreground rounded-lg font-medium hover:opacity-90 transition-opacity"
                    >
                        Retry Connection
                    </button>
                </div>
            </div>
        );
    }

    return (
        <Layout>
            <div className="mb-10">
                <h1 className="text-3xl font-bold tracking-tight mb-2 font-display">Evaluation Overview</h1>
                <p className="text-muted-foreground flex items-center gap-2">
                    Track performance by date range and project scope
                    <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium border border-primary/20">
                        {filteredRuns.length} runs in scope
                    </span>
                </p>
            </div>

            <div className="surface-card p-6 mb-8">
                <div className="flex items-center gap-2 text-sm font-semibold mb-4">
                    <span className="inline-flex h-2 w-2 rounded-full bg-primary"></span>
                    Filters
                </div>
                <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                    <div className="space-y-3">
                        <label className="text-xs font-semibold text-muted-foreground uppercase">
                            Date Range
                        </label>
                        <select
                            value={rangePreset}
                            onChange={(event) => setRangePreset(event.target.value as DateRangePreset)}
                            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                        >
                            {DATE_RANGE_OPTIONS.map((option) => (
                                <option key={option.value} value={option.value}>
                                    {option.label}
                                </option>
                            ))}
                        </select>
                        {rangePreset === "custom" && (
                            <div className="grid grid-cols-2 gap-2">
                                <input
                                    type="date"
                                    value={customStart}
                                    onChange={(event) => setCustomStart(event.target.value)}
                                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                                />
                                <input
                                    type="date"
                                    value={customEnd}
                                    onChange={(event) => setCustomEnd(event.target.value)}
                                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                                />
                            </div>
                        )}
                        <div className="text-xs text-muted-foreground">
                            Active: {dateRange.label}
                        </div>
                    </div>

                    <div className="space-y-3">
                        <label className="text-xs font-semibold text-muted-foreground uppercase">
                            Projects
                        </label>
                        <div className="flex flex-wrap gap-2">
                            {[PROJECT_ALL, PROJECT_UNASSIGNED, ...projectOptions].map((project) => {
                                const isSelected = selectedProjects.includes(project);
                                return (
                                    <button
                                        key={project}
                                        type="button"
                                        onClick={() => toggleProjectSelection(project)}
                                        className={`filter-chip ${isSelected
                                            ? "filter-chip-active"
                                            : "filter-chip-inactive"
                                            }`}
                                    >
                                        {projectLabel(project)}
                                    </button>
                                );
                            })}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Select multiple projects to compare grouped performance.
                        </p>
                    </div>

                    <div className="space-y-3">
                        <label className="text-xs font-semibold text-muted-foreground uppercase">
                            Search
                        </label>
                        <div className="relative">
                            <Search className="w-4 h-4 absolute left-3 top-3 text-muted-foreground" />
                            <input
                                type="text"
                                placeholder="Search by dataset, model, run, or project..."
                                value={searchQuery}
                                onChange={(event) => setSearchQuery(event.target.value)}
                                className="w-full pl-9 pr-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all shadow-sm"
                            />
                        </div>
                        <p className="text-xs text-muted-foreground">
                            {dateRange.from ? "Filtering to selected range." : "Showing all available history."}
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
                <div className="surface-card p-5">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground font-medium">Runs</p>
                            <p className="text-2xl font-bold mt-1">{stats.totalRuns.toLocaleString()}</p>
                        </div>
                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                            <Database className="w-5 h-5" />
                        </div>
                    </div>
                    {deltas && (
                        <div className="mt-3 flex items-center gap-2 text-xs">
                            {deltas.totalRuns >= 0 ? (
                                <TrendingUp className="w-3 h-3 text-emerald-500" />
                            ) : (
                                <TrendingDown className="w-3 h-3 text-rose-500" />
                            )}
                            <span className={deltas.totalRuns >= 0 ? "text-emerald-500" : "text-rose-500"}>
                                {deltas.totalRuns >= 0 ? "+" : ""}{deltas.totalRuns}
                            </span>
                            <span className="text-muted-foreground">vs previous period</span>
                        </div>
                    )}
                </div>

                <div className="surface-card p-5">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground font-medium">Test Cases</p>
                            <p className="text-2xl font-bold mt-1">
                                {stats.totalTestCases.toLocaleString()}
                            </p>
                        </div>
                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                            <Activity className="w-5 h-5" />
                        </div>
                    </div>
                    {deltas && (
                        <div className="mt-3 flex items-center gap-2 text-xs">
                            {deltas.totalTestCases >= 0 ? (
                                <TrendingUp className="w-3 h-3 text-emerald-500" />
                            ) : (
                                <TrendingDown className="w-3 h-3 text-rose-500" />
                            )}
                            <span className={deltas.totalTestCases >= 0 ? "text-emerald-500" : "text-rose-500"}>
                                {deltas.totalTestCases >= 0 ? "+" : ""}{deltas.totalTestCases}
                            </span>
                            <span className="text-muted-foreground">vs previous period</span>
                        </div>
                    )}
                </div>

                <div className="surface-card p-5">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground font-medium">Average Pass Rate</p>
                            <p className="text-2xl font-bold mt-1">
                                {(stats.avgPassRate * 100).toFixed(1)}%
                            </p>
                        </div>
                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                            <Activity className="w-5 h-5" />
                        </div>
                    </div>
                    {deltas && (
                        <div className="mt-3 flex items-center gap-2 text-xs">
                            {deltas.avgPassRate >= 0 ? (
                                <TrendingUp className="w-3 h-3 text-emerald-500" />
                            ) : (
                                <TrendingDown className="w-3 h-3 text-rose-500" />
                            )}
                            <span className={deltas.avgPassRate >= 0 ? "text-emerald-500" : "text-rose-500"}>
                                {formatDelta(deltas.avgPassRate * 100, "%")}
                            </span>
                            <span className="text-muted-foreground">vs previous period</span>
                        </div>
                    )}
                </div>

                <div className="surface-card p-5">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground font-medium">Total Cost</p>
                            <p className="text-2xl font-bold mt-1">
                                ${stats.totalCost.toFixed(2)}
                            </p>
                        </div>
                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                            <DollarSign className="w-5 h-5" />
                        </div>
                    </div>
                    {deltas && (
                        <div className="mt-3 flex items-center gap-2 text-xs">
                            {deltas.totalCost >= 0 ? (
                                <TrendingUp className="w-3 h-3 text-emerald-500" />
                            ) : (
                                <TrendingDown className="w-3 h-3 text-rose-500" />
                            )}
                            <span className={deltas.totalCost >= 0 ? "text-emerald-500" : "text-rose-500"}>
                                {(deltas.totalCost > 0 ? "+" : deltas.totalCost < 0 ? "-" : "")}
                                ${Math.abs(deltas.totalCost).toFixed(2)}
                            </span>
                            <span className="text-muted-foreground">vs previous period</span>
                        </div>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-10">
                <div className="chart-panel p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h2 className="section-title">Pass Rate Trend</h2>
                            <p className="text-sm text-muted-foreground">
                                Weighted by test cases per day
                            </p>
                        </div>
                    </div>
                    <div className="h-72">
                        {passRateSeries.length === 0 ? (
                            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                                No data for the selected filters.
                            </div>
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={passRateSeries} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="passRateGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.2} />
                                            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                                    <XAxis
                                        dataKey="date"
                                        stroke="#94A3B8"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={formatShortDate}
                                    />
                                    <YAxis
                                        stroke="#94A3B8"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        domain={[0, 100]}
                                        tickFormatter={(value) => `${value}%`}
                                    />
                                    <Tooltip
                                        formatter={(value: number | undefined) =>
                                            value == null ? "-" : `${value.toFixed(1)}%`
                                        }
                                        labelFormatter={(label) => `Date: ${label}`}
                                        contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="passRate"
                                        stroke="#3B82F6"
                                        strokeWidth={2}
                                        fill="url(#passRateGradient)"
                                        name="Pass Rate"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>

                <div className="chart-panel p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h2 className="section-title">Metric Trend</h2>
                            <p className="text-sm text-muted-foreground">
                                Track average metric scores over time
                            </p>
                        </div>
                    </div>
                    <div className="flex flex-wrap gap-2 mb-4">
                        {availableMetrics.length === 0 && (
                            <span className="text-xs text-muted-foreground">No metric data available.</span>
                        )}
                        {availableMetrics.map((metric) => {
                            const isSelected = selectedMetrics.includes(metric);
                            return (
                                <button
                                    key={metric}
                                    type="button"
                                    onClick={() => toggleMetricSelection(metric)}
                                    className={`filter-chip ${isSelected
                                        ? "filter-chip-active"
                                        : "filter-chip-inactive"
                                        }`}
                                >
                                    {metric}
                                </button>
                            );
                        })}
                    </div>
                    <div className="h-72">
                        {metricSeries.length === 0 || selectedMetrics.length === 0 ? (
                            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                                Select metrics to display trend lines.
                            </div>
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={metricSeries} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                                    <XAxis
                                        dataKey="date"
                                        stroke="#94A3B8"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={formatShortDate}
                                    />
                                    <YAxis
                                        stroke="#94A3B8"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        domain={[0, 100]}
                                        tickFormatter={(value) => `${value}%`}
                                    />
                                    <Tooltip
                                        formatter={(value: number | undefined) =>
                                            value == null ? "-" : `${value.toFixed(1)}%`
                                        }
                                        labelFormatter={(label) => `Date: ${label}`}
                                        contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }}
                                    />
                                    <Legend />
                                    {selectedMetrics.map((metric, index) => (
                                        <Line
                                            key={metric}
                                            type="monotone"
                                            dataKey={metric}
                                            stroke={CHART_METRIC_COLORS[index % CHART_METRIC_COLORS.length]}
                                            strokeWidth={2}
                                            dot={false}
                                            connectNulls
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>
            </div>

            {filteredRuns.length === 0 ? (
                <div className="text-sm text-muted-foreground pb-20">
                    No runs found for the selected filters.
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pb-20">
                    {filteredRuns.map((run) => {
                        const isSelected = selectedRuns.has(run.run_id);
                        const project = run.project_name || "Unassigned";
                        const thresholdProfileLabel = formatThresholdProfileLabel(run.threshold_profile);
                        return (
                            <div
                                key={run.run_id}
                                onClick={() => navigate(`/runs/${run.run_id}`)}
                                className={`group relative bg-card hover:bg-card/80 border rounded-2xl p-6 transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1 cursor-pointer overflow-hidden ${isSelected ? "border-primary ring-1 ring-primary" : "border-border/60 hover:border-primary/30"}`}
                            >
                                <div
                                    onClick={(event) => toggleRunSelection(run.run_id, event)}
                                    className={`absolute top-4 right-4 z-10 w-6 h-6 rounded-md border flex items-center justify-center transition-all ${isSelected ? "bg-primary border-primary" : "bg-secondary/50 border-border hover:border-primary/50"}`}
                                >
                                    {isSelected && (
                                        <ArrowUpRight className="w-4 h-4 text-primary-foreground transform rotate-0" />
                                    )}
                                </div>

                                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                                <div className="flex items-start justify-between mb-5">
                                    <div className="space-y-1.5">
                                        <div className="flex items-center gap-2">
                                            <Database className="w-3.5 h-3.5 text-muted-foreground" />
                                            <h3 className="font-semibold text-lg tracking-tight group-hover:text-primary transition-colors">
                                                {run.dataset_name}
                                            </h3>
                                        </div>
                                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                            <span className="px-2 py-0.5 rounded-full bg-secondary/80 border border-border">
                                                {project}
                                            </span>
                                            <span className="px-2 py-0.5 rounded-full bg-secondary/80 border border-border">
                                                Threshold: {thresholdProfileLabel}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                            <Cpu className="w-3.5 h-3.5" />
                                            <span className="font-mono text-xs">{run.model_name}</span>
                                        </div>
                                    </div>

                                    <div
                                        className={`flex flex-col items-center justify-center w-14 h-14 rounded-2xl border ${getPassRateColor(run.pass_rate)} shadow-sm transition-transform group-hover:scale-105`}
                                    >
                                        <span className="text-sm font-bold">
                                            {(run.pass_rate * 100).toFixed(0)}
                                            <span className="text-[10px]">%</span>
                                        </span>
                                    </div>
                                </div>

                                <div className="space-y-3 mb-5">
                                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                                        <span>Performance</span>
                                        <span>{run.passed_test_cases}/{run.total_test_cases} passed</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full ${run.pass_rate >= 0.7 ? "bg-emerald-500" : "bg-rose-500"}`}
                                            style={{ width: `${run.pass_rate * 100}%` }}
                                        />
                                    </div>

                                    <div className="flex flex-wrap gap-1.5 mt-3">
                                        {run.metrics_evaluated.slice(0, 3).map((metric) => (
                                            <span
                                                key={metric}
                                                className="px-2 py-1 rounded-md bg-secondary border border-border text-[10px] text-muted-foreground font-mono"
                                            >
                                                {metric}
                                            </span>
                                        ))}
                                        {run.metrics_evaluated.length > 3 && (
                                            <span className="px-2 py-1 rounded-md bg-secondary border border-border text-[10px] text-muted-foreground font-mono">
                                                +{run.metrics_evaluated.length - 3}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                <div className="flex items-center justify-between pt-4 border-t border-border/50">
                                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                        <Clock className="w-3.5 h-3.5" />
                                        <span>{new Date(run.started_at).toLocaleDateString()}</span>
                                        {run.finished_at && (
                                            <span className="opacity-50">
                                                {" | "}
                                                {new Date(run.finished_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {selectedRuns.size > 0 && (
                <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 bg-foreground text-background px-6 py-3 rounded-full shadow-xl flex items-center gap-4 animate-in slide-in-from-bottom-4 duration-200 z-50">
                    <span className="font-medium text-sm">{selectedRuns.size} runs selected</span>
                    <div className="h-4 w-px bg-background/20" />
                    <button
                        onClick={() => setSelectedRuns(new Set())}
                        className="text-xs uppercase tracking-wide text-background/80 hover:text-background transition-colors"
                    >
                        Clear
                    </button>
                    <button
                        disabled={selectedRuns.size !== 2}
                        onClick={handleCompare}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${selectedRuns.size === 2
                            ? "bg-primary text-primary-foreground hover:bg-primary/90"
                            : "bg-background/20 text-background/50 cursor-not-allowed"}`}
                    >
                        Compare
                    </button>
                </div>
            )}
        </Layout>
    );
}
