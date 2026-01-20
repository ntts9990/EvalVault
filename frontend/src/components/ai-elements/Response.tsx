import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ResponseProps {
    content: string;
}

export function Response({ content }: ResponseProps) {
    return (
        <div className="prose prose-sm dark:prose-invert max-w-none prose-headings:font-display prose-headings:font-semibold prose-p:leading-relaxed prose-pre:bg-secondary/50 prose-pre:border prose-pre:border-border">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
    );
}
