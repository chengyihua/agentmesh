"use client";

import { useState } from "react";
import { BaseLayout } from "@/components/BaseLayout";
import { useAgent, useAgentStats, useClaim } from "@/hooks/useRegistry";
import { useLanguage } from "@/contexts/LanguageContext";
import { useParams, useRouter } from "next/navigation";
import {
    ArrowLeft, Globe, Shield, Activity, Tag,
    ExternalLink, Clock, Server, Code, Loader2, AlertCircle,
    Fingerprint, User, CheckCircle2, KeyRound, Network, Trophy, Zap, AlertTriangle, Copy
} from "lucide-react";
import { cn, formatRelativeTime } from "@/lib/utils";
import Link from "next/link";
import { InvocationPlayground } from "@/components/InvocationPlayground";
import {
    LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import { TrustEvent, Skill, ApiError } from "@/types/agent";

export default function AgentDetailsPage() {
    const { t, language } = useLanguage();
    const { id } = useParams();
    const router = useRouter();
    const { data: agent, isLoading, isError } = useAgent(id as string);
    const { data: stats } = useAgentStats(id as string);
    const claimMutation = useClaim();
    const [claimCode, setClaimCode] = useState("");
    const [ownerId, setOwnerId] = useState("");
    const [claimSuccess, setClaimSuccess] = useState(false);
    const [claimError, setClaimError] = useState("");
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        if (agent?.endpoint) {
            navigator.clipboard.writeText(agent.endpoint);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleClaim = async () => {
        setClaimError("");
        try {
            await claimMutation.mutateAsync({ agentId: id as string, claimCode, ownerId });
            setClaimSuccess(true);
        } catch (e) {
            const err = e as ApiError;
            setClaimError(err?.response?.data?.error?.message || "Invalid claim code");
        }
    };

    if (isLoading) {
        return (
            <BaseLayout>
                <div className="flex-1 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
            </BaseLayout>
        );
    }

    if (isError || !agent) {
        return (
            <BaseLayout>
                <div className="flex-1 flex flex-col items-center justify-center p-12">
                    <AlertCircle className="w-12 h-12 text-destructive mb-4" />
                    <h2 className="text-2xl font-bold mb-2">{t("agent_details.not_found_title")}</h2>
                    <p className="text-muted-foreground mb-8 text-center max-w-md">
                        {t("agent_details.not_found_desc").replace("{id}", id as string)}
                    </p>
                    <button
                        onClick={() => router.push("/agents")}
                        className="px-6 py-2 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-all font-bold"
                    >
                        {t("agent_details.return_market")}
                    </button>
                </div>
            </BaseLayout>
        );
    }

    const isHealthy = agent.health_status === "healthy";
    const isRelay = agent.protocol?.toLowerCase() === "relay";

    return (
        <BaseLayout>
            <div className="container mx-auto px-4 py-12">
                {/* Back Button */}
                <Link
                    href="/agents"
                    className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-white transition-colors mb-12 group"
                >
                    <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    {t("agent_details.back_to_market")}
                </Link>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 items-start">
                    <div className="lg:col-span-2">
                        {/* Agent Header */}
                        <div className="flex items-start gap-6 mb-10">
                            <div className={cn(
                                "w-20 h-20 rounded-2xl flex items-center justify-center shrink-0 shadow-2xl",
                                isHealthy ? "bg-primary/10 shadow-primary/10" : "bg-destructive/10 shadow-destructive/10"
                            )}>
                                {isRelay ? (
                                    <Network className={cn("w-10 h-10", isHealthy ? "text-purple-400" : "text-destructive")} />
                                ) : (
                                    <Globe className={cn("w-10 h-10", isHealthy ? "text-primary" : "text-destructive")} />
                                )}
                            </div>
                            <div>
                                <div className="flex items-center gap-3 mb-2 flex-wrap">
                                    <h1 className="text-4xl font-extrabold text-white tracking-tight leading-none">{agent.name}</h1>
                                    <div className="flex items-center gap-2">
                                        <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-xs font-mono text-muted-foreground">
                                            v{agent.version}
                                        </span>
                                        {isRelay && (
                                            <span className="px-2 py-0.5 rounded-md bg-purple-500/10 border border-purple-500/20 text-xs font-bold text-purple-400 flex items-center gap-1">
                                                <Network className="w-3 h-3" /> RELAY
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 text-sm font-mono text-muted-foreground">
                                    <Fingerprint className="w-4 h-4 opacity-50" />
                                    <span className="break-all">{agent.id}</span>
                                </div>
                            </div>
                        </div>

                        {/* Description */}
                        <div className="glass p-8 rounded-3xl mb-10 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <Code className="w-24 h-24" />
                            </div>
                            <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                                <User className="w-4 h-4 text-primary" />
                                {t("agent_details.about_this_agent")}
                            </h3>
                            <p className="text-lg text-muted-foreground leading-relaxed">
                                {agent.description}
                            </p>
                        </div>

                        {/* Trust Score Breakdown (New Feature) */}
                        {agent.trust_score !== undefined && (
                            <div className="mb-10">
                                <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-6 flex items-center gap-2">
                                    <Shield className="w-4 h-4 text-primary" />
                                    {t("agent_details.trust_analysis")}
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    {/* Main Score */}
                                    <div className="glass p-6 rounded-2xl md:col-span-1 flex flex-col items-center justify-center text-center relative overflow-hidden">
                                        <div className={cn(
                                            "absolute inset-0 opacity-10 blur-3xl",
                                            agent.trust_score >= 0.8 ? "bg-blue-500" : agent.trust_score >= 0.5 ? "bg-amber-500" : "bg-red-500"
                                        )} />
                                        <div className="relative z-10">
                                            <span className="text-xs text-muted-foreground uppercase tracking-widest font-bold mb-2 block">{t("agent_details.trust_score")}</span>
                                            <div className={cn(
                                                "text-5xl font-black mb-2",
                                                agent.trust_score >= 0.8 ? "text-blue-400" : agent.trust_score >= 0.5 ? "text-amber-400" : "text-red-400"
                                            )}>
                                                {(agent.trust_score * 100).toFixed(0)}
                                            </div>
                                            <div className="flex items-center justify-center gap-1.5">
                                                {agent.trust_score >= 0.8 ? (
                                                    <span className="flex items-center gap-1 text-[10px] font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full border border-blue-500/20">
                                                        <Trophy className="w-3 h-3" /> {t("agent_details.status_top_tier")}
                                                    </span>
                                                ) : agent.trust_score < 0.5 ? (
                                                    <span className="flex items-center gap-1 text-[10px] font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded-full border border-red-500/20">
                                                        <AlertTriangle className="w-3 h-3" /> {t("agent_details.status_low_trust")}
                                                    </span>
                                                ) : (
                                                    <span className="flex items-center gap-1 text-[10px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                                                        <Activity className="w-3 h-3" /> {t("agent_details.status_standard")}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Event Metrics Breakdown */}
                                    <div className="glass p-6 rounded-2xl md:col-span-2 flex flex-col justify-center">
                                        <div className="space-y-4">
                                            {[
                                                { label: t("agent_details.availability"), value: stats?.trust_breakdown?.availability || 0, color: "bg-blue-500" },
                                                { label: t("agent_details.reliability"), value: stats?.trust_breakdown?.reliability || 0, color: "bg-purple-500" },
                                                { label: t("agent_details.performance"), value: stats?.trust_breakdown?.performance || 0, color: "bg-emerald-500" }
                                            ].map((item) => (
                                                <div key={item.label} className="space-y-1">
                                                    <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                                                        <span>{item.label}</span>
                                                        <span className="text-white">{Math.round(item.value * 100)}%</span>
                                                    </div>
                                                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                                        <div
                                                            className={cn("h-full transition-all duration-1000 ease-out", item.color)}
                                                            style={{ width: `${item.value * 100}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                        
                                        <div className="mt-6 pt-4 border-t border-white/5 grid grid-cols-3 gap-2 text-center">
                                            <div>
                                                <div className="text-lg font-bold text-white">{stats?.total_invocations || 0}</div>
                                                <div className="text-[9px] text-muted-foreground uppercase">{t("agent_details.calls")}</div>
                                            </div>
                                            <div>
                                                <div className="text-lg font-bold text-white">{stats?.error_rate ? `${(stats.error_rate * 100).toFixed(0)}%` : "0%"}</div>
                                                <div className="text-[9px] text-muted-foreground uppercase">{t("agent_details.errors")}</div>
                                            </div>
                                            <div>
                                                <div className="text-lg font-bold text-white">{stats?.avg_latency ? `${stats.avg_latency.toFixed(0)}ms` : "-"}</div>
                                                <div className="text-[9px] text-muted-foreground uppercase">{t("agent_details.latency")}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Trust History Chart */}
                        {stats?.trust_breakdown?.history && stats.trust_breakdown.history.length > 0 && (
                            <div className="mb-10">
                                <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-6 flex items-center gap-2">
                                    <Activity className="w-4 h-4 text-primary" />
                                    {t("agent_details.trust_history")}
                                </h3>
                                <div className="glass p-6 rounded-2xl h-[300px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={stats.trust_breakdown.history}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                                            <XAxis 
                                                dataKey="timestamp" 
                                                tickFormatter={(t) => new Date(t).toLocaleTimeString(language === 'zh' ? 'zh-CN' : 'en-US')} 
                                                stroke="#ffffff50" 
                                                tick={{ fontSize: 10 }}
                                                interval="preserveStartEnd"
                                            />
                                            <YAxis 
                                                domain={[0, 1]} 
                                                stroke="#ffffff50" 
                                                tick={{ fontSize: 10 }} 
                                            />
                                            <Tooltip 
                                                contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px' }}
                                                labelStyle={{ color: '#888' }}
                                                formatter={(value: number | string | Array<number | string> | undefined) => [
                                                    value !== undefined ? (Number(value) * 100).toFixed(1) + "%" : "0%", 
                                                    t("agent_details.trust_score")
                                                ]}
                                                labelFormatter={(label) => new Date(label).toLocaleString(language === 'zh' ? 'zh-CN' : 'en-US')}
                                            />
                                            <Line 
                                                type="monotone" 
                                                dataKey="score" 
                                                stroke="#3b82f6" 
                                                strokeWidth={2} 
                                                dot={false} 
                                                activeDot={{ r: 4, fill: '#3b82f6' }} 
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        )}

                        {/* Recent Events Log */}
                        {stats?.trust_breakdown?.history && stats.trust_breakdown.history.length > 0 && (
                             <div className="mb-10">
                                <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-6 flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-primary" />
                                    {t("agent_details.recent_events")}
                                </h3>
                                <div className="glass rounded-2xl overflow-hidden border border-white/5">
                                    <table className="w-full text-left text-xs">
                                        <thead className="bg-white/5 text-muted-foreground font-mono uppercase">
                                            <tr>
                                                <th className="p-4 font-medium">{t("agent_details.table_time")}</th>
                                                <th className="p-4 font-medium">{t("agent_details.table_event")}</th>
                                                <th className="p-4 font-medium text-right">{t("agent_details.table_impact")}</th>
                                                <th className="p-4 font-medium text-right">{t("agent_details.table_score")}</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-white/5">
                                            {[...stats.trust_breakdown.history].reverse().slice(0, 10).map((event: TrustEvent, i: number) => (
                                                <tr key={i} className="hover:bg-white/5 transition-colors">
                                                    <td className="p-4 text-muted-foreground font-mono whitespace-nowrap">
                                                        {formatRelativeTime(event.timestamp, language)}
                                                    </td>
                                                    <td className="p-4 font-bold text-white">
                                                        <span className={cn(
                                                            "px-2 py-1 rounded text-[10px] uppercase border font-mono",
                                                            (event.event === "success" || event.event === "heartbeat") ? "bg-green-500/10 border-green-500/20 text-green-400" :
                                                            event.event === "decay" ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
                                                            "bg-red-500/10 border-red-500/20 text-red-400"
                                                        )}>
                                                            {t(`agent_details.event_${event.event}`) || event.event}
                                                        </span>
                                                    </td>
                                                    <td className={cn("p-4 text-right font-mono font-bold", event.delta > 0 ? "text-green-400" : event.delta < 0 ? "text-red-400" : "text-muted-foreground")}>
                                                        {event.delta > 0 ? "+" : ""}{event.delta?.toFixed(3)}
                                                    </td>
                                                    <td className="p-4 text-right font-mono text-white">
                                                        {(event.score * 100).toFixed(1)}%
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                        <div className="mb-12">
                            <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-6 flex items-center gap-2">
                                <Zap className="w-4 h-4 text-primary" />
                                {t("agent_details.capabilities")}
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {(agent.skills || []).map((skill: Skill) => (
                                    <div key={skill.name} className="glass p-5 rounded-2xl group border-l-4 border-l-primary/30 hover:border-l-primary transition-all">
                                        <h4 className="font-bold text-white mb-2 group-hover:text-primary transition-colors flex items-center justify-between">
                                            {skill.name}
                                            <Code className="w-3 h-3 opacity-0 group-hover:opacity-50 transition-opacity" />
                                        </h4>
                                        <p className="text-xs text-muted-foreground leading-relaxed">{skill.description}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Interactive Playground */}
                        <InvocationPlayground agentId={agent.id} skills={agent.skills || []} />

                        {/* Technical Metadata */}
                        <div>
                            <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-6 flex items-center gap-2">
                                <Code className="w-4 h-4 text-primary" />
                                {t("agent_details.technical_metadata")}
                            </h3>
                            <div className="bg-black/40 rounded-2xl p-6 border border-white/5 font-mono text-xs space-y-3">
                                {[
                                    { key: t("agent_details.meta_endpoint"), value: agent.endpoint },
                                    { key: t("agent_details.meta_protocol"), value: agent.protocol?.toUpperCase() },
                                    { key: t("agent_details.meta_auth_required"), value: String(agent.auth_required ?? false) },
                                    { key: t("agent_details.meta_permissions"), value: agent.permissions?.length ? agent.permissions.join(", ") : "none" },
                                    { key: t("agent_details.meta_skills_count"), value: String(agent.skills?.length ?? 0) },
                                    { key: t("agent_details.meta_species_id"), value: agent.species_id ? `${agent.species_id.slice(0, 16)}…` : "—" },
                                ].map(({ key, value }) => (
                                    <div key={key} className="flex items-start justify-between gap-4">
                                        <span className="text-white/30 shrink-0">{key}</span>
                                        <span className="text-white/70 text-right break-all">{value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Sidebar / Metadata */}
                    <div className="space-y-6">
                        <div className="glass p-8 rounded-3xl border border-white/5">
                            <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-6 flex items-center gap-2">
                                <Server className="w-4 h-4 text-primary" />
                                {t("agent_details.network_status")}
                            </h3>

                            <div className="space-y-6">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">{t("agent_details.health_check")}</span>
                                    <div className={cn(
                                        "flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-bold uppercase border",
                                        isHealthy
                                            ? "bg-green-500/10 border-green-500/20 text-green-500"
                                            : "bg-destructive/10 border-destructive/20 text-destructive"
                                    )}>
                                        <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse", isHealthy ? "bg-green-500" : "bg-destructive")}></span>
                                        {t(`agent_details.status_${agent.health_status}`)}
                                    </div>
                                </div>

                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">{t("agent_details.last_heartbeat")}</span>
                                    <span className="text-xs font-mono text-white" suppressHydrationWarning>
                                        {agent.last_heartbeat ? formatRelativeTime(agent.last_heartbeat, language) : t("agent_details.never")}
                                    </span>
                                </div>

                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">{t("agent_details.protocol")}</span>
                                    <span className={cn(
                                        "text-xs font-mono px-2 py-0.5 rounded border uppercase font-bold",
                                        isRelay ? "bg-purple-500/10 border-purple-500/20 text-purple-400" : "bg-white/5 border-white/10 text-white"
                                    )}>
                                        {isRelay ? "RELAY" : agent.protocol}
                                    </span>
                                </div>

                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">{t("agent_details.endpoint")}</span>
                                    <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
                                        {isRelay ? (
                                            <span className="flex items-center gap-1 text-purple-400" title="Relay Tunnel Active">
                                                <Network className="w-3 h-3" /> {t("agent_details.secure_tunnel")}
                                            </span>
                                        ) : (
                                            <span className="truncate max-w-[120px]" title={agent.endpoint}>
                                                {agent.endpoint.replace(/^https?:\/\//, '')}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="mt-8 pt-8 border-t border-white/5">
                                <button
                                    onClick={handleCopy}
                                    className={cn(
                                        "w-full py-3 text-center font-bold rounded-xl flex items-center justify-center gap-2 transition-all text-sm",
                                        isRelay
                                            ? "bg-purple-500 hover:bg-purple-600 text-white shadow-[0_0_20px_rgba(168,85,247,0.4)]"
                                            : copied
                                                ? "bg-green-500 hover:bg-green-600 text-white"
                                                : "bg-white hover:bg-white/90 text-black"
                                    )}
                                >
                                    {isRelay ? (
                                        <>{t("agent_details.connect_via_relay")} <Network className="w-4 h-4" /></>
                                    ) : copied ? (
                                        <>{t("agent_details.copied")} <CheckCircle2 className="w-4 h-4" /></>
                                    ) : (
                                        <>{t("agent_details.direct_access")} <Copy className="w-4 h-4" /></>
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* Claim Widget */}
                        <div className="glass p-6 rounded-2xl border border-white/5">
                            <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                                <KeyRound className="w-4 h-4 text-primary" />
                                {t("agent_details.ownership")}
                            </h3>
                            {!claimSuccess ? (
                                <div className="space-y-3">
                                    <input
                                        type="text"
                                        placeholder={t("agent_details.owner_id_placeholder")}
                                        value={ownerId}
                                        onChange={(e) => setOwnerId(e.target.value)}
                                        className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary/50 transition-colors"
                                    />
                                    <input
                                        type="text"
                                        placeholder={t("agent_details.claim_code_placeholder")}
                                        value={claimCode}
                                        onChange={(e) => setClaimCode(e.target.value)}
                                        className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary/50 transition-colors"
                                    />
                                    {claimError && (
                                        <p className="text-xs text-destructive flex items-center gap-1">
                                            <AlertCircle className="w-3 h-3" /> {claimError}
                                        </p>
                                    )}
                                    <button
                                        onClick={handleClaim}
                                        disabled={claimMutation.isPending || !claimCode || !ownerId}
                                        className="w-full py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-bold text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                    >
                                        {claimMutation.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <KeyRound className="w-3 h-3" />}
                                        {claimMutation.isPending ? t("agent_details.verifying") : t("agent_details.claim_agent")}
                                    </button>
                                </div>
                            ) : (
                                <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 flex flex-col items-center text-center">
                                    <CheckCircle2 className="w-8 h-8 text-green-500 mb-2" />
                                    <p className="text-sm font-bold text-green-400">{t("agent_details.claim_success")}</p>
                                    <p className="text-xs text-muted-foreground mt-1">{t("agent_details.claim_success_desc")}</p>
                                </div>
                            )}
                        </div>

                        {/* Tags */}
                        {agent.tags && agent.tags.length > 0 && (
                            <div className="glass p-8 rounded-3xl">
                                <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4">{t("agent_details.tags")}</h3>
                                <div className="flex flex-wrap gap-2">
                                    {agent.tags.map((tag: string) => (
                                        <span key={tag} className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/5 text-[11px] text-muted-foreground">
                                            <Tag className="w-3 h-3" />
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </BaseLayout>
    );
}
