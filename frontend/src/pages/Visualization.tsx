import { useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";
import { Link, useParams } from "react-router-dom";
import {
    CartesianGrid,
    ReferenceLine,
    ResponsiveContainer,
    Scatter,
    ScatterChart,
    Tooltip,
    XAxis,
    YAxis,
    ZAxis,
    Cell,
} from "recharts";
import { ArrowLeft, Info, UploadCloud, X, XCircle } from "lucide-react";
import { Layout } from "../components/Layout";
import { CHART_METRIC_COLORS } from "../config/ui";
import {
    fetchClusterMapFile,
    fetchClusterMapFiles,
    fetchRunClusterMap,
    fetchRunClusterMapById,
    fetchRunClusterMaps,
    fetchRunDetails,
    fetchMetricSpecs,
    deleteRunClusterMap,
    saveRunClusterMap,
    type ClusterMapFileInfo,
    type ClusterMapVersionInfo,
    type MetricSpec,
    type RunDetailsResponse,
} from "../services/api";
import { formatScore, normalizeScore, safeAverage } from "../utils/score";

type AxisSpec = {
    key: "x" | "y" | "z";
    label: string;
    metrics: string[];
    description: string;
    detail: {
        calc: string;
        meaning: string;
        effect: string;
    };
};

type QuadrantSpec = {
    id: string;
    label: string;
    desc: string;
    detail: {
        calc: string;
        meaning: string;
        effect: string;
    };
};

type ScatterPoint = {
    id: string;
    question: string;
    answer: string;
    x: number;
    y: number;
    z: number;
    avg: number;
    passRate: number;
    failedMetrics: string[];
    clusterId?: string;
    quadrant: string | null;
    metrics: RunDetailsResponse["results"][number]["metrics"];
};

const SIGNAL_GROUP_META: Record<
    string,
    {
        label: string;
        description: string;
        detail: AxisSpec["detail"];
    }
> = {
    groundedness: {
        label: "근거성",
        description: "답변이 컨텍스트/사실에 근거하는 정도",
        detail: {
            calc: "그룹 내 사용 가능한 지표 평균 (누락 시 전체 평균으로 보정)",
            meaning: "근거 기반으로 답변이 신뢰 가능한지 보여줍니다.",
            effect: "낮으면 환각/근거 부족 리스크가 커집니다.",
        },
    },
    intent_alignment: {
        label: "질문-답변 정합성",
        description: "질문 의도와 답변 내용의 정합 정도",
        detail: {
            calc: "그룹 내 사용 가능한 지표 평균 (누락 시 전체 평균으로 보정)",
            meaning: "질문 의도에 맞는 답변을 내는지 보여줍니다.",
            effect: "낮으면 질문 해석/응답 방향이 어긋납니다.",
        },
    },
    retrieval_effectiveness: {
        label: "검색 효과성",
        description: "검색된 컨텍스트의 적합/재현 품질",
        detail: {
            calc: "그룹 내 사용 가능한 지표 평균 (누락 시 전체 평균으로 보정)",
            meaning: "검색 결과가 답변을 뒷받침하는지 나타냅니다.",
            effect: "낮으면 RAG 성능 저하가 발생합니다.",
        },
    },
    summary_fidelity: {
        label: "요약 품질",
        description: "요약의 정보 보존과 충실도",
        detail: {
            calc: "그룹 내 사용 가능한 지표 평균 (누락 시 전체 평균으로 보정)",
            meaning: "요약이 핵심 정보를 보존하는지 보여줍니다.",
            effect: "낮으면 요약 왜곡/누락 위험이 큽니다.",
        },
    },
    embedding_quality: {
        label: "임베딩 안정성",
        description: "임베딩 분포와 품질 안정성",
        detail: {
            calc: "그룹 내 사용 가능한 지표 평균 (누락 시 전체 평균으로 보정)",
            meaning: "임베딩 품질의 안정성을 나타냅니다.",
            effect: "낮으면 검색/유사도 품질이 흔들립니다.",
        },
    },
    efficiency: {
        label: "효율/지연",
        description: "응답/검색 효율과 지연",
        detail: {
            calc: "그룹 내 사용 가능한 지표 평균 (누락 시 전체 평균으로 보정)",
            meaning: "처리 효율과 지연 수준을 보여줍니다.",
            effect: "낮으면 비용/지연 부담이 커집니다.",
        },
    },
};

const SIGNAL_GROUP_ORDER = [
    "groundedness",
    "intent_alignment",
    "retrieval_effectiveness",
    "summary_fidelity",
    "embedding_quality",
    "efficiency",
];

const FALLBACK_AXIS_SPECS: AxisSpec[] = [
    {
        key: "x",
        label: "근거성",
        metrics: ["faithfulness", "factual_correctness", "context_precision", "context_recall"],
        description: "근거와 사실성 지표의 평균",
        detail: {
            calc: "(faithfulness + factual_correctness + context_precision + context_recall) / 4 (누락 시 전체 평균으로 보정)",
            meaning: "컨텍스트 근거와 사실성이 함께 충족되는 정도를 나타냅니다.",
            effect: "낮으면 근거 부족/검증 실패 위험이 커집니다.",
        },
    },
    {
        key: "y",
        label: "관련성",
        metrics: ["answer_relevancy", "semantic_similarity"],
        description: "질문-응답 관련성 지표의 평균",
        detail: {
            calc: "(answer_relevancy + semantic_similarity) / 2 (누락 시 전체 평균으로 보정)",
            meaning: "질문 의도와 답변 내용이 얼마나 밀착되는지 보여줍니다.",
            effect: "낮으면 질문 해석/답변 방향의 미스매치 가능성이 큽니다.",
        },
    },
    {
        key: "z",
        label: "요약 품질",
        metrics: [
            "summary_score",
            "summary_faithfulness",
            "entity_preservation",
            "summary_accuracy",
            "summary_risk_coverage",
            "summary_non_definitive",
            "summary_needs_followup",
        ],
        description: "요약/보존 지표의 평균",
        detail: {
            calc: "(summary_score + summary_faithfulness + entity_preservation + summary_accuracy + summary_risk_coverage + summary_non_definitive + summary_needs_followup) / 7 (누락 시 전체 평균으로 보정)",
            meaning: "요약의 핵심 보존, 근거성, 리스크 안내, 단정 표현 억제를 통합한 품질 지표입니다.",
            effect: "낮으면 요약이 왜곡되거나 핵심 정보가 누락됩니다.",
        },
    },
];

const CHART_THRESHOLD = 0.7;

const createQuadrantHints = (xLabel: string, yLabel: string): QuadrantSpec[] => [
    {
        id: "ur",
        label: "우상단",
        desc: `${xLabel}과 ${yLabel} 모두 높은 영역`,
        detail: {
            calc: `${xLabel} ≥ ${CHART_THRESHOLD}, ${yLabel} ≥ ${CHART_THRESHOLD}`,
            meaning: "두 축 모두 높은 안정 구간입니다.",
            effect: "현재 전략을 유지하고 확대하기에 유리합니다.",
        },
    },
    {
        id: "ul",
        label: "좌상단",
        desc: `${yLabel}은 높지만 ${xLabel}이 낮은 영역`,
        detail: {
            calc: `${xLabel} < ${CHART_THRESHOLD}, ${yLabel} ≥ ${CHART_THRESHOLD}`,
            meaning: "한 축은 안정적이지만 다른 축이 약한 상태입니다.",
            effect: "약한 축의 개선 우선순위를 높게 잡는 것이 좋습니다.",
        },
    },
    {
        id: "lr",
        label: "우하단",
        desc: `${xLabel}은 높지만 ${yLabel}이 낮은 영역`,
        detail: {
            calc: `${xLabel} ≥ ${CHART_THRESHOLD}, ${yLabel} < ${CHART_THRESHOLD}`,
            meaning: "한 축은 안정적이지만 다른 축이 약한 상태입니다.",
            effect: "약한 축의 개선 우선순위를 높게 잡는 것이 좋습니다.",
        },
    },
    {
        id: "ll",
        label: "좌하단",
        desc: `${xLabel}과 ${yLabel} 모두 낮은 영역`,
        detail: {
            calc: `${xLabel} < ${CHART_THRESHOLD}, ${yLabel} < ${CHART_THRESHOLD}`,
            meaning: "두 축 모두 낮아 전반적 품질 위험이 큽니다.",
            effect: "검색부터 생성까지 파이프라인 재점검이 필요합니다.",
        },
    },
];

function toScoreColor(score: number): string {
    const safeScore = Math.max(0, Math.min(1, score));
    const hue = Math.round(120 * safeScore);
    return `hsl(${hue}, 65%, 45%)`;
}

function parseClusterMap(text: string): Map<string, string> {
    const map = new Map<string, string>();
    const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    if (!lines.length) {
        return map;
    }
    const header = lines[0].toLowerCase();
    const startIndex = header.includes("test_case_id") ? 1 : 0;
    for (const line of lines.slice(startIndex)) {
        const [id, cluster] = line.split(",").map((part) => part?.trim());
        if (!id || !cluster) {
            continue;
        }
        map.set(id, cluster);
    }
    return map;
}

function buildAxisValue(
    metricMap: Map<string, { score: number }>,
    metrics: string[],
    fallback: number
): number {
    const scores = metrics
        .map((name) => metricMap.get(name)?.score)
        .filter((value): value is number => typeof value === "number");
    if (!scores.length) {
        return fallback;
    }
    return safeAverage(scores.map(normalizeScore));
}

type PlotlyInstance = {
    newPlot: (
        element: HTMLElement,
        data: unknown[],
        layout: Record<string, unknown>,
        config: Record<string, unknown>
    ) => Promise<void> | void;
    purge: (element: HTMLElement) => void;
};

type PlotlyClickEvent = {
    points?: Array<{ pointIndex?: number; pointNumber?: number }>;
};

function VisualizationPlot({
    points,
    axisSpecs,
    colorMode,
    clusterPalette,
    onSelect,
}: {
    points: ScatterPoint[];
    axisSpecs: AxisSpec[];
    colorMode: "score" | "cluster";
    clusterPalette: Map<string, string>;
    onSelect: (point: ScatterPoint) => void;
}) {
    const plotRef = useRef<HTMLDivElement | null>(null);
    const plotlyRef = useRef<PlotlyInstance | null>(null);

    useEffect(() => {
        let cancelled = false;

        const plotElement = plotRef.current;
        const render = async () => {
            if (!plotElement || points.length === 0) {
                return;
            }
            const module = await import("plotly.js-dist-min");
            const PlotlyModule = module as unknown as PlotlyInstance & { default?: PlotlyInstance };
            const Plotly = PlotlyModule.default ?? PlotlyModule;
            if (cancelled || !plotElement) {
                return;
            }
            plotlyRef.current = Plotly;

            const colors = points.map((point) => {
                if (colorMode === "cluster" && point.clusterId) {
                    const clusterColor = clusterPalette.get(point.clusterId);
                    if (clusterColor) {
                        return clusterColor;
                    }
                }
                return toScoreColor(point.avg);
            });

            const data = [
                {
                    type: "scatter3d",
                    mode: "markers",
                    x: points.map((point) => point.x),
                    y: points.map((point) => point.y),
                    z: points.map((point) => point.z),
                    text: points.map(
                        (point) =>
                            `${point.id}<br>${point.question}<br>평균 ${formatScore(point.avg)}`
                    ),
                    marker: {
                        size: points.map((point) => 6 + point.avg * 10),
                        color: colors,
                        opacity: 0.9,
                        line: {
                            width: 1,
                            color: "rgba(15, 23, 42, 0.35)",
                        },
                    },
                    hovertemplate: "%{text}<extra></extra>",
                },
            ];

            const axisTitleFont = { size: 12, color: "#475569" };
            const axisTickFont = { size: 11, color: "#64748b" };
            const layout = {
                margin: { l: 0, r: 0, t: 20, b: 0 },
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                clickmode: "event+select",
                scene: {
                    xaxis: {
                        title: { text: axisSpecs[0]?.label ?? "X", font: axisTitleFont },
                        range: [0, 1],
                        tickfont: axisTickFont,
                        gridcolor: "rgba(148,163,184,0.2)",
                    },
                    yaxis: {
                        title: { text: axisSpecs[1]?.label ?? "Y", font: axisTitleFont },
                        range: [0, 1],
                        tickfont: axisTickFont,
                        gridcolor: "rgba(148,163,184,0.2)",
                    },
                    zaxis: {
                        title: { text: axisSpecs[2]?.label ?? "Z", font: axisTitleFont },
                        range: [0, 1],
                        tickfont: axisTickFont,
                        gridcolor: "rgba(148,163,184,0.2)",
                    },
                },
            };

            const config = {
                displayModeBar: false,
                responsive: true,
            };

            await Plotly.newPlot(plotElement, data, layout, config);
            const node = plotElement as unknown as {
                on?: (eventName: string, handler: (event: PlotlyClickEvent) => void) => void;
            };
            node.on?.("plotly_click", (event) => {
                const hit = event?.points?.[0];
                const pointIndex = hit?.pointIndex ?? hit?.pointNumber;
                if (typeof pointIndex === "number" && points[pointIndex]) {
                    onSelect(points[pointIndex]);
                }
            });
        };

        render();

        return () => {
            cancelled = true;
            const plotly = plotlyRef.current;
            if (plotElement && plotly) {
                plotly.purge(plotElement);
            }
        };
    }, [points, axisSpecs, colorMode, clusterPalette, onSelect]);

    return <div ref={plotRef} className="h-[520px] w-full" />;
}

export function Visualization() {
    const { id } = useParams<{ id: string }>();
    const [data, setData] = useState<RunDetailsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [metricSpecs, setMetricSpecs] = useState<MetricSpec[]>([]);
    const [metricSpecError, setMetricSpecError] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<"2d" | "3d">("2d");
    const [colorMode, setColorMode] = useState<"score" | "cluster">("score");
    const [clusterMap, setClusterMap] = useState<Map<string, string>>(new Map());
    const [clusterSource, setClusterSource] = useState<"auto" | "upload" | "manual" | null>(null);
    const [clusterSourceLabel, setClusterSourceLabel] = useState<string | null>(null);
    const [clusterError, setClusterError] = useState<string | null>(null);
    const [clusterFiles, setClusterFiles] = useState<ClusterMapFileInfo[]>([]);
    const [clusterFilesError, setClusterFilesError] = useState<string | null>(null);
    const [clusterFilesLoading, setClusterFilesLoading] = useState(true);
    const [selectedClusterFile, setSelectedClusterFile] = useState("");
    const [runClusterMaps, setRunClusterMaps] = useState<ClusterMapVersionInfo[]>([]);
    const [runClusterMapsLoading, setRunClusterMapsLoading] = useState(true);
    const [runClusterMapsError, setRunClusterMapsError] = useState<string | null>(null);
    const [activeMapId, setActiveMapId] = useState<string | null>(null);
    const [activeMapCreatedAt, setActiveMapCreatedAt] = useState<string | null>(null);
    const [clusterFilter, setClusterFilter] = useState<Set<string>>(new Set());
    const [selectedPoint, setSelectedPoint] = useState<ScatterPoint | null>(null);
    const [activeDetail, setActiveDetail] = useState<string | null>(null);

    useEffect(() => {
        async function loadDetails() {
            if (!id) return;
            try {
                const details = await fetchRunDetails(id);
                setData(details);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load run");
            } finally {
                setLoading(false);
            }
        }
        loadDetails();
    }, [id]);

    useEffect(() => {
        let cancelled = false;
        setMetricSpecError(null);
        fetchMetricSpecs()
            .then((specs) => {
                if (!cancelled) {
                    setMetricSpecs(specs);
                }
            })
            .catch((err) => {
                if (!cancelled) {
                    setMetricSpecError(
                        err instanceof Error ? err.message : "메트릭 스펙을 불러오지 못했습니다."
                    );
                }
            });
        return () => {
            cancelled = true;
        };
    }, []);

    useEffect(() => {
        let cancelled = false;
        setClusterFilesError(null);
        setClusterFilesLoading(true);
        fetchClusterMapFiles()
            .then((files) => {
                if (cancelled) {
                    return;
                }
                const sorted = [...files].sort((a, b) => a.name.localeCompare(b.name));
                setClusterFiles(sorted);
                setClusterFilesLoading(false);
            })
            .catch((err) => {
                if (!cancelled) {
                    setClusterFilesError(
                        err instanceof Error ? err.message : "클러스터 맵 목록을 불러오지 못했습니다."
                    );
                    setClusterFilesLoading(false);
                }
            });
        return () => {
            cancelled = true;
        };
    }, []);

    useEffect(() => {
        if (!id) {
            return;
        }
        let cancelled = false;
        setRunClusterMapsLoading(true);
        setRunClusterMapsError(null);
        fetchRunClusterMaps(id)
            .then((maps) => {
                if (cancelled) {
                    return;
                }
                setRunClusterMaps(maps);
            })
            .catch((err) => {
                if (!cancelled) {
                    setRunClusterMapsError(
                        err instanceof Error
                            ? err.message
                            : "클러스터 맵 버전을 불러오지 못했습니다."
                    );
                }
            })
            .finally(() => {
                if (!cancelled) {
                    setRunClusterMapsLoading(false);
                }
            });
        return () => {
            cancelled = true;
        };
    }, [id]);

    useEffect(() => {
        setClusterMap(new Map());
        setClusterSource(null);
        setClusterSourceLabel(null);
        setClusterError(null);
        setSelectedClusterFile("");
        setRunClusterMaps([]);
        setRunClusterMapsError(null);
        setActiveMapId(null);
        setActiveMapCreatedAt(null);
        setClusterFilter(new Set());
        setColorMode("score");
        setSelectedPoint(null);
    }, [id]);

    useEffect(() => {
        if (!data?.summary?.run_id || clusterSource !== null) {
            return;
        }
        let cancelled = false;
        fetchRunClusterMap(data.summary.run_id)
            .then((response) => {
                if (cancelled || !response.items.length) {
                    return;
                }
                const map = new Map(
                    response.items.map((item) => [item.test_case_id, item.cluster_id])
                );
                setClusterMap(map);
                setClusterFilter(new Set());
                setColorMode("cluster");
                setClusterSource(response.source?.startsWith("auto") ? "auto" : "manual");
                setClusterSourceLabel(response.source ?? null);
                setActiveMapId(response.map_id ?? null);
                setActiveMapCreatedAt(response.created_at ?? null);
                if (data.summary.run_id) {
                    refreshRunClusterMaps(data.summary.run_id).catch(() => undefined);
                }
            })
            .catch(() => {
                if (!cancelled) {
                    setClusterSource("manual");
                }
            });

        return () => {
            cancelled = true;
        };
    }, [data, clusterSource]);

    const availableMetricNames = useMemo(() => {
        if (!data) {
            return new Set<string>();
        }
        const names = new Set<string>();
        data.results.forEach((result) => {
            result.metrics.forEach((metric) => {
                names.add(metric.name);
            });
        });
        return names;
    }, [data]);

    const axisSpecs = useMemo(() => {
        if (!metricSpecs.length || availableMetricNames.size === 0) {
            return FALLBACK_AXIS_SPECS;
        }

        const groupMap = new Map<string, string[]>();
        metricSpecs.forEach((spec) => {
            if (!availableMetricNames.has(spec.name)) {
                return;
            }
            const metrics = groupMap.get(spec.signal_group) || [];
            metrics.push(spec.name);
            groupMap.set(spec.signal_group, metrics);
        });

        if (groupMap.size === 0) {
            return FALLBACK_AXIS_SPECS;
        }

        const orderIndex = new Map(
            SIGNAL_GROUP_ORDER.map((group, index) => [group, index])
        );
        const groupEntries = Array.from(groupMap.entries()).map(([groupId, metrics]) => ({
            groupId,
            metrics: metrics.sort((a, b) => a.localeCompare(b)),
            count: metrics.length,
            order: orderIndex.get(groupId) ?? 999,
        }));

        groupEntries.sort((left, right) => {
            if (right.count !== left.count) {
                return right.count - left.count;
            }
            return left.order - right.order;
        });

        const axisKeys: AxisSpec["key"][] = ["x", "y", "z"];
        const specs = groupEntries.slice(0, 3).map((entry, index) => {
            const meta = SIGNAL_GROUP_META[entry.groupId];
            const label = meta?.label ?? entry.groupId;
            const description = meta?.description ?? `${label} 지표 평균`;
            const detail = meta?.detail ?? {
                calc: "그룹 내 사용 가능한 지표 평균 (누락 시 전체 평균으로 보정)",
                meaning: "지표 묶음의 평균으로 축을 구성합니다.",
                effect: "낮을수록 해당 영역 품질 리스크가 큽니다.",
            };
            return {
                key: axisKeys[index],
                label,
                metrics: entry.metrics,
                description,
                detail,
            };
        });

        while (specs.length < 3) {
            const key = axisKeys[specs.length];
            specs.push({
                key,
                label: "전체 평균",
                metrics: [],
                description: "전체 지표 평균",
                detail: {
                    calc: "전체 지표 평균",
                    meaning: "지표 전체 평균으로 축을 구성합니다.",
                    effect: "낮을수록 전반적 품질 리스크가 큽니다.",
                },
            });
        }

        return specs;
    }, [metricSpecs, availableMetricNames]);

    const points = useMemo(() => {
        if (!data) return [];
        return data.results.map((result) => {
            const metricMap = new Map(
                result.metrics.map((metric) => [metric.name, { score: normalizeScore(metric.score) }])
            );
            const avgAll = safeAverage(result.metrics.map((metric) => normalizeScore(metric.score)));
            const axisValues = axisSpecs.map((axis) =>
                buildAxisValue(metricMap, axis.metrics, avgAll)
            );
            const passRate = result.metrics.length
                ? result.metrics.filter((metric) => metric.passed).length / result.metrics.length
                : 0;
            const failedMetrics = result.metrics.filter((metric) => !metric.passed).map((m) => m.name);

            const x = axisValues[0] ?? avgAll;
            const y = axisValues[1] ?? avgAll;
            let quadrant: string | null = null;
            if (typeof x === "number" && typeof y === "number") {
                if (x >= CHART_THRESHOLD && y >= CHART_THRESHOLD) quadrant = "우상단";
                else if (x < CHART_THRESHOLD && y >= CHART_THRESHOLD) quadrant = "좌상단";
                else if (x >= CHART_THRESHOLD && y < CHART_THRESHOLD) quadrant = "우하단";
                else quadrant = "좌하단";
            }

            return {
                id: result.test_case_id,
                question: result.question,
                answer: result.answer,
                x,
                y,
                z: axisValues[2] ?? avgAll,
                avg: avgAll,
                passRate,
                failedMetrics,
                clusterId: clusterMap.get(result.test_case_id),
                quadrant,
                metrics: result.metrics,
            };
        });
    }, [data, clusterMap, axisSpecs]);

    const filteredPoints = useMemo(() => {
        if (clusterFilter.size === 0) {
            return points;
        }
        return points.filter(
            (point) => point.clusterId && clusterFilter.has(point.clusterId)
        );
    }, [points, clusterFilter]);

    useEffect(() => {
        if (!selectedPoint) {
            return;
        }
        if (
            clusterFilter.size > 0 &&
            !filteredPoints.some((point) => point.id === selectedPoint.id)
        ) {
            setSelectedPoint(null);
        }
    }, [clusterFilter, filteredPoints, selectedPoint]);

    const clusterPalette = useMemo(() => {
        const palette = new Map<string, string>();
        const clusters = Array.from(
            new Set(points.map((point) => point.clusterId).filter(Boolean))
        ) as string[];
        clusters.forEach((clusterId, index) => {
            palette.set(clusterId, CHART_METRIC_COLORS[index % CHART_METRIC_COLORS.length]);
        });
        return palette;
    }, [points]);

    const quadrantHints = useMemo(
        () =>
            createQuadrantHints(
                axisSpecs[0]?.label ?? "X",
                axisSpecs[1]?.label ?? "Y"
            ),
        [axisSpecs]
    );

    const clusterSummary = useMemo(() => {
        const counts = new Map<string, number>();
        points.forEach((point) => {
            if (!point.clusterId) {
                return;
            }
            counts.set(point.clusterId, (counts.get(point.clusterId) ?? 0) + 1);
        });
        return Array.from(counts.entries())
            .map(([clusterId, count]) => ({
                clusterId,
                count,
                color: clusterPalette.get(clusterId) ?? toScoreColor(0.5),
            }))
            .sort((a, b) => b.count - a.count);
    }, [points, clusterPalette]);

    const summary = data?.summary;
    const clusterCount = clusterPalette.size;
    const hasClusters = clusterMap.size > 0;
    const clusterCoverage = summary?.total_test_cases
        ? clusterMap.size / summary.total_test_cases
        : 0;

    const refreshRunClusterMaps = async (runId: string) => {
        setRunClusterMapsLoading(true);
        setRunClusterMapsError(null);
        try {
            const maps = await fetchRunClusterMaps(runId);
            setRunClusterMaps(maps);
            return maps;
        } catch (err) {
            setRunClusterMapsError(
                err instanceof Error ? err.message : "클러스터 맵 버전을 불러오지 못했습니다."
            );
            return null;
        } finally {
            setRunClusterMapsLoading(false);
        }
    };

    const persistClusterMap = async (map: Map<string, string>, source: string | null) => {
        if (!summary?.run_id || map.size === 0) {
            return;
        }
        try {
            const response = await saveRunClusterMap(summary.run_id, {
                source,
                items: Array.from(map, ([test_case_id, cluster_id]) => ({
                    test_case_id,
                    cluster_id,
                })),
            });
            setActiveMapId(response.map_id ?? null);
            setActiveMapCreatedAt(response.created_at ?? null);
            setClusterSourceLabel(response.source ?? source ?? null);
            await refreshRunClusterMaps(summary.run_id);
        } catch (err) {
            setClusterError(
                err instanceof Error
                    ? `서버 저장 실패: ${err.message}`
                    : "서버 저장에 실패했습니다."
            );
        }
    };

    const clearClusterMap = () => {
        setClusterMap(new Map());
        setColorMode("score");
        setClusterSource("manual");
        setClusterSourceLabel(null);
        setActiveMapId(null);
        setActiveMapCreatedAt(null);
        setClusterFilter(new Set());
    };

    const applyClusterMapVersion = async (mapId: string) => {
        if (!summary?.run_id) {
            return;
        }
        setClusterError(null);
        try {
            const response = await fetchRunClusterMapById(summary.run_id, mapId);
            if (!response.items.length) {
                setClusterError("선택한 클러스터 맵에 유효한 항목이 없습니다.");
                return;
            }
            const map = new Map(
                response.items.map((item) => [item.test_case_id, item.cluster_id])
            );
            setClusterMap(map);
            setClusterFilter(new Set());
            setColorMode("cluster");
            setClusterSource(response.source?.startsWith("auto") ? "auto" : "manual");
            setClusterSourceLabel(response.source ?? null);
            setActiveMapId(response.map_id ?? mapId);
            setActiveMapCreatedAt(response.created_at ?? null);
        } catch (err) {
            setClusterError(
                err instanceof Error ? err.message : "클러스터 맵을 불러오지 못했습니다."
            );
        }
    };

    const handleDeleteClusterMap = async (mapId: string) => {
        if (!summary?.run_id) {
            return;
        }
        if (!window.confirm("선택한 클러스터 맵을 삭제할까요?")) {
            return;
        }
        setClusterError(null);
        try {
            await deleteRunClusterMap(summary.run_id, mapId);
            const maps = await refreshRunClusterMaps(summary.run_id);
            if (activeMapId === mapId) {
                if (maps && maps.length > 0) {
                    await applyClusterMapVersion(maps[0].map_id);
                } else {
                    clearClusterMap();
                }
            }
        } catch (err) {
            setClusterError(
                err instanceof Error ? err.message : "클러스터 맵 삭제에 실패했습니다."
            );
        }
    };

    const handleExportClusterMap = () => {
        if (!summary || clusterMap.size === 0) {
            return;
        }
        const rows = ["test_case_id,cluster_id"];
        clusterMap.forEach((clusterId, testCaseId) => {
            rows.push(`${testCaseId},${clusterId}`);
        });
        const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `cluster_map_${summary.run_id.slice(0, 8)}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const handleClusterUpload = async (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;
        setClusterError(null);
        try {
            const text = await file.text();
            const map = parseClusterMap(text);
            if (!map.size) {
                setClusterError("유효한 클러스터 맵을 찾지 못했습니다.");
                return;
            }
            setClusterMap(map);
            setClusterFilter(new Set());
            setColorMode("cluster");
            setClusterSource("upload");
            setClusterSourceLabel(file.name);
            setSelectedClusterFile("");
            setActiveMapId(null);
            setActiveMapCreatedAt(null);
            await persistClusterMap(map, file.name);
        } catch (err) {
            setClusterError(err instanceof Error ? err.message : "파일을 읽는 데 실패했습니다.");
        }
    };

    const handleClusterFileSelect = async (event: ChangeEvent<HTMLSelectElement>) => {
        const fileName = event.target.value;
        setSelectedClusterFile(fileName);
        setClusterError(null);

        if (!fileName) {
            clearClusterMap();
            return;
        }

        setClusterMap(new Map());
        setColorMode("score");
        setClusterSource("manual");
        setClusterSourceLabel(null);
        setActiveMapId(null);
        setActiveMapCreatedAt(null);

        try {
            const response = await fetchClusterMapFile(fileName);
            if (!response.items.length) {
                setClusterError("선택한 클러스터 맵에 유효한 항목이 없습니다.");
                return;
            }
            const map = new Map(
                response.items.map((item) => [item.test_case_id, item.cluster_id])
            );
            setClusterMap(map);
            setClusterFilter(new Set());
            setColorMode("cluster");
            setClusterSource("manual");
            setClusterSourceLabel(response.source ?? fileName);
            await persistClusterMap(map, response.source ?? fileName);
        } catch (err) {
            setClusterError(err instanceof Error ? err.message : "클러스터 맵을 불러오지 못했습니다.");
        }
    };

    const toggleDetail = (key: string) => {
        setActiveDetail((current) => (current === key ? null : key));
    };

    const toggleClusterFilter = (clusterId: string) => {
        setClusterFilter((current) => {
            const next = new Set(current);
            if (next.has(clusterId)) {
                next.delete(clusterId);
            } else {
                next.add(clusterId);
            }
            return next;
        });
    };

    const clearClusterFilter = () => {
        setClusterFilter(new Set());
    };

    if (loading) {
        return (
            <Layout>
                <div className="flex items-center justify-center h-[50vh] text-muted-foreground">
                    시각화 데이터를 불러오는 중...
                </div>
            </Layout>
        );
    }

    if (error || !data || !summary) {
        return (
            <Layout>
                <div className="flex flex-col items-center justify-center h-[50vh] text-destructive gap-4">
                    <p className="text-xl font-bold">시각화 로딩 실패</p>
                    <p>{error || "데이터를 찾을 수 없습니다."}</p>
                    <Link to="/" className="text-primary hover:underline">
                        대시보드로 돌아가기
                    </Link>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="pb-16 space-y-6">
                <div className="flex flex-wrap items-start gap-4">
                    <Link
                        to={`/runs/${summary.run_id}`}
                        className="p-2 hover:bg-secondary rounded-lg transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5 text-muted-foreground" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight font-display">
                            {summary.dataset_name} 시각화
                        </h1>
                        <p className="text-sm text-muted-foreground mt-1 flex flex-wrap items-center gap-2">
                            <span className="font-mono bg-secondary px-1.5 py-0.5 rounded text-xs">
                                {summary.run_id.slice(0, 8)}
                            </span>
                            <span>•</span>
                            <span>{summary.model_name}</span>
                            <span>•</span>
                            <span>{summary.total_test_cases} cases</span>
                        </p>
                    </div>
                    <div className="ml-auto flex flex-wrap items-center gap-3">
                        <div className="tab-shell">
                            <button
                                type="button"
                                className={`tab-pill ${viewMode === "2d" ? "tab-pill-active" : "tab-pill-inactive"}`}
                                onClick={() => setViewMode("2d")}
                            >
                                2D
                            </button>
                            <button
                                type="button"
                                className={`tab-pill ${viewMode === "3d" ? "tab-pill-active" : "tab-pill-inactive"}`}
                                onClick={() => setViewMode("3d")}
                            >
                                3D
                            </button>
                        </div>
                        <div className="tab-shell">
                            <button
                                type="button"
                                className={`tab-pill ${colorMode === "score" ? "tab-pill-active" : "tab-pill-inactive"}`}
                                onClick={() => setColorMode("score")}
                            >
                                점수 색상
                            </button>
                            <button
                                type="button"
                                className={`tab-pill ${colorMode === "cluster" ? "tab-pill-active" : "tab-pill-inactive"}`}
                                onClick={() => setColorMode("cluster")}
                                disabled={!hasClusters}
                            >
                                클러스터 색상
                            </button>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-muted-foreground">
                                클러스터 맵
                            </span>
                            <select
                                value={selectedClusterFile}
                                onChange={handleClusterFileSelect}
                                disabled={clusterFilesLoading || clusterFiles.length === 0}
                                className="px-3 py-2 rounded-lg border border-border bg-background text-xs text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-60"
                            >
                                <option value="">
                                    {clusterFilesLoading
                                        ? "불러오는 중..."
                                        : clusterFiles.length
                                            ? "목록에서 선택"
                                            : "목록 없음"}
                                </option>
                                {clusterFiles.map((file) => (
                                    <option key={file.name} value={file.name}>
                                        {file.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <label className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-background text-xs font-semibold text-muted-foreground cursor-pointer hover:text-foreground hover:border-primary/40">
                            <UploadCloud className="w-4 h-4" />
                            클러스터 맵 업로드
                            <input
                                type="file"
                                accept=".csv"
                                className="hidden"
                                onChange={handleClusterUpload}
                            />
                        </label>
                        {hasClusters && (
                            <button
                                type="button"
                                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-secondary/40 text-xs font-semibold text-muted-foreground hover:text-foreground"
                                onClick={() => {
                                    clearClusterMap();
                                    setSelectedClusterFile("");
                                }}
                            >
                                <XCircle className="w-4 h-4" />
                                클러스터 해제
                            </button>
                        )}
                    </div>
                </div>

                {clusterError && (
                    <div className="text-sm text-rose-600 bg-rose-500/10 border border-rose-500/20 rounded-lg px-4 py-2">
                        {clusterError}
                    </div>
                )}
                {clusterFilesError && (
                    <div className="text-xs text-amber-600 bg-amber-500/10 border border-amber-500/20 rounded-lg px-4 py-2">
                        클러스터 맵 목록을 불러오지 못했습니다: {clusterFilesError}
                    </div>
                )}
                {runClusterMapsError && (
                    <div className="text-xs text-amber-600 bg-amber-500/10 border border-amber-500/20 rounded-lg px-4 py-2">
                        클러스터 맵 버전을 불러오지 못했습니다: {runClusterMapsError}
                    </div>
                )}
                {metricSpecError && (
                    <div className="text-xs text-amber-600 bg-amber-500/10 border border-amber-500/20 rounded-lg px-4 py-2">
                        메트릭 스펙을 불러오지 못했습니다: {metricSpecError}
                    </div>
                )}
                {hasClusters && (
                    <div className="text-xs text-muted-foreground">
                        {clusterSource === "auto"
                            ? "자동 생성된 클러스터 맵 적용 중"
                            : clusterSource === "upload"
                                ? "업로드된 클러스터 맵 적용 중"
                                : "선택한 클러스터 맵 적용 중"}
                        {clusterSourceLabel ? `: ${clusterSourceLabel}` : ""}
                        {activeMapCreatedAt
                            ? ` · ${new Date(activeMapCreatedAt).toLocaleString()}`
                            : ""}
                        .
                    </div>
                )}
                {!hasClusters && clusterSource === "manual" && (
                    <div className="text-xs text-muted-foreground">
                        클러스터 맵이 없어 점수 색상만 사용 중입니다. 목록 선택 또는 CSV 업로드 시 클러스터 색상으로 전환됩니다.
                    </div>
                )}

                <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
                    <div className="xl:col-span-3 space-y-6">
                        <div className="surface-panel p-5">
                            <div className="flex items-center justify-between mb-4">
                                <div>
                                    <h3 className="text-base font-semibold">공간 분포</h3>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        점 위치는 지표 평균을 정규화하여 표시합니다.
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        축은 실행된 지표의 신호 그룹 기준으로 자동 구성됩니다.
                                    </p>
                                </div>
                                <div className="text-xs text-muted-foreground">
                                    기준선: {CHART_THRESHOLD.toFixed(2)}
                                </div>
                            </div>
                            {viewMode === "3d" && (
                                <div className="mb-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                                    {axisSpecs.map((axis) => (
                                        <span
                                            key={axis.key}
                                            className="px-2 py-1 rounded-full border border-border bg-background/70"
                                        >
                                            {axis.key.toUpperCase()} = {axis.label}
                                        </span>
                                    ))}
                                </div>
                            )}
                            <div className="h-[520px] w-full">
                                {points.length === 0 ? (
                                    <div className="flex items-center justify-center h-full text-muted-foreground">
                                        표시할 데이터가 없습니다.
                                    </div>
                                ) : filteredPoints.length === 0 ? (
                                    <div className="flex items-center justify-center h-full text-muted-foreground">
                                        필터 조건에 맞는 포인트가 없습니다.
                                    </div>
                                ) : viewMode === "2d" ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.3)" />
                                            <XAxis
                                                type="number"
                                                dataKey="x"
                                                domain={[0, 1]}
                                                tickFormatter={(value) => formatScore(value)}
                                                label={{ value: axisSpecs[0].label, position: "insideBottom", offset: -5 }}
                                            />
                                            <YAxis
                                                type="number"
                                                dataKey="y"
                                                domain={[0, 1]}
                                                tickFormatter={(value) => formatScore(value)}
                                                label={{ value: axisSpecs[1].label, angle: -90, position: "insideLeft" }}
                                            />
                                            <ZAxis dataKey="avg" range={[80, 360]} />
                                            <ReferenceLine x={CHART_THRESHOLD} stroke="rgba(148,163,184,0.6)" />
                                            <ReferenceLine y={CHART_THRESHOLD} stroke="rgba(148,163,184,0.6)" />
                                            <Tooltip
                                                cursor={{ strokeDasharray: "3 3" }}
                                                content={({ active, payload }) => {
                                                    if (!active || !payload?.length) return null;
                                                    const point = payload[0].payload as ScatterPoint;
                                                    return (
                                                        <div className="bg-background border border-border rounded-lg px-3 py-2 text-xs shadow-md max-w-xs">
                                                            <p className="font-semibold text-foreground">{point.id}</p>
                                                            <p className="text-muted-foreground line-clamp-2 mt-1">
                                                                {point.question}
                                                            </p>
                                                            <div className="mt-2 space-y-1 text-muted-foreground">
                                                                <p>
                                                                    {axisSpecs[0].label}: {formatScore(point.x)}
                                                                    {" • "}
                                                                    {axisSpecs[1].label}: {formatScore(point.y)}
                                                                </p>
                                                                <p>
                                                                    평균 {formatScore(point.avg)} · 통과율{" "}
                                                                    {(point.passRate * 100).toFixed(0)}%
                                                                </p>
                                                                {point.quadrant && <p>사분면: {point.quadrant}</p>}
                                                                {point.clusterId && <p>클러스터 {point.clusterId}</p>}
                                                            </div>
                                                        </div>
                                                    );
                                                }}
                                            />
                                            <Scatter
                                                data={filteredPoints}
                                                onClick={(event) => {
                                                    if (event?.payload) {
                                                        setSelectedPoint(event.payload as ScatterPoint);
                                                    }
                                                }}
                                            >
                                                {filteredPoints.map((point) => {
                                                    let color = toScoreColor(point.avg);
                                                    if (colorMode === "cluster" && point.clusterId) {
                                                        color =
                                                            clusterPalette.get(point.clusterId) ??
                                                            toScoreColor(point.avg);
                                                    }
                                                    return <Cell key={point.id} fill={color} />;
                                                })}
                                            </Scatter>
                                        </ScatterChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <VisualizationPlot
                                        points={filteredPoints}
                                        axisSpecs={axisSpecs}
                                        colorMode={colorMode}
                                        clusterPalette={clusterPalette}
                                        onSelect={setSelectedPoint}
                                    />
                                )}
                            </div>
                        </div>

                        <div className="surface-panel p-5">
                            <h3 className="text-base font-semibold mb-3">축 정의 & 사분면 해석</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {axisSpecs.map((axis) => {
                                    const detailKey = `axis-${axis.key}`;
                                    return (
                                        <div
                                            key={axis.key}
                                            className="relative border border-border rounded-lg p-4 bg-background/40"
                                        >
                                            <div className="flex items-start justify-between gap-3">
                                                <p className="text-sm font-semibold text-foreground">
                                                    {axis.label}
                                                </p>
                                                <button
                                                    type="button"
                                                    className="inline-flex items-center gap-1 text-xs font-semibold text-muted-foreground hover:text-foreground"
                                                    onClick={() => toggleDetail(detailKey)}
                                                >
                                                    <Info className="w-3.5 h-3.5" />
                                                    자세히
                                                </button>
                                            </div>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {axis.description}
                                            </p>
                                            <p className="text-xs text-muted-foreground mt-2">
                                                {axis.metrics.length
                                                    ? axis.metrics.join(", ")
                                                    : "사용 가능한 지표 없음"}
                                            </p>
                                            {activeDetail === detailKey && (
                                                <div className="absolute left-0 top-full mt-2 w-72 rounded-lg border border-border bg-background p-3 shadow-lg z-20">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <p className="text-xs font-semibold text-foreground">
                                                            {axis.label} 상세
                                                        </p>
                                                        <button
                                                            type="button"
                                                            className="text-muted-foreground hover:text-foreground"
                                                            onClick={() => setActiveDetail(null)}
                                                        >
                                                            <X className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                    <div className="space-y-2 text-xs text-muted-foreground">
                                                        <p>
                                                            <span className="font-semibold text-foreground">
                                                                계산
                                                            </span>{" "}
                                                            {axis.detail.calc}
                                                        </p>
                                                        <p>
                                                            <span className="font-semibold text-foreground">
                                                                의미
                                                            </span>{" "}
                                                            {axis.detail.meaning}
                                                        </p>
                                                        <p>
                                                            <span className="font-semibold text-foreground">
                                                                효과
                                                            </span>{" "}
                                                            {axis.detail.effect}
                                                        </p>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-muted-foreground">
                                {quadrantHints.map((hint) => {
                                    const detailKey = `quad-${hint.id}`;
                                    return (
                                        <div
                                            key={hint.id}
                                            className="relative border border-border rounded-lg px-3 py-2 bg-background/40"
                                        >
                                            <div className="flex items-start justify-between gap-2">
                                                <div className="flex items-start gap-2">
                                                    <span className="font-semibold text-foreground">
                                                        {hint.label}
                                                    </span>
                                                    <span>{hint.desc}</span>
                                                </div>
                                                <button
                                                    type="button"
                                                    className="inline-flex items-center gap-1 text-xs font-semibold text-muted-foreground hover:text-foreground"
                                                    onClick={() => toggleDetail(detailKey)}
                                                >
                                                    <Info className="w-3.5 h-3.5" />
                                                    상세
                                                </button>
                                            </div>
                                            {activeDetail === detailKey && (
                                                <div className="absolute left-0 top-full mt-2 w-72 rounded-lg border border-border bg-background p-3 shadow-lg z-20">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <p className="text-xs font-semibold text-foreground">
                                                            {hint.label} 해석
                                                        </p>
                                                        <button
                                                            type="button"
                                                            className="text-muted-foreground hover:text-foreground"
                                                            onClick={() => setActiveDetail(null)}
                                                        >
                                                            <X className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                    <div className="space-y-2 text-xs text-muted-foreground">
                                                        <p>
                                                            <span className="font-semibold text-foreground">
                                                                계산
                                                            </span>{" "}
                                                            {hint.detail.calc}
                                                        </p>
                                                        <p>
                                                            <span className="font-semibold text-foreground">
                                                                의미
                                                            </span>{" "}
                                                            {hint.detail.meaning}
                                                        </p>
                                                        <p>
                                                            <span className="font-semibold text-foreground">
                                                                효과
                                                            </span>{" "}
                                                            {hint.detail.effect}
                                                        </p>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div className="surface-panel p-5">
                            <h3 className="text-base font-semibold mb-3">선택한 포인트</h3>
                            {selectedPoint ? (
                                <div className="space-y-3 text-sm">
                                    <div>
                                        <p className="text-xs text-muted-foreground">Test Case</p>
                                        <p className="font-semibold text-foreground">{selectedPoint.id}</p>
                                        {selectedPoint.quadrant && (
                                            <p className="text-xs text-muted-foreground mt-1">
                                                사분면: {selectedPoint.quadrant}
                                            </p>
                                        )}
                                        {selectedPoint.clusterId && (
                                            <p className="text-xs text-muted-foreground mt-1">
                                                클러스터 {selectedPoint.clusterId}
                                            </p>
                                        )}
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground">Question</p>
                                        <p className="text-sm text-foreground mt-1">
                                            {selectedPoint.question}
                                        </p>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                                        <div className="rounded-md border border-border p-2">
                                            {axisSpecs[0].label}: {formatScore(selectedPoint.x)}
                                        </div>
                                        <div className="rounded-md border border-border p-2">
                                            {axisSpecs[1].label}: {formatScore(selectedPoint.y)}
                                        </div>
                                        <div className="rounded-md border border-border p-2">
                                            {axisSpecs[2].label}: {formatScore(selectedPoint.z)}
                                        </div>
                                        <div className="rounded-md border border-border p-2">
                                            평균: {formatScore(selectedPoint.avg)}
                                        </div>
                                    </div>
                                    {selectedPoint.failedMetrics.length > 0 && (
                                        <div className="text-xs text-rose-600 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
                                            실패 지표: {selectedPoint.failedMetrics.join(", ")}
                                        </div>
                                    )}
                                    <Link
                                        to={`/runs/${summary.run_id}#case-${encodeURIComponent(selectedPoint.id)}`}
                                        className="inline-flex items-center gap-2 text-xs font-semibold text-primary hover:underline"
                                    >
                                        상세 케이스 열기
                                    </Link>
                                </div>
                            ) : (
                                <p className="text-sm text-muted-foreground">
                                    포인트를 클릭하면 상세 정보를 볼 수 있습니다.
                                </p>
                            )}
                        </div>

                        <div className="surface-panel p-5">
                            <h3 className="text-base font-semibold mb-3">인코딩 규칙</h3>
                            <div className="space-y-2 text-xs text-muted-foreground">
                                <p>위치: 축 정의에 따른 평균 점수</p>
                                <p>크기: 전체 평균 점수 (높을수록 큼)</p>
                                <p>
                                    색상:{" "}
                                    {colorMode === "cluster"
                                        ? "클러스터 그룹"
                                        : "평균 점수(녹색=높음, 적색=낮음)"}
                                </p>
                                <p>클러스터 수: {clusterCount || 0}</p>
                                <p>클러스터 커버리지: {(clusterCoverage * 100).toFixed(0)}%</p>
                            </div>
                        </div>

                        <div className="surface-panel p-5">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-base font-semibold">클러스터 요약</h3>
                                {clusterFilter.size > 0 && (
                                    <button
                                        type="button"
                                        className="text-xs font-semibold text-muted-foreground hover:text-foreground"
                                        onClick={clearClusterFilter}
                                    >
                                        필터 해제
                                    </button>
                                )}
                            </div>
                            {!hasClusters && (
                                <p className="text-xs text-muted-foreground">
                                    클러스터 맵이 아직 적용되지 않았습니다.
                                </p>
                            )}
                            {hasClusters && clusterSummary.length === 0 && (
                                <p className="text-xs text-muted-foreground">
                                    표시할 클러스터가 없습니다.
                                </p>
                            )}
                            {hasClusters && clusterSummary.length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                    {clusterSummary.map((cluster) => {
                                        const isActive = clusterFilter.has(cluster.clusterId);
                                        return (
                                            <button
                                                key={cluster.clusterId}
                                                type="button"
                                                onClick={() => toggleClusterFilter(cluster.clusterId)}
                                                className={`filter-chip ${isActive || clusterFilter.size === 0
                                                    ? "filter-chip-active"
                                                    : "filter-chip-inactive"
                                                    }`}
                                            >
                                                <span
                                                    className="inline-block w-2 h-2 rounded-full mr-1"
                                                    style={{ backgroundColor: cluster.color }}
                                                />
                                                {cluster.clusterId} ({cluster.count})
                                            </button>
                                        );
                                    })}
                                </div>
                            )}
                            {clusterFilter.size > 0 && (
                                <p className="mt-3 text-xs text-muted-foreground">
                                    선택한 클러스터만 표시 중입니다.
                                </p>
                            )}
                        </div>

                        <div className="surface-panel p-5">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-base font-semibold">클러스터 맵 버전</h3>
                                {hasClusters && (
                                    <button
                                        type="button"
                                        className="text-xs font-semibold text-muted-foreground hover:text-foreground"
                                        onClick={handleExportClusterMap}
                                    >
                                        CSV 내보내기
                                    </button>
                                )}
                            </div>
                            {runClusterMapsLoading && (
                                <p className="text-xs text-muted-foreground">불러오는 중...</p>
                            )}
                            {!runClusterMapsLoading && runClusterMaps.length === 0 && (
                                <p className="text-xs text-muted-foreground">
                                    저장된 클러스터 맵이 없습니다.
                                </p>
                            )}
                            {!runClusterMapsLoading && runClusterMaps.length > 0 && (
                                <div className="space-y-2 text-xs">
                                    {runClusterMaps.map((map) => {
                                        const isActive = activeMapId === map.map_id;
                                        return (
                                            <div
                                                key={map.map_id}
                                                className={`flex items-center justify-between gap-2 rounded-lg border px-3 py-2 ${isActive
                                                    ? "border-primary bg-primary/5"
                                                    : "border-border bg-background/40"
                                                    }`}
                                            >
                                                <div>
                                                    <p className="font-semibold text-foreground">
                                                        {map.source || map.map_id.slice(0, 8)}
                                                    </p>
                                                    <p className="text-muted-foreground">
                                                        {map.item_count}개 ·{" "}
                                                        {map.created_at
                                                            ? new Date(map.created_at).toLocaleString()
                                                            : "시간 정보 없음"}
                                                    </p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        type="button"
                                                        className="text-xs font-semibold text-primary hover:underline"
                                                        onClick={() => applyClusterMapVersion(map.map_id)}
                                                    >
                                                        적용
                                                    </button>
                                                    <button
                                                        type="button"
                                                        className="text-xs font-semibold text-rose-600 hover:underline"
                                                        onClick={() => handleDeleteClusterMap(map.map_id)}
                                                    >
                                                        삭제
                                                    </button>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    );
}
