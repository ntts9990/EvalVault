import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import {
    fetchAnalysisHistory,
    fetchPromptDiff,
    fetchRuns,
    type AnalysisHistoryItem,
    type PromptDiffResponse,
    type RunSummary,
} from "../services/api";
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
    resolveDateRange,
    toDateInputValue,
    type DateRangePreset,
} from "../utils/runAnalytics";
import {
    CHART_METRIC_COLORS,
    CUSTOM_RANGE_DEFAULT_DAYS,
    DATE_RANGE_OPTIONS,
    DEFAULT_DATE_RANGE_PRESET,
} from "../config/ui";
import { copyTextToClipboard } from "../utils/clipboard";
import {
    Activity,
    AlertCircle,
    FileText,
    Printer,
    Share2,
    GitCompare,
    Download,
    Info,
    CheckCircle2,
    XCircle,
    AlertTriangle,
} from "lucide-react";

type MetricTrendRow = Record<string, number | string | null>;

function projectLabel(value: string) {
    if (value === PROJECT_ALL) return "All Projects";
    if (value === PROJECT_UNASSIGNED) return "Unassigned";
    return value;
}

export function CustomerReport() {
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    const [rangePreset, setRangePreset] = useState<DateRangePreset>(DEFAULT_DATE_RANGE_PRESET);
    const [customStart, setCustomStart] = useState(() => {
        const offset = -(CUSTOM_RANGE_DEFAULT_DAYS - 1);
        return toDateInputValue(addDays(new Date(), offset));
    });
    const [customEnd, setCustomEnd] = useState(() => toDateInputValue(new Date()));
    const [selectedProjects, setSelectedProjects] = useState<string[]>([PROJECT_ALL]);
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
    const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistoryItem[]>([]);
    const [analysisHistoryError, setAnalysisHistoryError] = useState<string | null>(null);
    const [promptDiff, setPromptDiff] = useState<PromptDiffResponse | null>(null);
    const [diffLoading, setDiffLoading] = useState(false);
    const [diffError, setDiffError] = useState<string | null>(null);

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

    useEffect(() => {
        fetchAnalysisHistory(50)
            .then(setAnalysisHistory)
            .catch((err) => {
                setAnalysisHistoryError(
                    err instanceof Error ? err.message : "분석 이력을 불러오지 못했습니다."
                );
            });
    }, []);

    const projectOptions = useMemo(() => collectProjectNames(runs), [runs]);
    const dateRange = useMemo(
        () => resolveDateRange(rangePreset, customStart, customEnd),
        [rangePreset, customStart, customEnd]
    );

    const projectFilteredRuns = useMemo(
        () => filterRunsByProjects(runs, selectedProjects),
        [runs, selectedProjects]
    );
    const filteredRuns = useMemo(() => {
        const scoped = filterRunsByDate(projectFilteredRuns, dateRange.from, dateRange.to);
        return [...scoped].sort(
            (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
        );
    }, [projectFilteredRuns, dateRange.from, dateRange.to]);

    const stats = useMemo(() => computeStats(filteredRuns), [filteredRuns]);
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

    const analysisCompareLink = useMemo(() => {
        if (filteredRuns.length < 2) return null;
        const targetRunId = filteredRuns[0].run_id;
        const baseRunId = filteredRuns[1].run_id;
        const targetResult = analysisHistory.find(
            (item) => item.run_id === targetRunId && item.is_complete
        );
        const baseResult = analysisHistory.find(
            (item) => item.run_id === baseRunId && item.is_complete
        );
        if (!targetResult || !baseResult) return null;
        return `/analysis/compare?left=${encodeURIComponent(baseResult.result_id)}&right=${encodeURIComponent(
            targetResult.result_id
        )}`;
    }, [analysisHistory, filteredRuns]);

    useEffect(() => {
        if (filteredRuns.length < 2) {
            setPromptDiff(null);
            setDiffError(null);
            return;
        }

        const targetRun = filteredRuns[0];
        const baseRun = filteredRuns[1];

        if (
            promptDiff?.base_run_id === baseRun.run_id &&
            promptDiff?.target_run_id === targetRun.run_id
        ) {
            return;
        }

        async function loadDiff() {
            setDiffLoading(true);
            try {
                const data = await fetchPromptDiff(baseRun.run_id, targetRun.run_id);
                setPromptDiff(data);
                setDiffError(null);
            } catch (err) {
                console.error(err);
                setDiffError("프롬프트 변경 내역을 불러오지 못했습니다.");
            } finally {
                setDiffLoading(false);
            }
        }

        loadDiff();
    }, [filteredRuns, promptDiff?.base_run_id, promptDiff?.target_run_id]);

    const diffCounts = useMemo(() => {
        if (!promptDiff) return { same: 0, diff: 0, missing: 0 };
        return promptDiff.summary.reduce(
            (acc, item) => {
                acc[item.status] = (acc[item.status] || 0) + 1;
                return acc;
            },
            { same: 0, diff: 0, missing: 0 } as Record<string, number>
        );
    }, [promptDiff]);

    const handleDownloadDiff = () => {
        if (!promptDiff) return;
        const blob = new Blob([JSON.stringify(promptDiff, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `prompt-diff-${promptDiff.base_run_id}-${promptDiff.target_run_id}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
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

    const handleCopyLink = async () => {
        const success = await copyTextToClipboard(window.location.href);
        setCopied(success);
        setTimeout(() => setCopied(false), 1500);
    };

    if (loading) {
        return (
            <Layout>
                <div className="flex items-center justify-center h-[50vh]">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            </Layout>
        );
    }

    if (error) {
        return (
            <Layout>
                <div className="flex items-center justify-center min-h-[50vh]">
                    <div className="flex flex-col items-center gap-4 text-destructive p-8 rounded-2xl bg-destructive/5 border border-destructive/20 max-w-md text-center">
                        <AlertCircle className="w-12 h-12" />
                        <div>
                            <p className="text-xl font-bold tracking-tight">Report Error</p>
                            <p className="text-sm opacity-80 mt-1">{error}</p>
                        </div>
                    </div>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="max-w-6xl mx-auto pb-20">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight mb-2 font-display">Customer Report</h1>
                        <p className="text-muted-foreground">
                            Shareable performance summary for stakeholders.
                        </p>
                        <p className="text-xs text-muted-foreground mt-2">
                            Scope: {dateRange.label} | Projects: {selectedProjects.map(projectLabel).join(", ")}
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        <button
                            onClick={handleCopyLink}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-card text-sm hover:bg-secondary/40"
                        >
                            <Share2 className="w-4 h-4" />
                            {copied ? "Link copied" : "Copy link"}
                        </button>
                        <button
                            onClick={() => window.print()}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-card text-sm hover:bg-secondary/40"
                        >
                            <Printer className="w-4 h-4" />
                            Print / PDF
                        </button>
                    </div>
                </div>

                <div className="surface-card p-6 mb-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                            <p className="text-xs text-muted-foreground">
                                Active range: {dateRange.label}
                            </p>
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
                                Report reflects the selected project scope.
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
                                <FileText className="w-5 h-5" />
                            </div>
                        </div>
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
                    </div>
                    <div className="surface-card p-5">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground font-medium">Total Cost</p>
                                <p className="text-2xl font-bold mt-1">${stats.totalCost.toFixed(2)}</p>
                            </div>
                            <div className="p-2 bg-primary/10 rounded-lg text-primary">
                                <Activity className="w-5 h-5" />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="surface-card p-6 mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <GitCompare className="w-5 h-5 text-primary" />
                            <h2 className="text-lg font-semibold">최근 Run 2건 프롬프트 변경 요약</h2>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                            {filteredRuns.length >= 2 && (
                                <Link
                                    to={`/compare?base=${encodeURIComponent(filteredRuns[1].run_id)}&target=${encodeURIComponent(filteredRuns[0].run_id)}`}
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-border bg-background hover:bg-secondary/50 transition-colors"
                                >
                                    비교 상세 보기
                                </Link>
                            )}
                            {analysisCompareLink && (
                                <Link
                                    to={analysisCompareLink}
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-border bg-background hover:bg-secondary/50 transition-colors"
                                >
                                    <Activity className="w-3.5 h-3.5" />
                                    분석 결과 비교
                                </Link>
                            )}
                            {promptDiff && !diffLoading && (
                                <button
                                    onClick={handleDownloadDiff}
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-border bg-background hover:bg-secondary/50 transition-colors"
                                >
                                    <Download className="w-3.5 h-3.5" />
                                    상세 JSON 다운로드
                                </button>
                            )}
                            {analysisHistoryError && (
                                <div className="inline-flex items-center gap-1 px-2 py-1.5 text-xs text-muted-foreground opacity-70" title={analysisHistoryError}>
                                    <AlertCircle className="w-3 h-3" />
                                    <span className="truncate max-w-[120px]">{analysisHistoryError}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {filteredRuns.length < 2 ? (
                        <div className="flex items-center gap-2 text-muted-foreground text-sm p-2 bg-secondary/20 rounded-lg">
                            <Info className="w-4 h-4" />
                            <span>비교할 Run이 부족합니다. (현재 필터 기준 최소 2건 필요)</span>
                        </div>
                    ) : diffLoading ? (
                        <div className="flex items-center gap-3 text-sm text-muted-foreground animate-pulse">
                            <div className="w-4 h-4 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
                            <span>프롬프트 변경 내역 분석 중...</span>
                        </div>
                    ) : diffError ? (
                        <div className="flex items-center gap-2 text-destructive text-sm p-2 bg-destructive/10 rounded-lg border border-destructive/20">
                            <AlertTriangle className="w-4 h-4" />
                            <span>{diffError}</span>
                        </div>
                    ) : promptDiff ? (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="flex flex-col items-center justify-center p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                                <span className="text-xs text-muted-foreground font-medium uppercase mb-1 flex items-center gap-1">
                                    <CheckCircle2 className="w-3 h-3" /> 동일
                                </span>
                                <span className="text-2xl font-bold text-foreground">{diffCounts.same}</span>
                            </div>
                            <div className="flex flex-col items-center justify-center p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
                                <span className="text-xs text-muted-foreground font-medium uppercase mb-1 flex items-center gap-1">
                                    <GitCompare className="w-3 h-3" /> 변경
                                </span>
                                <span className="text-2xl font-bold text-foreground">{diffCounts.diff}</span>
                            </div>
                            <div className="flex flex-col items-center justify-center p-3 rounded-lg bg-rose-500/5 border border-rose-500/10">
                                <span className="text-xs text-muted-foreground font-medium uppercase mb-1 flex items-center gap-1">
                                    <XCircle className="w-3 h-3" /> 누락
                                </span>
                                <span className="text-2xl font-bold text-foreground">{diffCounts.missing}</span>
                            </div>
                        </div>
                    ) : null}

                    {promptDiff && filteredRuns.length >= 2 && (
                        <div className="mt-3 text-xs text-muted-foreground text-right">
                            비교 대상: <span className="font-mono">{filteredRuns[1].run_id.slice(0, 8)}</span> (Base)
                            vs <span className="font-mono">{filteredRuns[0].run_id.slice(0, 8)}</span> (Target)
                        </div>
                    )}
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-10">
                    <div className="chart-panel p-6">
                        <h2 className="section-title mb-2">Pass Rate Trend</h2>
                        <p className="text-sm text-muted-foreground mb-4">
                            Weighted by test cases per day
                        </p>
                        <div className="h-72">
                            {passRateSeries.length === 0 ? (
                                <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                                    No data for the selected filters.
                                </div>
                            ) : (
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={passRateSeries} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                                        <defs>
                                            <linearGradient id="customerPassRateGradient" x1="0" y1="0" x2="0" y2="1">
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
                                            fill="url(#customerPassRateGradient)"
                                            name="Pass Rate"
                                        />
                                    </AreaChart>
                                </ResponsiveContainer>
                            )}
                        </div>
                    </div>

                    <div className="chart-panel p-6">
                        <h2 className="section-title mb-2">Metric Trend</h2>
                        <p className="text-sm text-muted-foreground mb-4">
                            Track average metric scores over time
                        </p>
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

                <div className="surface-card p-6">
                    <h2 className="text-lg font-semibold mb-4">Recent Runs</h2>
                    {filteredRuns.length === 0 ? (
                        <div className="text-sm text-muted-foreground">
                            No runs available for the selected filters.
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="text-left text-muted-foreground border-b border-border/60">
                                        <th className="py-2">Date</th>
                                        <th className="py-2">Project</th>
                                        <th className="py-2">Dataset</th>
                                        <th className="py-2">Model</th>
                                        <th className="py-2">Threshold</th>
                                        <th className="py-2">Pass Rate</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredRuns.slice(0, 8).map((run) => (
                                        <tr key={run.run_id} className="border-b border-border/40">
                                            <td className="py-2">{new Date(run.started_at).toLocaleDateString()}</td>
                                            <td className="py-2">{run.project_name || "Unassigned"}</td>
                                            <td className="py-2">{run.dataset_name}</td>
                                            <td className="py-2">{run.model_name}</td>
                                            <td className="py-2">{run.threshold_profile ? run.threshold_profile.toUpperCase() : "Default"}</td>
                                            <td className="py-2">{(run.pass_rate * 100).toFixed(1)}%</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </Layout>
    );
}
