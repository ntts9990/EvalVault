import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import {
    fetchRunComparison,
    fetchPromptDiff,
    fetchStageMetrics,
    type PromptDiffResponse,
    type RunComparisonCounts,
    type RunDetailsResponse,
    type StageMetric,
} from "../services/api";
import { formatScore, normalizeScore, safeAverage } from "../utils/score";
import {
    ArrowLeft,
    CheckCircle2,
    XCircle,
    ArrowRight,
    TrendingUp,
    TrendingDown,
    PlusCircle,
    MinusCircle,
    Download,
    Eye,
    EyeOff,
    FileDiff,
    Terminal,
    AlertCircle
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";
import { buildCompareCommand } from "../utils/cliCommandBuilder";
import { copyTextToClipboard } from "../utils/clipboard";

export function CompareRuns() {
    const [searchParams] = useSearchParams();
    const baseId = searchParams.get("base");
    const targetId = searchParams.get("target");

    const [baseRun, setBaseRun] = useState<RunDetailsResponse | null>(null);
    const [targetRun, setTargetRun] = useState<RunDetailsResponse | null>(null);
    const [caseCounts, setCaseCounts] = useState<RunComparisonCounts | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [promptDiff, setPromptDiff] = useState<PromptDiffResponse | null>(null);
    const [diffLoading, setDiffLoading] = useState(false);
    const [diffError, setDiffError] = useState<string | null>(null);
    const [showDiff, setShowDiff] = useState(false);
    const [copyStatus, setCopyStatus] = useState<"idle" | "success" | "error">("idle");

    const [orderingWarningsBase, setOrderingWarningsBase] = useState<StageMetric[]>([]);
    const [orderingWarningsTarget, setOrderingWarningsTarget] = useState<StageMetric[]>([]);

    // View state
    const [filterMode, setFilterMode] = useState<"all" | "changes" | "regressions">("all");

    useEffect(() => {
        async function loadData() {
            if (!baseId || !targetId) {
                setError("Missing run IDs for comparison");
                setLoading(false);
                return;
            }

            try {
                const comparison = await fetchRunComparison(baseId, targetId);
                setBaseRun(comparison.base);
                setTargetRun(comparison.target);
                setCaseCounts(comparison.case_counts);
            } catch {
                setError("Failed to load runs for comparison");
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, [baseId, targetId]);

    useEffect(() => {
        if (!baseId || !targetId) return;
        setDiffLoading(true);
        setDiffError(null);
        fetchPromptDiff(baseId, targetId)
            .then(setPromptDiff)
            .catch((err) => {
                setDiffError(err instanceof Error ? err.message : "프롬프트 비교를 불러오지 못했습니다.");
            })
            .finally(() => setDiffLoading(false));

        Promise.all([
            fetchStageMetrics(baseId, undefined, "retrieval.ordering_warning"),
            fetchStageMetrics(targetId, undefined, "retrieval.ordering_warning")
        ]).then(([base, target]) => {
            setOrderingWarningsBase(base);
            setOrderingWarningsTarget(target);
        }).catch(err => console.error("Failed to fetch ordering warnings", err));
    }, [baseId, targetId]);

    if (loading) return (
        <Layout>
            <div className="flex items-center justify-center h-[50vh]">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        </Layout>
    );

    if (error || !baseRun || !targetRun) return (
        <Layout>
            <div className="flex flex-col items-center justify-center h-[50vh] text-destructive gap-4">
                <p className="text-xl font-bold">Comparison Error</p>
                <p>{error}</p>
                <Link to="/" className="text-primary hover:underline">Return to Dashboard</Link>
            </div>
        </Layout>
    );

    // --- Analysis Logic ---

    // 1. Calculate Metric Deltas
    const metricsSet = new Set([
        ...baseRun.summary.metrics_evaluated,
        ...targetRun.summary.metrics_evaluated
    ]);

    const getAvgMetric = (run: RunDetailsResponse, metricName: string) => {
        const scores = run.results.flatMap(
            r => r.metrics.filter(m => m.name === metricName).map(m => normalizeScore(m.score))
        );
        return safeAverage(scores);
    };

    const metricDeltas = Array.from(metricsSet).map(metric => {
        const baseScore = getAvgMetric(baseRun, metric);
        const targetScore = getAvgMetric(targetRun, metric);
        return {
            name: metric,
            base: baseScore,
            target: targetScore,
            delta: targetScore - baseScore
        };
    });

    // 2. Prepare Diff Table Rows
    // Match test cases by ID (or question if ID mapping is loose, but ID is best)
    const isPassed = (tc?: RunDetailsResponse["results"][number]) =>
        tc ? tc.metrics.every(m => m.passed) : false;

    const baseMap = new Map(baseRun.results.map(tc => [tc.test_case_id, tc]));
    const targetMap = new Map(targetRun.results.map(tc => [tc.test_case_id, tc]));
    const combinedResults: {
        id: string;
        question: string | null;
        baseAnswer: string | null;
        targetAnswer: string | null;
        status: "same_pass" | "same_fail" | "regression" | "improvement" | "removed" | "new";
        basePassed: boolean;
        targetPassed: boolean;
    }[] = [];

    for (const [caseId, baseCase] of baseMap.entries()) {
        const targetCase = targetMap.get(caseId);
        const basePassed = isPassed(baseCase);
        const targetPassed = isPassed(targetCase);

        let status: "same_pass" | "same_fail" | "regression" | "improvement" | "removed" | "new" = "same_pass";
        if (!targetCase) status = "removed";
        else if (basePassed && !targetPassed) status = "regression";
        else if (!basePassed && targetPassed) status = "improvement";
        else if (basePassed && targetPassed) status = "same_pass";
        else status = "same_fail";

        combinedResults.push({
            id: baseCase.test_case_id,
            question: baseCase.question,
            baseAnswer: baseCase.answer,
            targetAnswer: targetCase?.answer ?? "(N/A)",
            status,
            basePassed,
            targetPassed,
        });
    }

    for (const [caseId, targetCase] of targetMap.entries()) {
        if (baseMap.has(caseId)) continue;
        const targetPassed = isPassed(targetCase);
        combinedResults.push({
            id: targetCase.test_case_id,
            question: targetCase.question,
            baseAnswer: "(N/A)",
            targetAnswer: targetCase.answer,
            status: "new",
            basePassed: false,
            targetPassed,
        });
    }

    // Filter
    const computedCounts = combinedResults.reduce<RunComparisonCounts>(
        (acc, row) => {
            const statusKey: keyof RunComparisonCounts =
                row.status === "regression"
                    ? "regressions"
                    : row.status === "improvement"
                        ? "improvements"
                        : row.status;
            acc[statusKey] += 1;
            return acc;
        },
        {
            regressions: 0,
            improvements: 0,
            same_pass: 0,
            same_fail: 0,
            new: 0,
            removed: 0,
        }
    );
    const resolvedCounts = caseCounts ?? computedCounts;

    const visibleRows = combinedResults.filter((row) => {
        if (filterMode === "all") return true;
        if (filterMode === "regressions") return row.status === "regression";
        return row.status !== "same_pass" && row.status !== "same_fail";
    });

    const passRateDelta = targetRun.summary.pass_rate - baseRun.summary.pass_rate;

    const downloadPromptDiff = () => {
        if (!promptDiff || !baseId || !targetId) return;
        const blob = new Blob([JSON.stringify(promptDiff, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = `prompt_diff_${baseId}_${targetId}.json`;
        anchor.click();
        URL.revokeObjectURL(url);
    };

    const handleCopyCli = async () => {
        if (!baseId || !targetId) return;
        const command = buildCompareCommand({
            base_run_id: baseId,
            target_run_id: targetId,
        });
        const success = await copyTextToClipboard(command);
        setCopyStatus(success ? "success" : "error");
        setTimeout(() => setCopyStatus("idle"), 1500);
    };

    return (
        <Layout>
            <div className="pb-20 max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <Link to="/" className="p-2 hover:bg-secondary rounded-lg transition-colors">
                            <ArrowLeft className="w-5 h-5 text-muted-foreground" />
                        </Link>
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight font-display">Run Comparison</h1>
                            <p className="text-sm text-muted-foreground mt-0.5 flex items-center gap-2">
                                Comparing
                                <span className="font-mono bg-secondary px-1.5 py-0.5 rounded text-xs text-foreground">{baseRun.summary.run_id.slice(0, 8)}</span>
                                <ArrowRight className="w-3 h-3" />
                                <span className="font-mono bg-secondary px-1.5 py-0.5 rounded text-xs text-foreground font-bold">{targetRun.summary.run_id.slice(0, 8)}</span>
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={handleCopyCli}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-background hover:bg-secondary transition-colors text-xs font-medium"
                        title="Copy CLI command"
                    >
                        {copyStatus === "success" ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                        ) : copyStatus === "error" ? (
                            <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                        ) : (
                            <Terminal className="w-3.5 h-3.5 text-muted-foreground" />
                        )}
                        {copyStatus === "success" ? "Copied!" : "Copy CLI"}
                    </button>
                </div>

                {/* Top Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {/* Pass Rate Delta */}
                    <div className="surface-panel p-6 flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground mb-1">Pass Rate Change</p>
                            <div className="flex items-baseline gap-2">
                                <h2 className="text-3xl font-bold">
                                    {(targetRun.summary.pass_rate * 100).toFixed(1)}%
                                </h2>
                                <span className={`text-sm font-semibold flex items-center ${passRateDelta >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                                    {passRateDelta > 0 ? "+" : ""}{(passRateDelta * 100).toFixed(1)}%
                                    {passRateDelta >= 0 ? <TrendingUp className="w-3 h-3 ml-1" /> : <TrendingDown className="w-3 h-3 ml-1" />}
                                </span>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                                Base: {(baseRun.summary.pass_rate * 100).toFixed(1)}%
                            </p>
                        </div>
                    </div>

                    {/* Regressions Count */}
                    <div className="surface-panel p-6">
                        <p className="text-sm text-muted-foreground mb-1">Regressions</p>
                        <p className="text-3xl font-bold text-rose-500">
                            {resolvedCounts.regressions}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">Test cases that flipped from Pass to Fail</p>
                    </div>

                    {/* Improvements Count */}
                    <div className="surface-panel p-6">
                        <p className="text-sm text-muted-foreground mb-1">Improvements</p>
                        <p className="text-3xl font-bold text-emerald-500">
                            {resolvedCounts.improvements}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">Test cases that flipped from Fail to Pass</p>
                    </div>

                    <div
                        className="surface-panel p-6 cursor-help"
                        title={(() => {
                            const getStats = (warnings: StageMetric[]) => {
                                const reconstructed = warnings.filter(w => w.evidence?.order_reconstructed).length;
                                const unordered = warnings.filter(w => w.evidence?.unordered_input).length;
                                return `${warnings.length} (Recon: ${reconstructed}, Raw: ${unordered})`;
                            };
                            return `Target: ${getStats(orderingWarningsTarget)}\nBase: ${getStats(orderingWarningsBase)}`;
                        })()}
                    >
                        <p className="text-sm text-muted-foreground mb-1 flex items-center gap-1">
                            Ordering Warning
                            <CheckCircle2 className="w-3.5 h-3.5 text-amber-500" />
                        </p>
                        <div className="flex items-baseline gap-2">
                            <h2 className="text-3xl font-bold text-amber-500">
                                {((orderingWarningsTarget.length / (targetRun.summary.total_test_cases || 1)) * 100).toFixed(1)}%
                            </h2>
                            <span className="text-sm text-muted-foreground">
                                vs {((orderingWarningsBase.length / (baseRun.summary.total_test_cases || 1)) * 100).toFixed(1)}%
                            </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Retrieval consistency check
                        </p>
                    </div>
                </div>

                <div className="flex flex-wrap gap-2 mb-8 text-xs">
                    <span className="px-2 py-1 rounded-full border border-rose-500/30 bg-rose-500/10 text-rose-600">
                        Regressions {resolvedCounts.regressions}
                    </span>
                    <span className="px-2 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-600">
                        Improvements {resolvedCounts.improvements}
                    </span>
                    <span className="px-2 py-1 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-600">
                        New {resolvedCounts.new}
                    </span>
                    <span className="px-2 py-1 rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-600">
                        Removed {resolvedCounts.removed}
                    </span>
                </div>

                <div className="surface-panel p-6 mb-8">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-2">
                            <FileDiff className="w-5 h-5 text-primary" />
                            <h3 className="font-semibold">프롬프트 변경 사항</h3>
                            {diffLoading && (
                                <span className="text-xs text-muted-foreground animate-pulse ml-2">로딩 중...</span>
                            )}
                        </div>
                        <div className="flex gap-2">
                            {promptDiff && (
                                <button
                                    onClick={downloadPromptDiff}
                                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md border border-border hover:bg-secondary transition-colors"
                                >
                                    <Download className="w-3.5 h-3.5" />
                                    다운로드
                                </button>
                            )}
                            <button
                                onClick={() => setShowDiff((prev) => !prev)}
                                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
                            >
                                {showDiff ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                                {showDiff ? "상세 숨기기" : "비교 상세 보기"}
                            </button>
                        </div>
                    </div>

                    {diffError ? (
                        <div className="text-center py-8 text-sm text-rose-600 border border-dashed border-border rounded-lg">
                            {diffError}
                        </div>
                    ) : !promptDiff && !diffLoading ? (
                        <div className="text-center py-8 text-sm text-muted-foreground border border-dashed border-border rounded-lg">
                            프롬프트 비교 정보를 불러올 수 없습니다.
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="overflow-hidden rounded-lg border border-border">
                                <table className="w-full text-xs">
                                    <thead className="bg-secondary/30 text-muted-foreground font-medium border-b border-border">
                                        <tr>
                                            <th className="px-4 py-2 text-left">역할 (Role)</th>
                                            <th className="px-4 py-2 text-left">상태</th>
                                            <th className="px-4 py-2 text-left">Base</th>
                                            <th className="px-4 py-2 text-left">Target</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/50 bg-card">
                                        {promptDiff?.summary.map((item, idx) => (
                                            <tr key={`${item.role}-${idx}`} className="hover:bg-secondary/10 transition-colors">
                                                <td className="px-4 py-2 font-medium text-foreground">{item.role}</td>
                                                <td className="px-4 py-2">
                                                    <span
                                                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide ${
                                                            item.status === "same"
                                                                ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20"
                                                                : item.status === "diff"
                                                                ? "bg-amber-500/10 text-amber-600 border border-amber-500/20"
                                                                : "bg-secondary text-muted-foreground border border-border"
                                                        }`}
                                                    >
                                                        {item.status === "same"
                                                            ? "동일함"
                                                            : item.status === "diff"
                                                            ? "변경됨"
                                                            : "없음"}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-2 text-muted-foreground truncate max-w-[150px]" title={item.base_name || ""}>
                                                    {item.base_name || "-"}
                                                </td>
                                                <td className="px-4 py-2 text-muted-foreground truncate max-w-[150px]" title={item.target_name || ""}>
                                                    {item.target_name || "-"}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {showDiff && promptDiff?.diffs.length ? (
                                <div className="animate-in fade-in slide-in-from-top-2 duration-300 space-y-4 pt-2">
                                    {promptDiff.diffs.map((diff, idx) => (
                                        <div key={`diff-${idx}`} className="border border-border rounded-lg overflow-hidden shadow-sm">
                                            <div className="bg-secondary/30 px-4 py-2 border-b border-border flex justify-between items-center">
                                                <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                                                    {diff.role} Diff
                                                </span>
                                            </div>
                                            <div className="bg-background overflow-x-auto">
                                                <pre className="text-[11px] leading-relaxed font-mono p-4 min-w-full">
                                                    {diff.lines.map((line, index) => (
                                                        <div
                                                            key={`${diff.role}-${index}`}
                                                            className={`px-2 -mx-2 py-0.5 w-full ${
                                                                line.startsWith("+")
                                                                    ? "bg-emerald-500/5 text-emerald-600"
                                                                    : line.startsWith("-")
                                                                    ? "bg-rose-500/5 text-rose-600"
                                                                    : line.startsWith("?")
                                                                    ? "bg-amber-500/5 text-amber-600"
                                                                    : "text-muted-foreground"
                                                            }`}
                                                        >
                                                            {line}
                                                        </div>
                                                    ))}
                                                    {diff.truncated && (
                                                        <div className="px-2 py-2 text-muted-foreground italic border-t border-border/50 mt-2">
                                                            ... 결과가 너무 길어 생략되었습니다 (전체 내용은 다운로드하여 확인하세요)
                                                        </div>
                                                    )}
                                                </pre>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : null}
                        </div>
                    )}
                </div>

                <div className="surface-panel p-6 mb-8">
                    <h3 className="font-semibold mb-6">Metric Performance Delta</h3>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                data={metricDeltas}
                                layout="vertical"
                                margin={{ left: 100, right: 30 }}
                                stackOffset="sign"
                            >
                                <XAxis type="number" domain={[-0.5, 0.5]} hide />
                                <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 12 }} />
                                <Tooltip
                                    cursor={{ fill: 'transparent' }}
                                    content={({ active, payload }) => {
                                        if (active && payload && payload.length) {
                                            const d = payload[0].payload;
                                            return (
                                                <div className="bg-popover border border-border p-3 rounded-lg shadow-xl text-sm">
                                                    <p className="font-semibold mb-1">{d.name}</p>
                                                    <p>Base: {formatScore(d.base)}</p>
                                                    <p>Target: {formatScore(d.target)}</p>
                                                    <p className={d.delta >= 0 ? "text-emerald-500" : "text-rose-500"}>
                                                        Delta: {d.delta > 0 ? "+" : ""}{formatScore(d.delta, 3)}
                                                    </p>
                                                </div>
                                            );
                                        }
                                        return null;
                                    }}
                                />
                                <ReferenceLine x={0} stroke="#666" />
                                <Bar dataKey="delta" barSize={20}>
                                    {metricDeltas.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.delta >= 0 ? '#10b981' : '#f43f5e'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Diff Table */}
                <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
                    <div className="p-4 border-b border-border flex flex-wrap justify-between items-center gap-3 bg-secondary/20">
                        <h3 className="font-semibold">Test Case Comparison</h3>
                        <div className="flex items-center gap-2 text-xs">
                            {(["all", "changes", "regressions"] as const).map((mode) => (
                                <button
                                    key={mode}
                                    type="button"
                                    onClick={() => setFilterMode(mode)}
                                    className={`filter-chip ${filterMode === mode
                                        ? "filter-chip-active"
                                        : "filter-chip-inactive"
                                        }`}
                                >
                                    {mode === "all" ? "All" : mode === "changes" ? "Changes" : "Regressions"}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="divide-y divide-border">
                        {visibleRows.length === 0 ? (
                            <div className="p-12 text-center text-muted-foreground">
                                No test cases found matching the filter.
                            </div>
                        ) : (
                            visibleRows.map((row) => (
                                <div key={row.id} className="p-5 hover:bg-secondary/10 transition-colors">
                                    <div className="flex items-start gap-4 mb-3">
                                        <div className="flex flex-col gap-1 items-center mt-1">
                                            {/* Status Icon */}
                                            {row.status === "regression" && <TrendingDown className="w-5 h-5 text-rose-500" />}
                                            {row.status === "improvement" && <TrendingUp className="w-5 h-5 text-emerald-500" />}
                                            {row.status === "new" && <PlusCircle className="w-5 h-5 text-blue-500" />}
                                            {row.status === "removed" && <MinusCircle className="w-5 h-5 text-amber-500" />}
                                            {row.status === "same_pass" && <CheckCircle2 className="w-5 h-5 text-emerald-500/30" />}
                                            {row.status === "same_fail" && <XCircle className="w-5 h-5 text-rose-500/30" />}
                                        </div>
                                        <div className="flex-1">
                                            <p className="font-medium text-foreground">{row.question}</p>
                                            <div className="flex gap-2 mt-1">
                                                {row.status === "regression" && <span className="text-[10px] bg-rose-500/10 text-rose-500 px-1.5 py-0.5 rounded font-mono uppercase">Regression</span>}
                                                {row.status === "improvement" && <span className="text-[10px] bg-emerald-500/10 text-emerald-500 px-1.5 py-0.5 rounded font-mono uppercase">Improvement</span>}
                                                {row.status === "new" && <span className="text-[10px] bg-blue-500/10 text-blue-500 px-1.5 py-0.5 rounded font-mono uppercase">New</span>}
                                                {row.status === "removed" && <span className="text-[10px] bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded font-mono uppercase">Removed</span>}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4 mt-4 bg-background/50 rounded-lg p-3 border border-border/50 text-sm">
                                        <div>
                                            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2 border-b border-border/50 pb-1">Base Run ({baseRun.summary.model_name})</p>
                                            <p className="leading-relaxed text-muted-foreground">{row.baseAnswer}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2 border-b border-border/50 pb-1 text-foreground font-medium">Target Run ({targetRun.summary.model_name})</p>
                                            <p className="leading-relaxed text-foreground">{row.targetAnswer}</p>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
}
