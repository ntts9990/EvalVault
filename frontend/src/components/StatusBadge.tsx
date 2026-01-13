export type StatusKey =
    | "completed"
    | "failed"
    | "skipped"
    | "running"
    | "pending"
    | "missing"
    | "incomplete";

const STATUS_META: Record<StatusKey, { label: string; className: string }> = {
    completed: { label: "완료", className: "text-emerald-700 bg-emerald-50 border-emerald-200" },
    failed: { label: "실패", className: "text-rose-700 bg-rose-50 border-rose-200" },
    skipped: { label: "스킵", className: "text-amber-700 bg-amber-50 border-amber-200" },
    running: { label: "실행 중", className: "text-blue-700 bg-blue-50 border-blue-200" },
    pending: { label: "대기", className: "text-slate-600 bg-slate-50 border-slate-200" },
    missing: { label: "없음", className: "text-slate-500 bg-slate-50 border-slate-200" },
    incomplete: { label: "미완료", className: "text-amber-700 bg-amber-50 border-amber-200" },
};

function getStatusMeta(status?: string | null) {
    if (!status) return STATUS_META.pending;
    return STATUS_META[status as StatusKey] ?? STATUS_META.pending;
}

export function StatusBadge({
    status,
    prefix,
    value,
    className = "",
}: {
    status?: string | null;
    prefix?: string;
    value?: string | number;
    className?: string;
}) {
    const meta = getStatusMeta(status);
    return (
        <span
            className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${meta.className} ${className}`}
        >
            {prefix ? `${prefix} · ` : ""}
            {meta.label}
            {value !== undefined && value !== null && (
                <span className="font-semibold">{value}</span>
            )}
        </span>
    );
}
