/**
 * Phase 4 W-S2a — Design System Showcase
 *
 * Lives at `/design-system`. Demonstrates every W-S1 primitive in
 * realistic contexts so:
 *   - Designers / reviewers can verify Claude design language is applied.
 *   - Page authors (W-S2b/c/d onward) can copy patterns directly.
 *   - QA can spot regressions when tokens change.
 *
 * This page is intentionally self-contained — no API calls, no router
 * dependencies beyond the route entry. Safe to mount in any environment
 * (closed-network demo, Storybook stand-in, isolated dev).
 */

import { useState } from "react";
import {
    AlertCircle,
    CheckCircle2,
    Database,
    Inbox,
    Search,
} from "lucide-react";
import {
    AuthorityBadge,
    Button,
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
    ComposedCard,
    EmptyState,
    MetricChip,
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "../design";

function Section({ id, title, description, children }: {
    id: string;
    title: string;
    description: string;
    children: React.ReactNode;
}) {
    return (
        <section id={id} className="mb-12 scroll-mt-6">
            <header className="mb-4 border-b border-border pb-3">
                <h2 className="text-2xl font-semibold tracking-tight text-foreground">
                    {title}
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">{description}</p>
            </header>
            {children}
        </section>
    );
}

function Block({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="rounded-[var(--radius)] border border-border bg-muted/30 p-4">
            <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {label}
            </p>
            <div className="flex flex-wrap items-start gap-3">{children}</div>
        </div>
    );
}

export function DesignSystem() {
    const [loadingDemo, setLoadingDemo] = useState(false);

    return (
        <div className="mx-auto max-w-5xl px-6 py-12">
            <header className="mb-10 border-b border-border pb-6">
                <p className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--primary))]">
                    Phase 4 · W-S2a
                </p>
                <h1 className="mt-1 text-4xl font-semibold tracking-tight text-foreground">
                    EvalVault Design System
                </h1>
                <p className="mt-2 max-w-2xl text-base text-muted-foreground">
                    Claude design language applied to EvalVault. This page is the live reference for
                    the W-S1 component library; page redesigns from W-S2b onward compose on top of
                    these primitives.
                </p>
                <nav className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <a href="#authority" className="hover:text-foreground">Authority</a>
                    <span aria-hidden>·</span>
                    <a href="#button" className="hover:text-foreground">Button</a>
                    <span aria-hidden>·</span>
                    <a href="#card" className="hover:text-foreground">Card</a>
                    <span aria-hidden>·</span>
                    <a href="#metric" className="hover:text-foreground">MetricChip</a>
                    <span aria-hidden>·</span>
                    <a href="#table" className="hover:text-foreground">Table</a>
                    <span aria-hidden>·</span>
                    <a href="#empty" className="hover:text-foreground">EmptyState</a>
                </nav>
            </header>

            <Section
                id="authority"
                title="AuthorityBadge — T0..T4 hierarchy"
                description="Anti-conflation guard: T2 evaluation-pass ≠ T3 release-promote. EvalVault default profile emits T0/T1/T2 only; T3 is Reverra-Gate territory. See docs/adapter-contract.md §3.5."
            >
                <Block label="Authority levels">
                    <AuthorityBadge level="T0" />
                    <AuthorityBadge level="T1" />
                    <AuthorityBadge level="T2" />
                    <AuthorityBadge level="T3" />
                    <AuthorityBadge level="T4" />
                </Block>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <Block label="With verdict (T2 — EvalVault canonical)">
                        <AuthorityBadge level="T2" verdict="eval-pass" />
                        <AuthorityBadge level="T2" verdict="hold" />
                        <AuthorityBadge level="T2" verdict="informational" />
                    </Block>
                    <Block label="Other tiers with verdict">
                        <AuthorityBadge level="T1" verdict="0.86" />
                        <AuthorityBadge level="T3" verdict="promote" />
                        <AuthorityBadge level="T3" verdict="rollback" />
                        <AuthorityBadge level="T4" verdict="arbitrate" />
                    </Block>
                </div>
            </Section>

            <Section
                id="button"
                title="Button"
                description="Restraint with color — primary is the single warm accent. Ghost is the default for most actions."
            >
                <Block label="Variants">
                    <Button variant="primary">Primary action</Button>
                    <Button variant="secondary">Secondary</Button>
                    <Button variant="ghost">Ghost</Button>
                    <Button variant="destructive">Destructive</Button>
                </Block>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <Block label="Sizes">
                        <Button size="sm" variant="primary">Small</Button>
                        <Button size="md" variant="primary">Medium</Button>
                        <Button size="lg" variant="primary">Large</Button>
                    </Block>
                    <Block label="Slots & states">
                        <Button leading={<Search size={14} />} variant="ghost">Search</Button>
                        <Button trailing={<CheckCircle2 size={14} />} variant="primary">Submit</Button>
                        <Button
                            variant="primary"
                            loading={loadingDemo}
                            onClick={() => {
                                setLoadingDemo(true);
                                window.setTimeout(() => setLoadingDemo(false), 1200);
                            }}
                        >
                            Click for loading
                        </Button>
                        <Button variant="ghost" disabled>Disabled</Button>
                    </Block>
                </div>
            </Section>

            <Section
                id="card"
                title="Card"
                description="Generous whitespace, subtle border, no heavy elevation."
            >
                <div className="grid gap-4 sm:grid-cols-2">
                    <Card>
                        <CardHeader>
                            <CardTitle>Standard card</CardTitle>
                            <CardDescription>Header + content + footer.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-muted-foreground">
                                Body text inherits the body font and the foreground color.
                                Card padding is <code className="font-mono text-xs">--space-6</code> by default.
                            </p>
                        </CardContent>
                        <CardFooter>
                            <Button variant="ghost" size="sm">Cancel</Button>
                            <Button variant="primary" size="sm">Save</Button>
                        </CardFooter>
                    </Card>
                    <ComposedCard
                        title="ComposedCard convenience"
                        description="Same shape with less boilerplate."
                        interactive
                        footer={<Button variant="ghost" size="sm">Learn more</Button>}
                    >
                        <p className="text-sm text-muted-foreground">
                            Pass <code className="font-mono text-xs">interactive</code> to opt into
                            hover + focus-ring styles for clickable cards.
                        </p>
                    </ComposedCard>
                </div>
            </Section>

            <Section
                id="metric"
                title="MetricChip"
                description="Single metric value with optional delta vs baseline and authority hint. Delta colored only when materially different."
            >
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <MetricChip
                        label="Faithfulness"
                        value={0.86}
                        format="fixed2"
                        delta={+0.024}
                        authority="T1"
                    />
                    <MetricChip
                        label="Answer relevancy"
                        value={0.78}
                        format="fixed2"
                        delta={-0.031}
                        authority="T1"
                    />
                    <MetricChip
                        label="Context precision"
                        value={0.72}
                        format="fixed2"
                        delta={+0.0001}
                        authority="T1"
                    />
                    <MetricChip
                        label="Regression gate"
                        value="eval-pass"
                        authority="T2"
                    />
                </div>
            </Section>

            <Section
                id="table"
                title="Table"
                description="Accessible table primitives with hover + selected states. Caption renders below by default."
            >
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[28%]">Run ID</TableHead>
                            <TableHead>Dataset</TableHead>
                            <TableHead className="text-right">Faithfulness</TableHead>
                            <TableHead className="text-right">Verdict</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <TableRow>
                            <TableCell className="font-mono text-xs">run_2026_05_21_abc123</TableCell>
                            <TableCell>insurance-qa-dataset</TableCell>
                            <TableCell className="text-right font-mono">0.86</TableCell>
                            <TableCell className="text-right">
                                <AuthorityBadge level="T2" verdict="eval-pass" />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell className="font-mono text-xs">run_2026_05_21_def456</TableCell>
                            <TableCell>multiturn-benchmark</TableCell>
                            <TableCell className="text-right font-mono">0.71</TableCell>
                            <TableCell className="text-right">
                                <AuthorityBadge level="T2" verdict="hold" />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell className="font-mono text-xs">run_2026_05_21_ghi789</TableCell>
                            <TableCell>edge-cases</TableCell>
                            <TableCell className="text-right font-mono">—</TableCell>
                            <TableCell className="text-right">
                                <AuthorityBadge level="T2" verdict="informational" />
                            </TableCell>
                        </TableRow>
                    </TableBody>
                    <TableCaption>
                        Sample runs · authority badges enforce T2 (evaluation-gate) scope.
                    </TableCaption>
                </Table>
            </Section>

            <Section
                id="empty"
                title="EmptyState"
                description="For empty lists, error states, or pre-data interactions. Generous vertical whitespace; short, action-oriented copy."
            >
                <div className="grid gap-4 sm:grid-cols-2">
                    <Card>
                        <EmptyState
                            icon={<Inbox size={20} />}
                            title="실행 결과가 아직 없습니다"
                            description="평가를 한 번 돌리면 여기에 결과 카드가 채워집니다."
                            action={<Button variant="primary" size="sm">새 평가 시작</Button>}
                        />
                    </Card>
                    <Card>
                        <EmptyState
                            icon={<AlertCircle size={20} className="text-[hsl(var(--destructive))]" />}
                            title="데이터를 불러오지 못했습니다"
                            description="네트워크 또는 백엔드 연결을 확인해 주세요."
                            action={<Button variant="ghost" size="sm">다시 시도</Button>}
                        />
                    </Card>
                </div>
                <div className="mt-3">
                    <Card>
                        <EmptyState
                            compact
                            icon={<Database size={16} />}
                            title="No saved filters"
                            description="Compact variant for inline use."
                        />
                    </Card>
                </div>
            </Section>

            <footer className="border-t border-border pt-6 text-xs text-muted-foreground">
                <p>
                    EvalVault Design System · Phase 4 W-S1/W-S2a · See{" "}
                    <code className="font-mono">frontend/src/design/README.md</code> for token reference
                    and W-S0 inventory for the Phase 4 slice plan.
                </p>
            </footer>
        </div>
    );
}
