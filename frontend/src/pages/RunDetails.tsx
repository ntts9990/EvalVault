import { useEffect, useState } from "react";
import { useParams, Link, useLocation } from "react-router-dom";
import { fetchRunDetails, type RunDetailsResponse } from "../services/api";
import { Layout } from "../components/Layout";
import { formatScore, normalizeScore, safeAverage } from "../utils/score";
import {
    ArrowLeft,
    CheckCircle2,
    XCircle,
    ChevronDown,
    ChevronRight,
    Target,
    FileText,
    MessageSquare,
    BookOpen
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { SUMMARY_METRICS, SUMMARY_METRIC_THRESHOLDS } from "../utils/summaryMetrics";

export function RunDetails() {
    const { id } = useParams<{ id: string }>();
    const location = useLocation();
    const [data, setData] = useState<RunDetailsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    // Tabs
    const [activeTab, setActiveTab] = useState<"overview" | "performance">("overview");
    const [expandedCases, setExpandedCases] = useState<Set<string>>(new Set());
    const summaryMetricSet = new Set(SUMMARY_METRICS);

    useEffect(() => {
        async function loadDetails() {
            if (!id) return;
            try {
                const details = await fetchRunDetails(id);
                setData(details);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load run details");
            } finally {
                setLoading(false);
            }
        }
        loadDetails();
    }, [id]);

    useEffect(() => {
        if (!data || !location.hash) return;
        const match = location.hash.match(/^#case-(.+)$/);
        if (!match) return;
        const caseId = decodeURIComponent(match[1]);
        if (!data.results.some(result => result.test_case_id === caseId)) return;
        setExpandedCases(prev => {
            const next = new Set(prev);
            next.add(caseId);
            return next;
        });
        requestAnimationFrame(() => {
            const target = document.getElementById(`case-${caseId}`);
            if (target) {
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    }, [data, location.hash]);

    /*
    useEffect(() => {
        async function loadAnalysis() {
            if (!id || activeTab === "overview") return;

            // Only load if not already loaded
            if (activeTab === "improvement" && !improvementData) {
                setLoadingAnalysis(true);
                try {
                    const data = await fetchImprovementGuide(id);
                    setImprovementData(data);
                } catch (e) {
                    console.error(e);
                } finally {
                    setLoadingAnalysis(false);
                }
            } else if (activeTab === "report" && !reportData) {
                setLoadingAnalysis(true);
                try {
                    const data = await fetchLLMReport(id);
                    setReportData(data);
                } catch (e) {
                    console.error(e);
                } finally {
                    setLoadingAnalysis(false);
                }
            }
        }
        loadAnalysis();
    }, [id, activeTab, improvementData, reportData]);
    */

    const toggleExpand = (testCaseId: string) => {
        const newSet = new Set(expandedCases);
        if (newSet.has(testCaseId)) {
            newSet.delete(testCaseId);
        } else {
            newSet.add(testCaseId);
        }
        setExpandedCases(newSet);
    };

    // Prepare chart data
    const metricScores = data?.summary.metrics_evaluated?.map(metric => {
        if (!data?.results) return { name: metric, score: 0 };

        // Compute average
        const scores = data.results.flatMap(
            r => r.metrics?.filter(m => m.name === metric).map(m => normalizeScore(m.score)) || []
        );
        const avg = safeAverage(scores);

        return { name: metric, score: avg };
    }) || [];


    if (loading) return (
        <Layout>
            <div className="flex items-center justify-center h-[50vh] text-muted-foreground">Loading analysis...</div>
        </Layout>
    );

    if (error || !data) return (
        <Layout>
            <div className="flex flex-col items-center justify-center h-[50vh] text-destructive gap-4">
                <p className="text-xl font-bold">Error loading analysis</p>
                <p>{error}</p>
                <Link to="/" className="text-primary hover:underline">Return to Dashboard</Link>
            </div>
        </Layout>
    );

    const { summary, results } = data;
    const summaryThresholds = summary.thresholds || {};
    const summaryMetrics = summary.metrics_evaluated.filter((metric) =>
        summaryMetricSet.has(metric)
    );
    const thresholdProfileLabel = summary.threshold_profile
        ? summary.threshold_profile.toUpperCase()
        : "Dataset/default";
    const summarySafetyRows = summaryMetrics.map((metric) => {
        const scores = results.flatMap(
            (result) =>
                result.metrics
                    ?.filter((entry) => entry.name === metric)
                    .map((entry) => normalizeScore(entry.score)) || []
        );
        const avg = safeAverage(scores);
        const threshold =
            summaryThresholds[metric] ?? SUMMARY_METRIC_THRESHOLDS[metric] ?? 0.7;
        return {
            metric,
            avg,
            threshold,
            passed: avg >= threshold,
        };
    });
    const summarySafetyAlert = summarySafetyRows.some((row) => !row.passed);

    return (
        <Layout>
            <div className="pb-20">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <Link to="/" className="p-2 hover:bg-secondary rounded-lg transition-colors">
                        <ArrowLeft className="w-5 h-5 text-muted-foreground" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">{summary.dataset_name} Analysis</h1>
                        <p className="text-sm text-muted-foreground mt-0.5 flex items-center gap-2">
                            <span className="font-mono bg-secondary px-1.5 py-0.5 rounded text-xs">{summary.run_id.slice(0, 8)}</span>
                            <span>•</span>
                            <span className="font-medium text-foreground">{summary.model_name}</span>
                            <span>•</span>
                            <span>{new Date(summary.started_at).toLocaleString()}</span>
                        </p>
                    </div>
                    <div className="ml-auto flex items-center gap-6">
                        {/* Tab Navigation */}
                        <div className="flex bg-secondary p-1 rounded-lg">
                            <button
                                onClick={() => setActiveTab("overview")}
                                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === "overview" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
                            >
                                Overview
                            </button>
                            <button
                                onClick={() => setActiveTab("performance")}
                                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === "performance" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
                            >
                                Performance
                            </button>
                        </div>

                        {summary.phoenix_drift != null && (
                            <div className="text-right">
                                <p className="text-sm text-muted-foreground flex items-center gap-1 justify-end" title="Phoenix Drift Score (Embeddings Distance)">
                                    Drift Signal
                                </p>
                                <p className={`text-xl font-bold font-mono ${summary.phoenix_drift > 0.3 ? "text-rose-500" : summary.phoenix_drift > 0.1 ? "text-amber-500" : "text-emerald-500"}`}>
                                    {typeof summary.phoenix_drift === 'number' ? summary.phoenix_drift.toFixed(3) : "N/A"}
                                </p>
                            </div>
                        )}

                        <div className="text-right">
                            <p className="text-sm text-muted-foreground">Pass Rate</p>
                            <p className={`text-2xl font-bold ${summary.pass_rate >= 0.7 ? "text-emerald-500" : "text-rose-500"}`}>
                                {(summary.pass_rate * 100).toFixed(1)}%
                            </p>
                        </div>

                        {summary.phoenix_experiment_url && (
                            <a
                                href={summary.phoenix_experiment_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 px-4 py-2 bg-orange-50 text-orange-600 border border-orange-200 rounded-lg hover:bg-orange-100 transition-colors"
                            >
                                <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
                                <span className="font-medium text-sm">Phoenix</span>
                            </a>
                        )}
                    </div>
                </div>

                {summarySafetyRows.length > 0 && (
                    <div className="bg-card border border-border rounded-xl p-6 shadow-sm mb-8">
                        <div className="flex flex-wrap items-start justify-between gap-4">
                            <div>
                                <h3 className="font-semibold mb-1 flex items-center gap-2">
                                    <Target className="w-4 h-4 text-primary" />
                                    Summary Safety
                                </h3>
                                <p className="text-xs text-muted-foreground">
                                    Conservative thresholds apply when dataset thresholds are missing.
                                </p>
                            </div>
                            <span
                                className={`px-2 py-1 rounded-full text-xs font-semibold border ${summarySafetyAlert
                                    ? "bg-rose-500/10 text-rose-600 border-rose-500/20"
                                    : "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                                    }`}
                            >
                                {summarySafetyAlert ? "Attention" : "OK"}
                            </span>
                        </div>
                        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
                            {summarySafetyRows.map((row) => (
                                <div
                                    key={row.metric}
                                    className={`p-4 rounded-lg border ${row.passed
                                        ? "bg-emerald-500/5 border-emerald-500/20"
                                        : "bg-rose-500/5 border-rose-500/20"
                                        }`}
                                >
                                    <p className="text-sm text-muted-foreground">{row.metric}</p>
                                    <p
                                        className={`text-2xl font-bold ${row.passed
                                            ? "text-emerald-600"
                                            : "text-rose-600"
                                            }`}
                                    >
                                        {formatScore(row.avg)}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        Threshold {row.threshold.toFixed(2)}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === "overview" ? (
                    /* Charts & Summary Grid (Overview) */
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                        {/* Metric Performance Chart */}
                        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-6 shadow-sm">
                            <h3 className="font-semibold mb-6 flex items-center gap-2">
                                <Target className="w-4 h-4 text-primary" />
                                Metric Performance
                            </h3>
                            <div className="h-64 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={metricScores} layout="vertical" margin={{ left: 40, right: 30 }}>
                                        <XAxis type="number" domain={[0, 1]} hide />
                                        <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 12 }} />
                                        <Tooltip
                                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                            cursor={{ fill: 'transparent' }}
                                        />
                                        <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={24}>
                                            {metricScores.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.score >= 0.7 ? '#10b981' : '#f43f5e'} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Stats Cards */}
                        <div className="space-y-4">
                            <div className="bg-card border border-border rounded-xl p-5">
                                <p className="text-sm text-muted-foreground mb-1">Total Test Cases</p>
                                <p className="text-3xl font-bold">{summary.total_test_cases}</p>
                            </div>
                            <div className="bg-card border border-border rounded-xl p-5">
                                <p className="text-sm text-muted-foreground mb-1">Passed Cases</p>
                                <div className="flex items-baseline gap-2">
                                    <p className="text-3xl font-bold text-emerald-500">{summary.passed_test_cases}</p>
                                    <p className="text-sm text-muted-foreground">/ {summary.total_test_cases}</p>
                                </div>
                            </div>
                            <div className="bg-card border border-border rounded-xl p-5">
                                <p className="text-sm text-muted-foreground mb-1">Latency / Cost</p>
                                <p className="font-mono text-sm">
                                    {summary.total_cost_usd ? `$${summary.total_cost_usd.toFixed(4)}` : "N/A"}
                                </p>
                            </div>
                            <div className="bg-card border border-border rounded-xl p-5">
                                <p className="text-sm text-muted-foreground mb-1">Threshold Profile</p>
                                <p className="text-sm font-semibold tracking-wide">{thresholdProfileLabel}</p>
                            </div>
                        </div>
                    </div>
                ) : (
                    /* Performance Tab Content */
                    /* Performance Tab Content */
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8 animate-in fade-in duration-300">
                        {/* Latency Analysis */}
                        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
                            <h3 className="font-semibold mb-2">Evaluation Speed</h3>
                            <p className="text-sm text-muted-foreground mb-6">Average time per test case</p>
                            <div className="h-64 w-full flex items-center justify-center">
                                {summary.finished_at ? (
                                    <div className="text-center">
                                        <div className="inline-flex items-end justify-center w-32 bg-primary/10 border border-primary/30 h-40 rounded-t-lg relative mb-2">
                                            <span className="absolute -top-8 text-2xl font-bold text-foreground">
                                                {(() => {
                                                    const start = new Date(summary.started_at).getTime();
                                                    const end = new Date(summary.finished_at).getTime();
                                                    const durationMs = end - start;
                                                    const avgMs = durationMs / (summary.total_test_cases || 1);
                                                    return `${(avgMs / 1000).toFixed(2)}s`;
                                                })()}
                                            </span>
                                        </div>
                                        <p className="text-sm font-medium text-muted-foreground">Avg. Duration</p>
                                    </div>
                                ) : (
                                    <p className="text-muted-foreground">Run in progress...</p>
                                )}
                            </div>
                            <div className="mt-6 text-center text-xs text-muted-foreground bg-secondary/30 p-2 rounded">
                                * Calculated based on total run duration / test case count.
                            </div>
                        </div>

                        {/* Token Usage / Cost Distribution */}
                        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
                            <h3 className="font-semibold mb-2">Estimated Cost</h3>
                            <p className="text-sm text-muted-foreground mb-6">Based on model pricing (Input/Output)</p>
                            <div className="flex items-center justify-center h-64 text-muted-foreground italic">
                                {summary.total_cost_usd !== null && summary.total_cost_usd > 0 ? (
                                    <div className="text-center">
                                        <p className="text-4xl font-bold text-foreground mb-2">${summary.total_cost_usd.toFixed(4)}</p>
                                        <p>Total Run Cost</p>
                                        <p className="text-xs text-muted-foreground mt-2">(Excludes retrieval API costs)</p>
                                    </div>
                                ) : (
                                    <div className="text-center">
                                        <p className="text-lg text-muted-foreground">Cost data not available</p>
                                        <p className="text-xs mt-1">Make sure the model is supported for pricing.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Test Case Explorer */}
                <h3 className="font-semibold text-xl mb-4">Test Case Explorer</h3>
                <div className="space-y-4">
                    {(results || []).map((result) => {
                        const isExpanded = expandedCases.has(result.test_case_id);
                        const allPassed = result.metrics.every(m => m.passed);

                        return (
                            <div
                                id={`case-${result.test_case_id}`}
                                key={result.test_case_id}
                                className={`bg-card border rounded-xl overflow-hidden transition-all ${isExpanded ? "ring-2 ring-primary/20 border-primary shadow-md" : "border-border hover:border-border/80"
                                    }`}
                            >
                                {/* Summary Header (Clickable) */}
                                <div
                                    onClick={() => toggleExpand(result.test_case_id)}
                                    className="p-4 flex items-start gap-4 cursor-pointer hover:bg-secondary/30 transition-colors"
                                >
                                    <div className="mt-1">
                                        {allPassed ? (
                                            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                                        ) : (
                                            <XCircle className="w-5 h-5 text-rose-500" />
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-foreground line-clamp-1">{result.question}</p>
                                        <p className="text-sm text-muted-foreground line-clamp-1 mt-1">{result.answer}</p>
                                    </div>

                                    <div className="flex items-center gap-3">
                                        {/* Metric Mini-Badges */}
                                        <div className="flex gap-1 hidden sm:flex">
                                            {result.metrics.map(m => (
                                                <div
                                                    key={m.name}
                                                    className={`w-1.5 h-6 rounded-full ${m.passed ? "bg-emerald-500/50" : "bg-rose-500/50"}`}
                                                    title={`${m.name}: ${formatScore(m.score)}`}
                                                />
                                            ))}
                                        </div>
                                        <div className="text-muted-foreground">
                                            {isExpanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                                        </div>
                                    </div>
                                </div>

                                {/* Expanded Details */}
                                {isExpanded && (
                                    <div className="border-t border-border bg-secondary/10 p-6 animate-in slide-in-from-top-2 duration-200">
                                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                                            <div className="space-y-4">
                                                <div>
                                                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2">
                                                        <MessageSquare className="w-3.5 h-3.5" /> Question
                                                    </h4>
                                                    <div className="p-3 bg-background border border-border rounded-lg text-sm">
                                                        {result.question}
                                                    </div>
                                                </div>
                                                <div>
                                                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2">
                                                        <FileText className="w-3.5 h-3.5" /> Generated Answer
                                                    </h4>
                                                    <div className="p-3 bg-background border border-border rounded-lg text-sm leading-relaxed">
                                                        {result.answer}
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="space-y-4">
                                                {result.ground_truth && (
                                                    <div>
                                                        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2">
                                                            <Target className="w-3.5 h-3.5" /> Ground Truth
                                                        </h4>
                                                        <div className="p-3 bg-background border border-border rounded-lg text-sm text-muted-foreground">
                                                            {result.ground_truth}
                                                        </div>
                                                    </div>
                                                )}
                                                {result.contexts && result.contexts.length > 0 && (
                                                    <div>
                                                        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2">
                                                            <BookOpen className="w-3.5 h-3.5" /> Retrieved Contexts ({result.contexts.length})
                                                        </h4>
                                                        <div className="space-y-2 max-h-60 overflow-y-auto">
                                                            {result.contexts.map((ctx, idx) => (
                                                                <div key={idx} className="p-2.5 bg-background border border-border/60 rounded-lg text-xs text-muted-foreground border-l-2 border-l-primary/30">
                                                                    {ctx}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Detailed Metrics Table */}
                                        <div>
                                            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Metric Details</h4>
                                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                                                {result.metrics.map((metric) => {
                                                    const isSummaryMetric = summaryMetricSet.has(metric.name);
                                                    return (
                                                        <div
                                                            key={metric.name}
                                                            className={`p-3 rounded-lg border ${metric.passed
                                                                ? "bg-emerald-500/5 border-emerald-500/20"
                                                                : "bg-rose-500/5 border-rose-500/20"
                                                                } ${isSummaryMetric ? "ring-1 ring-primary/20" : ""}`}
                                                        >
                                                            <div className="flex justify-between items-start mb-1 gap-2">
                                                                <div className="flex items-center gap-2">
                                                                    <span className="font-medium text-sm">{metric.name}</span>
                                                                    {isSummaryMetric && (
                                                                        <span className="px-2 py-0.5 rounded-full bg-primary/10 text-[10px] text-primary">
                                                                            Summary
                                                                        </span>
                                                                    )}
                                                                </div>
                                                                <span className={`text-sm font-bold ${metric.passed ? "text-emerald-600" : "text-rose-600"}`}>
                                                                    {formatScore(metric.score)}
                                                                </span>
                                                            </div>
                                                            {metric.reason && (
                                                                <p className="text-xs text-muted-foreground mt-2 italic">
                                                                    "{metric.reason}"
                                                                </p>
                                                            )}
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </Layout>
    );
}
