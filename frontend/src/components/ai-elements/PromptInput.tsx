import { Send, Sparkles, StopCircle } from "lucide-react";

interface PromptInputProps {
    input: string;
    handleInputChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
    handleSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
    isLoading: boolean;
    stop: () => void;
}

export function PromptInput({
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    stop,
}: PromptInputProps) {
    return (
        <div className="sticky bottom-0 bg-background/80 backdrop-blur-xl border-t border-border/40 p-4 md:p-6">
            <div className="max-w-3xl mx-auto">
                <form onSubmit={handleSubmit} className="relative group">
                    <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent rounded-xl -z-10 opacity-0 group-focus-within:opacity-100 transition-opacity" />
                    <textarea
                        value={input}
                        onChange={handleInputChange}
                        placeholder="EvalVault에 대해 질문해보세요..."
                        className="w-full bg-secondary/30 hover:bg-secondary/50 focus:bg-background border border-border/50 focus:border-primary/50 rounded-xl px-4 py-4 pr-24 min-h-[60px] max-h-[200px] resize-none focus:outline-none focus:ring-1 focus:ring-primary/20 placeholder:text-muted-foreground/50 font-medium transition-all shadow-sm"
                        onKeyDown={(event) => {
                            if (event.key === "Enter" && !event.shiftKey) {
                                event.preventDefault();
                                handleSubmit(event as unknown as React.FormEvent<HTMLFormElement>);
                            }
                        }}
                    />
                    <div className="absolute right-2 bottom-2.5 flex items-center gap-2">
                        {isLoading ? (
                            <button
                                type="button"
                                onClick={stop}
                                className="p-2 rounded-lg bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors"
                            >
                                <StopCircle className="w-5 h-5" />
                            </button>
                        ) : (
                            <button
                                type="submit"
                                disabled={!input.trim()}
                                className="p-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md shadow-primary/20"
                            >
                                <Send className="w-5 h-5" />
                            </button>
                        )}
                    </div>
                </form>
                <div className="text-center mt-2">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-medium">
                        <Sparkles className="w-3 h-3 inline-block mr-1 text-primary" />
                        EvalVault AI Chat
                    </p>
                </div>
            </div>
        </div>
    );
}
