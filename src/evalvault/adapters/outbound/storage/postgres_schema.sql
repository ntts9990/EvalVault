-- EvalVault PostgreSQL Database Schema
-- Stores evaluation runs, test case results, and metric scores

CREATE EXTENSION IF NOT EXISTS vector;

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
    metadata JSONB,  -- Tracker metadata (Phoenix, Langfuse, etc.)
    retrieval_metadata JSONB,  -- Retrieval metadata by test case
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

-- Run cluster map table
CREATE TABLE IF NOT EXISTS run_cluster_maps (
    run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
    map_id UUID NOT NULL,
    test_case_id VARCHAR(255) NOT NULL,
    cluster_id VARCHAR(255) NOT NULL,
    source TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id, map_id, test_case_id)
);

CREATE INDEX IF NOT EXISTS idx_cluster_maps_run_id ON run_cluster_maps(run_id);
CREATE INDEX IF NOT EXISTS idx_cluster_maps_map_id ON run_cluster_maps(map_id);

CREATE TABLE IF NOT EXISTS satisfaction_feedback (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
    test_case_id VARCHAR(255) NOT NULL,
    satisfaction_score DECIMAL(4, 2),
    thumb_feedback VARCHAR(10),
    comment TEXT,
    rater_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_run_id ON satisfaction_feedback(run_id);
CREATE INDEX IF NOT EXISTS idx_feedback_test_case_id ON satisfaction_feedback(test_case_id);

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

-- Multiturn evaluation tables
CREATE TABLE IF NOT EXISTS multiturn_runs (
    run_id UUID PRIMARY KEY,
    dataset_name VARCHAR(255) NOT NULL,
    dataset_version VARCHAR(50),
    model_name VARCHAR(255),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    finished_at TIMESTAMP WITH TIME ZONE,
    conversation_count INTEGER DEFAULT 0,
    turn_count INTEGER DEFAULT 0,
    metrics_evaluated JSONB,
    drift_threshold DOUBLE PRECISION,
    summary JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_multiturn_runs_dataset ON multiturn_runs(dataset_name);
CREATE INDEX IF NOT EXISTS idx_multiturn_runs_started_at ON multiturn_runs(started_at DESC);

CREATE TABLE IF NOT EXISTS multiturn_conversations (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES multiturn_runs(run_id) ON DELETE CASCADE,
    conversation_id VARCHAR(255) NOT NULL,
    turn_count INTEGER DEFAULT 0,
    drift_score DOUBLE PRECISION,
    drift_threshold DOUBLE PRECISION,
    drift_detected BOOLEAN DEFAULT FALSE,
    summary JSONB
);

CREATE INDEX IF NOT EXISTS idx_multiturn_conversations_run_id ON multiturn_conversations(run_id);
CREATE INDEX IF NOT EXISTS idx_multiturn_conversations_conv_id ON multiturn_conversations(conversation_id);

CREATE TABLE IF NOT EXISTS multiturn_turn_results (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES multiturn_runs(run_id) ON DELETE CASCADE,
    conversation_id VARCHAR(255) NOT NULL,
    turn_id VARCHAR(255) NOT NULL,
    turn_index INTEGER,
    role VARCHAR(50) NOT NULL,
    passed BOOLEAN DEFAULT FALSE,
    latency_ms INTEGER,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_multiturn_turns_run_id ON multiturn_turn_results(run_id);
CREATE INDEX IF NOT EXISTS idx_multiturn_turns_conv_id ON multiturn_turn_results(conversation_id);

CREATE TABLE IF NOT EXISTS multiturn_metric_scores (
    id SERIAL PRIMARY KEY,
    turn_result_id INTEGER NOT NULL REFERENCES multiturn_turn_results(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    score DECIMAL(5, 4) NOT NULL,
    threshold DECIMAL(5, 4)
);

CREATE INDEX IF NOT EXISTS idx_multiturn_scores_turn_id ON multiturn_metric_scores(turn_result_id);
CREATE INDEX IF NOT EXISTS idx_multiturn_scores_metric_name ON multiturn_metric_scores(metric_name);

-- Prompt storage tables
CREATE TABLE IF NOT EXISTS prompts (
    prompt_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    kind VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    checksum VARCHAR(128) NOT NULL,
    source TEXT,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prompts_checksum ON prompts(checksum);
CREATE INDEX IF NOT EXISTS idx_prompts_kind ON prompts(kind);

CREATE TABLE IF NOT EXISTS prompt_sets (
    prompt_set_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prompt_set_items (
    id SERIAL PRIMARY KEY,
    prompt_set_id UUID NOT NULL REFERENCES prompt_sets(prompt_set_id) ON DELETE CASCADE,
    prompt_id UUID NOT NULL REFERENCES prompts(prompt_id) ON DELETE CASCADE,
    role VARCHAR(255) NOT NULL,
    item_order INTEGER DEFAULT 0,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_prompt_set_items_set_id ON prompt_set_items(prompt_set_id);

CREATE TABLE IF NOT EXISTS run_prompt_sets (
    run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
    prompt_set_id UUID NOT NULL REFERENCES prompt_sets(prompt_set_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id, prompt_set_id)
);

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

-- Ops reports table
CREATE TABLE IF NOT EXISTS ops_reports (
    report_id UUID PRIMARY KEY,
    run_id UUID REFERENCES evaluation_runs(run_id) ON DELETE SET NULL,
    report_type VARCHAR(50) NOT NULL,
    format VARCHAR(20) NOT NULL,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ops_reports_run_id ON ops_reports(run_id);

-- Analysis pipeline results table
CREATE TABLE IF NOT EXISTS pipeline_results (
    result_id UUID PRIMARY KEY,
    intent VARCHAR(100) NOT NULL,
    query TEXT,
    run_id UUID,
    pipeline_id UUID,
    profile VARCHAR(50),
    tags JSONB,
    metadata JSONB,
    is_complete BOOLEAN NOT NULL DEFAULT TRUE,
    duration_ms DOUBLE PRECISION,
    final_output JSONB,
    node_results JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pipeline_results_created_at
    ON pipeline_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_results_intent
    ON pipeline_results(intent);
CREATE INDEX IF NOT EXISTS idx_pipeline_results_run_id
    ON pipeline_results(run_id);

CREATE TABLE IF NOT EXISTS stage_events (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
    stage_id TEXT NOT NULL,
    parent_stage_id TEXT,
    stage_type TEXT NOT NULL,
    stage_name TEXT,
    status TEXT,
    attempt INTEGER DEFAULT 1,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    duration_ms DOUBLE PRECISION,
    input_ref JSONB,
    output_ref JSONB,
    attributes JSONB,
    metadata JSONB,
    trace_id TEXT,
    span_id TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_stage_events_run_stage_id
    ON stage_events(run_id, stage_id);
CREATE INDEX IF NOT EXISTS idx_stage_events_run_id ON stage_events(run_id);
CREATE INDEX IF NOT EXISTS idx_stage_events_stage_type ON stage_events(stage_type);

CREATE TABLE IF NOT EXISTS stage_metrics (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
    stage_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    threshold DOUBLE PRECISION,
    evidence JSONB
);

CREATE INDEX IF NOT EXISTS idx_stage_metrics_run_id ON stage_metrics(run_id);
CREATE INDEX IF NOT EXISTS idx_stage_metrics_stage_id ON stage_metrics(stage_id);

CREATE TABLE IF NOT EXISTS regression_baselines (
    baseline_key TEXT PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
    dataset_name VARCHAR(255),
    branch TEXT,
    commit_sha VARCHAR(64),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_baselines_run_id ON regression_baselines(run_id);
CREATE INDEX IF NOT EXISTS idx_baselines_dataset ON regression_baselines(dataset_name);
CREATE INDEX IF NOT EXISTS idx_baselines_updated_at ON regression_baselines(updated_at DESC);
