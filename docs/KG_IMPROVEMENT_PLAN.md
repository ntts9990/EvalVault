# Knowledge Graph Generation Improvement Plan

## 1. Critical Evaluation of Existing Options

### Option 1 — NetworkX Migration
- Strengths from `docs/options.md`: proven algorithms, performance, maintenance benefits.
- Missing considerations: does not address current extraction accuracy, canonicalization, or data quality; assumes swapping the backing structure unlocks value without defining how new algorithms improve generated test cases. Lack of discussion about graph schema governance (attributes, constraints) means we might port current flaws into the new graph.
- Risk: effort estimate (2–3h) is optimistic because we must rewrite serialization, statistics, and tests; ignoring these leads to regression.

### Option 2 — RAGAS TestsetGenerator
- Strengths: closer alignment with LLM-driven data generation, richer question types.
- Gaps: evaluation overlooks multilingual (Korean) support, prompt governance, reproducibility, and how to reconcile RAGAS’ abstractions with EvalVault’s dataset schema. The trade-off between deterministic, auditable datasets and stochastic LLM output is not quantified, so this “optional” integration could silently change evaluation outcomes.

### Option 3 — LlamaIndex KG Index
- Strengths: end-to-end solution.
- However, the assessment dismisses it mainly on complexity without comparing concrete benefits (e.g., streaming ingestion, persistence layers). The document also overlooks that adopting LlamaIndex could unify KG generation with online RAG, which might be necessary later. Purely discarding it limits future extensibility discussions.

### Existing Phase Proposal
- The “Phase 1/2/3” plan copies the option list instead of aligning with EvalVault’s objective: produce reliable, domain-specific evaluation datasets. It lacks checkpoints for extraction quality, schema validation, or observability, so even after completion we cannot verify that KG-generated questions are materially better.

## 2. Proposed Direction: Domain-Aware Hybrid Pipeline

Our goal is trustworthy KG-driven datasets for insurance QA, not generic KG tooling. We should focus on a pipeline that keeps deterministic control while unlocking targeted LLM assistance and better graph analytics.

### Core Principles
1. **Deterministic spine**: keep rule-based extraction for insurance-specific terminology, but enrich entities with normalized schemas (Pydantic models) and context provenance to ensure reproducibility.
2. **Enrichment on demand**: use lightweight LLM passes (via existing ports) only when the extractor produces low confidence or ambiguous relations; log prompts/responses for audit.
3. **NetworkX-backed knowledge store**: migrate storage to `nx.MultiDiGraph`, but pair it with validation layers (schema + metrics) so we immediately exploit algorithms such as `all_simple_paths`, community detection, and coverage analytics.
4. **Scenario synthesis interface**: expose KG slices to the dataset generator via composable strategies (single-hop, multi-hop, comparative, adversarial). Each strategy records which nodes/edges were used, satisfying EvalVault’s traceability requirements.
5. **Feedback loop**: automatically score KG integrity (degree distributions, orphan nodes, relation sparsity) and feed signals into CLI reports so contributors see whether changes improved coverage.

## 3. Implementation Plan

### Phase A — Observability & Schema (0.5–1 day)
- Define `EntityModel`/`RelationModel` using Pydantic in `src/evalvault/domain/entities_kg.py`.
- Add validation + serialization helpers so existing extractor output is normalized (e.g., `canonical_name`, `source_doc_id`, `confidence`).
- Instrument `KnowledgeGraphGenerator.build_graph` to emit metrics (counts, missing attributes) through the existing reporting utility or simple logging.

### Phase B — NetworkX Migration with Compatibility Layer (1–1.5 days)
- Introduce `NetworkXKnowledgeGraph` adapter wrapping `nx.MultiDiGraph` while preserving the public API expected by services/tests.
- Store entity metadata as node attributes, relations as edge attributes, and expose traversal helpers (`neighbors`, `relations`, `all_paths`) that proxy to NetworkX.
- Update unit tests (`tests/unit/test_kg_generator.py`) to validate graph invariants and new helper behavior.
- Document the change in `docs/kg_generation_plan.md` and `README` (short section) once shipped.

### Phase C — Confidence-Aware Extraction (1 day)
- Extend `EntityExtractor` to return confidence scores (regex match strength, frequency, or heuristics).
- Add an optional `LLMRelationAugmenter` (adapter under `src/evalvault/adapters/llm/`) that is invoked only when confidence < threshold; it should receive snippets and return validated relations.
- Persist provenance metadata (`"source": "regex"` vs `"llm"`) to ensure downstream consumers can filter.

### Phase D — Scenario Strategy Layer (1 day)
- Refactor question generation into strategy classes (`SingleHopStrategy`, `MultiHopStrategy`, `ComparisonStrategy`, `CounterfactualStrategy`).
- Each strategy accepts the graph plus selection parameters (entity types, hop count) and returns structured payloads used to build `TestCase`s.
- Register strategies with a factory so CLI/CLI configs can toggle them (`evalvault run ... --kg-strategy multi-hop`).
- Update documentation and add unit tests for each strategy.

### Phase E — Validation & Tooling (0.5 day)
- Add CLI subcommand `evalvault kg stats` that dumps entity/edge counts, isolated nodes, and relation coverage to help contributors evaluate data quality.
- Integrate with existing metrics pipeline to record KG statistics alongside dataset metadata.

## 4. Milestones & Deliverables
- **Milestone 1 (Phases A+B)**: deterministic NetworkX-backed KG with schema validation; provides immediate algorithmic benefits and resilience.
- **Milestone 2 (Phase C)**: confidence-aware extraction plus optional LLM augmentation; ensures higher recall without sacrificing auditability.
- **Milestone 3 (Phase D+E)**: richer question strategies and visibility tooling; unlocks new dataset types and gives maintainers actionable metrics.

## 5. Success Metrics
- Extraction precision/recall measured on curated fixtures (baseline today vs. after Phase C).
- Reduction of orphan entities and dangling relations by ≥30% after Phase B.
- Ability to generate >3 distinct scenario types per dataset run (Phase D) with explicit provenance metadata.
- Contributor satisfaction: KG stats command adopted in PR checklists (qualitative but track usage).

## 6. Next Steps
1. Align stakeholders on the phased roadmap during the next sprint planning.
2. Create tickets for each phase with acceptance criteria derived from this document.
3. Begin Phase A by introducing the schema models and instrumentation; this work unblocks the rest of the roadmap.
