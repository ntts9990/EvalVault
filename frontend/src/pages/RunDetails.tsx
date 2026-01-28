import { useEffect, useState } from "react";
import { useParams, Link, useLocation } from "react-router-dom";
import {
    fetchRunDetails,
    fetchRunFeedback,
    saveRunFeedback,
    fetchRunFeedbackSummary,
    fetchStageEvents,
    fetchStageMetrics,
    fetchQualityGateReport,
    fetchDebugReport,
    fetchDebugReportMarkdown,
    fetchRuns,
    fetchPromptDiff,
    fetchAnalysisReport,
    fetchDashboard,
    type RunDetailsResponse,
    type FeedbackResponse,
    type StageEvent,
    type StageMetric,
    type QualityGateReportResponse,
    type DebugReport,
    type RunSummary,
    type PromptDiffResponse,
} from "../services/api";
import { Layout } from "../components/Layout";
import { InsightSpacePanel } from "../components/InsightSpacePanel";
import { MarkdownContent } from "../components/MarkdownContent";
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
    Layers,
    Terminal,
    ShieldCheck,
    Bug,
    Download,
    GitCompare,
    PieChart,
    AlertCircle
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { SUMMARY_METRICS, SUMMARY_METRIC_THRESHOLDS, type SummaryMetric } from "../utils/summaryMetrics";
import { buildRunCommand } from "../utils/cliCommandBuilder";
import { copyTextToClipboard } from "../utils/clipboard";


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
    const [activeTab, setActiveTab] = useState<
        "overview" | "performance" | "feedback" | "stages" | "prompts" | "gate" | "debug" | "report" | "dashboard"
    >("overview");
    const [expandedCases, setExpandedCases] = useState<Set<string>>(new Set());
    const [feedbackMap, setFeedbackMap] = useState<Record<string, FeedbackResponse>>({});
    const [loadingFeedback, setLoadingFeedback] = useState(false);
    const [stageEvents, setStageEvents] = useState<StageEvent[]>([]);
    const [stageMetrics, setStageMetrics] = useState<StageMetric[]>([]);
    const [stagesLoaded, setStagesLoaded] = useState(false);
    const [loadingStages, setLoadingStages] = useState(false);
    const [stageError, setStageError] = useState<string | null>(null);
    const [gateReport, setGateReport] = useState<QualityGateReportResponse | null>(null);
    const [gateLoaded, setGateLoaded] = useState(false);
    const [loadingGate, setLoadingGate] = useState(false);
    const [gateError, setGateError] = useState<string | null>(null);
    const [debugReport, setDebugReport] = useState<DebugReport | null>(null);
    const [debugLoaded, setDebugLoaded] = useState(false);
    const [loadingDebug, setLoadingDebug] = useState(false);
    const [debugError, setDebugError] = useState<string | null>(null);

    const [diffTargetRunId, setDiffTargetRunId] = useState<string>("");
    const [diffData, setDiffData] = useState<PromptDiffResponse | null>(null);
    const [loadingDiff, setLoadingDiff] = useState(false);
    const [diffError, setDiffError] = useState<string | null>(null);
    const [runList, setRunList] = useState<RunSummary[]>([]);
    const [runListLoaded, setRunListLoaded] = useState(false);
    const [runListError, setRunListError] = useState<string | null>(null);

    const [analysisReport, setAnalysisReport] = useState<string | null>(null);
    const [reportLoaded, setReportLoaded] = useState(false);
    const [loadingReport, setLoadingReport] = useState(false);
    const [reportError, setReportError] = useState<string | null>(null);

    const [dashboardUrl, setDashboardUrl] = useState<string | null>(null);
    const [dashboardLoaded, setDashboardLoaded] = useState(false);
    const [loadingDashboard, setLoadingDashboard] = useState(false);
    const [dashboardError, setDashboardError] = useState<string | null>(null);

    const [orderingWarnings, setOrderingWarnings] = useState<StageMetric[]>([]);
    const [loadingWarnings, setLoadingWarnings] = useState(false);
    const [copyCliStatus, setCopyCliStatus] = useState<"idle" | "success" | "error">("idle");

    const summaryMetricSet = new Set<string>(SUMMARY_METRICS);

    const previewPrompt = (content?: string) => {
        if (!content) return "";
        const lines = content.split("\n");
        const snippet = lines.slice(0, 4).join("\n");
        return lines.length > 4 ? `${snippet}\n...` : snippet;
    };

    const downloadJson = (filename: string, payload: unknown) => {
        const blob = new Blob([JSON.stringify(payload, null, 2)], {
            type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    };

    const downloadBlob = (filename: string, blob: Blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
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
        setStageEvents([]);
        setStageMetrics([]);
        setStagesLoaded(false);
        setStageError(null);
        setGateReport(null);
        setGateLoaded(false);
        setGateError(null);
        setDebugReport(null);
        setDebugLoaded(false);
        setDebugError(null);
        setDiffTargetRunId("");
        setDiffData(null);
        setDiffError(null);
        setAnalysisReport(null);
        setReportLoaded(false);
        setReportError(null);
        if (dashboardUrl) URL.revokeObjectURL(dashboardUrl);
        setDashboardUrl(null);
        setDashboardLoaded(false);
        setDashboardError(null);
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
        if (!id) return;

        if (activeTab === "stages" && !stagesLoaded && !loadingStages) {
            setLoadingStages(true);
            setStageError(null);
            Promise.all([fetchStageEvents(id), fetchStageMetrics(id)])
                .then(([events, metrics]) => {
                    setStageEvents(events);
                    setStageMetrics(metrics);
                    setStagesLoaded(true);
                })
                .catch((err) => {
                    setStageError(err instanceof Error ? err.message : "Failed to load stage data");
                })
                .finally(() => setLoadingStages(false));
        }

        if (activeTab === "gate" && !gateLoaded && !loadingGate) {
            setLoadingGate(true);
            setGateError(null);
            fetchQualityGateReport(id)
                .then((report) => {
                    setGateReport(report);
                    setGateLoaded(true);
                })
                .catch((err) => {
                    setGateError(err instanceof Error ? err.message : "Failed to load quality gate");
                })
                .finally(() => setLoadingGate(false));
        }

        if (activeTab === "debug" && !debugLoaded && !loadingDebug) {
            setLoadingDebug(true);
            setDebugError(null);
            fetchDebugReport(id)
                .then((report) => {
                    setDebugReport(report);
                    setDebugLoaded(true);
                })
                .catch((err) => {
                    setDebugError(err instanceof Error ? err.message : "Failed to load debug report");
                })
                .finally(() => setLoadingDebug(false));
        }

        if (activeTab === "report" && !reportLoaded && !loadingReport) {
            setLoadingReport(true);
            setReportError(null);
            fetchAnalysisReport(id)
                .then((report) => {
                    setAnalysisReport(report);
                    setReportLoaded(true);
                })
                .catch((err) => {
                    setReportError(err instanceof Error ? err.message : "Failed to load analysis report");
                    setReportLoaded(true);
                })
                .finally(() => setLoadingReport(false));
        }

        if (activeTab === "dashboard" && !dashboardLoaded && !loadingDashboard) {
            setLoadingDashboard(true);
            setDashboardError(null);
            fetchDashboard(id)
                .then((blob) => {
                    if (dashboardUrl) URL.revokeObjectURL(dashboardUrl);
                    const url = URL.createObjectURL(blob);
                    setDashboardUrl(url);
                    setDashboardLoaded(true);
                })
                .catch((err) => {
                    setDashboardError(err instanceof Error ? err.message : "Failed to load dashboard");
                    setDashboardLoaded(true);
                })
                .finally(() => setLoadingDashboard(false));
        }
    }, [
        activeTab,
        debugLoaded,
        gateLoaded,
        id,
        loadingDebug,
        loadingGate,
        loadingStages,
        stagesLoaded,
        reportLoaded,
        loadingReport,
        dashboardLoaded,
        loadingDashboard,
        dashboardUrl,
    ]);

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

    useEffect(() => {
        if (activeTab !== "prompts" || runListLoaded) return;
        setRunListError(null);
        fetchRuns()
            .then((runs) => {
                setRunList(runs);
                setRunListLoaded(true);
            })
            .catch((err) => {
                setRunListError(err instanceof Error ? err.message : "런 목록을 불러오지 못했습니다.");
                setRunListLoaded(true);
            });
    }, [activeTab, runListLoaded]);

    useEffect(() => {
        if (!id) return;
        setLoadingWarnings(true);
        fetchStageMetrics(id, undefined, "retrieval.ordering_warning")
            .then(setOrderingWarnings)
            .catch((err) => console.error("Failed to load ordering warnings", err))
            .finally(() => setLoadingWarnings(false));
    }, [id]);

    useEffect(() => {
        if (!id || !diffTargetRunId) return;
        setLoadingDiff(true);
        setDiffError(null);
        setDiffData(null);
        fetchPromptDiff(id, diffTargetRunId)
            .then(setDiffData)
            .catch((err) => setDiffError(err instanceof Error ? err.message : "Failed to load diff"))
            .finally(() => setLoadingDiff(false));
    }, [id, diffTargetRunId]);

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

    const handleCopyCli = async () => {
        if (!data) return;
        const { summary } = data;
        const summaryMode = summary.evaluation_task === "summarization";
        const command = buildRunCommand({
            dataset_path: summary.dataset_name || "<DATASET_PATH>",
            model: summary.model_name,
            metrics: summary.metrics_evaluated,
            summaryMode,
            run_mode: summary.run_mode || undefined,
            threshold_profile: summary.threshold_profile || undefined,
        });
        const success = await copyTextToClipboard(command);
        setCopyCliStatus(success ? "success" : "error");
        setTimeout(() => setCopyCliStatus("idle"), 1500);
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
            sourceLabel:
                metric === "summary_faithfulness" || metric === "summary_score" ? "LLM" : "Rule",
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
                        <button
                            onClick={handleCopyCli}
                            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-background hover:bg-secondary transition-colors text-xs font-medium"
                            title="Copy rerun command"
                        >
                            {copyCliStatus === "success" ? (
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                            ) : copyCliStatus === "error" ? (
                                <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                            ) : (
                                <Terminal className="w-3.5 h-3.5 text-muted-foreground" />
                            )}
                            {copyCliStatus === "success" ? "Copied!" : "Rerun CLI"}
                        </button>
                        <Link
                            to={`/visualization/${summary.run_id}`}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-colors"
                        >
                            <ExternalLink className="w-4 h-4" />
                            시각화 열기
                        </Link>
                        {/* Tab Navigation */}
                        <div className="tab-shell flex flex-wrap">
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
                            <button
                                onClick={() => setActiveTab("stages")}
                                className={`tab-pill flex items-center gap-1.5 ${activeTab === "stages" ? "tab-pill-active" : "tab-pill-inactive"}`}
                            >
                                <Layers className="w-3.5 h-3.5" />
                                Stages
                            </button>
                            <button
                                onClick={() => setActiveTab("prompts")}
                                className={`tab-pill flex items-center gap-1.5 ${activeTab === "prompts" ? "tab-pill-active" : "tab-pill-inactive"}`}
                            >
                                <Terminal className="w-3.5 h-3.5" />
                                Prompts
                            </button>
                            <button
                                onClick={() => setActiveTab("gate")}
                                className={`tab-pill flex items-center gap-1.5 ${activeTab === "gate" ? "tab-pill-active" : "tab-pill-inactive"}`}
                            >
                                <ShieldCheck className="w-3.5 h-3.5" />
                                Gate
                            </button>
                            <button
                                onClick={() => setActiveTab("debug")}
                                className={`tab-pill flex items-center gap-1.5 ${activeTab === "debug" ? "tab-pill-active" : "tab-pill-inactive"}`}
                            >
                                <Bug className="w-3.5 h-3.5" />
                                Debug
                            </button>
                            <button
                                onClick={() => setActiveTab("report")}
                                className={`tab-pill flex items-center gap-1.5 ${activeTab === "report" ? "tab-pill-active" : "tab-pill-inactive"}`}
                            >
                                <FileText className="w-3.5 h-3.5" />
                                Report
                            </button>
                            <button
                                onClick={() => setActiveTab("dashboard")}
                                className={`tab-pill flex items-center gap-1.5 ${activeTab === "dashboard" ? "tab-pill-active" : "tab-pill-inactive"}`}
                            >
                                <PieChart className="w-3.5 h-3.5" />
                                Dashboard
                            </button>
                        </div>

                        {(loadingWarnings || orderingWarnings.length > 0) && (
                            <div className="text-right group relative">
                                <p className="text-sm text-muted-foreground flex items-center gap-1 justify-end cursor-help">
                                    Ordering Warning
                                    <ShieldCheck className="w-3.5 h-3.5 text-muted-foreground" />
                                </p>
                                <p
                                    className="text-xl font-bold font-mono text-amber-500 cursor-help"
                                    title={(() => {
                                        if (loadingWarnings) return "Loading...";
                                        const reconstructed = orderingWarnings.filter(w => w.evidence?.order_reconstructed).length;
                                        const unordered = orderingWarnings.filter(w => w.evidence?.unordered_input).length;
                                        return `Total Warnings: ${orderingWarnings.length}\nOrder Reconstructed: ${reconstructed}\nUnordered (Raw): ${unordered}`;
                                    })()}
                                >
                                    {loadingWarnings
                                        ? "..."
                                        : `${((orderingWarnings.length / (summary.total_test_cases || 1)) * 100).toFixed(1)}%`}
                                </p>

                                <div className="absolute right-0 top-full mt-2 w-64 p-3 bg-popover border border-border rounded-lg shadow-xl z-50 hidden group-hover:block animate-in fade-in zoom-in-95 duration-200">
                                    <h4 className="font-semibold text-xs mb-2 flex items-center gap-1.5">
                                        <ShieldCheck className="w-3.5 h-3.5 text-primary" />
                                        Strict Mode Checklist
                                    </h4>
                                    <ul className="space-y-1.5">
                                        <li className="text-[10px] text-muted-foreground flex items-start gap-1.5">
                                            <span className="mt-0.5 w-1 h-1 rounded-full bg-primary flex-shrink-0" />
                                            <span>Recent 3 runs: Warning ratio &lt; 1%</span>
                                        </li>
                                        <li className="text-[10px] text-muted-foreground flex items-start gap-1.5">
                                            <span className="mt-0.5 w-1 h-1 rounded-full bg-primary flex-shrink-0" />
                                            <span>No recurring warnings in dataset</span>
                                        </li>
                                        <li className="text-[10px] text-muted-foreground flex items-start gap-1.5">
                                            <span className="mt-0.5 w-1 h-1 rounded-full bg-primary flex-shrink-0" />
                                            <span>Check label noise on transition</span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        )}

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
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                        <span>{row.metric}</span>
                                        {row.sourceLabel && (
                                            <span className="px-1.5 py-0.5 rounded-full border border-border text-[10px]">
                                                {row.sourceLabel}
                                            </span>
                                        )}
                                    </div>
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
                                                    {item.prompt.kind === "ragas"
                                                        ? "LLM"
                                                        : item.prompt.kind === "custom"
                                                            ? "Rule"
                                                            : item.prompt.kind}
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

                {activeTab === "stages" && (
                    <div className="space-y-6 animate-in fade-in duration-300">
                        <div className="surface-panel p-6">
                            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                                <h3 className="font-semibold flex items-center gap-2">
                                    <Layers className="w-4 h-4 text-primary" />
                                    Stage Events
                                </h3>
                                <button
                                    type="button"
                                    onClick={() => downloadJson(`stage_events_${summary.run_id}.json`, stageEvents)}
                                    disabled={stageEvents.length === 0}
                                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-xs font-semibold text-muted-foreground disabled:opacity-50"
                                >
                                    <Download className="w-3.5 h-3.5" />
                                    이벤트 다운로드
                                </button>
                            </div>
                            {loadingStages ? (
                                <div className="text-center py-8 text-muted-foreground">Stage 이벤트를 불러오는 중...</div>
                            ) : stageError ? (
                                <div className="text-center py-8 text-destructive">{stageError}</div>
                            ) : stageEvents.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">Stage 이벤트가 없습니다.</div>
                            ) : (
                                <div className="space-y-3">
                                    {stageEvents.map((event) => (
                                        <div
                                            key={`${event.stage_id}-${event.attempt}`}
                                            className="border border-border rounded-lg p-4 bg-background/40"
                                        >
                                            <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-semibold text-foreground">{event.stage_name || event.stage_type}</span>
                                                    <span className="text-xs text-muted-foreground font-mono">
                                                        {event.stage_type}
                                                    </span>
                                                    <span className="text-[10px] px-2 py-0.5 rounded-full border border-border bg-secondary text-muted-foreground">
                                                        {event.status}
                                                    </span>
                                                </div>
                                                <span className="text-xs text-muted-foreground font-mono">
                                                    {event.duration_ms != null ? `${event.duration_ms.toFixed(1)}ms` : "-"}
                                                </span>
                                            </div>
                                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-muted-foreground">
                                                <span className="font-mono">stage_id: {event.stage_id}</span>
                                                {event.parent_stage_id && (
                                                    <span className="font-mono">parent: {event.parent_stage_id}</span>
                                                )}
                                                {event.started_at && (
                                                    <span>start: {new Date(event.started_at).toLocaleString()}</span>
                                                )}
                                                {event.finished_at && (
                                                    <span>end: {new Date(event.finished_at).toLocaleString()}</span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="surface-panel p-6">
                            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                                <h3 className="font-semibold flex items-center gap-2">
                                    <Layers className="w-4 h-4 text-primary" />
                                    Stage Metrics
                                </h3>
                                <button
                                    type="button"
                                    onClick={() => downloadJson(`stage_metrics_${summary.run_id}.json`, stageMetrics)}
                                    disabled={stageMetrics.length === 0}
                                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-xs font-semibold text-muted-foreground disabled:opacity-50"
                                >
                                    <Download className="w-3.5 h-3.5" />
                                    메트릭 다운로드
                                </button>
                            </div>
                            {loadingStages ? (
                                <div className="text-center py-8 text-muted-foreground">Stage 메트릭을 불러오는 중...</div>
                            ) : stageMetrics.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">Stage 메트릭이 없습니다.</div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="text-xs text-muted-foreground border-b border-border">
                                            <tr>
                                                <th className="py-2 text-left">Stage</th>
                                                <th className="py-2 text-left">Metric</th>
                                                <th className="py-2 text-right">Score</th>
                                                <th className="py-2 text-right">Threshold</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-border/50">
                                            {stageMetrics.map((metric) => (
                                                <tr key={`${metric.stage_id}-${metric.metric_name}`}>
                                                    <td className="py-2 pr-2 font-mono text-xs text-muted-foreground">
                                                        {metric.stage_id}
                                                    </td>
                                                    <td className="py-2 pr-2 font-medium text-foreground">
                                                        {metric.metric_name}
                                                    </td>
                                                    <td className="py-2 text-right font-mono text-sm">
                                                        {metric.score.toFixed(3)}
                                                    </td>
                                                    <td className="py-2 text-right font-mono text-sm text-muted-foreground">
                                                        {metric.threshold != null ? metric.threshold.toFixed(3) : "-"}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === "prompts" && (
                    <div className="space-y-6 animate-in fade-in duration-300">
                        {!promptSet ? (
                            <div className="surface-panel p-8 text-center text-muted-foreground">
                                <Terminal className="w-8 h-8 mx-auto mb-3 opacity-30" />
                                프롬프트 스냅샷이 없습니다.
                            </div>
                        ) : (
                            <>
                                <div className="surface-panel p-6">
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
                                </div>
                                <div className="space-y-3">
                                    {promptSet.items.map((item) => (
                                        <div
                                            key={item.prompt.prompt_id}
                                            className="border border-border rounded-lg p-4 bg-background/40"
                                        >
                                            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                                                <span className="font-semibold text-foreground">{item.role}</span>
                                                <span className="px-2 py-0.5 rounded-full border border-border bg-secondary">
                                                    {item.prompt.kind === "ragas"
                                                        ? "LLM"
                                                        : item.prompt.kind === "custom"
                                                            ? "Rule"
                                                            : item.prompt.kind}
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
                            </>
                        )}

                        <div className="surface-panel p-6 mt-8 border-t border-border">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-semibold flex items-center gap-2">
                                    <GitCompare className="w-4 h-4 text-primary" />
                                    Prompt Diff
                                </h3>
                                <div className="flex flex-col items-end gap-2">
                                    <div className="flex items-center gap-2">
                                        <select
                                            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                            value={diffTargetRunId || ""}
                                            onChange={(e) => setDiffTargetRunId(e.target.value)}
                                        >
                                            <option value="" disabled>비교할 Run 선택...</option>
                                            {runList
                                                .filter((r) => r.run_id !== id)
                                                .map((r) => (
                                                    <option key={r.run_id} value={r.run_id}>
                                                        {r.run_id.slice(0, 8)} - {r.dataset_name} ({new Date(r.started_at).toLocaleDateString()})
                                                    </option>
                                                ))}
                                        </select>
                                        {diffData && (
                                            <button
                                                onClick={() => downloadJson(`prompt_diff_${id}_vs_${diffTargetRunId}.json`, diffData)}
                                                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-xs font-semibold text-muted-foreground hover:bg-secondary"
                                            >
                                                <Download className="w-3.5 h-3.5" />
                                                JSON
                                            </button>
                                        )}
                                    </div>
                                    {runListError && (
                                        <span className="text-xs text-rose-600">{runListError}</span>
                                    )}
                                </div>
                            </div>

                            {loadingDiff ? (
                                <div className="text-center py-8 text-muted-foreground">Loading diff...</div>
                            ) : diffError ? (
                                <div className="text-center py-8 text-destructive">{diffError}</div>
                            ) : diffData ? (
                                <div className="space-y-6">
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead className="text-xs text-muted-foreground border-b border-border">
                                                <tr>
                                                    <th className="py-2 text-left">Role</th>
                                                    <th className="py-2 text-left">Status</th>
                                                    <th className="py-2 text-left">Base (Current)</th>
                                                    <th className="py-2 text-left">Target</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-border/50">
                                                {diffData.summary.map((item, idx) => (
                                                    <tr key={idx}>
                                                        <td className="py-2 font-medium">{item.role}</td>
                                                        <td className="py-2">
                                                            <span
                                                                className={`px-2 py-0.5 rounded text-xs font-mono ${
                                                                    item.status === "diff"
                                                                        ? "bg-amber-500/10 text-amber-500"
                                                                        : item.status === "missing"
                                                                        ? "bg-rose-500/10 text-rose-500"
                                                                        : "bg-secondary text-muted-foreground"
                                                                }`}
                                                            >
                                                                {item.status.toUpperCase()}
                                                            </span>
                                                        </td>
                                                        <td className="py-2 text-xs font-mono text-muted-foreground">
                                                            {item.base_checksum?.slice(0, 8) || "-"}
                                                        </td>
                                                        <td className="py-2 text-xs font-mono text-muted-foreground">
                                                            {item.target_checksum?.slice(0, 8) || "-"}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>

                                    <div className="space-y-4">
                                        {diffData.diffs.map((diff, idx) => (
                                            <div key={idx} className="border border-border rounded-lg overflow-hidden">
                                                <div className="bg-secondary/30 px-4 py-2 text-xs font-semibold border-b border-border flex justify-between">
                                                    <span>{diff.role}</span>
                                                    {diff.truncated && <span className="text-amber-500">Truncated</span>}
                                                </div>
                                                <div className="p-4 bg-background overflow-x-auto">
                                                    <pre className="text-xs font-mono leading-relaxed">
                                                        {diff.lines.map((line, i) => (
                                                            <div
                                                                key={i}
                                                                className={`${
                                                                    line.startsWith("+")
                                                                        ? "bg-emerald-500/10 text-emerald-600"
                                                                        : line.startsWith("-")
                                                                        ? "bg-rose-500/10 text-rose-600"
                                                                        : line.startsWith("?")
                                                                        ? "bg-amber-500/10 text-amber-600"
                                                                        : "text-muted-foreground"
                                                                }`}
                                                            >
                                                                {line}
                                                            </div>
                                                        ))}
                                                    </pre>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-8 text-muted-foreground text-sm">
                                    비교할 Run을 선택하면 프롬프트 변경사항을 확인할 수 있습니다.
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === "gate" && (
                    <div className="surface-panel p-6 animate-in fade-in duration-300">
                        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                            <h3 className="font-semibold flex items-center gap-2">
                                <ShieldCheck className="w-4 h-4 text-primary" />
                                Quality Gate
                            </h3>
                            <button
                                type="button"
                                onClick={() => gateReport && downloadJson(`quality_gate_${summary.run_id}.json`, gateReport)}
                                disabled={!gateReport}
                                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-xs font-semibold text-muted-foreground disabled:opacity-50"
                            >
                                <Download className="w-3.5 h-3.5" />
                                게이트 다운로드
                            </button>
                        </div>
                        {loadingGate ? (
                            <div className="text-center py-8 text-muted-foreground">게이트 결과를 불러오는 중...</div>
                        ) : gateError ? (
                            <div className="text-center py-8 text-destructive">{gateError}</div>
                        ) : !gateReport ? (
                            <div className="text-center py-8 text-muted-foreground">게이트 결과가 없습니다.</div>
                        ) : (
                            <div className="space-y-4">
                                <div className="flex items-center gap-3">
                                    <span
                                        className={`px-2 py-1 rounded-full text-xs font-semibold border ${gateReport.overall_passed
                                            ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                                            : "bg-rose-500/10 text-rose-600 border-rose-500/20"
                                            }`}
                                    >
                                        {gateReport.overall_passed ? "PASS" : "FAIL"}
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                        Threshold Profile: {thresholdProfileLabel}
                                    </span>
                                    {gateReport.regression_detected && (
                                        <span className="text-xs text-rose-600">
                                            Regression {gateReport.regression_amount != null
                                                ? gateReport.regression_amount.toFixed(3)
                                                : "detected"}
                                        </span>
                                    )}
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="text-xs text-muted-foreground border-b border-border">
                                            <tr>
                                                <th className="py-2 text-left">Metric</th>
                                                <th className="py-2 text-right">Score</th>
                                                <th className="py-2 text-right">Threshold</th>
                                                <th className="py-2 text-right">Gap</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-border/50">
                                            {gateReport.results.map((item) => (
                                                <tr key={item.metric}>
                                                    <td className="py-2 font-medium text-foreground">{item.metric}</td>
                                                    <td
                                                        className={`py-2 text-right font-mono ${item.passed
                                                            ? "text-emerald-600"
                                                            : "text-rose-600"
                                                            }`}
                                                    >
                                                        {item.score.toFixed(3)}
                                                    </td>
                                                    <td className="py-2 text-right font-mono text-muted-foreground">
                                                        {item.threshold.toFixed(3)}
                                                    </td>
                                                    <td className="py-2 text-right font-mono text-muted-foreground">
                                                        {item.gap.toFixed(3)}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === "debug" && (
                    <div className="space-y-6 animate-in fade-in duration-300">
                        <div className="surface-panel p-6">
                            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                                <h3 className="font-semibold flex items-center gap-2">
                                    <Bug className="w-4 h-4 text-primary" />
                                    Debug Report
                                </h3>
                                <div className="flex items-center gap-2">
                                    <button
                                        type="button"
                                        onClick={() => debugReport && downloadJson(`debug_report_${summary.run_id}.json`, debugReport)}
                                        disabled={!debugReport}
                                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-xs font-semibold text-muted-foreground disabled:opacity-50"
                                    >
                                        <Download className="w-3.5 h-3.5" />
                                        JSON
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            if (!id) return;
                                            fetchDebugReportMarkdown(id)
                                                .then((blob) => downloadBlob(`debug_report_${summary.run_id}.md`, blob))
                                                .catch((err) => setDebugError(err instanceof Error ? err.message : "다운로드 실패"));
                                        }}
                                        disabled={!id}
                                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-xs font-semibold text-muted-foreground disabled:opacity-50"
                                    >
                                        <Download className="w-3.5 h-3.5" />
                                        Markdown
                                    </button>
                                </div>
                            </div>
                            {loadingDebug ? (
                                <div className="text-center py-8 text-muted-foreground">Debug 리포트를 생성 중...</div>
                            ) : debugError ? (
                                <div className="text-center py-8 text-destructive">{debugError}</div>
                            ) : !debugReport ? (
                                <div className="text-center py-8 text-muted-foreground">Debug 리포트가 없습니다.</div>
                            ) : (
                                <div className="space-y-6">
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <div className="bg-card border border-border rounded-xl p-4">
                                            <p className="text-xs text-muted-foreground mb-1">Total Events</p>
                                            <p className="text-2xl font-bold">
                                                {debugReport.stage_summary?.total_events ?? 0}
                                            </p>
                                        </div>
                                        <div className="bg-card border border-border rounded-xl p-4">
                                            <p className="text-xs text-muted-foreground mb-1">Bottlenecks</p>
                                            <p className="text-2xl font-bold">
                                                {debugReport.bottlenecks.length}
                                            </p>
                                        </div>
                                        <div className="bg-card border border-border rounded-xl p-4">
                                            <p className="text-xs text-muted-foreground mb-1">Recommendations</p>
                                            <p className="text-2xl font-bold">
                                                {debugReport.recommendations.length}
                                            </p>
                                        </div>
                                    </div>

                                    {debugReport.stage_summary?.missing_required_stage_types?.length ? (
                                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-700">
                                            누락된 Stage: {debugReport.stage_summary.missing_required_stage_types.join(", ")}
                                        </div>
                                    ) : null}

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="surface-panel p-4">
                                            <h4 className="text-sm font-semibold mb-2">Bottlenecks</h4>
                                            {debugReport.bottlenecks.length === 0 ? (
                                                <p className="text-xs text-muted-foreground">없음</p>
                                            ) : (
                                                <ul className="space-y-1 text-xs text-muted-foreground">
                                                    {debugReport.bottlenecks.map((item, index) => (
                                                        <li key={`${item.type ?? "b"}-${index}`}>
                                                            {JSON.stringify(item)}
                                                        </li>
                                                    ))}
                                                </ul>
                                            )}
                                        </div>
                                        <div className="surface-panel p-4">
                                            <h4 className="text-sm font-semibold mb-2">Recommendations</h4>
                                            {debugReport.recommendations.length === 0 ? (
                                                <p className="text-xs text-muted-foreground">없음</p>
                                            ) : (
                                                <ul className="space-y-1 text-xs text-muted-foreground">
                                                    {debugReport.recommendations.map((item, index) => (
                                                        <li key={`${item}-${index}`}>{item}</li>
                                                    ))}
                                                </ul>
                                            )}
                                        </div>
                                    </div>

                                    {(debugReport.phoenix_trace_url || debugReport.langfuse_trace_url) && (
                                        <div className="flex flex-wrap items-center gap-3 text-xs">
                                            {debugReport.phoenix_trace_url && (
                                                <a
                                                    href={debugReport.phoenix_trace_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-primary hover:underline"
                                                >
                                                    Phoenix Trace
                                                </a>
                                            )}
                                            {debugReport.langfuse_trace_url && (
                                                <a
                                                    href={debugReport.langfuse_trace_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-primary hover:underline"
                                                >
                                                    Langfuse Trace
                                                </a>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === "report" && (
                    <div className="surface-panel p-6 animate-in fade-in duration-300">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="font-semibold flex items-center gap-2">
                                <FileText className="w-4 h-4 text-primary" />
                                Analysis Report
                            </h3>
                            <button
                                onClick={() => {
                                    if (analysisReport) {
                                        const blob = new Blob([analysisReport], { type: "text/markdown" });
                                        downloadBlob(`analysis_report_${summary.run_id}.md`, blob);
                                    }
                                }}
                                disabled={!analysisReport}
                                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-xs font-semibold text-muted-foreground hover:bg-secondary disabled:opacity-50"
                            >
                                <Download className="w-3.5 h-3.5" />
                                Download Markdown
                            </button>
                        </div>

                        {loadingReport ? (
                            <div className="text-center py-10 text-muted-foreground">Loading report...</div>
                        ) : reportError ? (
                            <div className="text-center py-10 text-destructive">{reportError}</div>
                        ) : analysisReport ? (
                            <MarkdownContent text={analysisReport} />
                        ) : (
                            <div className="text-center py-10 text-muted-foreground">No report available.</div>
                        )}
                    </div>
                )}

                {activeTab === "dashboard" && (
                    <div className="surface-panel p-6 animate-in fade-in duration-300">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="font-semibold flex items-center gap-2">
                                <PieChart className="w-4 h-4 text-primary" />
                                Dashboard
                            </h3>
                            <button
                                onClick={() => {
                                    if (dashboardUrl) {
                                        const link = document.createElement("a");
                                        link.href = dashboardUrl;
                                        link.download = `dashboard_${summary.run_id}.png`;
                                        link.click();
                                    }
                                }}
                                disabled={!dashboardUrl}
                                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-xs font-semibold text-muted-foreground hover:bg-secondary disabled:opacity-50"
                            >
                                <Download className="w-3.5 h-3.5" />
                                Download Image
                            </button>
                        </div>

                        {loadingDashboard ? (
                            <div className="text-center py-10 text-muted-foreground">Loading dashboard...</div>
                        ) : dashboardError ? (
                            <div className="text-center py-10 text-destructive">{dashboardError}</div>
                        ) : dashboardUrl ? (
                            <div className="flex justify-center bg-white p-4 rounded-lg border border-border">
                                <img src={dashboardUrl} alt="Analysis Dashboard" className="max-w-full h-auto rounded shadow-sm" />
                            </div>
                        ) : (
                            <div className="text-center py-10 text-muted-foreground">No dashboard available.</div>
                        )}
                    </div>
                )}

                {(activeTab === "overview" || activeTab === "performance") && (
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
