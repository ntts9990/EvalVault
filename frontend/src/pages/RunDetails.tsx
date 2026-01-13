import { useEffect, useState } from "react";
import { useParams, Link, useLocation } from "react-router-dom";
import {
    fetchRunDetails,
    fetchRunFeedback,
    saveRunFeedback,
    fetchRunFeedbackSummary,
    type RunDetailsResponse,
    type FeedbackResponse
} from "../services/api";
import { Layout } from "../components/Layout";
import { InsightSpacePanel } from "../components/InsightSpacePanel";
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
    BookOpen,
    ExternalLink,
    ThumbsUp,
    ThumbsDown,
    Star,
    Save,
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { SUMMARY_METRICS, SUMMARY_METRIC_THRESHOLDS, type SummaryMetric } from "../utils/summaryMetrics";

function FeedbackItem({
    result,
    feedback,
    onSave,
}: {
    result: RunDetailsResponse["results"][number];
    feedback?: FeedbackResponse;
    onSave: (
        id: string,
        score: number | null,
        thumb: "up" | "down" | "none" | null,
        comment: string | null
    ) => void;
}) {
    const [score, setScore] = useState<number | null>(feedback?.satisfaction_score ?? null);
    const resolveThumb = (value: string | null | undefined): "up" | "down" | "none" => {
        if (value === "up" || value === "down") {
            return value;
        }
        return "none";
    };
    const [thumb, setThumb] = useState<"up" | "down" | "none" | null>(
        resolveThumb(feedback?.thumb_feedback)
    );
    const [comment, setComment] = useState<string>(feedback?.comment ?? "");
    const [isDirty, setIsDirty] = useState(false);

    useEffect(() => {
        let canceled = false;
        Promise.resolve().then(() => {
            if (canceled) return;
            setScore(feedback?.satisfaction_score ?? null);
            setThumb(resolveThumb(feedback?.thumb_feedback));
            setComment(feedback?.comment ?? "");
            setIsDirty(false);
        });
        return () => {
            canceled = true;
        };
    }, [feedback]);

    const handleSave = () => {
        onSave(result.test_case_id, score, thumb, comment || null);
        setIsDirty(false);
    };

    return (
        <div className="bg-card border border-border rounded-xl p-4 transition-all hover:border-primary/50">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-3">
                    <div>
                        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                            Question
                        </h4>
                        <p className="text-sm font-medium text-foreground line-clamp-2">
                            {result.question}
                        </p>
                    </div>
                    <div>
                        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                            Answer
                        </h4>
                        <p className="text-sm text-muted-foreground line-clamp-3">
                            {result.answer}
                        </p>
                    </div>
                    {result.calibrated_satisfaction !== null && result.calibrated_satisfaction !== undefined && (
                        <div className="flex items-center gap-2 mt-2">
                            <span className="text-xs font-mono text-muted-foreground bg-secondary px-2 py-1 rounded">
                                Calibrated: {result.calibrated_satisfaction.toFixed(2)}
                            </span>
                            {result.imputed && (
                                <span className="text-[10px] text-amber-500 border border-amber-500/30 px-1.5 rounded">
                                    Imputed
                                </span>
                            )}
                        </div>
                    )}
                </div>

                <div className="space-y-4 border-l border-border/50 pl-0 lg:pl-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-1">
                                {[1, 2, 3, 4, 5].map((s) => (
                                    <button
                                        key={s}
                                        onClick={() => {
                                            setScore(s);
                                            setIsDirty(true);
                                        }}
                                        className={`p-1 transition-colors ${
                                            (score ?? 0) >= s
                                                ? "text-yellow-400"
                                                : "text-muted-foreground/30 hover:text-yellow-400/50"
                                        }`}
                                    >
                                        <Star
                                            className="w-5 h-5"
                                            fill={(score ?? 0) >= s ? "currentColor" : "none"}
                                        />
                                    </button>
                                ))}
                            </div>

                            <div className="flex items-center gap-2 border-l border-border pl-4">
                                <button
                                    onClick={() => {
                                        setThumb(thumb === "up" ? "none" : "up");
                                        setIsDirty(true);
                                    }}
                                    className={`p-2 rounded-full transition-colors ${
                                        thumb === "up"
                                            ? "bg-emerald-500/10 text-emerald-500"
                                            : "hover:bg-secondary text-muted-foreground"
                                    }`}
                                >
                                    <ThumbsUp className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => {
                                        setThumb(thumb === "down" ? "none" : "down");
                                        setIsDirty(true);
                                    }}
                                    className={`p-2 rounded-full transition-colors ${
                                        thumb === "down"
                                            ? "bg-rose-500/10 text-rose-500"
                                            : "hover:bg-secondary text-muted-foreground"
                                    }`}
                                >
                                    <ThumbsDown className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        <button
                            onClick={handleSave}
                            disabled={!isDirty}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                                isDirty
                                    ? "bg-primary text-primary-foreground shadow-md hover:bg-primary/90"
                                    : "bg-secondary text-muted-foreground opacity-50 cursor-not-allowed"
                            }`}
                        >
                            <Save className="w-3.5 h-3.5" />
                            Save
                        </button>
                    </div>

                    <textarea
                        value={comment}
                        onChange={(e) => {
                            setComment(e.target.value);
                            setIsDirty(true);
                        }}
                        placeholder="Add a comment about this result..."
                        className="w-full h-20 p-3 bg-secondary/20 border border-border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary/50 resize-none"
                    />
                </div>
            </div>
        </div>
    );
}

export function RunDetails() {
    const { id } = useParams<{ id: string }>();
    const location = useLocation();
    const [data, setData] = useState<RunDetailsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    // Tabs
    const [activeTab, setActiveTab] = useState<"overview" | "performance" | "feedback">("overview");
    const [expandedCases, setExpandedCases] = useState<Set<string>>(new Set());
    const [feedbackMap, setFeedbackMap] = useState<Record<string, FeedbackResponse>>({});
    const [loadingFeedback, setLoadingFeedback] = useState(false);

    const summaryMetricSet = new Set<string>(SUMMARY_METRICS);

    const previewPrompt = (content?: string) => {
        if (!content) return "";
        const lines = content.split("\n");
        const snippet = lines.slice(0, 4).join("\n");
        return lines.length > 4 ? `${snippet}\n...` : snippet;
    };

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
        if (activeTab === "feedback" && id) {
            setLoadingFeedback(true);
            fetchRunFeedback(id)
                .then((feedbacks) => {
                    const map: Record<string, FeedbackResponse> = {};
                    feedbacks.forEach((f) => (map[f.test_case_id] = f));
                    setFeedbackMap(map);
                })
                .catch((err) => console.error("Failed to load feedback", err))
                .finally(() => setLoadingFeedback(false));
        }
    }, [activeTab, id]);

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

    const handleSaveFeedback = async (
        caseId: string,
        score: number | null,
        thumb: "up" | "down" | "none" | null,
        comment: string | null
    ) => {
        if (!id) return;
        try {
            const result = await saveRunFeedback(id, {
                test_case_id: caseId,
                satisfaction_score: score,
                thumb_feedback: thumb,
                comment: comment,
            });
            setFeedbackMap((prev) => ({ ...prev, [caseId]: result }));

            try {
                const summaryData = await fetchRunFeedbackSummary(id);
                setData((prev) => {
                    if (!prev) return prev;
                    return {
                        ...prev,
                        summary: {
                            ...prev.summary,
                            avg_satisfaction_score: summaryData.avg_satisfaction_score,
                            thumb_up_rate: summaryData.thumb_up_rate,
                        },
                    };
                });
            } catch (summaryErr) {
                console.error("Failed to update feedback summary", summaryErr);
            }
        } catch (e) {
            console.error("Failed to save feedback", e);
            alert("Failed to save feedback");
        }
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
    const promptSet = data.prompt_set;
    const summaryThresholds = summary.thresholds || {};
    const summaryMetrics = summary.metrics_evaluated.filter((metric) =>
        summaryMetricSet.has(metric as SummaryMetric)
    );
    const thresholdProfileLabel = summary.threshold_profile
        ? summary.threshold_profile.toUpperCase()
        : "Dataset/default";
    const phoenixLinks = [
        summary.phoenix_trace_url
            ? { label: "Phoenix Trace", url: summary.phoenix_trace_url }
            : null,
        summary.phoenix_experiment_url
            ? { label: "Phoenix Experiment", url: summary.phoenix_experiment_url }
            : null,
    ].filter((link): link is { label: string; url: string } => Boolean(link));
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
                        <h1 className="text-2xl font-bold tracking-tight font-display">{summary.dataset_name} Analysis</h1>
                        <p className="text-sm text-muted-foreground mt-0.5 flex items-center gap-2">
                            <span className="font-mono bg-secondary px-1.5 py-0.5 rounded text-xs">{summary.run_id.slice(0, 8)}</span>
                            <span>•</span>
                            <span className="font-medium text-foreground">{summary.model_name}</span>
                            <span>•</span>
                            <span>{new Date(summary.started_at).toLocaleString()}</span>
                        </p>
                    </div>
                    <div className="ml-auto flex items-center gap-6">
                        <Link
                            to={`/visualization/${summary.run_id}`}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-colors"
                        >
                            <ExternalLink className="w-4 h-4" />
                            시각화 열기
                        </Link>
                        {/* Tab Navigation */}
                        <div className="tab-shell">
                            <button
                                onClick={() => setActiveTab("overview")}
                                className={`tab-pill ${activeTab === "overview" ? "tab-pill-active" : "tab-pill-inactive"}`}
                            >
                                Overview
                            </button>
                            <button
                                onClick={() => setActiveTab("performance")}
                                className={`tab-pill ${activeTab === "performance" ? "tab-pill-active" : "tab-pill-inactive"}`}
                            >
                                Performance
                            </button>
                            <button
                                onClick={() => setActiveTab("feedback")}
                                className={`tab-pill ${activeTab === "feedback" ? "tab-pill-active" : "tab-pill-inactive"}`}
                            >
                                Feedback
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

                        {phoenixLinks.length > 0 && (
                            <div className="flex items-center gap-2">
                                {phoenixLinks.map((link) => (
                                    <a
                                        key={link.label}
                                        href={link.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-2 px-4 py-2 bg-orange-50 text-orange-600 border border-orange-200 rounded-lg hover:bg-orange-100 transition-colors"
                                    >
                                        <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
                                        <span className="font-medium text-sm">{link.label}</span>
                                    </a>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {summarySafetyRows.length > 0 && (
                    <div className="surface-panel p-6 mb-8">
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

                {activeTab === "overview" && (
                    <>
                        {/* Charts & Summary Grid (Overview) */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                        {/* Metric Performance Chart */}
                        <div className="lg:col-span-2 surface-panel p-6">
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
                        <InsightSpacePanel runId={summary.run_id} />
                        {promptSet && (
                            <div className="surface-panel p-6 mb-8">
                                <div className="flex flex-wrap items-center justify-between gap-3">
                                    <div>
                                        <h3 className="font-semibold flex items-center gap-2">
                                            <FileText className="w-4 h-4 text-primary" />
                                            Prompt Snapshot
                                        </h3>
                                        <p className="text-xs text-muted-foreground">
                                            {promptSet.name || "Unnamed prompt set"}
                                            {promptSet.description ? ` • ${promptSet.description}` : ""}
                                        </p>
                                    </div>
                                    <span className="text-xs text-muted-foreground font-mono">
                                        {promptSet.prompt_set_id.slice(0, 8)}
                                    </span>
                                </div>
                                <div className="mt-4 space-y-3">
                                    {promptSet.items.map((item) => (
                                        <div key={item.prompt.prompt_id} className="border border-border rounded-lg p-4 bg-background/40">
                                            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                                                <span className="font-semibold text-foreground">{item.role}</span>
                                                <span className="px-2 py-0.5 rounded-full border border-border bg-secondary">
                                                    {item.prompt.kind}
                                                </span>
                                                <span className="font-mono">{item.prompt.checksum.slice(0, 12)}</span>
                                                {item.prompt.source && (
                                                    <span className="truncate max-w-[200px]">{item.prompt.source}</span>
                                                )}
                                            </div>
                                            {item.prompt.content && (
                                                <pre className="mt-2 text-xs text-muted-foreground whitespace-pre-wrap font-mono">
                                                    {previewPrompt(item.prompt.content)}
                                                </pre>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </>
                )}

                {activeTab === "performance" && (
                    /* Performance Tab Content */
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8 animate-in fade-in duration-300">
                        {/* Latency Analysis */}
                        <div className="surface-panel p-6">
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
                        <div className="surface-panel p-6">
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

                {activeTab === "feedback" && (
                    <div className="animate-in fade-in duration-300">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                            <div className="surface-panel p-6">
                                <h3 className="font-semibold text-muted-foreground text-sm mb-2">Avg. Satisfaction</h3>
                                <p className="text-3xl font-bold text-foreground">
                                    {summary.avg_satisfaction_score ? summary.avg_satisfaction_score.toFixed(2) : "N/A"}
                                    <span className="text-sm font-normal text-muted-foreground ml-2">/ 5.0</span>
                                </p>
                            </div>
                            <div className="surface-panel p-6">
                                <h3 className="font-semibold text-muted-foreground text-sm mb-2">Thumb Up Rate</h3>
                                <p className="text-3xl font-bold text-emerald-500">
                                    {summary.thumb_up_rate !== null && summary.thumb_up_rate !== undefined
                                        ? `${(summary.thumb_up_rate * 100).toFixed(1)}%`
                                        : "N/A"}
                                </p>
                            </div>
                            <div className="surface-panel p-6">
                                <h3 className="font-semibold text-muted-foreground text-sm mb-2">Imputed Ratio</h3>
                                <p className="text-3xl font-bold text-amber-500">
                                    {summary.imputed_ratio !== null && summary.imputed_ratio !== undefined
                                        ? `${(summary.imputed_ratio * 100).toFixed(1)}%`
                                        : "0.0%"}
                                </p>
                                <p className="text-xs text-muted-foreground mt-1">Cases with auto-calibrated feedback</p>
                            </div>
                        </div>

                        <div className="space-y-4">
                            {loadingFeedback ? (
                                <div className="text-center py-10 text-muted-foreground">Loading feedback...</div>
                            ) : (
                                results.map((result) => (
                                    <FeedbackItem
                                        key={result.test_case_id}
                                        result={result}
                                        feedback={feedbackMap[result.test_case_id]}
                                        onSave={handleSaveFeedback}
                                    />
                                ))
                            )}
                        </div>
                    </div>
                )}

                {activeTab !== "feedback" && (
                    <>
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
                                        <div className="flex items-center gap-2 mt-1">
                                            <p className="text-sm text-muted-foreground line-clamp-1">{result.answer}</p>
                                            {result.calibrated_satisfaction !== null && result.calibrated_satisfaction !== undefined && (
                                                <span className="shrink-0 px-1.5 py-0.5 rounded bg-secondary text-[10px] font-mono text-muted-foreground border border-border">
                                                    Satisf: {result.calibrated_satisfaction.toFixed(1)}
                                                </span>
                                            )}
                                        </div>
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
                                                    const isSummaryMetric = summaryMetricSet.has(metric.name as SummaryMetric);
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
                    </>
                )}
            </div>
        </Layout>
    );
}
