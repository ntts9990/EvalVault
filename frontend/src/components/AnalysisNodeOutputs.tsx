import { useMemo } from "react";
import { MarkdownContent } from "./MarkdownContent";
import { VirtualizedText } from "./VirtualizedText";

const STATUS_META: Record<string, { label: string; color: string }> = {
    completed: { label: "완료", color: "text-emerald-600" },
    failed: { label: "실패", color: "text-rose-600" },
    skipped: { label: "스킵", color: "text-amber-600" },
    running: { label: "실행 중", color: "text-blue-600" },
    pending: { label: "대기", color: "text-muted-foreground" },
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === "object" && value !== null;

const getStringField = (record: Record<string, unknown>, key: string) => {
    const value = record[key];
    return typeof value === "string" ? value : null;
};

const getStringLikeField = (record: Record<string, unknown>, key: string) => {
    const value = record[key];
    if (typeof value === "string") return value;
    if (typeof value === "number" && Number.isFinite(value)) return String(value);
    return null;
};

const getStringArrayField = (record: Record<string, unknown>, key: string) => {
    const value = record[key];
    if (!Array.isArray(value)) return null;
    const strings = value.filter((item): item is string => typeof item === "string");
    return strings.length ? strings : null;
};

const getRecordField = (record: Record<string, unknown>, key: string) => {
    const value = record[key];
    return isRecord(value) ? value : null;
};

const getFirstString = (record: Record<string, unknown>, keys: string[]) => {
    for (const key of keys) {
        const value = getStringField(record, key);
        if (value) return value;
    }
    return null;
};

const getFirstStringLike = (record: Record<string, unknown>, keys: string[]) => {
    for (const key of keys) {
        const value = getStringLikeField(record, key);
        if (value) return value;
    }
    return null;
};

type NodeResult = {
    status?: string;
    error?: string | null;
    duration_ms?: number | null;
    output?: unknown;
};

type NodeDefinition = {
    id: string;
    name: string;
    module: string;
    depends_on: string[];
};

const coerceNodeResult = (value: unknown): NodeResult => {
    if (!isRecord(value)) return {};
    const status = typeof value.status === "string" ? value.status : undefined;
    const errorValue = value.error;
    const error = typeof errorValue === "string" ? errorValue : errorValue ? String(errorValue) : null;
    const durationMs = typeof value.duration_ms === "number" ? value.duration_ms : undefined;
    return {
        status,
        error,
        duration_ms: durationMs,
        output: value.output,
    };
};

function formatValue(value: unknown) {
    if (typeof value === "number" && Number.isFinite(value)) {
        return value.toFixed(4);
    }
    if (typeof value === "string") {
        return value;
    }
    if (value === null || value === undefined) {
        return "-";
    }
    if (Array.isArray(value)) {
        return value.length ? `${value.length} items` : "-";
    }
    if (typeof value === "object") {
        return "object";
    }
    return String(value);
}

function formatDuration(durationMs?: number | null) {
    if (!durationMs && durationMs !== 0) return "";
    if (durationMs < 1000) return `${durationMs}ms`;
    return `${(durationMs / 1000).toFixed(2)}s`;
}

function normalizeNodeList(
    nodeResults: Record<string, unknown>,
    nodeDefinitions?: NodeDefinition[]
) {
    const definitionMap = new Map<string, NodeDefinition>();
    nodeDefinitions?.forEach((node) => definitionMap.set(node.id, node));

    const orderedIds = nodeDefinitions?.length
        ? nodeDefinitions.map((node) => node.id).filter((id) => id in nodeResults)
        : Object.keys(nodeResults);

    const extraIds = Object.keys(nodeResults).filter((id) => !orderedIds.includes(id));
    const ids = [...orderedIds, ...extraIds];

    return ids.map((id) => {
        const definition = definitionMap.get(id);
        return {
            id,
            name: definition?.name || id,
            module: definition?.module || id,
            result: coerceNodeResult(nodeResults[id]),
        };
    });
}

function extractEvidence(output: unknown) {
    if (!isRecord(output)) return [];
    const candidates = [output.evidence, output.evidence_samples, output.samples];
    for (const candidate of candidates) {
        if (Array.isArray(candidate)) {
            return candidate.filter(isRecord);
        }
    }
    return [];
}

function formatMetrics(metrics: Record<string, unknown> | null | undefined) {
    if (!metrics) return null;
    return Object.entries(metrics).map(([key, value]) => {
        if (typeof value === "number" && Number.isFinite(value)) {
            return `${key}: ${value.toFixed(3)}`;
        }
        return `${key}: ${String(value)}`;
    });
}

function normalizeDetailItems(
    items: unknown[],
    options: {
        titleKeys: string[];
        detailKeys: string[];
        scoreKey?: string;
    }
) {
    const { titleKeys, detailKeys, scoreKey } = options;
    return items.map((item, index) => {
        if (!isRecord(item)) {
            return {
                title: `Item ${index + 1}`,
                detail: String(item),
                score: null,
            };
        }
        const title =
            titleKeys
                .map((key) => item[key])
                .find((value) => value)
            || `Item ${index + 1}`;
        const detail =
            detailKeys
                .map((key) => item[key])
                .find((value) => value)
            || (item.detail ?? item.message ?? JSON.stringify(item));
        const scoreValue = scoreKey ? item[scoreKey] : null;
        const score =
            typeof scoreValue === "number" && Number.isFinite(scoreValue)
                ? scoreValue.toFixed(3)
                : null;
        return {
            title: String(title),
            detail: String(detail),
            score,
        };
    });
}

function normalizeStringList(items: unknown[]) {
    return items.map((item) => {
        if (typeof item === "string") return item;
        if (isRecord(item)) {
            const text = item.intervention || item.recommendation || item.detail || item.message;
            if (text) return String(text);
        }
        try {
            return JSON.stringify(item);
        } catch {
            return String(item);
        }
    });
}

export function AnalysisNodeOutputs({
    nodeResults,
    nodeDefinitions,
    title = "노드 출력",
}: {
    nodeResults?: Record<string, unknown> | null;
    nodeDefinitions?: NodeDefinition[];
    title?: string;
}) {
    const nodes = useMemo(() => {
        if (!nodeResults) return [];
        return normalizeNodeList(nodeResults, nodeDefinitions);
    }, [nodeResults, nodeDefinitions]);

    if (!nodes.length) return null;

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold">{title}</h3>
                <span className="text-xs text-muted-foreground">{nodes.length}개 노드</span>
            </div>
            <div className="space-y-3">
                {nodes.map((node) => {
                    const statusKey = node.result?.status || "pending";
                    const meta = STATUS_META[statusKey] || STATUS_META.pending;
                    const output = node.result?.output;
                    const outputRecord = isRecord(output) ? output : null;
                    const reportText =
                        outputRecord && typeof outputRecord.report === "string"
                            ? outputRecord.report
                            : null;
                    const summary =
                        outputRecord && isRecord(outputRecord.summary)
                            ? outputRecord.summary
                            : null;
                    const insights =
                        outputRecord && Array.isArray(outputRecord.insights)
                            ? outputRecord.insights.filter((item): item is string => typeof item === "string")
                            : null;
                    const recommendations =
                        outputRecord && Array.isArray(outputRecord.recommendations)
                            ? outputRecord.recommendations
                            : null;
                    const diagnostics =
                        outputRecord && Array.isArray(outputRecord.diagnostics)
                            ? outputRecord.diagnostics
                            : null;
                    const causes =
                        outputRecord && Array.isArray(outputRecord.causes)
                            ? outputRecord.causes
                            : null;
                    const interventions =
                        outputRecord && Array.isArray(outputRecord.interventions)
                            ? outputRecord.interventions
                            : null;
                    const evidence = extractEvidence(output);
                    const rawText = (() => {
                        try {
                            return JSON.stringify(output ?? {}, null, 2);
                        } catch {
                            return String(output ?? "");
                        }
                    })();
                    const reportIsLarge = (reportText?.length ?? 0) > 5000;

                    return (
                        <details key={node.id} className="border border-border rounded-lg">
                            <summary className="px-3 py-2 flex items-center justify-between cursor-pointer">
                                <div>
                                    <p className="text-sm font-medium">{node.name}</p>
                                    <p className="text-xs text-muted-foreground">{node.module}</p>
                                </div>
                                <div className="flex items-center gap-3">
                                    {node.result?.duration_ms !== undefined && (
                                        <span className="text-xs text-muted-foreground">
                                            {formatDuration(node.result?.duration_ms)}
                                        </span>
                                    )}
                                    <span className={`text-xs font-semibold ${meta.color}`}>
                                        {meta.label}
                                    </span>
                                </div>
                            </summary>

                            <div className="px-4 pb-4 space-y-4">
                                {node.result?.error && (
                                    <div className="text-xs text-rose-600 bg-rose-50 border border-rose-200 rounded-lg p-2">
                                        {node.result.error}
                                    </div>
                                )}

                                {reportText && (
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-muted-foreground">보고서</p>
                                        {reportIsLarge ? (
                                            <VirtualizedText
                                                text={reportText}
                                                height="16rem"
                                                className="bg-background border border-border rounded-lg p-3 text-xs"
                                            />
                                        ) : (
                                            <div className="bg-background border border-border rounded-lg p-3 text-sm">
                                                <MarkdownContent text={reportText} />
                                            </div>
                                        )}
                                    </div>
                                )}

                                {summary && (
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-muted-foreground">요약</p>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                                            {Object.entries(summary).slice(0, 12).map(([key, value]) => (
                                                <div key={key} className="border border-border rounded-md px-2 py-1">
                                                    <span className="text-muted-foreground">{key}</span>
                                                    <span className="ml-2 font-semibold text-foreground">
                                                        {formatValue(value)}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {insights && insights.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-muted-foreground">인사이트</p>
                                        <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
                                        {insights.slice(0, 8).map((item, index) => (
                                            <li key={`${node.id}-insight-${index}`}>{String(item)}</li>
                                        ))}
                                        </ul>
                                    </div>
                                )}

                                {diagnostics && diagnostics.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-muted-foreground">진단 항목</p>
                                        <div className="space-y-2">
                                            {normalizeDetailItems(diagnostics, {
                                                titleKeys: ["metric", "name", "type"],
                                                detailKeys: ["issue", "reason", "detail", "message"],
                                                scoreKey: "score",
                                            })
                                                .slice(0, 8)
                                                .map((item, index) => (
                                                    <div
                                                        key={`${node.id}-diagnostic-${index}`}
                                                        className="border border-border rounded-md px-2 py-1 text-xs"
                                                    >
                                                        <div className="flex items-center justify-between">
                                                            <span className="font-semibold text-foreground">{item.title}</span>
                                                            {item.score && (
                                                                <span className="text-[10px] text-muted-foreground">
                                                                    {item.score}
                                                                </span>
                                                            )}
                                                        </div>
                                                        <p className="text-muted-foreground">{item.detail}</p>
                                                    </div>
                                                ))}
                                        </div>
                                    </div>
                                )}

                                {causes && causes.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-muted-foreground">근본 원인</p>
                                        <div className="space-y-2">
                                            {normalizeDetailItems(causes, {
                                                titleKeys: ["metric", "name", "type"],
                                                detailKeys: ["reason", "description", "detail", "message"],
                                            })
                                                .slice(0, 8)
                                                .map((item, index) => (
                                                    <div
                                                        key={`${node.id}-cause-${index}`}
                                                        className="border border-border rounded-md px-2 py-1 text-xs"
                                                    >
                                                        <div className="font-semibold text-foreground">{item.title}</div>
                                                        <p className="text-muted-foreground">{item.detail}</p>
                                                    </div>
                                                ))}
                                        </div>
                                    </div>
                                )}

                                {recommendations && recommendations.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-muted-foreground">권장 사항</p>
                                        <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
                                            {normalizeStringList(recommendations).slice(0, 8).map((item, index) => (
                                                <li key={`${node.id}-recommendation-${index}`}>{item}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {interventions && interventions.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-muted-foreground">개선 개입</p>
                                        <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
                                            {normalizeStringList(interventions).slice(0, 8).map((item, index) => (
                                                <li key={`${node.id}-intervention-${index}`}>{item}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {evidence.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-muted-foreground">증거 샘플</p>
                                        <div className="space-y-3">
                                            {evidence.slice(0, 6).map((item, index) => {
                                                const evidenceItem = isRecord(item) ? item : {};
                                                const evidenceId =
                                                    getFirstStringLike(evidenceItem, [
                                                        "evidence_id",
                                                        "id",
                                                        "test_case_id",
                                                        "case_id",
                                                    ]) || `evidence-${index + 1}`;
                                                const question = getFirstString(evidenceItem, ["question", "query", "user_input"]);
                                                const answer = getFirstString(evidenceItem, ["answer", "response"]);
                                                const contexts =
                                                    getStringArrayField(evidenceItem, "contexts")
                                                    || getStringArrayField(evidenceItem, "retrieved_contexts");
                                                const metrics =
                                                    getRecordField(evidenceItem, "metrics")
                                                    || getRecordField(evidenceItem, "scores");
                                                const metricsText = formatMetrics(metrics);

                                                return (
                                                    <div key={`${node.id}-evidence-${evidenceId}`} className="border border-border rounded-lg p-3 text-xs space-y-2">
                                                        <div className="flex items-center justify-between">
                                                            <span className="text-muted-foreground">ID</span>
                                                            <span className="font-semibold">{evidenceId}</span>
                                                        </div>
                                                        {question && (
                                                            <div>
                                                                <p className="text-muted-foreground">질문</p>
                                                                <p className="font-medium text-foreground">{question}</p>
                                                            </div>
                                                        )}
                                                        {answer && (
                                                            <div>
                                                                <p className="text-muted-foreground">답변</p>
                                                                <p className="text-foreground">{answer}</p>
                                                            </div>
                                                        )}
                                                        {Array.isArray(contexts) && contexts.length > 0 && (
                                                            <div>
                                                                <p className="text-muted-foreground">컨텍스트</p>
                                                                <ul className="list-disc list-inside text-muted-foreground space-y-1">
                                                                    {contexts.slice(0, 3).map((ctx: string, ctxIndex: number) => (
                                                                        <li key={`${node.id}-ctx-${evidenceId}-${ctxIndex}`}>{ctx}</li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}
                                                        {metricsText && (
                                                            <div>
                                                                <p className="text-muted-foreground">메트릭</p>
                                                                <p className="text-foreground">{metricsText.join(" · ")}</p>
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}

                                <details className="border border-border rounded-lg">
                                    <summary className="px-3 py-2 text-xs text-muted-foreground cursor-pointer">
                                        RAW JSON
                                    </summary>
                                    <VirtualizedText
                                        text={rawText}
                                        height="16rem"
                                        className="bg-background border-t border-border p-3 text-xs"
                                    />
                                </details>
                            </div>
                        </details>
                    );
                })}
            </div>
        </div>
    );
}
