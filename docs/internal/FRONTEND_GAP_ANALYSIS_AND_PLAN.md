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

## 4. Stage Analysis & Waterfall (Medium Priority)
*Ref: [OBSERVABILITY_PLAYBOOK.md], [06-production-tips.md]*

**Gap**: `evalvault stage` command exists, but no UI to visualize latency breakdown.

### Implementation Strategy
*   **Tab**: "Performance" in `RunDetails`.
*   **Visualization**: **Waterfall Chart**.
    *   Segments: `Retrieval` -> `Reranking` -> `Generation` -> `Evaluation`.
    *   *Insight*: Highlight the bottleneck stage (e.g., "Retrieval took 80% of time").

---

## 5. Domain Memory Insights (Medium Priority)
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

## 6. Technical Integration Plan

### API Extensions Needed
1.  `GET /runs/compare`: (Or client-side merge).
2.  `POST /runs/start`: Support `phoenix_config` (dataset/experiment names) and `batch_size`.
3.  `GET /domain/trends`: Endpoint to fetch metric history for a domain.

### Visual Style
*   **Consistency**: Use existing `lucide-react` icons and `Tailwind` spacing.
*   **Color Palette**:
    *   *Memory*: Purple/Violet (Brain theme).
    *   *Phoenix*: Orange/Fire (Phoenix theme).
    *   *Comparison*: Green (Improvement) / Red (Regression).

---

This plan aligns the Web UI with the capabilities described in the Tutorials, ensuring users can use the full power of EvalVault (including Phoenix, Memory, and Advanced Config) without dropping to the CLI.
