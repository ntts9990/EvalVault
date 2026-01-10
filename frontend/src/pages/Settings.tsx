import { useEffect, useMemo, useState } from "react";
import { Layout } from "../components/Layout";
import {
    fetchConfig,
    fetchModels,
    updateConfig,
    type ModelItem,
    type SystemConfig,
} from "../services/api";
import { Settings as SettingsIcon, Cpu, Globe, Activity, Shield, ExternalLink } from "lucide-react";
import { getPhoenixUiUrl } from "../utils/phoenix";

type ConfigValue = string | number | boolean | null | undefined;

const formatValue = (value: ConfigValue) => {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "boolean") return value ? "Enabled" : "Disabled";
    return String(value);
};

export function Settings() {
    const [config, setConfig] = useState<SystemConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [providerDraft, setProviderDraft] = useState<"ollama" | "openai" | "vllm">("ollama");
    const [modelDraft, setModelDraft] = useState("");
    const [modelOptions, setModelOptions] = useState<ModelItem[]>([]);
    const [modelsLoading, setModelsLoading] = useState(false);
    const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "success" | "error">("idle");
    const [saveError, setSaveError] = useState<string | null>(null);
    const [openaiConsent, setOpenaiConsent] = useState(false);

    const activeModelValue = useMemo(() => {
        if (!config) return "";
        if (providerDraft === "openai") return String(config.openai_model || "");
        if (providerDraft === "vllm") return String(config.vllm_model || "");
        return String(config.ollama_model || "");
    }, [config, providerDraft]);

    const normalizeModelName = (provider: string, modelId: string) => {
        if (!modelId) return "";
        const prefix = `${provider}/`;
        return modelId.startsWith(prefix) ? modelId.slice(prefix.length) : modelId;
    };

    const loadModels = async (provider: "ollama" | "openai" | "vllm") => {
        setModelsLoading(true);
        try {
            const options = await fetchModels(provider);
            setModelOptions(options);
        } catch {
            setModelOptions([]);
        } finally {
            setModelsLoading(false);
        }
    };

    useEffect(() => {
        async function loadConfig() {
            try {
                const data = await fetchConfig();
                setConfig(data);
                const provider = (data.llm_provider as "ollama" | "openai" | "vllm") || "ollama";
                setProviderDraft(provider);
                setModelDraft(
                    provider === "openai"
                        ? String(data.openai_model || "")
                        : provider === "vllm"
                            ? String(data.vllm_model || "")
                            : String(data.ollama_model || "")
                );
                await loadModels(provider);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load config");
            } finally {
                setLoading(false);
            }
        }
        loadConfig();
    }, []);

    useEffect(() => {
        if (saveStatus !== "success") return;
        const timeout = window.setTimeout(() => setSaveStatus("idle"), 2000);
        return () => window.clearTimeout(timeout);
    }, [saveStatus]);

    const modelSelectOptions = modelOptions.map((model) => {
        const name = normalizeModelName(providerDraft, model.id);
        return { id: model.id, name: model.name, value: name };
    });

    const handleProviderChange = async (provider: "ollama" | "openai" | "vllm") => {
        setProviderDraft(provider);
        setOpenaiConsent(false);
        setSaveStatus("idle");
        setSaveError(null);
        await loadModels(provider);
        const fallback =
            provider === "openai"
                ? config?.openai_model
                : provider === "vllm"
                    ? config?.vllm_model
                    : config?.ollama_model;
        setModelDraft(String(fallback || ""));
    };

    const handleSave = async () => {
        if (!config) return;
        setSaveStatus("saving");
        setSaveError(null);
        try {
            const payload: Record<string, string> = {
                llm_provider: providerDraft,
            };
            if (providerDraft === "openai") {
                payload.openai_model = modelDraft;
            } else if (providerDraft === "vllm") {
                payload.vllm_model = modelDraft;
            } else {
                payload.ollama_model = modelDraft;
            }
            const updated = await updateConfig(payload);
            setConfig(updated);
            setSaveStatus("success");
        } catch (err) {
            setSaveStatus("error");
            setSaveError(err instanceof Error ? err.message : "Failed to update settings");
        }
    };

    if (loading) {
        return (
            <Layout>
                <div className="flex items-center justify-center h-[50vh]">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            </Layout>
        );
    }

    if (error || !config) {
        return (
            <Layout>
                <div className="flex flex-col items-center justify-center h-[50vh] text-destructive gap-4">
                    <p className="text-xl font-bold">Settings Error</p>
                    <p>{error || "Configuration unavailable"}</p>
                </div>
            </Layout>
        );
    }

    const phoenixUiUrl = getPhoenixUiUrl(config.phoenix_endpoint);
    const sections = [
        {
            title: "LLM Provider",
            icon: Cpu,
            rows: [
                { label: "Provider", value: config.llm_provider },
                { label: "Profile", value: config.evalvault_profile },
            ],
        },
        {
            title: "OpenAI",
            icon: Globe,
            rows: [
                { label: "Model", value: config.openai_model },
                { label: "Embedding", value: config.openai_embedding_model },
                { label: "Base URL", value: config.openai_base_url },
            ],
        },
        {
            title: "vLLM",
            icon: Globe,
            rows: [
                { label: "Model", value: config.vllm_model },
                { label: "Embedding", value: config.vllm_embedding_model },
                { label: "Base URL", value: config.vllm_base_url },
                { label: "Embedding Base URL", value: config.vllm_embedding_base_url },
                { label: "Timeout (s)", value: config.vllm_timeout },
            ],
        },
        {
            title: "Ollama",
            icon: Activity,
            rows: [
                { label: "Model", value: config.ollama_model },
                { label: "Embedding", value: config.ollama_embedding_model },
                { label: "Base URL", value: config.ollama_base_url },
                { label: "Timeout (s)", value: config.ollama_timeout },
                { label: "Think Level", value: config.ollama_think_level },
            ],
        },
        {
            title: "Tracking",
            icon: Shield,
            rows: [
                { label: "Default Tracker", value: config.tracker_provider },
                { label: "Langfuse Host", value: config.langfuse_host },
                { label: "Phoenix Enabled", value: config.phoenix_enabled },
                { label: "Phoenix Endpoint", value: config.phoenix_endpoint },
            ],
        },
    ];

    return (
        <Layout>
            <div className="max-w-5xl mx-auto pb-20">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold tracking-tight mb-2 flex items-center gap-2">
                        <SettingsIcon className="w-6 h-6 text-primary" />
                        Settings
                    </h1>
                    <p className="text-muted-foreground">Runtime configuration loaded from the backend.</p>
                </div>

                <section className="surface-panel p-6 mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <Cpu className="w-5 h-5 text-primary" />
                        <h2 className="text-lg font-semibold">LLM 기본 제공자</h2>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                        <div className="tab-shell">
                            {(["ollama", "openai", "vllm"] as const).map((provider) => (
                                <button
                                    key={provider}
                                    type="button"
                                    onClick={() => handleProviderChange(provider)}
                                    className={`tab-pill capitalize ${providerDraft === provider
                                        ? "tab-pill-active"
                                        : "tab-pill-inactive"
                                        }`}
                                >
                                    {provider}
                                </button>
                            ))}
                        </div>
                        <span className="text-xs text-muted-foreground">
                            분석 실험실/리포트 기본 모델에 적용됩니다.
                        </span>
                    </div>

                    <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-muted-foreground uppercase">
                                기본 모델
                            </label>
                            {modelsLoading ? (
                                <div className="text-sm text-muted-foreground">모델 목록을 불러오는 중...</div>
                            ) : modelSelectOptions.length > 0 ? (
                                <select
                                    value={modelDraft || activeModelValue}
                                    onChange={(event) => setModelDraft(event.target.value)}
                                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                                >
                                    {modelSelectOptions.map((option) => (
                                        <option key={option.id} value={option.value}>
                                            {option.name}
                                        </option>
                                    ))}
                                </select>
                            ) : (
                                <input
                                    value={modelDraft}
                                    onChange={(event) => setModelDraft(event.target.value)}
                                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                                    placeholder="예: gemma3:1b"
                                />
                            )}
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-muted-foreground uppercase">
                                적용 상태
                            </label>
                            <div className="text-sm text-muted-foreground">
                                기본값: {activeModelValue || "미설정"}
                            </div>
                            {providerDraft === "openai" && (
                                <label className="flex items-center gap-2 text-xs text-muted-foreground">
                                    <input
                                        type="checkbox"
                                        checked={openaiConsent}
                                        onChange={(event) => setOpenaiConsent(event.target.checked)}
                                    />
                                    OpenAI 사용 시 비용이 발생하는 것에 동의합니다.
                                </label>
                            )}
                        </div>
                    </div>

                    <div className="mt-4 flex flex-wrap items-center gap-3">
                        <button
                            type="button"
                            onClick={handleSave}
                            disabled={
                                saveStatus === "saving"
                                || (providerDraft === "openai" && !openaiConsent)
                                || !modelDraft
                            }
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50"
                        >
                            {saveStatus === "saving" ? "저장 중..." : "설정 적용"}
                        </button>
                        {saveStatus === "success" && (
                            <span className="text-xs text-emerald-600">적용 완료</span>
                        )}
                        {saveStatus === "error" && (
                            <span className="text-xs text-rose-600">{saveError}</span>
                        )}
                        <span className="text-xs text-muted-foreground">
                            서버 재시작 시 기본 설정으로 돌아갈 수 있습니다.
                        </span>
                    </div>
                </section>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {sections.map((section) => (
                        <section key={section.title} className="surface-panel p-6">
                            <div className="flex items-center gap-2 mb-4">
                                <section.icon className="w-5 h-5 text-primary" />
                                <h2 className="text-lg font-semibold">{section.title}</h2>
                            </div>
                            <div className="space-y-3">
                                {section.rows.map((row) => (
                                    <div key={row.label} className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground">{row.label}</span>
                                        <span className="font-medium text-foreground text-right max-w-[60%] truncate">
                                            {formatValue(row.value as ConfigValue)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                            {section.title === "Tracking" && phoenixUiUrl && (
                                <div className="mt-4">
                                    <a
                                        href={phoenixUiUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                                    >
                                        Open Phoenix UI
                                        <ExternalLink className="w-4 h-4" />
                                    </a>
                                </div>
                            )}
                        </section>
                    ))}
                </div>
            </div>
        </Layout>
    );
}
