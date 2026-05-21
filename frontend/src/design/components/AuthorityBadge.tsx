/**
 * Phase 4 W-S1 AuthorityBadge — T0-T4 decision authority surfacing.
 *
 * Companion to project_decision_authority_t2 memory + docs/adapter-contract.md §3.5.
 *
 * Anti-pattern this prevents: rendering EvalVault's "passed" regression-gate
 * verdict as if it were a release "promote". A T2 evaluation-pass is NOT a
 * release approval; the badge makes that visually explicit.
 *
 * Used on RunDetails, CompareRuns, Dashboard rows that surface a decision
 * artifact.
 */

export type AuthorityLevel = "T0" | "T1" | "T2" | "T3" | "T4";
export type DecisionScope =
    | "diagnostic"
    | "metric_evidence"
    | "evaluation_gate"
    | "release_gate"
    | "arbitration";

const LEVEL_META: Record<AuthorityLevel, { label: string; tone: string; description: string }> = {
    T0: {
        label: "T0 · diagnostic",
        tone: "border-[hsl(var(--authority-t0))] text-[hsl(var(--authority-t0))] bg-[hsl(var(--authority-t0)/0.08)]",
        description: "Trace / log / prompt — no decision authority.",
    },
    T1: {
        label: "T1 · metric",
        tone: "border-[hsl(var(--authority-t1))] text-[hsl(var(--authority-t1))] bg-[hsl(var(--authority-t1)/0.08)]",
        description: "Metric evidence (score, threshold check) — not a verdict.",
    },
    T2: {
        label: "T2 · eval-gate",
        tone: "border-[hsl(var(--authority-t2))] text-[hsl(var(--authority-t2))] bg-[hsl(var(--authority-t2)/0.08)]",
        description:
            "Run-level evaluation verdict (pass / hold). NOT a release promotion — release decisions are T3 (Reverra-Gate).",
    },
    T3: {
        label: "T3 · release-gate",
        tone: "border-[hsl(var(--authority-t3))] text-[hsl(var(--authority-t3))] bg-[hsl(var(--authority-t3)/0.10)]",
        description: "Release-level promote / hold / rollback. Owned by Reverra-Gate, not EvalVault.",
    },
    T4: {
        label: "T4 · arbitration",
        tone: "border-[hsl(var(--authority-t4))] text-[hsl(var(--authority-t4))] bg-[hsl(var(--authority-t4)/0.10)]",
        description: "Control-plane arbitration across tools. AI Tool Suite owns this.",
    },
};

const SCOPE_LABEL: Record<DecisionScope, string> = {
    diagnostic: "diagnostic",
    metric_evidence: "metric evidence",
    evaluation_gate: "evaluation gate",
    release_gate: "release gate",
    arbitration: "arbitration",
};

export interface AuthorityBadgeProps {
    level: AuthorityLevel;
    /** Optional explicit decision_scope; falls back to a sensible default per level. */
    scope?: DecisionScope;
    /** Optional verdict label (e.g. "eval-pass", "hold"). */
    verdict?: string;
    className?: string;
}

const DEFAULT_SCOPE: Record<AuthorityLevel, DecisionScope> = {
    T0: "diagnostic",
    T1: "metric_evidence",
    T2: "evaluation_gate",
    T3: "release_gate",
    T4: "arbitration",
};

export function AuthorityBadge({
    level,
    scope,
    verdict,
    className = "",
}: AuthorityBadgeProps) {
    const meta = LEVEL_META[level];
    const effectiveScope = scope ?? DEFAULT_SCOPE[level];
    const aria =
        `${meta.label} — ${SCOPE_LABEL[effectiveScope]}` +
        (verdict ? `, verdict ${verdict}` : "");
    return (
        <span
            className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium ${meta.tone} ${className}`}
            title={meta.description}
            aria-label={aria}
        >
            <span className="font-semibold">{level}</span>
            <span aria-hidden className="opacity-60">·</span>
            <span>{SCOPE_LABEL[effectiveScope]}</span>
            {verdict && (
                <>
                    <span aria-hidden className="opacity-60">·</span>
                    <span className="font-semibold">{verdict}</span>
                </>
            )}
        </span>
    );
}
