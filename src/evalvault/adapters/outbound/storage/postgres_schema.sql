-- EvalVault PostgreSQL Database Schema
-- Stores evaluation runs, test case results, and metric scores

-- Main evaluation runs table
CREATE TABLE IF NOT EXISTS evaluation_runs (
    run_id UUID PRIMARY KEY,
    dataset_name VARCHAR(255) NOT NULL,
    dataset_version VARCHAR(50),
    model_name VARCHAR(255) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    finished_at TIMESTAMP WITH TIME ZONE,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10, 6),
    pass_rate DECIMAL(5, 4),
    metrics_evaluated JSONB,  -- JSON array of metric names
    thresholds JSONB,  -- JSON object of metric thresholds
    langfuse_trace_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying by dataset and model
CREATE INDEX IF NOT EXISTS idx_runs_dataset ON evaluation_runs(dataset_name);
CREATE INDEX IF NOT EXISTS idx_runs_model ON evaluation_runs(model_name);
CREATE INDEX IF NOT EXISTS idx_runs_started_at ON evaluation_runs(started_at DESC);

-- Test case results table
CREATE TABLE IF NOT EXISTS test_case_results (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
    test_case_id VARCHAR(255) NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6),
    trace_id VARCHAR(255),
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    question TEXT,
    answer TEXT,
    contexts JSONB,  -- JSON array of context strings
    ground_truth TEXT
);

CREATE INDEX IF NOT EXISTS idx_results_run_id ON test_case_results(run_id);

-- Metric scores table
CREATE TABLE IF NOT EXISTS metric_scores (
    id SERIAL PRIMARY KEY,
    result_id INTEGER NOT NULL REFERENCES test_case_results(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    score DECIMAL(5, 4) NOT NULL,
    threshold DECIMAL(5, 4) NOT NULL,
    reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_scores_result_id ON metric_scores(result_id);
CREATE INDEX IF NOT EXISTS idx_scores_name ON metric_scores(name);

-- Experiments table for A/B testing
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    hypothesis TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    metrics_to_compare JSONB,  -- JSON array of metric names
    conclusion TEXT
);

CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_created_at ON experiments(created_at DESC);

-- Experiment groups table
CREATE TABLE IF NOT EXISTS experiment_groups (
    id SERIAL PRIMARY KEY,
    experiment_id UUID NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    run_ids JSONB  -- JSON array of run_id strings
);

CREATE INDEX IF NOT EXISTS idx_groups_experiment_id ON experiment_groups(experiment_id);

-- Analysis results table
CREATE TABLE IF NOT EXISTS analysis_results (
    analysis_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    result_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analysis_run_id ON analysis_results(run_id);
CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type);

-- Analysis reports table
CREATE TABLE IF NOT EXISTS analysis_reports (
    report_id UUID PRIMARY KEY,
    run_id UUID REFERENCES evaluation_runs(run_id) ON DELETE SET NULL,
    experiment_id UUID REFERENCES experiments(experiment_id) ON DELETE SET NULL,
    report_type VARCHAR(50) NOT NULL,
    format VARCHAR(20) NOT NULL,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_run_id ON analysis_reports(run_id);
CREATE INDEX IF NOT EXISTS idx_reports_experiment_id ON analysis_reports(experiment_id);
