/**
 * Phase 4 W-S1 — Claude design system barrel.
 *
 * Public surface for the EvalVault Claude-design component library.
 * Consumers (pages in frontend/src/pages/, future Storybook stories) should
 * import from "@/design" (or relative "../design") — NOT from individual
 * component files — so this barrel stays the contract.
 */

// Components
export { Button, type ButtonProps, type ButtonVariant, type ButtonSize } from "./components/Button";
export {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
    CardFooter,
    ComposedCard,
    type ComposedCardProps,
} from "./components/Card";
export {
    Table,
    TableHeader,
    TableBody,
    TableFooter,
    TableRow,
    TableHead,
    TableCell,
    TableCaption,
} from "./components/Table";
export { EmptyState, type EmptyStateProps } from "./components/EmptyState";
export { MetricChip, type MetricChipProps } from "./components/MetricChip";
export {
    AuthorityBadge,
    type AuthorityBadgeProps,
    type AuthorityLevel,
    type DecisionScope,
} from "./components/AuthorityBadge";

// Tokens are consumed via CSS — no JS re-export. Importing this barrel is
// enough to opt into the design language because tokens.css is loaded at
// the index.css level.
