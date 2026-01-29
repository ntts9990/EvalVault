-- EvalVault SQLite Database Schema
-- Stores evaluation runs, test case results, and metric scores

-- Main evaluation runs table
CREATE TABLE IF NOT EXISTS evaluation_runs (
    run_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    dataset_version TEXT,
    model_name TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd REAL,
    pass_rate REAL,
    metrics_evaluated TEXT,  -- JSON array of metric names
    thresholds TEXT,  -- JSON object of metric thresholds
    langfuse_trace_id TEXT,
    metadata TEXT,  -- Tracker metadata (Phoenix, Langfuse, etc.)
    retrieval_metadata TEXT,  -- Retrieval metadata by test case
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying by dataset and model
CREATE INDEX IF NOT EXISTS idx_runs_dataset ON evaluation_runs(dataset_name);
CREATE INDEX IF NOT EXISTS idx_runs_model ON evaluation_runs(model_name);
CREATE INDEX IF NOT EXISTS idx_runs_started_at ON evaluation_runs(started_at DESC);

-- Test case results table
CREATE TABLE IF NOT EXISTS test_case_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    test_case_id TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    cost_usd REAL,
    trace_id TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    question TEXT,
    answer TEXT,
    contexts TEXT,  -- JSON array of context strings
    ground_truth TEXT,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_results_run_id ON test_case_results(run_id);

-- Run cluster map table
CREATE TABLE IF NOT EXISTS run_cluster_maps (
    run_id TEXT NOT NULL,
    map_id TEXT NOT NULL,
    test_case_id TEXT NOT NULL,
    cluster_id TEXT NOT NULL,
    source TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id, map_id, test_case_id),
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cluster_maps_run_id ON run_cluster_maps(run_id);
CREATE INDEX IF NOT EXISTS idx_cluster_maps_map_id ON run_cluster_maps(map_id);

CREATE TABLE IF NOT EXISTS satisfaction_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    test_case_id TEXT NOT NULL,
    satisfaction_score REAL,
    thumb_feedback TEXT,
    comment TEXT,
    rater_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feedback_run_id ON satisfaction_feedback(run_id);
CREATE INDEX IF NOT EXISTS idx_feedback_test_case_id ON satisfaction_feedback(test_case_id);

-- Metric scores table
CREATE TABLE IF NOT EXISTS metric_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    score REAL NOT NULL,
    threshold REAL NOT NULL,
    reason TEXT,
    FOREIGN KEY (result_id) REFERENCES test_case_results(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scores_result_id ON metric_scores(result_id);
CREATE INDEX IF NOT EXISTS idx_scores_metric_name ON metric_scores(metric_name);

-- Multiturn evaluation tables
CREATE TABLE IF NOT EXISTS multiturn_runs (
    run_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    dataset_version TEXT,
    model_name TEXT,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    conversation_count INTEGER DEFAULT 0,
    turn_count INTEGER DEFAULT 0,
    metrics_evaluated TEXT,  -- JSON array of metric names
    drift_threshold REAL,
    summary TEXT,  -- JSON summary
    metadata TEXT,  -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_multiturn_runs_dataset ON multiturn_runs(dataset_name);
CREATE INDEX IF NOT EXISTS idx_multiturn_runs_started_at ON multiturn_runs(started_at DESC);

CREATE TABLE IF NOT EXISTS multiturn_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    turn_count INTEGER DEFAULT 0,
    drift_score REAL,
    drift_threshold REAL,
    drift_detected INTEGER DEFAULT 0,
    summary TEXT,  -- JSON summary
    FOREIGN KEY (run_id) REFERENCES multiturn_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_multiturn_conversations_run_id ON multiturn_conversations(run_id);
CREATE INDEX IF NOT EXISTS idx_multiturn_conversations_conv_id ON multiturn_conversations(conversation_id);

CREATE TABLE IF NOT EXISTS multiturn_turn_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    turn_id TEXT NOT NULL,
    turn_index INTEGER,
    role TEXT NOT NULL,
    passed INTEGER DEFAULT 0,
    latency_ms INTEGER,
    metadata TEXT,  -- JSON metadata
    FOREIGN KEY (run_id) REFERENCES multiturn_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_multiturn_turns_run_id ON multiturn_turn_results(run_id);
CREATE INDEX IF NOT EXISTS idx_multiturn_turns_conv_id ON multiturn_turn_results(conversation_id);

CREATE TABLE IF NOT EXISTS multiturn_metric_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    turn_result_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    score REAL NOT NULL,
    threshold REAL,
    FOREIGN KEY (turn_result_id) REFERENCES multiturn_turn_results(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_multiturn_scores_turn_id ON multiturn_metric_scores(turn_result_id);
CREATE INDEX IF NOT EXISTS idx_multiturn_scores_metric_name ON multiturn_metric_scores(metric_name);

-- Prompt storage tables
CREATE TABLE IF NOT EXISTS prompts (
    prompt_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    checksum TEXT NOT NULL,
    source TEXT,
    notes TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prompts_checksum ON prompts(checksum);
CREATE INDEX IF NOT EXISTS idx_prompts_kind ON prompts(kind);

CREATE TABLE IF NOT EXISTS prompt_sets (
    prompt_set_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prompt_set_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_set_id TEXT NOT NULL,
    prompt_id TEXT NOT NULL,
    role TEXT NOT NULL,
    item_order INTEGER DEFAULT 0,
    metadata TEXT,
    FOREIGN KEY (prompt_set_id) REFERENCES prompt_sets(prompt_set_id) ON DELETE CASCADE,
    FOREIGN KEY (prompt_id) REFERENCES prompts(prompt_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_prompt_set_items_set_id ON prompt_set_items(prompt_set_id);

CREATE TABLE IF NOT EXISTS run_prompt_sets (
    run_id TEXT NOT NULL,
    prompt_set_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id, prompt_set_id),
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
    FOREIGN KEY (prompt_set_id) REFERENCES prompt_sets(prompt_set_id) ON DELETE CASCADE
);

-- Experiments table for A/B testing
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    hypothesis TEXT,
    status TEXT DEFAULT 'draft',  -- draft, running, completed, archived
    metrics_to_compare TEXT,  -- JSON array of metric names
    conclusion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_created_at ON experiments(created_at DESC);

-- Experiment groups table
CREATE TABLE IF NOT EXISTS experiment_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    UNIQUE(experiment_id, name)
);

CREATE INDEX IF NOT EXISTS idx_groups_experiment_id ON experiment_groups(experiment_id);

-- Experiment group runs mapping
CREATE TABLE IF NOT EXISTS experiment_group_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    run_id TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES experiment_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
    UNIQUE(group_id, run_id)
);

CREATE INDEX IF NOT EXISTS idx_group_runs_group_id ON experiment_group_runs(group_id);

-- Analysis results table
CREATE TABLE IF NOT EXISTS analysis_results (
    analysis_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL,  -- 'statistical', 'nlp', 'causal', 'data_quality', 'dataset_features'
    result_data TEXT NOT NULL,  -- JSON serialized analysis result
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_analysis_run_id ON analysis_results(run_id);
CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type);

-- Analysis reports table
CREATE TABLE IF NOT EXISTS analysis_reports (
    report_id TEXT PRIMARY KEY,
    run_id TEXT,
    experiment_id TEXT,
    report_type TEXT NOT NULL,  -- 'executive', 'technical', 'comprehensive'
    format TEXT NOT NULL,  -- 'markdown', 'html', 'excel'
    content TEXT,  -- Report content (markdown/html) or file path (excel)
    metadata TEXT,  -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE SET NULL,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_run_id ON analysis_reports(run_id);
CREATE INDEX IF NOT EXISTS idx_reports_experiment_id ON analysis_reports(experiment_id);

-- Ops reports table
CREATE TABLE IF NOT EXISTS ops_reports (
    report_id TEXT PRIMARY KEY,
    run_id TEXT,
    report_type TEXT NOT NULL,  -- 'ops_report', 'ops_snapshot'
    format TEXT NOT NULL,  -- 'markdown', 'json'
    content TEXT,  -- Report content (markdown/json) or file path
    metadata TEXT,  -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_ops_reports_run_id ON ops_reports(run_id);

-- Analysis pipeline results table
CREATE TABLE IF NOT EXISTS pipeline_results (
    result_id TEXT PRIMARY KEY,
    intent TEXT NOT NULL,
    query TEXT,
    run_id TEXT,
    pipeline_id TEXT,
    profile TEXT,
    tags TEXT,  -- JSON array of tag strings
    metadata TEXT,  -- JSON metadata for trace/profile/user info
    is_complete INTEGER NOT NULL DEFAULT 1,
    duration_ms REAL,
    final_output TEXT,  -- JSON serialized pipeline output
    node_results TEXT,  -- JSON serialized node outputs
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pipeline_results_created_at
    ON pipeline_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_results_intent
    ON pipeline_results(intent);
CREATE INDEX IF NOT EXISTS idx_pipeline_results_run_id
    ON pipeline_results(run_id);

-- Stage events for pipeline-level observability
CREATE TABLE IF NOT EXISTS stage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    parent_stage_id TEXT,
    stage_type TEXT NOT NULL,
    stage_name TEXT,
    status TEXT,
    attempt INTEGER DEFAULT 1,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_ms REAL,
    input_ref TEXT,
    output_ref TEXT,
    attributes TEXT,
    metadata TEXT,
    trace_id TEXT,
    span_id TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_stage_events_run_stage_id
    ON stage_events(run_id, stage_id);
CREATE INDEX IF NOT EXISTS idx_stage_events_run_id ON stage_events(run_id);
CREATE INDEX IF NOT EXISTS idx_stage_events_stage_type ON stage_events(stage_type);

-- Stage-level evaluation metrics
CREATE TABLE IF NOT EXISTS stage_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    score REAL NOT NULL,
    threshold REAL,
    evidence TEXT
);

CREATE INDEX IF NOT EXISTS idx_stage_metrics_run_id ON stage_metrics(run_id);
CREATE INDEX IF NOT EXISTS idx_stage_metrics_stage_id ON stage_metrics(stage_id);

-- Benchmark runs table (KMMLU, MMLU, etc.)
CREATE TABLE IF NOT EXISTS benchmark_runs (
    run_id TEXT PRIMARY KEY,
    benchmark_type TEXT NOT NULL,
    model_name TEXT NOT NULL,
    backend TEXT NOT NULL,
    tasks TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    task_scores TEXT,
    overall_accuracy REAL,
    num_fewshot INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_seconds REAL DEFAULT 0.0,
    error_message TEXT,
    phoenix_trace_id TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_benchmark_runs_type ON benchmark_runs(benchmark_type);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_model ON benchmark_runs(model_name);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_created_at ON benchmark_runs(created_at DESC);

-- Regression baselines table for CI/CD integration
CREATE TABLE IF NOT EXISTS regression_baselines (
    baseline_key TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    dataset_name TEXT,
    branch TEXT,
    commit_sha TEXT,
    metadata TEXT,  -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_baselines_run_id ON regression_baselines(run_id);
CREATE INDEX IF NOT EXISTS idx_baselines_dataset ON regression_baselines(dataset_name);
CREATE INDEX IF NOT EXISTS idx_baselines_updated_at ON regression_baselines(updated_at DESC);
