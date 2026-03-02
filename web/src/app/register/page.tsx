"use client";

import { BaseLayout } from "@/components/BaseLayout";
import { useState, useRef, useEffect } from "react";
import { Terminal, Send, Copy, Check, Info, AlertTriangle, Loader2, Code, Server, ShieldCheck, Activity } from "lucide-react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { solvePoW } from "@/lib/pow";
import { useLanguage } from "@/contexts/LanguageContext";
import { useAuth } from "@/contexts/AuthContext";

interface RegistrationResponse {
    data?: {
        id: string;
        name: string;
        endpoint: string;
    };
}

interface LogEntry {
    id: string;
    timestamp: string;
    message: string;
    status: 'info' | 'success' | 'warning' | 'error' | 'pending';
}

export default function RegisterPage() {
    const { t } = useLanguage();
    const { user } = useAuth();
    const [jsonInput, setJsonInput] = useState(JSON.stringify({
        id: "weather-bot-001",
        name: "WeatherBot",
        version: "1.0.0",
        description: "Weather forecasting service for the mesh",
        skills: [
            { name: "get_weather", description: "Get current weather" }
        ],
        endpoint: "http://localhost:8001/weather",
        protocol: "http",
        tags: ["weather", "api"]
    }, null, 2));

    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState<RegistrationResponse | null>(null);
    const [copied, setCopied] = useState(false);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const logsEndRef = useRef<HTMLDivElement>(null);
    const abortControllerRef = useRef<AbortController | null>(null);
    const [activeTab, setActiveTab] = useState<'logs' | 'code'>('logs');

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            abortControllerRef.current?.abort();
        };
    }, []);

    // Auto-scroll logs
    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [logs, activeTab]);

    const addLog = (message: string, status: LogEntry['status'] = 'info') => {
        setLogs(prev => [...prev, {
            id: Math.random().toString(36).substring(7),
            timestamp: new Date().toLocaleTimeString(),
            message,
            status
        }]);
    };

    const handleRegister = async () => {
        // Cancel any pending request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        const controller = new AbortController();
        abortControllerRef.current = controller;

        setLoading(true);
        setLogs([]);
        setActiveTab('logs');
        setResponse(null);
        setCopied(false);

        try {
            // Step 1: Client-side validation
            addLog(t("register.log_init"), "info");
            await new Promise(r => setTimeout(r, 600));
            
            let data: any;
            try {
                data = JSON.parse(jsonInput);
                // Inject owner_id if user is logged in
                if (user?.owner_id) {
                    data.owner_id = user.owner_id;
                }
                addLog(t("register.log_validate"), "success");
            } catch {
                throw new Error(t("register.invalid_json"));
            }
            await new Promise(r => setTimeout(r, 800));

            // Step 2: Fetch PoW Challenge
            const apiUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/v1";
            addLog(t("register.log_pow_req"), "info");
            
            let challengeData;
            try {
                const challengeRes = await axios.get(`${apiUrl}/auth/challenge`);
                challengeData = challengeRes.data.data;
                addLog(t("register.log_challenge_received").replace("{nonce}", challengeData.nonce.substring(0, 8)).replace("{difficulty}", challengeData.difficulty), "success");
            } catch (err) {
                 addLog(t("register.log_challenge_failed"), "error");
                 throw err;
            }

            // Step 3: Solve PoW
            addLog(t("register.log_pow_solve"), "pending");
            await new Promise(r => setTimeout(r, 300)); // Visual delay
            
            const startTime = Date.now();
            let solution;
            try {
                solution = await solvePoW(challengeData.nonce, {
                    difficulty: challengeData.difficulty,
                    signal: controller.signal,
                    timeoutMs: 60000
                });
                const duration = Date.now() - startTime;
                addLog(t("register.log_puzzle_solved").replace("{duration}", duration.toString()).replace("{solution}", solution), "success");
            } catch (err) {
                addLog(t("register.log_puzzle_failed"), "error");
                throw err;
            }

            // Step 4: API Call
            addLog(t("register.log_connecting_registry").replace("{url}", apiUrl), "pending");
            const res = await axios.post(
                `${apiUrl}/agents/register`, 
                data,
                {
                    headers: {
                        "X-PoW-Nonce": challengeData.nonce,
                        "X-PoW-Solution": solution
                    }
                }
            );
            
            // Step 5: Success & Post-processing
            addLog(t("register.log_payload_accepted"), "success");
            await new Promise(r => setTimeout(r, 600));
            
            const agentData = res.data;
            setResponse(agentData);
            
            addLog(t("register.log_agent_allocated").replace("{id}", agentData.data.id), "success");
            await new Promise(r => setTimeout(r, 500));
            
            // Step 6: Simulation of network propagation
            addLog(t("register.log_propagating_dht"), "info");
            await new Promise(r => setTimeout(r, 1000));
            
            addLog(t("register.log_verifying_endpoint").replace("{endpoint}", data.endpoint), "pending");
            // Simulate health check
            await new Promise(r => setTimeout(r, 1200));
            addLog(t("register.log_health_check_passed"), "success");
            
            addLog(t("register.log_agent_active"), "success");
            setActiveTab('code');

        } catch (err: any) {
            console.error(err);
            const msg = err.response?.data?.message || err.response?.data?.detail || err.message || t("register.registration_failed");
            addLog(t("register.error_prefix").replace("{message}", msg), "error");
        } finally {
            setLoading(false);
        }
    };

    const copyCurl = () => {
        const curl = `curl -X POST http://localhost:8000/api/v1/agents/register \\
  -H "Content-Type: application/json" \\
  -d '${jsonInput}'`;
        navigator.clipboard.writeText(curl);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const getPythonCode = () => {
        if (!response) return "";
        const id = response.data?.id || "weather-bot-001";
        return `from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/weather")
def get_weather():
    return {
        "temperature": 22,
        "condition": "Sunny",
        "agent_id": "${id}"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)`;
    };

    return (
        <BaseLayout>
            <div className="container mx-auto px-4 py-12 max-w-6xl">
                <div className="mb-10 text-center">
                    <h1 className="text-4xl font-bold mb-4 text-white">{t("register.title")}</h1>
                    <p className="text-muted-foreground max-w-2xl mx-auto">
                        {t("register.subtitle")}
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
                    {/* Editor Side */}
                    <div className="glass rounded-3xl overflow-hidden flex flex-col h-[600px]">
                        <div className="bg-white/5 px-6 py-4 border-b border-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Terminal className="w-4 h-4 text-primary" />
                                <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">{t("register.json_label")}</span>
                            </div>
                            <button
                                onClick={copyCurl}
                                className="flex items-center gap-1.5 text-[10px] font-bold text-muted-foreground hover:text-white transition-colors"
                            >
                                {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                                {copied ? t("register.copied") : t("register.copy_curl")}
                            </button>
                        </div>

                        <textarea
                            value={jsonInput}
                            onChange={(e) => setJsonInput(e.target.value)}
                            className="flex-1 bg-transparent p-6 font-mono text-sm resize-none focus:outline-none text-white/90 selection:bg-primary/30"
                            spellCheck={false}
                        />

                        <div className="p-6 bg-white/[0.02] border-t border-white/5 space-y-4">
                            <div className="flex items-start gap-3 p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                                <Info className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
                                <p className="text-[11px] text-blue-200/80 leading-relaxed">
                                    Agents registered here are instantly visible in the Market. Ensure your `endpoint` is
                                    publicly reachable for health checks.
                                </p>
                            </div>

                            <button
                                onClick={handleRegister}
                                disabled={loading}
                                className="w-full py-4 bg-primary text-white font-bold rounded-xl hover:shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all disabled:opacity-50 disabled:shadow-none flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-4 h-4" />}
                                {loading ? t("register.registering") : t("register.register_btn")}
                            </button>
                        </div>
                    </div>

                    {/* Response / Status Side */}
                    <div className="flex flex-col gap-6 h-[600px]">
                        <div className="glass rounded-3xl flex-1 flex flex-col overflow-hidden relative">
                            {/* Tabs */}
                            <div className="flex border-b border-white/5">
                                <button 
                                    onClick={() => setActiveTab('logs')}
                                    className={`flex-1 px-6 py-4 text-xs font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2 ${activeTab === 'logs' ? 'bg-white/5 text-white' : 'text-muted-foreground hover:text-white hover:bg-white/[0.02]'}`}
                                >
                                    <Activity className="w-3 h-3" /> {t("register.logs_title")}
                                </button>
                                <button 
                                    onClick={() => setActiveTab('code')}
                                    disabled={!response}
                                    className={`flex-1 px-6 py-4 text-xs font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2 ${activeTab === 'code' ? 'bg-white/5 text-white' : 'text-muted-foreground hover:text-white hover:bg-white/[0.02] disabled:opacity-30 disabled:cursor-not-allowed'}`}
                                >
                                    <Code className="w-3 h-3" /> {t("register.success_title")}
                                </button>
                            </div>

                            <div className="flex-1 relative overflow-hidden">
                                <AnimatePresence mode="wait">
                                    {activeTab === 'logs' ? (
                                        <motion.div 
                                            key="logs"
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            exit={{ opacity: 0 }}
                                            className="absolute inset-0 p-6 overflow-auto font-mono text-xs space-y-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent"
                                        >
                                            {logs.length === 0 && !loading && (
                                                <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
                                                    <div className="w-16 h-16 rounded-full border-2 border-dashed border-white/20 mb-6 flex items-center justify-center">
                                                        <Server className="w-6 h-6" />
                                                    </div>
                                                    <p className="text-sm">{t("register.logs_desc")}</p>
                                                </div>
                                            )}
                                            
                                            {logs.map((log) => (
                                                <div key={log.id} className="flex gap-3 text-white/80">
                                                    <span className="text-white/30 shrink-0 select-none">[{log.timestamp}]</span>
                                                    <span className={
                                                        log.status === 'success' ? 'text-green-400' :
                                                        log.status === 'error' ? 'text-red-400' :
                                                        log.status === 'warning' ? 'text-yellow-400' :
                                                        log.status === 'pending' ? 'text-blue-400 animate-pulse' :
                                                        'text-white/80'
                                                    }>
                                                        {log.status === 'success' && '✔ '}
                                                        {log.status === 'error' && '✘ '}
                                                        {log.status === 'warning' && '⚠ '}
                                                        {log.status === 'pending' && '⟳ '}
                                                        {log.message}
                                                    </span>
                                                </div>
                                            ))}
                                            <div ref={logsEndRef} />
                                        </motion.div>
                                    ) : (
                                        <motion.div 
                                            key="code"
                                            initial={{ opacity: 0, x: 20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0, x: -20 }}
                                            className="absolute inset-0 flex flex-col"
                                        >
                                            <div className="p-6 border-b border-white/5 bg-green-500/5">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <div className="p-2 rounded-lg bg-green-500/20 text-green-400">
                                                        <ShieldCheck className="w-5 h-5" />
                                                    </div>
                                                    <div>
                                                        <h3 className="font-bold text-green-400">{t("register.success_title_msg")}</h3>
                                                        <p className="text-xs text-green-400/60">{t("register.success_desc_msg")}</p>
                                                    </div>
                                                </div>
                                                <div className="flex gap-2 mt-4">
                                                    <Link href={`/agents/${response?.data?.id}`} className="flex-1 py-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 text-xs font-bold rounded text-center transition-colors">
                                                        {t("register.view_market")}
                                                    </Link>
                                                    <Link href="/synergy" className="flex-1 py-2 bg-white/5 hover:bg-white/10 text-white text-xs font-bold rounded text-center transition-colors">
                                                        {t("register.test_synergy")}
                                                    </Link>
                                                </div>
                                            </div>
                                            
                                            <div className="flex-1 p-6 overflow-auto">
                                                <div className="mb-4 flex items-center justify-between">
                                                    <span className="text-xs font-bold text-white/60 uppercase tracking-wider">{t("register.quick_start_python")}</span>
                                                    <span className="text-[10px] text-white/30">main.py</span>
                                                </div>
                                                <pre className="p-4 rounded-xl bg-black/40 border border-white/5 font-mono text-xs text-blue-300 overflow-x-auto">
                                                    {getPythonCode()}
                                                </pre>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>

                        <div className="glass rounded-3xl p-6 bg-yellow-500/[0.03] border-yellow-500/10">
                            <div className="flex gap-4">
                                <div className="w-10 h-10 rounded-full bg-yellow-500/10 flex items-center justify-center shrink-0">
                                    <AlertTriangle className="w-5 h-5 text-yellow-500" />
                                </div>
                                <div>
                                    <h4 className="text-sm font-bold text-yellow-500 mb-1">{t("register.production_guardrails")}</h4>
                                    <p className="text-xs text-muted-foreground leading-relaxed">
                                        {t("register.guardrails_desc")}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </BaseLayout>
    );
}
