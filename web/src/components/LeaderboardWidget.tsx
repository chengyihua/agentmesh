"use client";

import { Trophy, Medal, Star, TrendingUp, Cpu } from "lucide-react";
import { useLeaderboard } from "@/hooks/useRegistry";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface LeaderboardAgent {
    agent_id: string;
    name: string;
    tier: string;
    trust_score: number;
    metrics: {
        heartbeats: number;
    };
}

export function LeaderboardWidget() {
    const { data: leaderboard, isLoading } = useLeaderboard(5);

    if (isLoading) {
        return (
            <div className="glass p-6 rounded-3xl h-[400px] flex items-center justify-center">
                <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <TrendingUp className="w-8 h-8 animate-pulse" />
                    <p className="text-xs font-medium">Calculating Rankings...</p>
                </div>
            </div>
        );
    }

    const getRankIcon = (index: number) => {
        switch (index) {
            case 0: return <Trophy className="w-4 h-4 text-yellow-500" />;
            case 1: return <Medal className="w-4 h-4 text-slate-300" />;
            case 2: return <Medal className="w-4 h-4 text-amber-600" />;
            default: return <Star className="w-4 h-4 text-muted-foreground/40" />;
        }
    };

    const getTierStyles = (tier: string) => {
        switch (tier) {
            case "Gold": return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
            case "Silver": return "bg-slate-300/10 text-slate-300 border-slate-300/20";
            case "Bronze": return "bg-amber-600/10 text-amber-600 border-amber-600/20";
            default: return "bg-white/5 text-muted-foreground border-white/10";
        }
    };

    return (
        <div className="glass p-6 rounded-3xl h-full flex flex-col border-white/5 bg-gradient-to-br from-white/[0.03] to-transparent">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-primary/10">
                        <Trophy className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                        <h3 className="text-sm font-bold text-white tracking-tight">Mesh Hall of Fame</h3>
                        <p className="text-[10px] text-muted-foreground font-mono uppercase tracking-widest">Top Performers</p>
                    </div>
                </div>
                <TrendingUp className="w-4 h-4 text-muted-foreground/50" />
            </div>

            <div className="space-y-3 flex-1 overflow-auto pr-1 custom-scrollbar">
                {leaderboard?.map((agent: LeaderboardAgent, index: number) => (
                    <Link key={agent.agent_id} href={`/agents/${agent.agent_id}`}>
                        <div className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-all group border border-transparent hover:border-white/5">
                            <div className="relative">
                                <div className={cn(
                                    "w-8 h-8 rounded-full flex items-center justify-center font-mono text-xs font-bold",
                                    index === 0 ? "bg-yellow-500/20 text-yellow-500" : "bg-white/5 text-muted-foreground"
                                )}>
                                    {index + 1}
                                </div>
                                <div className="absolute -top-1 -right-1">
                                    {getRankIcon(index)}
                                </div>
                            </div>

                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between gap-2">
                                    <h4 className="text-xs font-bold text-white group-hover:text-primary transition-colors truncate">
                                        {agent.name}
                                    </h4>
                                    <span className={cn(
                                        "px-1.5 py-0.5 rounded text-[8px] font-bold border uppercase tracking-tighter",
                                        getTierStyles(agent.tier)
                                    )}>
                                        {agent.tier}
                                    </span>
                                </div>
                                <div className="flex items-center gap-3 mt-1 text-[9px] font-mono text-muted-foreground">
                                    <span className="flex items-center gap-1">
                                        <TrendingUp className="w-2.5 h-2.5" />
                                        {(agent.trust_score * 100).toFixed(0)}% Trust
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <Cpu className="w-2.5 h-2.5" />
                                        {agent.metrics.heartbeats} beats
                                    </span>
                                </div>
                            </div>
                        </div>
                    </Link>
                ))}

                {leaderboard?.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-48 text-muted-foreground italic text-xs">
                        No qualified agents yet.
                    </div>
                )}
            </div>

            <Link
                href="/agents"
                className="mt-4 pt-4 border-t border-white/5 text-[10px] font-bold text-primary hover:text-primary/80 transition-colors flex items-center justify-center gap-1"
            >
                View Full Marketplace Rankings
            </Link>
        </div>
    );
}
