import { useState, useEffect } from "react";
import { Layout } from "../components/Layout";
import {
    Upload,
    FileText,
    Database,
    Play,
    AlertCircle,
    RefreshCw,
    Network
} from "lucide-react";
import {
    uploadDocuments,
    buildKnowledgeGraph,
    fetchKGStats,
    fetchJobStatus,
    type KGStats
} from "../services/api";
import { KNOWLEDGE_BASE_BUILD_WORKERS } from "../config/ui";

export function KnowledgeBase() {
    const [stats, setStats] = useState<KGStats | null>(null);
    const [refreshing, setRefreshing] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [building, setBuilding] = useState(false);
    const [files, setFiles] = useState<File[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [buildJobId, setBuildJobId] = useState<string | null>(null);
    const [buildProgress, setBuildProgress] = useState<string>("0%");
    const [buildStatus, setBuildStatus] = useState<string>("");

    const loadStats = async () => {
        setRefreshing(true);
        try {
            const data = await fetchKGStats();
            setStats(data);
        } catch (err) {
            console.error(err);
        } finally {
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadStats();
    }, []);

    // Poll for build job status
    useEffect(() => {
        if (!buildJobId) return;

        const interval = setInterval(async () => {
            try {
                const job = await fetchJobStatus(buildJobId);
                setBuildStatus(job.status);
                setBuildProgress(typeof job.progress === 'string' ? job.progress : "0%");

                if (job.status === "completed" || job.status === "failed") {
                    setBuilding(false);
                    setBuildJobId(null);
                    loadStats(); // Refresh stats on completion
                }
            } catch (err) {
                console.error("Failed to poll job status", err);
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [buildJobId]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFiles(Array.from(e.target.files));
        }
    };

    const handleUpload = async () => {
        if (files.length === 0) return;
        setUploading(true);
        setError(null);
        try {
            await uploadDocuments(files);
            setFiles([]); // Clear selection
            // In a real app, we might refresh a file list here
        } catch {
            setError("Failed to upload files");
        } finally {
            setUploading(false);
        }
    };

    const handleBuild = async () => {
        setBuilding(true);
        setError(null);
        try {
            const { job_id } = await buildKnowledgeGraph({
                workers: KNOWLEDGE_BASE_BUILD_WORKERS,
                rebuild: true,
            });
            setBuildJobId(job_id);
            setBuildStatus("pending");
        } catch {
            setError("Failed to start build");
            setBuilding(false);
        }
    };

    return (
        <Layout>
            <div className="max-w-6xl mx-auto pb-20">
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight mb-2 font-display">Knowledge Base</h1>
                        <p className="text-muted-foreground">Manage raw documents and build the Knowledge Graph.</p>
                    </div>
                    <button
                        onClick={loadStats}
                        disabled={refreshing}
                        className="p-2 hover:bg-secondary rounded-full transition-colors"
                    >
                        <RefreshCw className={`w-5 h-5 ${refreshing ? "animate-spin" : ""}`} />
                    </button>
                </div>

                {error && (
                    <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6 flex items-center gap-2">
                        <AlertCircle className="w-5 h-5" />
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Stats Panel */}
                    <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="surface-panel p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="p-2 bg-blue-500/10 rounded-lg">
                                    <Network className="w-6 h-6 text-blue-500" />
                                </div>
                                <span className="text-sm font-medium text-muted-foreground">Total Entities</span>
                            </div>
                            <p className="text-3xl font-bold">{stats?.num_entities || 0}</p>
                        </div>
                        <div className="surface-panel p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="p-2 bg-purple-500/10 rounded-lg">
                                    <Network className="w-6 h-6 text-purple-500" />
                                </div>
                                <span className="text-sm font-medium text-muted-foreground">Total Relations</span>
                            </div>
                            <p className="text-3xl font-bold">{stats?.num_relations || 0}</p>
                        </div>
                        <div className="surface-panel p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="p-2 bg-green-500/10 rounded-lg">
                                    <Database className="w-6 h-6 text-green-500" />
                                </div>
                                <span className="text-sm font-medium text-muted-foreground">KG Status</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className={`w-3 h-3 rounded-full ${stats?.status === 'available' ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
                                <p className="text-lg font-medium capitalize">{stats?.status === 'available' ? 'Ready' : 'Not Built'}</p>
                            </div>
                        </div>
                    </div>

                    {/* Upload Section */}
                    <div className="lg:col-span-2 space-y-6">
                        <section className="surface-panel p-6">
                            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                <Upload className="w-5 h-5 text-primary" />
                                Upload Documents
                            </h2>

                            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:bg-secondary/30 transition-colors">
                                <input
                                    type="file"
                                    multiple
                                    className="hidden"
                                    id="file-upload"
                                    onChange={handleFileChange}
                                />
                                <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                                    <FileText className="w-12 h-12 text-muted-foreground mb-4" />
                                    <span className="text-lg font-medium mb-1">Click to select files</span>
                                    <span className="text-sm text-muted-foreground">Supported: .txt, .md, .json, .csv</span>
                                </label>
                            </div>

                            {files.length > 0 && (
                                <div className="mt-6 space-y-4">
                                    <div className="bg-secondary/50 rounded-lg p-4">
                                        <h3 className="font-medium text-sm mb-2">Selected Files ({files.length})</h3>
                                        <ul className="text-sm space-y-1 text-muted-foreground max-h-40 overflow-y-auto">
                                            {files.map((f, i) => (
                                                <li key={i} className="flex items-center gap-2">
                                                    <FileText className="w-3 h-3" />
                                                    {f.name}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                    <button
                                        onClick={handleUpload}
                                        disabled={uploading}
                                        className="w-full bg-primary hover:bg-primary/90 text-primary-foreground py-2 rounded-lg font-medium transition-all disabled:opacity-50"
                                    >
                                        {uploading ? "Uploading..." : "Upload Files"}
                                    </button>
                                </div>
                            )}
                        </section>
                    </div>

                    {/* Build Action */}
                    <div className="lg:col-span-1">
                        <section className="surface-panel p-6 h-full">
                            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                <Database className="w-5 h-5 text-primary" />
                                Build Knowledge Graph
                            </h2>

                            <p className="text-sm text-muted-foreground mb-6">
                                Process all uploaded documents to extract entities and relations. This may take a while depending on the volume of data.
                            </p>

                            {building ? (
                                <div className="space-y-4 p-4 bg-secondary/30 rounded-lg border border-border">
                                    <div className="flex justify-between text-sm font-medium">
                                        <span>Building...</span>
                                        <span className="text-primary">{buildProgress}</span>
                                    </div>
                                    <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                                        <div
                                            className="bg-primary h-full transition-all duration-300"
                                            style={{ width: buildProgress }}
                                        ></div>
                                    </div>
                                    <p className="text-xs text-muted-foreground capitalize text-center">{buildStatus}</p>
                                </div>
                            ) : (
                                <button
                                    onClick={handleBuild}
                                    className="w-full bg-secondary hover:bg-secondary/80 text-secondary-foreground py-3 rounded-lg font-medium border border-border transition-all flex items-center justify-center gap-2 group"
                                >
                                    <Play className="w-4 h-4 text-primary group-hover:scale-110 transition-transform" />
                                    Start Build Process
                                </button>
                            )}
                        </section>
                    </div>
                </div>
            </div>
        </Layout>
    );
}
