import { useEffect, useRef, type ReactNode } from "react";

interface ConversationProps {
    children: ReactNode;
    className?: string;
}

export function Conversation({ children, className }: ConversationProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [children]);

    return (
        <div className={`flex-1 overflow-y-auto p-4 md:p-6 space-y-8 scroll-smooth ${className ?? ""}`}>
            <div className="max-w-3xl mx-auto flex flex-col gap-6">
                {children}
                <div ref={bottomRef} className="h-4" />
            </div>
        </div>
    );
}
