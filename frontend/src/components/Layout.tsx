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
        <div className="min-h-screen bg-background text-foreground font-sans relative overflow-hidden">
            <div className="pointer-events-none absolute -top-32 left-12 h-72 w-72 rounded-full bg-primary/15 blur-3xl" />
            <div className="pointer-events-none absolute top-20 right-0 h-80 w-80 rounded-full bg-slate-900/5 blur-3xl" />
            <div className="flex min-h-screen relative">
                {/* Sidebar */}
                <aside
                    className={`${isSidebarOpen ? "w-64" : "w-20"
                        } bg-card border-r border-border transition-all duration-300 flex flex-col fixed h-full z-20`}
                >
                <div className="h-16 flex items-center px-6 border-b border-border">
                    <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
                        <span className="text-primary-foreground font-bold text-lg">E</span>
                    </div>
                    {isSidebarOpen && (
                        <span className="ml-3 font-bold text-xl tracking-tight font-display">EvalVault</span>
                    )}
                    <button
                        onClick={() => setIsSidebarOpen(false)}
                        className="ml-auto lg:hidden p-1 hover:bg-secondary rounded-md"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    <p className={`px-4 text-xs font-semibold text-muted-foreground mb-4 mt-2 ${!isSidebarOpen && "text-center"}`}>
                        {isSidebarOpen ? "워크스페이스" : "..."}
                    </p>
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
                                className={`flex items-center px-4 py-3 rounded-lg transition-all group ${isActive
                                    ? "bg-primary text-primary-foreground shadow-sm shadow-primary/25"
                                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                                    }`}
                                title={item.label}
                            >
                                <item.icon className={`w-5 h-5 ${isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground"}`} />
                                {isSidebarOpen && <span className="ml-3 font-medium">{item.label}</span>}
                            </Link>
                        );
                    })}
                </nav>

                {/* Footer User Profile */}
                <div className="p-4 border-t border-border/50">
                    <div className={`flex items-center ${isSidebarOpen ? "gap-3" : "justify-center"}`}>
                        <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-xs font-bold text-muted-foreground">
                            JS
                        </div>
                        {isSidebarOpen && (
                            <div className="overflow-hidden">
                                <p className="text-sm font-medium truncate">John Smith</p>
                                <p className="text-xs text-muted-foreground truncate">john@example.com</p>
                            </div>
                        )}
                    </div>
                </div>
                </aside>

                {/* Main Content */}
                <div className={`flex-1 flex flex-col min-w-0 bg-background/50 relative transition-all duration-300 ${isSidebarOpen ? "ml-64" : "ml-20"}`}>
                    {/* Mobile Header */}
                    <header className="lg:hidden h-16 flex items-center px-4 border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-40">
                        <button onClick={() => setIsSidebarOpen(true)}>
                            <Menu className="w-6 h-6" />
                        </button>
                        <span className="ml-3 font-semibold font-display">EvalVault</span>
                    </header>

                {/* Desktop Header */}
                    <header className="hidden lg:flex h-16 items-center justify-between px-8 border-b border-border/40 bg-background/60 backdrop-blur-sm sticky top-0 z-40">
                        <div className="flex items-center text-sm text-muted-foreground">
                            <span className="text-foreground font-medium">워크스페이스</span>
                            <span className="mx-2">/</span>
                            <span>{navItems.find(i => i.href === location.pathname)?.label || "페이지"}</span>
                        </div>
                    </header>

                    <main className="flex-1 overflow-y-auto p-4 lg:p-8 scroll-smooth">
                        {children}
                    </main>
                </div>
            </div>
        </div>
    );
}
