import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Layout } from "../components/Layout";
import { type PriorityCase, type PrioritySummary } from "../components/PrioritySummaryPanel";
import { StatusBadge } from "../components/StatusBadge";
import {
    fetchAnalysisIntents,
    fetchAnalysisMetricSpecs,
    fetchAnalysisResult,
    fetchPromptDiff,
    type AnalysisIntentInfo,
    type AnalysisMetricSpec,
    type SavedAnalysisResult,
    type PromptDiffResponse,
} from "../services/api";
import { formatDateTime, formatDurationMs } from "../utils/format";
import { Activity, AlertCircle, ArrowLeft, GitCompare, Download, FileText, ChevronDown, ChevronUp } from "lucide-react";

const METRIC_EPSILON = 0.0001;

const METRIC_EXCLUDE_KEYS = new Set([
    "per_query",
    "statistics",
    "node_results",
    "contexts",
    "documents",
    "queries",
    "raw",
    "report",
    "evidence",
]);

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

function extractNumericMetrics(output: Record<string, unknown> | null) {
    const metrics: Record<string, number> = {};
    const visited = new Set<object>();

    const walk = (value: unknown, path: string, depth: number) => {
        if (value === null || value === undefined) return;
        if (depth > 4) return;

        if (typeof value === "number" && Number.isFinite(value)) {
            metrics[path] = value;
            return;
        }

        if (Array.isArray(value)) {
            if (value.length === 0) return;
            const numeric = value.filter(
                (item): item is number => typeof item === "number" && Number.isFinite(item)
            );
            if (numeric.length === value.length) {
                const avg = numeric.reduce((sum, item) => sum + item, 0) / numeric.length;
                metrics[`${path}.avg`] = avg;
            }
            return;
        }

        if (isRecord(value)) {
            if (visited.has(value)) return;
            visited.add(value);
            for (const [key, next] of Object.entries(value)) {
                if (METRIC_EXCLUDE_KEYS.has(key)) continue;
                const nextPath = path ? `${path}.${key}` : key;
                walk(next, nextPath, depth + 1);
            }
        }
    };

    walk(output, "", 0);
    return metrics;
}

type AnalysisMetricEntry = {
    key: string;
    spec: AnalysisMetricSpec;
    value: number;
    nodeId: string;
};

function buildAnalysisMetricEntries(
    result: SavedAnalysisResult | null,
    intentDefinition: AnalysisIntentInfo | null,
    specs: AnalysisMetricSpec[]
): AnalysisMetricEntry[] {
    if (!result || !intentDefinition || specs.length === 0) return [];
    if (!result.node_results || !isPlainRecord(result.node_results)) return [];

    const moduleNodes = new Map<string, string[]>();
    intentDefinition.nodes.forEach((node) => {
        const list = moduleNodes.get(node.module) || [];
        list.push(node.id);
        moduleNodes.set(node.module, list);
    });

    const entries: AnalysisMetricEntry[] = [];
    const nodeResults = result.node_results;

    specs.forEach((spec) => {
        const nodeIds = moduleNodes.get(spec.module_id) || [];
        nodeIds.forEach((nodeId) => {
            const node = nodeResults[nodeId];
            if (!isPlainRecord(node)) return;
            const output = node.output;
            if (!isPlainRecord(output)) return;
            const value = getNestedValue(output, spec.output_path);
            if (value === null) return;
            entries.push({ key: `${spec.key}:${nodeId}`, spec, value, nodeId });
        });
    });

    return entries;
}

function buildNodeMap(result: SavedAnalysisResult | null) {
    const map: Record<string, { status: string; error?: string | null }> = {};
    if (!result?.node_results) return map;
    Object.entries(result.node_results).forEach(([nodeId, node]) => {
        const nodeRecord = isRecord(node) ? node : null;
        const statusValue = nodeRecord?.status;
        const errorValue = nodeRecord?.error;
        const status = typeof statusValue === "string" ? statusValue : "pending";
        const error = typeof errorValue === "string" ? errorValue : errorValue ? String(errorValue) : null;
        map[nodeId] = {
            status,
            error,
        };
    });
    return map;
}

function formatMetricValue(value: number | undefined) {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return "-";
    }
    return value.toFixed(4);
}

function formatSignedDelta(value: number | null, digits: number = 4) {
    if (value === null || value === undefined || Number.isNaN(value)) {
        return "-";
    }
    const sign = value > 0 ? "+" : "";
    return `${sign}${value.toFixed(digits)}`;
}

function isPrioritySummary(value: unknown): value is PrioritySummary {
    if (!isRecord(value)) return false;
    return Array.isArray(value.bottom_cases) || Array.isArray(value.impact_cases);
}

function extractPrioritySummary(result: SavedAnalysisResult | null): PrioritySummary | null {
    if (!result) return null;
    const finalOutput = result.final_output || {};
    for (const entry of Object.values(finalOutput)) {
        if (isPrioritySummary(entry)) return entry;
    }
    const nodeResults = isRecord(result.node_results) ? result.node_results : null;
    const priorityNode = nodeResults && isRecord(nodeResults.priority_summary)
        ? nodeResults.priority_summary
        : null;
    const nodeOutput = priorityNode ? priorityNode.output : null;
    if (isPrioritySummary(nodeOutput)) return nodeOutput;
    return null;
}

function uniqueCases(cases: PriorityCase[]) {
    const seen = new Set<string>();
    const unique: PriorityCase[] = [];
    for (const item of cases) {
        const key = item.test_case_id || item.question_preview || JSON.stringify(item);
        if (seen.has(key)) continue;
        seen.add(key);
        unique.push(item);
    }
    return unique;
}

function buildCaseSet(cases: PriorityCase[]) {
    const ids = new Set<string>();
    for (const item of cases) {
        if (item.test_case_id) {
            ids.add(item.test_case_id);
        }
    }
    return ids;
}

function aggregateFailedMetrics(cases: PriorityCase[]) {
    const counts = new Map<string, number>();
    for (const item of cases) {
        for (const metric of item.failed_metrics || []) {
            counts.set(metric, (counts.get(metric) || 0) + 1);
        }
    }
    return counts;
}

function ResultCard({
    result,
    variant,
    failureCount,
}: {
    result: SavedAnalysisResult;
    variant: "A" | "B";
    failureCount: number;
}) {
    const queryText = result.query
        ? result.query.length > 120
            ? `${result.query.slice(0, 120)}...`
            : result.query
        : "N/A";
    const completionLabel = result.is_complete ? "완료" : "미완료";
    const completionClass = result.is_complete
        ? "text-emerald-700 bg-emerald-50 border-emerald-200"
        : "text-amber-700 bg-amber-50 border-amber-200";

    return (
        <div className="surface-panel p-4 space-y-4">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <p className="text-xs text-muted-foreground">{variant}</p>
                    <h2 className="text-lg font-semibold">{result.label}</h2>
                    <p className="text-xs text-muted-foreground mt-1">
                        {formatDateTime(result.created_at)}
                    </p>
                </div>
                <div className="flex flex-col items-end gap-2">
                    <span
                        className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${completionClass}`}
                    >
                        {completionLabel}
                    </span>
                    <Link
                        to={`/analysis/results/${result.result_id}`}
                        className="text-xs text-primary hover:underline"
                    >
                        결과 보기
                    </Link>
                </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <div>
                    <p className="text-xs text-muted-foreground">분석 유형</p>
                    <p className="font-medium">{result.intent}</p>
                </div>
                <div>
                    <p className="text-xs text-muted-foreground">처리 시간</p>
                    <p className="font-medium">{formatDurationMs(result.duration_ms)}</p>
                </div>
                <div>
                    <p className="text-xs text-muted-foreground">Run ID</p>
                    <p className="font-medium">{result.run_id || "샘플 데이터"}</p>
                </div>
                <div>
                    <p className="text-xs text-muted-foreground">실패 노드</p>
                    <p className="font-medium">{failureCount}개</p>
                </div>
                {result.profile && (
                    <div>
                        <p className="text-xs text-muted-foreground">Profile</p>
                        <p className="font-medium">{result.profile}</p>
                    </div>
                )}
            </div>
            {result.tags && result.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                    {result.tags.map((tag) => (
                        <span
                            key={`${result.result_id}-${tag}`}
                            className="px-2 py-0.5 rounded-full bg-secondary border border-border"
                        >
                            {tag}
                        </span>
                    ))}
                </div>
            )}
            <div className="text-xs text-muted-foreground">
                <p className="text-[10px] uppercase tracking-wide">Query</p>
                <p className="text-sm text-foreground mt-1 break-words">{queryText}</p>
            </div>
        </div>
    );
}

export function AnalysisCompareView() {
    const [searchParams] = useSearchParams();
    const idA = searchParams.get("left") ?? searchParams.get("a");
    const idB = searchParams.get("right") ?? searchParams.get("b");
    const [resultA, setResultA] = useState<SavedAnalysisResult | null>(null);
    const [resultB, setResultB] = useState<SavedAnalysisResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showOnlyDiff, setShowOnlyDiff] = useState(true);
    const [showAllMetrics, setShowAllMetrics] = useState(false);
    const [showOnlyMetricChanges, setShowOnlyMetricChanges] = useState(true);
    const [analysisCatalog, setAnalysisCatalog] = useState<AnalysisIntentInfo[]>([]);
    const [analysisCatalogError, setAnalysisCatalogError] = useState<string | null>(null);
    const [analysisMetricSpecs, setAnalysisMetricSpecs] = useState<AnalysisMetricSpec[]>([]);
    const [analysisMetricSpecError, setAnalysisMetricSpecError] = useState<string | null>(null);
    const [showAnalysisMetrics, setShowAnalysisMetrics] = useState(false);

    const [promptDiff, setPromptDiff] = useState<PromptDiffResponse | null>(null);
    const [promptDiffLoading, setPromptDiffLoading] = useState(false);
    const [promptDiffError, setPromptDiffError] = useState<string | null>(null);
    const [showPromptDiffDetail, setShowPromptDiffDetail] = useState(false);

    useEffect(() => {
        async function loadResults() {
            if (!idA || !idB) {
                setLoading(false);
                return;
            }
            setLoading(true);
            setError(null);
            try {
                const [dataA, dataB] = await Promise.all([
                    fetchAnalysisResult(idA),
                    fetchAnalysisResult(idB),
                ]);
                setResultA(dataA);
                setResultB(dataB);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load comparison results");
            } finally {
                setLoading(false);
            }
        }
        loadResults();
    }, [idA, idB]);

    useEffect(() => {
        async function loadPromptDiff() {
            if (!resultA?.run_id || !resultB?.run_id) {
                setPromptDiff(null);
                return;
            }
            setPromptDiffLoading(true);
            setPromptDiffError(null);
            try {
                const data = await fetchPromptDiff(resultA.run_id, resultB.run_id);
                setPromptDiff(data);
            } catch (err) {
                console.error("Failed to load prompt diff", err);
                setPromptDiffError("프롬프트 비교 정보를 불러오지 못했습니다.");
            } finally {
                setPromptDiffLoading(false);
            }
        }
        if (resultA && resultB) {
            loadPromptDiff();
        }
    }, [resultA, resultB]);

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

    const prioritySummaryA = useMemo(() => extractPrioritySummary(resultA), [resultA]);
    const prioritySummaryB = useMemo(() => extractPrioritySummary(resultB), [resultB]);

    const metricRows = useMemo(() => {
        if (!resultA || !resultB) return [];
        const metricsA = extractNumericMetrics(resultA.final_output);
        const metricsB = extractNumericMetrics(resultB.final_output);
        const keys = Array.from(new Set([...Object.keys(metricsA), ...Object.keys(metricsB)]));

        const rows = keys.map((key) => {
            const aValue = metricsA[key];
            const bValue = metricsB[key];
            const delta = aValue !== undefined && bValue !== undefined ? bValue - aValue : null;
            return {
                key,
                aValue,
                bValue,
                delta,
            };
        });

        rows.sort((left, right) => {
            const leftDelta = Math.abs(left.delta ?? 0);
            const rightDelta = Math.abs(right.delta ?? 0);
            return rightDelta - leftDelta;
        });

        return rows;
    }, [resultA, resultB]);

    const intentDefinitionA = useMemo(() => {
        if (!resultA) return null;
        return analysisCatalog.find((intent) => intent.intent === resultA.intent) ?? null;
    }, [analysisCatalog, resultA]);

    const intentDefinitionB = useMemo(() => {
        if (!resultB) return null;
        return analysisCatalog.find((intent) => intent.intent === resultB.intent) ?? null;
    }, [analysisCatalog, resultB]);

    const analysisEntriesA = useMemo(
        () => buildAnalysisMetricEntries(resultA, intentDefinitionA, analysisMetricSpecs),
        [resultA, intentDefinitionA, analysisMetricSpecs]
    );

    const analysisEntriesB = useMemo(
        () => buildAnalysisMetricEntries(resultB, intentDefinitionB, analysisMetricSpecs),
        [resultB, intentDefinitionB, analysisMetricSpecs]
    );

    const analysisMetricGroups = useMemo(() => {
        if (analysisMetricSpecs.length === 0) return [];
        const mapA = new Map<string, AnalysisMetricEntry>();
        const mapB = new Map<string, AnalysisMetricEntry>();

        analysisEntriesA.forEach((entry) => mapA.set(entry.key, entry));
        analysisEntriesB.forEach((entry) => mapB.set(entry.key, entry));

        const keys = new Set<string>([...mapA.keys(), ...mapB.keys()]);
        const groupMap = new Map<
            string,
            {
                id: string;
                label: string;
                items: {
                    key: string;
                    label: string;
                    description: string;
                    nodeId: string;
                    aValue?: number;
                    bValue?: number;
                    delta: number | null;
                }[];
            }
        >();

        keys.forEach((key) => {
            const entryA = mapA.get(key);
            const entryB = mapB.get(key);
            const spec = entryA?.spec ?? entryB?.spec;
            if (!spec) {
                return;
            }
            const nodeId = entryA?.nodeId ?? entryB?.nodeId ?? "";
            const aValue = entryA?.value;
            const bValue = entryB?.value;
            const delta =
                typeof aValue === "number" && typeof bValue === "number" ? bValue - aValue : null;
            const groupId = spec.signal_group;
            const label = SIGNAL_GROUP_LABELS[groupId] || groupId;
            if (!groupMap.has(groupId)) {
                groupMap.set(groupId, { id: groupId, label, items: [] });
            }
            groupMap.get(groupId)?.items.push({
                key,
                label: nodeId ? `${spec.label} (${nodeId})` : spec.label,
                description: spec.description,
                nodeId,
                aValue,
                bValue,
                delta,
            });
        });

        const orderIndex = new Map(
            SIGNAL_GROUP_ORDER.map((group, index) => [group, index])
        );

        return Array.from(groupMap.values())
            .map((group) => ({
                ...group,
                items: group.items.sort((a, b) => a.label.localeCompare(b.label)),
            }))
            .sort((left, right) => {
                const leftOrder = orderIndex.get(left.id) ?? 999;
                const rightOrder = orderIndex.get(right.id) ?? 999;
                return leftOrder - rightOrder;
            });
    }, [analysisEntriesA, analysisEntriesB, analysisMetricSpecs]);

    const priorityDiff = useMemo(() => {
        const priorityA = prioritySummaryA;
        const priorityB = prioritySummaryB;
        if (!priorityA || !priorityB) return null;

        const bottomA = buildCaseSet(priorityA.bottom_cases || []);
        const bottomB = buildCaseSet(priorityB.bottom_cases || []);
        const impactA = buildCaseSet(priorityA.impact_cases || []);
        const impactB = buildCaseSet(priorityB.impact_cases || []);

        const buildDelta = (setA: Set<string>, setB: Set<string>) => {
            const added = Array.from(setB).filter((id) => !setA.has(id));
            const removed = Array.from(setA).filter((id) => !setB.has(id));
            const shared = Array.from(setA).filter((id) => setB.has(id));
            return { added, removed, shared };
        };

        const bottomDelta = buildDelta(bottomA, bottomB);
        const impactDelta = buildDelta(impactA, impactB);

        const combinedA = uniqueCases([
            ...(priorityA.bottom_cases || []),
            ...(priorityA.impact_cases || []),
        ]);
        const combinedB = uniqueCases([
            ...(priorityB.bottom_cases || []),
            ...(priorityB.impact_cases || []),
        ]);
        const metricCountsA = aggregateFailedMetrics(combinedA);
        const metricCountsB = aggregateFailedMetrics(combinedB);

        const metricKeys = new Set([...metricCountsA.keys(), ...metricCountsB.keys()]);
        const metricDeltas = Array.from(metricKeys).map((metric) => {
            const aCount = metricCountsA.get(metric) || 0;
            const bCount = metricCountsB.get(metric) || 0;
            return {
                metric,
                aCount,
                bCount,
                delta: bCount - aCount,
            };
        });
        metricDeltas.sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta));

        return {
            bottom: bottomDelta,
            impact: impactDelta,
            metricDeltas,
        };
    }, [prioritySummaryA, prioritySummaryB]);

    const nodeRows = useMemo(() => {
        if (!resultA || !resultB) return [];
        const mapA = buildNodeMap(resultA);
        const mapB = buildNodeMap(resultB);
        const nodeIds = Array.from(new Set([...Object.keys(mapA), ...Object.keys(mapB)]));

        const rows = nodeIds.map((nodeId) => {
            const aNode = mapA[nodeId];
            const bNode = mapB[nodeId];
            const aStatus = aNode?.status || "missing";
            const bStatus = bNode?.status || "missing";
            const diff = aStatus !== bStatus || aNode?.error !== bNode?.error;
            return {
                nodeId,
                aStatus,
                bStatus,
                aError: aNode?.error,
                bError: bNode?.error,
                diff,
            };
        });
        rows.sort((left, right) => {
            if (left.diff !== right.diff) return left.diff ? -1 : 1;
            return left.nodeId.localeCompare(right.nodeId);
        });
        return rows;
    }, [resultA, resultB]);

    const filteredNodes = useMemo(() => {
        if (!showOnlyDiff) return nodeRows;
        return nodeRows.filter((row) => row.diff);
    }, [nodeRows, showOnlyDiff]);

    const failureCountA = nodeRows.filter(
        (row) => row.aStatus === "failed" || row.aError
    ).length;
    const failureCountB = nodeRows.filter(
        (row) => row.bStatus === "failed" || row.bError
    ).length;

    const nodeDiffCount = nodeRows.filter((row) => row.diff).length;
    const failureDelta = failureCountB - failureCountA;
    const failureDeltaClass =
        failureDelta > 0
            ? "text-rose-600"
            : failureDelta < 0
                ? "text-emerald-600"
                : "text-muted-foreground";
    const failureDeltaLabel =
        failureDelta > 0 ? "악화" : failureDelta < 0 ? "개선" : "변화 없음";
    const failureDeltaDisplay =
        failureDelta === 0 ? "변화 없음" : `${failureDeltaLabel} ${Math.abs(failureDelta)}개`;

    const metricStats = useMemo(() => {
        const stats = {
            total: metricRows.length,
            changed: 0,
            increased: 0,
            decreased: 0,
            unchanged: 0,
            missing: 0,
        };
        metricRows.forEach((row) => {
            if (row.delta === null || row.delta === undefined || Number.isNaN(row.delta)) {
                stats.missing += 1;
                return;
            }
            if (Math.abs(row.delta) < METRIC_EPSILON) {
                stats.unchanged += 1;
                return;
            }
            stats.changed += 1;
            if (row.delta > 0) stats.increased += 1;
            if (row.delta < 0) stats.decreased += 1;
        });
        return stats;
    }, [metricRows]);

    const metricRowsView = useMemo(() => {
        let rows = metricRows;
        if (showOnlyMetricChanges) {
            rows = rows.filter(
                (row) =>
                    row.delta !== null &&
                    row.delta !== undefined &&
                    Math.abs(row.delta) >= METRIC_EPSILON
            );
        }
        return showAllMetrics ? rows : rows.slice(0, 20);
    }, [metricRows, showOnlyMetricChanges, showAllMetrics]);

    const showAnalysisMetricSection =
        analysisMetricGroups.length > 0 || Boolean(analysisMetricSpecError || analysisCatalogError);

    const durationDelta = useMemo(() => {
        if (!resultA || !resultB) return null;
        if (typeof resultA.duration_ms !== "number" || typeof resultB.duration_ms !== "number") {
            return null;
        }
        return resultB.duration_ms - resultA.duration_ms;
    }, [resultA, resultB]);

    const durationDeltaClass =
        durationDelta === null
            ? "text-muted-foreground"
            : durationDelta > 0
                ? "text-rose-600"
                : durationDelta < 0
                    ? "text-emerald-600"
                    : "text-muted-foreground";
    const durationDeltaLabel =
        durationDelta === null
            ? "-"
            : durationDelta > 0
                ? "지연"
                : durationDelta < 0
                    ? "단축"
                    : "변화 없음";
    const durationDeltaDisplay =
        durationDelta === null
            ? "-"
            : durationDelta === 0
                ? "변화 없음"
                : `${durationDeltaLabel} ${formatDurationMs(Math.abs(durationDelta))}`;

    return (
        <Layout>
            <div className="max-w-6xl mx-auto pb-20">
                <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
                    <Link
                        to="/analysis"
                        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
                    >
                        <ArrowLeft className="w-4 h-4" /> 분석 실험실로 돌아가기
                    </Link>
                    {resultA && resultB && (
                        <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                            <span className="px-2 py-0.5 rounded-full bg-secondary border border-border">
                                A · {resultA.result_id.slice(0, 8)}
                            </span>
                            <span className="px-2 py-0.5 rounded-full bg-secondary border border-border">
                                B · {resultB.result_id.slice(0, 8)}
                            </span>
                        </div>
                    )}
                </div>

                {loading && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Activity className="w-4 h-4 animate-spin" /> 비교 로딩 중...
                    </div>
                )}

                {error && (
                    <div className="p-4 border border-destructive/30 bg-destructive/10 rounded-xl text-destructive flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        <span>{error}</span>
                    </div>
                )}

                {!loading && (!idA || !idB) && (
                    <div className="p-4 border border-border rounded-xl text-sm text-muted-foreground">
                        비교할 결과가 없습니다. 분석 실험실에서 2개를 선택해 주세요.
                    </div>
                )}

                {!loading && resultA && resultB && (
                    <div className="space-y-8">
                        <div className="flex flex-wrap items-start justify-between gap-4">
                            <div className="flex items-center gap-3">
                                <GitCompare className="w-5 h-5 text-primary" />
                                <div>
                                    <h1 className="text-2xl font-semibold font-display">분석 결과 비교</h1>
                                    <p className="text-sm text-muted-foreground">
                                        저장된 분석 결과 2건의 요약/메트릭/실패 노드를 비교합니다.
                                    </p>
                                </div>
                            </div>
                            <div className="text-xs text-muted-foreground">
                                A → B 비교 기준
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                            <div className="surface-panel p-4">
                                <p className="text-xs text-muted-foreground">노드 상태 변경</p>
                                <div className="mt-2 flex items-baseline gap-2">
                                    <span className="text-2xl font-semibold">
                                        {nodeDiffCount}
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                        / {nodeRows.length}개
                                    </span>
                                </div>
                                <p className="text-xs text-muted-foreground mt-2">
                                    실패 노드 A {failureCountA} → B {failureCountB}
                                </p>
                                <p className={`text-xs mt-1 ${failureDeltaClass}`}>
                                    {failureDeltaDisplay}
                                </p>
                            </div>
                            <div className="surface-panel p-4">
                                <p className="text-xs text-muted-foreground">메트릭 변화</p>
                                <div className="mt-2 flex items-baseline gap-2">
                                    <span className="text-2xl font-semibold">
                                        {metricStats.changed}
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                        / {metricStats.total}개
                                    </span>
                                </div>
                                <p className="text-xs text-muted-foreground mt-2">
                                    증가 {metricStats.increased} · 감소 {metricStats.decreased} · 유지 {metricStats.unchanged}
                                </p>
                                {metricStats.missing > 0 && (
                                    <p className="text-xs text-muted-foreground mt-1">
                                        비교 불가 {metricStats.missing}개
                                    </p>
                                )}
                            </div>
                            <div className="surface-panel p-4">
                                <p className="text-xs text-muted-foreground">우선순위 변화</p>
                                {!priorityDiff ? (
                                    <p className="text-xs text-muted-foreground mt-2">
                                        우선순위 요약 없음
                                    </p>
                                ) : (
                                    <div className="mt-2 text-xs text-muted-foreground space-y-1">
                                        <p>
                                            하위 추가 {priorityDiff.bottom.added.length} · 해소 {priorityDiff.bottom.removed.length}
                                        </p>
                                        <p>
                                            영향 추가 {priorityDiff.impact.added.length} · 해소 {priorityDiff.impact.removed.length}
                                        </p>
                                    </div>
                                )}
                            </div>
                            <div className="surface-panel p-4">
                                <p className="text-xs text-muted-foreground">처리 시간</p>
                                <div className="mt-2 text-sm text-muted-foreground">
                                    A {formatDurationMs(resultA.duration_ms)} → B {formatDurationMs(resultB.duration_ms)}
                                </div>
                                <p className={`text-xs mt-2 ${durationDeltaClass}`}>
                                    {durationDeltaDisplay}
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <ResultCard result={resultA} variant="A" failureCount={failureCountA} />
                            <ResultCard result={resultB} variant="B" failureCount={failureCountB} />
                        </div>

                        <div className="surface-panel p-4">
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <h3 className="text-sm font-semibold">프롬프트 변화</h3>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Run ID 기반 프롬프트 스냅샷을 비교합니다.
                                    </p>
                                </div>
                                <div className="flex items-center gap-2">
                                    {promptDiff && (
                                        <button
                                            type="button"
                                            onClick={() => {
                                                const blob = new Blob([JSON.stringify(promptDiff, null, 2)], {
                                                    type: "application/json",
                                                });
                                                const url = URL.createObjectURL(blob);
                                                const a = document.createElement("a");
                                                a.href = url;
                                                a.download = `prompt_diff_${resultA?.run_id}_${resultB?.run_id}.json`;
                                                document.body.appendChild(a);
                                                a.click();
                                                document.body.removeChild(a);
                                                URL.revokeObjectURL(url);
                                            }}
                                            className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-md transition-colors"
                                            title="JSON 다운로드"
                                        >
                                            <Download className="w-4 h-4" />
                                        </button>
                                    )}
                                    <button
                                        type="button"
                                        onClick={() => setShowPromptDiffDetail((prev) => !prev)}
                                        className="text-[11px] text-muted-foreground hover:text-foreground flex items-center gap-1"
                                    >
                                        {showPromptDiffDetail ? (
                                            <>
                                                <ChevronUp className="w-3 h-3" /> 접기
                                            </>
                                        ) : (
                                            <>
                                                <ChevronDown className="w-3 h-3" /> 상세 보기
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>

                            {promptDiffLoading && (
                                <div className="flex items-center gap-2 py-4 text-xs text-muted-foreground">
                                    <Activity className="w-3 h-3 animate-spin" /> 비교 분석 중...
                                </div>
                            )}

                            {promptDiffError && (
                                <p className="text-xs text-rose-500 py-2">{promptDiffError}</p>
                            )}

                            {!promptDiffLoading && !promptDiff && resultA && resultB && (
                                <p className="text-xs text-muted-foreground py-2">
                                    {!resultA.run_id || !resultB.run_id
                                        ? "Run ID가 없는 결과는 프롬프트를 비교할 수 없습니다."
                                        : "비교할 프롬프트 데이터가 없습니다."}
                                </p>
                            )}

                                {!promptDiffLoading && promptDiff && (
                                <div className="space-y-4">
                                    <div className="overflow-hidden border border-border rounded-lg">
                                        <table className="w-full text-xs">
                                            <thead className="bg-secondary/50 text-muted-foreground">
                                                <tr>
                                                    <th className="px-3 py-2 text-left font-medium">Role</th>
                                                    <th className="px-3 py-2 text-left font-medium">Status</th>
                                                    <th className="px-3 py-2 text-left font-medium">Base (A)</th>
                                                    <th className="px-3 py-2 text-left font-medium">Target (B)</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-border">
                                                {promptDiff.summary.map((item, idx) => (
                                                    <tr key={`${item.role}-${idx}`} className="hover:bg-secondary/20">
                                                        <td className="px-3 py-2 font-medium">{item.role}</td>
                                                        <td className="px-3 py-2">
                                                            <span
                                                                className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                                                                    item.status === "diff"
                                                                        ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                                                                        : item.status === "missing"
                                                                            ? "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                                                                            : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                                                                }`}
                                                            >
                                                                {item.status.toUpperCase()}
                                                            </span>
                                                        </td>
                                                        <td className="px-3 py-2 text-muted-foreground">
                                                            {item.base_name || "-"}
                                                        </td>
                                                        <td className="px-3 py-2 text-muted-foreground">
                                                            {item.target_name || "-"}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>

                                    {showPromptDiffDetail && (
                                        <div className="space-y-3">
                                            {promptDiff.diffs.length === 0 ? (
                                                <p className="text-xs text-muted-foreground">
                                                    변경사항이 없거나 텍스트 차이가 없습니다.
                                                </p>
                                            ) : (
                                                promptDiff.diffs.map((diff, idx) => (
                                                    <div key={`diff-${idx}`} className="border border-border rounded-lg overflow-hidden">
                                                        <div className="px-3 py-2 bg-secondary/30 border-b border-border flex items-center justify-between">
                                                            <span className="text-xs font-semibold flex items-center gap-2">
                                                                <FileText className="w-3 h-3" />
                                                                {diff.role}
                                                            </span>
                                                            {diff.truncated && (
                                                                <span className="text-[10px] text-amber-600">
                                                                    (일부 생략됨)
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="bg-slate-50 dark:bg-slate-950 p-3 overflow-x-auto">
                                                            <pre className="text-[11px] font-mono leading-relaxed whitespace-pre-wrap">
                                                                {diff.lines.map((line, lIdx) => {
                                                                    let colorClass = "text-foreground";
                                                                    if (line.startsWith("+")) colorClass = "text-emerald-600 dark:text-emerald-400";
                                                                    if (line.startsWith("-")) colorClass = "text-rose-600 dark:text-rose-400";
                                                                    if (line.startsWith("@")) colorClass = "text-blue-500";
                                                                    return (
                                                                        <div key={lIdx} className={colorClass}>
                                                                            {line}
                                                                        </div>
                                                                    );
                                                                })}
                                                            </pre>
                                                        </div>
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        <div className="surface-panel p-4">
                            <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                                <div>
                                    <h3 className="text-sm font-semibold">노드 상태 비교</h3>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        총 {nodeRows.length}개 중 {nodeDiffCount}개 변화
                                    </p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setShowOnlyDiff(true)}
                                        className={`filter-chip ${showOnlyDiff ? "filter-chip-active" : "filter-chip-inactive"}`}
                                    >
                                        차이만 보기
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setShowOnlyDiff(false)}
                                        className={`filter-chip ${showOnlyDiff ? "filter-chip-inactive" : "filter-chip-active"}`}
                                    >
                                        전체 보기
                                    </button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                {filteredNodes.length === 0 ? (
                                    <p className="text-xs text-muted-foreground">
                                        표시할 차이가 없습니다.
                                    </p>
                                ) : (
                                    filteredNodes.map((row) => {
                                        return (
                                            <div
                                                key={row.nodeId}
                                                className={`flex flex-col md:flex-row md:items-center md:justify-between gap-2 border rounded-lg px-3 py-2 ${row.diff ? "border-primary/40 bg-primary/5" : "border-border"}`}
                                            >
                                                <div>
                                                    <p className="text-sm font-medium">{row.nodeId}</p>
                                                    {(row.aError || row.bError) && (
                                                        <div className="text-xs text-rose-600 space-y-1">
                                                            {row.aError && <p>A: {row.aError}</p>}
                                                            {row.bError && <p>B: {row.bError}</p>}
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-4 text-xs">
                                                    <StatusBadge prefix="A" status={row.aStatus} />
                                                    <StatusBadge prefix="B" status={row.bStatus} />
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>
                        </div>

                        <div className="surface-panel p-4">
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <h3 className="text-sm font-semibold">우선순위 케이스 변화</h3>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Priority summary 기반으로 추가/해소된 케이스를 비교합니다.
                                    </p>
                                </div>
                            </div>
                            {!priorityDiff ? (
                                <p className="text-xs text-muted-foreground">
                                    우선순위 요약 데이터가 없어 비교할 수 없습니다.
                                </p>
                            ) : (
                                <div className="space-y-4 text-xs">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        <div className="border border-border rounded-lg p-3">
                                            <p className="font-semibold text-muted-foreground">하위 성능 케이스</p>
                                            <p className="mt-1">
                                                추가 {priorityDiff.bottom.added.length} · 해소 {priorityDiff.bottom.removed.length}
                                            </p>
                                            {(priorityDiff.bottom.added.length > 0 || priorityDiff.bottom.removed.length > 0) && (
                                                <p className="text-[11px] text-muted-foreground mt-1">
                                                    추가: {priorityDiff.bottom.added.slice(0, 5).join(", ") || "-"} · 해소: {priorityDiff.bottom.removed.slice(0, 5).join(", ") || "-"}
                                                </p>
                                            )}
                                        </div>
                                        <div className="border border-border rounded-lg p-3">
                                            <p className="font-semibold text-muted-foreground">개선 우선 케이스</p>
                                            <p className="mt-1">
                                                추가 {priorityDiff.impact.added.length} · 해소 {priorityDiff.impact.removed.length}
                                            </p>
                                            {(priorityDiff.impact.added.length > 0 || priorityDiff.impact.removed.length > 0) && (
                                                <p className="text-[11px] text-muted-foreground mt-1">
                                                    추가: {priorityDiff.impact.added.slice(0, 5).join(", ") || "-"} · 해소: {priorityDiff.impact.removed.slice(0, 5).join(", ") || "-"}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                    <div className="border border-border rounded-lg p-3">
                                        <p className="font-semibold text-muted-foreground">실패 메트릭 변화</p>
                                        {priorityDiff.metricDeltas.length === 0 ? (
                                            <p className="text-[11px] text-muted-foreground mt-1">
                                                비교할 실패 메트릭 변화가 없습니다.
                                            </p>
                                        ) : (
                                            <div className="space-y-1 mt-2">
                                                {priorityDiff.metricDeltas.slice(0, 6).map((row) => (
                                                    <div
                                                        key={`metric-delta-${row.metric}`}
                                                        className="flex items-center justify-between border border-border rounded-md px-2 py-1"
                                                    >
                                                        <span className="font-medium">{row.metric}</span>
                                                        <span className="text-muted-foreground">
                                                            A {row.aCount} → B {row.bCount} (Δ {row.delta})
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>

                        {showAnalysisMetricSection && (
                            <div className="surface-panel p-4">
                                <div className="flex items-center justify-between mb-3">
                                    <div>
                                        <h3 className="text-sm font-semibold">추가 분석 지표 비교</h3>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            분석 모듈 지표를 신호 그룹으로 묶어 A/B를 비교합니다.
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
                                    <p className="text-xs text-rose-500">{analysisCatalogError}</p>
                                )}
                                {analysisMetricSpecError && (
                                    <p className="text-xs text-rose-500">{analysisMetricSpecError}</p>
                                )}
                                {!showAnalysisMetrics ? (
                                    <p className="text-xs text-muted-foreground">
                                        추가 분석 지표는 선택 시에만 표시됩니다.
                                    </p>
                                ) : analysisMetricGroups.length === 0 ? (
                                    <p className="text-xs text-muted-foreground">
                                        표시할 추가 분석 지표가 없습니다.
                                    </p>
                                ) : (
                                    <div className="space-y-4 text-xs">
                                        {analysisMetricGroups.map((group) => (
                                            <div key={group.id} className="space-y-2">
                                                <p className="text-xs font-semibold text-muted-foreground">
                                                    {group.label}
                                                </p>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                    {group.items.map((item) => (
                                                        <div
                                                            key={item.key}
                                                            className="border border-border rounded-md px-2 py-2 space-y-1"
                                                            title={item.description}
                                                        >
                                                            <p className="text-muted-foreground">
                                                                {item.label}
                                                            </p>
                                                            <div className="flex items-center justify-between">
                                                                <span>A {formatMetricValue(item.aValue)}</span>
                                                                <span>B {formatMetricValue(item.bValue)}</span>
                                                                <span
                                                                    className={
                                                                        item.delta === null
                                                                            ? "text-muted-foreground"
                                                                            : item.delta > 0
                                                                                ? "text-emerald-600"
                                                                                : item.delta < 0
                                                                                    ? "text-rose-600"
                                                                                    : "text-muted-foreground"
                                                                    }
                                                                >
                                                                    Δ {formatSignedDelta(item.delta, 4)}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        <div className="surface-panel p-4">
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <h3 className="text-sm font-semibold">메트릭 차이</h3>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        숫자형 요약 지표를 추출해 차이를 계산합니다.
                                    </p>
                                </div>
                                <div className="flex flex-wrap items-center gap-2">
                                    <div className="flex items-center gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setShowOnlyMetricChanges(true)}
                                            className={`filter-chip ${showOnlyMetricChanges ? "filter-chip-active" : "filter-chip-inactive"}`}
                                        >
                                            변경 지표만
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setShowOnlyMetricChanges(false)}
                                            className={`filter-chip ${showOnlyMetricChanges ? "filter-chip-inactive" : "filter-chip-active"}`}
                                        >
                                            전체 지표
                                        </button>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setShowAllMetrics(false)}
                                            className={`filter-chip ${showAllMetrics ? "filter-chip-inactive" : "filter-chip-active"}`}
                                        >
                                            간단히
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setShowAllMetrics(true)}
                                            className={`filter-chip ${showAllMetrics ? "filter-chip-active" : "filter-chip-inactive"}`}
                                        >
                                            전체 보기
                                        </button>
                                    </div>
                                </div>
                            </div>
                            {metricRowsView.length === 0 ? (
                                <p className="text-xs text-muted-foreground">
                                    비교할 수 있는 숫자 지표가 없습니다.
                                </p>
                            ) : (
                                <div className="space-y-2 text-xs">
                                    {metricRowsView.map((row) => (
                                        <div
                                            key={row.key}
                                            className="grid grid-cols-1 md:grid-cols-4 gap-2 border border-border rounded-lg px-3 py-2"
                                        >
                                            <p className="text-muted-foreground break-all">{row.key}</p>
                                            <p>A: {formatMetricValue(row.aValue)}</p>
                                            <p>B: {formatMetricValue(row.bValue)}</p>
                                            <p
                                                className={
                                                    row.delta === null
                                                        ? "text-muted-foreground"
                                                        : row.delta > 0
                                                            ? "text-emerald-600"
                                                            : row.delta < 0
                                                                ? "text-rose-600"
                                                                : "text-muted-foreground"
                                                }
                                            >
                                                Δ {formatSignedDelta(row.delta, 4)}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {metricRows.length > 0 && (
                                <p className="text-[11px] text-muted-foreground mt-3">
                                    표시 중 {metricRowsView.length} / 전체 {metricRows.length}개
                                </p>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    );
}
