import { Globe, Shield, Activity, ArrowRight, Tag, Network } from "lucide-react";
import { cn, formatRelativeTime } from "@/lib/utils";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import { Agent } from "@/types/agent";

interface AgentCardProps {
    agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
    const { t, language } = useLanguage();
    const isHealthy = agent.health_status === "healthy";
    const isRelay = agent.protocol?.toLowerCase() === "relay";

    return (
        <Link href={`/agents/${agent.id}`}>
            <div className="glass p-6 rounded-2xl glass-hover group h-full flex flex-col">
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3 min-w-0 flex-1 mr-2">
                        <div className={cn(
                            "w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 transition-all group-hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]",
                            isHealthy ? "bg-primary/10" : "bg-destructive/10"
                        )}>
                            {isRelay ? (
                                <Network className={cn("w-5 h-5", isHealthy ? "text-purple-400" : "text-destructive")} />
                            ) : (
                                <Globe className={cn("w-5 h-5", isHealthy ? "text-primary" : "text-destructive")} />
                            )}
                        </div>
                        <div className="min-w-0 flex-1">
                            <h4 className="font-bold text-white group-hover:text-primary transition-colors truncate">
                                {agent.name}
                            </h4>
                            <p className="text-[10px] font-mono text-muted-foreground truncate">
                                {agent.id}
                            </p>
                        </div>
                    </div>

                    <div className="flex flex-col items-end gap-2 flex-shrink-0">
                        <div className={cn(
                            "flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[9px] font-bold uppercase tracking-wider",
                            isHealthy
                                ? "bg-green-500/10 border-green-500/20 text-green-500"
                                : "bg-destructive/10 border-destructive/20 text-destructive"
                        )}>
                            <span className={cn("w-1 h-1 rounded-full animate-pulse", isHealthy ? "bg-green-500" : "bg-destructive")}></span>
                            {t(`agent_details.status_${agent.health_status}`)}
                        </div>
                        
                        {agent.trust_score !== undefined && (
                            <div className={cn(
                                "flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[9px] font-bold border transition-colors",
                                agent.trust_score >= 0.8
                                    ? "bg-blue-500/10 border-blue-500/20 text-blue-400"
                                    : agent.trust_score >= 0.5
                                        ? "bg-amber-500/10 border-amber-500/20 text-amber-400"
                                        : "bg-red-500/10 border-red-500/20 text-red-400"
                            )}>
                                {agent.trust_score >= 0.8 && (
                                    <Shield className="w-3 h-3 fill-current/20" />
                                )}
                                <span>{t("agent_details.trust_score")}: {(agent.trust_score * 100).toFixed(0)}%</span>
                            </div>
                        )}
                        
                        <span className="text-[9px] text-muted-foreground font-mono opacity-60">v{agent.version}</span>
                    </div>
                </div>

                <p className="text-sm text-muted-foreground mb-6 line-clamp-2 flex-1">
                    {agent.description}
                </p>

                <div className="flex flex-wrap gap-2 mb-6">
                    {agent.tags?.slice(0, 3).map(tag => (
                        <span key={tag} className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-white/5 border border-white/5 text-[10px] text-muted-foreground">
                            <Tag className="w-3 h-3" />
                            {tag}
                        </span>
                    ))}
                    {(agent.tags?.length || 0) > 3 && (
                        <span className="text-[10px] text-muted-foreground px-1">+{(agent.tags?.length || 0) - 3}</span>
                    )}
                </div>

                <div className="pt-4 border-t border-white/5 flex items-center justify-between mt-auto">
                    <div className="flex items-center gap-4 text-[11px] text-muted-foreground font-mono">
                        <div className="flex items-center gap-1">
                            {isRelay ? (
                                <Network className="w-3 h-3 text-purple-400" />
                            ) : (
                                <Shield className="w-3 h-3" />
                            )}
                            <span className={cn(isRelay && "text-purple-400 font-bold")}>{(agent.protocol || "http").toUpperCase()}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <Activity className="w-3 h-3" />
                            <span suppressHydrationWarning>{agent.last_heartbeat ? formatRelativeTime(agent.last_heartbeat, language) : t("agent_details.never")}</span>
                        </div>
                    </div>

                    <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-all group-hover:translate-x-1" />
                </div>
            </div>
        </Link>
    );
}
