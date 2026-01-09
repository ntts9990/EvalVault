import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { AnalysisNodeOutputs } from "../components/AnalysisNodeOutputs";
import { MarkdownContent } from "../components/MarkdownContent";
import { PrioritySummaryPanel, type PrioritySummary } from "../components/PrioritySummaryPanel";
import { StatusBadge } from "../components/StatusBadge";
import { VirtualizedText } from "../components/VirtualizedText";
import {
    fetchAnalysisIntents,
    fetchAnalysisHistory,
    fetchRuns,
    fetchImprovementGuide,
    runAnalysis,
    saveAnalysisResult,
    type AnalysisHistoryItem,
    type AnalysisIntentInfo,
    type AnalysisResult,
    type ImprovementReport,
    type RunSummary,
} from "../services/api";
import { formatDateTime, formatDurationMs } from "../utils/format";
import {
    Activity,
    AlertCircle,
    CheckCircle2,
    Circle,
    ExternalLink,
    Play,
    Save,
} from "lucide-react";

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

const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === "object" && value !== null;

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
    if (!isRecord(value)) return false;
    return Array.isArray(value.bottom_cases) || Array.isArray(value.impact_cases);
}

export function AnalysisLab() {
    const [catalog, setCatalog] = useState<AnalysisIntentInfo[]>([]);
    const [catalogError, setCatalogError] = useState<string | null>(null);
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
    const [saveProfile, setSaveProfile] = useState("");
    const [saveTags, setSaveTags] = useState("");
    const [saveMetadataText, setSaveMetadataText] = useState("");
    const [metadataError, setMetadataError] = useState<string | null>(null);
    const [useLlmReport, setUseLlmReport] = useState(true);
    const [recomputeRagas, setRecomputeRagas] = useState(false);
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

    const compareLink = useMemo(() => {
        if (compareSelection.length !== 2) return null;
        const [left, right] = compareSelection;
        return `/analysis/compare?left=${encodeURIComponent(left)}&right=${encodeURIComponent(right)}`;
    }, [compareSelection]);

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

    const handleSave = async () => {
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
    };

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

    const toggleCompareSelection = (resultId: string) => {
        setCompareSelection(prev => {
            if (prev.includes(resultId)) {
                return prev.filter(id => id !== resultId);
            }
            if (prev.length >= 2) {
                return [prev[1], resultId];
            }
            return [...prev, resultId];
        });
    };

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

    const resultSummary = useMemo(() => {
        if (!result) return null;
        const nodeResults = result.node_results || {};
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
    }, [result]);

    const resultSummaryTotal = useMemo(() => {
        if (!resultSummary) return 0;
        return Object.values(resultSummary).reduce((sum, value) => sum + value, 0);
    }, [resultSummary]);

    const reportText = useMemo(() => {
        if (!result?.final_output) return null;
        const reportEntry = (result.final_output as Record<string, any>).report;
        if (reportEntry && typeof reportEntry === "object" && typeof reportEntry.report === "string") {
            return reportEntry.report as string;
        }
        const entries = Object.values(result.final_output);
        for (const entry of entries) {
            if (isRecord(entry) && typeof entry.report === "string") {
                return entry.report;
            }
        }
        return null;
    }, [result]);

    const reportIsLarge = (reportText?.length ?? 0) > 5000;

    useEffect(() => {
        if (!reportIsLarge) {
            setRenderMarkdown(true);
        } else {
            setRenderMarkdown(false);
        }
    }, [reportIsLarge, reportText]);

    const rawOutput = useMemo(() => {
        if (!result?.final_output) return null;
        try {
            return JSON.stringify(result.final_output, null, 2);
        } catch {
            return null;
        }
    }, [result]);

    const intentLabel = selectedIntent?.label
        || catalog.find(item => item.intent === result?.intent)?.label
        || result?.intent
        || "분석";

    const intentDefinition = selectedIntent || catalog.find(item => item.intent === result?.intent) || null;
    const activeIntentValue = intentDefinition?.intent || result?.intent || null;
    const isBenchmarkIntent = activeIntentValue === "benchmark_retrieval";
    const requiresRunData = useMemo(() => {
        const nodes = intentDefinition?.nodes || selectedIntent?.nodes || [];
        return nodes.some(node => RUN_REQUIRED_MODULES.has(node.module));
    }, [intentDefinition, selectedIntent]);

    const prioritySummary = useMemo(() => {
        if (!result) return null;
        const finalOutput = result.final_output || {};
        for (const entry of Object.values(finalOutput)) {
            if (isPrioritySummary(entry)) return entry;
        }
        const nodeOutput = getNodeOutput(result.node_results, "priority_summary");
        if (isPrioritySummary(nodeOutput)) return nodeOutput;
        return null;
    }, [result]);

    const hasNodeError = useMemo(() => {
        if (!result?.node_results) return false;
        return Object.values(result.node_results).some((node) => Boolean(getNodeError(node)));
    }, [result]);

    return (
        <Layout>
            <div className="max-w-6xl mx-auto pb-20">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold tracking-tight mb-2">Analysis Lab</h1>
                    <p className="text-muted-foreground">
                        분석 클래스를 선택해 바로 실행하고 결과를 확인하세요.
                    </p>
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
                        <div className="bg-card border border-border rounded-xl p-6 shadow-sm h-full">
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
                                <div className="h-full flex flex-col items-center justify-center text-muted-foreground text-sm">
                                    <Activity className="w-6 h-6 mb-2" />
                                    분석 항목을 선택하면 결과가 여기에 표시됩니다.
                                </div>
                            )}

                            {result && (
                                <div className="space-y-6">
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                        <div className="border border-border rounded-lg p-3">
                                            <p className="text-xs text-muted-foreground">Intent</p>
                                            <p className="text-sm font-semibold mt-1">{intentLabel}</p>
                                        </div>
                                        <div className="border border-border rounded-lg p-3">
                                            <p className="text-xs text-muted-foreground">Duration</p>
                                            <p className="text-sm font-semibold mt-1">{formatDurationMs(result.duration_ms)}</p>
                                        </div>
                                        <div className="border border-border rounded-lg p-3">
                                            <p className="text-xs text-muted-foreground">Status</p>
                                            <p className="text-sm font-semibold mt-1">{result.is_complete ? "Complete" : "Partial"}</p>
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
                                        {saveError && (
                                            <span className="text-xs text-destructive">{saveError}</span>
                                        )}
                                    </div>

                                    {resultSummary && (
                                        <div className="border border-border rounded-xl p-4 bg-card">
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
                                            <div className="space-y-2">
                                                {selectedIntent.nodes.map(node => {
                                                    const status = getNodeStatus(result.node_results?.[node.id]);
                                                    return (
                                                        <div key={node.id} className="flex items-center justify-between border border-border rounded-lg px-3 py-2">
                                                            <div>
                                                                <p className="text-sm font-medium">{node.name}</p>
                                                                <p className="text-xs text-muted-foreground">{node.module}</p>
                                                            </div>
                                                            <StatusBadge status={status} />
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
                                                text={rawOutput || "{}"}
                                                height="20rem"
                                                className="bg-background border border-border rounded-lg p-3 text-xs"
                                            />
                                        ) : reportText ? (
                                            renderMarkdown ? (
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
                                                text={rawOutput || "{}"}
                                                height="20rem"
                                                className="bg-background border border-border rounded-lg p-3 text-xs"
                                            />
                                        )}
                                    </div>

                                    <AnalysisNodeOutputs
                                        nodeResults={result.node_results}
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
