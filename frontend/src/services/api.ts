import { API_BASE_URL } from "../config";

export interface RunSummary {
    run_id: string;
    dataset_name: string;
    project_name?: string | null;
    model_name: string;
    pass_rate: number;
    total_test_cases: number;
    passed_test_cases: number;
    started_at: string;
    finished_at: string | null;
    metrics_evaluated: string[];
    avg_metric_scores?: Record<string, number> | null;
    total_cost_usd: number | null;
    phoenix_precision: number | null;
    phoenix_drift: number | null;
    phoenix_experiment_url: string | null;
}

export interface TestCase {
    test_case_id: string;
    question: string;
    answer: string;
    ground_truth: string | null;
    contexts: string[] | null;
    metrics: {
        name: string;
        score: number;
        passed: boolean;
        reason: string | null;
    }[];
}

export interface RunDetailsResponse {
    summary: RunSummary;
    results: TestCase[];
}

export interface RunComparisonMetric {
    name: string;
    base: number | null;
    target: number | null;
    delta: number | null;
}

export interface RunComparisonCounts {
    regressions: number;
    improvements: number;
    same_pass: number;
    same_fail: number;
    new: number;
    removed: number;
}

export interface RunComparisonResponse {
    base: RunDetailsResponse;
    target: RunDetailsResponse;
    metric_deltas: RunComparisonMetric[];
    case_counts: RunComparisonCounts;
    pass_rate_delta: number;
    total_cases_delta: number;
}

export interface DatasetItem {
    name: string;
    path: string;
    type: string;
    size: number;
}

export interface ModelItem {
    id: string;
    name: string;
    supports_tools?: boolean;
}

export interface StartEvaluationRequest {
    dataset_path: string;
    metrics: string[];
    model: string;
    parallel?: boolean;
    batch_size?: number;
    thresholds?: Record<string, number>;
    project_name?: string;
    retriever_config?: Record<string, any>;
    memory_config?: Record<string, any>;
    tracker_config?: Record<string, any>;
    prompt_config?: Record<string, any>;
}

export interface JobStatusResponse {
    status: "pending" | "running" | "completed" | "failed";
    progress: number;
    message: string;
    result?: string;
    error?: string;
}

export interface Fact {
    fact_id: string;
    subject: string;
    predicate: string;
    object: string;
    domain: string | null;
    verification_score: number;
    created_at: string;
}

export interface Behavior {
    behavior_id: string;
    description: string;
    success_rate: number;
    use_count: number;
}

export interface SystemConfig {
    [key: string]: any;
}

export interface ImprovementAction {
    action_id: string;
    title: string;
    description?: string;
    implementation_hint?: string;
    expected_improvement: number;
    expected_improvement_range?: number[];
    effort: "low" | "medium" | "high";
    priority_score?: number;
}

export interface ImprovementGuide {
    guide_id: string;
    created_at: string;
    component: string;
    target_metrics: string[];
    priority: string;
    actions: ImprovementAction[];
    evidence?: Record<string, any> | null;
    affected_test_case_ids?: string[];
    verification_command?: string;
    metadata?: Record<string, any> | null;
}

export interface ImprovementReport {
    report_id: string;
    run_id: string;
    created_at: string;
    total_test_cases: number;
    failed_test_cases: number;
    pass_rate: number;
    metric_scores: Record<string, number>;
    metric_thresholds: Record<string, number>;
    metric_gaps: Record<string, number>;
    guides: ImprovementGuide[];
    total_expected_improvement: Record<string, number>;
    analysis_methods_used: string[];
    metadata: Record<string, any>;
}

export interface LLMReport {
    run_id: string;
    content: string; // Markdown content
    created_at: string;
}

export async function fetchRuns(): Promise<RunSummary[]> {
    const response = await fetch(`${API_BASE_URL}/runs/`);
    if (!response.ok) {
        throw new Error(`Failed to fetch runs: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchRunDetails(runId: string): Promise<RunDetailsResponse> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch run details: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchRunComparison(
    baseRunId: string,
    targetRunId: string
): Promise<RunComparisonResponse> {
    const params = new URLSearchParams({ base: baseRunId, target: targetRunId });
    const response = await fetch(`${API_BASE_URL}/runs/compare?${params.toString()}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch run comparison: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchDatasets(): Promise<DatasetItem[]> {
    const response = await fetch(`${API_BASE_URL}/runs/options/datasets`);
    if (!response.ok) throw new Error("Failed to fetch datasets");
    return response.json();
}

export async function fetchDatasetTemplate(format: "json" | "csv" | "xlsx"): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/runs/options/dataset-templates/${format}`);
    if (!response.ok) throw new Error("Failed to fetch dataset template");
    return response.blob();
}

export async function uploadDataset(file: File): Promise<{ message: string; path: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/runs/options/datasets`, {
        method: "POST",
        body: formData,
    });
    if (!response.ok) throw new Error("Failed to upload dataset");
    return response.json();
}

export async function uploadRetrieverDocs(
    file: File
): Promise<{ message: string; path: string; filename: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/runs/options/retriever-docs`, {
        method: "POST",
        body: formData,
    });
    if (!response.ok) throw new Error("Failed to upload retriever docs");
    return response.json();
}

export async function fetchModels(provider?: string): Promise<ModelItem[]> {
    const params = new URLSearchParams();
    if (provider) params.append("provider", provider);
    const query = params.toString();
    const response = await fetch(`${API_BASE_URL}/runs/options/models${query ? `?${query}` : ""}`);
    if (!response.ok) throw new Error("Failed to fetch models");
    return response.json();
}

export async function fetchMetrics(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/runs/options/metrics`);
    if (!response.ok) throw new Error("Failed to fetch metrics");
    return response.json();
}

export interface EvaluationProgressEvent {
    type: "progress" | "info" | "warning" | "error" | "result" | "step";
    data?: any;
    message?: string;
}

export async function startEvaluation(
    config: StartEvaluationRequest,
    onProgress?: (event: EvaluationProgressEvent) => void
): Promise<{ run_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/runs/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to start evaluation: ${errorText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let finalResult = null;

    if (reader) {
        let buffer = "";
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");

            // 마지막 라인이 불완전할 수 있으므로 버퍼에 남김
            buffer = lines.pop() || "";

            for (const rawLine of lines) {
                const line = rawLine.trim();
                if (line === "") continue;
                try {
                    const event = JSON.parse(line);
                    if (onProgress) onProgress(event);

                    if (event.type === "result") {
                        finalResult = event.data;
                    }
                    if (event.type === "error") {
                        throw new Error(event.message);
                    }
                } catch (e) {
                    console.warn("Stream parse error:", e, line);
                }
            }
        }

        const remaining = buffer.trim();
        if (remaining) {
            try {
                const event = JSON.parse(remaining);
                if (onProgress) onProgress(event);
                if (event.type === "result") {
                    finalResult = event.data;
                }
                if (event.type === "error") {
                    throw new Error(event.message);
                }
            } catch (e) {
                console.warn("Stream parse error:", e, remaining);
            }
        }
    }

    if (!finalResult) {
        throw new Error("Evaluation stream ended without result");
    }
    return finalResult;
}

export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/knowledge/jobs/${jobId}`);
    if (!response.ok) throw new Error("Failed to fetch job status");
    return response.json();
}

// --- Domain Memory API ---

export async function fetchFacts(filters?: { domain?: string; subject?: string }): Promise<Fact[]> {
    const params = new URLSearchParams();
    if (filters?.domain) params.append("domain", filters.domain);
    if (filters?.subject) params.append("subject", filters.subject);

    const response = await fetch(`${API_BASE_URL}/domain/facts?${params.toString()}`);
    if (!response.ok) throw new Error("Failed to fetch facts");
    return response.json();
}

export async function fetchBehaviors(filters?: { domain?: string }): Promise<Behavior[]> {
    const params = new URLSearchParams();
    if (filters?.domain) params.append("domain", filters.domain);

    const response = await fetch(`${API_BASE_URL}/domain/behaviors?${params.toString()}`);
    if (!response.ok) throw new Error("Failed to fetch behaviors");
    return response.json();
}

// Knowledge Base
export interface KGStats {
    num_entities: number;
    num_relations: number;
    status: "not_built" | "available" | "error";
    message?: string;
}

export async function uploadDocuments(files: File[]): Promise<{ message: string; files: string[] }> {
    const formData = new FormData();
    files.forEach(file => formData.append("files", file));

    const response = await fetch(`${API_BASE_URL}/knowledge/upload`, {
        method: "POST",
        body: formData,
    });
    if (!response.ok) throw new Error("Failed to upload files");
    return response.json();
}

export async function buildKnowledgeGraph(config: { workers?: number; rebuild?: boolean } = {}): Promise<{ status: string; job_id: string }> {
    const response = await fetch(`${API_BASE_URL}/knowledge/build`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error("Failed to start KG build");
    return response.json();
}

export async function fetchKGStats(): Promise<KGStats> {
    const response = await fetch(`${API_BASE_URL}/knowledge/stats`);
    if (!response.ok) throw new Error("Failed to fetch KG stats");
    return response.json();
}

// Analysis Pipeline
export interface AnalysisResult {
    intent: string;
    is_complete: boolean;
    duration_ms: number | null;
    pipeline_id?: string | null;
    started_at?: string | null;
    finished_at?: string | null;
    final_output: Record<string, any> | null;
    node_results: Record<string, any>;
}

export interface AnalysisIntentInfo {
    intent: string;
    label: string;
    category: string;
    description: string;
    sample_query: string;
    available: boolean;
    missing_modules: string[];
    nodes: {
        id: string;
        name: string;
        module: string;
        depends_on: string[];
    }[];
}

export interface SaveAnalysisResultRequest {
    intent: string;
    query?: string | null;
    run_id?: string | null;
    pipeline_id?: string | null;
    profile?: string | null;
    tags?: string[] | null;
    metadata?: Record<string, any> | null;
    is_complete: boolean;
    duration_ms?: number | null;
    final_output?: Record<string, any> | null;
    node_results?: Record<string, any> | null;
    started_at?: string | null;
    finished_at?: string | null;
}

export interface AnalysisHistoryItem {
    result_id: string;
    intent: string;
    label: string;
    query: string | null;
    run_id: string | null;
    profile?: string | null;
    tags?: string[] | null;
    duration_ms: number | null;
    is_complete: boolean;
    created_at: string;
    started_at?: string | null;
    finished_at?: string | null;
}

export interface SavedAnalysisResult extends AnalysisHistoryItem {
    pipeline_id: string | null;
    final_output: Record<string, any> | null;
    node_results: Record<string, any> | null;
    metadata?: Record<string, any> | null;
}

export async function fetchAnalysisIntents(): Promise<AnalysisIntentInfo[]> {
    const response = await fetch(`${API_BASE_URL}/pipeline/intents`);
    if (!response.ok) throw new Error("Failed to fetch analysis intents");
    return response.json();
}

export async function runAnalysis(
    query: string,
    runId?: string,
    intent?: string,
    params?: Record<string, any>
): Promise<AnalysisResult> {
    const response = await fetch(`${API_BASE_URL}/pipeline/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, run_id: runId, intent, params }),
    });
    if (!response.ok) throw new Error("Analysis failed");
    return response.json();
}

export async function saveAnalysisResult(
    payload: SaveAnalysisResultRequest
): Promise<AnalysisHistoryItem> {
    const response = await fetch(`${API_BASE_URL}/pipeline/results`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("Failed to save analysis result");
    return response.json();
}

export async function fetchAnalysisHistory(limit: number = 20): Promise<AnalysisHistoryItem[]> {
    const response = await fetch(`${API_BASE_URL}/pipeline/results?limit=${limit}`);
    if (!response.ok) throw new Error("Failed to fetch analysis history");
    return response.json();
}

export async function fetchAnalysisResult(resultId: string): Promise<SavedAnalysisResult> {
    const response = await fetch(`${API_BASE_URL}/pipeline/results/${resultId}`);
    if (!response.ok) throw new Error("Failed to fetch analysis result");
    return response.json();
}

// --- Config API ---

export async function fetchConfig(): Promise<SystemConfig> {
    const response = await fetch(`${API_BASE_URL}/config/`);
    if (!response.ok) throw new Error("Failed to fetch config");
    return response.json();
}

// --- Analysis & Report API ---

export async function fetchImprovementGuide(runId: string, includeLlm: boolean = false): Promise<ImprovementReport> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/improvement?include_llm=${includeLlm}`);
    if (!response.ok) throw new Error("Failed to fetch improvement guide");
    return response.json();
}

export async function fetchLLMReport(runId: string, modelId?: string): Promise<LLMReport> {
    const url = modelId
        ? `${API_BASE_URL}/runs/${runId}/report?model_id=${encodeURIComponent(modelId)}`
        : `${API_BASE_URL}/runs/${runId}/report`;

    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to generate report");
    return response.json();
}
