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
