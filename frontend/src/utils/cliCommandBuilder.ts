export interface RunCommandOptions {
    dataset_path: string;
    model?: string;
    metrics?: string[];
    summaryMode?: boolean;
    run_mode?: string;
    threshold_profile?: string;
    retriever_mode?: string;
    docs_path?: string;
    tracker?: string;
    stage_store?: boolean;
    enable_memory?: boolean;
    system_prompt?: string;
    system_prompt_name?: string;
    prompt_set_name?: string;
    prompt_set_description?: string;
    batch_size?: number;
    parallel?: boolean;
    ragas_prompts_yaml?: string;
}

export interface AnalyzeCommandOptions {
    query: string;
    run_id?: string;
    intent?: string;
}

export interface CompareCommandOptions {
    base_run_id: string;
    target_run_id: string;
}

export function buildRunCommand(options: RunCommandOptions): string {
    const parts = ["uv run evalvault run"];

    parts.push(options.dataset_path || "<DATASET_PATH>");

    if (options.model) {
        parts.push(`--model ${options.model}`);
    }

    if (options.summaryMode) {
        parts.push("--summary");
    } else if (options.metrics && options.metrics.length > 0) {
        parts.push(`--metrics ${options.metrics.join(",")}`);
    }

    if (options.threshold_profile && options.threshold_profile !== "none") {
        parts.push(`--threshold-profile ${options.threshold_profile}`);
    }

    if (options.retriever_mode && options.retriever_mode !== "none") {
        parts.push(`--retriever ${options.retriever_mode}`);
        if (options.docs_path) {
            parts.push(`--retriever-docs ${options.docs_path}`);
        }
    }

    if (options.tracker && options.tracker !== "none") {
        parts.push(`--tracker ${options.tracker}`);
    }

    if (options.stage_store) {
        parts.push("--stage-store");
    }

    if (options.enable_memory) {
        parts.push("--use-domain-memory");
        parts.push("--augment-context");
    }

    if (options.system_prompt) {
        const escaped = options.system_prompt.replace(/"/g, '\\"');
        parts.push(`--system-prompt "${escaped}"`);
    }
    if (options.system_prompt_name) {
        parts.push(`--system-prompt-name "${options.system_prompt_name}"`);
    }

    if (options.prompt_set_name) {
        parts.push(`--prompt-set-name "${options.prompt_set_name}"`);
    }
    if (options.prompt_set_description) {
        parts.push(`--prompt-set-description "${options.prompt_set_description}"`);
    }

    if (options.run_mode) {
        parts.push(`--mode ${options.run_mode}`);
    }

    if (options.batch_size && options.batch_size > 1) {
        parts.push(`--batch-size ${options.batch_size}`);
        if (options.parallel) {
            parts.push("--parallel");
        }
    }

    if (options.ragas_prompts_yaml) {
        parts.push("--ragas-prompts <RAGAS_PROMPTS_YAML_FILE>");
    }

    return parts.join(" ");
}

export function buildAnalyzeCommand(options: AnalyzeCommandOptions): string {
    const parts = ["uv run evalvault pipeline analyze"];
    parts.push(`"${options.query.replace(/"/g, '\\"')}"`);

    if (options.run_id) {
        parts.push(`--run ${options.run_id}`);
    }

    return parts.join(" ");
}

export function buildCompareCommand(options: CompareCommandOptions): string {
    return `uv run evalvault compare ${options.base_run_id} ${options.target_run_id}`;
}
