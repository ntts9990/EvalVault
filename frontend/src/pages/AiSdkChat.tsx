import { useEffect, useMemo, useState, type FormEvent } from "react";
import { MessageSquare } from "lucide-react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport, type UIMessage } from "ai";
import { Layout } from "../components/Layout";
import { Conversation, Message, PromptInput } from "../components/ai-elements";
import { fetchRuns, type RunSummary } from "../services/api";

type ChatDataParts = {
    status: { message: string };
};

type ChatUiMessage = UIMessage<unknown, ChatDataParts>;

type ChatCategory = "dataset" | "analysis_method" | "result_interpretation" | "improvement_direction";

const categoryOptions: { value: ChatCategory; label: string; hint: string }[] = [
    {
        value: "dataset",
        label: "데이터셋 질문",
        hint: "데이터셋 구성/필드/전처리 관련",
    },
    {
        value: "analysis_method",
        label: "분석 방식",
        hint: "메트릭/평가/분석 흐름 질문",
    },
    {
        value: "result_interpretation",
        label: "결과 해석",
        hint: "특정 run 결과 요약/해석",
    },
    {
        value: "improvement_direction",
        label: "개선 방향",
        hint: "특정 run 개선/다음 액션",
    },
];

const getMessageText = (message: ChatUiMessage) => {
    return message.parts
        .filter((part) => part.type === "text")
        .map((part) => part.text)
        .join("")
        .trim();
};

export function AiSdkChat() {
    const [input, setInput] = useState("");
    const [statusMessage, setStatusMessage] = useState<string | null>(null);
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [runsError, setRunsError] = useState<string | null>(null);
    const [runId, setRunId] = useState("");
    const [category, setCategory] = useState<ChatCategory>("result_interpretation");

    const trimmedRunId = runId.trim();
    const selectedRun = useMemo(
        () => runs.find((run) => run.run_id === trimmedRunId),
        [runs, trimmedRunId]
    );
    const hasRun = Boolean(selectedRun);
    const hasCases = (selectedRun?.total_test_cases ?? 0) > 0;
    const hasMetrics = (selectedRun?.metrics_evaluated?.length ?? 0) > 0;
    const isUnknownRun = Boolean(trimmedRunId) && !hasRun;

    const categoryAvailability = useMemo(
        () => ({
            dataset: { enabled: true, reason: "" },
            analysis_method: {
                enabled: !trimmedRunId || hasMetrics,
                reason: trimmedRunId && !hasMetrics ? "메트릭 정보 없음" : "",
            },
            result_interpretation: {
                enabled: hasRun && hasCases,
                reason: !trimmedRunId
                    ? "run 선택 필요"
                    : !hasRun
                      ? "run_id 확인 필요"
                      : "테스트 케이스 없음",
            },
            improvement_direction: {
                enabled: hasRun && hasCases && hasMetrics,
                reason: !trimmedRunId
                    ? "run 선택 필요"
                    : !hasRun
                      ? "run_id 확인 필요"
                      : !hasCases
                        ? "테스트 케이스 없음"
                        : "메트릭 정보 없음",
            },
        }),
        [trimmedRunId, hasRun, hasCases, hasMetrics]
    );

    useEffect(() => {
        if (categoryAvailability[category].enabled) {
            return;
        }
        const next = categoryOptions.find((option) => categoryAvailability[option.value].enabled);
        if (next) {
            setCategory(next.value);
        }
    }, [category, categoryAvailability]);

    useEffect(() => {
        let active = true;
        fetchRuns()
            .then((items) => {
                if (!active) return;
                setRuns(items);
            })
            .catch((err) => {
                if (!active) return;
                setRunsError(err instanceof Error ? err.message : "run 목록을 불러오지 못했습니다.");
            });
        return () => {
            active = false;
        };
    }, []);

    const transport = useMemo(() => {
        return new DefaultChatTransport({
            api: "/api/v1/chat/ai-stream",
            body: () => ({
                run_id: trimmedRunId ? trimmedRunId : null,
                category,
            }),
        });
    }, [runId, category]);

    const { messages, sendMessage, status, error, stop } = useChat<ChatUiMessage>({
        transport,
        onData: (dataPart) => {
            if (dataPart.type === "data-status" && typeof dataPart.data.message === "string") {
                setStatusMessage(dataPart.data.message);
            }
        },
        onError: (err) => {
            setStatusMessage(err.message);
        },
    });

    const isLoading = status === "submitted" || status === "streaming";

    const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!input.trim() || isLoading) {
            return;
        }
        if (!categoryAvailability[category].enabled) {
            setStatusMessage("선택한 분류를 사용할 수 없습니다. 다른 분류를 선택해주세요.");
            return;
        }
        const text = input.trim();
        setInput("");
        setStatusMessage(null);
        sendMessage(
            { text },
            {
                body: {
                    run_id: runId.trim() ? runId.trim() : null,
                    category,
                },
            }
        );
    };

    const handleStop = () => {
        stop();
    };

    return (
        <Layout>
            <div className="-m-4 lg:-m-8 flex h-[calc(100vh-6rem)] flex-col">
                <div className="px-4 lg:px-8 pt-4 lg:pt-6">
                    <div className="rounded-2xl border border-border/60 bg-background/70 backdrop-blur-sm p-4 lg:p-5">
                        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                            <div className="text-sm text-muted-foreground">
                                <p className="font-semibold text-foreground">대상 run과 질문 분류를 먼저 선택하세요.</p>
                                <p className="text-xs">선택 정보는 서버에 함께 전송됩니다.</p>
                            </div>
                            {runsError && (
                                <div className="text-xs text-destructive">{runsError}</div>
                            )}
                        </div>
                        <div className="mt-4 grid gap-4 lg:grid-cols-2">
                            <div className="space-y-2">
                                <label className="text-xs font-semibold text-muted-foreground">run_id 선택</label>
                                <div className="flex flex-col gap-2">
                                    <select
                                        value={runId}
                                        onChange={(event) => setRunId(event.target.value)}
                                        className="w-full rounded-lg border border-border/60 bg-background/60 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary/30"
                                    >
                                        <option value="">선택 안 함</option>
                                        {runs.slice(0, 20).map((run) => (
                                            <option key={run.run_id} value={run.run_id}>
                                                {run.run_id} · {run.dataset_name} · {run.model_name}
                                            </option>
                                        ))}
                                    </select>
                                    <input
                                        value={runId}
                                        onChange={(event) => setRunId(event.target.value)}
                                        placeholder="run_id를 직접 입력하세요"
                                        className="w-full rounded-lg border border-border/60 bg-background/60 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary/30"
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-semibold text-muted-foreground">질문 분류</label>
                                    <select
                                        value={category}
                                        onChange={(event) => setCategory(event.target.value as ChatCategory)}
                                        className="w-full rounded-lg border border-border/60 bg-background/60 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary/30"
                                    >
                                        {categoryOptions.map((option) => (
                                            <option
                                                key={option.value}
                                                value={option.value}
                                                disabled={!categoryAvailability[option.value].enabled}
                                            >
                                                {option.label}
                                                {!categoryAvailability[option.value].enabled
                                                    ? ` · ${categoryAvailability[option.value].reason}`
                                                    : ""}
                                            </option>
                                        ))}
                                    </select>
                                    <p className="text-xs text-muted-foreground">
                                        {categoryOptions.find((option) => option.value === category)?.hint}
                                    </p>
                                    {isUnknownRun && (
                                        <p className="text-xs text-destructive">
                                            선택한 run_id가 목록에 없습니다. run 의존 분류는 비활성화됩니다.
                                        </p>
                                    )}
                            </div>
                        </div>
                    </div>
                </div>
                <div className="flex-1 relative bg-background/50">
                    {messages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4 opacity-70">
                            <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                                <MessageSquare className="w-8 h-8 text-primary" />
                            </div>
                            <h3 className="text-lg font-semibold text-foreground">AI SDK 채팅을 시작해보세요</h3>
                            <p className="text-sm text-muted-foreground max-w-sm">
                                AI SDK 스트리밍 프로토콜로 동작하는 챗봇입니다. 분석 결과 해석과 개선 아이디어를
                                바로 질문해볼 수 있습니다.
                            </p>
                        </div>
                    ) : (
                        <Conversation>
                            {messages.map((msg) => {
                                const content = getMessageText(msg);
                                if (!content) {
                                    return null;
                                }
                                const role = msg.role === "user" ? "user" : "assistant";
                                return <Message key={msg.id} role={role} content={content} />;
                            })}
                            {(statusMessage || error) && (
                                <div className="p-4 rounded-lg bg-secondary/60 border border-border/60 text-sm text-muted-foreground text-center">
                                    {statusMessage ?? error?.message}
                                </div>
                            )}
                        </Conversation>
                    )}
                </div>
                <PromptInput
                    input={input}
                    handleInputChange={(event) => setInput(event.target.value)}
                    handleSubmit={handleSubmit}
                    isLoading={isLoading}
                    stop={handleStop}
                />
            </div>
        </Layout>
    );
}
