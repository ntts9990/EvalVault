import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import {
    type DatasetItem,
    type ModelItem,
    fetchDatasets,
    fetchDatasetTemplate,
    fetchModels,
    fetchMetrics,
    fetchConfig,
    startEvaluation,
    uploadDataset
} from "../services/api";
import { Play, Database, Brain, Target, CheckCircle2, AlertCircle, Settings, Upload, FileText, X } from "lucide-react";
import { useNavigate } from "react-router-dom";

export function EvaluationStudio() {
    const navigate = useNavigate();

    // Options
    const [datasets, setDatasets] = useState<DatasetItem[]>([]);
    const [models, setModels] = useState<ModelItem[]>([]);
    const [availableMetrics, setAvailableMetrics] = useState<string[]>([]);

    // Selections
    const [selectedDataset, setSelectedDataset] = useState<string>("");
    const [selectedModel, setSelectedModel] = useState<string>("");
    const [selectedProvider, setSelectedProvider] = useState<"ollama" | "openai" | "vllm">("ollama");
    const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set(["faithfulness", "answer_relevancy"]));

    // Advanced Options State
    const [retrieverMode, setRetrieverMode] = useState<"none" | "bm25" | "hybrid">("none");
    const [docsPath, setDocsPath] = useState<string>("");
    const [enableMemory, setEnableMemory] = useState<boolean>(false);
    const [tracker, setTracker] = useState<"none" | "phoenix" | "langfuse">("phoenix");
    const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
    const [batchSize, setBatchSize] = useState<number>(1);

    // Upload Modal State
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);

    // UI State
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [modelsLoading, setModelsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Progress State
    const [progress, setProgress] = useState(0);
    const [progressMessage, setProgressMessage] = useState("Initializing...");
    const [logs, setLogs] = useState<string[]>([]);

    const handleUpload = async () => {
        if (!uploadFile) return;
        setUploading(true);
        try {
            await uploadDataset(uploadFile);
            setIsUploadModalOpen(false);
            setUploadFile(null);
            // Refresh datasets
            const d = await fetchDatasets();
            setDatasets(d);
            // Auto select new dataset
            const newDs = d.find(ds => ds.name === uploadFile.name);
            if (newDs) setSelectedDataset(newDs.path);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to upload");
        } finally {
            setUploading(false);
        }
    };

    const handleTemplateDownload = async (format: "json" | "csv" | "xlsx") => {
        try {
            const blob = await fetchDatasetTemplate(format);
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = `dataset_template.${format}`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to download template");
        }
    };

    useEffect(() => {
        async function loadOptions() {
            try {
                const [d, met, cfg] = await Promise.all([
                    fetchDatasets(),
                    fetchMetrics(),
                    fetchConfig().catch(() => null)
                ]);
                setDatasets(d);
                setAvailableMetrics(met);

                if (d.length > 0) setSelectedDataset(d[0].path);

                let provider: "ollama" | "openai" | "vllm" = "ollama";
                if (cfg && (cfg.llm_provider === "ollama" || cfg.llm_provider === "openai" || cfg.llm_provider === "vllm")) {
                    provider = cfg.llm_provider;
                }

                setSelectedProvider(provider);
                setModelsLoading(true);

                let modelList = await fetchModels(provider);
                if (modelList.length === 0 && provider !== "openai") {
                    provider = "openai";
                    setSelectedProvider(provider);
                    modelList = await fetchModels(provider);
                }

                setModels(modelList);
                if (modelList.length > 0) setSelectedModel(modelList[0].id);
            } catch (err) {
                setError("Failed to load configuration options");
                console.error(err);
            } finally {
                setModelsLoading(false);
                setLoading(false);
            }
        }
        loadOptions();
    }, []);

    const handleProviderChange = async (provider: "ollama" | "openai" | "vllm") => {
        if (provider === selectedProvider) return;
        setSelectedProvider(provider);
        setModels([]);
        setSelectedModel("");
        setModelsLoading(true);
        setError(null);

        try {
            const modelList = await fetchModels(provider);
            setModels(modelList);
            if (modelList.length > 0) {
                setSelectedModel(modelList[0].id);
            } else {
                const hint = provider === "ollama"
                    ? "Run 'ollama list' to verify local models."
                    : provider === "vllm"
                        ? "Check VLLM_BASE_URL and model settings."
                        : "Check provider configuration.";
                setError(`No ${provider.toUpperCase()} models found. ${hint}`);
            }
        } catch (err) {
            setError(`${provider.toUpperCase()} 모델 목록을 불러오지 못했습니다.`);
        } finally {
            setModelsLoading(false);
        }
    };

    const toggleMetric = (metric: string) => {
        const newSet = new Set(selectedMetrics);
        if (newSet.has(metric)) {
            newSet.delete(metric);
        } else {
            newSet.add(metric);
        }
        setSelectedMetrics(newSet);
    };

    const handleStart = async () => {
        if (!selectedDataset || !selectedModel || selectedMetrics.size === 0) {
            setError("Please select all required fields");
            return;
        }
        if (retrieverMode !== "none" && !docsPath.trim()) {
            setError("Retriever docs path is required when retriever is enabled.");
            return;
        }

        setSubmitting(true);
        setError(null);
        setProgress(0);
        setLogs([]);
        setProgressMessage("Initializing...");

        try {
            const result = await startEvaluation({
                dataset_path: selectedDataset,
                model: selectedModel,
                metrics: Array.from(selectedMetrics),
                parallel: batchSize > 1,
                batch_size: batchSize,
                retriever_config: retrieverMode !== "none"
                    ? { mode: retrieverMode, docs_path: docsPath.trim(), top_k: 5 }
                    : undefined,
                memory_config: enableMemory ? { enabled: true, augment_context: true } : undefined,
                tracker_config: tracker !== "none" ? { provider: tracker } : undefined
            }, (event) => {
                if (event.type === "progress") {
                    setProgress(event.data.percent);
                    setProgressMessage(event.data.message || "Processing...");
                } else if (event.type === "info" || event.type === "warning" || event.type === "step") {
                    const msg = event.message || "";
                    setLogs(prev => [...prev, msg]);
                    setProgressMessage(msg);
                }
            });

            // Short delay to show 100%
            await new Promise(r => setTimeout(r, 500));
            // Navigate to run details
            navigate(`/runs/${result.run_id}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to start evaluation");
            setSubmitting(false);
        }
    };

    if (loading) return (
        <Layout>
            <div className="flex items-center justify-center h-[50vh]">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        </Layout>
    );

    return (
        <Layout>
            <div className="max-w-4xl mx-auto pb-20">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold tracking-tight mb-2">Evaluation Studio</h1>
                    <p className="text-muted-foreground">Configure and execute new RAG evaluations.</p>
                </div>

                {error && (
                    <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6 flex items-center gap-2">
                        <AlertCircle className="w-5 h-5" />
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 gap-8">
                    {/* Dataset Selection */}
                    <section className="bg-card border border-border rounded-xl p-6 shadow-sm">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-semibold flex items-center gap-2">
                                <Database className="w-5 h-5 text-primary" />
                                Select Dataset
                            </h2>
                            <div className="flex items-center gap-3">
                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                    <span>Templates:</span>
                                    {(["json", "csv", "xlsx"] as const).map((format) => (
                                        <button
                                            key={format}
                                            onClick={() => handleTemplateDownload(format)}
                                            className="px-2 py-1 rounded-md border border-border bg-secondary text-foreground hover:bg-secondary/80"
                                        >
                                            {format.toUpperCase()}
                                        </button>
                                    ))}
                                </div>
                                <button
                                    onClick={() => setIsUploadModalOpen(true)}
                                    className="text-sm text-primary hover:underline flex items-center gap-1"
                                >
                                    + Upload New
                                </button>
                            </div>
                        </div>
                        {datasets.length === 0 ? (
                            <p className="text-sm text-yellow-500">No datasets found. Please add files to `data/datasets`.</p>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {datasets.map((ds) => (
                                    <div
                                        key={ds.path}
                                        onClick={() => setSelectedDataset(ds.path)}
                                        className={`p-4 rounded-lg border cursor-pointer transition-all ${selectedDataset === ds.path
                                            ? "border-primary bg-primary/5 ring-1 ring-primary"
                                            : "border-border hover:border-primary/50"
                                            }`}
                                    >
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <p className="font-medium">{ds.name}</p>
                                                <p className="text-xs text-muted-foreground uppercase mt-1">{ds.type}</p>
                                            </div>
                                            {selectedDataset === ds.path && <CheckCircle2 className="w-5 h-5 text-primary" />}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>

                    {/* Model Selection */}
                    <section className="bg-card border border-border rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Brain className="w-5 h-5 text-primary" />
                            Select Model
                        </h2>
                        <div className="flex flex-wrap gap-2 mb-4">
                            {(["ollama", "openai", "vllm"] as const).map((provider) => (
                                <button
                                    key={provider}
                                    onClick={() => handleProviderChange(provider)}
                                    className={`px-3 py-1.5 rounded-md text-sm border capitalize ${selectedProvider === provider
                                        ? "bg-primary/10 border-primary text-primary"
                                        : "bg-secondary border-transparent"}`}
                                >
                                    {provider}
                                </button>
                            ))}
                        </div>
                        {selectedProvider === "ollama" && (
                            <div className="mb-4 rounded-lg border border-border/60 bg-secondary/40 p-3 text-xs text-muted-foreground">
                                <div className="text-sm font-medium text-foreground mb-2">Recommended Ollama models</div>
                                <div className="flex flex-wrap gap-2">
                                    {["gpt-oss:120b", "gpt-oss-safeguard:120b", "gpt-oss-safeguard:20b"].map((model) => (
                                        <span
                                            key={model}
                                            className="px-2 py-0.5 rounded-full border border-border bg-background text-[11px]"
                                        >
                                            {model}
                                        </span>
                                    ))}
                                </div>
                                <div className="mt-2">
                                    Add a model with{" "}
                                    <code className="px-1 py-0.5 rounded bg-muted font-mono text-[11px]">
                                        ollama pull &lt;model&gt;
                                    </code>{" "}
                                    then refresh. Embedding-only models are hidden.
                                </div>
                            </div>
                        )}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {modelsLoading ? (
                                <div className="col-span-2 text-sm text-muted-foreground flex items-center gap-2">
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                                    Loading models...
                                </div>
                            ) : models.length === 0 ? (
                                <div className="col-span-2 text-sm text-muted-foreground">
                                    No models available for {selectedProvider}. Check backend connectivity.
                                </div>
                            ) : (
                                models.map((model) => (
                                    <div
                                        key={model.id}
                                        onClick={() => setSelectedModel(model.id)}
                                        className={`p-4 rounded-lg border cursor-pointer transition-all ${selectedModel === model.id
                                            ? "border-primary bg-primary/5 ring-1 ring-primary"
                                            : "border-border hover:border-primary/50"
                                            }`}
                                    >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <p className="font-medium">{model.name}</p>
                                                {model.supports_tools && (
                                                    <span className="text-[10px] uppercase px-2 py-0.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-600 font-semibold">
                                                        Tools
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-xs text-muted-foreground mt-1">{model.id}</p>
                                        </div>
                                            {selectedModel === model.id && <CheckCircle2 className="w-5 h-5 text-primary" />}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </section>

                    {/* Metrics Selection */}
                    <section className="bg-card border border-border rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Target className="w-5 h-5 text-primary" />
                            Select Metrics
                        </h2>
                        <div className="flex flex-wrap gap-3">
                            {availableMetrics.map((metric) => {
                                const isSelected = selectedMetrics.has(metric);
                                return (
                                    <button
                                        key={metric}
                                        onClick={() => toggleMetric(metric)}
                                        className={`px-4 py-2 rounded-full text-sm font-medium transition-all border ${isSelected
                                            ? "bg-primary text-primary-foreground border-primary"
                                            : "bg-secondary text-secondary-foreground border-transparent hover:bg-secondary/80"
                                            }`}
                                    >
                                        {metric}
                                    </button>
                                );
                            })}
                        </div>
                    </section>
                    {/* Advanced Configuration */}
                    <section className="bg-card border border-border rounded-xl p-6 shadow-sm">
                        <button
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className="flex items-center gap-2 w-full text-left"
                        >
                            <Settings className="w-5 h-5 text-primary" />
                            <h2 className="text-lg font-semibold">Advanced Configuration</h2>
                            <span className="text-xs text-muted-foreground ml-auto">
                                {showAdvanced ? "Hide" : "Show"}
                            </span>
                        </button>

                        {showAdvanced && (
                            <div className="mt-6 space-y-6 pt-4 border-t border-border/50">
                                {/* Retriever */}
                                <div>
                                    <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                                        Retriever Setup
                                        <span className="text-xs font-normal text-muted-foreground">(Augment context with external docs)</span>
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="space-y-4">
                                            <div className="flex gap-2">
                                                {(["none", "bm25", "hybrid"] as const).map(mode => (
                                                    <button
                                                        key={mode}
                                                        onClick={() => setRetrieverMode(mode)}
                                                        className={`px-3 py-1.5 rounded-md text-sm border capitalize ${retrieverMode === mode
                                                            ? "bg-primary/10 border-primary text-primary"
                                                            : "bg-secondary border-transparent"}`}
                                                    >
                                                        {mode}Mode
                                                    </button>
                                                ))}
                                            </div>
                                            {retrieverMode !== "none" && (
                                                <input
                                                    type="text"
                                                    placeholder="Absolute path to documents (json/jsonl/txt)"
                                                    className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm"
                                                    value={docsPath}
                                                    onChange={(e) => setDocsPath(e.target.value)}
                                                />
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Performance Config */}
                                <div>
                                    <h3 className="text-sm font-medium mb-3">Performance & Batching</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <label className="text-xs text-muted-foreground mb-1 block">Batch Size (parallelism)</label>
                                            <input
                                                type="number"
                                                min="1"
                                                max="50"
                                                value={batchSize}
                                                onChange={(e) => setBatchSize(Math.max(1, Number(e.target.value) || 1))}
                                                className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm"
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Domain Memory */}
                                <div>
                                    <h3 className="text-sm font-medium mb-3">Domain Memory</h3>
                                    <div
                                        onClick={() => setEnableMemory(!enableMemory)}
                                        className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${enableMemory
                                            ? "border-primary bg-primary/5"
                                            : "border-border hover:border-primary/30"}`}
                                    >
                                        <div className={`w-5 h-5 rounded border flex items-center justify-center ${enableMemory ? "bg-primary border-primary" : "border-muted-foreground"}`}>
                                            {enableMemory && <CheckCircle2 className="w-3 h-3 text-primary-foreground" />}
                                        </div>
                                        <div>
                                            <p className="font-medium text-sm">Enable Domain Memory</p>
                                            <p className="text-xs text-muted-foreground">Use historical facts and behaviors to improve generation</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Tracker */}
                                <div>
                                    <h3 className="text-sm font-medium mb-3">Observability Tracker</h3>
                                    <div className="flex gap-2">
                                        {(["none", "phoenix", "langfuse"] as const).map(t => (
                                            <button
                                                key={t}
                                                onClick={() => setTracker(t)}
                                                className={`px-3 py-1.5 rounded-md text-sm border capitalize ${tracker === t
                                                    ? "bg-primary/10 border-primary text-primary"
                                                    : "bg-secondary border-transparent"}`}
                                            >
                                                {t}
                                            </button>
                                        ))}
                                    </div>
                                    {tracker === "phoenix" && (
                                        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in slide-in-from-top-1">
                                            <input
                                                type="text"
                                                placeholder="Phoenix Project Name (Optional)"
                                                className="px-3 py-2 rounded-md border border-border bg-background text-sm"
                                            />
                                            <input
                                                type="text"
                                                placeholder="Experiment Description (Optional)"
                                                className="px-3 py-2 rounded-md border border-border bg-background text-sm"
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </section>

                    {/* Action */}
                    <div className="flex justify-end">
                        <button
                            onClick={handleStart}
                            disabled={submitting || !selectedDataset || !selectedModel}
                            className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-3 rounded-lg font-semibold flex items-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {submitting ? (
                                <>Starting...</>
                            ) : (
                                <>
                                    <Play className="w-5 h-5 fill-current" />
                                    Start Evaluation
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Progress Overlay */}
            {submitting && (
                <div className="fixed inset-0 bg-background/90 backdrop-blur-sm z-[60] flex flex-col items-center justify-center p-6">
                    <div className="w-full max-w-lg space-y-6 text-center animate-in fade-in zoom-in-95">
                        <div className="relative w-24 h-24 mx-auto mb-4">
                            <div className="absolute inset-0 rounded-full border-4 border-muted"></div>
                            <div
                                className="absolute inset-0 rounded-full border-4 border-primary border-t-transparent animate-spin"
                                style={{ animationDuration: '1.5s' }}
                            ></div>
                            <div className="absolute inset-0 flex items-center justify-center font-bold text-xl">
                                {Math.round(progress)}%
                            </div>
                        </div>

                        <div>
                            <h2 className="text-2xl font-semibold mb-2">Evaluating...</h2>
                            <p className="text-muted-foreground animate-pulse">{progressMessage}</p>
                        </div>

                        <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
                            <div
                                className="bg-primary h-full transition-all duration-300 ease-out"
                                style={{ width: `${progress}%` }}
                            />
                        </div>

                        <div className="bg-card border border-border rounded-lg p-4 h-48 overflow-y-auto text-left font-mono text-xs">
                            {logs.length === 0 && <span className="text-muted-foreground opacity-50">Waiting for logs...</span>}
                            {logs.map((log, i) => (
                                <div key={i} className="mb-1 pb-1 border-b border-border/10 last:border-0">
                                    <span className="text-primary mr-2">›</span>
                                    {log}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Upload Modal */}
            {isUploadModalOpen && (
                <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
                    <div className="bg-card border border-border w-full max-w-md rounded-xl shadow-lg p-6 animate-in zoom-in-95 duration-200">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-lg font-semibold flex items-center gap-2">
                                <Upload className="w-5 h-5 text-primary" />
                                Upload Dataset
                            </h2>
                            <button onClick={() => setIsUploadModalOpen(false)} className="text-muted-foreground hover:text-foreground">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="space-y-6">
                            <div className="border-2 border-dashed border-border rounded-xl p-8 flex flex-col items-center justify-center text-center hover:bg-secondary/50 transition-colors relative">
                                <input
                                    type="file"
                                    accept=".json,.csv,.xlsx"
                                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                                    className="absolute inset-0 opacity-0 cursor-pointer"
                                />
                                {uploadFile ? (
                                    <>
                                        <FileText className="w-10 h-10 text-primary mb-3" />
                                        <p className="font-medium text-foreground">{uploadFile.name}</p>
                                        <p className="text-xs text-muted-foreground mt-1">{(uploadFile.size / 1024).toFixed(1)} KB</p>
                                    </>
                                ) : (
                                    <>
                                        <Upload className="w-10 h-10 text-muted-foreground mb-3" />
                                        <p className="font-medium text-muted-foreground">Click to browse or drag file here</p>
                                        <p className="text-xs text-muted-foreground mt-2">Supports JSON, CSV, Excel</p>
                                    </>
                                )}
                            </div>

                            <div className="flex gap-3 justify-end">
                                <button
                                    onClick={() => setIsUploadModalOpen(false)}
                                    className="px-4 py-2 rounded-lg text-sm font-medium hover:bg-secondary transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleUpload}
                                    disabled={!uploadFile || uploading}
                                    className="bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50 transition-colors"
                                >
                                    {uploading ? "Uploading..." : "Upload Dataset"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </Layout>
    );
}
