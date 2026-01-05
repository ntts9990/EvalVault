import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import { VirtualizedText } from "./VirtualizedText";

const STATUS_META: Record<string, { label: string; color: string }> = {
    completed: { label: "완료", color: "text-emerald-600" },
    failed: { label: "실패", color: "text-rose-600" },
    skipped: { label: "스킵", color: "text-amber-600" },
    running: { label: "실행 중", color: "text-blue-600" },
    pending: { label: "대기", color: "text-muted-foreground" },
};

type NodeResult = {
    status?: string;
    error?: string | null;
    duration_ms?: number | null;
    output?: any;
};

type NodeDefinition = {
    id: string;
    name: string;
    module: string;
    depends_on: string[];
};

function formatValue(value: any) {
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
    nodeResults: Record<string, NodeResult>,
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
            result: nodeResults[id],
        };
    });
}

function extractEvidence(output: any) {
    if (!output || typeof output !== "object") return [];
    if (Array.isArray(output.evidence)) return output.evidence;
    if (Array.isArray(output.evidence_samples)) return output.evidence_samples;
    if (Array.isArray(output.samples)) return output.samples;
    return [];
}

function formatMetrics(metrics: Record<string, any> | null | undefined) {
    if (!metrics) return null;
    return Object.entries(metrics).map(([key, value]) => {
        if (typeof value === "number" && Number.isFinite(value)) {
            return `${key}: ${value.toFixed(3)}`;
        }
        return `${key}: ${String(value)}`;
    });
}

export function AnalysisNodeOutputs({
    nodeResults,
    nodeDefinitions,
    title = "노드 출력",
}: {
    nodeResults?: Record<string, NodeResult> | null;
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
                    const reportText =
                        output && typeof output === "object" && typeof output.report === "string"
                            ? output.report
                            : null;
                    const summary =
                        output && typeof output === "object" && output.summary && typeof output.summary === "object"
                            ? output.summary
                            : null;
                    const insights =
                        output && typeof output === "object" && Array.isArray(output.insights)
                            ? output.insights
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
                                                <div className="prose prose-sm max-w-none">
                                                    <ReactMarkdown>{reportText}</ReactMarkdown>
                                                </div>
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
                                                <li key={`${node.id}-insight-${index}`}>{item}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {evidence.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-muted-foreground">증거 샘플</p>
                                        <div className="space-y-3">
                                            {evidence.slice(0, 6).map((item: any, index: number) => {
                                                const evidenceId =
                                                    item.evidence_id
                                                    || item.id
                                                    || item.test_case_id
                                                    || item.case_id
                                                    || `evidence-${index + 1}`;
                                                const question = item.question || item.query || item.user_input;
                                                const answer = item.answer || item.response;
                                                const contexts = item.contexts || item.retrieved_contexts;
                                                const metrics = item.metrics || item.scores;
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
