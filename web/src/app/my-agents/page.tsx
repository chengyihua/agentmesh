"use client";

import { BaseLayout } from "@/components/BaseLayout";
import { AgentCard } from "@/components/AgentCard";
import { useAgents } from "@/hooks/useRegistry";
import { useAuth } from "@/contexts/AuthContext";
import { Search, Loader2, AlertCircle, RefreshCw, ArrowUp, ArrowDown, ChevronDown, User, ShieldCheck } from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useLanguage } from "@/contexts/LanguageContext";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function MyAgentsPage() {
    const { t } = useLanguage();
    const { user } = useAuth();
    const router = useRouter();
    const [search, setSearch] = useState("");
    const [filter, setFilter] = useState<string>("all");
    const [sortBy, setSortBy] = useState<string>("updated_at");
    const [order, setOrder] = useState<string>("desc");

    // Redirect if not logged in
    useEffect(() => {
        if (!user) {
            router.push("/");
        }
    }, [user, router]);

    const { data: agents, isLoading, isError, refetch, isRefetching } = useAgents({
        sort_by: sortBy,
        order: order,
        health_status: filter === "all" ? undefined : filter,
        owner_id: user?.owner_id,
    });

    const filteredAgents = agents?.filter((a) => {
        const matchesSearch = a.name.toLowerCase().includes(search.toLowerCase()) ||
            a.id.toLowerCase().includes(search.toLowerCase()) ||
            a.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()));

        return matchesSearch;
    });

    const filterOptions = [
        { id: "all", label: t("market.filter_all") },
        { id: "healthy", label: t("market.filter_healthy") },
        { id: "unhealthy", label: t("market.filter_unhealthy") },
        { id: "degraded", label: t("market.filter_degraded") },
    ];

    const sortOptions = [
        { id: "trust_score", label: t("market.sort_trust") },
        { id: "updated_at", label: t("market.sort_updated") },
        { id: "created_at", label: t("market.sort_created") },
    ];

    if (!user) return null;

    return (
        <BaseLayout>
            <div className="container mx-auto px-4 py-12">
                {/* Header Area */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2 bg-primary/20 rounded-lg">
                                <User className="w-6 h-6 text-primary" />
                            </div>
                            <h1 className="text-4xl font-bold text-white">My Agents</h1>
                        </div>
                        <p className="text-muted-foreground max-w-xl">
                            Manage agents owned by <span className="text-white font-mono font-bold">{user.owner_id}</span>
                        </p>
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="text-right">
                            <p className="text-[10px] text-muted-foreground uppercase tracking-widest mb-1">Total Owned</p>
                            <p className="text-2xl font-mono font-bold text-white leading-none">{agents?.length || 0}</p>
                        </div>
                    </div>
                </div>

                {/* Controls */}
                <div className="flex flex-col lg:flex-row gap-4 mb-8">
                    <div className="relative flex-1 group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                        <input
                            type="text"
                            placeholder={t("market.search_placeholder")}
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-11 pr-4 text-sm focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all placeholder:text-muted-foreground"
                        />
                    </div>

                    <div className="flex items-center gap-2 overflow-x-auto pb-2 lg:pb-0">
                        {filterOptions.map((opt) => (
                            <button
                                key={opt.id}
                                onClick={() => setFilter(opt.id)}
                                className={cn(
                                    "px-4 py-2 rounded-xl text-xs font-semibold capitalize border transition-all whitespace-nowrap",
                                    filter === opt.id
                                        ? "bg-primary/20 border-primary/40 text-primary shadow-[0_0_15px_rgba(59,130,246,0.15)]"
                                        : "bg-white/5 border-white/10 text-muted-foreground hover:bg-white/10"
                                )}
                            >
                                {opt.label}
                            </button>
                        ))}
                        <div className="w-px h-6 bg-white/10 mx-2"></div>
                        
                        <div className="relative">
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value)}
                                className="appearance-none bg-white/5 border border-white/10 text-xs font-semibold rounded-xl pl-4 pr-10 py-2 text-muted-foreground hover:bg-white/10 focus:outline-none focus:ring-1 focus:ring-primary/20 transition-all cursor-pointer"
                            >
                                {sortOptions.map((opt) => (
                                    <option key={opt.id} value={opt.id} className="bg-gray-900 text-white">
                                        {opt.label}
                                    </option>
                                ))}
                            </select>
                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
                        </div>

                        <button
                            onClick={() => setOrder(order === "asc" ? "desc" : "asc")}
                            className={cn(
                                "flex items-center justify-center w-8 h-8 rounded-xl border transition-all",
                                "bg-white/5 border-white/10 text-muted-foreground hover:bg-white/10"
                            )}
                            title={order === "asc" ? t("market.order_asc") : t("market.order_desc")}
                        >
                            {order === "asc" ? <ArrowUp className="w-3.5 h-3.5" /> : <ArrowDown className="w-3.5 h-3.5" />}
                        </button>
                        <div className="w-px h-6 bg-white/10 mx-2"></div>
                        <button
                            onClick={() => refetch()}
                            className={cn(
                                "p-2 rounded-xl bg-white/5 border border-white/10 text-muted-foreground hover:text-white transition-all",
                                isRefetching && "animate-spin text-primary"
                            )}
                        >
                            <RefreshCw className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Content Grid */}
                {isLoading ? (
                    <div className="h-64 flex flex-col items-center justify-center gap-4 text-muted-foreground">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                        <p className="text-sm font-medium">{t("market.loading")}</p>
                    </div>
                ) : isError ? (
                    <div className="glass border-destructive/20 p-12 text-center rounded-3xl">
                        <AlertCircle className="w-12 h-12 text-destructive mx-auto mb-4" />
                        <h3 className="text-xl font-bold mb-2">{t("market.error_title")}</h3>
                        <p className="text-muted-foreground mb-6">{t("market.error_desc")}</p>
                        <button
                            onClick={() => refetch()}
                            className="px-6 py-2 bg-destructive/10 border border-destructive/20 text-destructive rounded-lg hover:bg-destructive/20 transition-colors"
                        >
                            {t("market.retry")}
                        </button>
                    </div>
                ) : filteredAgents?.length === 0 ? (
                    <div className="glass p-24 text-center rounded-3xl flex flex-col items-center">
                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mb-6">
                            <ShieldCheck className="w-8 h-8 text-muted-foreground" />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">No agents found</h3>
                        <p className="text-muted-foreground text-sm mb-8 max-w-md">
                            You haven't claimed or registered any agents yet with owner ID <span className="font-mono text-white">{user.owner_id}</span>.
                        </p>
                        <div className="flex gap-4">
                            <Link 
                                href="/register"
                                className="px-6 py-3 bg-primary text-white font-bold rounded-xl hover:bg-primary/90 transition-colors"
                            >
                                Register New Agent
                            </Link>
                            <Link 
                                href="/agents"
                                className="px-6 py-3 bg-white/5 border border-white/10 text-white font-bold rounded-xl hover:bg-white/10 transition-colors"
                            >
                                Claim Existing
                            </Link>
                        </div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                        {filteredAgents?.map((agent) => (
                            <AgentCard key={agent.id} agent={agent} />
                        ))}
                    </div>
                )}
            </div>
        </BaseLayout>
    );
}