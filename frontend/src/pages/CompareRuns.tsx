import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { fetchRunDetails, type RunDetailsResponse } from "../services/api";
import { formatScore, normalizeScore, safeAverage } from "../utils/score";
import {
    ArrowLeft,
    CheckCircle2,
    XCircle,
    ArrowRight,
    TrendingUp,
    TrendingDown,
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";

export function CompareRuns() {
    const [searchParams] = useSearchParams();
    const baseId = searchParams.get("base");
    const targetId = searchParams.get("target");

    const [baseRun, setBaseRun] = useState<RunDetailsResponse | null>(null);
    const [targetRun, setTargetRun] = useState<RunDetailsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // View state
    const [showOnlyDiff, setShowOnlyDiff] = useState(false);

    useEffect(() => {
        async function loadData() {
            if (!baseId || !targetId) {
                setError("Missing run IDs for comparison");
                setLoading(false);
                return;
            }

            try {
                const [base, target] = await Promise.all([
                    fetchRunDetails(baseId),
                    fetchRunDetails(targetId)
                ]);
                setBaseRun(base);
                setTargetRun(target);
            } catch (err) {
                setError("Failed to load runs for comparison");
            } finally {
                setLoading(false);
            }
        }
        loadData();
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
    const combinedResults = baseRun.results.map(baseCase => {
        const targetCase = targetRun.results.find(tc => tc.test_case_id === baseCase.test_case_id);
        const basePassed = baseCase.metrics.every(m => m.passed);
        const targetPassed = targetCase ? targetCase.metrics.every(m => m.passed) : false;

        // Status: "same_pass", "same_fail", "regression", "improvement", "removed"
        let status: "same_pass" | "same_fail" | "regression" | "improvement" | "removed" | "new" = "same_pass";

        if (!targetCase) status = "removed";
        else if (basePassed && !targetPassed) status = "regression";
        else if (!basePassed && targetPassed) status = "improvement";
        else if (basePassed && targetPassed) status = "same_pass";
        else status = "same_fail";

        return {
            id: baseCase.test_case_id,
            question: baseCase.question,
            baseAnswer: baseCase.answer,
            targetAnswer: targetCase?.answer || "(N/A)",
            status,
            basePassed,
            targetPassed
        };
    });

    // Filter
    const visibleRows = showOnlyDiff
        ? combinedResults.filter(r => r.status === "regression" || r.status === "improvement")
        : combinedResults;

    const passRateDelta = targetRun.summary.pass_rate - baseRun.summary.pass_rate;

    return (
        <Layout>
            <div className="pb-20 max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <Link to="/" className="p-2 hover:bg-secondary rounded-lg transition-colors">
                        <ArrowLeft className="w-5 h-5 text-muted-foreground" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Run Comparison</h1>
                        <p className="text-sm text-muted-foreground mt-0.5 flex items-center gap-2">
                            Comparing
                            <span className="font-mono bg-secondary px-1.5 py-0.5 rounded text-xs text-foreground">{baseRun.summary.run_id.slice(0, 8)}</span>
                            <ArrowRight className="w-3 h-3" />
                            <span className="font-mono bg-secondary px-1.5 py-0.5 rounded text-xs text-foreground font-bold">{targetRun.summary.run_id.slice(0, 8)}</span>
                        </p>
                    </div>
                </div>

                {/* Top Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    {/* Pass Rate Delta */}
                    <div className="bg-card border border-border rounded-xl p-6 shadow-sm flex items-center justify-between">
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
                    <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
                        <p className="text-sm text-muted-foreground mb-1">Regressions</p>
                        <p className="text-3xl font-bold text-rose-500">
                            {combinedResults.filter(r => r.status === "regression").length}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">Test cases that flipped from Pass to Fail</p>
                    </div>

                    {/* Improvements Count */}
                    <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
                        <p className="text-sm text-muted-foreground mb-1">Improvements</p>
                        <p className="text-3xl font-bold text-emerald-500">
                            {combinedResults.filter(r => r.status === "improvement").length}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">Test cases that flipped from Fail to Pass</p>
                    </div>
                </div>

                {/* Metric Delta Chart */}
                <div className="bg-card border border-border rounded-xl p-6 shadow-sm mb-8">
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
                    <div className="p-4 border-b border-border flex justify-between items-center bg-secondary/20">
                        <h3 className="font-semibold">Test Case Comparison</h3>
                        <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
                            <input
                                type="checkbox"
                                checked={showOnlyDiff}
                                onChange={(e) => setShowOnlyDiff(e.target.checked)}
                                className="rounded border-gray-300 text-primary focus:ring-primary"
                            />
                            Show only changes (Regressions/Improvements)
                        </label>
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
                                            {row.status === "same_pass" && <CheckCircle2 className="w-5 h-5 text-emerald-500/30" />}
                                            {row.status === "same_fail" && <XCircle className="w-5 h-5 text-rose-500/30" />}
                                        </div>
                                        <div className="flex-1">
                                            <p className="font-medium text-foreground">{row.question}</p>
                                            <div className="flex gap-2 mt-1">
                                                {row.status === "regression" && <span className="text-[10px] bg-rose-500/10 text-rose-500 px-1.5 py-0.5 rounded font-mono uppercase">Regression</span>}
                                                {row.status === "improvement" && <span className="text-[10px] bg-emerald-500/10 text-emerald-500 px-1.5 py-0.5 rounded font-mono uppercase">Improvement</span>}
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
