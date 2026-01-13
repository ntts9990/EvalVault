import { useMemo } from "react";
import { Link } from "react-router-dom";
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
    metadata?: Record<string, unknown> | null;
    tags?: string[];
};

type RunMetadata = {
    run_id?: string;
    dataset_name?: string;
    model_name?: string;
    [key: string]: unknown;
};

export type PrioritySummary = {
    bottom_percentile?: number;
    impact_count?: number;
    total_cases?: number;
    bottom_count?: number;
    bottom_cases?: PriorityCase[];
    impact_cases?: PriorityCase[];
    run_metadata?: RunMetadata | null;
};

const TAG_LABELS: Record<string, string> = {
    bottom_percentile: "하위",
    high_impact: "우선",
};

const METRIC_ACTIONS: Record<string, string> = {
    factual_correctness: "정답/지식베이스 검증과 후처리 룰을 점검하세요.",
    faithfulness: "컨텍스트 기반 답변 제약 및 인용 근거를 강화하세요.",
    answer_relevancy: "질문-답변 정렬 프롬프트/의도 파싱을 보강하세요.",
    context_recall: "retriever top_k/쿼리 확장/청킹 전략을 개선하세요.",
    context_precision: "리랭킹/필터링 강화로 노이즈를 줄이세요.",
    semantic_similarity: "정답 표현 다양성 또는 평가 기준을 재조정하세요.",
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

function formatMetadata(metadata?: Record<string, unknown> | null) {
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
    runId,
}: {
    item: PriorityCase;
    showImpact?: boolean;
    runId?: string | null;
}) {
    const metadataText = formatMetadata(item.metadata);
    const tags = item.tags || [];
    const runLink =
        runId && item.test_case_id
            ? `/runs/${runId}#case-${encodeURIComponent(item.test_case_id)}`
            : null;

    return (
        <div className="border border-border rounded-lg p-3 text-xs space-y-2 break-words">
            <div className="flex items-start justify-between gap-2">
                <div>
                    <p className="font-semibold">{item.test_case_id || "unknown"}</p>
                    <p className="text-[11px] text-muted-foreground">
                        평균 점수 {formatScore(item.avg_score)}
                        {showImpact ? ` · 영향도 ${formatScore(item.impact_score, 2)}` : ""}
                    </p>
                    {runLink && (
                        <Link
                            to={runLink}
                            className="text-[11px] text-primary underline underline-offset-2"
                        >
                            Run 상세 보기
                        </Link>
                    )}
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
    const bottomCases = useMemo(() => summary.bottom_cases ?? [], [summary.bottom_cases]);
    const impactCases = useMemo(() => summary.impact_cases ?? [], [summary.impact_cases]);

    const combinedCases = useMemo(() => {
        const merged = [...bottomCases, ...impactCases];
        const seen = new Set<string>();
        const unique: PriorityCase[] = [];
        for (const item of merged) {
            const key = item.test_case_id || item.question_preview || JSON.stringify(item);
            if (seen.has(key)) continue;
            seen.add(key);
            unique.push(item);
        }
        return unique;
    }, [bottomCases, impactCases]);

    const metricHighlights = useMemo(() => {
        const metricStats = new Map<string, { count: number; gapTotal: number }>();
        for (const item of combinedCases) {
            const failed = item.failed_metrics || [];
            for (const metric of failed) {
                const gap = item.gap_by_metric?.[metric] ?? 0;
                const entry = metricStats.get(metric) || { count: 0, gapTotal: 0 };
                entry.count += 1;
                entry.gapTotal += gap;
                metricStats.set(metric, entry);
            }
        }
        return Array.from(metricStats.entries())
            .sort((a, b) => {
                if (b[1].count !== a[1].count) return b[1].count - a[1].count;
                return b[1].gapTotal - a[1].gapTotal;
            })
            .slice(0, 3)
            .map(([metric, stats]) => ({
                metric,
                count: stats.count,
                avgGap: stats.count ? stats.gapTotal / stats.count : 0,
                action: METRIC_ACTIONS[metric],
            }));
    }, [combinedCases]);

    const questionHighlights = useMemo(() => {
        const counts = new Map<string, number>();
        for (const item of combinedCases) {
            const label = item.question_type_label || item.question_type;
            if (!label) continue;
            counts.set(label, (counts.get(label) || 0) + 1);
        }
        return Array.from(counts.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3);
    }, [combinedCases]);

    if (!bottomCases.length && !impactCases.length) return null;

    const bottomPercentile = summary.bottom_percentile ?? 10;
    const bottomCount = summary.bottom_count ?? bottomCases.length;
    const impactCount = summary.impact_count ?? impactCases.length;
    const totalCases = summary.total_cases ?? 0;
    const runMeta: RunMetadata = summary.run_metadata || {};
    const runId = typeof runMeta.run_id === "string" ? runMeta.run_id : null;

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

            {(metricHighlights.length > 0 || questionHighlights.length > 0) && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 text-xs">
                    {metricHighlights.length > 0 && (
                        <div className="border border-border rounded-lg p-3 space-y-2">
                            <p className="text-[11px] font-semibold text-muted-foreground">
                                주요 실패 메트릭
                            </p>
                            <div className="space-y-2">
                                {metricHighlights.map(item => (
                                    <div
                                        key={`metric-${item.metric}`}
                                        className="border border-border rounded-md px-2 py-1"
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="font-semibold">{item.metric}</span>
                                            <span className="text-[10px] text-muted-foreground">
                                                {item.count}건 · Δ{formatScore(item.avgGap, 2)}
                                            </span>
                                        </div>
                                        {item.action && (
                                            <p className="text-[11px] text-muted-foreground">{item.action}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    {questionHighlights.length > 0 && (
                        <div className="border border-border rounded-lg p-3 space-y-2">
                            <p className="text-[11px] font-semibold text-muted-foreground">
                                주요 질문 유형
                            </p>
                            <div className="flex flex-wrap gap-2">
                                {questionHighlights.map(([label, count]) => (
                                    <span
                                        key={`question-${label}`}
                                        className="px-2 py-1 rounded-full bg-secondary border border-border text-[10px] text-muted-foreground"
                                    >
                                        {label} · {count}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="space-y-2">
                    <p className="text-xs font-semibold text-muted-foreground">하위 성능 케이스</p>
                    {bottomCases.length === 0 ? (
                        <p className="text-xs text-muted-foreground">표시할 항목이 없습니다.</p>
                    ) : (
                        bottomCases.map(item => (
                            <CaseCard key={`bottom-${item.test_case_id}`} item={item} runId={runId} />
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
                                runId={runId}
                            />
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
