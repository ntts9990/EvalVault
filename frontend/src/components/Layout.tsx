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
            {/* Dark-ground instrument panel: single faint clay bloom, no light washes */}
            <div className="pointer-events-none fixed inset-0 overflow-hidden">
                <div className="absolute -top-40 left-0 h-80 w-80 rounded-full bg-primary/6 blur-3xl" />
                <div className="absolute bottom-0 right-0 h-60 w-60 rounded-full bg-primary/4 blur-3xl" />
            </div>

            <div className="flex min-h-screen relative">
                {/* Sidebar — dark card surface, slightly lighter than the ground */}
                <aside
                    className={`${
                        isSidebarOpen ? "w-56" : "w-14"
                    } bg-card border-r border-border transition-all duration-[var(--duration-slow)] flex flex-col fixed h-full z-20`}
                >
                    {/* Logo lockup */}
                    <div className="h-12 flex items-center px-4 border-b border-border shrink-0">
                        <div
                            className="w-7 h-7 rounded-[var(--radius)] bg-primary flex items-center justify-center shrink-0"
                            style={{ boxShadow: "0 0 12px hsl(var(--primary)/0.35)" }}
                        >
                            {/* Dark ink on clay — not cream (cream fails WCAG on clay) */}
                            <span className="text-[hsl(30_26%_7%)] font-display font-bold text-sm select-none">E</span>
                        </div>
                        {isSidebarOpen && (
                            <span className="ml-2.5 font-display font-semibold text-base text-foreground tracking-tight">
                                EvalVault
                            </span>
                        )}
                        <button
                            onClick={() => setIsSidebarOpen(false)}
                            className="ml-auto lg:hidden p-1 hover:bg-secondary rounded-[var(--radius-sm)]"
                            aria-label="Close sidebar"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>

                    <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
                        {isSidebarOpen && (
                            <p className="px-3 pt-3 pb-1.5 font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground/60">
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
                                        relative flex items-center px-3 py-2 rounded-[var(--radius)]
                                        text-sm transition-colors group
                                        ${isActive
                                            ? "bg-secondary/80 text-foreground"
                                            : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
                                        }
                                    `}
                                >
                                    {/* Clay left-border for active item — instrument panel style */}
                                    {isActive && (
                                        <span
                                            aria-hidden
                                            className="absolute left-0 top-1 bottom-1 w-0.5 rounded-full bg-primary"
                                        />
                                    )}
                                    <item.icon
                                        className={`shrink-0 w-4 h-4 ${
                                            isActive
                                                ? "text-primary"
                                                : "text-muted-foreground group-hover:text-foreground"
                                        }`}
                                    />
                                    {isSidebarOpen && (
                                        <span className="ml-2.5 font-medium truncate">{item.label}</span>
                                    )}
                                </Link>
                            );
                        })}
                    </nav>

                    {/* User profile footer */}
                    <div className="p-3 border-t border-border/40 shrink-0">
                        <div className={`flex items-center ${isSidebarOpen ? "gap-2.5" : "justify-center"}`}>
                            <div className="w-7 h-7 rounded-[var(--radius-sm)] bg-secondary flex items-center justify-center font-mono text-[10px] font-bold text-muted-foreground shrink-0">
                                JS
                            </div>
                            {isSidebarOpen && (
                                <div className="min-w-0">
                                    <p className="text-xs font-medium truncate text-foreground">John Smith</p>
                                    <p className="font-mono text-[10px] text-muted-foreground truncate">john@example.com</p>
                                </div>
                            )}
                        </div>
                    </div>
                </aside>

                {/* Main content area */}
                <div
                    className={`flex-1 flex flex-col min-w-0 relative transition-all duration-[var(--duration-slow)] ${
                        isSidebarOpen ? "ml-56" : "ml-14"
                    }`}
                >
                    {/* Mobile header */}
                    <header className="lg:hidden h-12 flex items-center px-4 border-b border-border bg-background/90 backdrop-blur-sm sticky top-0 z-40">
                        <button
                            onClick={() => setIsSidebarOpen(true)}
                            aria-label="Open sidebar"
                        >
                            <Menu className="w-5 h-5" />
                        </button>
                        <span className="ml-3 font-display font-semibold text-sm">EvalVault</span>
                    </header>

                    {/* Desktop topbar — slim breadcrumb strip */}
                    <header className="hidden lg:flex h-11 items-center justify-between px-6 border-b border-border/50 bg-background/70 backdrop-blur-sm sticky top-0 z-40">
                        <div className="flex items-center gap-1.5 font-mono text-xs text-muted-foreground">
                            <span className="text-foreground/70">workspace</span>
                            <span className="text-border">/</span>
                            <span className="text-foreground">
                                {navItems.find(i => i.href === location.pathname)?.label ?? "—"}
                            </span>
                        </div>
                    </header>

                    <main className="flex-1 overflow-y-auto p-4 lg:p-6 scroll-smooth">
                        {children}
                    </main>
                </div>
            </div>
        </div>
    );
}
