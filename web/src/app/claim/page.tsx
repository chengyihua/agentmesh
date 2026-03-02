"use client";

import { BaseLayout } from "@/components/BaseLayout";
import { useClaim } from "@/hooks/useRegistry";
import { useAuth } from "@/contexts/AuthContext";
import { useState } from "react";
import { Loader2, ShieldCheck, KeyRound, Fingerprint, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ApiError } from "@/types/agent";

export default function ClaimPage() {
    const { isAuthenticated } = useAuth();
    const router = useRouter();
    const claimMutation = useClaim();

    const [agentId, setAgentId] = useState("");
    const [claimCode, setClaimCode] = useState("");
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleClaim = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        
        if (!agentId || !claimCode) {
            setError("Please fill in all fields");
            return;
        }

        try {
            await claimMutation.mutateAsync({ agentId, claimCode });
            setSuccess(true);
        } catch (e: any) {
            const err = e as ApiError;
            const errorMsg = typeof err?.response?.data?.detail === 'string' 
                ? err.response.data.detail 
                : err?.response?.data?.error?.message || err?.message || "Invalid claim code or agent ID";
            setError(errorMsg);
        }
    };

    if (!isAuthenticated && typeof window !== 'undefined') {
        // Redirect to login if not authenticated
        // Using useEffect or similar in a real app, here we just show a message
    }

    return (
        <BaseLayout>
            <div className="flex-1 flex flex-col items-center justify-center p-4 min-h-[calc(100vh-80px)]">
                <div className="w-full max-w-lg">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-6 relative group">
                            <ShieldCheck className="w-8 h-8 text-primary relative z-10" />
                            <div className="absolute inset-0 bg-primary/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl" />
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-2">Claim Agent Ownership</h1>
                        <p className="text-muted-foreground">
                            Bind an autonomous agent to your identity using its unique claim code.
                        </p>
                    </div>

                    {!isAuthenticated ? (
                        <div className="glass p-8 rounded-3xl border border-yellow-500/20 bg-yellow-500/5 text-center">
                            <h3 className="text-yellow-200 font-bold mb-2">Authentication Required</h3>
                            <p className="text-yellow-200/70 text-sm mb-6">
                                You need to be logged in to claim agents.
                            </p>
                            <Link 
                                href="/login"
                                className="inline-flex items-center gap-2 px-6 py-3 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-200 rounded-xl font-bold transition-colors border border-yellow-500/20"
                            >
                                Sign In <ArrowRight className="w-4 h-4" />
                            </Link>
                        </div>
                    ) : success ? (
                        <div className="glass p-8 rounded-3xl border border-green-500/20 bg-green-500/5 text-center animate-in zoom-in-95 duration-300">
                            <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                                <CheckCircle2 className="w-8 h-8 text-green-500" />
                            </div>
                            <h3 className="text-2xl font-bold text-white mb-2">Successfully Claimed!</h3>
                            <p className="text-muted-foreground mb-8">
                                Agent <span className="text-white font-mono bg-white/5 px-2 py-0.5 rounded">{agentId}</span> has been bound to your account.
                            </p>
                            <div className="flex gap-4 justify-center">
                                <Link 
                                    href="/my-agents"
                                    className="px-6 py-3 bg-primary text-white rounded-xl font-bold hover:bg-primary/90 transition-colors"
                                >
                                    View My Agents
                                </Link>
                                <button
                                    onClick={() => {
                                        setSuccess(false);
                                        setAgentId("");
                                        setClaimCode("");
                                    }}
                                    className="px-6 py-3 bg-white/5 text-white rounded-xl font-bold hover:bg-white/10 transition-colors border border-white/10"
                                >
                                    Claim Another
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="glass p-8 rounded-3xl border border-white/5 relative overflow-hidden">
                            <form onSubmit={handleClaim} className="space-y-6 relative z-10">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                                        <Fingerprint className="w-3 h-3 text-primary" />
                                        Agent ID
                                    </label>
                                    <input
                                        type="text"
                                        placeholder="e.g. agent-xyz-123"
                                        value={agentId}
                                        onChange={(e) => setAgentId(e.target.value)}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-white text-sm focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-white/20 font-mono"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                                        <KeyRound className="w-3 h-3 text-primary" />
                                        Claim Code
                                    </label>
                                    <input
                                        type="text"
                                        placeholder="XXXX-XXXX"
                                        value={claimCode}
                                        onChange={(e) => setClaimCode(e.target.value)}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-white text-sm focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-white/20 font-mono tracking-wide"
                                    />
                                    <p className="text-[10px] text-muted-foreground">
                                        You can find this code in the agent's initialization logs.
                                    </p>
                                </div>

                                {error && (
                                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2">
                                        <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                                        <p className="text-xs text-red-400">{error}</p>
                                    </div>
                                )}

                                <button
                                    type="submit"
                                    disabled={claimMutation.isPending || !agentId || !claimCode}
                                    className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3.5 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:shadow-[0_0_25px_rgba(59,130,246,0.5)] hover:-translate-y-0.5 flex items-center justify-center gap-2"
                                >
                                    {claimMutation.isPending ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" /> Verifying...
                                        </>
                                    ) : (
                                        <>
                                            Claim Agent <ArrowRight className="w-4 h-4" />
                                        </>
                                    )}
                                </button>
                            </form>
                        </div>
                    )}
                </div>
            </div>
        </BaseLayout>
    );
}