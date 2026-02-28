"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Users, PlusSquare, Github, Globe, Search, BookOpen } from "lucide-react";
import { CommandSearch } from "./CommandSearch";
import { useLanguage } from "@/contexts/LanguageContext";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function Navigation() {
    const pathname = usePathname();
    const { t } = useLanguage();

    const navLinks = [
        { href: "/", label: t("nav.dashboard"), icon: LayoutDashboard },
        { href: "/agents", label: t("nav.market"), icon: Users },
        { href: "/synergy", label: t("nav.synergy"), icon: Globe },
        { href: "/register", label: t("nav.sandbox"), icon: PlusSquare },
        { href: "/guide", label: t("nav.guide"), icon: BookOpen },
    ];

    return (
        <nav className="sticky top-0 z-50 w-full border-b border-white/5 bg-background/80 backdrop-blur-md">
            <CommandSearch />
            <div className="container mx-auto px-4">
                <div className="flex h-14 items-center justify-between">
                    <div className="flex items-center gap-8">
                        <Link href="/" className="flex items-center gap-2 group">
                            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center group-hover:shadow-[0_0_15px_rgba(59,130,246,0.5)] transition-all">
                                <Globe className="w-5 h-5 text-white" />
                            </div>
                            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                                AgentMesh
                            </span>
                        </Link>

                        <div className="hidden md:flex items-center gap-1">
                            {navLinks.map((link) => {
                                const Icon = link.icon;
                                const isActive = pathname === link.href;
                                return (
                                    <Link
                                        key={link.href}
                                        href={link.href}
                                        className={cn(
                                            "px-3 py-1.5 text-xs font-medium rounded-md transition-colors flex items-center gap-2",
                                            isActive
                                                ? "text-white bg-white/5"
                                                : "text-muted-foreground hover:text-white hover:bg-white/5"
                                        )}
                                    >
                                        <Icon className="w-4 h-4" />
                                        {link.label}
                                    </Link>
                                );
                            })}
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-muted-foreground text-[10px] font-mono">
                            <Search className="w-3 h-3" />
                            <span>{t("nav.search_placeholder")}</span>
                        </div>

                        <LanguageSwitcher />

                        <a
                            href="https://github.com/agentmesh/agentmesh"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-muted-foreground hover:text-white transition-colors"
                        >
                            <Github className="w-5 h-5" />
                        </a>

                        <div className="flex items-center gap-2 ml-2">
                            <button className="text-xs font-medium text-muted-foreground hover:text-white px-3 py-1.5 transition-colors">
                                {t("nav.sign_in")}
                            </button>
                            <button className="text-xs font-medium bg-white text-black px-4 py-1.5 rounded-md hover:bg-white/90 transition-colors">
                                {t("nav.sign_up")}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    );
}
