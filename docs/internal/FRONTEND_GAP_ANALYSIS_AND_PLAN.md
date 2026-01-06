# Frontend Gap Analysis & Implementation Guide

> Analysis of features present in CLI/Docs/Tutorials but missing in Frontend, with implementation strategies preserving the current UI/UX philosophy.

**Date**: 2026-01-05
**Reference**: Tutorials 01-07, Playbooks

---

## 1. Run Comparison (High Priority)
*Ref: [02-basic-evaluation.md] - "결과 비교"*

**Gap**: CLI supports `evalvault compare <id1> <id2>`, but Frontend lacks visual comparison.
**Goal**: Enable visual regression testing between two runs (Base vs Target).

### Implementation Strategy
*   **Entry**: `Dashboard` -> Select 2 runs -> Floating "Compare" Action.
*   **Page**: `/compare?base={id}&target={id}`
*   **Components**:
    *   **Delta Header**: Summary of changes (e.g., "Pass Rate: +5%").
    *   **Metric Delta Chart**: Horizontal bar chart showing gain/loss per metric.
    *   **Diff Table**:
        *   **Row**: Test Case.
        *   **Columns**: Base Answer | Target Answer | Diff Highlight.
        *   **Text Diff**: Highlight added/removed words in the answer (e.g., using `diff-match-patch`).
    *   **Filter**: "Regressed Cases Only" toggle.

---

## 2. Phoenix Observability Integration (High Priority)
*Ref: [04-phoenix-integration.md] - "Dataset/Experiment 동기화"*

**Gap**: CLI allows deep storage linking and drift analysis, but Frontend lacks both configuration and deep links.

### Implementation Strategy
*   **Configuration (Evaluation Studio)**:
    *   Add **"Observability Settings"** in Advanced Config.
    *   Fields: `Phoenix Project Name`, `Experiment Description`.
    *   *Why*: Allows users to group runs logically in Phoenix directly from the UI.
*   **Run Details**:
    *   **Header**: "View in Phoenix" button (External Link).
    *   **Drift Indicator**: Badge showing `Drift Score` (fetched from metadata).
    *   **Prompt Version**: "Prompt Changed" warning if `tracker_metadata.phoenix.prompts` indicates a diff.

---

## 3. Evaluation Studio Enhancements (Medium Priority)
*Ref: [02-basic-evaluation.md], [03-custom-metrics.md], [05-korean-rag.md], [06-production-tips.md]*

**Gap**: The current Studio is too simple compared to the rich CLI options available in tutorials.

### Implementation Strategy
*   **Dataset Management**:
    *   **Upload/Preview**: Allow uploading CSV/Excel/JSON directly in Studio (currently only in Knowledge Base).
    *   **Format Validation**: Show "JSON Structure Valid" checkmark.
*   **Metric Configuration**:
    *   **Custom Metrics**: Visually distinguish "Custom Metrics" (from `src/evalvault/domain/metrics`) vs "Standard Metrics".
    *   **Configuration**: Simple toggle for `Faithfulness` is not enough. Add "Strict Mode" or "Threshold" overrides per metric.
*   **Korean/Performance Settings**:
    *   **Tokenizer**: Display active tokenizer (Kiwi/Space) in run metadata.
    *   **Batch Size**: Slider for `Batch Size` (Performance Tip from *06*).

---

## 4. GraphRAG Configuration & KG Validation (High Priority)
*Ref: [LIGHTRAG_OPERATIONS_GUIDE.md], [CLI_GUIDE.md]*

**Gap**: Evaluation Studio exposes only `bm25/hybrid`. There is no UI for GraphRAG/KG input, and the Knowledge Base output is not directly usable with `--kg`.

### Implementation Strategy
*   **Evaluation Studio (Advanced Config)**:
    * Add `graphrag` to retriever modes and expose `top_k`.
    * Add KG JSON picker (upload + server path) alongside retriever docs.
    * Add inline note: GraphRAG fills contexts **only when empty**.
    * Add "Validate KG" action: show entity/relation counts and doc_id mismatches (first N).
*   **Knowledge Base**:
    * List KG build outputs in `data/kg` with "Use in Evaluation" action.
    * Provide "Normalize Format" toggle to wrap as `{ "knowledge_graph": ... }`.
    * Show doc_id alignment summary (KG `source_document_id` vs retriever docs `doc_id`).
*   **Backend**:
    * Accept KG payloads wrapped in `graph` or `knowledge_graph`.
    * Add KG validation endpoint (schema + doc_id match) and KG upload endpoint.

### Scope Proposal (v1)
*   **Phase 1 (MVP)**:
    * Enable `graphrag` retriever mode in Evaluation Studio.
    * Support KG file upload + server path selection.
    * Show a hard warning: GraphRAG only fills empty `contexts`.
*   **Phase 2 (Validation)**:
    * KG schema validation (entities/relations) and doc_id mismatch check (first N).
    * Surface validation result inline before run.
*   **Phase 3 (Knowledge Base UX)**:
    * List KG outputs in `data/kg` with "Use in Evaluation".
    * Normalize/export KG to `knowledge_graph` wrapper for CLI parity.

### API Priority (v1)
1. `POST /runs/options/kg` (upload KG JSON, return server path)
2. `POST /knowledge/validate` (schema + doc_id alignment report)
3. `GET /knowledge/kg-files` (list server-side KG outputs)

### Validation Spec (v1)
**Goal**: Fail fast on invalid KG structure and warn on doc_id mismatches before running GraphRAG.

**Request (JSON)**:
```json
{
  "kg_path": "data/kg/knowledge_graph.json",
  "retriever_docs_path": "data/retriever_docs/graphrag_docs.json",
  "max_samples": 10
}
```
*Optional*: allow inline `kg_payload` to validate without server file storage.
*Normalization*: accept `{ "graph": ... }` or `{ "knowledge_graph": ... }` wrappers.

**Validation Checks**
1. **Schema**
   - `entities`/`relations` are arrays.
   - Entity: `name`, `entity_type` required; `confidence` in `[0,1]`; `provenance` in `regex|llm|manual|unknown` (default `unknown`).
   - Relation: `source`, `target`, `relation_type` required; `source != target`; `confidence` in `[0,1]`.
2. **Integrity**
   - Relation endpoints exist in entity set (orphan relations -> warning).
   - Duplicate entity names reported (first N).
3. **doc_id Alignment**
   - KG `source_document_id` must exist in retriever docs `doc_id`.
   - Missing `source_document_id` counted (warning).
   - Unused retriever docs reported (info).

**Response (JSON)**:
```json
{
  "valid": false,
  "errors": [
    {"code": "KG_SCHEMA", "message": "Missing entities array"}
  ],
  "warnings": [
    {"code": "DOC_ID_MISMATCH", "message": "Unknown doc_id: doc-999"}
  ],
  "summary": {
    "entities": 120,
    "relations": 310,
    "orphan_relations": 4,
    "missing_source_document_id": 12,
    "doc_id_mismatches": 7
  },
  "samples": {
    "orphan_relations": [{"source": "A", "target": "B"}],
    "unknown_doc_ids": ["doc-999"]
  }
}
```

**UI Usage**
- `valid=false` + `errors` → Run disabled.
- `warnings` only → Allow run with “Run Anyway” confirmation.
- Surface doc_id mismatch counts inline with a “Fix doc_id” hint.

### Out of Scope (v1)
* KG visualization/graph explorer
* KG diff/versioning UI
* Auto doc_id reconciliation or mapping wizard

---

## 5. Stage Analysis & Waterfall (Medium Priority)
*Ref: [OBSERVABILITY_PLAYBOOK.md], [06-production-tips.md]*

**Gap**: `evalvault stage` command exists, but no UI to visualize latency breakdown.

### Implementation Strategy
*   **Tab**: "Performance" in `RunDetails`.
*   **Visualization**: **Waterfall Chart**.
    *   Segments: `Retrieval` -> `Reranking` -> `Generation` -> `Evaluation`.
    *   *Insight*: Highlight the bottleneck stage (e.g., "Retrieval took 80% of time").

---

## 6. Domain Memory Insights (Medium Priority)
*Ref: [07-domain-memory.md]*

**Gap**: Tutorial mentions "Trend Analysis" and "Context Augmentation", but UI only lists Facts/Behaviors.

### Implementation Strategy
*   **Trend Visualization (DomainMemory Page)**:
    *   **Chart**: Line chart showing `Faithfulness` trend over time for the domain.
    *   **Baseline Comparison**: "vs. Last Month" delta.
*   **Context Augmentation Preview (RunDetails)**:
    *   **Test Case View**: Clearly separate "Retrieved Context" from "Memory Facts".
    *   *UI*: Use a distinct colored block or icon for `[Related Facts]` injected by memory.

---

## 7. Technical Integration Plan

### API Extensions Needed
1.  `GET /runs/compare`: (Or client-side merge).
2.  `POST /runs/start`: Support `phoenix_config` (dataset/experiment names) and `batch_size`.
3.  `GET /domain/trends`: Endpoint to fetch metric history for a domain.
4.  `POST /runs/options/kg`: Upload KG JSON file (server storage).
5.  `POST /knowledge/validate`: Validate KG schema and doc_id mapping.
6.  `GET /knowledge/kg-files`: List KG outputs in `data/kg`.

### Visual Style
*   **Consistency**: Use existing `lucide-react` icons and `Tailwind` spacing.
*   **Color Palette**:
    *   *Memory*: Purple/Violet (Brain theme).
    *   *Phoenix*: Orange/Fire (Phoenix theme).
    *   *Comparison*: Green (Improvement) / Red (Regression).

---

This plan aligns the Web UI with the capabilities described in the Tutorials, ensuring users can use the full power of EvalVault (including Phoenix, Memory, and Advanced Config) without dropping to the CLI.
