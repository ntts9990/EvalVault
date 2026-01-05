import { useEffect, useState } from "react";
import { fetchRuns, type RunSummary } from "../services/api";
import {
    Activity,
    AlertCircle,
    Clock,
    Database,
    Cpu,
    ArrowUpRight,
    Search
} from "lucide-react";
import { Layout } from "../components/Layout";
import { useNavigate } from "react-router-dom";

export function Dashboard() {
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const [selectedRuns, setSelectedRuns] = useState<Set<string>>(new Set());

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

    const toggleRunSelection = (runId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const newSet = new Set(selectedRuns);
        if (newSet.has(runId)) {
            newSet.delete(runId);
        } else {
            if (newSet.size >= 2) {
                // Determine which one to remove (FIFO or just block? Let's just block > 2 for now or shift)
                // Actually, let's just allow toggling. UX usually allows selecting more but we only compare 2.
                // For simplicity, let's max out at 2 effectively or show alert.
                // But better UX: allow multiple, but "Compare" button disabled if != 2.
                newSet.add(runId);
            } else {
                newSet.add(runId);
            }
        }
        setSelectedRuns(newSet);
    };

    const handleCompare = () => {
        if (selectedRuns.size !== 2) return;
        const [base, target] = Array.from(selectedRuns);
        // Ensure we have an order, maybe by date? Sort by started_at if possible.
        // For now just pass as is.
        navigate(`/compare?base=${base}&target=${target}`);
    };

    const getPassRateColor = (rate: number) => {
        if (rate >= 0.9) return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
        if (rate >= 0.7) return "text-blue-500 bg-blue-500/10 border-blue-500/20";
        if (rate >= 0.5) return "text-amber-500 bg-amber-500/10 border-amber-500/20";
        return "text-rose-500 bg-rose-500/10 border-rose-500/20";
    };

    if (loading) {
        return (
            <Layout>
                <div className="flex flex-col items-center justify-center h-[60vh] animate-in fade-in duration-500 gap-4">
                    <div className="relative">
                        <div className="w-12 h-12 rounded-xl bg-primary/20 animate-pulse"></div>
                        <Activity className="w-6 h-6 text-primary absolute top-3 left-3 animate-spin" />
                    </div>
                    <p className="text-muted-foreground font-medium animate-pulse">Loading workspace...</p>
                </div>
            </Layout>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-background text-foreground">
                <div className="flex flex-col items-center gap-4 text-destructive p-8 rounded-2xl bg-destructive/5 border border-destructive/20 max-w-md text-center">
                    <AlertCircle className="w-12 h-12" />
                    <div>
                        <p className="text-xl font-bold tracking-tight">System Error</p>
                        <p className="text-sm opacity-80 mt-1">{error}</p>
                    </div>
                    <button
                        onClick={() => window.location.reload()}
                        className="mt-4 px-4 py-2 bg-destructive text-destructive-foreground rounded-lg font-medium hover:opacity-90 transition-opacity"
                    >
                        Retry Connection
                    </button>
                </div>
            </div>
        );
    }

    return (
        <Layout>
            {/* Hero Section */}
            <div className="mb-10">
                <h1 className="text-3xl font-bold tracking-tight mb-2">Evaluation Overview</h1>
                <p className="text-muted-foreground flex items-center gap-2">
                    Manage and analyze your RAG system performance
                    <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium border border-primary/20">
                        {runs.length} runs active
                    </span>
                </p>

                {/* Quick Stats Row (Placeholder calculations) */}
                {!loading && runs.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                        <div className="p-5 rounded-2xl bg-card border border-border/50 shadow-sm">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground font-medium">Avg Pass Rate</p>
                                    <p className="text-2xl font-bold mt-1">
                                        {((runs.reduce((acc, r) => acc + r.pass_rate, 0) / runs.length) * 100).toFixed(1)}%
                                    </p>
                                </div>
                                <div className="p-2 bg-primary/10 rounded-lg text-primary">
                                    <Activity className="w-5 h-5" />
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Search and Filters Strip */}
            <div className="flex flex-col sm:flex-row gap-4 mb-6 sticky top-20 z-30 bg-background/50 backdrop-blur-xl p-2 -mx-2 rounded-xl border border-transparent">
                <div className="relative flex-1">
                    <Search className="w-4 h-4 absolute left-3 top-3 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Search runs by dataset or model..."
                        className="w-full pl-9 pr-4 py-2.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all shadow-sm"
                    />
                </div>
            </div>

            {/* Grid Layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pb-20">
                {runs.map((run) => {
                    const isSelected = selectedRuns.has(run.run_id);
                    return (
                        <div
                            key={run.run_id}
                            onClick={() => navigate(`/runs/${run.run_id}`)}
                            className={`group relative bg-card hover:bg-card/80 border rounded-2xl p-6 transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1 cursor-pointer overflow-hidden ${isSelected ? 'border-primary ring-1 ring-primary' : 'border-border/60 hover:border-primary/30'}`}
                        >
                            {/* Selection Checkbox (Floating) */}
                            <div
                                onClick={(e) => toggleRunSelection(run.run_id, e)}
                                className={`absolute top-4 right-4 z-10 w-6 h-6 rounded-md border flex items-center justify-center transition-all ${isSelected ? "bg-primary border-primary" : "bg-secondary/50 border-border hover:border-primary/50"}`}
                            >
                                {isSelected && <ArrowUpRight className="w-4 h-4 text-primary-foreground transform rotate-0" />}
                            </div>

                            {/* Top decorative gradient line */}
                            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                            <div className="flex items-start justify-between mb-5">
                                <div className="space-y-1.5">
                                    <div className="flex items-center gap-2">
                                        <Database className="w-3.5 h-3.5 text-muted-foreground" />
                                        <h3 className="font-semibold text-lg tracking-tight group-hover:text-primary transition-colors">
                                            {run.dataset_name}
                                        </h3>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                        <Cpu className="w-3.5 h-3.5" />
                                        <span className="font-mono text-xs">{run.model_name}</span>
                                    </div>
                                </div>

                                <div
                                    className={`flex flex-col items-center justify-center w-14 h-14 rounded-2xl border ${getPassRateColor(run.pass_rate)} shadow-sm transition-transform group-hover:scale-105`}
                                >
                                    <span className="text-sm font-bold">
                                        {(run.pass_rate * 100).toFixed(0)}<span className="text-[10px]">%</span>
                                    </span>
                                </div>
                            </div>

                            {/* Metrics Preview */}
                            <div className="space-y-3 mb-5">
                                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                                    <span>Performance</span>
                                    <span>{run.passed_test_cases}/{run.total_test_cases} passed</span>
                                </div>
                                <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
                                    <div
                                        className={`h-full rounded-full ${run.pass_rate >= 0.7 ? "bg-emerald-500" : "bg-rose-500"}`}
                                        style={{ width: `${run.pass_rate * 100}%` }}
                                    />
                                </div>

                                <div className="flex flex-wrap gap-1.5 mt-3">
                                    {run.metrics_evaluated.slice(0, 3).map(metric => (
                                        <span key={metric} className="px-2 py-1 rounded-md bg-secondary border border-border text-[10px] text-muted-foreground font-mono">
                                            {metric}
                                        </span>
                                    ))}
                                    {run.metrics_evaluated.length > 3 && (
                                        <span className="px-2 py-1 rounded-md bg-secondary border border-border text-[10px] text-muted-foreground font-mono">
                                            +{run.metrics_evaluated.length - 3}
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div className="flex items-center justify-between pt-4 border-t border-border/50">
                                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                    <Clock className="w-3.5 h-3.5" />
                                    <span>{new Date(run.started_at).toLocaleDateString()}</span>
                                    {run.finished_at && (
                                        <span className="opacity-50">• {new Date(run.finished_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Floating Comparison Action Bar */}
            {selectedRuns.size > 0 && (
                <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 bg-foreground text-background px-6 py-3 rounded-full shadow-xl flex items-center gap-4 animate-in slide-in-from-bottom-4 duration-200 z-50">
                    <span className="font-medium text-sm">{selectedRuns.size} runs selected</span>
                    <div className="h-4 w-px bg-background/20" />
                    <button
                        onClick={() => setSelectedRuns(new Set())}
                        className="text-sm text-background/70 hover:text-background transition-colors"
                    >
                        Clear
                    </button>
                    <button
                        onClick={handleCompare}
                        disabled={selectedRuns.size !== 2}
                        className={`bg-primary text-primary-foreground px-4 py-1.5 rounded-full text-sm font-semibold transition-all ${selectedRuns.size !== 2 ? "opacity-50 cursor-not-allowed" : "hover:bg-primary/90 hover:scale-105"}`}
                    >
                        Compare {selectedRuns.size === 2 ? "" : "(Select 2)"}
                    </button>
                </div>
            )}
        </Layout>
    );
}
