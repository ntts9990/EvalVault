import { useEffect, useState, useMemo } from "react";
import { Layout } from "../components/Layout";
import { fetchFacts, fetchBehaviors, type Fact, type Behavior } from "../services/api";
import { Brain, ScrollText, TrendingUp, Activity } from "lucide-react";
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

export function DomainMemory() {
    const [activeTab, setActiveTab] = useState<"facts" | "behaviors" | "insights">("facts");
    const [facts, setFacts] = useState<Fact[]>([]);
    const [behaviors, setBehaviors] = useState<Behavior[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadData() {
            setLoading(true);
            try {
                // If insights, we need facts for calculations
                if (activeTab === "facts" || activeTab === "insights") {
                    const data = await fetchFacts();
                    setFacts(data);
                }

                if (activeTab === "behaviors") {
                    const data = await fetchBehaviors();
                    setBehaviors(data);
                }
            } catch (err) {
                console.error("Failed to load domain memory data", err);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, [activeTab]);

    // Prepare Insight Data
    const trendData = useMemo(() => {
        if (!facts.length) return [];

        // Group by Date
        const grouped = facts.reduce((acc, fact) => {
            const date = new Date(fact.created_at).toLocaleDateString();
            if (!acc[date]) acc[date] = { count: 0, sum: 0 };
            acc[date].count += 1;
            acc[date].sum += fact.verification_score;
            return acc;
        }, {} as Record<string, { count: number; sum: number }>);

        return Object.entries(grouped)
            .map(([date, { count, sum }]) => ({
                date,
                avgScore: sum / count,
                count
            }))
            .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    }, [facts]);

    return (
        <Layout>
            <div className="max-w-6xl mx-auto pb-20">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold tracking-tight mb-2 font-display">Domain Memory</h1>
                    <p className="text-muted-foreground">Inspect learned facts and reusable behaviors.</p>
                </div>

                {/* Tabs */}
                <div className="mb-6">
                    <div className="tab-shell">
                        <button
                            onClick={() => setActiveTab("facts")}
                            className={`tab-pill flex items-center gap-2 ${activeTab === "facts"
                                ? "tab-pill-active"
                                : "tab-pill-inactive"
                                }`}
                        >
                            <ScrollText className="w-4 h-4" />
                            Verified Facts
                        </button>
                        <button
                            onClick={() => setActiveTab("behaviors")}
                            className={`tab-pill flex items-center gap-2 ${activeTab === "behaviors"
                                ? "tab-pill-active"
                                : "tab-pill-inactive"
                                }`}
                        >
                            <Brain className="w-4 h-4" />
                            Behaviors
                        </button>
                        <button
                            onClick={() => setActiveTab("insights")}
                            className={`tab-pill flex items-center gap-2 ${activeTab === "insights"
                                ? "tab-pill-active"
                                : "tab-pill-inactive"
                                }`}
                        >
                            <TrendingUp className="w-4 h-4" />
                            Insights
                        </button>
                    </div>
                </div>

                {/* Content */}
                {loading ? (
                    <div className="flex items-center justify-center h-40">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                ) : (
                    <>
                        {activeTab === "facts" && (
                            <div className="grid grid-cols-1 gap-4">
                                {facts.length === 0 ? (
                                    <p className="text-muted-foreground p-8 text-center bg-card rounded-xl border border-border">No facts found yet.</p>
                                ) : (
                                    facts.map((fact) => (
                                        <div key={fact.fact_id} className="surface-panel p-4 hover:shadow-md transition-all">
                                            <div className="flex justify-between items-start mb-2">
                                                <div className="flex gap-2 items-center">
                                                    <span className="bg-primary/10 text-primary text-xs px-2 py-1 rounded-full font-medium">{fact.domain || "General"}</span>
                                                    <span className="text-xs text-muted-foreground">{new Date(fact.created_at).toLocaleDateString()}</span>
                                                </div>
                                                <div className="text-xs font-mono text-muted-foreground">{fact.fact_id.substring(0, 8)}</div>
                                            </div>
                                            <div className="grid grid-cols-3 gap-2 text-sm">
                                                <div className="font-semibold text-right text-muted-foreground contents">
                                                    <span className="col-span-1 text-right pr-2 py-1 border-r border-border/50">Subject</span>
                                                    <span className="col-span-2 py-1 pl-2 font-medium">{fact.subject}</span>

                                                    <span className="col-span-1 text-right pr-2 py-1 border-r border-border/50">Predicate</span>
                                                    <span className="col-span-2 py-1 pl-2 text-blue-500 font-mono">{fact.predicate}</span>

                                                    <span className="col-span-1 text-right pr-2 py-1 border-r border-border/50">Object</span>
                                                    <span className="col-span-2 py-1 pl-2 font-medium">{fact.object}</span>
                                                </div>
                                            </div>
                                            <div className="mt-3 pt-3 border-t border-border/30 flex justify-between items-center">
                                                <span className="text-xs text-muted-foreground">Confidence Score</span>
                                                <div className="flex items-center gap-2">
                                                    <div className="w-24 h-2 bg-secondary rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-green-500"
                                                            style={{ width: `${fact.verification_score * 100}%` }}
                                                        ></div>
                                                    </div>
                                                    <span className="text-xs font-bold">{(fact.verification_score * 100).toFixed(0)}%</span>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}

                        {activeTab === "behaviors" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {behaviors.length === 0 ? (
                                    <p className="text-muted-foreground col-span-2 p-8 text-center bg-card rounded-xl border border-border">No behaviors learned yet.</p>
                                ) : (
                                    behaviors.map((behavior) => (
                                        <div key={behavior.behavior_id} className="surface-panel p-4 hover:shadow-md transition-all">
                                            <h3 className="font-semibold mb-2">{behavior.description}</h3>
                                            <div className="flex justify-between items-center text-sm text-muted-foreground mb-4">
                                                <span>Uses: {behavior.use_count}</span>
                                                <span className="text-green-500 font-medium">rate: {(behavior.success_rate * 100).toFixed(1)}%</span>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}

                        {activeTab === "insights" && (
                            <div className="space-y-6 animate-in fade-in duration-300">
                                {/* Fact Verification Trend (Line/Area Chart) */}
                                <div className="surface-panel p-6">
                                    <h3 className="font-semibold mb-2 flex items-center gap-2">
                                        <Activity className="w-4 h-4 text-primary" />
                                        Fact Verification Trend
                                    </h3>
                                    <p className="text-sm text-muted-foreground mb-6">Average confidence of learned facts over time</p>

                                    <div className="h-72 w-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                                <defs>
                                                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                                    </linearGradient>
                                                </defs>
                                                <XAxis dataKey="date" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} domain={[0, 1]} />
                                                <Tooltip
                                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                                />
                                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                                <Area
                                                    type="monotone"
                                                    dataKey="avgScore"
                                                    stroke="#10b981"
                                                    strokeWidth={2}
                                                    fillOpacity={1}
                                                    fill="url(#colorScore)"
                                                    name="Confidence Score"
                                                />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="surface-panel p-6">
                                        <h3 className="font-semibold mb-4">Memory Health</h3>
                                        <div className="space-y-4">
                                            <div className="flex justify-between items-center">
                                                <span className="text-sm text-muted-foreground">Total Facts</span>
                                                <span className="font-bold">{facts.length}</span>
                                            </div>
                                            <div className="flex justify-between items-center">
                                                <span className="text-sm text-muted-foreground">Average Confidence</span>
                                                <span className="font-bold text-emerald-500">
                                                    {(facts.reduce((acc, f) => acc + f.verification_score, 0) / (facts.length || 1) * 100).toFixed(1)}%
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </Layout>
    );
}
