import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Layout } from "../components/Layout";
import { type PriorityCase, type PrioritySummary } from "../components/PrioritySummaryPanel";
import { fetchAnalysisResult, type SavedAnalysisResult } from "../services/api";
import { formatDateTime, formatDurationMs } from "../utils/format";
import { Activity, AlertCircle, ArrowLeft, GitCompare } from "lucide-react";

const STATUS_META: Record<string, { label: string; color: string }> = {
    completed: { label: "완료", color: "text-emerald-600" },
    failed: { label: "실패", color: "text-rose-600" },
    skipped: { label: "스킵", color: "text-amber-600" },
    running: { label: "실행 중", color: "text-blue-600" },
    pending: { label: "대기", color: "text-muted-foreground" },
    missing: { label: "없음", color: "text-muted-foreground" },
};

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

function extractNumericMetrics(output: Record<string, any> | null) {
    const metrics: Record<string, number> = {};
    const visited = new Set<any>();

    const walk = (value: any, path: string, depth: number) => {
        if (value === null || value === undefined) return;
        if (depth > 4) return;

        if (typeof value === "number" && Number.isFinite(value)) {
            metrics[path] = value;
            return;
        }

        if (Array.isArray(value)) {
            if (value.length === 0) return;
            const numeric = value.filter((item) => typeof item === "number" && Number.isFinite(item));
            if (numeric.length === value.length) {
                const avg = numeric.reduce((sum, item) => sum + item, 0) / numeric.length;
                metrics[`${path}.avg`] = avg;
            }
            return;
        }

        if (typeof value === "object") {
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

function buildNodeMap(result: SavedAnalysisResult | null) {
    const map: Record<string, { status: string; error?: string | null }> = {};
    if (!result?.node_results) return map;
    Object.entries(result.node_results).forEach(([nodeId, node]) => {
        map[nodeId] = {
            status: (node as any)?.status || "pending",
            error: (node as any)?.error || null,
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

function isPrioritySummary(value: any): value is PrioritySummary {
    if (!value || typeof value !== "object") return false;
    return Array.isArray(value.bottom_cases) || Array.isArray(value.impact_cases);
}

function extractPrioritySummary(result: SavedAnalysisResult | null): PrioritySummary | null {
    if (!result) return null;
    const finalOutput = result.final_output || {};
    for (const entry of Object.values(finalOutput)) {
        if (isPrioritySummary(entry)) return entry;
    }
    const nodeOutput = result.node_results?.priority_summary?.output;
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

export function AnalysisCompareView() {
    const [searchParams] = useSearchParams();
    const idA = searchParams.get("a");
    const idB = searchParams.get("b");
    const [resultA, setResultA] = useState<SavedAnalysisResult | null>(null);
    const [resultB, setResultB] = useState<SavedAnalysisResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showOnlyDiff, setShowOnlyDiff] = useState(true);
    const [showAllMetrics, setShowAllMetrics] = useState(false);

    useEffect(() => {
        async function loadResults() {
            if (!idA || !idB) {
                setLoading(false);
                return;
            }
            setLoading(true);
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

    const priorityDiff = useMemo(() => {
        const priorityA = extractPrioritySummary(resultA);
        const priorityB = extractPrioritySummary(resultB);
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
    }, [resultA, resultB]);

    const nodeRows = useMemo(() => {
        if (!resultA || !resultB) return [];
        const mapA = buildNodeMap(resultA);
        const mapB = buildNodeMap(resultB);
        const nodeIds = Array.from(new Set([...Object.keys(mapA), ...Object.keys(mapB)]));

        return nodeIds.map((nodeId) => {
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

    const metricPreview = showAllMetrics ? metricRows : metricRows.slice(0, 20);

    return (
        <Layout>
            <div className="max-w-6xl mx-auto pb-20">
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
                        <div className="flex items-center gap-3">
                            <GitCompare className="w-5 h-5 text-primary" />
                            <div>
                                <h1 className="text-2xl font-semibold">분석 결과 비교</h1>
                                <p className="text-sm text-muted-foreground">
                                    저장된 분석 결과 2건의 요약/메트릭/실패 노드를 비교합니다.
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {[resultA, resultB].map((result, index) => (
                                <div
                                    key={result.result_id}
                                    className="border border-border rounded-xl p-4 bg-card"
                                >
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="text-xs text-muted-foreground">
                                                {index === 0 ? "A" : "B"}
                                            </p>
                                            <h2 className="text-lg font-semibold">{result.label}</h2>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {formatDateTime(result.created_at)}
                                            </p>
                                        </div>
                                        <Link
                                            to={`/analysis/results/${result.result_id}`}
                                            className="text-xs text-primary hover:underline"
                                        >
                                            결과 보기
                                        </Link>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
                                        <div>
                                            <p className="text-xs text-muted-foreground">Intent</p>
                                            <p className="font-medium">{result.intent}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-muted-foreground">Duration</p>
                                            <p className="font-medium">
                                                {formatDurationMs(result.duration_ms)}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-muted-foreground">Run ID</p>
                                            <p className="font-medium">
                                                {result.run_id || "샘플 데이터"}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-muted-foreground">실패 노드</p>
                                            <p className="font-medium">
                                                {index === 0 ? failureCountA : failureCountB}개
                                            </p>
                                        </div>
                                        {result.profile && (
                                            <div>
                                                <p className="text-xs text-muted-foreground">Profile</p>
                                                <p className="font-medium">{result.profile}</p>
                                            </div>
                                        )}
                                        {result.tags && result.tags.length > 0 && (
                                            <div>
                                                <p className="text-xs text-muted-foreground">Tags</p>
                                                <p className="font-medium">
                                                    {result.tags.join(", ")}
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="border border-border rounded-xl p-4 bg-card">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-sm font-semibold">노드 상태 비교</h3>
                                <button
                                    type="button"
                                    onClick={() => setShowOnlyDiff((prev) => !prev)}
                                    className="text-xs text-muted-foreground hover:text-foreground"
                                >
                                    {showOnlyDiff ? "전체 보기" : "차이만 보기"}
                                </button>
                            </div>
                            <div className="space-y-2">
                                {filteredNodes.length === 0 ? (
                                    <p className="text-xs text-muted-foreground">
                                        표시할 차이가 없습니다.
                                    </p>
                                ) : (
                                    filteredNodes.map((row) => {
                                        const metaA = STATUS_META[row.aStatus] || STATUS_META.pending;
                                        const metaB = STATUS_META[row.bStatus] || STATUS_META.pending;
                                        return (
                                            <div
                                                key={row.nodeId}
                                                className="flex items-center justify-between border border-border rounded-lg px-3 py-2"
                                            >
                                                <div>
                                                    <p className="text-sm font-medium">{row.nodeId}</p>
                                                    {(row.aError || row.bError) && (
                                                        <p className="text-xs text-rose-600">
                                                            {row.aError || row.bError}
                                                        </p>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-4 text-xs">
                                                    <span className={metaA.color}>A · {metaA.label}</span>
                                                    <span className={metaB.color}>B · {metaB.label}</span>
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>
                        </div>

                        <div className="border border-border rounded-xl p-4 bg-card">
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

                        <div className="border border-border rounded-xl p-4 bg-card">
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <h3 className="text-sm font-semibold">메트릭 차이</h3>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        숫자형 요약 지표를 추출해 차이를 계산합니다.
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => setShowAllMetrics((prev) => !prev)}
                                    className="text-xs text-muted-foreground hover:text-foreground"
                                >
                                    {showAllMetrics ? "간단히" : "전체 보기"}
                                </button>
                            </div>
                            {metricPreview.length === 0 ? (
                                <p className="text-xs text-muted-foreground">
                                    비교할 수 있는 숫자 지표가 없습니다.
                                </p>
                            ) : (
                                <div className="space-y-2 text-xs">
                                    {metricPreview.map((row) => (
                                        <div
                                            key={row.key}
                                            className="grid grid-cols-1 md:grid-cols-4 gap-2 border border-border rounded-lg px-3 py-2"
                                        >
                                            <p className="text-muted-foreground break-all">{row.key}</p>
                                            <p>A: {formatMetricValue(row.aValue)}</p>
                                            <p>B: {formatMetricValue(row.bValue)}</p>
                                            <p className="text-muted-foreground">
                                                Δ {row.delta !== null ? row.delta.toFixed(4) : "-"}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    );
}
