import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownContentProps = {
    text: string;
    className?: string;
};

export function MarkdownContent({ text, className = "" }: MarkdownContentProps) {
    const classes = [
        "prose",
        "prose-sm",
        "max-w-none",
        "break-words",
        className,
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <div className={classes}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    pre: ({ children }) => (
                        <pre className="overflow-x-auto rounded-lg bg-muted/60 p-3 text-xs leading-relaxed">
                            {children}
                        </pre>
                    ),
                    code: ({ className: codeClass, children, ...props }) => {
                        const isInline = !codeClass;
                        if (isInline) {
                            return (
                                <code
                                    className="rounded bg-muted px-1 py-0.5 text-[0.85em] break-words"
                                    {...props}
                                >
                                    {children}
                                </code>
                            );
                        }
                        return (
                            <code className={`text-xs ${codeClass ?? ""}`.trim()} {...props}>
                                {children}
                            </code>
                        );
                    },
                    table: ({ children }) => (
                        <div className="my-2 overflow-x-auto">
                            <table className="w-full border-collapse text-xs">{children}</table>
                        </div>
                    ),
                    th: ({ children }) => (
                        <th className="border border-border bg-muted/40 px-2 py-1 text-left text-xs font-semibold">
                            {children}
                        </th>
                    ),
                    td: ({ children }) => (
                        <td className="border border-border px-2 py-1 align-top text-xs">
                            {children}
                        </td>
                    ),
                    a: ({ children, ...props }) => (
                        <a
                            className="break-words text-primary underline underline-offset-2"
                            {...props}
                        >
                            {children}
                        </a>
                    ),
                }}
            >
                {text}
            </ReactMarkdown>
        </div>
    );
}
