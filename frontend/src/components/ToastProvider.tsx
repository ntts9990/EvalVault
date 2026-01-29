import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

type ToastVariant = "info" | "success" | "warning" | "error";

type ToastItem = {
    id: string;
    message: string;
    variant: ToastVariant;
};

type ToastOptions = {
    variant?: ToastVariant;
    durationMs?: number;
};

type ToastContextValue = {
    pushToast: (message: string, options?: ToastOptions) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = useState<ToastItem[]>([]);
    const timersRef = useRef<Map<string, number>>(new Map());
    const counterRef = useRef(0);

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
        const timer = timersRef.current.get(id);
        if (timer) {
            window.clearTimeout(timer);
            timersRef.current.delete(id);
        }
    }, []);

    const pushToast = useCallback((message: string, options?: ToastOptions) => {
        const id = `${Date.now()}-${counterRef.current++}`;
        const variant = options?.variant ?? "info";
        const durationMs = options?.durationMs ?? 2200;

        setToasts((prev) => [...prev, { id, message, variant }]);
        const timer = window.setTimeout(() => removeToast(id), durationMs);
        timersRef.current.set(id, timer);
    }, [removeToast]);

    useEffect(() => () => {
        timersRef.current.forEach((timer) => window.clearTimeout(timer));
        timersRef.current.clear();
    }, []);

    const contextValue = useMemo(() => ({ pushToast }), [pushToast]);

    return (
        <ToastContext.Provider value={contextValue}>
            {children}
            <div className="fixed right-6 top-6 z-50 space-y-2">
                {toasts.map((toast) => (
                    <div
                        key={toast.id}
                        className={`rounded-lg border px-3 py-2 text-xs shadow-md backdrop-blur bg-background/95 ${variantClass(toast.variant)}`}
                    >
                        {toast.message}
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
}

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error("useToast must be used within ToastProvider");
    }
    return context;
}

function variantClass(variant: ToastVariant) {
    if (variant === "success") {
        return "border-emerald-500/30 text-emerald-600 bg-emerald-500/10";
    }
    if (variant === "warning") {
        return "border-amber-500/30 text-amber-600 bg-amber-500/10";
    }
    if (variant === "error") {
        return "border-rose-500/30 text-rose-600 bg-rose-500/10";
    }
    return "border-border text-muted-foreground";
}
