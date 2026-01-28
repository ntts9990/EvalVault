import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Layout } from "../components/Layout";
import { AnalysisNodeOutputs } from "../components/AnalysisNodeOutputs";
import { MarkdownContent } from "../components/MarkdownContent";
import { PrioritySummaryPanel, type PrioritySummary } from "../components/PrioritySummaryPanel";
import { StatusBadge } from "../components/StatusBadge";
import { VirtualizedText } from "../components/VirtualizedText";
import {
    fetchAnalysisIntents,
    fetchAnalysisMetricSpecs,
    fetchAnalysisResult,
    type AnalysisIntentInfo,
    type AnalysisMetricSpec,
    type SavedAnalysisResult,
} from "../services/api";
import { ANALYSIS_LARGE_REPORT_THRESHOLD } from "../config/ui";
import { formatDateTime, formatDurationMs } from "../utils/format";
import { copyTextToClipboard } from "../utils/clipboard";
import {
    Activity,
    AlertCircle,
    ArrowLeft,
    Download,
    ExternalLink,
    Link2,
} from "lucide-react";

const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === "object" && value !== null;

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

const isPlainRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === "object" && value !== null && !Array.isArray(value);

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

function downloadText(filename: string, content: string, type: string) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
}

export function AnalysisResultView() {
    const { id } = useParams();
    const [result, setResult] = useState<SavedAnalysisResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [analysisCatalog, setAnalysisCatalog] = useState<AnalysisIntentInfo[]>([]);
    const [analysisCatalogError, setAnalysisCatalogError] = useState<string | null>(null);
    const [analysisMetricSpecs, setAnalysisMetricSpecs] = useState<AnalysisMetricSpec[]>([]);
    const [analysisMetricSpecError, setAnalysisMetricSpecError] = useState<string | null>(null);
    const [showRaw, setShowRaw] = useState(false);
    const [showAnalysisMetrics, setShowAnalysisMetrics] = useState(false);
    const [copyStatus, setCopyStatus] = useState<"idle" | "success" | "error">("idle");
    const [renderMarkdown, setRenderMarkdown] = useState(true);

    useEffect(() => {
        async function loadResult() {
            if (!id) {
                setError("Invalid result id");
                setLoading(false);
                return;
            }
            try {
                const data = await fetchAnalysisResult(id);
                setResult(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load result");
            } finally {
                setLoading(false);
            }
        }
        loadResult();
    }, [id]);

    useEffect(() => {
        let cancelled = false;
        fetchAnalysisIntents()
            .then((data) => {
                if (!cancelled) {
                    setAnalysisCatalog(data);
                }
            })
            .catch((err) => {
                if (!cancelled) {
                    setAnalysisCatalogError(
                        err instanceof Error ? err.message : "분석 카탈로그를 불러오지 못했습니다."
                    );
                }
            });
        return () => {
            cancelled = true;
        };
    }, []);

    useEffect(() => {
        let cancelled = false;
        fetchAnalysisMetricSpecs()
            .then((data) => {
                if (!cancelled) {
                    setAnalysisMetricSpecs(data);
                }
            })
            .catch((err) => {
                if (!cancelled) {
                    setAnalysisMetricSpecError(
                        err instanceof Error ? err.message : "분석 메트릭 스펙을 불러오지 못했습니다."
                    );
                }
            });
        return () => {
            cancelled = true;
        };
    }, []);

    const reportText = useMemo(() => {
        if (!result?.final_output) return null;
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

    const safeNodeResults = useMemo(() => {
        if (!result?.node_results || !isPlainRecord(result.node_results)) return null;
        return result.node_results;
    }, [result]);

    const intentDefinition = useMemo(() => {
        if (!result) return null;
        return analysisCatalog.find((intent) => intent.intent === result.intent) ?? null;
    }, [analysisCatalog, result]);

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

    const reportIsLarge = (reportText?.length ?? 0) > ANALYSIS_LARGE_REPORT_THRESHOLD;

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

    const metadataText = useMemo(() => {
        if (!result?.metadata) return null;
        try {
            return JSON.stringify(result.metadata, null, 2);
        } catch {
            return null;
        }
    }, [result]);

    const handleDownloadJson = () => {
        if (!result) return;
        const payload = JSON.stringify(result, null, 2);
        downloadText(`analysis-${result.result_id}.json`, payload, "application/json");
    };

    const handleDownloadReport = () => {
        if (!reportText || !result) return;
        downloadText(`analysis-${result.result_id}.md`, reportText, "text/markdown");
    };

    const handleCopyLink = async () => {
        if (typeof window === "undefined") return;
        const url = window.location.href;
        const success = await copyTextToClipboard(url);
        setCopyStatus(success ? "success" : "error");
        setTimeout(() => setCopyStatus("idle"), 1500);
    };

    const handleOpenNewTab = () => {
        if (typeof window === "undefined") return;
        window.open(window.location.href, "_blank", "noopener,noreferrer");
    };

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

    const nodeSummary = useMemo(() => {
        if (!safeNodeResults) return null;
        const counts = {
            completed: 0,
            failed: 0,
            skipped: 0,
            running: 0,
            pending: 0,
        };
        let failedCount = 0;
        Object.values(safeNodeResults).forEach((node) => {
            const status = getNodeStatus(node);
            if (counts[status as keyof typeof counts] !== undefined) {
                counts[status as keyof typeof counts] += 1;
            }
            if (status === "failed" || getNodeError(node)) {
                failedCount += 1;
            }
        });
        const total = Object.values(counts).reduce((sum, value) => sum + value, 0);
        return { counts, total, failedCount };
    }, [safeNodeResults]);

    const showAnalysisMetricSection =
        analysisMetricGroups.length > 0 || Boolean(analysisMetricSpecError || analysisCatalogError);

    return (
        <Layout>
            <div className="max-w-5xl mx-auto pb-20">
                <div className="mb-8 flex items-center gap-3">
                    <Link
                        to="/analysis"
                        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
                    >
                        <ArrowLeft className="w-4 h-4" /> 분석 실험실로 돌아가기
                    </Link>
                </div>

                {loading && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Activity className="w-4 h-4 animate-spin" /> 로딩 중...
                    </div>
                )}

                {error && (
                    <div className="p-4 border border-destructive/30 bg-destructive/10 rounded-xl text-destructive flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        <span>{error}</span>
                    </div>
                )}

                {!loading && result && (
                    <div className="space-y-6">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                                <h1 className="text-3xl font-bold tracking-tight font-display">{result.label}</h1>
                                <p className="text-sm text-muted-foreground mt-1">
                                    저장된 분석 결과를 확인합니다.
                                </p>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
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
                                <button
                                    type="button"
                                    onClick={handleCopyLink}
                                    className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40"
                                >
                                    <Link2 className="w-3 h-3" /> 링크 복사
                                </button>
                                <button
                                    type="button"
                                    onClick={handleOpenNewTab}
                                    className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40"
                                >
                                    <ExternalLink className="w-3 h-3" /> 새 창 열기
                                </button>
                                <button
                                    type="button"
                                    onClick={handleDownloadJson}
                                    className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40"
                                >
                                    <Download className="w-3 h-3" /> JSON 다운로드
                                </button>
                                <button
                                    type="button"
                                    onClick={handleDownloadReport}
                                    disabled={!reportText}
                                    className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40 disabled:opacity-50"
                                >
                                    <Download className="w-3 h-3" /> 리포트 다운로드
                                </button>
                                {copyStatus === "success" && (
                                    <span className="text-xs text-emerald-600">링크 복사됨</span>
                                )}
                                {copyStatus === "error" && (
                                    <span className="text-xs text-rose-600">복사 실패</span>
                                )}
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                            <div className="surface-panel p-4">
                                <p className="text-xs text-muted-foreground">결과 상태</p>
                                <div className="mt-2">
                                    <StatusBadge status={result.is_complete ? "completed" : "incomplete"} />
                                </div>
                                <p className="text-xs text-muted-foreground mt-2">
                                    저장 {formatDateTime(result.created_at)}
                                </p>
                            </div>
                            <div className="surface-panel p-4">
                                <p className="text-xs text-muted-foreground">분석 유형</p>
                                <p className="text-lg font-semibold mt-2">{result.intent}</p>
                                {result.pipeline_id && (
                                    <p className="text-xs text-muted-foreground mt-2">
                                        Pipeline {result.pipeline_id}
                                    </p>
                                )}
                            </div>
                            <div className="surface-panel p-4">
                                <p className="text-xs text-muted-foreground">처리 시간</p>
                                <p className="text-2xl font-semibold mt-2">
                                    {formatDurationMs(result.duration_ms)}
                                </p>
                                <p className="text-xs text-muted-foreground mt-2">
                                    시작 {formatDateTime(result.started_at)}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    종료 {formatDateTime(result.finished_at)}
                                </p>
                            </div>
                            <div className="surface-panel p-4">
                                <p className="text-xs text-muted-foreground">노드 상태</p>
                                {nodeSummary ? (
                                    <>
                                        <div className="mt-2 flex flex-wrap gap-2">
                                            {Object.entries(nodeSummary.counts).map(([status, count]) => {
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
                                        <p className="text-xs text-muted-foreground mt-2">
                                            실패 노드 {nodeSummary.failedCount}개 / 총 {nodeSummary.total}개
                                        </p>
                                    </>
                                ) : (
                                    <p className="text-xs text-muted-foreground mt-2">
                                        노드 정보 없음
                                    </p>
                                )}
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="surface-panel p-4">
                                <p className="text-xs text-muted-foreground">Query</p>
                                <p className="text-sm font-medium mt-2">
                                    {result.query || "-"}
                                </p>
                            </div>
                            <div className="surface-panel p-4">
                                <p className="text-xs text-muted-foreground">Run ID</p>
                                <p className="text-sm font-medium mt-2">
                                    {result.run_id || "샘플 데이터"}
                                </p>
                            </div>
                        </div>
                        {(result.profile || (result.tags && result.tags.length > 0)) && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {result.profile && (
                                    <div className="surface-panel p-4">
                                        <p className="text-xs text-muted-foreground">Profile</p>
                                        <p className="text-sm font-medium mt-2">{result.profile}</p>
                                    </div>
                                )}
                                {result.tags && result.tags.length > 0 && (
                                    <div className="surface-panel p-4">
                                        <p className="text-xs text-muted-foreground">Tags</p>
                                        <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                                            {result.tags.map((tag) => (
                                                <span
                                                    key={`${result.result_id}-${tag}`}
                                                    className="px-2 py-0.5 rounded-full bg-secondary border border-border"
                                                >
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {result.node_results && (
                            <div>
                                <h2 className="text-sm font-semibold mb-3">실행 단계</h2>
                                <div className="space-y-2">
                                    {Object.entries(result.node_results).map(([nodeId, node]) => {
                                        const status = getNodeStatus(node);
                                        const errorText = getNodeError(node);
                                        return (
                                            <div
                                                key={nodeId}
                                                className="flex items-center justify-between border border-border rounded-lg px-3 py-2"
                                            >
                                                <div>
                                                    <p className="text-sm font-medium">{nodeId}</p>
                                                    {errorText && (
                                                        <p className="text-xs text-rose-600">
                                                            {errorText}
                                                        </p>
                                                    )}
                                                </div>
                                                <StatusBadge status={status} />
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {metadataText && (
                            <div>
                                <h2 className="text-sm font-semibold mb-3">메타데이터</h2>
                                <VirtualizedText
                                    text={metadataText}
                                    height="16rem"
                                    className="bg-background border border-border rounded-lg p-4 text-xs"
                                />
                            </div>
                        )}

                        {prioritySummary && (
                            <PrioritySummaryPanel summary={prioritySummary} />
                        )}

                        {showAnalysisMetricSection && (
                            <div className="surface-panel p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h2 className="text-sm font-semibold">추가 분석 지표</h2>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            분석 모듈에서 추출된 지표를 신호 그룹으로 묶어 표시합니다.
                                        </p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => setShowAnalysisMetrics((prev) => !prev)}
                                        className="text-[11px] text-muted-foreground hover:text-foreground"
                                    >
                                        {showAnalysisMetrics ? "접기" : "표시"}
                                    </button>
                                </div>
                                {analysisCatalogError && (
                                    <p className="mt-2 text-xs text-rose-500">
                                        {analysisCatalogError}
                                    </p>
                                )}
                                {analysisMetricSpecError && (
                                    <p className="mt-2 text-xs text-rose-500">
                                        {analysisMetricSpecError}
                                    </p>
                                )}
                                {!showAnalysisMetrics ? (
                                    <p className="mt-3 text-xs text-muted-foreground">
                                        추가 분석 지표는 선택 시에만 표시됩니다.
                                    </p>
                                ) : analysisMetricGroups.length === 0 ? (
                                    <p className="mt-3 text-xs text-muted-foreground">
                                        표시할 추가 분석 지표가 없습니다.
                                    </p>
                                ) : (
                                    <div className="mt-4 space-y-4">
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

                        <div>
                            <h2 className="text-sm font-semibold mb-3">결과 출력</h2>
                            {showRaw ? (
                                <VirtualizedText
                                    text={rawOutput || "{}"}
                                    height="60vh"
                                    className="bg-background border border-border rounded-lg p-4 text-xs"
                                />
                            ) : reportText ? (
                                renderMarkdown ? (
                                    <div className="bg-background border border-border rounded-lg p-6 text-sm max-h-[60vh] overflow-auto">
                                        <MarkdownContent text={reportText} />
                                    </div>
                                ) : (
                                    <VirtualizedText
                                        text={reportText}
                                        height="60vh"
                                        className="bg-background border border-border rounded-lg p-4 text-xs"
                                    />
                                )
                            ) : (
                                <VirtualizedText
                                    text={rawOutput || "{}"}
                                    height="60vh"
                                    className="bg-background border border-border rounded-lg p-4 text-xs"
                                />
                            )}
                        </div>

                        <AnalysisNodeOutputs
                            nodeResults={result.node_results || undefined}
                            title="노드 상세 출력"
                        />
                    </div>
                )}
            </div>
        </Layout>
    );
}
