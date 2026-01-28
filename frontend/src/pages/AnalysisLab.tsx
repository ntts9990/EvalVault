import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { AnalysisNodeOutputs } from "../components/AnalysisNodeOutputs";
import { MarkdownContent } from "../components/MarkdownContent";
import { PrioritySummaryPanel, type PrioritySummary } from "../components/PrioritySummaryPanel";
import { StatusBadge } from "../components/StatusBadge";
import { VirtualizedText } from "../components/VirtualizedText";
import {
    fetchConfig,
    fetchAnalysisIntents,
    fetchAnalysisHistory,
    fetchAnalysisMetricSpecs,
    fetchRuns,
    fetchImprovementGuide,
    fetchStageMetrics,
    runAnalysis,
    saveAnalysisResult,
    type AnalysisHistoryItem,
    type AnalysisIntentInfo,
    type AnalysisMetricSpec,
    type AnalysisResult,
    type ImprovementReport,
    type RunSummary,
    type StageMetric,
} from "../services/api";
import {
    ANALYSIS_LARGE_RAW_THRESHOLD,
    ANALYSIS_LARGE_REPORT_THRESHOLD,
    ANALYSIS_RAW_PREVIEW_LENGTH,
    ANALYSIS_REPORT_PREVIEW_LENGTH,
} from "../config/ui";
import { formatDateTime, formatDurationMs } from "../utils/format";
import {
    Activity,
    AlertCircle,
    CheckCircle2,
    Circle,
    Copy,
    ExternalLink,
    FileDiff,
    Link2,
    Play,
    Save,
    Terminal
} from "lucide-react";
import { buildAnalyzeCommand } from "../utils/cliCommandBuilder";
import { copyTextToClipboard } from "../utils/clipboard";

const CATEGORY_META: Record<string, { label: string; description: string }> = {
    verification: {
        label: "검증",
        description: "품질 검증과 신뢰성 점검",
    },
    comparison: {
        label: "비교",
        description: "모델/실행/검색 방식 비교",
    },
    analysis: {
        label: "분석",
        description: "패턴·원인·추세 분석",
    },
    report: {
        label: "보고서",
        description: "요약/상세/비교 리포트",
    },
    benchmark: {
        label: "벤치마크",
        description: "실제 문서 기반 검색 성능 측정",
    },
};

const API_STATUS_META: Record<string, { label: string; className: string }> = {
    loading: { label: "API 확인 중", className: "text-slate-600 bg-slate-100 border-slate-200" },
    ok: { label: "API 연결됨", className: "text-emerald-700 bg-emerald-50 border-emerald-200" },
    error: { label: "API 연결 실패", className: "text-rose-700 bg-rose-50 border-rose-200" },
};

const STEP_STATUS_COLORS: Record<string, string> = {
    completed: "bg-emerald-500",
    failed: "bg-rose-500",
    skipped: "bg-amber-500",
    running: "bg-blue-500",
    pending: "bg-slate-300",
};

const PRIORITY_META: Record<string, { label: string; color: string }> = {
    p0_critical: { label: "P0 Critical", color: "text-rose-600" },
    p1_high: { label: "P1 High", color: "text-amber-600" },
    p2_medium: { label: "P2 Medium", color: "text-yellow-600" },
    p3_low: { label: "P3 Low", color: "text-emerald-600" },
};

const EFFORT_LABEL: Record<string, string> = {
    low: "낮음",
    medium: "중간",
    high: "높음",
};

const RUN_REQUIRED_MODULES = new Set([
    "run_loader",
    "ragas_evaluator",
    "low_performer_extractor",
    "diagnostic_playbook",
    "root_cause_analyzer",
    "retrieval_analyzer",
    "retrieval_quality_checker",
    "bm25_searcher",
    "embedding_searcher",
    "hybrid_rrf",
    "hybrid_weighted",
    "search_comparator",
    "nlp_analyzer",
    "pattern_detector",
    "morpheme_analyzer",
    "morpheme_quality_checker",
    "embedding_analyzer",
    "embedding_distribution",
    "causal_analyzer",
    "model_analyzer",
    "run_analyzer",
    "run_comparator",
    "statistical_comparator",
    "time_series_analyzer",
    "trend_detector",
    "priority_summary",
]);

const SIGNAL_GROUP_LABELS: Record<string, string> = {
    groundedness: "근거성",
    intent_alignment: "질문-답변 정합성",
    retrieval_effectiveness: "검색 효과성",
    summary_fidelity: "요약 품질",
    embedding_quality: "임베딩 안정성",
    efficiency: "효율/지연",
};

const SIGNAL_GROUP_ORDER = [
    "groundedness",
    "intent_alignment",
    "retrieval_effectiveness",
    "summary_fidelity",
    "embedding_quality",
    "efficiency",
];

const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === "object" && value !== null;

const isPlainRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === "object" && value !== null && !Array.isArray(value);

const getNodeStatus = (node: unknown) => {
    if (!isRecord(node)) return "pending";
    const status = node.status;
    return typeof status === "string" ? status : "pending";
};

const getNodeError = (node: unknown) => {
    if (!isRecord(node)) return null;
    const error = node.error;
    if (typeof error === "string") return error;
    return error ? String(error) : null;
};

const getNodeOutput = (nodeResults: Record<string, unknown> | null | undefined, nodeId: string) => {
    if (!nodeResults) return null;
    const node = nodeResults[nodeId];
    if (!isRecord(node)) return null;
    return node.output;
};

function isPrioritySummary(value: unknown): value is PrioritySummary {
    if (!isPlainRecord(value)) return false;
    return Array.isArray(value.bottom_cases) || Array.isArray(value.impact_cases);
}

const PARAM_LABELS: Record<string, string> = {
    use_llm_report: "LLM 보고서",
    recompute_ragas: "RAGAS 재평가",
    benchmark_path: "벤치마크 경로",
    top_k: "top_k",
    ndcg_k: "ndcg_k",
    use_hybrid_search: "하이브리드 검색",
    embedding_profile: "임베딩 프로필",
};

const formatParamValue = (value: unknown) => {
    if (typeof value === "boolean") return value ? "예" : "아니오";
    if (typeof value === "number" && Number.isFinite(value)) return String(value);
    if (typeof value === "string") {
        return value.length > 80 ? `${value.slice(0, 80)}...` : value;
    }
    if (value === null || value === undefined) return "-";
    if (Array.isArray(value)) return value.map(item => String(item)).join(", ");
    if (isPlainRecord(value)) {
        try {
            return JSON.stringify(value);
        } catch {
            return "object";
        }
    }
    return String(value);
};

const collectNumericEntries = (record: Record<string, unknown>) =>
    Object.entries(record)
        .filter(([, value]) => typeof value === "number" && Number.isFinite(value))
        .map(([key, value]) => ({ key, value: value as number }));

const extractMetricEntries = (record: Record<string, unknown>) => {
    const metrics: { key: string; value: number }[] = [];
    const sources = [record.summary, record.metrics, record.scores];
    sources.forEach((source) => {
        if (isPlainRecord(source)) {
            metrics.push(...collectNumericEntries(source));
        }
    });
    return metrics;
};

const extractEvidenceRecords = (record: Record<string, unknown>) => {
    const candidates = [record.evidence, record.evidence_samples, record.samples];
    for (const candidate of candidates) {
        if (Array.isArray(candidate)) {
            return candidate.filter(isPlainRecord);
        }
    }
    return [];
};

const normalizeNumber = (value: unknown) => {
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string") {
        const parsed = Number(value);
        if (Number.isFinite(parsed)) return parsed;
    }
    return null;
};

const getNestedValue = (record: Record<string, unknown>, path: string[]) => {
    let current: unknown = record;
    for (const key of path) {
        if (!isPlainRecord(current)) return null;
        current = current[key];
    }
    return normalizeNumber(current);
};

type ExecutionMeta = {
    query: string;
    intent: string;
    runId: string | null;
    params: Record<string, unknown>;
};

type NextActionItem = {
    id: string;
    title: string;
    description: string;
    ctaLabel?: string;
    onClick?: () => void;
    disabled?: boolean;
};

export function AnalysisLab() {
    const [catalog, setCatalog] = useState<AnalysisIntentInfo[]>([]);
    const [catalogError, setCatalogError] = useState<string | null>(null);
    const [analysisMetricSpecs, setAnalysisMetricSpecs] = useState<AnalysisMetricSpec[]>([]);
    const [analysisMetricSpecError, setAnalysisMetricSpecError] = useState<string | null>(null);
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [runError, setRunError] = useState<string | null>(null);
    const [selectedRunId, setSelectedRunId] = useState<string>("");
    const [analysisRunId, setAnalysisRunId] = useState<string | null>(null);
    const [selectedIntent, setSelectedIntent] = useState<AnalysisIntentInfo | null>(null);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showRaw, setShowRaw] = useState(false);
    const [renderMarkdown, setRenderMarkdown] = useState(true);
    const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
    const [historyError, setHistoryError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [lastQuery, setLastQuery] = useState<string | null>(null);
    const [savedResultId, setSavedResultId] = useState<string | null>(null);
    const [showAnalysisMetrics, setShowAnalysisMetrics] = useState(false);
    const [saveProfile, setSaveProfile] = useState("");
    const [saveTags, setSaveTags] = useState("");
    const [saveMetadataText, setSaveMetadataText] = useState("");
    const [metadataError, setMetadataError] = useState<string | null>(null);
    const [useLlmReport, setUseLlmReport] = useState(true);
    const [recomputeRagas, setRecomputeRagas] = useState(false);
    const [executionMeta, setExecutionMeta] = useState<ExecutionMeta | null>(null);
    const [showFullReport, setShowFullReport] = useState(false);
    const [showFullRaw, setShowFullRaw] = useState(false);
    const [shareCopyStatus, setShareCopyStatus] = useState<"idle" | "success" | "error">("idle");
    const [shareLinkStatus, setShareLinkStatus] = useState<"idle" | "success" | "error">("idle");
    const [cliCopyStatus, setCliCopyStatus] = useState<"idle" | "success" | "error">("idle");
    const [showAllMetrics, setShowAllMetrics] = useState(false);
    const [benchmarkPath, setBenchmarkPath] = useState(
        "examples/benchmarks/korean_rag/retrieval_test.json"
    );
    const [benchmarkTopK, setBenchmarkTopK] = useState(5);
    const [benchmarkNdcgK, setBenchmarkNdcgK] = useState("");
    const [benchmarkUseHybrid, setBenchmarkUseHybrid] = useState(false);
    const [benchmarkEmbeddingProfile, setBenchmarkEmbeddingProfile] = useState("");
    const [historySearch, setHistorySearch] = useState("");
    const [intentFilter, setIntentFilter] = useState("all");
    const [runFilter, setRunFilter] = useState("all");
    const [profileFilter, setProfileFilter] = useState("all");
    const [dateFrom, setDateFrom] = useState("");
    const [dateTo, setDateTo] = useState("");
    const [sortOrder, setSortOrder] = useState("newest");
    const [compareSelection, setCompareSelection] = useState<string[]>([]);
    const [improvementReport, setImprovementReport] = useState<ImprovementReport | null>(null);
    const [improvementLoading, setImprovementLoading] = useState(false);
    const [improvementError, setImprovementError] = useState<string | null>(null);
    const [includeImprovementLlm, setIncludeImprovementLlm] = useState(false);
    const [apiStatus, setApiStatus] = useState<"loading" | "ok" | "error">("loading");
    const [apiError, setApiError] = useState<string | null>(null);

    const [orderingWarnings, setOrderingWarnings] = useState<StageMetric[]>([]);

    useEffect(() => {
        if (!selectedRunId) {
            setOrderingWarnings([]);
            return;
        }
        fetchStageMetrics(selectedRunId, undefined, "retrieval.ordering_warning")
            .then(setOrderingWarnings)
            .catch((err) => console.error("Failed to load ordering warnings", err));
    }, [selectedRunId]);

    useEffect(() => {
        async function loadCatalog() {
            try {
                const data = await fetchAnalysisIntents();
                setCatalog(data);
            } catch (err) {
                setCatalogError(err instanceof Error ? err.message : "Failed to load analysis catalog");
            }
        }
        loadCatalog();
    }, []);

    useEffect(() => {
        async function loadAnalysisMetricSpecs() {
            try {
                const data = await fetchAnalysisMetricSpecs();
                setAnalysisMetricSpecs(data);
            } catch (err) {
                setAnalysisMetricSpecError(
                    err instanceof Error ? err.message : "Failed to load analysis metric specs"
                );
            }
        }
        loadAnalysisMetricSpecs();
    }, []);

    const refreshApiStatus = useCallback(async () => {
        setApiStatus("loading");
        setApiError(null);
        try {
            await fetchConfig();
            setApiStatus("ok");
        } catch (err) {
            setApiStatus("error");
            setApiError(err instanceof Error ? err.message : "연결 실패");
        }
    }, []);

    useEffect(() => {
        refreshApiStatus();
    }, [refreshApiStatus]);

    useEffect(() => {
        async function loadRuns() {
            try {
                const data = await fetchRuns();
                setRuns(data);
            } catch (err) {
                setRunError(err instanceof Error ? err.message : "Failed to load runs");
            }
        }
        loadRuns();
    }, []);

    useEffect(() => {
        async function loadHistory() {
            try {
                const data = await fetchAnalysisHistory(20);
                setHistory(data);
            } catch (err) {
                setHistoryError(err instanceof Error ? err.message : "Failed to load history");
            }
        }
        loadHistory();
    }, []);

    useEffect(() => {
        if (!selectedRunId && recomputeRagas) {
            setRecomputeRagas(false);
        }
    }, [selectedRunId, recomputeRagas]);

    useEffect(() => {
        setImprovementReport(null);
        setImprovementError(null);
    }, [analysisRunId]);

    const groupedCatalog = useMemo(() => {
        const grouped: Record<string, AnalysisIntentInfo[]> = {};
        for (const item of catalog) {
            const key = item.category || "analysis";
            if (!grouped[key]) grouped[key] = [];
            grouped[key].push(item);
        }
        return grouped;
    }, [catalog]);

    const filteredHistory = useMemo(() => {
        const query = historySearch.trim().toLowerCase();
        const fromDate = dateFrom ? new Date(dateFrom) : null;
        const toDate = dateTo ? new Date(dateTo) : null;
        if (toDate) {
            toDate.setHours(23, 59, 59, 999);
        }

        let items = [...history];

        if (intentFilter !== "all") {
            items = items.filter(item => item.intent === intentFilter);
        }
        if (runFilter !== "all") {
            items = items.filter(item => (item.run_id || "sample") === runFilter);
        }
        if (profileFilter !== "all") {
            items = items.filter(item => (item.profile || "") === profileFilter);
        }
        if (fromDate) {
            items = items.filter(item => new Date(item.created_at) >= fromDate);
        }
        if (toDate) {
            items = items.filter(item => new Date(item.created_at) <= toDate);
        }
        if (query) {
            items = items.filter(item => {
                const haystack = [
                    item.label,
                    item.intent,
                    item.query || "",
                    item.run_id || "",
                    item.profile || "",
                    item.tags?.join(" ") || "",
                ]
                    .join(" ")
                    .toLowerCase();
                return haystack.includes(query);
            });
        }

        items.sort((a, b) => {
            if (sortOrder === "oldest") {
                return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
            }
            if (sortOrder === "duration_desc") {
                return (b.duration_ms ?? -1) - (a.duration_ms ?? -1);
            }
            if (sortOrder === "duration_asc") {
                return (a.duration_ms ?? -1) - (b.duration_ms ?? -1);
            }
            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });

        return items;
    }, [
        history,
        historySearch,
        intentFilter,
        runFilter,
        profileFilter,
        dateFrom,
        dateTo,
        sortOrder,
    ]);

    const recentHistory = useMemo(() => {
        const sorted = [...history].sort(
            (left, right) =>
                new Date(right.created_at).getTime() - new Date(left.created_at).getTime()
        );
        return sorted.slice(0, 3);
    }, [history]);

    const recentCompareLink = useMemo(() => {
        if (recentHistory.length < 2) return null;
        const [left, right] = recentHistory;
        return `/analysis/compare?left=${encodeURIComponent(left.result_id)}&right=${encodeURIComponent(right.result_id)}`;
    }, [recentHistory]);

    type ReportMeta = {
        hasReport: boolean;
        llmUsed: boolean | null;
        llmModel: string | null;
        llmError: string | null;
    };

    const reportMeta = useMemo<ReportMeta | null>(() => {
        if (!result?.final_output || !isPlainRecord(result.final_output)) return null;
        let hasReport = false;
        let llmUsed: boolean | null = null;
        let llmModel: string | null = null;
        let llmError: string | null = null;

        const scan = (value: unknown) => {
            if (!isRecord(value)) return;
            if (typeof value.report === "string") {
                hasReport = true;
            }
            if (typeof value.llm_used === "boolean") {
                llmUsed = value.llm_used;
            }
            if (typeof value.llm_model === "string") {
                llmModel = value.llm_model;
            }
            if (value.llm_error) {
                llmError = String(value.llm_error);
            }
        };

        Object.values(result.final_output).forEach(scan);

        return {
            hasReport,
            llmUsed,
            llmModel,
            llmError,
        };
    }, [result]);

    const reportBadge = useMemo(() => {
        if (!reportMeta?.hasReport) {
            return {
                label: "보고서 없음",
                className: "text-slate-600 bg-slate-100 border-slate-200",
            };
        }
        if (reportMeta.llmError) {
            return {
                label: "LLM 오류(대체 보고서)",
                className: "text-rose-700 bg-rose-50 border-rose-200",
            };
        }
        if (reportMeta.llmUsed === true) {
            return {
                label: "LLM 보고서 사용",
                className: "text-emerald-700 bg-emerald-50 border-emerald-200",
            };
        }
        if (reportMeta.llmUsed === false) {
            return {
                label: "LLM 보고서 미사용",
                className: "text-amber-700 bg-amber-50 border-amber-200",
            };
        }
        return {
            label: "기본 보고서",
            className: "text-slate-600 bg-slate-100 border-slate-200",
        };
    }, [reportMeta]);

    const reportErrorText = useMemo(() => {
        if (!reportMeta?.llmError) return null;
        if (reportMeta.llmError.length <= 120) return reportMeta.llmError;
        return `${reportMeta.llmError.slice(0, 120)}...`;
    }, [reportMeta]);

    const schemaIssues = useMemo(() => {
        if (!result) return [];
        const issues: string[] = [];
        if (result.final_output === null) {
            issues.push("final_output가 비어 있습니다.");
        } else if (!isPlainRecord(result.final_output)) {
            issues.push("final_output 형식이 예상과 다릅니다.");
        }
        if (!isPlainRecord(result.node_results)) {
            issues.push("node_results 형식이 예상과 다릅니다.");
        }
        return issues;
    }, [result]);

    const compareLink = useMemo(() => {
        if (compareSelection.length !== 2) return null;
        const [left, right] = compareSelection;
        return `/analysis/compare?left=${encodeURIComponent(left)}&right=${encodeURIComponent(right)}`;
    }, [compareSelection]);

    const promptDiffLink = useMemo(() => {
        if (compareSelection.length !== 2) return null;
        const [leftId, rightId] = compareSelection;
        const leftItem = history.find(item => item.result_id === leftId);
        const rightItem = history.find(item => item.result_id === rightId);

        if (!leftItem?.run_id || !rightItem?.run_id) return null;

        return `/compare?base=${encodeURIComponent(leftItem.run_id)}&target=${encodeURIComponent(rightItem.run_id)}`;
    }, [compareSelection, history]);

    const savedInCompare = useMemo(() => {
        if (!savedResultId) return false;
        return compareSelection.includes(savedResultId);
    }, [compareSelection, savedResultId]);

    const historyIntentOptions = useMemo(() => {
        const unique = new Map<string, string>();
        history.forEach(item => {
            if (!unique.has(item.intent)) {
                unique.set(item.intent, item.label);
            }
        });
        return Array.from(unique.entries()).map(([intent, label]) => ({ intent, label }));
    }, [history]);

    const historyRunOptions = useMemo(() => {
        const unique = new Set<string>();
        history.forEach(item => {
            unique.add(item.run_id || "sample");
        });
        return Array.from(unique.values());
    }, [history]);

    const historyProfileOptions = useMemo(() => {
        const unique = new Set<string>();
        history.forEach(item => {
            if (item.profile) {
                unique.add(item.profile);
            }
        });
        return Array.from(unique.values());
    }, [history]);

    const handleRun = async (intent: AnalysisIntentInfo) => {
        if (!intent.available || loading) return;
        const isBenchmark = intent.intent === "benchmark_retrieval";
        if (isBenchmark && !benchmarkPath.trim()) {
            setError("벤치마크 파일 경로를 입력하세요.");
            return;
        }
        const runIdForAnalysis = selectedRunId || null;
        setSelectedIntent(intent);
        setError(null);
        setSaveError(null);
        setResult(null);
        setSavedResultId(null);
        setLastQuery(intent.sample_query);
        setAnalysisRunId(runIdForAnalysis);
        setLoading(true);
        try {
            const params: Record<string, unknown> = {
                use_llm_report: useLlmReport,
            };
            if (recomputeRagas && runIdForAnalysis) {
                params.recompute_ragas = true;
            }
            if (isBenchmark) {
                params.benchmark_path = benchmarkPath.trim();
                params.top_k = benchmarkTopK;
                if (benchmarkNdcgK.trim()) {
                    const ndcgValue = Number(benchmarkNdcgK);
                    if (!Number.isNaN(ndcgValue) && ndcgValue > 0) {
                        params.ndcg_k = ndcgValue;
                    }
                }
                params.use_hybrid_search = benchmarkUseHybrid;
                if (benchmarkEmbeddingProfile.trim()) {
                    params.embedding_profile = benchmarkEmbeddingProfile.trim();
                }
            }
            setExecutionMeta({
                query: intent.sample_query,
                intent: intent.intent,
                runId: runIdForAnalysis,
                params,
            });
            const analysis = await runAnalysis(
                intent.sample_query,
                runIdForAnalysis || undefined,
                intent.intent,
                params
            );
            setResult(analysis);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Analysis failed");
        } finally {
            setLoading(false);
        }
    };

    const handleSave = useCallback(async () => {
        if (!result || saving) return;
        setSaving(true);
        setSaveError(null);
        setMetadataError(null);
        try {
            let metadata: unknown = null;
            if (saveMetadataText.trim()) {
                try {
                    metadata = JSON.parse(saveMetadataText);
                } catch {
                    setMetadataError("메타데이터 JSON 형식이 올바르지 않습니다.");
                    setSaving(false);
                    return;
                }
            }
            const tags = saveTags
                .split(",")
                .map(tag => tag.trim())
                .filter(tag => tag.length > 0);
            const payload = {
                intent: result.intent,
                query: lastQuery || selectedIntent?.sample_query || result.intent,
                run_id: analysisRunId,
                pipeline_id: result.pipeline_id || null,
                profile: saveProfile.trim() ? saveProfile.trim() : null,
                tags: tags.length > 0 ? tags : null,
                metadata: metadata,
                is_complete: result.is_complete,
                duration_ms: result.duration_ms,
                final_output: result.final_output,
                node_results: result.node_results,
                started_at: result.started_at || null,
                finished_at: result.finished_at || null,
            };
            const saved = await saveAnalysisResult(payload);
            setSavedResultId(saved.result_id);
            setHistory(prev => [saved, ...prev.filter(item => item.result_id !== saved.result_id)]);
        } catch (err) {
            setSaveError(err instanceof Error ? err.message : "Failed to save analysis result");
        } finally {
            setSaving(false);
        }
    }, [
        analysisRunId,
        lastQuery,
        result,
        saveMetadataText,
        saveProfile,
        saveTags,
        saving,
        selectedIntent?.sample_query,
    ]);

    const handleLoadImprovement = async () => {
        if (!analysisRunId || improvementLoading) return;
        setImprovementLoading(true);
        setImprovementError(null);
        try {
            const report = await fetchImprovementGuide(analysisRunId, includeImprovementLlm);
            setImprovementReport(report);
        } catch (err) {
            setImprovementError(err instanceof Error ? err.message : "개선 가이드 로드 실패");
        } finally {
            setImprovementLoading(false);
        }
    };

    const toggleCompareSelection = useCallback((resultId: string) => {
        setCompareSelection(prev => {
            if (prev.includes(resultId)) {
                return prev.filter(id => id !== resultId);
            }
            if (prev.length >= 2) {
                return [prev[1], resultId];
            }
            return [...prev, resultId];
        });
    }, []);

    const clearCompareSelection = () => {
        setCompareSelection([]);
    };

    const resetHistoryFilters = () => {
        setHistorySearch("");
        setIntentFilter("all");
        setRunFilter("all");
        setProfileFilter("all");
        setDateFrom("");
        setDateTo("");
        setSortOrder("newest");
    };

    const safeNodeResults = useMemo(() => {
        if (!result?.node_results || !isPlainRecord(result.node_results)) return null;
        return result.node_results;
    }, [result]);

    const resultSummary = useMemo(() => {
        if (!result || !safeNodeResults) return null;
        const nodeResults = safeNodeResults;
        const counts = {
            completed: 0,
            failed: 0,
            skipped: 0,
            running: 0,
            pending: 0,
        };
        Object.values(nodeResults).forEach((node) => {
            const status = getNodeStatus(node);
            if (counts[status as keyof typeof counts] !== undefined) {
                counts[status as keyof typeof counts] += 1;
            }
        });
        return counts;
    }, [result, safeNodeResults]);

    const resultSummaryTotal = useMemo(() => {
        if (!resultSummary) return 0;
        return Object.values(resultSummary).reduce((sum, value) => sum + value, 0);
    }, [resultSummary]);

    const reportText = useMemo(() => {
        if (!result?.final_output || !isPlainRecord(result.final_output)) return null;
        const reportEntry = (result.final_output as Record<string, unknown>).report;
        if (isRecord(reportEntry) && typeof reportEntry.report === "string") {
            return reportEntry.report;
        }
        const entries = Object.values(result.final_output);
        for (const entry of entries) {
            if (isRecord(entry) && typeof entry.report === "string") {
                return entry.report;
            }
        }
        return null;
    }, [result]);

    const rawOutput = useMemo(() => {
        if (!result?.final_output) return null;
        try {
            return JSON.stringify(result.final_output, null, 2);
        } catch {
            return null;
        }
    }, [result]);

    const reportIsLarge = (reportText?.length ?? 0) > ANALYSIS_LARGE_REPORT_THRESHOLD;
    const rawIsLarge = (rawOutput?.length ?? 0) > ANALYSIS_LARGE_RAW_THRESHOLD;
    const reportPreview = reportText && reportIsLarge
        ? `${reportText.slice(0, ANALYSIS_REPORT_PREVIEW_LENGTH)}...`
        : reportText;
    const rawPreview = rawOutput && rawIsLarge
        ? `${rawOutput.slice(0, ANALYSIS_RAW_PREVIEW_LENGTH)}...`
        : rawOutput;

    useEffect(() => {
        if (!reportIsLarge) {
            setRenderMarkdown(true);
        } else {
            setRenderMarkdown(false);
        }
    }, [reportIsLarge, reportText]);

    useEffect(() => {
        setShowFullReport(false);
        setShowFullRaw(false);
    }, [reportText, rawOutput]);

    useEffect(() => {
        if (!showRaw) {
            setShowFullRaw(false);
        }
    }, [showRaw]);

    const copyToClipboard = useCallback(
        async (text: string, mode: "summary" | "link") => {
            if (typeof window === "undefined") return;
            const setStatus = mode === "summary" ? setShareCopyStatus : setShareLinkStatus;
            const success = await copyTextToClipboard(text);
            setStatus(success ? "success" : "error");
            setTimeout(() => setStatus("idle"), 1500);
        },
        [setShareCopyStatus, setShareLinkStatus]
    );

    const handleCopyCli = async () => {
        if (!executionMeta) return;
        const command = buildAnalyzeCommand({
            query: executionMeta.query,
            run_id: executionMeta.runId || undefined,
            intent: executionMeta.intent,
        });
        const success = await copyTextToClipboard(command);
        setCliCopyStatus(success ? "success" : "error");
        setTimeout(() => setCliCopyStatus("idle"), 1500);
    };

    const intentLabel = selectedIntent?.label
        || catalog.find(item => item.intent === result?.intent)?.label
        || result?.intent
        || "분석";

    const intentDefinition = selectedIntent || catalog.find(item => item.intent === result?.intent) || null;
    const requiresRunData = useMemo(() => {
        const nodes = intentDefinition?.nodes || selectedIntent?.nodes || [];
        return nodes.some(node => RUN_REQUIRED_MODULES.has(node.module));
    }, [intentDefinition, selectedIntent]);

    const prioritySummary = useMemo(() => {
        if (!result) return null;
        const finalOutput = isPlainRecord(result.final_output) ? result.final_output : null;
        if (!finalOutput) return null;
        for (const entry of Object.values(finalOutput)) {
            if (isPrioritySummary(entry)) return entry;
        }
        const nodeOutput = getNodeOutput(safeNodeResults, "priority_summary");
        if (isPrioritySummary(nodeOutput)) return nodeOutput;
        return null;
    }, [result, safeNodeResults]);

    const hasNodeError = useMemo(() => {
        if (!safeNodeResults) return false;
        return Object.values(safeNodeResults).some((node) => Boolean(getNodeError(node)));
    }, [safeNodeResults]);

    const nodeErrorSummary = useMemo(() => {
        if (!safeNodeResults) return null;
        const nodes = intentDefinition?.nodes || [];
        const nameMap = new Map(nodes.map((node) => [node.id, node.name]));
        const errors = Object.entries(safeNodeResults)
            .map(([nodeId, nodeValue]) => {
                const error = getNodeError(nodeValue);
                if (!error) return null;
                return {
                    id: nodeId,
                    name: nameMap.get(nodeId) || nodeId,
                    error,
                };
            })
            .filter((item): item is { id: string; name: string; error: string } => Boolean(item));
        if (!errors.length) return null;
        return {
            total: errors.length,
            preview: errors.slice(0, 3),
        };
    }, [intentDefinition, safeNodeResults]);

    const metricDistributions = useMemo(() => {
        if (!result) return [];
        const map = new Map<string, number[]>();
        const addMetric = (key: string, value: number) => {
            if (!map.has(key)) {
                map.set(key, []);
            }
            map.get(key)?.push(value);
        };

        const scanRecord = (record: Record<string, unknown>) => {
            extractEvidenceRecords(record).forEach((item) => {
                const metrics =
                    (isPlainRecord(item.metrics) && item.metrics)
                    || (isPlainRecord(item.scores) && item.scores);
                if (!metrics) return;
                collectNumericEntries(metrics).forEach(({ key, value }) => {
                    addMetric(key, value);
                });
            });
        };

        if (isPlainRecord(result.final_output)) {
            scanRecord(result.final_output);
            Object.values(result.final_output).forEach((value) => {
                if (isPlainRecord(value)) {
                    scanRecord(value);
                }
            });
        }

        if (safeNodeResults) {
            Object.values(safeNodeResults).forEach((node) => {
                if (!isPlainRecord(node)) return;
                const output = node.output;
                if (isPlainRecord(output)) {
                    scanRecord(output);
                }
            });
        }

        return Array.from(map.entries())
            .map(([key, values]) => {
                const min = Math.min(...values);
                const max = Math.max(...values);
                const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
                return {
                    key,
                    min,
                    max,
                    avg,
                    count: values.length,
                };
            })
            .sort((left, right) => right.count - left.count);
    }, [result, safeNodeResults]);

    const keyMetricEntries = useMemo(() => {
        if (!result) return [];
        const entries: { key: string; value: number }[] = [];
        const seen = new Set<string>();

        const addEntries = (items: { key: string; value: number }[]) => {
            items.forEach((item) => {
                if (seen.has(item.key)) return;
                seen.add(item.key);
                entries.push(item);
            });
        };

        if (isPlainRecord(result.final_output)) {
            addEntries(extractMetricEntries(result.final_output));
            Object.values(result.final_output).forEach((value) => {
                if (isPlainRecord(value)) {
                    addEntries(extractMetricEntries(value));
                }
            });
        }

        if (safeNodeResults) {
            Object.values(safeNodeResults).forEach((node) => {
                if (!isPlainRecord(node)) return;
                const output = node.output;
                if (isPlainRecord(output)) {
                    addEntries(extractMetricEntries(output));
                }
            });
        }

        return entries.slice(0, 3);
    }, [result, safeNodeResults]);

    const analysisMetricGroups = useMemo(() => {
        if (!analysisMetricSpecs.length || !safeNodeResults || !intentDefinition) return [];
        const moduleNodes = new Map<string, string[]>();
        intentDefinition.nodes.forEach((node) => {
            const list = moduleNodes.get(node.module) || [];
            list.push(node.id);
            moduleNodes.set(node.module, list);
        });

        const groupMap = new Map<
            string,
            {
                id: string;
                label: string;
                items: { spec: AnalysisMetricSpec; value: number; nodeId: string }[];
            }
        >();

        analysisMetricSpecs.forEach((spec) => {
            const nodeIds = moduleNodes.get(spec.module_id) || [];
            nodeIds.forEach((nodeId) => {
                const node = safeNodeResults[nodeId];
                if (!isPlainRecord(node)) return;
                const output = node.output;
                if (!isPlainRecord(output)) return;
                const value = getNestedValue(output, spec.output_path);
                if (value === null) return;

                const groupId = spec.signal_group;
                const label = SIGNAL_GROUP_LABELS[groupId] || groupId;
                if (!groupMap.has(groupId)) {
                    groupMap.set(groupId, { id: groupId, label, items: [] });
                }
                groupMap.get(groupId)?.items.push({ spec, value, nodeId });
            });
        });

        const orderIndex = new Map(
            SIGNAL_GROUP_ORDER.map((group, index) => [group, index])
        );

        return Array.from(groupMap.values())
            .map((group) => ({
                ...group,
                items: group.items.sort((a, b) => a.spec.label.localeCompare(b.spec.label)),
            }))
            .sort((left, right) => {
                const leftOrder = orderIndex.get(left.id) ?? 999;
                const rightOrder = orderIndex.get(right.id) ?? 999;
                return leftOrder - rightOrder;
            });
    }, [analysisMetricSpecs, intentDefinition, safeNodeResults]);

    const metricPreview = useMemo(() => {
        if (metricDistributions.length <= 6) return metricDistributions;
        return showAllMetrics ? metricDistributions : metricDistributions.slice(0, 6);
    }, [metricDistributions, showAllMetrics]);

    const executionParamEntries = useMemo(() => {
        if (!executionMeta) return [];
        const entries: { label: string; value: string }[] = [
            { label: "쿼리", value: executionMeta.query },
            { label: "Intent", value: intentLabel },
            {
                label: "Run",
                value: executionMeta.runId ? `Run ${executionMeta.runId.slice(0, 8)}` : "샘플 데이터",
            },
        ];
        Object.entries(executionMeta.params).forEach(([key, value]) => {
            const label = PARAM_LABELS[key] || key;
            entries.push({ label, value: formatParamValue(value) });
        });
        return entries;
    }, [executionMeta, intentLabel]);

    const nextActions = useMemo<NextActionItem[]>(() => {
        if (!result) return [];
        const actions: NextActionItem[] = [];

        if (!savedResultId) {
            actions.push({
                id: "save-result",
                title: "결과 저장",
                description: "이번 결과를 저장해 비교와 추적에 활용하세요.",
                ctaLabel: saving ? "저장 중..." : "저장하기",
                onClick: () => {
                    void handleSave();
                },
                disabled: saving,
            });
        }

        if (!analysisRunId) {
            actions.push({
                id: "choose-run",
                title: "실제 Run 선택",
                description: "Run을 선택하면 실제 평가 데이터를 기반으로 분석합니다.",
            });
        }

        if (reportErrorText) {
            actions.push({
                id: "llm-check",
                title: "LLM 설정 확인",
                description: "LLM 오류가 발생했습니다. 모델/키 설정을 확인하세요.",
            });
        }

        if (hasNodeError) {
            actions.push({
                id: "node-errors",
                title: "오류 노드 점검",
                description: "실행 단계 또는 노드 상세 출력에서 오류 원인을 확인하세요.",
            });
        }

        if (savedResultId && compareSelection.length < 2) {
            actions.push({
                id: "compare-ready",
                title: "비교 준비",
                description: "다른 결과 1개를 추가하면 비교가 가능합니다.",
                ctaLabel: savedInCompare ? "비교에서 제거" : "비교에 추가",
                onClick: () => toggleCompareSelection(savedResultId),
            });
        }

        return actions.slice(0, 3);
    }, [
        analysisRunId,
        compareSelection.length,
        hasNodeError,
        handleSave,
        reportErrorText,
        result,
        savedInCompare,
        savedResultId,
        saving,
        toggleCompareSelection,
    ]);

    const shareSummaryText = useMemo(() => {
        if (!result) return "";
        const lines = [
            `[EvalVault] ${intentLabel} 분석 결과`,
            `상태: ${result.is_complete ? "완료" : "미완료"}`,
            `처리 시간: ${formatDurationMs(result.duration_ms)}`,
            `Run: ${analysisRunId ? `Run ${analysisRunId.slice(0, 8)}` : "샘플 데이터"}`,
            `보고서: ${reportBadge.label}`,
        ];
        if (keyMetricEntries.length > 0) {
            lines.push(
                `주요 지표: ${keyMetricEntries
                    .map((entry) => `${entry.key} ${entry.value.toFixed(3)}`)
                    .join(", ")}`
            );
        }
        if (nodeErrorSummary) {
            lines.push(`오류: ${nodeErrorSummary.total}건`);
        }
        return lines.join("\n");
    }, [analysisRunId, intentLabel, keyMetricEntries, nodeErrorSummary, reportBadge, result]);

    return (
        <Layout>
            <div className="max-w-6xl mx-auto pb-20">
                <div className="mb-8 space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight mb-2 font-display">분석 실험실</h1>
                            <p className="text-muted-foreground">
                                분석 클래스를 선택해 바로 실행하고 결과를 확인하세요.
                            </p>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                            <span
                                className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-medium ${API_STATUS_META[apiStatus].className}`}
                            >
                                {API_STATUS_META[apiStatus].label}
                            </span>
                            {apiStatus === "error" && (
                                <button
                                    type="button"
                                    onClick={refreshApiStatus}
                                    className="text-xs text-muted-foreground hover:text-foreground"
                                >
                                    재시도
                                </button>
                            )}
                        </div>
                    </div>
                    {apiStatus === "error" && apiError && (
                        <p className="text-xs text-rose-600">
                            API 연결 실패: {apiError}
                        </p>
                    )}
                </div>

                {catalogError && (
                    <div className="mb-6 p-4 border border-destructive/30 bg-destructive/10 rounded-xl text-destructive flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        <span>{catalogError}</span>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-1 space-y-6">
                        <div className="bg-card border border-border rounded-xl p-4 shadow-sm">
                            <h3 className="font-semibold mb-3 flex items-center gap-2">
                                <Activity className="w-4 h-4 text-primary" /> 실행 대상 선택
                            </h3>
                            <label className="text-xs text-muted-foreground">평가 Run</label>
                            <select
                                value={selectedRunId}
                                onChange={(e) => setSelectedRunId(e.target.value)}
                                className="mt-2 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
                            >
                                <option value="">샘플 데이터 사용</option>
                                {runs.map((run) => {
                                    const profileLabel = run.threshold_profile
                                        ? run.threshold_profile.toUpperCase()
                                        : "DEFAULT";
                                    return (
                                        <option key={run.run_id} value={run.run_id}>
                                            {run.dataset_name} · {run.model_name} · {profileLabel} · {run.run_id.slice(0, 8)}
                                        </option>
                                    );
                                })}
                            </select>
                            {runError && (
                                <p className="text-xs text-destructive mt-2">{runError}</p>
                            )}

                            {orderingWarnings.length > 0 && (
                                <div className="mt-3 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-xs text-amber-600">
                                    <div className="flex items-center gap-2 mb-1 font-semibold">
                                        <AlertCircle className="w-3.5 h-3.5" />
                                        Ordering Warning Detected
                                    </div>
                                    <p>
                                        이 Run에는 검색 순서 경고가 {orderingWarnings.length}건 있습니다.
                                        점수에 영향을 줄 수 있습니다.
                                        <a
                                            href="https://github.com/ntts9990/EvalVault/blob/main/docs/guides/RAG_NOISE_REDUCTION_GUIDE.md#35-ordering_warning-%EB%9F%B0%EB%B6%81%EB%B9%84%EC%9C%A8%EB%B6%84%ED%8F%AC-%ED%99%95%EC%9D%B8"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="underline font-semibold ml-2 hover:text-amber-800 inline-flex items-center gap-0.5"
                                        >
                                            런북 보기 <ExternalLink className="w-3 h-3" />
                                        </a>
                                    </p>
                                </div>
                            )}

                        {!selectedRunId && (
                            <p className="text-xs text-muted-foreground mt-3">
                                Run을 선택하지 않으면 샘플 메트릭 기반으로 분석합니다.
                            </p>
                        )}
                        {!selectedRunId && selectedIntent && requiresRunData && (
                            <p className="text-xs text-amber-600 mt-2">
                                선택한 인텐트는 Run 데이터가 필요합니다. 샘플 모드에서는 결과가
                                제한될 수 있습니다.
                            </p>
                        )}
                            <div className="mt-4 space-y-2 text-xs">
                                <label className="flex items-center gap-2 text-muted-foreground">
                                    <input
                                        type="checkbox"
                                        className="accent-primary"
                                        checked={useLlmReport}
                                        onChange={(e) => setUseLlmReport(e.target.checked)}
                                    />
                                    LLM 보고서 사용 (증거 인용 포함)
                                </label>
                                <label className="flex items-center gap-2 text-muted-foreground">
                                    <input
                                        type="checkbox"
                                        className="accent-primary"
                                        checked={recomputeRagas}
                                        disabled={!selectedRunId}
                                        onChange={(e) => setRecomputeRagas(e.target.checked)}
                                    />
                                    RAGAS 재평가 실행 (오래 걸릴 수 있음)
                                </label>
                                {!selectedRunId && (
                                    <p className="text-[11px] text-muted-foreground">
                                        RAGAS 재평가는 Run 선택 시 활성화됩니다.
                                    </p>
                                )}
                            </div>
                            {selectedIntent?.intent === "benchmark_retrieval" && (
                                <div className="mt-4 space-y-3 text-xs">
                                    <label className="text-muted-foreground">
                                        벤치마크 파일 경로
                                        <input
                                            type="text"
                                            value={benchmarkPath}
                                            onChange={(event) => setBenchmarkPath(event.target.value)}
                                            placeholder="examples/benchmarks/korean_rag/retrieval_test.json"
                                            className="mt-2 w-full bg-background border border-border rounded-lg px-3 py-2 text-xs"
                                        />
                                    </label>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                        <label className="text-muted-foreground">
                                            top_k
                                            <input
                                                type="number"
                                                min={1}
                                                value={benchmarkTopK}
                                                onChange={(event) => setBenchmarkTopK(Number(event.target.value))}
                                                className="mt-2 w-full bg-background border border-border rounded-lg px-3 py-2 text-xs"
                                            />
                                        </label>
                                        <label className="text-muted-foreground">
                                            ndcg_k (선택)
                                            <input
                                                type="number"
                                                min={1}
                                                value={benchmarkNdcgK}
                                                onChange={(event) => setBenchmarkNdcgK(event.target.value)}
                                                className="mt-2 w-full bg-background border border-border rounded-lg px-3 py-2 text-xs"
                                            />
                                        </label>
                                    </div>
                                    <label className="flex items-center gap-2 text-muted-foreground">
                                        <input
                                            type="checkbox"
                                            className="accent-primary"
                                            checked={benchmarkUseHybrid}
                                            onChange={(event) => setBenchmarkUseHybrid(event.target.checked)}
                                        />
                                        하이브리드 검색 사용 (BM25 + Dense)
                                    </label>
                                    <label className="text-muted-foreground">
                                        임베딩 프로필 (dev/prod)
                                        <input
                                            type="text"
                                            value={benchmarkEmbeddingProfile}
                                            onChange={(event) => setBenchmarkEmbeddingProfile(event.target.value)}
                                            placeholder="dev"
                                            className="mt-2 w-full bg-background border border-border rounded-lg px-3 py-2 text-xs"
                                        />
                                    </label>
                                </div>
                            )}
                        </div>

                        <div className="bg-card border border-border rounded-xl p-4 shadow-sm">
                            <div className="flex items-start justify-between gap-3 mb-3">
                                <h3 className="font-semibold flex items-center gap-2">
                                    <Activity className="w-4 h-4 text-primary" /> 저장된 결과
                                </h3>
                                <div className="flex flex-wrap items-center gap-2">
                                    <span className="text-[11px] text-muted-foreground">
                                        선택 {compareSelection.length}/2
                                    </span>
                                    {compareLink ? (
                                        <Link
                                            to={compareLink}
                                            className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded-md border border-border hover:border-primary/40"
                                        >
                                            비교 보기
                                        </Link>
                                    ) : (
                                        <button
                                            type="button"
                                            disabled
                                            className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded-md border border-border text-muted-foreground opacity-60"
                                        >
                                            비교 보기
                                        </button>
                                    )}
                                    {promptDiffLink && (
                                        <Link
                                            to={promptDiffLink}
                                            className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded-md border border-border hover:border-primary/40"
                                        >
                                            <FileDiff className="w-3 h-3" />
                                            프롬프트 비교
                                        </Link>
                                    )}
                                    {compareSelection.length > 0 && (
                                        <button
                                            type="button"
                                            onClick={clearCompareSelection}
                                            className="text-[11px] text-muted-foreground hover:text-foreground"
                                        >
                                            선택 해제
                                        </button>
                                    )}
                                    {promptDiffLink && (
                                        <Link
                                            to={promptDiffLink}
                                            className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded-md border border-border hover:border-primary/40"
                                        >
                                            <FileDiff className="w-3 h-3" />
                                            프롬프트 비교
                                        </Link>
                                    )}
                                    {compareSelection.length > 0 && (
                                        <button
                                            type="button"
                                            onClick={clearCompareSelection}
                                            className="text-[11px] text-muted-foreground hover:text-foreground"
                                        >
                                            선택 해제
                                        </button>
                                    )}
                                </div>
                            </div>
                            {historyError && (
                                <p className="text-xs text-destructive mb-2">{historyError}</p>
                            )}
                            {history.length > 0 && (
                                <div className="space-y-2 mb-4">
                                    <input
                                        type="text"
                                        value={historySearch}
                                        onChange={(event) => setHistorySearch(event.target.value)}
                                        placeholder="검색어(라벨/쿼리/Run)"
                                        className="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs"
                                    />
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                        <select
                                            value={intentFilter}
                                            onChange={(event) => setIntentFilter(event.target.value)}
                                            className="bg-background border border-border rounded-lg px-3 py-2 text-xs"
                                        >
                                            <option value="all">모든 Intent</option>
                                            {historyIntentOptions.map(option => (
                                                <option key={option.intent} value={option.intent}>
                                                    {option.label}
                                                </option>
                                            ))}
                                        </select>
                                        <select
                                            value={runFilter}
                                            onChange={(event) => setRunFilter(event.target.value)}
                                            className="bg-background border border-border rounded-lg px-3 py-2 text-xs"
                                        >
                                            <option value="all">모든 Run</option>
                                            {historyRunOptions.map(runId => (
                                                <option key={runId} value={runId}>
                                                    {runId === "sample" ? "샘플 데이터" : `Run ${runId.slice(0, 8)}`}
                                                </option>
                                            ))}
                                        </select>
                                        <select
                                            value={profileFilter}
                                            onChange={(event) => setProfileFilter(event.target.value)}
                                            className="bg-background border border-border rounded-lg px-3 py-2 text-xs"
                                        >
                                            <option value="all">모든 프로필</option>
                                            {historyProfileOptions.map(profile => (
                                                <option key={profile} value={profile}>
                                                    {profile}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                        <input
                                            type="date"
                                            value={dateFrom}
                                            onChange={(event) => setDateFrom(event.target.value)}
                                            className="bg-background border border-border rounded-lg px-3 py-2 text-xs"
                                        />
                                        <input
                                            type="date"
                                            value={dateTo}
                                            onChange={(event) => setDateTo(event.target.value)}
                                            className="bg-background border border-border rounded-lg px-3 py-2 text-xs"
                                        />
                                    </div>
                                    <div className="flex items-center justify-between gap-2">
                                        <select
                                            value={sortOrder}
                                            onChange={(event) => setSortOrder(event.target.value)}
                                            className="bg-background border border-border rounded-lg px-3 py-2 text-xs"
                                        >
                                            <option value="newest">최신순</option>
                                            <option value="oldest">오래된순</option>
                                            <option value="duration_desc">소요시간 긴 순</option>
                                            <option value="duration_asc">소요시간 짧은 순</option>
                                        </select>
                                        <button
                                            type="button"
                                            onClick={resetHistoryFilters}
                                            className="text-[11px] text-muted-foreground hover:text-foreground"
                                        >
                                            필터 초기화
                                        </button>
                                    </div>
                                </div>
                            )}
                            {history.length === 0 ? (
                                <p className="text-xs text-muted-foreground">
                                    아직 저장된 분석 결과가 없습니다.
                                </p>
                            ) : filteredHistory.length === 0 ? (
                                <p className="text-xs text-muted-foreground">
                                    조건에 맞는 결과가 없습니다.
                                </p>
                            ) : (
                                <div className="space-y-2">
                                    {filteredHistory.map(item => {
                                        const selected = compareSelection.includes(item.result_id);
                                        const metaParts: string[] = [];
                                        if (item.profile) {
                                            metaParts.push(`Profile ${item.profile}`);
                                        }
                                        if (item.tags && item.tags.length > 0) {
                                            metaParts.push(`Tags ${item.tags.join(", ")}`);
                                        }
                                        return (
                                            <div
                                                key={item.result_id}
                                                className="flex items-start gap-2 border border-border rounded-lg p-3 hover:border-primary/40 hover:shadow-sm transition-all"
                                            >
                                                <button
                                                    type="button"
                                                    onClick={() => toggleCompareSelection(item.result_id)}
                                                    className="mt-1 text-muted-foreground hover:text-foreground"
                                                    aria-label="비교 선택"
                                                >
                                                    {selected ? (
                                                        <CheckCircle2 className="w-4 h-4 text-primary" />
                                                    ) : (
                                                        <Circle className="w-4 h-4" />
                                                    )}
                                                </button>
                                                <Link
                                                    to={`/analysis/results/${item.result_id}`}
                                                    className="flex-1"
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <p className="text-sm font-medium">{item.label}</p>
                                                        <span className="text-xs text-muted-foreground">
                                                            {formatDurationMs(item.duration_ms)}
                                                        </span>
                                                    </div>
                                                    <p className="text-xs text-muted-foreground mt-1">
                                                        {formatDateTime(item.created_at)}
                                                    </p>
                                                    <p className="text-[11px] text-muted-foreground mt-1">
                                                        {item.run_id
                                                            ? `Run ${item.run_id.slice(0, 8)}`
                                                            : "샘플 데이터"}
                                                    </p>
                                                    {metaParts.length > 0 && (
                                                        <p className="text-[11px] text-muted-foreground mt-1">
                                                            {metaParts.join(" · ")}
                                                        </p>
                                                    )}
                                                </Link>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>

                        {Object.entries(groupedCatalog).map(([category, intents]) => {
                            const meta = CATEGORY_META[category] || {
                                label: category,
                                description: "",
                            };
                            return (
                                <div key={category} className="bg-card border border-border rounded-xl p-4 shadow-sm">
                                    <div className="mb-4">
                                        <h3 className="font-semibold">{meta.label}</h3>
                                        <p className="text-xs text-muted-foreground mt-1">{meta.description}</p>
                                    </div>
                                    <div className="space-y-3">
                                        {intents.map(intent => {
                                            const isActive = selectedIntent?.intent === intent.intent;
                                            const isBenchmark = intent.intent === "benchmark_retrieval";
                                            const isMissingBenchmarkPath = isBenchmark && !benchmarkPath.trim();
                                            const isDisabled = !intent.available || loading || isMissingBenchmarkPath;
                                            return (
                                                <button
                                                    key={intent.intent}
                                                    type="button"
                                                    onClick={() => handleRun(intent)}
                                                    disabled={isDisabled}
                                                    className={`w-full text-left border rounded-xl p-3 transition-all ${isActive ? "border-primary ring-1 ring-primary/30 bg-primary/5" : "border-border hover:border-primary/40"} ${isDisabled ? "opacity-60 cursor-not-allowed" : "hover:shadow-sm"}`}
                                                >
                                                    <div className="flex items-center justify-between gap-3">
                                                        <div>
                                                            <p className="font-medium text-sm">{intent.label}</p>
                                                            <p className="text-xs text-muted-foreground mt-1">{intent.description}</p>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            {!intent.available && (
                                                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">준비중</span>
                                                            )}
                                                            <Play className="w-4 h-4 text-primary" />
                                                        </div>
                                                    </div>
                                                    {intent.nodes.length > 0 && (
                                                        <div className="flex flex-wrap gap-1 mt-3">
                                                            {intent.nodes.slice(0, 3).map(node => (
                                                                <span
                                                                    key={node.id}
                                                                    className="text-[10px] px-2 py-1 rounded-md bg-secondary border border-border text-muted-foreground"
                                                                >
                                                                    {node.name}
                                                                </span>
                                                            ))}
                                                            {intent.nodes.length > 3 && (
                                                                <span className="text-[10px] px-2 py-1 rounded-md bg-secondary border border-border text-muted-foreground">
                                                                    +{intent.nodes.length - 3}
                                                                </span>
                                                            )}
                                                        </div>
                                                    )}
                                                    {!intent.available && intent.missing_modules.length > 0 && (
                                                        <p className="text-[10px] text-amber-700 mt-2">
                                                            미구현 모듈: {intent.missing_modules.join(", ")}
                                                        </p>
                                                    )}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    <div className="lg:col-span-2">
                        <div className="surface-panel p-6 h-full relative overflow-hidden">
                            <div className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-primary/10 blur-3xl" />
                            <div className="flex items-center justify-between mb-4">
                                <div>
                                    <h2 className="text-xl font-semibold">{intentLabel} 결과</h2>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        선택한 분석의 실행 상태와 결과를 확인합니다.
                                    </p>
                                </div>
                                {loading && (
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                        <Activity className="w-4 h-4 animate-spin" />
                                        실행 중...
                                    </div>
                                )}
                            </div>

                            {error && (
                                <div className="mb-4 p-3 border border-destructive/30 bg-destructive/10 rounded-lg text-destructive text-sm flex items-center gap-2">
                                    <AlertCircle className="w-4 h-4" />
                                    {error}
                                </div>
                            )}

                            {!result && !loading && !error && (
                                <div className="space-y-6">
                                    <div className="border border-border rounded-xl p-4 bg-background">
                                        <h3 className="text-sm font-semibold">시작 가이드</h3>
                                        <div className="mt-2 space-y-2 text-xs text-muted-foreground">
                                            <p>1. 좌측에서 분석 항목을 선택하세요.</p>
                                            <p>2. Run을 지정하면 실제 데이터 기반으로 분석합니다.</p>
                                            <p>3. 결과를 저장해 비교/추적할 수 있습니다.</p>
                                        </div>
                                    </div>
                                    <div className="border border-border rounded-xl p-4 bg-background">
                                        <div className="flex flex-wrap items-center justify-between gap-2">
                                            <div>
                                                <h3 className="text-sm font-semibold">최근 저장 결과</h3>
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    최신 {recentHistory.length}건을 요약합니다.
                                                </p>
                                            </div>
                                            {recentCompareLink && (
                                                <Link
                                                    to={recentCompareLink}
                                                    className="text-xs text-primary hover:underline"
                                                >
                                                    최근 2개 비교
                                                </Link>
                                            )}
                                        </div>
                                        {historyError && (
                                            <p className="text-xs text-destructive mt-2">
                                                {historyError}
                                            </p>
                                        )}
                                        {recentHistory.length === 0 ? (
                                            <p className="text-xs text-muted-foreground mt-3">
                                                저장된 분석 결과가 없습니다.
                                            </p>
                                        ) : (
                                            <div className="mt-3 space-y-3">
                                                {recentHistory.map((item) => (
                                                    <div
                                                        key={`recent-${item.result_id}`}
                                                        className="flex flex-wrap items-center justify-between gap-3 border border-border rounded-lg px-3 py-2"
                                                    >
                                                        <div className="min-w-[12rem]">
                                                            <p className="text-sm font-medium">{item.label}</p>
                                                            <p className="text-[11px] text-muted-foreground mt-1">
                                                                {formatDateTime(item.created_at)} · {formatDurationMs(item.duration_ms)}
                                                            </p>
                                                            <p className="text-[11px] text-muted-foreground">
                                                                {item.query || "쿼리 없음"}
                                                            </p>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <StatusBadge status={item.is_complete ? "completed" : "incomplete"} />
                                                            <Link
                                                                to={`/analysis/results/${item.result_id}`}
                                                                className="text-[11px] text-primary hover:underline"
                                                            >
                                                                보기
                                                            </Link>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {result && (
                                <div className="space-y-6 animate-in fade-in duration-300">
                                    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
                                        <div className="border border-border rounded-lg p-3">
                                            <p className="text-xs text-muted-foreground">분석 유형</p>
                                            <p className="text-sm font-semibold mt-1">{intentLabel}</p>
                                        </div>
                                        <div className="border border-border rounded-lg p-3">
                                            <p className="text-xs text-muted-foreground">처리 시간</p>
                                            <p className="text-sm font-semibold mt-1">{formatDurationMs(result.duration_ms)}</p>
                                        </div>
                                        <div className="border border-border rounded-lg p-3">
                                            <p className="text-xs text-muted-foreground">상태</p>
                                            <div className="mt-2">
                                                <StatusBadge status={result.is_complete ? "completed" : "incomplete"} />
                                            </div>
                                        </div>
                                        <div className="border border-border rounded-lg p-3">
                                            <p className="text-xs text-muted-foreground">보고서 상태</p>
                                            <div className="mt-2">
                                                <span
                                                    className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${reportBadge.className}`}
                                                >
                                                    {reportBadge.label}
                                                </span>
                                            </div>
                                            {reportMeta?.llmModel && (
                                                <p className="text-[11px] text-muted-foreground mt-2">
                                                    모델 {reportMeta.llmModel}
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    {!analysisRunId && (
                                        <div className="border border-amber-200 bg-amber-50 text-amber-700 rounded-lg p-3 text-xs">
                                            샘플 데이터로 분석 중입니다. Run을 선택하면 실제 평가 결과를 기반으로 분석합니다.
                                        </div>
                                    )}

                                    {reportErrorText && (
                                        <div className="border border-rose-200 bg-rose-50 text-rose-700 rounded-lg p-3 text-xs">
                                            LLM 오류로 대체 보고서를 사용했습니다: {reportErrorText}
                                        </div>
                                    )}

                                    {schemaIssues.length > 0 && (
                                        <div className="border border-amber-200 bg-amber-50 text-amber-700 rounded-lg p-3 text-xs space-y-1">
                                            <p className="font-medium">결과 구조 확인 필요</p>
                                            <ul className="list-disc list-inside">
                                                {schemaIssues.map((issue) => (
                                                    <li key={issue}>{issue}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    {executionParamEntries.length > 0 && (
                                        <div className="border border-border rounded-lg p-4 space-y-3">
                                            <div className="flex items-center justify-between">
                                                <p className="text-sm font-semibold">실행 파라미터</p>
                                                <div className="flex items-center gap-3">
                                                    <button
                                                        onClick={handleCopyCli}
                                                        className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors disabled:opacity-60"
                                                        title="Copy CLI command"
                                                        disabled={!executionMeta}
                                                    >
                                                        {cliCopyStatus === "success" ? (
                                                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                                                        ) : cliCopyStatus === "error" ? (
                                                            <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                                                        ) : (
                                                            <Terminal className="w-3.5 h-3.5" />
                                                        )}
                                                        {cliCopyStatus === "success" ? "Copied!" : "Copy CLI"}
                                                    </button>
                                                    <span className="text-[11px] text-muted-foreground">
                                                        재현용 요약
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                                                {executionParamEntries.map((entry) => (
                                                    <div
                                                        key={`${entry.label}-${entry.value}`}
                                                        className="border border-border rounded-md px-2 py-1"
                                                    >
                                                        <span className="text-muted-foreground">{entry.label}</span>
                                                        <span className="ml-2 font-semibold text-foreground">
                                                            {entry.value || "-"}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {(keyMetricEntries.length > 0 || nodeErrorSummary) && (
                                        <div className="border border-border rounded-lg p-4 space-y-3">
                                            <div className="flex items-center justify-between">
                                                <p className="text-sm font-semibold">핵심 요약</p>
                                                <span className="text-[11px] text-muted-foreground">
                                                    주요 지표/실패 요인
                                                </span>
                                            </div>
                                            {keyMetricEntries.length > 0 && (
                                                <div className="space-y-2">
                                                    <p className="text-xs text-muted-foreground">
                                                        주요 지표 상위 3개
                                                    </p>
                                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                                                        {keyMetricEntries.map((entry) => (
                                                            <div
                                                                key={`metric-${entry.key}`}
                                                                className="border border-border rounded-md px-2 py-2"
                                                            >
                                                                <p className="text-muted-foreground">{entry.key}</p>
                                                                <p className="text-sm font-semibold text-foreground">
                                                                    {entry.value.toFixed(3)}
                                                                </p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                            {nodeErrorSummary && (
                                                <div className="space-y-2">
                                                    <p className="text-xs text-muted-foreground">
                                                        실패 유형 상위 3개
                                                    </p>
                                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                                                        {nodeErrorSummary.preview.map((item) => (
                                                            <div
                                                                key={`failure-${item.id}`}
                                                                className="border border-rose-200 bg-rose-50 text-rose-700 rounded-md px-2 py-2"
                                                            >
                                                                <p className="font-semibold">{item.name}</p>
                                                                <p className="text-[11px]">{item.error}</p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {nextActions.length > 0 && (
                                        <div className="border border-border rounded-lg p-4 space-y-3">
                                            <div className="flex items-center justify-between">
                                                <p className="text-sm font-semibold">다음 액션</p>
                                                <span className="text-[11px] text-muted-foreground">
                                                    추천 흐름
                                                </span>
                                            </div>
                                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                                                {nextActions.map((action) => (
                                                    <div
                                                        key={action.id}
                                                        className="border border-border rounded-md px-2 py-2 space-y-2"
                                                    >
                                                        <div>
                                                            <p className="font-semibold text-foreground">
                                                                {action.title}
                                                            </p>
                                                            <p className="text-muted-foreground">
                                                                {action.description}
                                                            </p>
                                                        </div>
                                                        {action.onClick && action.ctaLabel && (
                                                            <button
                                                                type="button"
                                                                onClick={action.onClick}
                                                                disabled={action.disabled}
                                                                className="text-[11px] inline-flex items-center gap-1 px-2 py-1 rounded-md border border-border hover:border-primary/40 disabled:opacity-60"
                                                            >
                                                                {action.ctaLabel}
                                                            </button>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {analysisMetricGroups.length > 0 && (
                                        <div className="border border-border rounded-lg p-4 space-y-3">
                                            <div className="flex items-center justify-between">
                                                <p className="text-sm font-semibold">추가 분석 지표</p>
                                                <button
                                                    type="button"
                                                    onClick={() => setShowAnalysisMetrics((prev) => !prev)}
                                                    className="text-[11px] text-muted-foreground hover:text-foreground"
                                                >
                                                    {showAnalysisMetrics ? "접기" : "표시"}
                                                </button>
                                            </div>
                                            {analysisMetricSpecError && (
                                                <p className="text-xs text-rose-500">
                                                    {analysisMetricSpecError}
                                                </p>
                                            )}
                                            {!showAnalysisMetrics ? (
                                                <p className="text-xs text-muted-foreground">
                                                    분석 모듈에서 추출된 추가 지표를 표시합니다.
                                                </p>
                                            ) : (
                                                <div className="space-y-4">
                                                    {analysisMetricGroups.map((group) => (
                                                        <div key={group.id} className="space-y-2">
                                                            <p className="text-xs font-semibold text-muted-foreground">
                                                                {group.label}
                                                            </p>
                                                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                                                                {group.items.map((item) => (
                                                                    <div
                                                                        key={`${item.spec.key}-${item.nodeId}`}
                                                                        className="border border-border rounded-md px-2 py-2"
                                                                        title={item.spec.description}
                                                                    >
                                                                        <span className="text-muted-foreground">
                                                                            {item.spec.label}
                                                                        </span>
                                                                        <span className="ml-2 font-semibold text-foreground">
                                                                            {item.value.toFixed(4)}
                                                                        </span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    <div className="border border-border rounded-lg p-4 space-y-3">
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm font-semibold">지표 드릴다운</p>
                                            <span className="text-[11px] text-muted-foreground">
                                                증거 기반 분포
                                            </span>
                                        </div>
                                        {metricDistributions.length === 0 ? (
                                            <p className="text-xs text-muted-foreground">
                                                현재 결과에는 증거 기반 지표가 없습니다.
                                            </p>
                                        ) : (
                                            <div className="space-y-3">
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                                                    {metricPreview.map((metric) => {
                                                        const range = metric.max - metric.min;
                                                        const ratio = range > 0 ? (metric.avg - metric.min) / range : 1;
                                                        return (
                                                            <div
                                                                key={`dist-${metric.key}`}
                                                                className="border border-border rounded-md px-2 py-2 space-y-2"
                                                            >
                                                                <div className="flex items-center justify-between">
                                                                    <p className="font-semibold text-foreground">{metric.key}</p>
                                                                    <span className="text-[11px] text-muted-foreground">
                                                                        {metric.count}개
                                                                    </span>
                                                                </div>
                                                                <div className="h-2 rounded-full bg-slate-100">
                                                                    <div
                                                                        className="h-2 rounded-full bg-primary/70"
                                                                        style={{ width: `${Math.round(ratio * 100)}%` }}
                                                                    />
                                                                </div>
                                                                <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                                                                    <span>min {metric.min.toFixed(3)}</span>
                                                                    <span>avg {metric.avg.toFixed(3)}</span>
                                                                    <span>max {metric.max.toFixed(3)}</span>
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                                {metricDistributions.length > 6 && (
                                                    <button
                                                        type="button"
                                                        onClick={() => setShowAllMetrics(prev => !prev)}
                                                        className="text-xs text-muted-foreground hover:text-foreground"
                                                    >
                                                        {showAllMetrics ? "접기" : "전체 지표 보기"}
                                                    </button>
                                                )}
                                            </div>
                                        )}
                                    </div>

                                    <div className="border border-border rounded-lg p-4 space-y-3">
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm font-semibold">공유 템플릿</p>
                                            <span className="text-[11px] text-muted-foreground">
                                                팀 공유용 요약
                                            </span>
                                        </div>
                                        <textarea
                                            readOnly
                                            value={shareSummaryText}
                                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs h-28"
                                        />
                                        <div className="flex flex-wrap items-center gap-2 text-xs">
                                            <button
                                                type="button"
                                                onClick={() => copyToClipboard(shareSummaryText, "summary")}
                                                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-background hover:border-primary/40"
                                            >
                                                <Copy className="w-3 h-3" />
                                                요약 복사
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    if (!savedResultId || typeof window === "undefined") return;
                                                    const url = `${window.location.origin}/analysis/results/${savedResultId}`;
                                                    void copyToClipboard(url, "link");
                                                }}
                                                disabled={!savedResultId}
                                                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-background hover:border-primary/40 disabled:opacity-60"
                                            >
                                                <Link2 className="w-3 h-3" />
                                                결과 링크 복사
                                            </button>
                                            {shareCopyStatus === "success" && (
                                                <span className="text-emerald-600">복사 완료</span>
                                            )}
                                            {shareCopyStatus === "error" && (
                                                <span className="text-rose-600">복사 실패</span>
                                            )}
                                            {shareLinkStatus === "success" && (
                                                <span className="text-emerald-600">링크 복사 완료</span>
                                            )}
                                            {shareLinkStatus === "error" && (
                                                <span className="text-rose-600">링크 복사 실패</span>
                                            )}
                                            {!savedResultId && (
                                                <span className="text-muted-foreground">
                                                    결과 저장 후 링크 공유 가능
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    <div className="border border-border rounded-lg p-4 space-y-3">
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm font-semibold">저장 메타데이터</p>
                                            <span className="text-[11px] text-muted-foreground">
                                                선택 입력
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                            <label className="text-xs text-muted-foreground">
                                                프로필
                                                <input
                                                    type="text"
                                                    value={saveProfile}
                                                    onChange={(event) => setSaveProfile(event.target.value)}
                                                    placeholder="예: dev / prod"
                                                    className="mt-2 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
                                                />
                                            </label>
                                            <label className="text-xs text-muted-foreground">
                                                태그
                                                <input
                                                    type="text"
                                                    value={saveTags}
                                                    onChange={(event) => setSaveTags(event.target.value)}
                                                    placeholder="예: ragas, korean, baseline"
                                                    className="mt-2 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
                                                />
                                                <span className="text-[11px] text-muted-foreground mt-1 block">
                                                    쉼표로 구분합니다.
                                                </span>
                                            </label>
                                        </div>
                                        <label className="text-xs text-muted-foreground">
                                            메타데이터 (JSON)
                                            <textarea
                                                value={saveMetadataText}
                                                onChange={(event) => {
                                                    setSaveMetadataText(event.target.value);
                                                    if (metadataError) {
                                                        setMetadataError(null);
                                                    }
                                                }}
                                                placeholder='예: {"dataset":"insurance","version":"v2"}'
                                                className="mt-2 w-full bg-background border border-border rounded-lg px-3 py-2 text-xs h-24"
                                            />
                                        </label>
                                        {metadataError && (
                                            <p className="text-xs text-destructive">{metadataError}</p>
                                        )}
                                    </div>

                                    <div className="flex flex-wrap items-center gap-2">
                                        <button
                                            type="button"
                                            onClick={handleSave}
                                            disabled={saving}
                                            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40 disabled:opacity-60"
                                        >
                                            <Save className="w-3 h-3" />
                                            {saving ? "저장 중..." : "결과 저장"}
                                        </button>
                                        {savedResultId && (
                                            <Link
                                                to={`/analysis/results/${savedResultId}`}
                                                className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40"
                                            >
                                                <ExternalLink className="w-3 h-3" />
                                                결과 보기
                                            </Link>
                                        )}
                                        {savedResultId && (
                                            <button
                                                type="button"
                                                onClick={() => toggleCompareSelection(savedResultId)}
                                                className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40"
                                            >
                                                {savedInCompare ? "비교에서 제거" : "비교에 추가"}
                                            </button>
                                        )}
                                        {compareLink && (
                                            <Link
                                                to={compareLink}
                                                className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40"
                                            >
                                                비교 보기
                                            </Link>
                                        )}
                                        {saveError && (
                                            <span className="text-xs text-destructive">{saveError}</span>
                                        )}
                                    </div>

                                    {resultSummary && (
                                        <div className="surface-panel p-4">
                                            <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                                                <div>
                                                    <h3 className="text-sm font-semibold">실행 요약</h3>
                                                    <p className="text-xs text-muted-foreground">
                                                        총 {resultSummaryTotal}개 노드 상태
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex flex-wrap gap-2 text-xs">
                                                {Object.entries(resultSummary).map(([status, count]) => {
                                                    if (count === 0) return null;
                                                    return (
                                                        <StatusBadge
                                                            key={status}
                                                            status={status}
                                                            value={count}
                                                        />
                                                    );
                                                })}
                                            </div>
                                            {nodeErrorSummary && (
                                                <div className="mt-3 border border-rose-200 bg-rose-50 text-rose-700 rounded-lg p-3 text-xs space-y-1">
                                                    <p className="font-semibold">오류 {nodeErrorSummary.total}건</p>
                                                    {nodeErrorSummary.preview.map((item) => (
                                                        <p key={item.id}>
                                                            {item.name}: {item.error}
                                                        </p>
                                                    ))}
                                                    {nodeErrorSummary.total > nodeErrorSummary.preview.length && (
                                                        <p>그 외 {nodeErrorSummary.total - nodeErrorSummary.preview.length}건</p>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {!analysisRunId && requiresRunData && (
                                        <div className="border border-amber-200 bg-amber-50 text-amber-700 rounded-lg p-3 text-xs">
                                            Run 데이터가 없어 일부 분석 결과가 비어 있을 수 있습니다.
                                            정확한 분석을 위해 Run을 선택해 다시 실행하세요.
                                        </div>
                                    )}

                                    {prioritySummary && (
                                        <PrioritySummaryPanel summary={prioritySummary} />
                                    )}

                                    <div className="border border-border rounded-lg p-4 space-y-3">
                                        <div className="flex flex-wrap items-center justify-between gap-3">
                                            <div>
                                                <h3 className="text-sm font-semibold">개선 가이드</h3>
                                                <p className="text-xs text-muted-foreground">
                                                    Run 기반 우선순위 개선 제안을 확인합니다.
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-3 text-xs">
                                                <label className="flex items-center gap-2 text-muted-foreground">
                                                    <input
                                                        type="checkbox"
                                                        className="accent-primary"
                                                        checked={includeImprovementLlm}
                                                        onChange={(event) =>
                                                            setIncludeImprovementLlm(event.target.checked)
                                                        }
                                                        disabled={!analysisRunId}
                                                    />
                                                    LLM 보강
                                                </label>
                                                <button
                                                    type="button"
                                                    onClick={handleLoadImprovement}
                                                    disabled={!analysisRunId || improvementLoading}
                                                    className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40 disabled:opacity-60"
                                                >
                                                    {improvementLoading
                                                        ? "불러오는 중..."
                                                        : improvementReport
                                                            ? "새로고침"
                                                            : "불러오기"}
                                                </button>
                                            </div>
                                        </div>

                                        {!analysisRunId && (
                                            <p className="text-xs text-amber-600">
                                                개선 가이드는 Run 선택이 필요합니다.
                                            </p>
                                        )}

                                        {improvementError && (
                                            <p className="text-xs text-destructive">{improvementError}</p>
                                        )}

                                        {!improvementReport && !improvementLoading && analysisRunId && !improvementError && (
                                            <p className="text-xs text-muted-foreground">
                                                개선 가이드를 불러오면 우선순위와 예상 개선폭을 확인할 수 있습니다.
                                            </p>
                                        )}

                                        {improvementReport && (
                                            <div className="space-y-4">
                                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                                                    <div className="border border-border rounded-lg p-3">
                                                        <p className="text-muted-foreground">Pass Rate</p>
                                                        <p className="text-sm font-semibold mt-1">
                                                            {(improvementReport.pass_rate * 100).toFixed(1)}%
                                                        </p>
                                                    </div>
                                                    <div className="border border-border rounded-lg p-3">
                                                        <p className="text-muted-foreground">Failed Cases</p>
                                                        <p className="text-sm font-semibold mt-1">
                                                            {improvementReport.failed_test_cases}
                                                            /
                                                            {improvementReport.total_test_cases}
                                                        </p>
                                                    </div>
                                                    <div className="border border-border rounded-lg p-3">
                                                        <p className="text-muted-foreground">Guide Count</p>
                                                        <p className="text-sm font-semibold mt-1">
                                                            {improvementReport.guides.length}
                                                        </p>
                                                    </div>
                                                </div>

                                                <div className="space-y-2">
                                                    <p className="text-xs font-semibold text-muted-foreground">메트릭 갭</p>
                                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                                        {Object.entries(improvementReport.metric_scores).map(
                                                            ([metric, score]) => {
                                                                const threshold = improvementReport.metric_thresholds[metric] ?? 0.7;
                                                                const gap = improvementReport.metric_gaps[metric] ?? threshold - score;
                                                                const passed = score >= threshold;
                                                                return (
                                                                    <div
                                                                        key={metric}
                                                                        className="border border-border rounded-lg p-3 text-xs"
                                                                    >
                                                                        <div className="flex items-center justify-between">
                                                                            <span className="font-medium">{metric}</span>
                                                                            <span className={passed ? "text-emerald-600" : "text-rose-600"}>
                                                                                {passed ? "통과" : "미달"}
                                                                            </span>
                                                                        </div>
                                                                        <p className="text-muted-foreground mt-1">
                                                                            score {score.toFixed(3)} / threshold {threshold.toFixed(2)} / gap {gap.toFixed(3)}
                                                                        </p>
                                                                    </div>
                                                                );
                                                            }
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="space-y-2">
                                                    <p className="text-xs font-semibold text-muted-foreground">우선순위 가이드</p>
                                                    {improvementReport.guides.length === 0 ? (
                                                        <p className="text-xs text-muted-foreground">
                                                            현재 탐지된 개선 가이드가 없습니다.
                                                        </p>
                                                    ) : (
                                                        <div className="space-y-3">
                                                            {improvementReport.guides.map((guide) => {
                                                                const meta = PRIORITY_META[guide.priority] || {
                                                                    label: guide.priority,
                                                                    color: "text-muted-foreground",
                                                                };
                                                                const totalImprovement = guide.actions.reduce(
                                                                    (sum, action) => sum + (action.expected_improvement || 0),
                                                                    0
                                                                );
                                                                return (
                                                                    <div key={guide.guide_id} className="border border-border rounded-lg p-3">
                                                                        <div className="flex items-center justify-between">
                                                                            <div>
                                                                                <p className="text-sm font-medium">
                                                                                    {guide.component}
                                                                                </p>
                                                                                <p className="text-xs text-muted-foreground mt-1">
                                                                                    대상 메트릭: {guide.target_metrics.join(", ") || "-"}
                                                                                </p>
                                                                            </div>
                                                                            <div className="text-right">
                                                                                <p className={`text-xs font-semibold ${meta.color}`}>
                                                                                    {meta.label}
                                                                                </p>
                                                                                <p className="text-[11px] text-muted-foreground mt-1">
                                                                                    예상 개선 +{(totalImprovement * 100).toFixed(1)}%
                                                                                </p>
                                                                            </div>
                                                                        </div>
                                                                        {guide.actions.length > 0 && (
                                                                            <div className="mt-3 space-y-2 text-xs">
                                                                                {guide.actions.map((action) => (
                                                                                    <div key={action.action_id} className="border border-border rounded-lg p-2">
                                                                                        <div className="flex items-center justify-between">
                                                                                            <p className="font-medium">{action.title}</p>
                                                                                            <span className="text-muted-foreground">
                                                                                                {EFFORT_LABEL[action.effort] || action.effort}
                                                                                            </span>
                                                                                        </div>
                                                                                        {action.description && (
                                                                                            <p className="text-muted-foreground mt-1">{action.description}</p>
                                                                                        )}
                                                                                        <p className="text-muted-foreground mt-1">
                                                                                            예상 개선 +{(action.expected_improvement * 100).toFixed(1)}%
                                                                                        </p>
                                                                                    </div>
                                                                                ))}
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                );
                                                            })}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {selectedIntent?.nodes.length ? (
                                        <div>
                                            <h3 className="text-sm font-semibold mb-3">실행 단계</h3>
                                            <div className="space-y-3">
                                                {selectedIntent.nodes.map((node, index) => {
                                                    const status = getNodeStatus(safeNodeResults?.[node.id]);
                                                    const indicatorClass = STEP_STATUS_COLORS[status] || STEP_STATUS_COLORS.pending;
                                                    const isLast = index === selectedIntent.nodes.length - 1;
                                                    return (
                                                        <div key={node.id} className="relative pl-7">
                                                            <span
                                                                className={`absolute left-0 top-2 flex h-4 w-4 items-center justify-center rounded-full text-[10px] text-white ${indicatorClass}`}
                                                            >
                                                                {index + 1}
                                                            </span>
                                                            {!isLast && (
                                                                <span className="absolute left-[7px] top-6 h-full w-px bg-border" />
                                                            )}
                                                            <div className="flex items-center justify-between border border-border rounded-lg px-3 py-2">
                                                                <div>
                                                                    <p className="text-sm font-medium">{node.name}</p>
                                                                    <p className="text-xs text-muted-foreground">{node.module}</p>
                                                                </div>
                                                                <StatusBadge status={status} />
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    ) : null}

                                    <div>
                                        <div className="flex items-center justify-between mb-3">
                                            <h3 className="text-sm font-semibold">결과 출력</h3>
                                            <div className="flex items-center gap-3">
                                                <button
                                                    type="button"
                                                    onClick={() => setShowRaw(prev => !prev)}
                                                    className="text-xs text-muted-foreground hover:text-foreground"
                                                >
                                                    {showRaw ? "리포트 보기" : "RAW JSON"}
                                                </button>
                                                {!showRaw && reportIsLarge && (
                                                    <button
                                                        type="button"
                                                        onClick={() => setShowFullReport(prev => !prev)}
                                                        className="text-xs text-muted-foreground hover:text-foreground"
                                                    >
                                                        {showFullReport ? "요약 보기" : "전체 보기"}
                                                    </button>
                                                )}
                                                {showRaw && rawIsLarge && (
                                                    <button
                                                        type="button"
                                                        onClick={() => setShowFullRaw(prev => !prev)}
                                                        className="text-xs text-muted-foreground hover:text-foreground"
                                                    >
                                                        {showFullRaw ? "요약 보기" : "전체 보기"}
                                                    </button>
                                                )}
                                                {!showRaw && (!reportIsLarge || showFullReport) && (
                                                    <button
                                                        type="button"
                                                        onClick={() => setRenderMarkdown(prev => !prev)}
                                                        className="text-xs text-muted-foreground hover:text-foreground"
                                                    >
                                                        {renderMarkdown ? "경량 보기" : "마크다운 렌더링"}
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                        {showRaw ? (
                                            <VirtualizedText
                                                text={
                                                    (!showFullRaw && rawIsLarge ? rawPreview : rawOutput) || "{}"
                                                }
                                                height={showFullRaw || !rawIsLarge ? "20rem" : "12rem"}
                                                className="bg-background border border-border rounded-lg p-3 text-xs"
                                            />
                                        ) : reportText ? (
                                            reportIsLarge && !showFullReport ? (
                                                <VirtualizedText
                                                    text={reportPreview || ""}
                                                    height="12rem"
                                                    className="bg-background border border-border rounded-lg p-3 text-xs"
                                                />
                                            ) : renderMarkdown ? (
                                                <div className="bg-background border border-border rounded-lg p-4 text-sm max-h-80 overflow-auto">
                                                    <MarkdownContent text={reportText} />
                                                </div>
                                            ) : (
                                                <VirtualizedText
                                                    text={reportText}
                                                    height="20rem"
                                                    className="bg-background border border-border rounded-lg p-3 text-xs"
                                                />
                                            )
                                        ) : (
                                            <VirtualizedText
                                                text={
                                                    (!showFullRaw && rawIsLarge ? rawPreview : rawOutput) || "{}"
                                                }
                                                height={showFullRaw || !rawIsLarge ? "20rem" : "12rem"}
                                                className="bg-background border border-border rounded-lg p-3 text-xs"
                                            />
                                        )}
                                    </div>

                                    <AnalysisNodeOutputs
                                        nodeResults={safeNodeResults}
                                        nodeDefinitions={intentDefinition?.nodes}
                                        title="노드 상세 출력"
                                    />

                                    {hasNodeError && (
                                        <div className="border border-amber-200 bg-amber-50 text-amber-700 rounded-lg p-3 text-xs">
                                            일부 단계에서 오류가 발생했습니다. 실행 로그를 확인하세요.
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
