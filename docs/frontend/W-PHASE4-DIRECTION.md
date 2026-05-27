# Phase 4 — Flagship Visual Direction: "Data-Dense Pro × Warm"

> **Slice**: W-Phase4-Flagship
> **Branch**: `refactor/w-phase4-flagship-dashboard`
> **Status date**: 2026-05-27
> **Scope**: Re-tune the **global base palette/tokens** + fully redesign **one flagship page** (`Dashboard.tsx`). Sign-off proposal before rolling the direction out to the other 16 pages.
> **Supersedes**: the "Warm Console" (editorial/warm-paper) direction documented in the prior version of this file. The warm-console pass was a working draft; this is the ratified direction.

---

## 0. One-line thesis

EvalVault is an **evaluation instrument panel** — a place where engineers form trust in a number. The interface should feel like a precision dashboard: a **warm near-black ground**, **sans-serif instrument headings**, **monospace numerics that read like gauges**, and **charts as the hero element**. Color is rationed to one clay accent plus a high-separation chart ramp. Density is tight. Authority is never faked.

The rejected alternative was "Warm Console" (warm-paper ground, Fraunces serif headings, generous whitespace) — appropriate for editorial/portfolio product, wrong register for an evaluation instrument.

---

## 1. Palette

### 1.1 Dark-first warm ground

`:root` is the **dark state** — the hero look. `.light` is an override for light-mode fallback. All contrast ratios are measured on the dark card surface `#1d1a14`.

| Token | Dark (`:root`) | Light (`.light`) | Role |
|---|---|---|---|
| `--background` | `30 26% 7%` (`#14120e`) | `40 33% 97%` | App ground |
| `--foreground` | `38 22% 88%` | `30 12% 14%` | Primary ink |
| `--card` | `32 18% 10%` (`#1d1a14`) | `42 30% 99%` | Raised surface |
| `--card-foreground` | `38 22% 88%` | `30 12% 14%` | |
| `--secondary` | `32 14% 14%` | `38 22% 94%` | Subtle fills, chips |
| `--muted` | `32 12% 12%` | `38 20% 95%` | Quietest fill |
| `--muted-foreground` | `34 12% 57%` (`#9e9280`, **5.68:1 AA**) | `34 9% 44%` | Meta text |
| `--border` | `32 16% 18%` | `36 16% 86%` | Hairline dividers |

### 1.2 The one accent — "Clay"

| Token | Dark | Light | Role |
|---|---|---|---|
| `--primary` | `16 52% 53%` (`#c96442`) | `16 68% 40%` | Brand, CTAs, active nav indicator, focus ring. **Strictly rationed.** |
| `--primary-foreground` | `30 26% 7%` (dark ink) | `40 33% 97%` | CTA label. Dark ink on clay — cream FAILS WCAG AA on clay background. |
| `--ring` | `16 52% 53%` | `16 68% 40%` | Focus outline = brand |

Clay is used for: the active nav left-border indicator, primary CTA buttons, the single hero-KPI card wash, and focus rings. It is **never** used to paint data series or decorative card fills beyond the single hero tile.

### 1.3 Status semantics

Measured on dark card surface `#1d1a14`:

| Token | Dark | Contrast | Role |
|---|---|---|---|
| `--destructive` | `4 70% 58%` | 4.62 AA | Error / fail |
| `--success` | `148 42% 52%` (`#4cba7a`) | **7.12 AA** | Pass / good |
| `--warning` | `43 68% 51%` (`#d4a832`) | **7.81 AA** | Hold / warn |
| `--info` | `210 72% 60%` (`#4da6e8`) | **6.56 AA** | Informational |

---

## 2. T0–T4 Authority hues — critical anti-conflation constraint

EvalVault's default profile emits **T1 (metric evidence)** and **T2 (evaluation gate)** only. T3–T4 are implemented for completeness but never triggered by this tool.

**Hard rule**: T2 eval-pass color MUST NEVER look like T3 release-promote color. Measured on dark card `#1d1a14`:

| Level | Meaning | Hue family | Dark value | Contrast |
|---|---|---|---|---|
| `--authority-t0` | diagnostic (trace/log) | violet-gray `250°` | `250 10% 47%` (`#7a7488`) | 3.87 AA-large (diagnostic/lowest emphasis only) |
| `--authority-t1` | metric evidence | blue `210°` | `210 72% 60%` (`#4da6e8`) | **6.56 AA** |
| `--authority-t2` | evaluation gate | green `148°` | `148 42% 52%` (`#4cba7a`) | **7.12 AA** |
| `--authority-t3` | release gate (not EvalVault) | gold `43°` | `43 68% 51%` (`#d4a832`) | **7.81 AA** |
| `--authority-t4` | control-plane arbitration | violet `266°` | `266 60% 68%` (`#9b7de0`) | **5.29 AA** |

Separation guarantees (hue wheel distance):
- T2 green `148°` vs T3 gold `43°` → **105° apart** (the conflation risk: resolved).
- T3 gold `43°` vs brand clay `16°` → **27° apart** — BUT clay is `53% L` (lighter, more saturated); T3 gold is `51% L` at 43° hue. The literal `T3` text label is the primary disambiguator; the hue proximity is safe.
- T1 blue `210°` vs all others → fully isolated.
- T0 violet-gray `250°` reads as neutral/muted at 47% L — lowest authority by design.

`--eval-pass` tracks T2 green; `--eval-hold` is T3 gold (hold-for-review, not release-gate — the shared hue is intentional per T2 sub-state semantics); `--eval-info` is T1 blue; `--eval-needs-human` is T4 violet. `AuthorityBadge` semantics are unchanged — only hues were retuned for dark ground.

Pass-rate **dial colors** use `--success`/`--warning`/`--destructive` (status semantics), never the clay brand accent — so a green pass dial never reads as "branded" or as a T2 authority badge.

---

## 3. Typography

Ratified stack — Fraunces serif dropped (editorial register, wrong for instrument panel):

```
--font-display: "IBM Plex Sans", "IBM Plex Sans KR", system-ui, sans-serif;
--font-sans:    "IBM Plex Sans", "IBM Plex Sans KR", system-ui, sans-serif;
--font-mono:    "JetBrains Mono", ui-monospace, monospace;
```

Loaded from Google Fonts (in `index.html`):
```
IBM Plex Sans: 400;500;600;700
IBM Plex Sans KR: 400;500;600;700  (Korean glyph coverage — non-negotiable)
JetBrains Mono: 400;500;600
```

Rules:
- **IBM Plex Sans** for all page headings, section titles, labels, body text. `-0.018em` tracking + OpenType features for display contexts.
- **JetBrains Mono** for every number, metric value, score, run ID, percentage, threshold, timestamp. `tabular-nums` always applied. Numbers are instruments — they must read as such.
- **IBM Plex Sans KR** ensures Korean nav labels (`대시보드`, `평가 스튜디오`, etc.) render at the same quality level.

Type scale (tighter than Warm Console phase — instrument density):

| Token | rem | px | Use |
|---|---|---|---|
| `--text-xs` | 0.6875 | 11 | meta / authority tags / micro labels |
| `--text-sm` | 0.8125 | 13 | secondary body |
| `--text-base` | 0.9375 | 15 | primary body |
| `--text-lg` | 1.0 | 16 | card section titles |
| `--text-xl` | 1.125 | 18 | section headings |
| `--text-2xl` | 1.375 | 22 | KPI values (dashboard stat area) |
| `--text-3xl` | 1.75 | 28 | page title |
| `--text-4xl` | 2.25 | 36 | (reserved) |

---

## 4. Density and spacing rhythm

Instrument-panel density — tighter than the Warm Console phase:

| Concern | Decision | Rationale |
|---|---|---|
| Base radius `--radius` | `0.375rem` (6px) | Tight, precise — instrument panel, not consumer app |
| Radius-sm | `0.25rem` (4px) | Chips, badges, micro elements |
| Card padding | `p-4` (16px) | Was p-5/p-6 in Warm Console; density gain |
| KPI value size | `1.75rem` | Was 2rem; tighter KPI row fits 4-up on md+ |
| Sidebar width | `14rem` open / `3.5rem` collapsed | Was 16rem/5rem |
| Section gap | `gap-3` KPIs, `gap-4` chart grid | Tighter than gap-4/gap-6 |
| Chart height | 300px pass-rate, 268px metric grid | Taller than Warm Console (~240px) — charts are hero |

**Spacing scale** (`--space-1..16`) is standard; pages use it via Tailwind utilities — no change from the base.

---

## 5. Chart ramp — high-separation on dark ground

Charts are the hero element. All series colors verified WCAG AA (4.5:1+) on card surface `#1d1a14`:

```typescript
// frontend/src/config/ui.ts — CHART_METRIC_COLORS
"#f59e0b"  // amber   8.08:1  — primary series (series 0)
"#2dd4bf"  // teal    9.32:1  — secondary series (series 1)
"#a78bfa"  // violet  6.38:1  — tertiary (series 2)
"#fb7185"  // rose    6.45:1  — quaternary (series 3)
"#4da6e8"  // blue    6.56:1  — quinary (series 4)
"#d4a832"  // gold    7.81:1  — senary (series 5)
```

Order maximizes perceptual distance between adjacent series. None conflicts with clay brand (hue `16°`) or T2 eval-pass green (`148°`).

Pass-rate area chart color: `#2dd4bf` (teal) — distinct from both clay brand and T2 authority green. Assigned to `CHART_PASS_RATE_COLOR` in `config/ui.ts`.

Chart grid lines: `hsl(32 12% 20%)` — warm dark separator, visible but recessed.
Chart axis text: `font-mono text-[10px]` — all numeric axes render in JetBrains Mono.
Tooltip background: `hsl(32 18% 12%)` — slightly lighter than card, warm dark.

---

## 6. Motion

Snappy for dense UI — no bounce, no looping animation:

| Token | Value | Role |
|---|---|---|
| `--duration-fast` | 100ms | Micro-interactions (icon swap, badge update) |
| `--duration-base` | 160ms | Most transitions (hover, focus, toggle) |
| `--duration-slow` | 280ms | Sidebar open/close, panel reveals |
| `--ease-standard` | `cubic-bezier(0.2,0,0,1)` | Default easing |
| `--ease-emphasis` | `cubic-bezier(0.3,0,0,1)` | Emphasis (primary button, reveal) |

Staggered reveal on page load (`rise` keyframe — `translateY(10px)` → 0 + fade):
- `.reveal-1` 30ms, `.reveal-2` 90ms, `.reveal-3` 150ms, `.reveal-4` 210ms, `.reveal-5` 270ms
- Applied: header → filter bar → KPI row → charts → run grid
- `@media (prefers-reduced-motion: reduce)` suppresses all keyframe animation.

Hover: `hover:-translate-y-px` on stat cards — 1px lift, no shadow escalation.

---

## 7. Component treatment

### 7.1 StatCard (`frontend/src/design/components/StatCard.tsx`)

KPI tile for the instrument panel. Key decisions:
- `p-4` padding, `gap-2.5` internal gap — density first
- Value in `font-mono text-[1.75rem] tabular-nums` — number as instrument
- Label in `font-mono text-[10px] uppercase tracking-[0.15em]` — kicker style
- Icon: `h-5 w-5` in `bg-primary/15 text-primary` (hero) or `bg-muted text-muted-foreground` (default)
- Hero tone: `border-primary/25 bg-[hsl(var(--primary)/0.08)]` — restrained clay wash (8% opacity)
- Hero bloom: `-right-6 -top-6 h-20 w-20 rounded-full bg-primary/12 blur-xl` — single decorative glow
- Authority badge: `text-[9px] rounded-[var(--radius-sm)]` — lowest-footprint evidence indicator

Props: `label`, `value`, `delta`, `deltaDirection`, `deltaIsPositiveGood`, `authority` (T0–T4), `icon`, `spark` (sparkline slot), `caption`, `tone` (default | hero).

### 7.2 Dial (`frontend/src/design/components/Dial.tsx`)

Radial SVG pass-rate gauge. Key decisions:
- `size` and `thickness` props allow per-context density (run cards use `size={48} thickness={4}`)
- Color flows through CSS vars — no hardcoded hex; `dialColor()` helper in Dashboard returns success/warning/destructive (status semantics only, never clay brand)
- Text renders in JetBrains Mono

### 7.3 Layout sidebar (`frontend/src/components/Layout.tsx`)

- Dark instrument panel: `bg-card border-r border-border`
- Active nav: clay **left-border** `w-0.5 bg-primary` + `bg-secondary/80` container — NOT full clay fill (would overpower dark ground)
- Active icon: `text-primary` (clay) — restrained accent
- Logo: dark ink `hsl(30 26% 7%)` on clay badge + `box-shadow: 0 0 12px hsl(var(--primary)/0.35)` glow
- Decorative blobs on main content: `bg-primary/6` and `bg-primary/4` — single faint clay bloom, no light washes
- Topbar: `font-mono text-xs` breadcrumb strip

---

## 8. What changed globally (and what didn't)

**Changed globally (expected and desired):**
- `frontend/src/index.css` — `:root` is now dark-first; `.light` overrides to warm-neutral
- `frontend/tailwind.config.js` — `font-display` → IBM Plex Sans stack (Fraunces removed); `--radius` tighter
- `frontend/src/design/tokens.css` — T0–T4 authority hues retuned for dark ground
- `frontend/src/config/ui.ts` — chart ramp, `CHART_PASS_RATE_COLOR`, `PASS_RATE_COLOR_BANDS`
- `frontend/index.html` — IBM Plex Sans + IBM Plex Sans KR + JetBrains Mono font imports

Other pages will shift toward dark-warm automatically from the `:root` token change. This is acceptable and desired — the instrument direction is being locked in globally.

**Not changed:**
- No other page's JSX was restyled in this slice
- No API/data-shape changes
- `AuthorityBadge`, `MetricChip`, `Button`, `Card`, `Table`, `EmptyState` keep their public props
- Two new primitives added (`StatCard`, `Dial`); none removed

---

## 9. Rollout notes for the other 16 pages

1. **Chart hex migration**: replace any hardcoded chart hex (`#3B82F6`, `#10B981`, etc.) with `CHART_METRIC_COLORS[n]` from `config/ui.ts`. The ramp is ordered for perceptual distance.
2. **Numeric text**: audit every place a number renders; apply `font-mono tabular-nums`. Most are metric scores, percentages, counts.
3. **Heading hierarchy**: replace any display headings still using serif or Space Grotesk with IBM Plex Sans `font-semibold` (h1/h2) + `font-mono` (kicker labels in ALL CAPS with `tracking-[0.2em]`).
4. **Stat cards**: replace ad-hoc KPI div patterns with `<StatCard>` from the design barrel (`import { StatCard } from "../design"`).
5. **Radius audit**: if any page uses `rounded-lg`/`rounded-xl` independently, verify it resolves to the tight instrument-panel scale via the Tailwind config (not Tailwind defaults).
6. **WCAG per page**: all new text-bearing color pairs must be checked on the dark card surface `#1d1a14`. The verified base tokens are AA+; per-page additions need their own verification.
7. **T0–T4 separation**: anywhere a verdict, status badge, or authority chip is surfaced, apply the `AuthorityBadge` component with the correct tier — never improvise status colors.
8. **Korean text**: IBM Plex Sans KR is already loaded globally. No per-page font change needed for Korean.
