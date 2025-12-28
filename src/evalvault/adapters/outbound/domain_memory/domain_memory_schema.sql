-- EvalVault Domain Memory Schema
-- Based on "Memory in the Age of AI Agents: A Survey" framework
-- Forms: Flat (Phase 1), Planar/Hierarchical (Phase 2-3)
-- Functions: Factual, Experiential, Working layers
-- Dynamics: Formation, Evolution, Retrieval strategies

-- =========================================================================
-- Factual Layer - 검증된 도메인 사실 (SPO 트리플)
-- =========================================================================

CREATE TABLE IF NOT EXISTS factual_facts (
    fact_id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,           -- 엔티티 이름
    predicate TEXT NOT NULL,         -- 관계 타입
    object TEXT NOT NULL,            -- 대상 엔티티
    language TEXT DEFAULT 'ko',      -- 언어 코드 (ko, en)
    domain TEXT DEFAULT 'default',   -- 도메인 (insurance, legal, medical)
    fact_type TEXT DEFAULT 'verified', -- verified, inferred, contradictory
    verification_score REAL DEFAULT 1.0, -- 0.0-1.0
    verification_count INTEGER DEFAULT 1,
    source_document_ids TEXT,        -- JSON array of document IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 검색 최적화를 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_facts_domain_lang ON factual_facts(domain, language);
CREATE INDEX IF NOT EXISTS idx_facts_subject ON factual_facts(subject);
CREATE INDEX IF NOT EXISTS idx_facts_predicate ON factual_facts(predicate);
CREATE INDEX IF NOT EXISTS idx_facts_object ON factual_facts(object);
CREATE INDEX IF NOT EXISTS idx_facts_triple ON factual_facts(subject, predicate, object);
CREATE INDEX IF NOT EXISTS idx_facts_verification_score ON factual_facts(verification_score DESC);
CREATE INDEX IF NOT EXISTS idx_facts_last_verified ON factual_facts(last_verified DESC);

-- =========================================================================
-- Experiential Layer - 평가에서 학습된 패턴
-- =========================================================================

CREATE TABLE IF NOT EXISTS learning_memories (
    learning_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,            -- 원본 평가 run ID
    domain TEXT DEFAULT 'default',
    language TEXT DEFAULT 'ko',
    entity_type_reliability TEXT,    -- JSON: {entity_type: reliability_score}
    relation_type_reliability TEXT,  -- JSON: {relation_type: reliability_score}
    failed_patterns TEXT,            -- JSON array of failed patterns
    successful_patterns TEXT,        -- JSON array of successful patterns
    faithfulness_by_entity_type TEXT, -- JSON: {entity_type: faithfulness_score}
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_learnings_domain_lang ON learning_memories(domain, language);
CREATE INDEX IF NOT EXISTS idx_learnings_run_id ON learning_memories(run_id);
CREATE INDEX IF NOT EXISTS idx_learnings_timestamp ON learning_memories(timestamp DESC);

-- =========================================================================
-- Behavior Layer - Metacognitive Reuse (재사용 가능한 행동)
-- =========================================================================

CREATE TABLE IF NOT EXISTS behavior_entries (
    behavior_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    trigger_pattern TEXT,            -- 트리거 조건 (regex 또는 키워드)
    action_sequence TEXT,            -- JSON array of action steps
    success_rate REAL DEFAULT 0.0,   -- 역사적 성공률
    token_savings INTEGER DEFAULT 0, -- 절감되는 토큰 수
    applicable_languages TEXT DEFAULT '["ko", "en"]', -- JSON array
    domain TEXT DEFAULT 'default',
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    use_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_behaviors_domain ON behavior_entries(domain);
CREATE INDEX IF NOT EXISTS idx_behaviors_success_rate ON behavior_entries(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_behaviors_use_count ON behavior_entries(use_count DESC);
CREATE INDEX IF NOT EXISTS idx_behaviors_last_used ON behavior_entries(last_used DESC);

-- =========================================================================
-- Working Layer - 현재 세션의 활성 컨텍스트
-- =========================================================================

CREATE TABLE IF NOT EXISTS memory_contexts (
    session_id TEXT PRIMARY KEY,
    domain TEXT DEFAULT 'default',
    language TEXT DEFAULT 'ko',
    active_entities TEXT,            -- JSON array of entity names
    entity_type_distribution TEXT,   -- JSON: {entity_type: count}
    current_quality_metrics TEXT,    -- JSON: {metric_name: value}
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contexts_domain ON memory_contexts(domain);
CREATE INDEX IF NOT EXISTS idx_contexts_updated_at ON memory_contexts(updated_at DESC);

-- =========================================================================
-- Fact Sources - 사실과 문서 간의 관계 (Phase 2)
-- =========================================================================

CREATE TABLE IF NOT EXISTS fact_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    extraction_confidence REAL DEFAULT 1.0,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fact_id) REFERENCES factual_facts(fact_id) ON DELETE CASCADE,
    UNIQUE(fact_id, document_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_sources_fact_id ON fact_sources(fact_id);
CREATE INDEX IF NOT EXISTS idx_fact_sources_document_id ON fact_sources(document_id);

-- =========================================================================
-- Memory Evolution Log - 메모리 변화 추적 (Phase 2)
-- =========================================================================

CREATE TABLE IF NOT EXISTS memory_evolution_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,         -- consolidate, update, forget, decay
    target_type TEXT NOT NULL,       -- fact, learning, behavior
    target_id TEXT NOT NULL,
    details TEXT,                    -- JSON: operation-specific details
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evolution_log_operation ON memory_evolution_log(operation);
CREATE INDEX IF NOT EXISTS idx_evolution_log_target ON memory_evolution_log(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_evolution_log_performed_at ON memory_evolution_log(performed_at DESC);

-- =========================================================================
-- Full-Text Search (FTS5) - Phase 2 Retrieval Dynamics
-- =========================================================================

-- Facts FTS5 virtual table for keyword search
CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
    fact_id UNINDEXED,
    subject,
    predicate,
    object,
    content='factual_facts',
    content_rowid='rowid'
);

-- Triggers to keep FTS5 index synchronized with factual_facts
CREATE TRIGGER IF NOT EXISTS facts_fts_insert AFTER INSERT ON factual_facts BEGIN
    INSERT INTO facts_fts(rowid, fact_id, subject, predicate, object)
    VALUES (NEW.rowid, NEW.fact_id, NEW.subject, NEW.predicate, NEW.object);
END;

CREATE TRIGGER IF NOT EXISTS facts_fts_delete AFTER DELETE ON factual_facts BEGIN
    INSERT INTO facts_fts(facts_fts, rowid, fact_id, subject, predicate, object)
    VALUES ('delete', OLD.rowid, OLD.fact_id, OLD.subject, OLD.predicate, OLD.object);
END;

CREATE TRIGGER IF NOT EXISTS facts_fts_update AFTER UPDATE ON factual_facts BEGIN
    INSERT INTO facts_fts(facts_fts, rowid, fact_id, subject, predicate, object)
    VALUES ('delete', OLD.rowid, OLD.fact_id, OLD.subject, OLD.predicate, OLD.object);
    INSERT INTO facts_fts(rowid, fact_id, subject, predicate, object)
    VALUES (NEW.rowid, NEW.fact_id, NEW.subject, NEW.predicate, NEW.object);
END;

-- Behaviors FTS5 virtual table for context-based search
CREATE VIRTUAL TABLE IF NOT EXISTS behaviors_fts USING fts5(
    behavior_id UNINDEXED,
    description,
    trigger_pattern,
    content='behavior_entries',
    content_rowid='rowid'
);

-- Triggers to keep behaviors FTS5 index synchronized
CREATE TRIGGER IF NOT EXISTS behaviors_fts_insert AFTER INSERT ON behavior_entries BEGIN
    INSERT INTO behaviors_fts(rowid, behavior_id, description, trigger_pattern)
    VALUES (NEW.rowid, NEW.behavior_id, NEW.description, NEW.trigger_pattern);
END;

CREATE TRIGGER IF NOT EXISTS behaviors_fts_delete AFTER DELETE ON behavior_entries BEGIN
    INSERT INTO behaviors_fts(behaviors_fts, rowid, behavior_id, description, trigger_pattern)
    VALUES ('delete', OLD.rowid, OLD.behavior_id, OLD.description, OLD.trigger_pattern);
END;

CREATE TRIGGER IF NOT EXISTS behaviors_fts_update AFTER UPDATE ON behavior_entries BEGIN
    INSERT INTO behaviors_fts(behaviors_fts, rowid, behavior_id, description, trigger_pattern)
    VALUES ('delete', OLD.rowid, OLD.behavior_id, OLD.description, OLD.trigger_pattern);
    INSERT INTO behaviors_fts(rowid, behavior_id, description, trigger_pattern)
    VALUES (NEW.rowid, NEW.behavior_id, NEW.description, NEW.trigger_pattern);
END;

-- =========================================================================
-- Phase 5: Planar Form - KG Integration
-- =========================================================================

-- Add KG integration columns to factual_facts (if not exists)
-- Note: SQLite doesn't support IF NOT EXISTS for ALTER TABLE,
-- so these are handled programmatically in the adapter

-- KG Entity binding table for explicit KG links
CREATE TABLE IF NOT EXISTS fact_kg_bindings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_id TEXT NOT NULL,
    kg_entity_id TEXT NOT NULL,          -- KG 엔티티 이름/ID
    kg_relation_type TEXT,               -- KG 관계 타입
    binding_confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fact_id) REFERENCES factual_facts(fact_id) ON DELETE CASCADE,
    UNIQUE(fact_id, kg_entity_id)
);

CREATE INDEX IF NOT EXISTS idx_kg_bindings_fact_id ON fact_kg_bindings(fact_id);
CREATE INDEX IF NOT EXISTS idx_kg_bindings_kg_entity ON fact_kg_bindings(kg_entity_id);
CREATE INDEX IF NOT EXISTS idx_kg_bindings_relation_type ON fact_kg_bindings(kg_relation_type);

-- =========================================================================
-- Phase 5: Hierarchical Form - Summary Layers
-- =========================================================================

-- Fact hierarchy table for parent-child relationships
CREATE TABLE IF NOT EXISTS fact_hierarchy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_fact_id TEXT NOT NULL,
    child_fact_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_fact_id) REFERENCES factual_facts(fact_id) ON DELETE CASCADE,
    FOREIGN KEY (child_fact_id) REFERENCES factual_facts(fact_id) ON DELETE CASCADE,
    UNIQUE(parent_fact_id, child_fact_id)
);

CREATE INDEX IF NOT EXISTS idx_hierarchy_parent ON fact_hierarchy(parent_fact_id);
CREATE INDEX IF NOT EXISTS idx_hierarchy_child ON fact_hierarchy(child_fact_id);
