import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import { fetchConfig, type SystemConfig } from "../services/api";
import { Settings as SettingsIcon, Cpu, Globe, Activity, Shield } from "lucide-react";

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

    useEffect(() => {
        async function loadConfig() {
            try {
                const data = await fetchConfig();
                setConfig(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load config");
            } finally {
                setLoading(false);
            }
        }
        loadConfig();
    }, []);

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
                        </section>
                    ))}
                </div>
            </div>
        </Layout>
    );
}
