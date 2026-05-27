# Phase 4 — Flagship Visual Direction: "Data-Dense Pro, Neutral-Cool Dark"

> **Slice**: W-Phase4-Flagship
> **Branch**: `refactor/w-phase4-flagship-dashboard`
> **Status date**: 2026-05-27
> **Scope**: Re-tune global base palette/tokens + fully redesign `Dashboard.tsx` as the sign-off proposal before rolling out to 16 other pages.
> **Supersedes**: "Warm Console" (editorial warm-paper) and "Data-Dense Pro × Warm" (warm near-black / clay) directions — both rejected. This is the ratified direction.

---

## 0. One-line thesis

EvalVault is an **evaluation instrument panel**. The interface is a precision control room: **cool neutral dark ground**, **no brown or warm tones**, **indigo accent rationed to one use**, charts as the dominant center element, and runs presented as a **dense sortable table** (not cards). Numbers are instruments. Authority is honest. Density is intentional.

**Rejected alternatives:**
- "Warm Console" (#F4F1EA warm paper, Fraunces serif): editorial register — wrong for a dashboard
- "Data-Dense Pro × Warm" (#14120e warm near-black / clay #c96442): ground reads as brown; maintainer rejected

---

## 1. Palette

### 1.1 Cool-neutral dark ground (`:root` = hero/default)

| Token | Value | Hex approx | Role |
|---|---|---|---|
| `--background` | `228 14% 7%` | `#0e0f13` | App ground — near-black neutral |
| `--foreground` | `220 14% 90%` | `#e2e4ec` | Primary text |
| `--card` | `228 12% 10%` | `#16171c` | Raised surface |
| `--secondary` | `228 10% 13%` | `#1c1d23` | Elevated panel |
| `--muted-foreground` | `220 8% 58%` | `#8e9099` | Meta text — **4.76:1 AA on card** |
| `--border` | `228 10% 16%` | `#222431` | Hairline dividers |

No warm tones. No brown. True cool-gray ramp throughout.

### 1.2 The single accent — electric indigo

| Token | Dark | Light | Role |
|---|---|---|---|
| `--primary` | `239 84% 67%` (`#6366f1`) | `239 68% 52%` | Electric indigo — CTAs, active nav, focus rings. Rationed. |
| `--primary-foreground` | `228 14% 7%` (near-black) | `220 20% 97%` | Text on indigo — dark ink, not white (WCAG AA) |
| `--ring` | `239 84% 67%` | `239 68% 52%` | Focus outline = accent |

Indigo is used for: active nav left-border indicator, primary CTA buttons, focus rings, hero KPI tile wash (8% opacity), sparkline, body bloom. **Never** used for data series or authority badges.

**Hue separation from T0–T4:** indigo sits at 239° — 29° from T1 blue (210°), 91° from T2 green (148°), 196° from T3 gold (43°), 27° from T4 violet (266°). The 27° proximity to T4 is safe: T4 is lower saturation/lightness and always carries the `T4` text label as primary disambiguator.

### 1.3 Status semantics — verified on `#16171c` card surface

| Token | Value | Hex | Contrast | Role |
|---|---|---|---|---|
| `--success` | `148 50% 54%` | `#4ec87e` | **7.45:1 AA** | Pass / good |
| `--warning` | `44 70% 51%` | `#d6ac30` | **7.95:1 AA** | Hold / warn |
| `--info` | `210 80% 64%` | `#5aabf0` | **6.82:1 AA** | Informational |
| `--destructive` | `0 72% 62%` | `#e85e5e` | **4.55:1 AA** | Error / fail |

### 1.4 Light mode — `.light` class on `<html>`

Cool-neutral light fallback. `--primary` deepens to `239 68% 52%` for AA on light card.

---

## 2. T0–T4 Authority hues — anti-conflation (CRITICAL)

EvalVault emits T1 and T2 only by default. T3/T4 implemented for completeness.

**Hard rule**: T2 eval-pass (green) MUST NEVER look like T3 release-promote. Verified on `#16171c`:

| Level | Meaning | Hue | Dark value | Hex | Contrast |
|---|---|---|---|---|---|
| T0 | diagnostic | cool-gray 220° | `220 8% 56%` | `#8e9099` | 4.76 AA |
| T1 | metric evidence | blue 210° | `210 80% 64%` | `#5aabf0` | **6.82 AA** |
| T2 | evaluation gate | green 148° | `148 50% 54%` | `#4ec87e` | **7.45 AA** |
| T3 | release gate | gold 44° | `44 70% 51%` | `#d6ac30` | **7.81 AA** |
| T4 | control-plane | violet 266° | `266 65% 70%` | `#a07be8` | **5.42 AA** |

Hue separation guarantees:
- T2 green 148° vs T3 gold 44° → **104° apart** (the conflation risk — resolved)
- T1 blue 210° vs T2 green 148° → 62° apart
- Accent indigo 239° vs T1 blue 210° → 29° apart — visually distinct (indigo = vivid purple-blue; T1 = muted steel-blue)
- T3 gold 44° vs accent indigo 239° → 195° apart — fully isolated

`--eval-pass` = T2 green; `--eval-hold` = T3 gold (hold-for-review); `--eval-info` = T1 blue; `--eval-needs-human` = T4 violet. Pass-rate **dial colors** use `--success`/`--warning`/`--destructive` — never indigo or any authority hue.

---

## 3. Typography

```
--font-display: "IBM Plex Sans", "IBM Plex Sans KR", system-ui, sans-serif;
--font-sans:    "IBM Plex Sans", "IBM Plex Sans KR", system-ui, sans-serif;
--font-mono:    "JetBrains Mono", ui-monospace, monospace;
```

Rules:
- **IBM Plex Sans** for all headings, labels, body — `-0.018em` tracking on display contexts
- **JetBrains Mono** for every number, score, percentage, run ID, timestamp, metric tag — `tabular-nums` always
- **IBM Plex Sans KR** for Korean nav labels at equal glyph quality
- No serif fonts anywhere

---

## 4. Dashboard layout — structural IA change

The prior layout was a stacked vertical flow (header → filters → KPIs → charts → card grid). The new layout is a **multi-panel command center**:

```
┌─────────────────────────────────────────────────────────────────┐
│ COMMAND BAR — sticky, full-width                                 │
│ [Title] | [Search] [Date] [Projects] [Scope] | [Actions]        │
├──────────────────┬──────────────────────────────────────────────┤
│ LEFT RAIL (176px)│ CHART ZONE — dominant, 2-up side-by-side     │
│                  │                                              │
│ 4 KPI tiles      │  Pass Rate Trend  │  Metric Trends           │
│ (stacked)        │  (220px)          │  (220px)                 │
│                  ├──────────────────────────────────────────────┤
│ Metric selector  │ RUNS TABLE — dense, sortable, 8 columns      │
│ (inline rail)    │  Dataset · Model · PassRate · Cases ·        │
│                  │  Metrics · Verdict · Started · →             │
└──────────────────┴──────────────────────────────────────────────┘
```

**Key structural decisions:**

| Decision | Rationale |
|---|---|
| KPIs in left rail | Persistent visibility while scrolling the runs table |
| Charts as dominant zone | Charts are the hero — maximum horizontal space, always above the fold |
| Runs as table, not card grid | 8+ columns per run; cards wasted space and hid sortable structure |
| Sortable table columns | Dataset, Model, Pass Rate, Cases, Started — direction indicator visible |
| Filters in command bar | All controls in one horizontal strip; no separate filter section |
| Metric selector in rail | Co-located with KPIs — changing charted metrics without scrolling |

---

## 5. Density

| Concern | Value |
|---|---|
| Base radius `--radius` | `0.375rem` (6px) — tight instrument panel |
| Card padding (KPI rail) | `p-3` (12px) |
| Command bar height | ~40px sticky strip |
| Chart height | 220px each side-by-side |
| Table row | `py-2.5` — dense, no card-padding waste |
| Sidebar | `13rem` open / `3rem` collapsed |

---

## 6. Chart ramp — high-separation on cool dark ground

Verified WCAG AA on `#16171c`:

```typescript
"#f59e0b"  // amber   8.14:1  — series 0
"#22d3ee"  // cyan    9.61:1  — series 1
"#a78bfa"  // violet  6.41:1  — series 2
"#fb7185"  // rose    6.48:1  — series 3
"#38bdf8"  // sky     8.22:1  — series 4
"#a3e635"  // lime    9.88:1  — series 5
```

Pass-rate area: `#22d3ee` (cyan, 186°) — distinct from indigo accent (239°) and T2 green (148°).
Chart grid: `hsl(228 10% 18%)`. Axis text: JetBrains Mono 9px, `hsl(220 8% 50%)`.

---

## 7. Motion

| Token | Value |
|---|---|
| `--duration-fast` | 100ms |
| `--duration-base` | 160ms |
| `--duration-slow` | 280ms |
| Reveal stagger | 20/60/100/140/180ms |

`prefers-reduced-motion` suppresses all keyframe animation.

---

## 8. Files changed

| File | Change |
|---|---|
| `frontend/src/index.css` | `:root` = cool neutral dark; no warm tones |
| `frontend/src/design/tokens.css` | Authority hues retuned for cool dark ground |
| `frontend/src/config/ui.ts` | Chart ramp: cyan/lime replace teal/gold |
| `frontend/src/design/components/StatCard.tsx` | `p-3` density, `1.5rem` value for rail fit |
| `frontend/src/components/Layout.tsx` | Narrower sidebar (w-52/w-12), indigo active indicator |
| `frontend/src/pages/Dashboard.tsx` | Full structural rewrite — command bar + rail + chart zone + table |
| `frontend/index.html` | Unchanged — IBM Plex Sans stack correct |
| `frontend/tailwind.config.js` | Unchanged — font stack correct |

**Not changed**: no other page's JSX restyled; no API/data-shape changes; `AuthorityBadge`, `Button`, `Card`, `Dial`, `EmptyState` public props unchanged.

---

## 9. Rollout notes for the other 16 pages

1. **Chart hex migration**: replace hardcoded hex with `CHART_METRIC_COLORS[n]` from `config/ui.ts`
2. **Numeric text**: `font-mono tabular-nums` on every number, score, percentage
3. **Table pattern**: prefer the table pattern over card grids for dense list views
4. **Authority badges**: `AuthorityBadge` with correct tier wherever a verdict is surfaced
5. **No warm tones**: remaining warm/clay values in other pages clear automatically via `:root` token change — audit any page with hardcoded hex
6. **WCAG per page**: verify all new text-bearing pairs on `#16171c` dark card
7. **Korean text**: IBM Plex Sans KR loaded globally — no per-page change
8. **Sidebar offsets**: update any page that hardcoded old sidebar widths to `ml-52`/`ml-12`
