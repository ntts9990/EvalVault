# EvalVault Design System (Phase 4 W-S1)

> Claude design language applied to EvalVault's React frontend. Deep application — typographic hierarchy, color restraint, generous whitespace, clear primary action, minimal visual chrome.

## Files

| Path | Purpose |
|---|---|
| `tokens.css` | CSS variables for color / spacing / radius / motion / typography. Light + dark. Imported by `src/index.css`. |
| `components/Button.tsx` | Primary / secondary / ghost / destructive variants, three sizes, optional leading/trailing slots + loading state. |
| `components/Card.tsx` | `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`, plus `ComposedCard` convenience. |
| `components/Table.tsx` | `Table` + `TableHeader/Body/Footer/Row/Head/Cell/Caption` accessible primitives. |
| `components/EmptyState.tsx` | Empty-list / error / "no data" surface with icon + title + description + optional CTA. |
| `components/MetricChip.tsx` | Single metric value with optional delta + authority hint. |
| `components/AuthorityBadge.tsx` | **T0–T4** decision authority indicator. Phase 4 W-S7 will use this on every decision-bearing surface. |
| `index.ts` | Barrel — consumers import from here only. |

## Usage

```tsx
import {
    Button,
    Card,
    CardHeader,
    CardTitle,
    CardContent,
    EmptyState,
    MetricChip,
    AuthorityBadge,
} from "@/design"; // or "../design"

<MetricChip label="faithfulness" value={0.86} delta={+0.02} format="fixed2" authority="T1" />

<AuthorityBadge level="T2" verdict="eval-pass" />
// NOT: <AuthorityBadge level="T3" ... /> from EvalVault default profile.
// T3 is Reverra-Gate territory.
```

## T0–T4 Authority Discipline (anti-pattern guard)

`AuthorityBadge` exists because the UI must not falsely conflate:

- EvalVault's `regression_gate_report.status="passed"` → **T2 evaluation-pass** (✅)
- A release-level **T3 "promote"** (❌ Reverra-Gate territory)

EvalVault's default profile emits T1 or T2 only. The badge surfaces this honestly so a reviewer never reads "passed" and assumes the change has been approved for production. Companion docs: `docs/adapter-contract.md §3.5`, memory `project_decision_authority_t2`.

## Tokens

```css
--background, --foreground, --card, --popover, --muted, --accent, --border, --input, --ring
--primary, --secondary
--destructive, --success, --warning, --info
--authority-t0..t4
--eval-pass, --eval-hold, --eval-info, --eval-needs-human
--radius (default 0.5rem), --radius-sm, --radius-lg, --radius-xl, --radius-full
--space-1..16
--duration-fast/base/slow, --ease-standard/emphasis
--font-display, --font-body, --font-mono
```

All HSL via CSS variables. Dark mode flips on `.dark` class on `<html>`.

## Direction (not yet implemented in W-S1)

- **Storybook / ladle**: deferred to a separate W-S1b slice or W-S2. Components are documented inline via TSDoc.
- **lucide-react 0.562 → 1.16** bump: deferred to W-S6 (e2e refresh + final icon audit). Attempted during W-S1 but local `npm run build` could not verify icon-name compatibility in this environment (50+ icon import sites + npm cache permission issue). Safer to fold the bump into the slice that already revisits every icon usage.
- **Migration of existing pages**: W-S2 onward. The legacy components in `src/components/` continue to work alongside the new ones — design system rollout is incremental, not big-bang.

## Why these specific components first?

W-S0 inventory identified six visual atoms used across nearly every page: button, card, table, empty state, metric chip, decision badge. Building them first means W-S2 page redesigns can compose on top instead of inventing each time.
