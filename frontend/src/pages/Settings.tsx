import { useEffect, useMemo, useState, type ComponentType } from "react";
import { Layout } from "../components/Layout";
import {
    fetchConfig,
    fetchConfigProfiles,
    fetchModels,
    fetchMetricSpecs,
    updateConfig,
    type ConfigProfile,
    type ConfigUpdateRequest,
    type MetricSpec,
    type ModelItem,
    type SystemConfig,
} from "../services/api";
import {
    Settings as SettingsIcon,
    Cpu,
    Globe,
    Activity,
    Shield,
    Database,
    Sliders,
    ExternalLink,
    BookOpen,
} from "lucide-react";
import { getPhoenixUiUrl } from "../utils/phoenix";

type ProviderKey = "ollama" | "openai" | "vllm";

type DraftValue = string | boolean;
type DraftState = Partial<Record<keyof ConfigUpdateRequest, DraftValue>>;

type FieldType = "text" | "number" | "toggle" | "select" | "model" | "provider";

type FieldOption = {
    label: string;
    value: string;
};

type FieldDefinition = {
    key: keyof ConfigUpdateRequest;
    label: string;
    type: FieldType;
    placeholder?: string;
    hint?: string;
    options?: FieldOption[];
    provider?: ProviderKey;
    nullable?: boolean;
    min?: number;
    max?: number;
    step?: number;
};

type SectionDefinition = {
    id: string;
    title: string;
    description?: string;
    note?: string;
    icon?: ComponentType<{ className?: string }>;
    fields: FieldDefinition[];
};

const INPUT_CLASS = "w-full px-3 py-2 rounded-lg border border-border bg-background text-sm";
const PROVIDERS: ProviderKey[] = ["ollama", "openai", "vllm"];

const FALLBACK_PROVIDER_OPTIONS: FieldOption[] = [
    { label: "사용 안 함", value: "" },
    { label: "Ollama", value: "ollama" },
    { label: "OpenAI", value: "openai" },
    { label: "vLLM", value: "vllm" },
];

const TRACKER_OPTIONS: FieldOption[] = [
    { label: "사용 안 함", value: "none" },
    { label: "Langfuse", value: "langfuse" },
    { label: "Phoenix", value: "phoenix" },
    { label: "MLflow", value: "mlflow" },
];

const FIELD_DEFINITIONS: Record<string, FieldDefinition> = {
    evalvault_profile: {
        key: "evalvault_profile",
        label: "모델 프로필",
        type: "select",
        nullable: true,
        hint: "config/models.yaml의 프로필을 적용합니다.",
    },
    llm_provider: {
        key: "llm_provider",
        label: "기본 제공자",
        type: "provider",
    },
    faithfulness_fallback_provider: {
        key: "faithfulness_fallback_provider",
        label: "Faithfulness Fallback 제공자",
        type: "select",
        nullable: true,
    },
    faithfulness_fallback_model: {
        key: "faithfulness_fallback_model",
        label: "Faithfulness Fallback 모델",
        type: "text",
        placeholder: "예: gpt-5-mini",
        nullable: true,
    },
    openai_model: {
        key: "openai_model",
        label: "모델",
        type: "model",
        provider: "openai",
        placeholder: "gpt-5-mini",
    },
    openai_embedding_model: {
        key: "openai_embedding_model",
        label: "임베딩 모델",
        type: "text",
        placeholder: "text-embedding-3-small",
    },
    openai_base_url: {
        key: "openai_base_url",
        label: "Base URL",
        type: "text",
        placeholder: "https://api.openai.com/v1",
        nullable: true,
    },
    ollama_model: {
        key: "ollama_model",
        label: "모델",
        type: "model",
        provider: "ollama",
        placeholder: "gemma3:1b",
    },
    ollama_embedding_model: {
        key: "ollama_embedding_model",
        label: "임베딩 모델",
        type: "text",
        placeholder: "qwen3-embedding:0.6b",
    },
    ollama_base_url: {
        key: "ollama_base_url",
        label: "Base URL",
        type: "text",
        placeholder: "http://localhost:11434",
    },
    ollama_timeout: {
        key: "ollama_timeout",
        label: "타임아웃 (초)",
        type: "number",
        min: 1,
        step: 1,
    },
    ollama_think_level: {
        key: "ollama_think_level",
        label: "Think Level",
        type: "text",
        placeholder: "medium",
        nullable: true,
    },
    ollama_tool_models: {
        key: "ollama_tool_models",
        label: "Tool 모델 Allowlist",
        type: "text",
        placeholder: "model-a, model-b",
        nullable: true,
    },
    vllm_model: {
        key: "vllm_model",
        label: "모델",
        type: "model",
        provider: "vllm",
        placeholder: "gpt-oss-120b",
    },
    vllm_embedding_model: {
        key: "vllm_embedding_model",
        label: "임베딩 모델",
        type: "text",
        placeholder: "qwen3-embedding:0.6b",
    },
    vllm_base_url: {
        key: "vllm_base_url",
        label: "Base URL",
        type: "text",
        placeholder: "http://localhost:8001/v1",
    },
    vllm_embedding_base_url: {
        key: "vllm_embedding_base_url",
        label: "Embedding Base URL",
        type: "text",
        nullable: true,
    },
    vllm_timeout: {
        key: "vllm_timeout",
        label: "타임아웃 (초)",
        type: "number",
        min: 1,
        step: 1,
    },
    tracker_provider: {
        key: "tracker_provider",
        label: "기본 트래커",
        type: "select",
    },
    phoenix_enabled: {
        key: "phoenix_enabled",
        label: "Phoenix 사용",
        type: "toggle",
    },
    phoenix_endpoint: {
        key: "phoenix_endpoint",
        label: "Phoenix Endpoint",
        type: "text",
        placeholder: "http://localhost:6006/v1/traces",
    },
    phoenix_sample_rate: {
        key: "phoenix_sample_rate",
        label: "Phoenix 샘플링 비율",
        type: "number",
        min: 0,
        max: 1,
        step: 0.1,
    },
    langfuse_host: {
        key: "langfuse_host",
        label: "Langfuse Host",
        type: "text",
        placeholder: "https://cloud.langfuse.com",
    },
    mlflow_tracking_uri: {
        key: "mlflow_tracking_uri",
        label: "MLflow Tracking URI",
        type: "text",
        nullable: true,
    },
    mlflow_experiment_name: {
        key: "mlflow_experiment_name",
        label: "MLflow Experiment",
        type: "text",
    },
    anthropic_model: {
        key: "anthropic_model",
        label: "모델",
        type: "text",
        placeholder: "claude-3-5-sonnet-20241022",
    },
    anthropic_thinking_budget: {
        key: "anthropic_thinking_budget",
        label: "Thinking Budget",
        type: "number",
        nullable: true,
        min: 0,
        step: 100,
    },
    azure_endpoint: {
        key: "azure_endpoint",
        label: "Azure Endpoint",
        type: "text",
        nullable: true,
    },
    azure_deployment: {
        key: "azure_deployment",
        label: "Azure Deployment",
        type: "text",
        nullable: true,
    },
    azure_embedding_deployment: {
        key: "azure_embedding_deployment",
        label: "Azure Embedding Deployment",
        type: "text",
        nullable: true,
    },
    azure_api_version: {
        key: "azure_api_version",
        label: "Azure API Version",
        type: "text",
        placeholder: "2024-02-15-preview",
        nullable: true,
    },
    evalvault_db_path: {
        key: "evalvault_db_path",
        label: "EvalVault DB 경로",
        type: "text",
        placeholder: "data/db/evalvault.db",
    },
    evalvault_memory_db_path: {
        key: "evalvault_memory_db_path",
        label: "Domain Memory DB 경로",
        type: "text",
        placeholder: "data/db/evalvault_memory.db",
    },
    postgres_host: {
        key: "postgres_host",
        label: "Postgres Host",
        type: "text",
        nullable: true,
    },
    postgres_port: {
        key: "postgres_port",
        label: "Postgres Port",
        type: "number",
        min: 1,
        step: 1,
    },
    postgres_database: {
        key: "postgres_database",
        label: "Postgres Database",
        type: "text",
        nullable: true,
    },
    postgres_user: {
        key: "postgres_user",
        label: "Postgres User",
        type: "text",
        nullable: true,
    },
    cors_origins: {
        key: "cors_origins",
        label: "CORS Origins",
        type: "text",
        placeholder: "http://localhost:5173,http://127.0.0.1:5173",
    },
};

const SECTION_FIELDS = {
    llm: [
        "evalvault_profile",
        "llm_provider",
        "faithfulness_fallback_provider",
        "faithfulness_fallback_model",
    ],
    openai: ["openai_model", "openai_embedding_model", "openai_base_url"],
    ollama: [
        "ollama_model",
        "ollama_embedding_model",
        "ollama_base_url",
        "ollama_timeout",
        "ollama_think_level",
        "ollama_tool_models",
    ],
    vllm: [
        "vllm_model",
        "vllm_embedding_model",
        "vllm_base_url",
        "vllm_embedding_base_url",
        "vllm_timeout",
    ],
    tracking: [
        "tracker_provider",
        "phoenix_enabled",
        "phoenix_endpoint",
        "phoenix_sample_rate",
        "langfuse_host",
        "mlflow_tracking_uri",
        "mlflow_experiment_name",
    ],
    anthropic: ["anthropic_model", "anthropic_thinking_budget"],
    azure: [
        "azure_endpoint",
        "azure_deployment",
        "azure_embedding_deployment",
        "azure_api_version",
    ],
    storage: [
        "evalvault_db_path",
        "evalvault_memory_db_path",
        "postgres_host",
        "postgres_port",
        "postgres_database",
        "postgres_user",
        "cors_origins",
    ],
} as const;

const FIELD_META = Object.values(FIELD_DEFINITIONS);

const normalizeModelName = (provider: ProviderKey, modelId: string) => {
    const prefix = `${provider}/`;
    return modelId.startsWith(prefix) ? modelId.slice(prefix.length) : modelId;
};

const getStringValue = (value: DraftValue | undefined) => {
    if (typeof value === "string") return value;
    if (value === undefined) return "";
    return String(value);
};

const buildDraftFromConfig = (config: SystemConfig): DraftState => {
    const next: DraftState = {};
    FIELD_META.forEach((field) => {
        const value = config[field.key];
        if (field.type === "toggle") {
            next[field.key] = Boolean(value);
            return;
        }
        if (value === null || value === undefined) {
            next[field.key] = "";
            return;
        }
        next[field.key] = String(value);
    });
    return next;
};

const parseDraftValue = (field: FieldDefinition, raw: DraftValue | undefined) => {
    if (field.type === "toggle") return Boolean(raw);

    const textValue = typeof raw === "string" ? raw.trim() : "";
    if (field.nullable && textValue === "") return null;

    if (field.type === "number") {
        if (textValue === "") return field.nullable ? null : "";
        const numeric = Number(textValue);
        return Number.isNaN(numeric) ? textValue : numeric;
    }

    return textValue;
};

const normalizeCurrentValue = (field: FieldDefinition, value: unknown) => {
    if (field.type === "toggle") return Boolean(value);
    if (value === null || value === undefined) return field.nullable ? null : "";
    if (field.type === "number") {
        const numeric = typeof value === "number" ? value : Number(value);
        return Number.isNaN(numeric) ? value : numeric;
    }
    return String(value);
};

export function Settings() {
    const [config, setConfig] = useState<SystemConfig | null>(null);
    const [draft, setDraft] = useState<DraftState>({});
    const [profiles, setProfiles] = useState<ConfigProfile[]>([]);
    const [modelOptions, setModelOptions] = useState<Record<ProviderKey, ModelItem[]>>({
        ollama: [],
        openai: [],
        vllm: [],
    });
    const [modelsLoading, setModelsLoading] = useState<Record<ProviderKey, boolean>>({
        ollama: false,
        openai: false,
        vllm: false,
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "success" | "error">("idle");
    const [saveError, setSaveError] = useState<string | null>(null);
    const [openaiConsent, setOpenaiConsent] = useState(false);
    const [metricSpecs, setMetricSpecs] = useState<MetricSpec[]>([]);
    const [metricsLoading, setMetricsLoading] = useState(false);
    const [metricsError, setMetricsError] = useState<string | null>(null);

    const profileOptions = useMemo<FieldOption[]>(() => {
        const baseOptions = [{ label: "사용 안 함", value: "" }];
        if (profiles.length === 0) return baseOptions;

        const mapped = profiles.map((profile) => ({
            label: `${profile.name} · ${profile.llm_provider}/${profile.llm_model}`,
            value: profile.name,
        }));
        return [...baseOptions, ...mapped];
    }, [profiles]);

    const sections = useMemo<SectionDefinition[]>(() => {
        const selectOverrides: Record<string, FieldOption[] | undefined> = {
            evalvault_profile: profileOptions,
            faithfulness_fallback_provider: FALLBACK_PROVIDER_OPTIONS,
            tracker_provider: TRACKER_OPTIONS,
        };

        const resolveFields = (keys: readonly string[]) =>
            keys
                .map((key) => {
                    const base = FIELD_DEFINITIONS[key];
                    if (!base) return null;
                    const options = selectOverrides[key] ?? base.options;
                    return options ? { ...base, options } : base;
                })
                .filter((field): field is FieldDefinition => Boolean(field));

        return [
            {
                id: "llm",
                title: "기본 LLM",
                description: "웹 UI 기본 제공자/프로필 및 fallback을 관리합니다.",
                icon: Cpu,
                fields: resolveFields(SECTION_FIELDS.llm),
            },
            {
                id: "openai",
                title: "OpenAI",
                note: "OpenAI API 키는 환경변수(.env)에서 설정하세요.",
                icon: Globe,
                fields: resolveFields(SECTION_FIELDS.openai),
            },
            {
                id: "ollama",
                title: "Ollama",
                icon: Activity,
                fields: resolveFields(SECTION_FIELDS.ollama),
            },
            {
                id: "vllm",
                title: "vLLM",
                icon: Sliders,
                fields: resolveFields(SECTION_FIELDS.vllm),
            },
            {
                id: "tracking",
                title: "Tracing / Tracking",
                note: "Langfuse/Phoenix 키는 환경변수에서 설정합니다.",
                icon: Shield,
                fields: resolveFields(SECTION_FIELDS.tracking),
            },
            {
                id: "anthropic",
                title: "Anthropic",
                icon: Globe,
                fields: resolveFields(SECTION_FIELDS.anthropic),
            },
            {
                id: "azure",
                title: "Azure OpenAI",
                icon: Globe,
                fields: resolveFields(SECTION_FIELDS.azure),
            },
            {
                id: "storage",
                title: "Storage / Network",
                icon: Database,
                fields: resolveFields(SECTION_FIELDS.storage),
            },
        ];
    }, [profileOptions]);

    const pendingUpdates = useMemo(() => {
        if (!config) return {} as ConfigUpdateRequest;

        const updates: ConfigUpdateRequest = {};
        FIELD_META.forEach((field) => {
            const raw = draft[field.key];
            const parsed = parseDraftValue(field, raw);
            const current = normalizeCurrentValue(field, config[field.key]);
            if (!Object.is(parsed, current)) {
                (updates as Record<string, unknown>)[field.key] = parsed;
            }
        });
        return updates;
    }, [config, draft]);

    const hasChanges = Object.keys(pendingUpdates).length > 0;
    const draftProvider = (draft.llm_provider as ProviderKey)
        || (config?.llm_provider as ProviderKey)
        || "ollama";
    const requiresOpenAIConsent = config?.llm_provider !== "openai" && draftProvider === "openai";

    useEffect(() => {
        if (saveStatus !== "success") return;
        const timeout = window.setTimeout(() => setSaveStatus("idle"), 2000);
        return () => window.clearTimeout(timeout);
    }, [saveStatus]);

    useEffect(() => {
        if (draftProvider !== "openai") {
            setOpenaiConsent(false);
        }
    }, [draftProvider]);

    useEffect(() => {
        async function loadInitial() {
            setLoading(true);
            setError(null);
            try {
                const data = await fetchConfig();
                setConfig(data);
                setDraft(buildDraftFromConfig(data));
            } catch (err) {
                setError(err instanceof Error ? err.message : "설정을 불러오지 못했습니다.");
            } finally {
                setLoading(false);
            }
        }

        async function loadProfiles() {
            try {
                const data = await fetchConfigProfiles();
                setProfiles(data);
            } catch {
                setProfiles([]);
            }
        }

        async function loadModelOptions(provider: ProviderKey) {
            setModelsLoading((prev) => ({ ...prev, [provider]: true }));
            try {
                const options = await fetchModels(provider);
                setModelOptions((prev) => ({ ...prev, [provider]: options }));
            } catch {
                setModelOptions((prev) => ({ ...prev, [provider]: [] }));
            } finally {
                setModelsLoading((prev) => ({ ...prev, [provider]: false }));
            }
        }

        loadInitial();
        loadProfiles();
        PROVIDERS.forEach((provider) => {
            loadModelOptions(provider);
        });
    }, []);

    useEffect(() => {
        async function loadMetrics() {
            setMetricsLoading(true);
            setMetricsError(null);
            try {
                const specs = await fetchMetricSpecs();
                setMetricSpecs(specs);
            } catch {
                setMetricsError("메트릭 정보를 불러오지 못했습니다.");
            } finally {
                setMetricsLoading(false);
            }
        }

        loadMetrics();
    }, []);

    const updateDraftValue = (key: keyof ConfigUpdateRequest, value: DraftValue) => {
        setDraft((prev) => ({ ...prev, [key]: value }));
    };

    const handleSave = async () => {
        if (!config || !hasChanges) return;
        setSaveStatus("saving");
        setSaveError(null);
        try {
            const updated = await updateConfig(pendingUpdates);
            setConfig(updated);
            setDraft(buildDraftFromConfig(updated));
            setSaveStatus("success");
        } catch (err) {
            setSaveStatus("error");
            setSaveError(err instanceof Error ? err.message : "설정 업데이트 실패");
        }
    };

    const handleReset = () => {
        if (!config) return;
        setDraft(buildDraftFromConfig(config));
        setSaveStatus("idle");
        setSaveError(null);
    };

    const renderFieldInput = (field: FieldDefinition) => {
        const rawValue = draft[field.key];
        const value = getStringValue(rawValue);

        if (field.type === "provider") {
            return (
                <div className="tab-shell">
                    {PROVIDERS.map((provider) => (
                        <button
                            key={provider}
                            type="button"
                            onClick={() => updateDraftValue("llm_provider", provider)}
                            className={`tab-pill capitalize ${draftProvider === provider
                                ? "tab-pill-active"
                                : "tab-pill-inactive"
                                }`}
                        >
                            {provider}
                        </button>
                    ))}
                </div>
            );
        }

        if (field.type === "toggle") {
            const isEnabled = Boolean(rawValue);
            return (
                <label className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                    <input
                        type="checkbox"
                        checked={isEnabled}
                        onChange={(event) => updateDraftValue(field.key, event.target.checked)}
                    />
                    {isEnabled ? "Enabled" : "Disabled"}
                </label>
            );
        }

        if (field.type === "select") {
            return (
                <select
                    className={INPUT_CLASS}
                    value={value}
                    onChange={(event) => updateDraftValue(field.key, event.target.value)}
                >
                    {(field.options || []).map((option) => (
                        <option key={`${field.key}-${option.value}`} value={option.value}>
                            {option.label}
                        </option>
                    ))}
                </select>
            );
        }

        if (field.type === "model" && field.provider) {
            const provider = field.provider;
            const providerModels = modelOptions[provider] || [];
            const isLoading = modelsLoading[provider];
            const options = providerModels.map((model) => ({
                value: normalizeModelName(provider, model.id),
                label: model.name,
            }));
            const hasValue = value !== "";
            if (hasValue && !options.some((option) => option.value === value)) {
                options.unshift({ value, label: `${value} (custom)` });
            }

            if (isLoading) {
                return <div className="text-sm text-muted-foreground">모델 목록을 불러오는 중...</div>;
            }

            if (options.length > 0) {
                return (
                    <select
                        className={INPUT_CLASS}
                        value={value}
                        onChange={(event) => updateDraftValue(field.key, event.target.value)}
                    >
                        {options.map((option) => (
                            <option key={`${field.key}-${option.value}`} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                );
            }
        }

        return (
            <input
                type={field.type === "number" ? "number" : "text"}
                className={INPUT_CLASS}
                placeholder={field.placeholder}
                value={value}
                min={field.min}
                max={field.max}
                step={field.step}
                onChange={(event) => updateDraftValue(field.key, event.target.value)}
            />
        );
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
                    <p className="text-xl font-bold">설정 오류</p>
                    <p>{error || "설정 정보를 불러오지 못했습니다."}</p>
                </div>
            </Layout>
        );
    }

    const phoenixEndpointDraft = getStringValue(draft.phoenix_endpoint);
    const phoenixUiUrl = getPhoenixUiUrl(phoenixEndpointDraft || (config.phoenix_endpoint as string));

    return (
        <Layout>
            <div className="max-w-5xl mx-auto pb-20">
                <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight mb-2 flex items-center gap-2">
                            <SettingsIcon className="w-6 h-6 text-primary" />
                            설정
                        </h1>
                        <p className="text-muted-foreground">백엔드 런타임 설정을 편집할 수 있습니다.</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                        <button
                            type="button"
                            onClick={handleSave}
                            disabled={!hasChanges || saveStatus === "saving" || (requiresOpenAIConsent && !openaiConsent)}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50"
                        >
                            {saveStatus === "saving" ? "저장 중..." : "변경사항 저장"}
                        </button>
                        <button
                            type="button"
                            onClick={handleReset}
                            disabled={!hasChanges || saveStatus === "saving"}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-sm font-semibold text-muted-foreground disabled:opacity-50"
                        >
                            변경 취소
                        </button>
                        {saveStatus === "success" && (
                            <span className="text-xs text-emerald-600">적용 완료</span>
                        )}
                        {saveStatus === "error" && (
                            <span className="text-xs text-rose-600">{saveError}</span>
                        )}
                        {!hasChanges && (
                            <span className="text-xs text-muted-foreground">변경 사항 없음</span>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-6">
                    {sections.map((section) => (
                        <section key={section.id} className="surface-panel p-6">
                            <div className="flex items-start justify-between gap-4 mb-4">
                                <div className="flex items-center gap-2">
                                    {section.icon && (
                                        <section.icon className="w-5 h-5 text-primary" />
                                    )}
                                    <div>
                                        <h2 className="text-lg font-semibold">{section.title}</h2>
                                        {section.description && (
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {section.description}
                                            </p>
                                        )}
                                    </div>
                                </div>
                                {section.id === "tracking" && phoenixUiUrl && (
                                    <a
                                        href={phoenixUiUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                                    >
                                        Phoenix UI 열기
                                        <ExternalLink className="w-4 h-4" />
                                    </a>
                                )}
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {section.fields.map((field) => (
                                    <div key={field.key} className="space-y-2">
                                        <label className="text-xs font-semibold text-muted-foreground uppercase">
                                            {field.label}
                                        </label>
                                        {renderFieldInput(field)}
                                        {field.hint && (
                                            <p className="text-xs text-muted-foreground">{field.hint}</p>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {section.id === "llm" && draftProvider === "openai" && (
                                <div className="mt-4 text-xs text-muted-foreground">
                                    OpenAI 사용 시 비용이 발생합니다. 기본 제공자를 OpenAI로 변경하려면 동의가 필요합니다.
                                </div>
                            )}

                            {section.id === "llm" && requiresOpenAIConsent && (
                                <label className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
                                    <input
                                        type="checkbox"
                                        checked={openaiConsent}
                                        onChange={(event) => setOpenaiConsent(event.target.checked)}
                                    />
                                    OpenAI 사용 시 비용이 발생하는 것에 동의합니다.
                                </label>
                            )}

                            {section.note && (
                                <p className="text-xs text-muted-foreground mt-4">{section.note}</p>
                            )}
                        </section>
                    ))}
                </div>

                <section className="surface-panel p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <BookOpen className="w-5 h-5 text-primary" />
                        <div>
                            <h2 className="text-lg font-semibold">메트릭 카탈로그</h2>
                            <p className="text-xs text-muted-foreground mt-1">
                                시스템에서 사용 가능한 평가 지표 명세입니다.
                            </p>
                        </div>
                    </div>

                    {metricsLoading && (
                        <div className="text-sm text-muted-foreground py-8 text-center flex flex-col items-center gap-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                            <span>메트릭 정보를 불러오는 중...</span>
                        </div>
                    )}

                    {metricsError && (
                        <div className="text-sm text-rose-600 py-4 text-center bg-rose-50/50 rounded-lg border border-rose-100">
                            {metricsError}
                        </div>
                    )}

                    {!metricsLoading && !metricsError && (
                        <div className="overflow-hidden rounded-lg border border-border">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-muted/30 text-xs text-muted-foreground uppercase">
                                    <tr>
                                        <th className="py-2.5 px-4 font-semibold w-[25%]">이름 / 그룹</th>
                                        <th className="py-2.5 px-4 font-semibold w-[55%]">설명</th>
                                        <th className="py-2.5 px-4 font-semibold w-[20%] text-right">요구 데이터</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border bg-background">
                                    {metricSpecs.map((spec) => (
                                        <tr key={spec.name} className="hover:bg-muted/30 transition-colors">
                                            <td className="py-3 px-4 align-top">
                                                <div className="font-medium text-foreground">{spec.name}</div>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground font-mono">
                                                        {spec.signal_group}
                                                    </span>
                                                    <span className="text-[10px] text-muted-foreground border border-border px-1.5 py-0.5 rounded">
                                                        {spec.source}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="py-3 px-4 align-top text-muted-foreground leading-relaxed">
                                                {spec.description}
                                            </td>
                                            <td className="py-3 px-4 align-top text-right">
                                                <div className="flex flex-wrap justify-end gap-1.5">
                                                    {spec.requires_ground_truth && (
                                                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
                                                            정답셋(GT)
                                                        </span>
                                                    )}
                                                    {spec.requires_embeddings && (
                                                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-500/10 text-blue-600 border border-blue-500/20">
                                                            임베딩
                                                        </span>
                                                    )}
                                                    {!spec.requires_ground_truth && !spec.requires_embeddings && (
                                                        <span className="text-xs text-muted-foreground">-</span>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                    {metricSpecs.length === 0 && (
                                        <tr>
                                            <td colSpan={3} className="py-8 text-center text-muted-foreground">
                                                등록된 메트릭이 없습니다.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>
            </div>
        </Layout>
    );
}
