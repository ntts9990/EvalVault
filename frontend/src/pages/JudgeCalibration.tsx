import { useEffect, useMemo, useState } from "react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    ComposedChart,
    Legend,
    Line,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import {
    fetchJudgeCalibrationHistory,
    fetchRuns,
    runJudgeCalibration,
    type JudgeCalibrationCase,
    type JudgeCalibrationHistoryItem,
    type JudgeCalibrationResponse,
    type RunSummary,
} from "../services/api";
import { Layout } from "../components/Layout";
import {
    CheckCircle2,
    ChevronLeft,
    ChevronRight,
    FileText,
    Loader2,
    Play,
    XCircle,
} from "lucide-react";

const LABEL_OPTIONS = [
    { value: "feedback", label: "Feedback" },
    { value: "hybrid", label: "Hybrid" },
    { value: "gold", label: "Gold" },
];

const METHOD_OPTIONS = [
    { value: "isotonic", label: "Isotonic" },
    { value: "platt", label: "Platt" },
    { value: "temperature", label: "Temperature" },
    { value: "none", label: "None" },
];

const RUN_PAGE_SIZE = 50;

interface CalibrationBin {
    prob: number;
    trueProb: number;
    count: number;
}

interface HistogramBin {
    range: string;
    raw: number;
    calibrated: number;
}

function calculateCalibrationCurve(cases: JudgeCalibrationCase[], bins = 10): CalibrationBin[] {
    const validCases = cases.filter((c) => c.label !== null && c.label !== undefined);
    if (validCases.length === 0) return [];

    const sorted = [...validCases].sort((a, b) => a.calibrated_score - b.calibrated_score);
    const binSize = 1 / bins;
    const result: CalibrationBin[] = [];

    for (let i = 0; i < bins; i++) {
        const min = i * binSize;
        const max = (i + 1) * binSize;
        const binCases = sorted.filter(
            (c) =>
                c.calibrated_score >= min &&
                (i === bins - 1 ? c.calibrated_score <= max : c.calibrated_score < max)
        );

        if (binCases.length > 0) {
            const avgPred = binCases.reduce((sum, c) => sum + c.calibrated_score, 0) / binCases.length;
            const avgTrue = binCases.reduce((sum, c) => sum + (c.label || 0), 0) / binCases.length;
            result.push({ prob: avgPred, trueProb: avgTrue, count: binCases.length });
        }
    }
    return result;
}

function calculateHistograms(cases: JudgeCalibrationCase[], bins = 20): HistogramBin[] {
    const binSize = 1 / bins;
    const result: HistogramBin[] = [];

    for (let i = 0; i < bins; i++) {
        const min = i * binSize;
        const max = (i + 1) * binSize;
        const range = `${min.toFixed(2)}-${max.toFixed(2)}`;

        const rawCount = cases.filter(
            (c) =>
                c.raw_score >= min &&
                (i === bins - 1 ? c.raw_score <= max : c.raw_score < max)
        ).length;

        const calCount = cases.filter(
            (c) =>
                c.calibrated_score >= min &&
                (i === bins - 1 ? c.calibrated_score <= max : c.calibrated_score < max)
        ).length;

        result.push({ range, raw: rawCount, calibrated: calCount });
    }
    return result;
}

export function JudgeCalibration() {
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [history, setHistory] = useState<JudgeCalibrationHistoryItem[]>([]);
    const [selectedRunId, setSelectedRunId] = useState<string>("");
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
    const [labelsSource, setLabelsSource] = useState("feedback");
    const [method, setMethod] = useState("isotonic");
    const [holdoutRatio, setHoldoutRatio] = useState(0.2);
    const [seed, setSeed] = useState(42);
    const [parallel, setParallel] = useState(false);
    const [concurrency, setConcurrency] = useState(8);
    const [result, setResult] = useState<JudgeCalibrationResponse | null>(null);
    const [selectedMetricKey, setSelectedMetricKey] = useState<string>("");
    const [loading, setLoading] = useState(true);
    const [loadingMoreRuns, setLoadingMoreRuns] = useState(false);
    const [hasMoreRuns, setHasMoreRuns] = useState(false);
    const [running, setRunning] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const pageSize = 50;

    useEffect(() => {
        let active = true;
        async function loadRunsPage(offset: number) {
            return fetchRuns({ includeFeedback: true, limit: RUN_PAGE_SIZE, offset });
        }
        async function load() {
            setLoading(true);
            setError(null);
            try {
                const [runList, historyList] = await Promise.all([
                    loadRunsPage(0),
                    fetchJudgeCalibrationHistory(20),
                ]);
                if (!active) return;
                setRuns(runList);
                setHasMoreRuns(runList.length === RUN_PAGE_SIZE);
                setHistory(historyList);
            } catch (err) {
                if (!active) return;
                setError(err instanceof Error ? err.message : "Failed to load data");
            } finally {
                if (active) setLoading(false);
            }
        }
        load();
        return () => {
            active = false;
        };
    }, []);

    const handleLoadMoreRuns = async () => {
        if (loadingMoreRuns || !hasMoreRuns) return;
        setLoadingMoreRuns(true);
        try {
            const nextRuns = await fetchRuns({
                includeFeedback: true,
                limit: RUN_PAGE_SIZE,
                offset: runs.length,
            });
            setRuns((prev) => [...prev, ...nextRuns]);
            setHasMoreRuns(nextRuns.length === RUN_PAGE_SIZE);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load runs");
        } finally {
            setLoadingMoreRuns(false);
        }
    };

    useEffect(() => {
        if (!selectedRunId) {
            setSelectedMetrics([]);
            return;
        }
        const run = runs.find((item) => item.run_id === selectedRunId);
        if (run?.metrics_evaluated?.length) {
            setSelectedMetrics(run.metrics_evaluated);
        }
    }, [selectedRunId, runs]);

    useEffect(() => {
        if (!result) return;
        const keys = Object.keys(result.case_results || {});
        if (keys.length && !keys.includes(selectedMetricKey)) {
            setSelectedMetricKey(keys[0]);
        }
    }, [result, selectedMetricKey]);

    const availableMetrics = useMemo(() => {
        const run = runs.find((item) => item.run_id === selectedRunId);
        return run?.metrics_evaluated || [];
    }, [runs, selectedRunId]);

    const requiresFeedback = labelsSource === "feedback" || labelsSource === "hybrid";
    const labelsSupported = labelsSource !== "gold";
    const eligibleRuns = useMemo(() => {
        if (!labelsSupported) return [];
        if (!requiresFeedback) return runs;
        return runs.filter((run) => (run.feedback_count ?? 0) > 0);
    }, [runs, requiresFeedback, labelsSupported]);

    useEffect(() => {
        if (!selectedRunId) return;
        if (!eligibleRuns.some((run) => run.run_id === selectedRunId)) {
            setSelectedRunId("");
        }
    }, [eligibleRuns, selectedRunId]);

    const caseRows = useMemo(() => {
        if (!result || !selectedMetricKey) return [];
        return result.case_results[selectedMetricKey] || [];
    }, [result, selectedMetricKey]);

    const paginatedCaseRows = useMemo(() => {
        const start = (page - 1) * pageSize;
        return caseRows.slice(start, start + pageSize);
    }, [caseRows, page]);

    const totalPages = Math.ceil(caseRows.length / pageSize);

    const calibrationData = useMemo(() => {
        return calculateCalibrationCurve(caseRows);
    }, [caseRows]);

    const histogramData = useMemo(() => {
        return calculateHistograms(caseRows);
    }, [caseRows]);

    const handleMetricToggle = (metric: string) => {
        setSelectedMetrics((prev) =>
            prev.includes(metric) ? prev.filter((item) => item !== metric) : [...prev, metric]
        );
    };

    const handleRunCalibration = async () => {
        if (!selectedRunId) {
            setError("Run을 선택하세요.");
            return;
        }
        setRunning(true);
        setError(null);
        try {
            const payload = await runJudgeCalibration({
                run_id: selectedRunId,
                labels_source: labelsSource as "feedback" | "gold" | "hybrid",
                method: method as "platt" | "isotonic" | "temperature" | "none",
                metrics: selectedMetrics.length ? selectedMetrics : undefined,
                holdout_ratio: holdoutRatio,
                seed,
                parallel,
                concurrency,
            });
            setResult(payload);
            const updatedHistory = await fetchJudgeCalibrationHistory(20);
            setHistory(updatedHistory);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Calibration failed");
        } finally {
            setRunning(false);
        }
    };

    if (loading) {
        return (
            <Layout>
                <div className="flex items-center justify-center h-[60vh] text-muted-foreground">
                    <Loader2 className="w-6 h-6 animate-spin" />
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="space-y-6">
                <div className="space-y-1">
                    <p className="section-kicker">Calibration</p>
                    <h1 className="text-2xl font-semibold">Judge Calibration</h1>
                    <p className="text-sm text-muted-foreground">
                        Judge 보정 실행과 결과를 한 번에 확인하세요.
                    </p>
                </div>

                {error && (
                    <div className="surface-panel border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
                        {error}
                    </div>
                )}

                <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
                    <div className="space-y-6">
                        <div className="surface-panel p-5 space-y-4">
                            <div className="flex items-center justify-between">
                                <h2 className="section-title">설정</h2>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs font-semibold uppercase text-muted-foreground">Labels</label>
                                    <select
                                        className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                                        value={labelsSource}
                                        onChange={(event) => setLabelsSource(event.target.value)}
                                    >
                                        {LABEL_OPTIONS.map((option) => (
                                            <option key={option.value} value={option.value}>
                                                {option.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-semibold uppercase text-muted-foreground">Method</label>
                                    <select
                                        className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                                        value={method}
                                        onChange={(event) => setMethod(event.target.value)}
                                    >
                                        {METHOD_OPTIONS.map((option) => (
                                            <option key={option.value} value={option.value}>
                                                {option.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            {!labelsSupported && (
                                <p className="text-xs text-amber-600">
                                    Gold 라벨 보정은 아직 지원되지 않습니다.
                                </p>
                            )}
                            {labelsSupported && requiresFeedback && eligibleRuns.length === 0 && (
                                <p className="text-xs text-amber-600">
                                    {hasMoreRuns
                                        ? "피드백 라벨이 있는 run이 없습니다. 더 보기로 확인하거나 피드백을 남겨주세요."
                                        : "피드백 라벨이 있는 run이 없습니다. 먼저 피드백을 남겨주세요."}
                                </p>
                            )}
                            <div className="space-y-3">
                                <label className="text-xs font-semibold uppercase text-muted-foreground">Run 선택</label>
                                <select
                                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                                    value={selectedRunId}
                                    onChange={(event) => setSelectedRunId(event.target.value)}
                                    disabled={!labelsSupported || (requiresFeedback && eligibleRuns.length === 0)}
                                >
                                    <option value="">Run을 선택하세요</option>
                                    {eligibleRuns.map((run) => (
                                        <option key={run.run_id} value={run.run_id}>
                                            {run.dataset_name} · {run.run_id.slice(0, 8)}
                                        </option>
                                    ))}
                                </select>
                                <div className="flex items-center justify-between text-xs text-muted-foreground">
                                    <span>
                                        {requiresFeedback
                                            ? `피드백 있는 run ${eligibleRuns.length}건 표시 중`
                                            : `전체 run ${eligibleRuns.length}건 표시 중`}
                                    </span>
                                    <button
                                        type="button"
                                        onClick={handleLoadMoreRuns}
                                        disabled={loadingMoreRuns || !hasMoreRuns}
                                        className="text-primary disabled:text-muted-foreground"
                                    >
                                        {loadingMoreRuns ? "불러오는 중..." : hasMoreRuns ? "더 보기" : "마지막"}
                                    </button>
                                </div>
                            </div>

                            <div>
                                <label className="text-xs font-semibold uppercase text-muted-foreground">Metrics</label>
                                <div className="mt-2 flex flex-wrap gap-2">
                                    {availableMetrics.length === 0 && (
                                        <span className="text-xs text-muted-foreground">Run 선택 후 표시됩니다.</span>
                                    )}
                                    {availableMetrics.map((metric) => {
                                        const active = selectedMetrics.includes(metric);
                                        return (
                                            <button
                                                key={metric}
                                                type="button"
                                                className={`filter-chip ${active ? "filter-chip-active" : "filter-chip-inactive"}`}
                                                onClick={() => handleMetricToggle(metric)}
                                            >
                                                {metric}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs font-semibold uppercase text-muted-foreground">Holdout</label>
                                    <input
                                        type="number"
                                        min={0.05}
                                        max={0.95}
                                        step={0.05}
                                        className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                                        value={holdoutRatio}
                                        onChange={(event) => setHoldoutRatio(Number(event.target.value))}
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-semibold uppercase text-muted-foreground">Seed</label>
                                    <input
                                        type="number"
                                        min={0}
                                        className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                                        value={seed}
                                        onChange={(event) => setSeed(Number(event.target.value))}
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <label className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <input
                                        type="checkbox"
                                        checked={parallel}
                                        onChange={(event) => setParallel(event.target.checked)}
                                    />
                                    병렬 실행
                                </label>
                                <div>
                                    <label className="text-xs font-semibold uppercase text-muted-foreground">Concurrency</label>
                                    <input
                                        type="number"
                                        min={1}
                                        className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                                        value={concurrency}
                                        onChange={(event) => setConcurrency(Number(event.target.value))}
                                    />
                                </div>
                            </div>

                            <button
                                className="w-full rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground flex items-center justify-center gap-2 disabled:opacity-60"
                                onClick={handleRunCalibration}
                                disabled={
                                    running ||
                                    !selectedRunId ||
                                    !labelsSupported ||
                                    (requiresFeedback && eligibleRuns.length === 0)
                                }
                            >
                                {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                                Judge 보정 실행
                            </button>
                        </div>

                        <div className="surface-panel p-5 space-y-4">
                            <h2 className="section-title">히스토리</h2>
                            <div className="space-y-3 text-sm">
                                {history.length === 0 && (
                                    <p className="text-muted-foreground">아직 실행 기록이 없습니다.</p>
                                )}
                                {history.map((item) => (
                                    <div
                                        key={item.calibration_id}
                                        className="flex items-start justify-between gap-3 rounded-lg border border-border/60 p-3"
                                    >
                                        <div>
                                            <p className="font-medium">{item.run_id.slice(0, 8)}</p>
                                            <p className="text-xs text-muted-foreground">
                                                {item.created_at}
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                {item.metrics.join(", ") || "metrics 없음"}
                                            </p>
                                        </div>
                                        <span
                                            className={`text-xs font-semibold ${item.gate_passed ? "text-emerald-600" : "text-amber-600"}`}
                                        >
                                            {item.gate_passed ? "PASSED" : "DEGRADED"}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div className="surface-panel p-5 space-y-4">
                            <div className="flex items-center justify-between">
                                <h2 className="section-title">결과 요약</h2>
                                {result && (
                                    <span
                                        className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${result.summary.gate_passed
                                                ? "bg-emerald-100 text-emerald-700"
                                                : "bg-amber-100 text-amber-700"
                                            }`}
                                    >
                                        {result.summary.gate_passed ? (
                                            <CheckCircle2 className="w-3.5 h-3.5" />
                                        ) : (
                                            <XCircle className="w-3.5 h-3.5" />
                                        )}
                                        {result.summary.gate_passed ? "PASSED" : "DEGRADED"}
                                    </span>
                                )}
                            </div>
                            {!result && <p className="text-sm text-muted-foreground">아직 실행된 결과가 없습니다.</p>}
                            {result && (
                                <div className="grid gap-4 md:grid-cols-3">
                                    <div className="surface-subtle p-3">
                                        <p className="text-xs text-muted-foreground">Labels</p>
                                        <p className="font-semibold">{result.summary.total_labels}</p>
                                    </div>
                                    <div className="surface-subtle p-3">
                                        <p className="text-xs text-muted-foreground">Samples</p>
                                        <p className="font-semibold">{result.summary.total_samples}</p>
                                    </div>
                                    <div className="surface-subtle p-3">
                                        <p className="text-xs text-muted-foreground">Method</p>
                                        <p className="font-semibold">{result.summary.method}</p>
                                    </div>
                                    <div className="surface-subtle p-3">
                                        <p className="text-xs text-muted-foreground">Holdout</p>
                                        <p className="font-semibold">{result.summary.holdout_ratio}</p>
                                    </div>
                                    <div className="surface-subtle p-3">
                                        <p className="text-xs text-muted-foreground">Seed</p>
                                        <p className="font-semibold">{result.summary.seed}</p>
                                    </div>
                                    <div className="surface-subtle p-3">
                                        <p className="text-xs text-muted-foreground">Duration</p>
                                        <p className="font-semibold">{result.duration_ms}ms</p>
                                    </div>
                                </div>
                            )}
                            {result?.warnings?.length ? (
                                <div className="rounded-lg border border-amber-300/50 bg-amber-50/70 p-3 text-xs text-amber-700">
                                    {result.warnings.map((warning) => (
                                        <p key={warning}>• {warning}</p>
                                    ))}
                                </div>
                            ) : null}
                        </div>

                        {result && (
                            <div className="surface-panel p-5 space-y-4">
                                <h2 className="section-title">Visualizations</h2>
                                <div className="grid gap-6 md:grid-cols-2">
                                    <div className="space-y-2">
                                        <h3 className="text-sm font-medium text-muted-foreground">Calibration Curve</h3>
                                        <div className="h-[300px] w-full">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <ComposedChart
                                                    data={calibrationData}
                                                    margin={{ top: 10, right: 10, bottom: 20, left: 10 }}
                                                >
                                                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                                    <XAxis
                                                        dataKey="prob"
                                                        type="number"
                                                        domain={[0, 1]}
                                                        label={{
                                                            value: "Predicted Probability",
                                                            position: "insideBottom",
                                                            offset: -10,
                                                            fontSize: 12,
                                                        }}
                                                    />
                                                    <YAxis
                                                        type="number"
                                                        domain={[0, 1]}
                                                        label={{
                                                            value: "True Probability",
                                                            angle: -90,
                                                            position: "insideLeft",
                                                            fontSize: 12,
                                                        }}
                                                    />
                                                    <Tooltip
                                                        contentStyle={{
                                                            backgroundColor: "hsl(var(--card))",
                                                            borderColor: "hsl(var(--border))",
                                                            borderRadius: "0.5rem",
                                                            fontSize: "0.75rem",
                                                        }}
                                                    />
                                                    <Legend wrapperStyle={{ fontSize: "0.75rem" }} />
                                                    <Line
                                                        type="monotone"
                                                        dataKey="prob"
                                                        stroke="#94a3b8"
                                                        dot={false}
                                                        strokeDasharray="5 5"
                                                        name="Ideal"
                                                    />
                                                    <Line
                                                        type="monotone"
                                                        dataKey="trueProb"
                                                        stroke="#2563eb"
                                                        strokeWidth={2}
                                                        name="Actual"
                                                    />
                                                </ComposedChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <h3 className="text-sm font-medium text-muted-foreground">Score Distribution</h3>
                                        <div className="h-[300px] w-full">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart
                                                    data={histogramData}
                                                    margin={{ top: 10, right: 10, bottom: 20, left: 10 }}
                                                >
                                                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                                    <XAxis
                                                        dataKey="range"
                                                        angle={-45}
                                                        textAnchor="end"
                                                        height={60}
                                                        interval={0}
                                                        fontSize={10}
                                                    />
                                                    <YAxis fontSize={10} />
                                                    <Tooltip
                                                        contentStyle={{
                                                            backgroundColor: "hsl(var(--card))",
                                                            borderColor: "hsl(var(--border))",
                                                            borderRadius: "0.5rem",
                                                            fontSize: "0.75rem",
                                                        }}
                                                    />
                                                    <Legend wrapperStyle={{ fontSize: "0.75rem" }} />
                                                    <Bar dataKey="raw" fill="#94a3b8" name="Raw" opacity={0.6} />
                                                    <Bar
                                                        dataKey="calibrated"
                                                        fill="#2563eb"
                                                        name="Calibrated"
                                                        opacity={0.8}
                                                    />
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {result && result.artifacts && Object.keys(result.artifacts).length > 0 && (
                            <div className="surface-panel p-5 space-y-3">
                                <h2 className="section-title">Artifacts</h2>
                                <div className="grid gap-2">
                                    {Object.entries(result.artifacts).map(([name, path]) => (
                                        <div
                                            key={name}
                                            className="flex items-center justify-between rounded-lg border border-border/60 p-3 text-sm"
                                        >
                                            <div className="flex items-center gap-3">
                                                <FileText className="h-4 w-4 text-muted-foreground" />
                                                <span className="font-medium">{name}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs text-muted-foreground truncate max-w-[300px]">
                                                    {path}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="surface-panel p-5 space-y-3">
                            <h2 className="section-title">Metric 결과</h2>
                            {result ? (
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="text-xs text-muted-foreground">
                                            <tr>
                                                <th className="text-left py-2">Metric</th>
                                                <th className="text-right">MAE</th>
                                                <th className="text-right">Pearson</th>
                                                <th className="text-right">Spearman</th>
                                                <th className="text-center">Gate</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {result.metrics.map((metric) => (
                                                <tr key={metric.metric} className="border-t border-border/60">
                                                    <td className="py-2 font-medium">{metric.metric}</td>
                                                    <td className="text-right">{metric.mae ?? "-"}</td>
                                                    <td className="text-right">{metric.pearson ?? "-"}</td>
                                                    <td className="text-right">{metric.spearman ?? "-"}</td>
                                                    <td className="text-center">
                                                        {metric.gate_passed === undefined || metric.gate_passed === null
                                                            ? "-"
                                                            : metric.gate_passed
                                                                ? "✅"
                                                                : "⚠️"}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <p className="text-sm text-muted-foreground">결과가 없습니다.</p>
                            )}
                        </div>

                        <div className="surface-panel p-5 space-y-3">
                            <h2 className="section-title">Case 결과</h2>
                            {!result && <p className="text-sm text-muted-foreground">보정 결과가 없습니다.</p>}
                            {result && (
                                <div className="space-y-3">
                                    <div className="flex items-center gap-3">
                                        <label className="text-xs font-semibold uppercase text-muted-foreground">
                                            Metric 선택
                                        </label>
                                        <select
                                            className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
                                            value={selectedMetricKey}
                                            onChange={(event) => {
                                                setSelectedMetricKey(event.target.value);
                                                setPage(1);
                                            }}
                                        >
                                            {Object.keys(result.case_results).map((metricKey) => (
                                                <option key={metricKey} value={metricKey}>
                                                    {metricKey}
                                                </option>
                                            ))}
                                        </select>
                                        <span className="text-xs text-muted-foreground">
                                            Total {caseRows.length} cases
                                        </span>
                                    </div>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead className="text-xs text-muted-foreground">
                                                <tr>
                                                    <th className="text-left py-2">Case</th>
                                                    <th className="text-right">Raw</th>
                                                    <th className="text-right">Calibrated</th>
                                                    <th className="text-right">Label</th>
                                                    <th className="text-right">Source</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {paginatedCaseRows.map((item) => (
                                                    <tr key={item.test_case_id} className="border-t border-border/60">
                                                        <td className="py-2 font-medium">{item.test_case_id}</td>
                                                        <td className="text-right">{item.raw_score.toFixed(3)}</td>
                                                        <td className="text-right">{item.calibrated_score.toFixed(3)}</td>
                                                        <td className="text-right">{item.label ?? "-"}</td>
                                                        <td className="text-right">{item.label_source ?? "-"}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>

                                    {totalPages > 1 && (
                                        <div className="flex items-center justify-between border-t border-border/60 pt-3">
                                            <div className="text-xs text-muted-foreground">
                                                Page {page} of {totalPages}
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    className="p-1 rounded hover:bg-muted disabled:opacity-50"
                                                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                                                    disabled={page === 1}
                                                >
                                                    <ChevronLeft className="h-4 w-4" />
                                                </button>
                                                <button
                                                    className="p-1 rounded hover:bg-muted disabled:opacity-50"
                                                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                                                    disabled={page === totalPages}
                                                >
                                                    <ChevronRight className="h-4 w-4" />
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    );
}
