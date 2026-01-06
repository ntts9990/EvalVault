import { VirtualizedText } from "./VirtualizedText";

export type PriorityCase = {
    test_case_id?: string;
    avg_score?: number;
    failed_metrics?: string[];
    failed_metric_count?: number;
    gap_by_metric?: Record<string, number>;
    shortfall?: number;
    impact_score?: number;
    worst_metric?: string | null;
    worst_score?: number | null;
    worst_gap?: number | null;
    question_type?: string;
    question_type_label?: string;
    question_preview?: string;
    analysis_hints?: string[];
    metadata?: Record<string, any> | null;
    tags?: string[];
};

export type PrioritySummary = {
    bottom_percentile?: number;
    impact_count?: number;
    total_cases?: number;
    bottom_count?: number;
    bottom_cases?: PriorityCase[];
    impact_cases?: PriorityCase[];
    run_metadata?: Record<string, any> | null;
};

const TAG_LABELS: Record<string, string> = {
    bottom_percentile: "하위",
    high_impact: "우선",
};

function formatScore(value: unknown, digits: number = 2) {
    if (typeof value === "number" && Number.isFinite(value)) {
        return value.toFixed(digits);
    }
    return "-";
}

function formatGapList(gaps?: Record<string, number>) {
    if (!gaps) return "-";
    const entries = Object.entries(gaps);
    if (!entries.length) return "-";
    return entries.map(([metric, gap]) => `${metric} +${formatScore(gap, 2)}`).join(", ");
}

function formatMetadata(metadata?: Record<string, any> | null) {
    if (!metadata) return null;
    try {
        return JSON.stringify(metadata, null, 2);
    } catch {
        return String(metadata);
    }
}

function CaseCard({
    item,
    showImpact = false,
}: {
    item: PriorityCase;
    showImpact?: boolean;
}) {
    const metadataText = formatMetadata(item.metadata);
    const tags = item.tags || [];

    return (
        <div className="border border-border rounded-lg p-3 text-xs space-y-2 break-words">
            <div className="flex items-start justify-between gap-2">
                <div>
                    <p className="font-semibold">{item.test_case_id || "unknown"}</p>
                    <p className="text-[11px] text-muted-foreground">
                        평균 점수 {formatScore(item.avg_score)}
                        {showImpact ? ` · 영향도 ${formatScore(item.impact_score, 2)}` : ""}
                    </p>
                </div>
                {tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                        {tags.map(tag => (
                            <span
                                key={`${item.test_case_id}-${tag}`}
                                className="px-2 py-0.5 rounded-full bg-secondary border border-border text-[10px] text-muted-foreground"
                            >
                                {TAG_LABELS[tag] || tag}
                            </span>
                        ))}
                    </div>
                )}
            </div>
            <div className="text-muted-foreground">
                질문 유형: {item.question_type_label || item.question_type || "-"}
            </div>
            <div className="text-foreground">질문: {item.question_preview || "-"}</div>
            <div className="text-muted-foreground">
                실패 메트릭: {item.failed_metrics?.length ? item.failed_metrics.join(", ") : "-"}
            </div>
            <div className="text-muted-foreground">
                메트릭 갭: {formatGapList(item.gap_by_metric)}
            </div>
            {item.worst_metric && (
                <div className="text-muted-foreground">
                    최저 메트릭: {item.worst_metric} ({formatScore(item.worst_score)})
                </div>
            )}
            {item.analysis_hints && item.analysis_hints.length > 0 && (
                <div className="text-muted-foreground">
                    힌트: {item.analysis_hints.join(" · ")}
                </div>
            )}
            {metadataText && (
                <details className="border border-border rounded-md">
                    <summary className="cursor-pointer px-2 py-1 text-[11px] text-muted-foreground">
                        메타데이터
                    </summary>
                    <VirtualizedText
                        text={metadataText}
                        height="8rem"
                        className="bg-background border-t border-border p-2 text-[11px]"
                    />
                </details>
            )}
        </div>
    );
}

export function PrioritySummaryPanel({ summary }: { summary: PrioritySummary }) {
    const bottomCases = summary.bottom_cases || [];
    const impactCases = summary.impact_cases || [];
    if (!bottomCases.length && !impactCases.length) return null;

    const bottomPercentile = summary.bottom_percentile ?? 10;
    const bottomCount = summary.bottom_count ?? bottomCases.length;
    const impactCount = summary.impact_count ?? impactCases.length;
    const totalCases = summary.total_cases ?? 0;
    const runMeta = summary.run_metadata || {};

    return (
        <div className="border border-border rounded-xl p-4 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                    <h3 className="text-sm font-semibold">문제 케이스 분류</h3>
                    <p className="text-xs text-muted-foreground">
                        하위 {bottomPercentile}% ({bottomCount}개) · 영향도 상위 {impactCount}개
                    </p>
                </div>
                <div className="text-[11px] text-muted-foreground">
                    {runMeta.dataset_name ? `${runMeta.dataset_name} · ` : ""}
                    {runMeta.model_name || ""}
                    {totalCases ? ` · 총 ${totalCases}건` : ""}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="space-y-2">
                    <p className="text-xs font-semibold text-muted-foreground">하위 성능 케이스</p>
                    {bottomCases.length === 0 ? (
                        <p className="text-xs text-muted-foreground">표시할 항목이 없습니다.</p>
                    ) : (
                        bottomCases.map(item => (
                            <CaseCard key={`bottom-${item.test_case_id}`} item={item} />
                        ))
                    )}
                </div>
                <div className="space-y-2">
                    <p className="text-xs font-semibold text-muted-foreground">개선 효과 우선 케이스</p>
                    {impactCases.length === 0 ? (
                        <p className="text-xs text-muted-foreground">표시할 항목이 없습니다.</p>
                    ) : (
                        impactCases.map(item => (
                            <CaseCard
                                key={`impact-${item.test_case_id}`}
                                item={item}
                                showImpact
                            />
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
