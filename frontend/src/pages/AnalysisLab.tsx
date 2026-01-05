import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { Layout } from "../components/Layout";
import {
    fetchAnalysisIntents,
    fetchAnalysisHistory,
    fetchRuns,
    runAnalysis,
    saveAnalysisResult,
    type AnalysisHistoryItem,
    type AnalysisIntentInfo,
    type AnalysisResult,
    type RunSummary,
} from "../services/api";
import { formatDateTime, formatDurationMs } from "../utils/format";
import {
    Activity,
    AlertCircle,
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
};

const STATUS_META: Record<string, { label: string; color: string }> = {
    completed: { label: "완료", color: "text-emerald-600" },
    failed: { label: "실패", color: "text-rose-600" },
    skipped: { label: "스킵", color: "text-amber-600" },
    running: { label: "실행 중", color: "text-blue-600" },
    pending: { label: "대기", color: "text-muted-foreground" },
};

export function AnalysisLab() {
    const [catalog, setCatalog] = useState<AnalysisIntentInfo[]>([]);
    const [catalogError, setCatalogError] = useState<string | null>(null);
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [runError, setRunError] = useState<string | null>(null);
    const [selectedRunId, setSelectedRunId] = useState<string>("");
    const [selectedIntent, setSelectedIntent] = useState<AnalysisIntentInfo | null>(null);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showRaw, setShowRaw] = useState(false);
    const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
    const [historyError, setHistoryError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [lastQuery, setLastQuery] = useState<string | null>(null);
    const [savedResultId, setSavedResultId] = useState<string | null>(null);

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

    const groupedCatalog = useMemo(() => {
        const grouped: Record<string, AnalysisIntentInfo[]> = {};
        for (const item of catalog) {
            const key = item.category || "analysis";
            if (!grouped[key]) grouped[key] = [];
            grouped[key].push(item);
        }
        return grouped;
    }, [catalog]);

    const handleRun = async (intent: AnalysisIntentInfo) => {
        if (!intent.available || loading) return;
        setSelectedIntent(intent);
        setError(null);
        setSaveError(null);
        setResult(null);
        setSavedResultId(null);
        setLastQuery(intent.sample_query);
        setLoading(true);
        try {
            const analysis = await runAnalysis(intent.sample_query, selectedRunId || undefined, intent.intent);
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
        try {
            const payload = {
                intent: result.intent,
                query: lastQuery || selectedIntent?.sample_query || result.intent,
                run_id: selectedRunId || null,
                pipeline_id: result.pipeline_id || null,
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
        Object.values(nodeResults).forEach((node: any) => {
            const status = node?.status || "pending";
            if (counts[status as keyof typeof counts] !== undefined) {
                counts[status as keyof typeof counts] += 1;
            }
        });
        return counts;
    }, [result]);

    const reportText = useMemo(() => {
        if (!result?.final_output) return null;
        const entries = Object.values(result.final_output);
        for (const entry of entries) {
            if (entry && typeof entry === "object" && "report" in entry && typeof (entry as any).report === "string") {
                return (entry as any).report as string;
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

    const intentLabel = selectedIntent?.label
        || catalog.find(item => item.intent === result?.intent)?.label
        || result?.intent
        || "분석";

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
                                {runs.map(run => (
                                    <option key={run.run_id} value={run.run_id}>
                                        {run.dataset_name} · {run.model_name} · {run.run_id.slice(0, 8)}
                                    </option>
                                ))}
                            </select>
                            {runError && (
                                <p className="text-xs text-destructive mt-2">{runError}</p>
                            )}
                            {!selectedRunId && (
                                <p className="text-xs text-muted-foreground mt-3">
                                    Run을 선택하지 않으면 샘플 메트릭 기반으로 분석합니다.
                                </p>
                            )}
                        </div>

                        <div className="bg-card border border-border rounded-xl p-4 shadow-sm">
                            <h3 className="font-semibold mb-3 flex items-center gap-2">
                                <Activity className="w-4 h-4 text-primary" /> 저장된 결과
                            </h3>
                            {historyError && (
                                <p className="text-xs text-destructive mb-2">{historyError}</p>
                            )}
                            {history.length === 0 ? (
                                <p className="text-xs text-muted-foreground">
                                    아직 저장된 분석 결과가 없습니다.
                                </p>
                            ) : (
                                <div className="space-y-2">
                                    {history.map(item => (
                                        <Link
                                            key={item.result_id}
                                            to={`/analysis/results/${item.result_id}`}
                                            className="block border border-border rounded-lg p-3 hover:border-primary/40 hover:shadow-sm transition-all"
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
                                                {item.run_id ? `Run ${item.run_id.slice(0, 8)}` : "샘플 데이터"}
                                            </p>
                                        </Link>
                                    ))}
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
                                            const isDisabled = !intent.available || loading;
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
                                        <div className="flex flex-wrap gap-3 text-xs">
                                            {Object.entries(resultSummary).map(([status, count]) => {
                                                if (count === 0) return null;
                                                const meta = STATUS_META[status] || STATUS_META.pending;
                                                return (
                                                    <div key={status} className="px-3 py-1 rounded-full bg-secondary border border-border">
                                                        <span className={meta.color}>{meta.label}</span> {count}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}

                                    {selectedIntent?.nodes.length ? (
                                        <div>
                                            <h3 className="text-sm font-semibold mb-3">실행 단계</h3>
                                            <div className="space-y-2">
                                                {selectedIntent.nodes.map(node => {
                                                    const nodeResult = result.node_results?.[node.id];
                                                    const status = nodeResult?.status || "pending";
                                                    const meta = STATUS_META[status] || STATUS_META.pending;
                                                    return (
                                                        <div key={node.id} className="flex items-center justify-between border border-border rounded-lg px-3 py-2">
                                                            <div>
                                                                <p className="text-sm font-medium">{node.name}</p>
                                                                <p className="text-xs text-muted-foreground">{node.module}</p>
                                                            </div>
                                                            <div className={`text-xs font-semibold ${meta.color}`}>
                                                                {meta.label}
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
                                            <button
                                                type="button"
                                                onClick={() => setShowRaw(prev => !prev)}
                                                className="text-xs text-muted-foreground hover:text-foreground"
                                            >
                                                {showRaw ? "리포트 보기" : "RAW JSON"}
                                            </button>
                                        </div>
                                        {showRaw ? (
                                            <pre className="bg-background border border-border rounded-lg p-3 text-xs overflow-auto max-h-80">
                                                {rawOutput || "{}"}
                                            </pre>
                                        ) : reportText ? (
                                            <div className="bg-background border border-border rounded-lg p-4 text-sm max-h-80 overflow-auto">
                                                <div className="prose prose-sm max-w-none">
                                                    <ReactMarkdown>{reportText}</ReactMarkdown>
                                                </div>
                                            </div>
                                        ) : (
                                            <pre className="bg-background border border-border rounded-lg p-3 text-xs overflow-auto max-h-80">
                                                {rawOutput || "{}"}
                                            </pre>
                                        )}
                                    </div>

                                    {result.node_results && Object.values(result.node_results).some((node: any) => node?.error) && (
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
