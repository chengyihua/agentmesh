"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Search,
    CheckCircle2,
    AlertCircle,
    ArrowRight,
    Terminal,
    Zap,
    Sparkles,
    Globe,
    Handshake,
    Radar,
    Loader2,
    Activity,
    Network
} from "lucide-react";
import axios from "axios";
import { cn } from "@/lib/utils";
import { BaseLayout } from "@/components/BaseLayout";
import { ApiError } from "@/types/agent";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface MatchResult {
    agent_id: string;
    name: string;
    description: string;
    protocol: string;
    endpoint: string;
    score: number;
    suggestion: string;
    action_instructions: {
        step_1: string;
        step_2: string;
        sample_negotiation: {
            url: string;
            payload: Record<string, unknown>;
        };
    };
}

interface NegotiationResult {
    feasible: boolean;
    confidence: number;
    matched_skills: string[];
    instructions: string;
}

interface LogEntry {
    id: string;
    timestamp: string;
    message: string;
    status: 'info' | 'success' | 'warning' | 'error' | 'pending';
}

export default function SynergyPlayground() {
    const { t } = useLanguage();
    const [proposal, setProposal] = useState("");
    const [isMatching, setIsMatching] = useState(false);
    const [match, setMatch] = useState<MatchResult | null>(null);
    const [negotiation, setNegotiation] = useState<NegotiationResult | null>(null);
    const [isNegotiating, setIsNegotiating] = useState(false);
    const [manifest, setManifest] = useState<unknown>(null);
    const [isFetchingManifest, setIsFetchingManifest] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const logsEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll logs
    // useEffect(() => {
    //     if (logsEndRef.current) {
    //         logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    //     }
    // }, [logs]);

    const addLog = (message: string, status: LogEntry['status'] = 'info') => {
        setLogs(prev => [...prev, {
            id: Math.random().toString(36).substring(7),
            timestamp: new Date().toLocaleTimeString(),
            message,
            status
        }]);
    };

    const handleMatch = async () => {
        if (!proposal.trim()) return;
        setIsMatching(true);
        setError(null);
        setMatch(null);
        setNegotiation(null);
        setLogs([]);

        try {
            addLog(t("synergy.log_intent"), "info");
            await new Promise(r => setTimeout(r, 600));

            addLog(t("synergy.log_embedding"), "info");
            await new Promise(r => setTimeout(r, 800));

            addLog(t("synergy.log_querying_dht"), "pending");
            
            const res = await axios.post(`${API_BASE}/agents/match?q=${encodeURIComponent(proposal)}`);
            const result = res.data.data;
            
            await new Promise(r => setTimeout(r, 600));
            addLog(t("synergy.log_candidate_found").replace("{name}", result.name).replace("{id}", result.agent_id), "success");
            addLog(t("synergy.log_relevance_score").replace("{score}", (result.score * 100).toFixed(1)), "success");
            
            setMatch(result);
        } catch (err: unknown) {
            const e = err as ApiError;
            const msg = e.response?.data?.detail?.reason || "Failed to find a matching agent.";
            addLog(t("synergy.log_discovery_error").replace("{error}", msg), "error");
            setError(msg);
        } finally {
            setIsMatching(false);
        }
    };

    const handleNegotiate = async () => {
        if (!match) return;
        setIsNegotiating(true);
        setError(null);

        try {
            addLog(t("synergy.log_initiating_handshake").replace("{endpoint}", match.endpoint), "pending");
            await new Promise(r => setTimeout(r, 800));

            addLog(t("synergy.log_verifying_identity"), "success");
            await new Promise(r => setTimeout(r, 500));

            addLog(t("synergy.log_exchanging_manifest"), "info");
            await new Promise(r => setTimeout(r, 600));

            const res = await axios.post(`${API_BASE}/agents/${match.agent_id}/negotiate`, {
                proposal: proposal
            });
            const result = res.data.data;
            setNegotiation(result);

            if (result.feasible) {
                addLog(t("synergy.log_negotiation_success_log"), "success");
                addLog(t("synergy.log_confidence").replace("{score}", (result.confidence * 100).toFixed(1)), "success");
            } else {
                addLog(t("synergy.log_negotiation_failed_log"), "warning");
            }

        } catch {
            addLog(t("synergy.log_protocol_failed"), "error");
            setError("Negotiation failed.");
        } finally {
            setIsNegotiating(false);
        }
    };

    const fetchManifest = async () => {
        setIsFetchingManifest(true);
        try {
            addLog(t("synergy.log_fetching_manifest"), "pending");
            const res = await axios.get("http://localhost:8000/.well-known/agentmesh");
            setManifest(res.data);
            addLog(t("synergy.log_manifest_retrieved"), "success");
        } catch {
            addLog(t("synergy.log_manifest_failed"), "error");
            setError("Failed to fetch protocol manifest.");
        } finally {
            setIsFetchingManifest(false);
        }
    };

    return (
        <BaseLayout>
            <div className="container mx-auto px-4 py-12 max-w-7xl">
                {/* Hero Header */}
                <div className="mb-12 text-center">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="inline-flex items-center gap-3 mb-4 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium"
                    >
                        <Sparkles className="w-4 h-4" />
                        <span>{t("synergy.protocol_tag")}</span>
                    </motion.div>
                    <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-6 bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent">
                        {t("synergy.hero_title")}
                    </h1>
                    <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                        {t("synergy.subtitle")}
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                    {/* Left Column: Interaction Area (7/12) */}
                    <div className="lg:col-span-7 space-y-8">
                        
                        {/* Step 1: Proposal Input */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="p-1 rounded-3xl bg-gradient-to-br from-white/10 to-white/5 p-[1px]"
                        >
                            <div className="bg-black/40 backdrop-blur-xl rounded-[23px] p-6 border border-white/5">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
                                        <Radar className="w-4 h-4 text-blue-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-sm font-bold text-white">{t("synergy.discovery_phase")}</h3>
                                        <p className="text-[11px] text-muted-foreground">{t("synergy.discovery_desc")}</p>
                                    </div>
                                </div>

                                <div className="relative">
                                    <textarea
                                        value={proposal}
                                        onChange={(e) => setProposal(e.target.value)}
                                        placeholder={t("synergy.input_placeholder")}
                                        className="w-full h-32 bg-white/5 border border-white/10 rounded-xl p-4 text-sm focus:ring-2 focus:ring-primary/50 outline-none resize-none transition-all placeholder:text-white/20 font-mono"
                                    />
                                    <button
                                        onClick={handleMatch}
                                        disabled={isMatching || !proposal.trim()}
                                        className="absolute bottom-4 right-4 bg-primary text-white text-xs font-bold px-6 py-2.5 rounded-lg hover:shadow-[0_0_20px_rgba(59,130,246,0.5)] disabled:opacity-50 transition-all flex items-center gap-2 group"
                                    >
                                        {isMatching ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3 group-hover:scale-110 transition-transform" />}
                                        {isMatching ? t("synergy.finding") : t("synergy.find_btn")}
                                    </button>
                                </div>
                            </div>

                            {error && (
                                <div className="mt-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-[11px] flex items-center gap-2">
                                    <AlertCircle className="w-3 h-3" />
                                    {error}
                                </div>
                            )}
                        </motion.div>

                        {/* Step 2: Match Results */}
                        <AnimatePresence>
                            {match && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    className="p-1 rounded-3xl bg-gradient-to-br from-emerald-500/20 to-purple-500/20 p-[1px]"
                                >
                                    <div className="bg-black/40 backdrop-blur-xl rounded-[23px] p-6 border border-white/5 relative overflow-hidden">
                                        <div className="absolute top-0 right-0 p-8 opacity-[0.03] pointer-events-none">
                                            <Zap className="w-32 h-32" />
                                        </div>

                                        <div className="flex items-center gap-3 mb-6">
                                            <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30">
                                                <Zap className="w-4 h-4 text-emerald-400" />
                                            </div>
                                            <div>
                                                <h3 className="text-sm font-bold text-white">{t("synergy.match_identified")}</h3>
                                                <p className="text-[11px] text-muted-foreground">{t("synergy.match_desc")}</p>
                                            </div>
                                            <div className="ml-auto px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold">
                                                {t("synergy.match_score")}: {(match.score * 100).toFixed(0)}%
                                            </div>
                                        </div>

                                        <div className="mb-6 p-4 rounded-xl bg-white/5 border border-white/5">
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="font-bold text-lg">{match.name}</h4>
                                                <span className="text-[10px] font-mono text-white/40">{match.agent_id}</span>
                                            </div>
                                            <p className="text-sm text-white/70 italic">&quot;{match.suggestion}&quot;</p>
                                        </div>

                                        <div className="grid md:grid-cols-2 gap-4">
                                            <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                                                <div className="flex items-center gap-2 mb-3 text-[10px] font-bold text-white/40 uppercase tracking-widest">
                                                    <Terminal className="w-3 h-3" /> Protocol Schema
                                                </div>
                                                <div className="space-y-2 font-mono text-[10px] text-white/60">
                                                    <div className="flex gap-2">
                                                        <span className="text-blue-400">Endpoint:</span>
                                                        <span className="truncate">{match.endpoint}</span>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <span className="text-purple-400">Protocol:</span>
                                                        <span>{match.protocol}</span>
                                                    </div>
                                                </div>
                                            </div>

                                            <button
                                                onClick={handleNegotiate}
                                                disabled={isNegotiating}
                                                className="h-full bg-white text-black text-xs font-bold py-3 px-6 rounded-xl hover:bg-white/90 disabled:opacity-50 transition-all flex flex-col items-center justify-center gap-2 text-center"
                                            >
                                                {isNegotiating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Handshake className="w-5 h-5" />}
                                                <span>{isNegotiating ? t("synergy.negotiating") : t("synergy.negotiate_btn")}</span>
                                            </button>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Step 3: Negotiation Outcome */}
                        <AnimatePresence>
                            {negotiation && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={cn(
                                        "p-1 rounded-3xl bg-gradient-to-br p-[1px]",
                                        negotiation.feasible ? "from-emerald-500/30 to-emerald-500/10" : "from-amber-500/30 to-amber-500/10"
                                    )}
                                >
                                    <div className="bg-black/40 backdrop-blur-xl rounded-[23px] p-6 border border-white/5">
                                        <div className="flex items-center gap-3 mb-6">
                                            <div className={cn(
                                                "w-8 h-8 rounded-full flex items-center justify-center border",
                                                negotiation.feasible ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-400" : "bg-amber-500/20 border-amber-500/30 text-amber-400"
                                            )}>
                                                {negotiation.feasible ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                                            </div>
                                            <div>
                                                <h3 className="text-sm font-bold text-white">{t("synergy.negotiation_phase")}</h3>
                                                <p className="text-[11px] text-muted-foreground">
                                                    {negotiation.feasible ? t("synergy.negotiation_success") : t("synergy.negotiation_failed")}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="p-4 bg-white/5 rounded-xl border border-white/5 mb-4">
                                            <div className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-2">
                                                {t("synergy.response_payload")}
                                            </div>
                                            <p className="text-sm leading-relaxed text-white/80">{negotiation.instructions}</p>
                                        </div>

                                        {negotiation.matched_skills.length > 0 && (
                                            <div className="flex flex-wrap gap-2 mb-6">
                                                {negotiation.matched_skills.map(skill => (
                                                    <span key={skill} className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-[10px] font-mono text-blue-300">
                                                        {skill}
                                                    </span>
                                                ))}
                                            </div>
                                        )}

                                        {negotiation.feasible && match && (
                                            <div className="flex justify-end">
                                                <Link
                                                    href={`/agents/${match.agent_id}`}
                                                    className="flex items-center gap-2 text-xs font-bold text-emerald-400 hover:text-emerald-300 transition-colors group"
                                                >
                                                    {t("synergy.proceed_gateway")} <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                                </Link>
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* Right Column: Network Terminal (5/12) */}
                    <div className="lg:col-span-5 sticky top-8">
                        <div className="glass rounded-3xl overflow-hidden border border-white/10 bg-black/60 backdrop-blur-2xl flex flex-col h-[600px] shadow-2xl shadow-black/50">
                            {/* Terminal Header */}
                            <div className="bg-white/5 px-5 py-3 border-b border-white/5 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
                                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
                                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/50"></div>
                                    <span className="ml-2 text-xs font-mono font-bold text-white/60 uppercase tracking-wider flex items-center gap-1.5">
                                        <Network className="w-3 h-3" /> {t("synergy.network_activity")}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button 
                                        onClick={fetchManifest} 
                                        disabled={isFetchingManifest}
                                        className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-white/40 hover:text-white"
                                        title={t("synergy.refresh_manifest")}
                                    >
                                        <Globe className={cn("w-3.5 h-3.5", isFetchingManifest && "animate-spin")} />
                                    </button>
                                </div>
                            </div>

                            {/* Terminal Body */}
                            <div className="flex-1 p-5 overflow-auto font-mono text-xs space-y-3 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent bg-black/40">
                                {logs.length === 0 && !isMatching && !isNegotiating ? (
                                    <div className="h-full flex flex-col items-center justify-center text-center opacity-30 space-y-4">
                                        <div className="w-20 h-20 rounded-full border-2 border-dashed border-white/20 flex items-center justify-center animate-[spin_10s_linear_infinite]">
                                            <Activity className="w-8 h-8" />
                                        </div>
                                        <p className="text-sm max-w-[200px]">{t("synergy.waiting_events")}<br/>{t("synergy.initiate_discovery")}</p>
                                    </div>
                                ) : (
                                    <AnimatePresence initial={false}>
                                        {logs.map((log) => (
                                            <motion.div 
                                                key={log.id}
                                                initial={{ opacity: 0, x: -10 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                className="flex gap-3 text-white/80"
                                            >
                                                <span className="text-white/30 shrink-0 select-none text-[10px] py-0.5">[{log.timestamp}]</span>
                                                <div className="flex-1 break-words">
                                                    <span className={cn(
                                                        "mr-2 font-bold text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded-sm",
                                                        log.status === 'success' ? 'bg-green-500/20 text-green-400' :
                                                        log.status === 'error' ? 'bg-red-500/20 text-red-400' :
                                                        log.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                                                        log.status === 'pending' ? 'bg-blue-500/20 text-blue-400 animate-pulse' :
                                                        'bg-white/10 text-white/60'
                                                    )}>
                                                        {log.status === 'pending' ? 'BUSY' : log.status}
                                                    </span>
                                                    <span className={cn(
                                                        "leading-relaxed",
                                                        log.status === 'success' ? 'text-green-100' :
                                                        log.status === 'error' ? 'text-red-100' :
                                                        'text-white/80'
                                                    )}>
                                                        {log.message}
                                                    </span>
                                                </div>
                                            </motion.div>
                                        ))}
                                    </AnimatePresence>
                                )}
                                <div ref={logsEndRef} />
                            </div>

                            {/* Manifest Preview (if active) */}
                            <AnimatePresence>
                                {!!manifest && (
                                    <motion.div
                                        initial={{ height: 0 }}
                                        animate={{ height: "auto" }}
                                        exit={{ height: 0 }}
                                        className="border-t border-white/10 bg-black/80"
                                    >
                                        <div className="p-3 bg-white/5 border-b border-white/5 flex items-center justify-between">
                                            <span className="text-[10px] font-bold text-white/60">{t("synergy.protocol_manifest")}</span>
                                            <button onClick={() => setManifest(null)} className="text-[10px] text-white/40 hover:text-white">{t("synergy.close")}</button>
                                        </div>
                                        <pre className="p-4 text-[10px] text-emerald-400/80 max-h-[200px] overflow-auto">
                                            {JSON.stringify(manifest, null, 2)}
                                        </pre>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* Status Widget */}
                        <div className="mt-6 flex items-center justify-between px-4 py-3 rounded-xl bg-white/5 border border-white/5">
                            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                                {t("synergy.network_status")}: {t("synergy.operational")}
                            </div>
                            <div className="text-[10px] font-mono text-white/40">
                                v1.0.2-beta
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </BaseLayout>
    );
}
