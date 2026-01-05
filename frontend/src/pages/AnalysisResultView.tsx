import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { Layout } from "../components/Layout";
import { fetchAnalysisResult, type SavedAnalysisResult } from "../services/api";
import { formatDateTime, formatDurationMs } from "../utils/format";
import { Activity, AlertCircle, ArrowLeft, Download, Link2 } from "lucide-react";

const STATUS_META: Record<string, { label: string; color: string }> = {
    completed: { label: "완료", color: "text-emerald-600" },
    failed: { label: "실패", color: "text-rose-600" },
    skipped: { label: "스킵", color: "text-amber-600" },
    running: { label: "실행 중", color: "text-blue-600" },
    pending: { label: "대기", color: "text-muted-foreground" },
};

function downloadText(filename: string, content: string, type: string) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
}

export function AnalysisResultView() {
    const { id } = useParams();
    const [result, setResult] = useState<SavedAnalysisResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showRaw, setShowRaw] = useState(false);
    const [copyStatus, setCopyStatus] = useState<"idle" | "success" | "error">("idle");

    useEffect(() => {
        async function loadResult() {
            if (!id) {
                setError("Invalid result id");
                setLoading(false);
                return;
            }
            try {
                const data = await fetchAnalysisResult(id);
                setResult(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load result");
            } finally {
                setLoading(false);
            }
        }
        loadResult();
    }, [id]);

    const reportText = useMemo(() => {
        if (!result?.final_output) return null;
        const entries = Object.values(result.final_output);
        for (const entry of entries) {
            if (entry && typeof entry === "object" && "report" in entry) {
                const report = (entry as any).report;
                if (typeof report === "string") return report;
            }
        }
        return null;
    }, [result]);

    const rawOutput = useMemo(() => {
        if (!result?.final_output) return null;
        try {
            return JSON.stringify(result.final_output, null, 2);
        } catch {
            return null;
        }
    }, [result]);

    const handleDownloadJson = () => {
        if (!result) return;
        const payload = JSON.stringify(result, null, 2);
        downloadText(`analysis-${result.result_id}.json`, payload, "application/json");
    };

    const handleDownloadReport = () => {
        if (!reportText || !result) return;
        downloadText(`analysis-${result.result_id}.md`, reportText, "text/markdown");
    };

    const handleCopyLink = async () => {
        if (typeof window === "undefined") return;
        const url = window.location.href;
        try {
            if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(url);
            } else {
                const textarea = document.createElement("textarea");
                textarea.value = url;
                textarea.style.position = "fixed";
                textarea.style.opacity = "0";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                document.execCommand("copy");
                document.body.removeChild(textarea);
            }
            setCopyStatus("success");
        } catch (err) {
            setCopyStatus("error");
        }
        setTimeout(() => setCopyStatus("idle"), 1500);
    };

    return (
        <Layout>
            <div className="max-w-5xl mx-auto pb-20">
                <div className="mb-8 flex items-center gap-3">
                    <Link
                        to="/analysis"
                        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
                    >
                        <ArrowLeft className="w-4 h-4" /> 분석 실험실로 돌아가기
                    </Link>
                </div>

                {loading && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Activity className="w-4 h-4 animate-spin" /> 로딩 중...
                    </div>
                )}

                {error && (
                    <div className="p-4 border border-destructive/30 bg-destructive/10 rounded-xl text-destructive flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        <span>{error}</span>
                    </div>
                )}

                {!loading && result && (
                    <div className="space-y-6">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                                <h1 className="text-3xl font-bold tracking-tight">{result.label}</h1>
                                <p className="text-sm text-muted-foreground mt-1">
                                    저장된 분석 결과를 확인합니다.
                                </p>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                                <button
                                    type="button"
                                    onClick={() => setShowRaw(prev => !prev)}
                                    className="text-xs text-muted-foreground hover:text-foreground"
                                >
                                    {showRaw ? "리포트 보기" : "RAW JSON"}
                                </button>
                                <button
                                    type="button"
                                    onClick={handleCopyLink}
                                    className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40"
                                >
                                    <Link2 className="w-3 h-3" /> 링크 복사
                                </button>
                                <button
                                    type="button"
                                    onClick={handleDownloadJson}
                                    className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40"
                                >
                                    <Download className="w-3 h-3" /> JSON 다운로드
                                </button>
                                <button
                                    type="button"
                                    onClick={handleDownloadReport}
                                    disabled={!reportText}
                                    className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-border bg-background hover:border-primary/40 disabled:opacity-50"
                                >
                                    <Download className="w-3 h-3" /> 리포트 다운로드
                                </button>
                                {copyStatus === "success" && (
                                    <span className="text-xs text-emerald-600">링크 복사됨</span>
                                )}
                                {copyStatus === "error" && (
                                    <span className="text-xs text-rose-600">복사 실패</span>
                                )}
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="border border-border rounded-lg p-3">
                                <p className="text-xs text-muted-foreground">Intent</p>
                                <p className="text-sm font-semibold mt-1">{result.intent}</p>
                            </div>
                            <div className="border border-border rounded-lg p-3">
                                <p className="text-xs text-muted-foreground">Duration</p>
                                <p className="text-sm font-semibold mt-1">
                                    {formatDurationMs(result.duration_ms)}
                                </p>
                            </div>
                            <div className="border border-border rounded-lg p-3">
                                <p className="text-xs text-muted-foreground">Saved At</p>
                                <p className="text-sm font-semibold mt-1">
                                    {formatDateTime(result.created_at)}
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="border border-border rounded-lg p-3">
                                <p className="text-xs text-muted-foreground">Query</p>
                                <p className="text-sm font-medium mt-1">
                                    {result.query || "-"}
                                </p>
                            </div>
                            <div className="border border-border rounded-lg p-3">
                                <p className="text-xs text-muted-foreground">Run ID</p>
                                <p className="text-sm font-medium mt-1">
                                    {result.run_id || "샘플 데이터"}
                                </p>
                            </div>
                        </div>

                        {result.node_results && (
                            <div>
                                <h2 className="text-sm font-semibold mb-3">실행 단계</h2>
                                <div className="space-y-2">
                                    {Object.entries(result.node_results).map(([nodeId, node]) => {
                                        const status = (node as any)?.status || "pending";
                                        const meta = STATUS_META[status] || STATUS_META.pending;
                                        return (
                                            <div
                                                key={nodeId}
                                                className="flex items-center justify-between border border-border rounded-lg px-3 py-2"
                                            >
                                                <div>
                                                    <p className="text-sm font-medium">{nodeId}</p>
                                                    {(node as any)?.error && (
                                                        <p className="text-xs text-rose-600">
                                                            {(node as any).error}
                                                        </p>
                                                    )}
                                                </div>
                                                <div className={`text-xs font-semibold ${meta.color}`}>
                                                    {meta.label}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        <div>
                            <h2 className="text-sm font-semibold mb-3">결과 출력</h2>
                            {showRaw ? (
                                <pre className="bg-background border border-border rounded-lg p-4 text-xs overflow-auto max-h-[60vh]">
                                    {rawOutput || "{}"}
                                </pre>
                            ) : reportText ? (
                                <div className="bg-background border border-border rounded-lg p-6 text-sm max-h-[60vh] overflow-auto">
                                    <div className="prose prose-sm max-w-none">
                                        <ReactMarkdown>{reportText}</ReactMarkdown>
                                    </div>
                                </div>
                            ) : (
                                <pre className="bg-background border border-border rounded-lg p-4 text-xs overflow-auto max-h-[60vh]">
                                    {rawOutput || "{}"}
                                </pre>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    );
}
