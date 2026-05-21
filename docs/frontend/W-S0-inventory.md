# Phase 4 W-S0 — Frontend Discovery & Inventory

> **Slice**: W-S0 (Phase 4, discovery)
> **Branch**: `refactor/w-s0-frontend-discovery` (base c89085f)
> **Status date**: 2026-05-21
> **Goal**: Inventory the 17 React pages, identify pain points, define Claude design tokens, and produce the slice plan for W-S1+ (design system → page redesigns → e2e refresh).
> **Companion memory**: `project_phase4_web_frontend_overhaul.md` (user directive: deeply apply Claude design language, not surface mimicry).
> **Constraint**: This slice is **research only — no UI code changes**. W-S1 will start the actual design-system module.

---

## 1. Current Page Inventory (17 pages)

Source: `frontend/src/pages/*.tsx`.

### 1.1 Categorization

| Category | Pages | Count |
|---|---|---|
| **Entry surfaces** (daily-driver) | `Dashboard`, `EvaluationStudio` | 2 |
| **Analysis cluster** | `AnalysisLab`, `AnalysisResultView`, `AnalysisCompareView`, `ComprehensiveAnalysis` | 4 |
| **Run inspection** | `CompareRuns`, `RunDetails` | 2 |
| **LLM interaction** | `Chat`, `AiSdkChat`, `JudgeCalibration` | 3 |
| **Knowledge surfaces** | `DomainMemory`, `KnowledgeBase` | 2 |
| **Visualization** | `Visualization`, `VisualizationHome` | 2 |
| **Domain-specific report** | `CustomerReport` | 1 |
| **Settings** | `Settings` | 1 |

**Hypothesis** (to validate in W-S1 redesign): the analysis cluster (4) and visualization cluster (2) likely consolidate into 2–3 pages each. Chat + AiSdkChat duplication suggests one survives. Net target after Phase 4: **~10 pages**, not 17.

### 1.2 Per-page first-pass note

| Page | Apparent purpose | Composition signals (imports + first-30 lines) | W-S0 hypothesis for Phase 4 |
|---|---|---|---|
| `Dashboard` | Run history overview + KPI cards | recharts (Area, Line), lucide icons, `fetchRuns` API | Keep, redesign as the canonical entry surface |
| `EvaluationStudio` | Launch + monitor a run | (read in W-S1) | Keep, primary "do work" surface |
| `AnalysisLab` | Analysis pipeline runs | (read in W-S1) | Keep, secondary analysis surface |
| `AnalysisResultView` | Single analysis result | (read in W-S1) | **Merge** into RunDetails or under AnalysisLab tab |
| `AnalysisCompareView` | Compare two analysis results | (read in W-S1) | **Merge** into CompareRuns |
| `ComprehensiveAnalysis` | Aggregate analysis | (read in W-S1) | **Merge** into AnalysisLab as "summary" mode |
| `CompareRuns` | Compare two evaluation runs | (read in W-S1) | Keep + absorb AnalysisCompareView |
| `RunDetails` | Single run details | (read in W-S1) | Keep + absorb AnalysisResultView |
| `Chat` | Generic chat UI | (read in W-S1) | **Remove or merge** with AiSdkChat (likely duplicate) |
| `AiSdkChat` | Vercel AI SDK chat | uses `@ai-sdk/react`, `ai` | Keep, prime LLM-side surface |
| `JudgeCalibration` | Tune judge LLM scoring | (read in W-S1) | Keep, niche but important |
| `DomainMemory` | Per-domain memory inspect | (read in W-S1) | **Audit usage**: keep or remove |
| `KnowledgeBase` | Knowledge graph inspect | (read in W-S1) | Keep, link to KG generator |
| `Visualization` | Chart explorer | (read in W-S1) | **Merge** with VisualizationHome |
| `VisualizationHome` | Viz landing | (read in W-S1) | **Merge** into Dashboard or unified Viz |
| `CustomerReport` | Domain-specific report | (read in W-S1) | **Audit usage**: keep or rename to be generic |
| `Settings` | App settings | (read in W-S1) | Keep, simplify |

→ **Estimated Phase 4 page count after redesign**: 10 pages (Dashboard, EvaluationStudio, AnalysisLab, CompareRuns, RunDetails, AiSdkChat, JudgeCalibration, KnowledgeBase, Visualization, Settings) with possible CustomerReport conditional on usage.

---

## 2. Current Styling Foundation (`frontend/tailwind.config.js`)

| Aspect | Current state | Phase 4 implication |
|---|---|---|
| Approach | shadcn/ui-style CSS variables (`hsl(var(--primary))` etc.) | ✅ Good base — Claude design can re-tune the CSS variables without rewriting components |
| Fonts | `IBM Plex Sans KR` (sans), `Space Grotesk` (display), `JetBrains Mono` (mono) | Decent Korean + display + mono trio; Claude typically uses Inter / Söhne / Berkeley Mono — propose keeping IBM Plex KR for Korean coverage, swapping Space Grotesk for Inter |
| Color tokens | primary, secondary, destructive, muted, accent, popover, card (HSL-via-CSS-vars) | ✅ Already well-structured. Claude design palette → re-tune variables in a new theme file |
| Radius | `--radius` driven (lg/md/sm) | Match Claude's relatively conservative radius (md: 6–8px) |
| Animations | accordion-down/up only | Add motion tokens (duration-* / ease-*) in W-S1 |
| Plugins | `@tailwindcss/typography` | Useful for markdown surfaces (AiSdkChat, RunDetails). Keep. |
| Design dir | `frontend/src/design/`, `frontend/src/styles/`, `frontend/src/theme/` all absent | W-S1 creates `frontend/src/design/` with tokens + component library |

---

## 3. Identified Pain Points (Hypotheses for W-S1)

> These are **hypotheses to verify** during W-S1 — user said "심각" (serious) but did not enumerate. The Phase 4 brief is committed to discovery before redesign.

### 3.1 Information architecture
1. **17 pages is too many** for the actual jobs-to-be-done. Several pairs duplicate (Chat/AiSdkChat, Visualization/VisualizationHome, AnalysisCompareView/CompareRuns).
2. **No clear "home"** — Dashboard vs EvaluationStudio vs VisualizationHome all compete for the primary entry surface.
3. **Settings hidden** — important controls (profile, tracker provider, db backend) may be buried.

### 3.2 Visual quality
1. **Generic shadcn aesthetic** — the CSS-variable foundation is solid but the actual hue choices (default indigo from mkdocs.yml) are conservative and don't read as a serious evaluation tool.
2. **Chart library dual usage** — both Plotly (heavy, full-featured) and Recharts (light) coexist. Claude design tends toward focused, single-purpose visualizations. Likely Plotly stays for advanced and Recharts gets simplified.
3. **Inconsistent density** — some pages dense with multi-column tables, others overly airy.

### 3.3 Interaction design
1. **No keyboard-first patterns** — needs cmd-K palette, navigation shortcuts (Claude design heavily emphasizes keyboard).
2. **Modal vs inline patterns** — unclear which actions modal vs route.
3. **No loading-state convention** — different pages handle async differently.

### 3.4 Performance
1. **Plotly bundle size** — `plotly.js-dist-min` is heavy (~3MB). For pages that don't need Plotly's advanced features, recharts or visx suffices.
2. **No code-splitting verification** — Vite handles automatically but per-route splits should be verified.
3. **No image / font preload strategy** documented.

### 3.5 Accessibility
1. **No a11y audit on file** — need axe-core run as W-S0 follow-up.
2. **Color contrast** uncertain in the current shadcn theme — need WCAG AA verification.
3. **Korean / English language toggling** — many pages mix; need explicit `lang` attribute strategy.

---

## 4. Proposed Claude Design Tokens (W-S1 starting point)

These are **proposals to apply in W-S1** — not yet implemented. Sourced from public Claude.ai / Anthropic UI patterns (typographic hierarchy, color restraint, generous whitespace).

### 4.1 Color (CSS variables, OKLCH or HSL)

```css
:root {
  /* Neutral spine — most surface uses these */
  --background: 250 33% 99%;            /* near-white with warm tint */
  --foreground: 250 18% 10%;            /* near-black */
  --muted: 250 14% 96%;                 /* card surface */
  --muted-foreground: 250 12% 40%;
  --border: 250 14% 88%;

  /* Single accent (Claude uses a warm orange / clay) */
  --primary: 25 75% 47%;                /* terracotta-ish */
  --primary-foreground: 0 0% 100%;

  /* Status semantics — rare, intentional */
  --success: 145 55% 38%;
  --warning: 38 90% 50%;
  --destructive: 0 70% 48%;

  /* T2 evaluation-gate state (per project-decision-authority-t2 memory) */
  --eval-pass: 145 45% 42%;
  --eval-hold: 38 80% 50%;
  --eval-info: 250 12% 40%;
}

.dark {
  --background: 250 25% 8%;
  --foreground: 250 14% 96%;
  /* ... */
}
```

Rationale: restraint with color, one strong accent, status colors used sparingly. This is the opposite of dashboard-style "rainbow KPI cards".

### 4.2 Typography scale

```
--font-display: "Inter", "IBM Plex Sans KR", system-ui, sans-serif;
--font-body:    "Inter", "IBM Plex Sans KR", system-ui, sans-serif;
--font-mono:    "JetBrains Mono", ui-monospace, monospace;

--text-xs:   0.75rem;   /* meta */
--text-sm:   0.875rem;
--text-base: 1rem;
--text-lg:   1.125rem;
--text-xl:   1.25rem;
--text-2xl:  1.5rem;    /* section heading */
--text-3xl:  1.875rem;
--text-4xl:  2.25rem;   /* page title */
```

Maintain IBM Plex Sans KR as fallback for Korean glyphs. Inter as primary (Claude design uses Söhne which isn't publicly licensable; Inter is the closest open alternative).

### 4.3 Spacing & radius

```
--space-1: 0.25rem;   /* internal padding */
--space-2: 0.5rem;
--space-3: 0.75rem;
--space-4: 1rem;
--space-6: 1.5rem;    /* card padding */
--space-8: 2rem;      /* section gap */
--space-12: 3rem;
--space-16: 4rem;

--radius: 0.5rem;     /* md (current default) */
--radius-sm: 0.375rem;
--radius-lg: 0.75rem;
```

Generous whitespace (--space-6 / --space-8 default for cards / sections).

### 4.4 Motion

```
--duration-fast: 120ms;
--duration-base: 200ms;
--duration-slow: 320ms;
--ease-standard: cubic-bezier(0.2, 0, 0, 1);
--ease-emphasis: cubic-bezier(0.3, 0, 0, 1);
```

Subtle, fast, no bouncy easing. Claude design avoids dramatic motion.

---

## 5. Open Questions (verify before W-S1)

1. **CustomerReport — is it used?** If yes, generic-ize the name. If no, remove.
2. **DomainMemory — usage data?** If <5% of sessions touch it, deprecate.
3. **Plotly vs Recharts — which charts need Plotly's advanced features (3D, complex layouts)?** If none, drop Plotly entirely (saves ~3 MB bundle).
4. **`lucide-react` major bump (0.562 → 1.16) — should be done as part of W-S1 / W-S2** rather than separate slice (per user decision to fold frontend majors into Phase 4).
5. **`plotly.js-dist-min` major bump (2.35 → 3.5) — same** — conditional on whether Plotly survives the audit.
6. **Branding** — is there a brand guideline document for EvalVault, or are we creating it in W-S1?
7. **Dark mode default** — currently `darkMode: ["class"]` (manual toggle). Should it follow system preference?

---

## 6. W-S0 Deliverables (this slice)

- ✅ This document (`docs/frontend/W-S0-inventory.md`).
- 📅 Next slice (W-S1) deliverable: `frontend/src/design/` directory with tokens + component library (Button, Card, Table, EmptyState, StatusBadge, MetricChip).

## 7. Next Slice Sequence (Phase 4)

```
W-S0 ✓ (this doc — discovery)
  ↓
W-S1: design system foundation
  - frontend/src/design/tokens.css (the variables proposed above)
  - frontend/src/design/components/ (Button, Card, Table, EmptyState, StatusBadge, MetricChip, ...)
  - Storybook OR ladle for the component library
  - lucide-react bump 0.562 → 1.16 (icon API stabilization, smaller bundle)
  ↓
W-S2: redesign primary surfaces (Dashboard, EvaluationStudio, AnalysisLab) on top of W-S1
  ↓
W-S3: analysis cluster consolidation (merge 4 pages → 2)
  ↓
W-S4: LLM interaction redesign (AiSdkChat, JudgeCalibration) — respect prompt-discipline memory
  ↓
W-S5: secondary page cleanup (Settings, CustomerReport, DomainMemory, KnowledgeBase, Visualization)
  - plotly.js bump 2.35 → 3.5 OR removal decision
  ↓
W-S6: Playwright e2e refresh against new interactions
  ↓
W-S7: T2 authority surfacing — evaluation verdicts show `authority_level: "T2"` honestly (no false "promoted" labels)
```

**Estimated total**: 4–6 weeks for the entire Phase 4 if executed serially. Parallel execution (designer + executor agents) could compress.
