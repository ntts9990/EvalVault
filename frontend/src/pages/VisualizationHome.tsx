import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AlertCircle, ExternalLink, Search, Sparkles } from "lucide-react";
import { Layout } from "../components/Layout";
import { fetchRuns, type RunSummary } from "../services/api";
import { PASS_RATE_COLOR_BANDS } from "../config/ui";

const PROJECT_ALL = "__all__";
const PROJECT_UNASSIGNED = "__unassigned__";
const METRIC_ALL = "__metric_all__";

function getPassRateStyle(rate: number) {
    const band = PASS_RATE_COLOR_BANDS.find((item) => rate >= item.min);
    return band?.className ?? "text-muted-foreground bg-secondary/40 border-border";
}

function projectLabel(project: string) {
    if (project === PROJECT_ALL) return "전체";
    if (project === PROJECT_UNASSIGNED) return "미지정";
    return project;
}

export function VisualizationHome() {
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedProject, setSelectedProject] = useState(PROJECT_ALL);
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);

    useEffect(() => {
        async function loadRuns() {
            try {
                const data = await fetchRuns();
                setRuns(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load runs");
            } finally {
                setLoading(false);
            }
        }
        loadRuns();
    }, []);

    const projectOptions = useMemo(() => {
        const names = new Set<string>();
        runs.forEach((run) => {
            if (run.project_name) {
                names.add(run.project_name);
            }
        });
        return Array.from(names).sort((a, b) => a.localeCompare(b));
    }, [runs]);

    const hasUnassignedProject = useMemo(
        () => runs.some((run) => !run.project_name),
        [runs]
    );

    const metricOptions = useMemo(() => {
        const names = new Set<string>();
        runs.forEach((run) => {
            run.metrics_evaluated?.forEach((metric) => names.add(metric));
        });
        return Array.from(names).sort((a, b) => a.localeCompare(b));
    }, [runs]);

    const filteredRuns = useMemo(() => {
        const trimmed = searchQuery.trim().toLowerCase();
        return runs.filter((run) => {
            const projectName = run.project_name ?? "";
            const matchesSearch =
                !trimmed ||
                run.dataset_name.toLowerCase().includes(trimmed) ||
                run.model_name.toLowerCase().includes(trimmed) ||
                run.run_id.toLowerCase().includes(trimmed) ||
                projectName.toLowerCase().includes(trimmed);
            const matchesProject =
                selectedProject === PROJECT_ALL ||
                (selectedProject === PROJECT_UNASSIGNED && !run.project_name) ||
                run.project_name === selectedProject;
            const metrics = run.metrics_evaluated ?? [];
            const matchesMetrics =
                selectedMetrics.length === 0 ||
                selectedMetrics.every((metric) => metrics.includes(metric));
            return matchesSearch && matchesProject && matchesMetrics;
        });
    }, [runs, searchQuery, selectedProject, selectedMetrics]);

    const latestRun = filteredRuns[0];

    const toggleMetricSelection = (metric: string) => {
        if (metric === METRIC_ALL) {
            setSelectedMetrics([]);
            return;
        }
        setSelectedMetrics((prev) =>
            prev.includes(metric) ? prev.filter((item) => item !== metric) : [...prev, metric]
        );
    };

    return (
        <Layout>
            <div className="pb-20 space-y-6">
                <div className="flex flex-wrap items-center gap-4">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight font-display">시각화</h1>
                        <p className="text-sm text-muted-foreground mt-1">
                            실행 결과를 2D/3D 공간에서 빠르게 탐색합니다.
                        </p>
                    </div>
                    {latestRun && (
                        <Link
                            to={`/visualization/${latestRun.run_id}`}
                            className="ml-auto inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-colors"
                        >
                            <Sparkles className="w-4 h-4" />
                            최신 Run 바로 보기
                        </Link>
                    )}
                </div>

                <div className="surface-panel p-5">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <h3 className="text-base font-semibold">Run 선택</h3>
                            <p className="text-xs text-muted-foreground mt-1">
                                시각화할 평가 Run을 선택하세요.
                            </p>
                        </div>
                        <div className="flex items-center gap-2 border border-border rounded-lg px-3 py-2 bg-background/70">
                            <Search className="w-4 h-4 text-muted-foreground" />
                            <input
                                value={searchQuery}
                                onChange={(event) => setSearchQuery(event.target.value)}
                                placeholder="Dataset / Model / Project / Run ID 검색"
                                className="bg-transparent text-sm outline-none w-60"
                            />
                        </div>
                    </div>

                    <div className="mt-4 grid grid-cols-1 lg:grid-cols-3 gap-4">
                        <div className="space-y-2">
                            <p className="text-xs font-semibold text-muted-foreground uppercase">
                                Project
                            </p>
                            <div className="flex flex-wrap gap-2">
                                {[PROJECT_ALL, ...(hasUnassignedProject ? [PROJECT_UNASSIGNED] : []), ...projectOptions].map(
                                    (project) => {
                                        const isSelected = selectedProject === project;
                                        return (
                                            <button
                                                key={project}
                                                type="button"
                                                onClick={() => setSelectedProject(project)}
                                                className={`filter-chip ${isSelected
                                                    ? "filter-chip-active"
                                                    : "filter-chip-inactive"
                                                    }`}
                                            >
                                                {projectLabel(project)}
                                            </button>
                                        );
                                    }
                                )}
                            </div>
                        </div>
                        <div className="space-y-2 lg:col-span-2">
                            <div className="flex items-center justify-between gap-3">
                                <p className="text-xs font-semibold text-muted-foreground uppercase">
                                    Metrics
                                </p>
                                {selectedMetrics.length > 0 && (
                                    <button
                                        type="button"
                                        className="text-xs font-semibold text-muted-foreground hover:text-foreground"
                                        onClick={() => setSelectedMetrics([])}
                                    >
                                        초기화
                                    </button>
                                )}
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {[METRIC_ALL, ...metricOptions].map((metric) => {
                                    const isSelected =
                                        metric === METRIC_ALL
                                            ? selectedMetrics.length === 0
                                            : selectedMetrics.includes(metric);
                                    return (
                                        <button
                                            key={metric}
                                            type="button"
                                            onClick={() => toggleMetricSelection(metric)}
                                            className={`filter-chip ${isSelected
                                                ? "filter-chip-active"
                                                : "filter-chip-inactive"
                                                }`}
                                        >
                                            {metric === METRIC_ALL ? "전체" : metric}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    </div>

                    {loading && (
                        <div className="mt-8 text-sm text-muted-foreground">불러오는 중...</div>
                    )}
                    {error && (
                        <div className="mt-8 flex items-center gap-2 text-sm text-rose-600">
                            <AlertCircle className="w-4 h-4" />
                            {error}
                        </div>
                    )}
                    {!loading && !error && filteredRuns.length === 0 && (
                        <div className="mt-8 text-sm text-muted-foreground">
                            조건에 맞는 Run이 없습니다.
                        </div>
                    )}
                    <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {filteredRuns.map((run) => (
                            <div
                                key={run.run_id}
                                className="border border-border rounded-xl p-4 bg-background/60 flex flex-col gap-3"
                            >
                                <div>
                                    <p className="text-sm font-semibold text-foreground">
                                        {run.dataset_name}
                                    </p>
                                    <p className="text-xs text-muted-foreground mt-1 flex flex-wrap items-center gap-2">
                                        <span className="font-mono bg-secondary px-1.5 py-0.5 rounded">
                                            {run.run_id.slice(0, 8)}
                                        </span>
                                        <span>•</span>
                                        <span>{run.model_name}</span>
                                        <span>•</span>
                                        <span>{run.total_test_cases} cases</span>
                                    </p>
                                </div>
                                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                    <span
                                        className={`px-2 py-1 rounded-full border ${getPassRateStyle(
                                            run.pass_rate
                                        )}`}
                                    >
                                        Pass {Math.round(run.pass_rate * 100)}%
                                    </span>
                                    <span>
                                        {run.passed_test_cases}/{run.total_test_cases} 통과
                                    </span>
                                    {run.finished_at && (
                                        <span>
                                            {new Date(run.finished_at).toLocaleString()}
                                        </span>
                                    )}
                                </div>
                                <div className="flex gap-2">
                                    <Link
                                        to={`/visualization/${run.run_id}`}
                                        className="inline-flex items-center justify-center px-3 py-2 rounded-md bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90"
                                    >
                                        시각화 열기
                                    </Link>
                                    <Link
                                        to={`/visualization/${run.run_id}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center justify-center gap-1 px-3 py-2 rounded-md border border-border text-xs font-semibold text-muted-foreground hover:text-foreground hover:border-primary/50"
                                    >
                                        <ExternalLink className="w-3.5 h-3.5" />
                                        새 창
                                    </Link>
                                    <Link
                                        to={`/runs/${run.run_id}`}
                                        className="inline-flex items-center justify-center px-3 py-2 rounded-md border border-border text-xs font-semibold text-muted-foreground hover:text-foreground hover:border-primary/50"
                                    >
                                        Run 상세
                                    </Link>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </Layout>
    );
}
