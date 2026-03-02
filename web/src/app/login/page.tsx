"use client";

import React, { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { Loader2, Globe, Smartphone, Lock, ArrowRight, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { BaseLayout } from "@/components/BaseLayout";

export default function LoginPage() {
    const { loginWithOtp, sendOtp } = useAuth();
    const router = useRouter();

    const [step, setStep] = useState<'phone' | 'otp'>('phone');
    const [phoneNumber, setPhoneNumber] = useState("");
    const [otpCode, setOtpCode] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [debugCode, setDebugCode] = useState("");

    const handleSendOtp = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!phoneNumber.trim()) return;
        
        setLoading(true);
        setError("");
        try {
            const res = await sendOtp(phoneNumber);
            setStep('otp');
            if (res.debug_code) setDebugCode(res.debug_code);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to send OTP");
        } finally {
            setLoading(false);
        }
    };

    const handleVerify = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!otpCode.trim()) return;
        
        setLoading(true);
        setError("");
        try {
            await loginWithOtp(phoneNumber, otpCode);
            router.push("/my-agents");
        } catch (err: any) {
            setError(err.response?.data?.detail || "Invalid OTP");
        } finally {
            setLoading(false);
        }
    };

    return (
        <BaseLayout>
            <div className="flex-1 flex items-center justify-center p-4 min-h-[calc(100vh-80px)]">
                <div className="w-full max-w-md">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <Link href="/" className="inline-flex items-center gap-2 mb-4 group">
                            <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center group-hover:shadow-[0_0_20px_rgba(59,130,246,0.5)] transition-all">
                                <Globe className="w-6 h-6 text-white" />
                            </div>
                        </Link>
                        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Welcome Back</h1>
                        <p className="text-muted-foreground text-sm">
                            Manage your autonomous agent fleet
                        </p>
                    </div>

                    {/* Card */}
                    <div className="glass p-8 rounded-3xl border border-white/5 relative overflow-hidden">
                        {/* Decorative background elements */}
                        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />
                        <div className="absolute bottom-0 left-0 w-32 h-32 bg-purple-500/5 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2 pointer-events-none" />

                        <div className="relative z-10">
                            {step === 'phone' ? (
                                <form onSubmit={handleSendOtp} className="space-y-6">
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                                            <Smartphone className="w-3 h-3 text-primary" />
                                            Phone Number
                                        </label>
                                        <div className="relative group">
                                            <input
                                                type="tel"
                                                placeholder="+1234567890"
                                                value={phoneNumber}
                                                onChange={(e) => setPhoneNumber(e.target.value)}
                                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-white text-sm focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-white/20"
                                                autoFocus
                                            />
                                        </div>
                                    </div>

                                    {error && (
                                        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                                            <p className="text-xs text-red-400 text-center">{error}</p>
                                        </div>
                                    )}

                                    <button
                                        type="submit"
                                        disabled={loading || !phoneNumber}
                                        className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3.5 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:shadow-[0_0_25px_rgba(59,130,246,0.5)] hover:-translate-y-0.5 flex items-center justify-center gap-2 group"
                                    >
                                        {loading ? (
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                        ) : (
                                            <>
                                                Continue <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                            </>
                                        )}
                                    </button>
                                </form>
                            ) : (
                                <form onSubmit={handleVerify} className="space-y-6 animate-in slide-in-from-right-8 fade-in duration-300">
                                    <button 
                                        type="button"
                                        onClick={() => {
                                            setStep('phone');
                                            setError("");
                                        }}
                                        className="text-xs text-muted-foreground hover:text-white flex items-center gap-1 mb-2 transition-colors"
                                    >
                                        <ArrowLeft className="w-3 h-3" /> Back to phone number
                                    </button>

                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                                            <Lock className="w-3 h-3 text-primary" />
                                            Verification Code
                                        </label>
                                        <p className="text-xs text-muted-foreground mb-4">
                                            Enter the 6-digit code sent to <span className="text-white font-mono">{phoneNumber}</span>
                                        </p>
                                        <input
                                            type="text"
                                            placeholder="000000"
                                            maxLength={6}
                                            value={otpCode}
                                            onChange={(e) => setOtpCode(e.target.value)}
                                            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-white text-lg font-mono text-center tracking-[0.5em] focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-white/10"
                                            autoFocus
                                        />
                                    </div>

                                    {debugCode && (
                                        <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-center">
                                            <p className="text-[10px] text-yellow-500 uppercase font-bold mb-1">Development Mode</p>
                                            <p className="text-lg font-mono text-yellow-200 tracking-widest select-all cursor-pointer">{debugCode}</p>
                                        </div>
                                    )}

                                    {error && (
                                        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                                            <p className="text-xs text-red-400 text-center">{error}</p>
                                        </div>
                                    )}

                                    <button
                                        type="submit"
                                        disabled={loading || otpCode.length < 6}
                                        className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3.5 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:shadow-[0_0_25px_rgba(59,130,246,0.5)] hover:-translate-y-0.5 flex items-center justify-center gap-2"
                                    >
                                        {loading ? (
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                        ) : (
                                            "Verify & Login"
                                        )}
                                    </button>
                                </form>
                            )}
                        </div>
                    </div>
                    
                    <p className="text-center text-xs text-muted-foreground mt-8">
                        By continuing, you agree to AgentMesh's <a href="#" className="underline hover:text-white">Terms of Service</a> and <a href="#" className="underline hover:text-white">Privacy Policy</a>.
                    </p>
                </div>
            </div>
        </BaseLayout>
    );
}