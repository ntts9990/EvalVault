import { useEffect, useMemo, useState } from "react";
import { SpacePlot2D } from "./SpacePlot2D";
import { SpacePlot3D } from "./SpacePlot3D";
import { SpaceLegend } from "./SpaceLegend";
import { useInsightSpace } from "../hooks/useInsightSpace";
import type { VisualSpaceGranularity, VisualSpaceQuery } from "../services/api";

const GRANULARITIES: { value: VisualSpaceGranularity; label: string }[] = [
    { value: "run", label: "런" },
    { value: "case", label: "케이스" },
    { value: "cluster", label: "클러스터" },
];

export function InsightSpacePanel({ runId }: { runId: string }) {
    const [granularity, setGranularity] = useState<VisualSpaceGranularity>("case");
    const [viewMode, setViewMode] = useState<"2d" | "3d">("2d");
    const [autoBase, setAutoBase] = useState(true);
    const [baseRunId, setBaseRunId] = useState("");
    const [clusterMap, setClusterMap] = useState<Record<string, string> | null>(null);
    const [clusterError, setClusterError] = useState<string | null>(null);

    const query: VisualSpaceQuery = useMemo(
        () => ({
            runId,
            granularity,
            baseRunId: autoBase ? undefined : baseRunId || undefined,
            autoBase,
            include: ["summary", "encoding", "breakdown"],
            clusterMap: granularity === "cluster" ? clusterMap || undefined : undefined,
        }),
        [runId, granularity, baseRunId, autoBase, clusterMap]
    );

    const { data, loading, error, reload } = useInsightSpace(query);

    useEffect(() => {
        if (granularity !== "cluster" && clusterMap) {
            setClusterMap(null);
            setClusterError(null);
        }
    }, [granularity, clusterMap]);

    const quadrantCounts = useMemo(() => {
        if (!data) return null;
        if (data.summary?.quadrant_counts) return data.summary.quadrant_counts;

        const counts: Record<string, number> = {};
        data.points.forEach((p) => {
            const q = p.labels?.quadrant;
            if (q) counts[q] = (counts[q] || 0) + 1;
        });
        return counts;
    }, [data]);

    const QUADRANT_DISPLAY = [
        { key: "search_boost", label: "좌상단" },
        { key: "expand", label: "우상단" },
        { key: "reset", label: "좌하단" },
        { key: "generation_fix", label: "우하단" },
    ];

    const handleClusterUpload = async (file: File) => {
        setClusterError(null);
        try {
            const text = await file.text();
            const parsed =
                file.name.toLowerCase().endsWith(".json") ?
                    parseClusterJson(text) :
                    parseClusterCsv(text);
            if (!parsed || Object.keys(parsed).length === 0) {
                throw new Error("클러스터 매핑이 없습니다.");
            }
            setClusterMap(parsed);
        } catch (err) {
            setClusterMap(null);
            setClusterError(err instanceof Error ? err.message : "클러스터 맵 파싱 실패");
        }
    };

    return (
        <div className="surface-panel p-6 mb-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                    <p className="section-kicker">인사이트 공간</p>
                    <h3 className="section-title">4사분면 개요</h3>
                    <p className="text-xs text-muted-foreground mt-1">
                        근거 충족도 vs 답변 정합성 (2D에서는 Z 축을 숨깁니다).
                    </p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                    <div className="tab-shell">
                        <button
                            className={`tab-pill ${
                                viewMode === "2d" ? "tab-pill-active" : "tab-pill-inactive"
                            }`}
                            onClick={() => setViewMode("2d")}
                        >
                            2D
                        </button>
                        <button
                            className={`tab-pill ${
                                viewMode === "3d" ? "tab-pill-active" : "tab-pill-inactive"
                            }`}
                            onClick={() => setViewMode("3d")}
                        >
                            3D
                        </button>
                    </div>
                    <select
                        className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
                        value={granularity}
                        onChange={(event) =>
                            setGranularity(event.target.value as VisualSpaceGranularity)
                        }
                    >
                        {GRANULARITIES.map((item) => (
                            <option key={item.value} value={item.value}>
                                {item.label}
                            </option>
                        ))}
                    </select>
                    <label className="flex items-center gap-2 text-xs text-muted-foreground">
                        <input
                            type="checkbox"
                            className="h-4 w-4 rounded border-border"
                            checked={autoBase}
                        onChange={(event) => setAutoBase(event.target.checked)}
                    />
                        자동 기준
                    </label>
                    <input
                        type="text"
                        value={baseRunId}
                        placeholder="기준 Run ID"
                        disabled={autoBase}
                        onChange={(event) => setBaseRunId(event.target.value)}
                        className={
                            "rounded-lg border border-border bg-background px-3 py-2 text-xs " +
                            "font-mono"
                        }
                    />
                    <button
                        className={
                            "rounded-lg border border-border bg-secondary/60 px-3 py-2 text-xs " +
                            "font-medium"
                        }
                        onClick={reload}
                    >
                        새로고침
                    </button>
                </div>
            </div>

            {granularity === "cluster" && (
                <div
                    className={
                        "mt-4 flex flex-wrap items-center gap-3 text-xs text-muted-foreground"
                    }
                >
                    <label className="flex items-center gap-2">
                        <span className="font-medium text-foreground">클러스터 맵</span>
                        <input
                            type="file"
                            accept=".csv,.json"
                            className="text-xs"
                            onChange={(event) => {
                                const file = event.target.files?.[0];
                                if (file) handleClusterUpload(file);
                            }}
                        />
                    </label>
                    <span className="text-xs text-muted-foreground">
                        CSV 형식: test_case_id,cluster_id
                    </span>
                    {clusterMap && (
                        <span
                            className={
                                "rounded-full border border-emerald-400/30 bg-emerald-500/10 " +
                                "px-3 py-1 text-emerald-600"
                            }
                        >
                            {Object.keys(clusterMap).length}개 매핑됨
                        </span>
                    )}
                    {clusterError && (
                        <span
                            className={
                                "rounded-full border border-rose-400/30 bg-rose-500/10 " +
                                "px-3 py-1 text-rose-600"
                            }
                        >
                            {clusterError}
                        </span>
                    )}
                </div>
            )}

            <div className="mt-5">
                {loading && (
                    <div
                        className={
                            "h-[360px] w-full flex items-center justify-center " +
                            "text-muted-foreground"
                        }
                >
                        인사이트 공간 로딩 중...
                    </div>
                )}
                {error && (
                    <div
                        className={
                            "h-[360px] w-full flex items-center justify-center text-rose-500"
                        }
                    >
                        {error}
                    </div>
                )}
                {!loading && !error && data && viewMode === "2d" && (
                    <SpacePlot2D points={data.points} />
                )}
                {!loading && !error && data && viewMode === "3d" && (
                    <SpacePlot3D points={data.points} />
                )}
            </div>

            {data?.warnings && data.warnings.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                    {data.warnings.map((warning) => (
                        <span
                            key={warning}
                            className={
                                "rounded-full border border-amber-400/30 bg-amber-500/10 " +
                                "px-3 py-1 text-xs text-amber-600"
                            }
                        >
                            {warning}
                        </span>
                    ))}
                </div>
            )}

            {quadrantCounts && (
                <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-xs border-t border-border/40 pt-3">
                    {QUADRANT_DISPLAY.map(({ key, label }) => (
                        <div key={key} className="flex items-center gap-2">
                            <span className="text-muted-foreground">{label}</span>
                            <span className="font-mono font-medium text-foreground">
                                {quadrantCounts[key] || 0}
                            </span>
                        </div>
                    ))}
                </div>
            )}

            {data?.summary && (
                <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
                    {"regressions" in data.summary && (
                        <span>Regressions: {String(data.summary.regressions)}</span>
                    )}
                    {"improvements" in data.summary && (
                        <span>Improvements: {String(data.summary.improvements)}</span>
                    )}
                </div>
            )}

            <div className="mt-5">
                <SpaceLegend />
            </div>
        </div>
    );
}

const parseClusterJson = (raw: string): Record<string, string> => {
    const data = JSON.parse(raw);
    if (Array.isArray(data)) {
        return data.reduce<Record<string, string>>((acc, item) => {
            if (!item || typeof item !== "object") return acc;
            const caseId = item.test_case_id || item.case_id || item.id;
            const clusterId = item.cluster_id || item.cluster;
            if (caseId != null && clusterId != null) {
                acc[String(caseId)] = String(clusterId);
            }
            return acc;
        }, {});
    }
    if (data && typeof data === "object") {
        return Object.fromEntries(
            Object.entries(data).map(([key, value]) => [String(key), String(value)])
        );
    }
    return {};
};

const parseClusterCsv = (raw: string): Record<string, string> => {
    const lines = raw.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    if (lines.length === 0) return {};
    const separator = lines[0].includes(",") ? "," : lines[0].includes("\t") ? "\t" : ";";
    const entries = lines.map((line) => line.split(separator).map((cell) => cell.trim()));
    if (entries.length === 0) return {};

    const header = entries[0].map((cell) => cell.toLowerCase());
    const hasHeader = header.some((cell) => cell.includes("case") || cell.includes("cluster"));
    const startIndex = hasHeader ? 1 : 0;

    const mapping: Record<string, string> = {};
    for (let i = startIndex; i < entries.length; i += 1) {
        const [caseId, clusterId] = entries[i];
        if (!caseId || !clusterId) continue;
        mapping[String(caseId)] = String(clusterId);
    }
    return mapping;
};
