import { useEffect, useMemo, useState } from "react";
import { Layout } from "../components/Layout";
import {
    type DatasetItem,
    type MetricSpec,
    type ModelItem,
    type SystemConfig,
    fetchDatasets,
    fetchDatasetTemplate,
    fetchMetricSpecs,
    fetchModels,
    fetchMetrics,
    fetchRuns,
    fetchConfig,
    startEvaluation,
    uploadDataset,
    uploadRetrieverDocs
} from "../services/api";
import {
    Play,
    Database,
    Brain,
    Target,
    CheckCircle2,
    AlertCircle,
    Settings,
    Upload,
    FileText,
    X,
    ExternalLink,
    Terminal
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { SUMMARY_METRICS, SUMMARY_METRIC_THRESHOLDS, type SummaryMetric } from "../utils/summaryMetrics";
import { getPhoenixUiUrl } from "../utils/phoenix";
import { buildRunCommand } from "../utils/cliCommandBuilder";
import { copyTextToClipboard } from "../utils/clipboard";

const DEFAULT_METRICS = ["faithfulness", "answer_relevancy"];
const RETRIEVER_MODES = [
    { value: "none", label: "Off" },
    { value: "bm25", label: "BM25" },
    { value: "hybrid", label: "Hybrid" },
] as const;

const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === "object" && value !== null;

const formatEta = (seconds: number | null) => {
    if (seconds == null || !Number.isFinite(seconds)) return "--:--";
    const total = Math.max(0, Math.floor(seconds));
    const mins = Math.floor(total / 60);
    const secs = total % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
};

export function EvaluationStudio() {
    const navigate = useNavigate();

    // Options
    const [datasets, setDatasets] = useState<DatasetItem[]>([]);
    const [models, setModels] = useState<ModelItem[]>([]);
    const [availableMetrics, setAvailableMetrics] = useState<string[]>([]);
    const [metricSpecs, setMetricSpecs] = useState<MetricSpec[]>([]);
    const [metricSpecError, setMetricSpecError] = useState<string | null>(null);

    // Selections
    const [selectedDataset, setSelectedDataset] = useState<string>("");
    const [selectedModel, setSelectedModel] = useState<string>("");
    const [selectedProvider, setSelectedProvider] = useState<"ollama" | "openai" | "vllm">("ollama");
    const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set(DEFAULT_METRICS));
    const [summaryMode, setSummaryMode] = useState(false);
    const [metricBackup, setMetricBackup] = useState<string[]>([]);
    const [projectName, setProjectName] = useState<string>("");
    const [projectOptions, setProjectOptions] = useState<string[]>([]);

    // Advanced Options State
    const [retrieverMode, setRetrieverMode] = useState<"none" | "bm25" | "hybrid">("none");
    const [docsPath, setDocsPath] = useState<string>("");
    const [retrieverFile, setRetrieverFile] = useState<File | null>(null);
    const [retrieverUploading, setRetrieverUploading] = useState(false);
    const [enableMemory, setEnableMemory] = useState<boolean>(false);
    const [stageStore, setStageStore] = useState<boolean>(true);
    const [tracker, setTracker] = useState<"none" | "phoenix" | "langfuse" | "mlflow">("phoenix");
    const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
    const [batchSize, setBatchSize] = useState<number>(1);
    const [thresholdProfile, setThresholdProfile] = useState<"none" | "summary" | "qa">("none");
    const [systemPrompt, setSystemPrompt] = useState<string>("");
    const [systemPromptName, setSystemPromptName] = useState<string>("");
    const [promptSetName, setPromptSetName] = useState<string>("");
    const [promptSetDescription, setPromptSetDescription] = useState<string>("");
    const [ragasPromptsYaml, setRagasPromptsYaml] = useState<string>("");
    const [phoenixUiUrl, setPhoenixUiUrl] = useState<string | null>(null);
    const [configDefaults, setConfigDefaults] = useState<SystemConfig | null>(null);

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
    const [progressStats, setProgressStats] = useState({
        current: 0,
        total: 0,
        etaSeconds: null as number | null,
        rate: null as number | null,
    });
    const [copyStatus, setCopyStatus] = useState<"idle" | "success" | "error">("idle");

    const metricSpecMap = useMemo(() => {
        return new Map(metricSpecs.map((spec) => [spec.name, spec]));
    }, [metricSpecs]);

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

    const handleRetrieverFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setRetrieverFile(e.target.files?.[0] || null);
    };

    const handleRetrieverUpload = async () => {
        if (!retrieverFile) return;
        setRetrieverUploading(true);
        setError(null);
        try {
            const result = await uploadRetrieverDocs(retrieverFile);
            setDocsPath(result.path);
            setRetrieverFile(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to upload retriever docs");
        } finally {
            setRetrieverUploading(false);
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
                const [d, met, specs, cfg, runList] = await Promise.all([
                    fetchDatasets(),
                    fetchMetrics().catch(() => []),
                    fetchMetricSpecs().catch((err) => {
                        setMetricSpecError(
                            err instanceof Error ? err.message : "Failed to fetch metric specs"
                        );
                        return [];
                    }),
                    fetchConfig().catch(() => null),
                    fetchRuns().catch(() => [])
                ]);
                setDatasets(d);
                setMetricSpecs(specs);
                setAvailableMetrics(specs.length ? specs.map((spec) => spec.name) : met);
                const projects = Array.from(
                    new Set(
                        runList
                            .map(run => (run.project_name || "").trim())
                            .filter(name => name.length > 0)
                    )
                ).sort((a, b) => a.localeCompare(b));
                setProjectOptions(projects);
                setConfigDefaults(cfg);
                setPhoenixUiUrl(getPhoenixUiUrl(cfg?.phoenix_endpoint));

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
                if (modelList.length > 0) {
                    const defaultName = provider === "openai"
                        ? String(cfg?.openai_model || "")
                        : provider === "vllm"
                            ? String(cfg?.vllm_model || "")
                            : String(cfg?.ollama_model || "");
                    const defaultId = defaultName ? `${provider}/${defaultName}` : "";
                    const matched = defaultId ? modelList.find(model => model.id === defaultId) : undefined;
                    setSelectedModel(matched?.id || modelList[0].id);
                }

                const trackerCandidate = cfg?.tracker_provider;
                if (trackerCandidate === "phoenix" || trackerCandidate === "langfuse" || trackerCandidate === "mlflow" || trackerCandidate === "none") {
                    setTracker(trackerCandidate);
                }
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
                const defaultName = provider === "openai"
                    ? String(configDefaults?.openai_model || "")
                    : provider === "vllm"
                        ? String(configDefaults?.vllm_model || "")
                        : String(configDefaults?.ollama_model || "");
                const defaultId = defaultName ? `${provider}/${defaultName}` : "";
                const matched = defaultId ? modelList.find(model => model.id === defaultId) : undefined;
                setSelectedModel(matched?.id || modelList[0].id);
            } else {
                const hint = provider === "ollama"
                    ? "Run 'ollama list' to verify local models."
                    : provider === "vllm"
                        ? "Check VLLM_BASE_URL and model settings."
                        : "Check provider configuration.";
                setError(`No ${provider.toUpperCase()} models found. ${hint}`);
            }
        } catch {
            setError(`${provider.toUpperCase()} 모델 목록을 불러오지 못했습니다.`);
        } finally {
            setModelsLoading(false);
        }
    };

    const summaryMetricSet = new Set<string>(SUMMARY_METRICS);
    const summaryThresholdLabel = SUMMARY_METRICS.map((metric) => {
        const threshold = SUMMARY_METRIC_THRESHOLDS[metric];
        return `${metric} >= ${threshold.toFixed(2)}`;
    }).join(" | ");

    const toggleSummaryMode = () => {
        if (!summaryMode) {
            setMetricBackup(Array.from(selectedMetrics));
            setSelectedMetrics(new Set(SUMMARY_METRICS));
            setSummaryMode(true);
            return;
        }
        const fallback = metricBackup.length ? metricBackup : DEFAULT_METRICS;
        setSelectedMetrics(new Set(fallback));
        setSummaryMode(false);
    };

    const toggleMetric = (metric: string) => {
        if (summaryMode) return;
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
        setProgressStats({ current: 0, total: 0, etaSeconds: null, rate: null });

        try {
            const systemPromptValue = systemPrompt.trim();
            const ragasPromptValue = ragasPromptsYaml.trim();
            const result = await startEvaluation({
                dataset_path: selectedDataset,
                model: selectedModel,
                metrics: Array.from(selectedMetrics),
                evaluation_task: summaryMode ? "summarization" : "qa",
                project_name: projectName.trim() || undefined,
                parallel: batchSize > 1,
                batch_size: batchSize,
                threshold_profile: thresholdProfile !== "none" ? thresholdProfile : undefined,
                retriever_config: retrieverMode !== "none"
                    ? { mode: retrieverMode, docs_path: docsPath.trim(), top_k: 5 }
                    : undefined,
                memory_config: enableMemory ? { enabled: true, augment_context: true } : undefined,
                tracker_config: tracker !== "none" ? { provider: tracker } : undefined,
                stage_store: stageStore,
                system_prompt: systemPromptValue ? systemPrompt : undefined,
                system_prompt_name: systemPromptName.trim() || undefined,
                prompt_set_name: promptSetName.trim() || undefined,
                prompt_set_description: promptSetDescription.trim() || undefined,
                ragas_prompts_yaml: ragasPromptValue ? ragasPromptsYaml : undefined,
            }, (event) => {
                if (event.type === "progress") {
                    const data = isRecord(event.data) ? event.data : {};
                    const percent = typeof data.percent === "number" ? data.percent : 0;
                    const message = typeof data.message === "string" ? data.message : "Processing...";
                    const current = typeof data.current === "number" ? data.current : 0;
                    const total = typeof data.total === "number" ? data.total : 0;
                    const etaSeconds = typeof data.eta_seconds === "number" && Number.isFinite(data.eta_seconds)
                        ? data.eta_seconds
                        : null;
                    const rate = typeof data.rate === "number" && Number.isFinite(data.rate)
                        ? data.rate
                        : null;
                    setProgress(percent);
                    setProgressMessage(message);
                    setProgressStats({ current, total, etaSeconds, rate });
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

    const handleCopyCli = async () => {
        const command = buildRunCommand({
            dataset_path: selectedDataset,
            model: selectedModel,
            metrics: Array.from(selectedMetrics),
            summaryMode,
            threshold_profile: thresholdProfile,
            retriever_mode: retrieverMode,
            docs_path: docsPath,
            tracker,
            stage_store: stageStore,
            enable_memory: enableMemory,
            system_prompt: systemPrompt,
            system_prompt_name: systemPromptName,
            prompt_set_name: promptSetName,
            prompt_set_description: promptSetDescription,
            batch_size: batchSize,
            parallel: batchSize > 1,
            ragas_prompts_yaml: ragasPromptsYaml,
        });

        const success = await copyTextToClipboard(command);
        setCopyStatus(success ? "success" : "error");
        setTimeout(() => setCopyStatus("idle"), 1500);
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
                    <h1 className="text-3xl font-bold tracking-tight mb-2 font-display">Evaluation Studio</h1>
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
                    <section className="surface-panel p-6">
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
                    <section className="surface-panel p-6">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Brain className="w-5 h-5 text-primary" />
                            Select Model
                        </h2>
                        <div className="tab-shell mb-4">
                            {(["ollama", "openai", "vllm"] as const).map((provider) => (
                                <button
                                    key={provider}
                                    onClick={() => handleProviderChange(provider)}
                                    className={`tab-pill capitalize ${selectedProvider === provider
                                        ? "tab-pill-active"
                                        : "tab-pill-inactive"}`}
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

                    <section className="surface-panel p-6">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Target className="w-5 h-5 text-primary" />
                            Project Label
                        </h2>
                        <div className="space-y-3">
                            <input
                                list="project-options"
                                value={projectName}
                                onChange={(event) => setProjectName(event.target.value)}
                                placeholder="e.g. Insurance QA Revamp"
                                className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm"
                            />
                            <datalist id="project-options">
                                {projectOptions.map((project) => (
                                    <option key={project} value={project} />
                                ))}
                            </datalist>
                            <p className="text-xs text-muted-foreground">
                                Project labels drive dashboard and report filtering.
                            </p>
                            {projectName && (
                                <button
                                    type="button"
                                    onClick={() => setProjectName("")}
                                    className="text-xs text-muted-foreground hover:text-foreground"
                                >
                                    Clear project label
                                </button>
                            )}
                        </div>
                    </section>

                    <section className="surface-panel p-6">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <FileText className="w-5 h-5 text-primary" />
                            Summary Evaluation
                        </h2>
                        <div
                            onClick={toggleSummaryMode}
                            className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-all ${summaryMode
                                ? "border-primary bg-primary/5"
                                : "border-border hover:border-primary/30"}`}
                        >
                            <div className={`mt-0.5 w-5 h-5 rounded border flex items-center justify-center ${summaryMode ? "bg-primary border-primary" : "border-muted-foreground"}`}>
                                {summaryMode && <CheckCircle2 className="w-3 h-3 text-primary-foreground" />}
                            </div>
                            <div className="space-y-1">
                                <p className="font-medium text-sm">
                                    Enable summary-focused preset
                                </p>
                                    <p className="text-xs text-muted-foreground">
                                        Locks metrics to summary_faithfulness(LLM), summary_score(LLM),
                                        entity_preservation(Rule), summary_accuracy(Rule), summary_risk_coverage(Rule),
                                        summary_non_definitive(Rule), summary_needs_followup(Rule).
                                    </p>

                            </div>
                        </div>
                        <div className="mt-3 text-xs text-muted-foreground space-y-1">
                            <p>Defaults apply when dataset thresholds are missing.</p>
                            <p>{summaryThresholdLabel}</p>
                        </div>
                        <div className="mt-3 space-y-2">
                            <div className="flex flex-wrap gap-2">
                                {SUMMARY_METRICS.map(metric => (
                                    <span
                                        key={metric}
                                        className="px-2 py-0.5 rounded-full border border-border bg-secondary text-[11px] text-muted-foreground"
                                    >
                                        {metric}
                                    </span>
                                ))}
                            </div>
                            <div className="text-[11px] text-muted-foreground">
                                LLM: summary_faithfulness, summary_score · Rule: entity_preservation,
                                summary_accuracy, summary_risk_coverage, summary_non_definitive,
                                summary_needs_followup
                            </div>
                        </div>
                    </section>

                    {/* Metrics Selection */}
                    <section className="surface-panel p-6">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Target className="w-5 h-5 text-primary" />
                            Select Metrics
                        </h2>
                        <div className="flex flex-wrap gap-3">
                            {availableMetrics.map((metric) => {
                                const isSelected = selectedMetrics.has(metric);
                                const isSummaryMetric = summaryMetricSet.has(metric as SummaryMetric);
                                const isDisabled = summaryMode;
                                const spec = metricSpecMap.get(metric);
                                return (
                                    <button
                                        key={metric}
                                        onClick={() => toggleMetric(metric)}
                                        disabled={isDisabled}
                                        className={`filter-chip text-sm px-4 py-2 disabled:opacity-60 disabled:cursor-not-allowed ${isSelected
                                            ? "filter-chip-active"
                                            : "filter-chip-inactive"
                                            } ${summaryMode && isSummaryMetric ? "ring-1 ring-primary/40" : ""}`}
                                    >
                                        <span className="inline-flex items-center gap-2">
                                            <span title={spec?.description || metric}>{metric}</span>
                                            {spec?.requires_ground_truth && (
                                                <span className="rounded-full border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">
                                                    GT
                                                </span>
                                            )}
                                            {spec?.requires_embeddings && (
                                                <span className="rounded-full border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">
                                                    Emb
                                                </span>
                                            )}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                        {metricSpecError && (
                            <p className="mt-3 text-xs text-rose-500">
                                {metricSpecError}
                            </p>
                        )}
                    </section>
                    {/* Advanced Configuration */}
                    <section className="surface-panel p-6">
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
                        <p className="mt-2 text-xs text-muted-foreground">
                            고급 옵션은 필요할 때만 사용하세요. 기본값만으로도 평가가 가능합니다.
                        </p>

                        {showAdvanced && (
                            <div className="mt-6 space-y-6 pt-4 border-t border-border/50">
                                {/* Retriever */}
                                <div>
                                    <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                                        Retriever Setup
                                        <span className="text-xs font-normal text-muted-foreground">(빈 컨텍스트 자동 보강)</span>
                                    </h3>
                                    <div className="text-xs text-muted-foreground space-y-1 mb-4">
                                        <p>contexts가 비어 있는 케이스에만 문서 검색 결과를 채웁니다. 기존 contexts는 유지됩니다.</p>
                                        <p>
                                            Retriever는{" "}
                                            <code className="px-1 py-0.5 rounded bg-muted font-mono text-[11px]">
                                                uv sync --extra korean
                                            </code>{" "}
                                            설치가 필요합니다.
                                        </p>
                                        <p>Web UI는 top_k=5로 고정됩니다. 더 조정하려면 CLI/API를 사용하세요.</p>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="space-y-4">
                                            <div className="tab-shell">
                                                {RETRIEVER_MODES.map((mode) => (
                                                    <button
                                                        key={mode.value}
                                                        onClick={() => setRetrieverMode(mode.value)}
                                                        className={`tab-pill ${retrieverMode === mode.value
                                                            ? "tab-pill-active"
                                                            : "tab-pill-inactive"}`}
                                                    >
                                                        {mode.label}
                                                    </button>
                                                ))}
                                            </div>
                                            <p className="text-xs text-muted-foreground">
                                                BM25는 키워드 기반, Hybrid는 BM25 + Dense를 결합합니다.
                                            </p>
                                            {retrieverMode !== "none" && (
                                                <div className="space-y-3">
                                                    <input
                                                        type="text"
                                                        placeholder="Upload docs or paste server path (json/jsonl/txt)"
                                                        className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm"
                                                        value={docsPath}
                                                        onChange={(e) => setDocsPath(e.target.value)}
                                                    />
                                                    <p className="text-xs text-muted-foreground">
                                                        문서 경로는 API 서버 기준입니다. 업로드 버튼을 사용하면 자동 경로가 입력됩니다.
                                                        지원 포맷: .json, .jsonl, .txt.
                                                    </p>
                                                    <div className="flex flex-col gap-2">
                                                        <div className="flex flex-wrap items-center gap-2">
                                                            <input
                                                                id="retriever-docs-upload"
                                                                type="file"
                                                                accept=".json,.jsonl,.txt"
                                                                className="hidden"
                                                                onChange={handleRetrieverFileChange}
                                                            />
                                                            <label
                                                                htmlFor="retriever-docs-upload"
                                                                className="px-3 py-1.5 rounded-md text-sm border bg-secondary text-secondary-foreground cursor-pointer hover:bg-secondary/80"
                                                            >
                                                                Choose file
                                                            </label>
                                                            <button
                                                                type="button"
                                                                onClick={handleRetrieverUpload}
                                                                disabled={!retrieverFile || retrieverUploading}
                                                                className="px-3 py-1.5 rounded-md text-sm border bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                                                            >
                                                                {retrieverUploading ? "Uploading..." : "Upload"}
                                                            </button>
                                                        </div>
                                                        {retrieverFile && (
                                                            <div className="text-xs text-muted-foreground flex items-center gap-2">
                                                                <FileText className="w-3 h-3" />
                                                                <span>{retrieverFile.name}</span>
                                                                <span>{(retrieverFile.size / 1024).toFixed(1)} KB</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Performance Config */}
                                <div>
                                    <h3 className="text-sm font-medium mb-3">Performance & Batching</h3>
                                    <p className="text-xs text-muted-foreground mb-3">
                                        배치 크기를 높이면 속도가 빨라지지만 LLM 호출량/메모리 사용량과 rate limit 부담이 증가합니다.
                                    </p>
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

                                {/* Threshold Profile */}
                                <div>
                                    <h3 className="text-sm font-medium mb-3">Threshold Profile</h3>
                                    <p className="text-xs text-muted-foreground mb-3">
                                        데이터셋 threshold가 비어 있을 때 추천값을 적용합니다. 선택한 프로필에 해당하는 메트릭만 덮어씁니다.
                                    </p>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <label className="text-xs text-muted-foreground mb-1 block">
                                                Apply recommended thresholds
                                            </label>
                                            <select
                                                value={thresholdProfile}
                                                onChange={(event) => setThresholdProfile(event.target.value as "none" | "summary" | "qa")}
                                                className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm"
                                            >
                                                <option value="none">None (use dataset/default)</option>
                                                <option value="summary">Summary profile (0.90/0.85/0.90)</option>
                                                <option value="qa">QA profile (0.7/0.6 baseline)</option>
                                            </select>
                                        </div>
                                        <div className="text-xs text-muted-foreground flex items-center">
                                            Only matching metrics are overridden; others keep dataset or default values.
                                        </div>
                                    </div>
                                </div>

                                {/* Prompt Snapshot */}
                                <div>
                                    <h3 className="text-sm font-medium mb-3">Prompt Snapshot</h3>
                                    <p className="text-xs text-muted-foreground mb-3">
                                        실행 시점의 프롬프트/설정을 저장해 추후 비교와 리포트, Phoenix/Langfuse 기록에 활용합니다.
                                    </p>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <label className="text-xs text-muted-foreground mb-1 block">Prompt Set Name</label>
                                            <input
                                                type="text"
                                                placeholder="e.g., prod-sys-v3"
                                                className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm"
                                                value={promptSetName}
                                                onChange={(e) => setPromptSetName(e.target.value)}
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs text-muted-foreground mb-1 block">Prompt Set Description</label>
                                            <input
                                                type="text"
                                                placeholder="Optional description for this prompt set"
                                                className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm"
                                                value={promptSetDescription}
                                                onChange={(e) => setPromptSetDescription(e.target.value)}
                                            />
                                        </div>
                                        <div className="md:col-span-2">
                                            <label className="text-xs text-muted-foreground mb-1 block">System Prompt (target LLM)</label>
                                            <textarea
                                                rows={4}
                                                placeholder="Paste the system prompt used in your production LLM"
                                                className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm"
                                                value={systemPrompt}
                                                onChange={(e) => setSystemPrompt(e.target.value)}
                                            />
                                            <div className="mt-2">
                                                <label className="text-xs text-muted-foreground mb-1 block">System Prompt Name</label>
                                                <input
                                                    type="text"
                                                    placeholder="Optional label (e.g., sys-v2)"
                                                    className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm"
                                                    value={systemPromptName}
                                                    onChange={(e) => setSystemPromptName(e.target.value)}
                                                />
                                            </div>
                                        </div>
                                        <div className="md:col-span-2">
                                            <label className="text-xs text-muted-foreground mb-1 block">Ragas Prompt Overrides (YAML)</label>
                                            <textarea
                                                rows={6}
                                                placeholder={"metrics:\n  faithfulness: |\n    ...\n  answer_relevancy: |\n    ..."}
                                                className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm font-mono"
                                                value={ragasPromptsYaml}
                                                onChange={(e) => setRagasPromptsYaml(e.target.value)}
                                            />
                                            <p className="text-xs text-muted-foreground mt-2">
                                                Provide metric prompt templates to override Ragas defaults. Leave empty to skip.
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Domain Memory */}
                                <div>
                                    <h3 className="text-sm font-medium mb-3">Domain Memory</h3>
                                    <p className="text-xs text-muted-foreground mb-3">
                                        평가 결과를 도메인 메모리에 학습하고, 실행 전에 컨텍스트를 보강합니다.
                                    </p>
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

                                {/* Stage Events */}
                                <div>
                                    <h3 className="text-sm font-medium mb-3">Stage Event Trace</h3>
                                    <p className="text-xs text-muted-foreground mb-3">
                                        입력/검색/출력 단계 이벤트를 저장해 Waterfall/Stage 메트릭 시각화의 기반을
                                        만듭니다.
                                    </p>
                                    <div
                                        onClick={() => setStageStore(!stageStore)}
                                        className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${stageStore
                                            ? "border-primary bg-primary/5"
                                            : "border-border hover:border-primary/30"}`}
                                    >
                                        <div className={`w-5 h-5 rounded border flex items-center justify-center ${stageStore ? "bg-primary border-primary" : "border-muted-foreground"}`}>
                                            {stageStore && <CheckCircle2 className="w-3 h-3 text-primary-foreground" />}
                                        </div>
                                        <div>
                                            <p className="font-medium text-sm">Store Stage Events</p>
                                            <p className="text-xs text-muted-foreground">
                                                Stage 이벤트/메트릭 API에 바로 사용할 수 있습니다.
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Tracker */}
                                <div>
                                    <h3 className="text-sm font-medium mb-3">Observability Tracker</h3>
                                    <p className="text-xs text-muted-foreground mb-3">
                                        Phoenix는 로컬 UI에서 trace/metrics를 확인합니다. Langfuse/MLflow는 별도 설정이 필요합니다.
                                    </p>
                                    <div className="tab-shell">
                                        {(["none", "phoenix", "langfuse", "mlflow"] as const).map(t => (
                                            <button
                                                key={t}
                                                onClick={() => setTracker(t)}
                                                className={`tab-pill capitalize ${tracker === t
                                                    ? "tab-pill-active"
                                                    : "tab-pill-inactive"}`}
                                            >
                                                {t}
                                            </button>
                                        ))}
                                    </div>
                                    {tracker === "phoenix" && (
                                        <div className="mt-3 space-y-2 text-xs text-muted-foreground animate-in fade-in slide-in-from-top-1">
                                            {phoenixUiUrl && (
                                                <a
                                                    href={phoenixUiUrl}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="inline-flex items-center gap-1 text-primary hover:underline"
                                                >
                                                    Open Phoenix UI
                                                    <ExternalLink className="w-3 h-3" />
                                                </a>
                                            )}
                                            <p>
                                                Phoenix 서버가 없다면{" "}
                                                <code className="px-1 py-0.5 rounded bg-muted font-mono text-[11px]">
                                                    docker run -p 6006:6006 arizephoenix/phoenix:latest
                                                </code>{" "}
                                                로 실행하세요.
                                            </p>
                                            <p>Dataset/Experiment 업로드 및 Prompt manifest는 CLI에서만 지원됩니다.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </section>

                    {/* Action */}
                    <div className="flex justify-end">
                        <div className="flex items-center gap-3 ml-auto">
                            <button
                                onClick={handleCopyCli}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-background hover:bg-secondary transition-colors text-sm font-medium"
                                title="Copy as CLI command"
                            >
                                {copyStatus === "success" ? (
                                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                                ) : copyStatus === "error" ? (
                                    <AlertCircle className="w-4 h-4 text-rose-500" />
                                ) : (
                                    <Terminal className="w-4 h-4 text-muted-foreground" />
                                )}
                                {copyStatus === "success" ? "Copied!" : "Copy CLI"}
                            </button>
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
                            <div className="mt-2 text-xs text-muted-foreground flex items-center justify-center gap-2">
                                <span>{progressStats.total > 0 ? `${progressStats.current}/${progressStats.total}` : `${progressStats.current}`}</span>
                                <span>•</span>
                                <span>ETA {formatEta(progressStats.etaSeconds)}</span>
                                {progressStats.rate != null && (
                                    <>
                                        <span>•</span>
                                        <span>{progressStats.rate.toFixed(2)}/s</span>
                                    </>
                                )}
                            </div>
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
