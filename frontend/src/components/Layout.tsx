import React from "react";
import {
    LayoutDashboard,
    Settings,
    Menu,
    Database,
    PlayCircle,
    Brain,
    X,
    Orbit,
    FlaskConical,
    FileText,
    MessageSquare,
    Target
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

export function Layout({ children }: { children: React.ReactNode }) {
    const [isSidebarOpen, setIsSidebarOpen] = React.useState(true);
    const location = useLocation();

    const navItems = [
        { icon: LayoutDashboard, label: "대시보드", href: "/" },
        { icon: MessageSquare, label: "AI Chat", href: "/chat" },
        { icon: Orbit, label: "시각화", href: "/visualization" },
        { icon: PlayCircle, label: "평가 스튜디오", href: "/studio" },
        { icon: Brain, label: "도메인 메모리", href: "/domain" },
        { icon: Database, label: "지식 베이스", href: "/knowledge" },
        { icon: FlaskConical, label: "분석 실험실", href: "/analysis" },
        { icon: Target, label: "Judge 보정", href: "/calibration" },
        { icon: FileText, label: "고객 리포트", href: "/reports" },
        { icon: Settings, label: "설정", href: "/settings" },
    ];

    return (
        <div className="min-h-screen bg-background text-foreground font-sans relative">
            {/* Subtle indigo bloom — cool, not warm */}
            <div className="pointer-events-none fixed inset-0 overflow-hidden">
                <div className="absolute -top-32 right-0 h-64 w-64 rounded-full bg-primary/5 blur-3xl" />
            </div>

            <div className="flex min-h-screen relative">
                {/* Sidebar — cool card surface */}
                <aside
                    className={`${
                        isSidebarOpen ? "w-52" : "w-12"
                    } bg-card border-r border-border transition-all duration-[var(--duration-slow)] flex flex-col fixed h-full z-20`}
                >
                    {/* Logo lockup */}
                    <div className="h-11 flex items-center px-3 border-b border-border shrink-0">
                        <div
                            className="w-6 h-6 rounded-[var(--radius)] bg-primary flex items-center justify-center shrink-0"
                            style={{ boxShadow: "0 0 10px hsl(var(--primary)/0.4)" }}
                        >
                            <span className="text-primary-foreground font-display font-bold text-xs select-none">E</span>
                        </div>
                        {isSidebarOpen && (
                            <span className="ml-2 font-display font-semibold text-sm text-foreground tracking-tight">
                                EvalVault
                            </span>
                        )}
                        {isSidebarOpen && (
                            <button
                                onClick={() => setIsSidebarOpen(false)}
                                className="ml-auto p-1 hover:bg-secondary rounded-[var(--radius-sm)] text-muted-foreground hover:text-foreground"
                                aria-label="Collapse sidebar"
                            >
                                <X className="w-3.5 h-3.5" />
                            </button>
                        )}
                        {!isSidebarOpen && (
                            <button
                                onClick={() => setIsSidebarOpen(true)}
                                className="ml-auto p-1 hover:bg-secondary rounded-[var(--radius-sm)] text-muted-foreground hover:text-foreground hidden lg:flex"
                                aria-label="Expand sidebar"
                            >
                                <Menu className="w-3.5 h-3.5" />
                            </button>
                        )}
                    </div>

                    <nav className="flex-1 px-1.5 py-2 space-y-px overflow-y-auto">
                        {isSidebarOpen && (
                            <p className="px-2 pt-2 pb-1 font-mono text-[8px] uppercase tracking-[0.25em] text-muted-foreground/50">
                                Workspace
                            </p>
                        )}
                        {navItems.map((item) => {
                            const isActive =
                                item.href === "/"
                                    ? location.pathname === "/"
                                    : location.pathname === item.href ||
                                      location.pathname.startsWith(`${item.href}/`);
                            return (
                                <Link
                                    key={item.label}
                                    to={item.href}
                                    aria-current={isActive ? "page" : undefined}
                                    title={!isSidebarOpen ? item.label : undefined}
                                    className={`
                                        relative flex items-center px-2 py-1.5 rounded-[var(--radius)]
                                        text-xs transition-colors group
                                        ${isActive
                                            ? "bg-primary/10 text-foreground"
                                            : "text-muted-foreground hover:bg-secondary/70 hover:text-foreground"
                                        }
                                    `}
                                >
                                    {/* Indigo left-border for active item */}
                                    {isActive && (
                                        <span
                                            aria-hidden
                                            className="absolute left-0 top-1 bottom-1 w-0.5 rounded-full bg-primary"
                                        />
                                    )}
                                    <item.icon
                                        className={`shrink-0 w-3.5 h-3.5 ${
                                            isActive
                                                ? "text-primary"
                                                : "text-muted-foreground group-hover:text-foreground"
                                        }`}
                                    />
                                    {isSidebarOpen && (
                                        <span className="ml-2 font-medium truncate">{item.label}</span>
                                    )}
                                </Link>
                            );
                        })}
                    </nav>

                    {/* User profile footer */}
                    <div className="p-2 border-t border-border/40 shrink-0">
                        <div className={`flex items-center ${isSidebarOpen ? "gap-2" : "justify-center"}`}>
                            <div className="w-6 h-6 rounded-[var(--radius-sm)] bg-secondary flex items-center justify-center font-mono text-[9px] font-bold text-muted-foreground shrink-0">
                                JS
                            </div>
                            {isSidebarOpen && (
                                <div className="min-w-0">
                                    <p className="text-xs font-medium truncate text-foreground">John Smith</p>
                                    <p className="font-mono text-[9px] text-muted-foreground truncate">john@example.com</p>
                                </div>
                            )}
                        </div>
                    </div>
                </aside>

                {/* Main content area */}
                <div
                    className={`flex-1 flex flex-col min-w-0 relative transition-all duration-[var(--duration-slow)] ${
                        isSidebarOpen ? "ml-52" : "ml-12"
                    }`}
                >
                    {/* Mobile header */}
                    <header className="lg:hidden h-11 flex items-center px-4 border-b border-border bg-background/90 backdrop-blur-sm sticky top-0 z-40">
                        <button
                            onClick={() => setIsSidebarOpen(true)}
                            aria-label="Open sidebar"
                        >
                            <Menu className="w-4 h-4" />
                        </button>
                        <span className="ml-3 font-display font-semibold text-sm">EvalVault</span>
                    </header>

                    {/* Desktop topbar — slim command strip */}
                    <header className="hidden lg:flex h-10 items-center justify-between px-5 border-b border-border/60 bg-background/80 backdrop-blur-sm sticky top-0 z-40">
                        <div className="flex items-center gap-1.5 font-mono text-[10px] text-muted-foreground">
                            <span className="text-foreground/60">workspace</span>
                            <span className="text-border mx-0.5">/</span>
                            <span className="text-foreground">
                                {navItems.find(i =>
                                    i.href === "/"
                                        ? location.pathname === "/"
                                        : location.pathname.startsWith(i.href)
                                )?.label ?? "—"}
                            </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="font-mono text-[9px] text-muted-foreground/50 uppercase tracking-[0.2em]">
                                v1.78.0
                            </span>
                        </div>
                    </header>

                    <main className="flex-1 overflow-y-auto scroll-smooth">
                        {children}
                    </main>
                </div>
            </div>
        </div>
    );
}
