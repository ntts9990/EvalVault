# Dependency Audit — 2026-05-21 (Phase 3.5 L-S0)

> **Audit branch**: `refactor/l-s0-dependency-audit` (base c89085f)
> **Purpose**: Inventory all external dependencies (Python + frontend), compare installed vs latest, classify per directive `project_phase35_library_update.md`: (a) safe minor/patch update / (b) major bump with breaking changes / (c) intentional pin (document reason).
> **Method**: `uv pip show` + PyPI JSON API + `npm outdated --json`. All numbers as of audit date.
> **Sequence after audit**: L-S1 (safe bulk) → L-S2/3/4/5 (major bumps, separate slices) → L-S6 (frontend) → Phase 4 (web redesign).

---

## 1. Executive Summary

| Category | Count | Examples |
|---|---|---|
| **(a) Safe minor/patch ready** | 10 | pydantic, fastapi, typer, mlflow, chainlit, pypdf, uvicorn, datasets, psycopg, ruff |
| **(b) Major bump (audit needed)** | 8 | openai, pandas, chardet, rich, anthropic, langchain-openai, langfuse, arize-phoenix, instructor (large minor) |
| **(c) Intentional pin / blocked** | 3 | matplotlib<3.9.0, scikit-learn<1.4.0, ragas==0.4.2 |
| **Already latest** | 4 | networkx, openpyxl, pgvector, truststore |
| **Frontend major bump** | 2 | lucide-react (0.562→1.16), plotly.js-dist-min (2.35→3.5) |
| **Frontend already latest** | 11 | react, vite, tailwind, recharts, etc. |

**Key risks identified during audit:**

1. **`ragas==0.4.2` hard pin** is stale — patch 0.4.3 is available on PyPI but blocked by the `==` operator. No 1.x line has shipped yet, so the original L-S2 plan ("ragas major bump") was based on a false premise. Recommend relaxing to `ragas>=0.4.2,<0.5` immediately to pick up patch fixes.

2. **`openai 1.40.8 → 2.37.0`** is a major version jump with API changes. EvalVault uses openai throughout the LLM adapter + evaluator + faithfulness fallback + cost calculation (D-S5a). This bump alone is a multi-day slice.

3. **`anthropic 0.32.0 → 0.103.1`** is also massive (Anthropic SDK iterates fast). Affects `anthropic_adapter.py` and the new RetryPolicy plumbing (A-S1).

4. **`pandas 2.1.4 → 3.0.3`** is the biggest mainstream Python ecosystem disruption — pandas 3.0 dropped several long-deprecated APIs. EvalVault uses pandas in `pipeline_orchestrator`, several report renderers, dataset loaders, and analysis modules.

5. **`langchain-openai 0.2.2 → 1.2.1`** is a major bump — LangChain itself stabilized at 1.x in late 2025. Affects the Ragas integration boundary.

6. **`matplotlib<3.9.0` cap** is documented as a manim/scikit-learn compat constraint. The actual blocker should be re-verified — if manim is dropped (or moved to optional), the cap can lift to 3.10.x.

7. **Frontend `lucide-react` and `plotly.js-dist-min` jumped majors**. Visual artifacts (icons, charts) may change. Best handled inside Phase 4 web redesign rather than a standalone slice.

---

## 2. Python Dependencies (Runtime + Optional Extras)

### 2.1 Inventory + Classification

| Package | Installed | Latest | Class | Rationale |
|---|---|---|---|---|
| ragas | 0.4.2 | **0.4.3** | (c)→(a) | Hard pin (`==`) blocks even patches. Relax to `>=0.4.2,<0.5` to ship 0.4.3 in L-S1. No 1.x line yet. |
| pydantic | 2.12.5 | **2.13.4** | (a) | Patch+minor in 2.x line. Safe bulk. |
| pydantic-settings | (installed) | (current) | (a) | Track pydantic. |
| instructor | 1.4.1 | **1.15.1** | (b) | 1.4 → 1.15 is many minor releases; verify Pydantic-schema features. D-S5d uses Instructor — adoption opportunity. |
| openai | 1.40.8 | **2.37.0** | (b) | 1.x → 2.x major. API shapes changed (Responses API, structured outputs default). Slice-level audit. |
| langchain-openai | 0.2.2 | **1.2.1** | (b) | 0.x → 1.x major. LangChain stabilized at 1.x. Affects ragas integration. |
| fastapi | 0.128.0 | **0.136.1** | (a) | Minor bumps in 0.x. Safe bulk. |
| typer | 0.21.0 | **0.25.1** | (a) | Minor bumps. New completion/Rich features. |
| uvicorn | 0.40.0 | **0.47.0** | (a) | Minor bumps. Safe. |
| pandas | 2.1.4 | **3.0.3** | (b) | 2.x → 3.x major. APIs removed/changed. Affects multiple modules. |
| matplotlib | 3.8.4 | **3.10.9** | (c) | Capped `<3.9.0`. Re-verify why (manim compat). Lift if manim is removed. |
| scikit-learn | 1.3.2 | **1.8.0** | (c) | Capped `<1.4.0`. Re-verify why. Several minor versions blocked. |
| networkx | 3.6.1 | 3.6.1 | already-latest | — |
| pypdf | 6.6.0 | **6.12.0** | (a) | Minor bumps. Safe. |
| truststore | 0.10.4 | 0.10.4 | already-latest | — |
| openpyxl | 3.1.5 | 3.1.5 | already-latest | — |
| chardet | 5.2.0 | **7.4.3** | (b) | 5.x → 7.x. Two majors jumped. API may change. |
| xlrd | (installed) | 2.0.2 (stable) | already-latest | — |
| rich | 13.9.4 | **15.0.0** | (b) | 13 → 15. Two majors. Verify CLI output compatibility. |
| chainlit | 2.9.5 | **2.11.1** | (a) | Minor in 2.x. |
| anthropic | 0.32.0 | **0.103.1** | (b) | Massive jump (0.32 → 0.103). Anthropic SDK pre-1.0 ships rapidly. |
| langfuse | 3.11.2 | **4.6.1** | (b) | 3.x → 4.x major. Tracker adapter affected. |
| mlflow | 3.8.1 | **3.12.0** | (a) | Minor bumps in 3.x. Safe. |
| arize-phoenix | 12.27.0 | **15.11.1** | (b) | 12 → 15. Three majors. Phoenix moves fast. |
| psycopg | 3.3.2 | **3.3.4** | (a) | Patch. Safe. |
| pgvector | 0.4.2 | 0.4.2 | already-latest | — |
| ruff | 0.15.13 | **0.15.14** | (a) | Patch. Safe. |
| pytest | 9.0.3 | 9.0.3 | already-latest | — |
| pytest-asyncio | 1.3.0 | 1.3.0 | already-latest | — |
| datasets | 4.4.2 | **4.8.5** | (a) | Minor bumps. |
| sentence-transformers | (extra) | 5.5.1 latest | (a) when extra installed | — |
| kiwipiepy | (extra) | 0.23.1 latest | (a) when extra installed | — |
| faiss-cpu | (extra) | 1.13.2 latest | (a) when extra installed | — |
| lm-eval | (extra) | 0.4.12 latest | (a) when extra installed | — |
| manim | (extra, in dev) | 0.20.1 latest | (a or audit) | Build dep — verify pycairo compat still applies. Consider dropping if unused. |
| aeon | (extra timeseries) | 1.4.0 latest | (a) | Time series analysis. |
| numba | (extra timeseries) | 0.65.1 latest | (a) | — |
| mkdocs | (docs extra) | 1.6.1 latest | (a) | — |
| mkdocs-material | (docs extra) | 9.7.6 latest | (a) | — |
| mkdocstrings | (docs extra, `>=0.24.0` floor) | **1.0.4** | (b) | 0.x → 1.x major. Stability declaration. Worth bumping. |

### 2.2 Intentional pin re-evaluation

| Pin | Stated reason | Current validity | Recommended action |
|---|---|---|---|
| `ragas==0.4.2` | RagasEvaluator surgery would be needed for any version bump | Hard pin blocks 0.4.3 patches; D-S2/D-S5 already refactored the surrounding code | **Relax to `>=0.4.2,<0.5`** in L-S1 (still constrains majors, allows patches) |
| `matplotlib>=3.8.0,<3.9.0` | manim/scikit-learn compat | manim has been on 0.20.x for a while; check if pycairo issue still applies at matplotlib 3.10 | L-S0 follow-up: test the actual constraint. If safe, lift cap in L-S1. |
| `scikit-learn>=1.3.0,<1.4.0` | Unstated; likely manim or aeon | manim doesn't depend on sklearn directly. aeon may. Verify against aeon 1.4.0. | L-S0 follow-up: test. Likely liftable. |

---

## 3. Frontend Dependencies (`frontend/package.json`)

### 3.1 Inventory + Classification

| Package | Installed | Latest | Class | Rationale |
|---|---|---|---|---|
| react | 19.2.x | 19.2.6 | already-latest | — |
| react-dom | 19.2.x | 19.2.6 | already-latest | — |
| @types/react | 19.2.x | 19.2.5 | already-latest | — |
| @types/react-dom | 19.2.x | 19.2.3 | already-latest | — |
| react-router-dom | 7.11.x | 7.15.1 | (a) | Caret range covers latest. |
| vite | 7.2.x | 7.2.4 | already-latest | — |
| @vitejs/plugin-react | 5.1.x | 5.1.1 | already-latest | — |
| typescript | 5.9.3 | (current) | already-latest | — |
| eslint | 9.39.x | 9.39.1 | already-latest | — |
| typescript-eslint | 8.46.x | 8.46.4 | already-latest | — |
| tailwindcss | 4.1.x | 4.1.18 | already-latest | — |
| @tailwindcss/postcss | 4.1.x | 4.1.18 | already-latest | — |
| @tailwindcss/vite | 4.1.x | 4.1.18 | already-latest | — |
| @tailwindcss/typography | 0.5.x | 0.5.16 | already-latest | — |
| postcss | 8.5.6 | 8.5.6 | already-latest | — |
| autoprefixer | 10.4.x | 10.4.23 | already-latest | — |
| @ai-sdk/react | 3.0.x | 3.0.190 | already-latest | — |
| ai | 6.0.x | 6.0.188 | already-latest | — |
| react-markdown | 10.1.0 | 10.1.0 | already-latest | — |
| remark-gfm | 4.0.x | 4.0.1 | already-latest | — |
| @radix-ui/react-slot | 1.2.4 | 1.2.4 | already-latest | — |
| clsx | 2.1.1 | 2.1.1 | already-latest | — |
| tailwind-merge | 3.4.x | 3.6.0 | already-latest | — |
| lucide-react | **0.562.0** | **1.16.0** | (b) | 0.x → 1.x major. Icon API stabilization. Many icon name changes possible. |
| plotly.js-dist-min | **2.35.3** | **3.5.1** | (b) | 2.x → 3.x major. Internal API changes; React wrappers may need updates. |
| recharts | 3.6.0 | 3.8.1 | (a) | Minor bumps in 3.x. |
| @playwright/test | 1.57.0 | (current) | already-latest | — |
| @types/node | 24.10.x | 24.10.1 | already-latest | — |

---

## 4. Recommended Slice Sequence (Refined)

Original Phase 3.5 plan had L-S0 → L-S1 → L-S2 (ragas) → L-S3/L-S4/L-S5/L-S6. The audit reveals ragas has no 1.x line, so L-S2 is downsized; **other major bumps are the real cost**. Revised:

```
L-S0 ✓ (this doc)
  ↓
L-S1: safe minor/patch bulk bump (no API breakage expected)
  - pydantic 2.12.5 → 2.13.4
  - fastapi 0.128.0 → 0.136.1
  - typer 0.21.0 → 0.25.1
  - uvicorn 0.40.0 → 0.47.0
  - mlflow 3.8.1 → 3.12.0
  - chainlit 2.9.5 → 2.11.1
  - pypdf 6.6.0 → 6.12.0
  - psycopg 3.3.2 → 3.3.4
  - datasets 4.4.2 → 4.8.5
  - ruff 0.15.13 → 0.15.14
  - relax ragas==0.4.2 → >=0.4.2,<0.5 (picks up 0.4.3)
  - re-verify matplotlib + scikit-learn caps (lift if manim/aeon don't block)
  ↓
L-S2: major bumps with audits — each is its own slice
  - L-S2a: openai 1.40.8 → 2.37.0 (Responses API; structured outputs)
  - L-S2b: pandas 2.1.4 → 3.0.3 (deprecated API removals)
  - L-S2c: anthropic 0.32.0 → 0.103.1 + langchain-openai 0.2.2 → 1.2.1 (together since they bind to LangChain 1.x)
  - L-S2d: langfuse 3.11.2 → 4.6.1 (tracker)
  - L-S2e: arize-phoenix 12.27.0 → 15.11.1 (tracker)
  - L-S2f: rich 13.9.4 → 15.0.0 (CLI output)
  - L-S2g: chardet 5.2.0 → 7.4.3 (encoding detection)
  - L-S2h: instructor 1.4.1 → 1.15.1 (D-S5d already started using it; check structured-output features)
  - L-S2i: mkdocstrings 0.24+ → 1.0.4 (docs build)
  ↓
L-S3: pydantic v2.13 new feature adoption (computed_field, model_validator improvements) — light slice after L-S1
  ↓
L-S4: fastapi/typer/instructor new feature adoption (after their L-S2 slices land)
  ↓
L-S5: mkdocs stack feature adoption (after mkdocstrings 1.0 lands)
  ↓
L-S6: frontend — lucide-react + plotly.js-dist-min majors (better folded into Phase 4)
  ↓
Phase 4: Web frontend Claude design overhaul (memory project_phase4_web_frontend_overhaul)
```

**Risk-ranked execution order for L-S2 sub-slices:**

1. **L-S2a (openai 2.x)** — highest impact + many call sites. Do first; baseline regression-gate runs against this.
2. **L-S2b (pandas 3.x)** — wide impact across reports + dataset loaders.
3. **L-S2c (anthropic + langchain-openai)** — together since LangChain 1.x is the contract.
4. **L-S2d (langfuse 4.x)** + **L-S2e (phoenix 15.x)** — tracker layer (MultiTrackerAdapter from A-S3 cushions the change).
5. **L-S2f (rich 15.x)** — CLI output cosmetic; baseline `evalvault --help` snapshot needed before/after.
6. **L-S2g (chardet 7.x)** — narrow scope, dataset CSV encoding only.
7. **L-S2h (instructor 1.15)** — verify new Pydantic schema features map onto D-S5d's wrapper.
8. **L-S2i (mkdocstrings 1.0)** — docs-only.

---

## 5. Feature Highlights Worth Adopting (Pending Update)

Once major bumps land, scan for these features (verify against current release notes):

- **openai 2.x**: Responses API simplifies multi-step LLM calls; structured outputs default; new tool use shape — could simplify `faithfulness_fallback` and `summary_faithfulness_judge`.
- **pydantic 2.13**: improved `computed_field`, `@field_validator` ergonomics — clean up custom validators in `Settings` and entities.
- **typer 0.25**: improved rich help formatting; better completion — better `evalvault --help` UX.
- **fastapi 0.136**: improved dependency injection patterns + async middleware — Web UI backend cleanups.
- **rich 15.0**: new layout primitives, improved table rendering — better CLI report output.
- **mlflow 3.12**: native dataset tracking — could align EvalVault dataset version with MLflow run logging.
- **arize-phoenix 15.x**: improved trace visualization + new schema for evaluation runs — Phoenix adapter alignment.
- **langfuse 4.x**: new score schema + dataset linking — Langfuse adapter alignment.
- **instructor 1.15**: improved Pydantic schema validation + streaming — fold into D-S5d feature-flag path.
- **lucide-react 1.x**: stable icon API + tree-shaken; smaller bundle.
- **plotly.js 3.x**: new chart types + improved React-friendly bundles.

---

## 6. Open Questions for User Before L-S1 Execution

1. **Are manim and matplotlib<3.9 still required?** If manim is unused in actual reports/CI, dropping it (and its pycairo system-dep mess) unlocks matplotlib 3.10 plus simplifies `uv sync --extra dev`.
2. **scikit-learn<1.4 — why?** If unstated reason, re-test with sklearn 1.8 against the analysis modules.
3. **Should L-S2 sub-slices run in parallel (worktree per major bump) or serial?** Worktree-parallel is faster but introduces merge conflict risk if multiple bumps touch the same module (e.g. openai 2.x + langchain-openai 1.x both touch the LLM adapter).
4. **For frontend major bumps (lucide-react, plotly.js)**: fold into Phase 4 redesign (preferred — lets Claude design choose new icons/charts) or do separately first?

---

## Verification

```bash
# Re-run the audit to confirm numbers (refresh as PyPI/npm shifts):
uv pip list | grep -E "^(ragas|pydantic|openai|fastapi|pandas|matplotlib)"
cd frontend && npm outdated --json
```

This document should be deleted or archived after L-S1 + L-S2 sub-slices complete.
