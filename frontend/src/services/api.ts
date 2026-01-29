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
    run_mode?: string | null;
    evaluation_task?: string | null;
    threshold_profile?: string | null;
    thresholds?: Record<string, number> | null;
    avg_metric_scores?: Record<string, number> | null;
    avg_satisfaction_score?: number | null;
    thumb_up_rate?: number | null;
    imputed_ratio?: number | null;
    total_cost_usd: number | null;
    phoenix_precision: number | null;
    phoenix_drift: number | null;
    phoenix_experiment_url: string | null;
    phoenix_trace_url?: string | null;
    feedback_count?: number | null;
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
    calibrated_satisfaction?: number | null;
    imputed?: boolean;
    imputation_source?: string | null;
}

export interface RunDetailsResponse {
    summary: RunSummary;
    results: TestCase[];
    prompt_set?: PromptSetDetail;
}

export interface FeedbackSaveRequest {
    test_case_id: string;
    satisfaction_score?: number | null;
    thumb_feedback?: "up" | "down" | "none" | null;
    comment?: string | null;
    rater_id?: string | null;
}

export interface FeedbackResponse {
    feedback_id: string;
    run_id: string;
    test_case_id: string;
    satisfaction_score?: number | null;
    thumb_feedback?: string | null;
    comment?: string | null;
    rater_id?: string | null;
    created_at?: string | null;
}

export interface FeedbackSummaryResponse {
    avg_satisfaction_score?: number | null;
    thumb_up_rate?: number | null;
    total_feedback: number;
}

export interface ClusterMapItem {
    test_case_id: string;
    cluster_id: string;
}

export interface ClusterMapResponse {
    run_id: string;
    dataset_name: string;
    map_id: string;
    source?: string | null;
    created_at?: string | null;
    metadata?: Record<string, unknown> | null;
    items: ClusterMapItem[];
}

export interface ClusterMapFileInfo {
    name: string;
    path: string;
    size: number;
}

export interface ClusterMapContentResponse {
    source: string;
    items: ClusterMapItem[];
}

export interface ClusterMapSaveRequest {
    source?: string | null;
    metadata?: Record<string, unknown> | null;
    items: ClusterMapItem[];
}

export interface ClusterMapSaveResponse {
    run_id: string;
    map_id: string;
    source?: string | null;
    created_at?: string | null;
    metadata?: Record<string, unknown> | null;
    saved_count: number;
    skipped_count: number;
}

export interface ClusterMapVersionInfo {
    map_id: string;
    source?: string | null;
    created_at?: string | null;
    item_count: number;
}

export interface ClusterMapDeleteResponse {
    run_id: string;
    map_id: string;
    deleted_count: number;
}

export type VisualSpaceGranularity = "run" | "case" | "cluster";
export type VisualSpaceInclude = "summary" | "encoding" | "breakdown";

export interface VisualSpaceQuery {
    runId: string;
    granularity?: VisualSpaceGranularity;
    baseRunId?: string;
    autoBase?: boolean;
    include?: VisualSpaceInclude[];
    limit?: number;
    offset?: number;
    clusterMap?: Record<string, string>;
}

export interface VisualSpaceAxis {
    x: string;
    y: string;
    z: string;
    normalization?: string;
    targets?: Record<string, number>;
}

export interface VisualSpacePoint {
    id: string;
    coords: {
        x: number | null;
        y: number | null;
        z?: number | null;
    };
    encoding?: {
        color?: string;
        size?: number;
        shape?: string;
        opacity?: number;
        border?: string;
    };
    labels?: {
        name?: string;
        quadrant?: string | null;
        guide_hint?: string | null;
    };
    stats?: Record<string, number>;
    breakdown?: Record<string, number | null>;
}

export interface VisualSpaceResponse {
    run_id: string;
    granularity: VisualSpaceGranularity;
    axis: VisualSpaceAxis;
    points: VisualSpacePoint[];
    warnings?: string[];
    base?: {
        run_id: string;
        auto_selected: boolean;
        criteria: Record<string, unknown>;
    };
    summary?: {
        quadrant_counts?: Record<string, number>;
        regressions?: number;
        improvements?: number;
    };
}

export interface PromptSnapshotItem {
    role: string;
    order: number;
    metadata?: Record<string, unknown>;
    prompt: {
        prompt_id: string;
        name: string;
        kind: string;
        checksum: string;
        source?: string | null;
        notes?: string | null;
        metadata?: Record<string, unknown>;
        created_at: string;
        content?: string;
    };
}

export interface PromptSetDetail {
    prompt_set_id: string;
    name: string;
    description?: string;
    metadata?: Record<string, unknown>;
    created_at: string;
    items: PromptSnapshotItem[];
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

export interface QualityGateResultResponse {
    metric: string;
    score: number;
    threshold: number;
    passed: boolean;
    gap: number;
}

export interface QualityGateReportResponse {
    run_id: string;
    overall_passed: boolean;
    results: QualityGateResultResponse[];
    regression_detected: boolean;
    regression_amount?: number | null;
}

export interface JudgeCalibrationRequest {
    run_id: string;
    labels_source: "feedback" | "gold" | "hybrid";
    method: "platt" | "isotonic" | "temperature" | "none";
    metrics?: string[] | null;
    holdout_ratio: number;
    seed: number;
    parallel?: boolean;
    concurrency?: number;
}

export interface JudgeCalibrationCase {
    test_case_id: string;
    raw_score: number;
    calibrated_score: number;
    label?: number | null;
    label_source?: string | null;
}

export interface JudgeCalibrationMetric {
    metric: string;
    method: string;
    sample_count: number;
    label_count: number;
    mae?: number | null;
    pearson?: number | null;
    spearman?: number | null;
    temperature?: number | null;
    parameters?: Record<string, number | null>;
    gate_passed?: boolean | null;
    warning?: string | null;
}

export interface JudgeCalibrationSummary {
    calibration_id: string;
    run_id: string;
    labels_source: string;
    method: string;
    metrics: string[];
    holdout_ratio: number;
    seed: number;
    total_labels: number;
    total_samples: number;
    gate_passed: boolean;
    gate_threshold?: number | null;
    notes: string[];
    created_at: string;
}

export interface JudgeCalibrationResponse {
    calibration_id: string;
    status: "ok" | "degraded";
    started_at: string;
    finished_at: string;
    duration_ms: number;
    artifacts: Record<string, string>;
    summary: JudgeCalibrationSummary;
    metrics: JudgeCalibrationMetric[];
    case_results: Record<string, JudgeCalibrationCase[]>;
    warnings: string[];
}

export interface JudgeCalibrationHistoryItem {
    calibration_id: string;
    run_id: string;
    labels_source: string;
    method: string;
    metrics: string[];
    holdout_ratio: number;
    seed: number;
    total_labels: number;
    total_samples: number;
    gate_passed: boolean;
    gate_threshold?: number | null;
    created_at: string;
}

export interface DebugReport {
    run_summary: Record<string, unknown>;
    stage_summary: {
        run_id: string;
        total_events: number;
        stage_type_counts: Record<string, number>;
        stage_type_avg_durations: Record<string, number>;
        missing_required_stage_types: string[];
    } | null;
    stage_metrics: StageMetric[];
    bottlenecks: Record<string, unknown>[];
    recommendations: string[];
    phoenix_trace_url?: string | null;
    langfuse_trace_url?: string | null;
}

export interface OpsReportResponse {
    run_summary: Record<string, unknown>;
    ops_kpis: {
        total_test_cases?: number | null;
        pass_rate?: number | null;
        failure_rate?: number | null;
        stage_error_rate?: number | null;
        stage_error_severity?: "ok" | "warning" | "critical" | string | null;
        duration_seconds?: number | null;
        total_tokens?: number | null;
        total_cost_usd?: number | null;
        avg_latency_ms?: number | null;
        p95_latency_ms?: number | null;
        avg_tokens_per_case?: number | null;
        avg_cost_per_case_usd?: number | null;
    };
    metadata?: Record<string, unknown>;
}

export interface PromptDiffSummaryItem {
    role: string;
    base_checksum?: string | null;
    target_checksum?: string | null;
    status: "same" | "diff" | "missing";
    base_name?: string | null;
    target_name?: string | null;
    base_kind?: string | null;
    target_kind?: string | null;
}

export interface PromptDiffEntry {
    role: string;
    lines: string[];
    truncated: boolean;
}

export interface PromptDiffResponse {
    base_run_id: string;
    target_run_id: string;
    summary: PromptDiffSummaryItem[];
    diffs: PromptDiffEntry[];
}

export interface DatasetItem {
    name: string;
    path: string;
    type: string;
    size: number;
}

export interface MetricSpec {
    name: string;
    description: string;
    requires_ground_truth: boolean;
    requires_embeddings: boolean;
    source: string;
    category: string;
    signal_group: string;
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
    evaluation_task?: string;
    parallel?: boolean;
    batch_size?: number;
    thresholds?: Record<string, number>;
    threshold_profile?: string;
    project_name?: string;
    retriever_config?: Record<string, unknown>;
    memory_config?: Record<string, unknown>;
    tracker_config?: Record<string, unknown>;
    stage_store?: boolean;
    prompt_config?: Record<string, unknown>;
    system_prompt?: string;
    system_prompt_name?: string;
    prompt_set_name?: string;
    prompt_set_description?: string;
    ragas_prompts?: Record<string, string>;
    ragas_prompts_yaml?: string;
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
    [key: string]: unknown;
}

export type ConfigUpdateRequest = {
    evalvault_profile?: string | null;
    cors_origins?: string | null;
    evalvault_db_path?: string | null;
    evalvault_memory_db_path?: string | null;
    llm_provider?: "ollama" | "openai" | "vllm";
    faithfulness_fallback_provider?: "ollama" | "openai" | "vllm" | null;
    faithfulness_fallback_model?: string | null;
    openai_model?: string | null;
    openai_embedding_model?: string | null;
    openai_base_url?: string | null;
    ollama_model?: string | null;
    ollama_embedding_model?: string | null;
    ollama_base_url?: string | null;
    ollama_timeout?: number | null;
    ollama_think_level?: string | null;
    ollama_tool_models?: string | null;
    vllm_model?: string | null;
    vllm_embedding_model?: string | null;
    vllm_base_url?: string | null;
    vllm_embedding_base_url?: string | null;
    vllm_timeout?: number | null;
    azure_endpoint?: string | null;
    azure_deployment?: string | null;
    azure_embedding_deployment?: string | null;
    azure_api_version?: string | null;
    anthropic_model?: string | null;
    anthropic_thinking_budget?: number | null;
    langfuse_host?: string | null;
    mlflow_tracking_uri?: string | null;
    mlflow_experiment_name?: string | null;
    phoenix_endpoint?: string | null;
    phoenix_enabled?: boolean | null;
    phoenix_sample_rate?: number | null;
    tracker_provider?: "langfuse" | "mlflow" | "phoenix" | "none" | null;
    postgres_host?: string | null;
    postgres_port?: number | null;
    postgres_database?: string | null;
    postgres_user?: string | null;
};

export interface ConfigProfile {
    name: string;
    description?: string;
    llm_provider: string;
    llm_model: string;
    embedding_provider: string;
    embedding_model: string;
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
    evidence?: Record<string, unknown> | null;
    affected_test_case_ids?: string[];
    verification_command?: string;
    metadata?: Record<string, unknown> | null;
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
    metadata: Record<string, unknown>;
}

export interface StageEvent {
    run_id: string;
    stage_id: string;
    parent_stage_id?: string | null;
    stage_type: string;
    stage_name?: string | null;
    status: string;
    attempt: number;
    started_at?: string | null;
    finished_at?: string | null;
    duration_ms?: number | null;
    input_ref?: Record<string, unknown> | null;
    output_ref?: Record<string, unknown> | null;
    attributes: Record<string, unknown>;
    metadata: Record<string, unknown>;
    trace?: { trace_id?: string | null; span_id?: string | null };
}

export interface StageMetric {
    run_id: string;
    stage_id: string;
    metric_name: string;
    score: number;
    threshold?: number | null;
    evidence?: Record<string, unknown> | null;
}

export interface LLMReport {
    run_id: string;
    content: string; // Markdown content
    created_at: string;
}

export async function fetchRuns(options?: {
    includeFeedback?: boolean;
    limit?: number;
    offset?: number;
}): Promise<RunSummary[]> {
    const params = new URLSearchParams();
    if (options?.includeFeedback) {
        params.set("include_feedback", "true");
    }
    if (options?.limit !== undefined) {
        params.set("limit", String(options.limit));
    }
    if (options?.offset !== undefined) {
        params.set("offset", String(options.offset));
    }
    const query = params.toString();
    const response = await fetch(`${API_BASE_URL}/runs/${query ? `?${query}` : ""}`);
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

export async function fetchRunFeedback(runId: string): Promise<FeedbackResponse[]> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/feedback`);
    if (!response.ok) {
        throw new Error(`Failed to fetch feedback: ${response.statusText}`);
    }
    return response.json();
}

export async function saveRunFeedback(
    runId: string,
    payload: FeedbackSaveRequest
): Promise<FeedbackResponse> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Failed to save feedback: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchRunFeedbackSummary(
    runId: string
): Promise<FeedbackSummaryResponse> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/feedback/summary`);
    if (!response.ok) {
        throw new Error(`Failed to fetch feedback summary: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchRunClusterMap(runId: string): Promise<ClusterMapResponse> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/cluster-map`);
    if (response.status === 404) {
        throw new Error("Cluster map not found");
    }
    if (!response.ok) {
        throw new Error(`Failed to fetch cluster map: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchRunClusterMaps(runId: string): Promise<ClusterMapVersionInfo[]> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/cluster-maps`);
    if (!response.ok) {
        throw new Error(`Failed to fetch cluster map versions: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchRunClusterMapById(
    runId: string,
    mapId: string
): Promise<ClusterMapResponse> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/cluster-maps/${mapId}`);
    if (response.status === 404) {
        throw new Error("Cluster map not found");
    }
    if (!response.ok) {
        throw new Error(`Failed to fetch cluster map: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchVisualSpace(
    runId: string,
    payload: Omit<VisualSpaceQuery, "runId">
): Promise<VisualSpaceResponse> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/visual-space`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            granularity: payload.granularity,
            base_run_id: payload.baseRunId,
            auto_base: payload.autoBase,
            include: payload.include,
            limit: payload.limit,
            offset: payload.offset,
            cluster_map: payload.clusterMap,
        }),
    });
    if (!response.ok) {
        throw new Error(`Failed to fetch visual space: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchClusterMapFiles(): Promise<ClusterMapFileInfo[]> {
    const response = await fetch(`${API_BASE_URL}/runs/options/cluster-maps`);
    if (!response.ok) {
        throw new Error(`Failed to fetch cluster map list: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchClusterMapFile(fileName: string): Promise<ClusterMapContentResponse> {
    const response = await fetch(
        `${API_BASE_URL}/runs/options/cluster-maps/${encodeURIComponent(fileName)}`
    );
    if (response.status === 404) {
        throw new Error("Cluster map not found");
    }
    if (!response.ok) {
        throw new Error(`Failed to fetch cluster map file: ${response.statusText}`);
    }
    return response.json();
}

export async function saveRunClusterMap(
    runId: string,
    payload: ClusterMapSaveRequest
): Promise<ClusterMapSaveResponse> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/cluster-maps`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Failed to save cluster map: ${response.statusText}`);
    }
    return response.json();
}

export async function deleteRunClusterMap(
    runId: string,
    mapId: string
): Promise<ClusterMapDeleteResponse> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/cluster-maps/${mapId}`, {
        method: "DELETE",
    });
    if (!response.ok) {
        throw new Error(`Failed to delete cluster map: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchStageEvents(
    runId: string,
    stageType?: string
): Promise<StageEvent[]> {
    const params = new URLSearchParams();
    if (stageType) params.append("stage_type", stageType);
    const query = params.toString();
    const response = await fetch(
        `${API_BASE_URL}/runs/${runId}/stage-events${query ? `?${query}` : ""}`
    );
    if (!response.ok) {
        throw new Error(`Failed to fetch stage events: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchStageMetrics(
    runId: string,
    stageId?: string,
    metricName?: string
): Promise<StageMetric[]> {
    const params = new URLSearchParams();
    if (stageId) params.append("stage_id", stageId);
    if (metricName) params.append("metric_name", metricName);
    const query = params.toString();
    const response = await fetch(
        `${API_BASE_URL}/runs/${runId}/stage-metrics${query ? `?${query}` : ""}`
    );
    if (!response.ok) {
        throw new Error(`Failed to fetch stage metrics: ${response.statusText}`);
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

export async function fetchQualityGateReport(runId: string): Promise<QualityGateReportResponse> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/quality-gate`);
    if (!response.ok) {
        throw new Error(`Failed to fetch quality gate: ${response.statusText}`);
    }
    return response.json();
}

export async function runJudgeCalibration(
    payload: JudgeCalibrationRequest
): Promise<JudgeCalibrationResponse> {
    const response = await fetch(`${API_BASE_URL}/calibration/judge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Failed to run calibration: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchJudgeCalibration(
    calibrationId: string
): Promise<JudgeCalibrationResponse> {
    const response = await fetch(`${API_BASE_URL}/calibration/judge/${calibrationId}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch calibration: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchJudgeCalibrationHistory(
    limit: number = 20
): Promise<JudgeCalibrationHistoryItem[]> {
    const response = await fetch(`${API_BASE_URL}/calibration/judge/history?limit=${limit}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch calibration history: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchDebugReport(runId: string): Promise<DebugReport> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/debug-report`);
    if (!response.ok) {
        throw new Error(`Failed to fetch debug report: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchDebugReportMarkdown(runId: string): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/debug-report?format=markdown`);
    if (!response.ok) {
        throw new Error(`Failed to fetch debug report: ${response.statusText}`);
    }
    return response.blob();
}

export async function fetchOpsReport(runId: string): Promise<OpsReportResponse> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/ops-report?format=json&save=false`);
    if (!response.ok) {
        throw new Error(`Failed to fetch ops report: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchPromptDiff(
    baseRunId: string,
    targetRunId: string,
    maxLines: number = 40,
    includeDiff: boolean = true
): Promise<PromptDiffResponse> {
    const params = new URLSearchParams({
        base_run_id: baseRunId,
        target_run_id: targetRunId,
        max_lines: String(maxLines),
        include_diff: includeDiff ? "true" : "false",
    });
    const response = await fetch(`${API_BASE_URL}/runs/prompt-diff?${params.toString()}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch prompt diff: ${response.statusText}`);
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

export async function fetchMetricSpecs(): Promise<MetricSpec[]> {
    const response = await fetch(`${API_BASE_URL}/runs/options/metric-specs`);
    if (!response.ok) throw new Error("Failed to fetch metric specs");
    return response.json();
}

export interface EvaluationProgressEvent {
    type: "progress" | "info" | "warning" | "error" | "result" | "step";
    data?: unknown;
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
    final_output: Record<string, unknown> | null;
    node_results: Record<string, unknown>;
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

export interface AnalysisMetricSpec {
    key: string;
    label: string;
    description: string;
    signal_group: string;
    module_id: string;
    output_path: string[];
}

export interface SaveAnalysisResultRequest {
    intent: string;
    query?: string | null;
    run_id?: string | null;
    pipeline_id?: string | null;
    profile?: string | null;
    tags?: string[] | null;
    metadata?: unknown;
    is_complete: boolean;
    duration_ms?: number | null;
    final_output?: Record<string, unknown> | null;
    node_results?: Record<string, unknown> | null;
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
    final_output: Record<string, unknown> | null;
    node_results: Record<string, unknown> | null;
    metadata?: unknown;
}

export async function fetchAnalysisIntents(): Promise<AnalysisIntentInfo[]> {
    const response = await fetch(`${API_BASE_URL}/pipeline/intents`);
    if (!response.ok) throw new Error("Failed to fetch analysis intents");
    return response.json();
}

export async function fetchAnalysisMetricSpecs(): Promise<AnalysisMetricSpec[]> {
    const response = await fetch(`${API_BASE_URL}/pipeline/options/analysis-metric-specs`);
    if (!response.ok) throw new Error("Failed to fetch analysis metric specs");
    return response.json();
}

export async function runAnalysis(
    query: string,
    runId?: string,
    intent?: string,
    params?: Record<string, unknown>
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

export async function fetchConfigProfiles(): Promise<ConfigProfile[]> {
    const response = await fetch(`${API_BASE_URL}/config/profiles`);
    if (!response.ok) throw new Error("Failed to fetch config profiles");
    return response.json();
}

export async function updateConfig(payload: ConfigUpdateRequest): Promise<SystemConfig> {
    const response = await fetch(`${API_BASE_URL}/config/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("Failed to update config");
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

export async function fetchAnalysisReport(
    runId: string,
    params: { format?: "markdown" | "html"; includeNlp?: boolean; includeCausal?: boolean } = {}
): Promise<string> {
    const query = new URLSearchParams();
    if (params.format) query.set("format", params.format);
    if (params.includeNlp !== undefined) query.set("include_nlp", String(params.includeNlp));
    if (params.includeCausal !== undefined) query.set("include_causal", String(params.includeCausal));
    const suffix = query.toString() ? `?${query.toString()}` : "";
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/analysis-report${suffix}`);
    if (!response.ok) throw new Error("Failed to fetch analysis report");
    return response.text();
}

export async function fetchDashboard(
    runId: string,
    format: "png" | "svg" | "pdf" = "png"
): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/dashboard?format=${format}`);
    if (!response.ok) throw new Error("Failed to fetch dashboard");
    return response.blob();
}
