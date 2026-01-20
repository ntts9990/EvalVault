import { useState, type FormEvent } from "react";
import { MessageSquare } from "lucide-react";
import { Layout } from "../components/Layout";
import { Conversation, Message, PromptInput } from "../components/ai-elements";

type ChatEvent =
    | { type: "status"; message: string }
    | { type: "error"; message: string }
    | { type: "delta"; content: string }
    | { type: "final"; content: string };

type ChatMessage = {
    id: string;
    role: "user" | "assistant";
    content: string;
    meta?: { streaming?: boolean };
};

const createMessageId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

const parseChatEvent = (raw: string): ChatEvent | null => {
    if (!raw.trim()) {
        return null;
    }
    try {
        const payload = JSON.parse(raw) as { type?: string; content?: unknown; message?: unknown };
        if (!payload || typeof payload.type !== "string") {
            return null;
        }
        if ((payload.type === "status" || payload.type === "error") && typeof payload.message === "string") {
            return { type: payload.type, message: payload.message } as ChatEvent;
        }
        if ((payload.type === "delta" || payload.type === "final") && typeof payload.content === "string") {
            return { type: payload.type, content: payload.content } as ChatEvent;
        }
        return null;
    } catch {
        return null;
    }
};


export function Chat() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [statusMessage, setStatusMessage] = useState<string | null>(null);
    const [streamController, setStreamController] = useState<AbortController | null>(null);

    const updateAssistant = (assistantId: string, updater: (prev: ChatMessage) => ChatMessage) => {
        setMessages((prev): ChatMessage[] =>
            prev.map((msg): ChatMessage => {
                if (msg.id !== assistantId) {
                    return msg;
                }
                const next = updater(msg);
                return { ...next, content: next.content ?? "" };
            })
        );
    };

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!input.trim() || isLoading) {
            return;
        }

        const userMessage: ChatMessage = {
            id: createMessageId(),
            role: "user",
            content: input.trim(),
        };
        const assistantMessageId = createMessageId();
        const assistantMessage: ChatMessage = {
            id: assistantMessageId,
            role: "assistant",
            content: "",
            meta: { streaming: true },
        };

        setMessages((prev) => [...prev, userMessage, assistantMessage]);
        setInput("");
        setIsLoading(true);
        setStatusMessage(null);

        const controller = new AbortController();
        setStreamController(controller);

        try {
            const response = await fetch("/api/v1/chat/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage.content }),
                signal: controller.signal,
            });

            if (!response.ok) {
                throw new Error(`Chat request failed (${response.status})`);
            }

            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error("Streaming is not supported in this environment.");
            }

            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split("\n");
                buffer = parts.pop() ?? "";

                for (const raw of parts) {
                    const eventPayload = parseChatEvent(raw);
                    if (!eventPayload) {
                        continue;
                    }

                    switch (eventPayload.type) {
                        case "status":
                            setStatusMessage(eventPayload.message);
                            break;
                        case "error":
                            setStatusMessage(eventPayload.message);
                            updateAssistant(assistantMessageId, (msg) => ({
                                ...msg,
                                content: eventPayload.message,
                                meta: { streaming: false },
                            }));
                            break;
                        case "delta":
                            updateAssistant(assistantMessageId, (msg) => ({
                                ...msg,
                                content: `${msg.content}${eventPayload.content}`,
                                meta: { streaming: true },
                            }));
                            break;
                        case "final":
                            updateAssistant(assistantMessageId, (msg) => ({
                                ...msg,
                                content: eventPayload.content,
                                meta: { streaming: false },
                            }));
                            break;
                        default:
                            break;
                    }
                }
            }
        } catch (err) {
            if ((err as Error).name !== "AbortError") {
                setStatusMessage(err instanceof Error ? err.message : "채팅 요청에 실패했습니다.");
            }
        } finally {
            setIsLoading(false);
            setStreamController(null);
        }
    };

    const handleStop = () => {
        streamController?.abort();
        setStreamController(null);
        setIsLoading(false);
    };

    return (
        <Layout>
            <div className="-m-4 lg:-m-8 flex h-[calc(100vh-6rem)] flex-col">
                <div className="flex-1 relative bg-background/50">
                    {messages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4 opacity-70">
                            <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                                <MessageSquare className="w-8 h-8 text-primary" />
                            </div>
                            <h3 className="text-lg font-semibold text-foreground">새 대화를 시작해보세요</h3>
                            <p className="text-sm text-muted-foreground max-w-sm">
                                최신 실행 결과를 요약하거나, 메트릭 변화 원인을 분석하고, 평가 개선 아이디어를
                                요청할 수 있습니다.
                            </p>
                        </div>
                    ) : (
                        <Conversation>
                            {messages.map((msg) => (
                                <Message key={msg.id} role={msg.role} content={msg.content} />
                            ))}
                            {statusMessage && (
                                <div className="p-4 rounded-lg bg-secondary/60 border border-border/60 text-sm text-muted-foreground text-center">
                                    {statusMessage}
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
