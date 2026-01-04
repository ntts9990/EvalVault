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
    analysis_type TEXT NOT NULL,  -- 'statistical', 'nlp', 'causal', 'data_quality'
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
