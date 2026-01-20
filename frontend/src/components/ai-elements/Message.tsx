import { Bot, User } from "lucide-react";
import { Response } from "./Response";

interface MessageProps {
    role: "user" | "assistant" | "system" | "data" | "function";
    content: string;
}

export function Message({ role, content }: MessageProps) {
    if (role === "system" || role === "data" || role === "function") {
        return null;
    }

    const isUser = role === "user";

    return (
        <div
            className={`flex gap-4 ${
                isUser ? "flex-row-reverse" : "flex-row"
            } animate-in fade-in slide-in-from-bottom-2`}
        >
            <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${
                    isUser
                        ? "bg-primary/10 border-primary/20 text-primary"
                        : "bg-secondary/50 border-secondary text-secondary-foreground"
                }`}
            >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            <div className={`flex flex-col max-w-[80%] ${isUser ? "items-end" : "items-start"}`}>
                <div
                    className={`rounded-2xl px-5 py-3.5 shadow-sm ${
                        isUser
                            ? "bg-primary text-primary-foreground rounded-tr-sm"
                            : "bg-card border border-border/60 rounded-tl-sm"
                    }`}
                >
                    {isUser ? (
                        <p className="whitespace-pre-wrap leading-relaxed">{content}</p>
                    ) : (
                        <Response content={content} />
                    )}
                </div>
            </div>
        </div>
    );
}
