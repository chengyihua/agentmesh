"use client";

import { useState } from "react";
import { useInvoke } from "@/hooks/useRegistry";
import { Play, Loader2, AlertCircle, CheckCircle2, Code, Key, Terminal, Wand2, Braces } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLanguage } from "@/contexts/LanguageContext";
import { Skill, ApiError } from "@/types/agent";

interface InvocationPlaygroundProps {
    agentId: string;
    skills: Skill[];
}

export function InvocationPlayground({ agentId, skills }: InvocationPlaygroundProps) {
    const { t } = useLanguage();
    const invokeMutation = useInvoke();
    const [selectedSkill, setSelectedSkill] = useState<string>(skills[0]?.name || "");
    
    // Generate initial payload based on skill
    const generateTemplate = (skillName: string) => {
        const skill = skills.find(s => s.name === skillName);
        if (!skill) return "{}";
        
        if (skill.schema) {
            // Simple schema to JSON generator
            try {
                const schema = skill.schema as Record<string, any>;
                const template: Record<string, any> = {};
                
                if (schema.properties) {
                    Object.keys(schema.properties).forEach(key => {
                        const prop = schema.properties[key];
                        // Improved default value logic
                        if (prop.default !== undefined) template[key] = prop.default;
                        else if (prop.example !== undefined) template[key] = prop.example;
                        else if (prop.type === 'number' || prop.type === 'integer') template[key] = 0;
                        else if (prop.type === 'boolean') template[key] = false;
                        else if (prop.type === 'array') template[key] = [];
                        else if (prop.type === 'object') template[key] = {};
                        else template[key] = "value";
                    });
                }
                return JSON.stringify(template, null, 2);
            } catch {
                return "{}";
            }
        }
        
        // Manual templates for known demo skills
        const lowerName = skillName.toLowerCase();
        
        if (lowerName.includes('forecast') || lowerName.includes('weather')) {
            return JSON.stringify({
                location: "San Francisco, CA",
                days: 3,
                unit: "celsius"
            }, null, 2);
        }
        
        if (lowerName.includes('price') || lowerName.includes('crypto')) {
            return JSON.stringify({
                symbol: "BTC-USD",
                exchange: "Binance"
            }, null, 2);
        }
        
        if (lowerName.includes('sentiment')) {
            return JSON.stringify({
                symbol: "ETH-USD",
                include_social: true
            }, null, 2);
        }

        if (lowerName.includes('review') || lowerName.includes('pr')) {
            return JSON.stringify({
                repo_url: "https://github.com/agentmesh/core",
                pr_number: 42,
                branch: "main"
            }, null, 2);
        }

        if (lowerName.includes('lint') || lowerName.includes('fix')) {
            return JSON.stringify({
                files: ["src/main.py", "src/utils.py"],
                auto_commit: false
            }, null, 2);
        }
        
        if (lowerName.includes('flight') || lowerName.includes('travel')) {
            return JSON.stringify({
                origin: "JFK",
                destination: "LHR",
                date: "2024-12-25",
                passengers: 1
            }, null, 2);
        }

        if (lowerName.includes('summarize') || lowerName.includes('legal')) {
            return JSON.stringify({
                text: "This Agreement is made on [Date] between [Party A] and [Party B]...",
                max_length: 200,
                format: "bullet_points"
            }, null, 2);
        }
        
        if (lowerName.includes('search')) {
            return JSON.stringify({
                query: "latest AI agent protocols",
                limit: 5
            }, null, 2);
        }
        
        if (lowerName.includes('calc')) {
            return JSON.stringify({
                expression: "2 * (5 + 10) / 3"
            }, null, 2);
        }

        if (lowerName.includes('heartrate') || lowerName.includes('health')) {
            return JSON.stringify({
                user_id: "user_123",
                date: "today"
            }, null, 2);
        }
        
        // Default generic template (valid JSON)
        return JSON.stringify({
            param: "value"
        }, null, 2);
    };

    const [payload, setPayload] = useState<string>(generateTemplate(skills[0]?.name || ""));
    const [apiKey, setApiKey] = useState<string>("");

    const handleSkillChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newSkill = e.target.value;
        setSelectedSkill(newSkill);
        setPayload(generateTemplate(newSkill));
    };

    const [result, setResult] = useState<unknown>(null);
    const [error, setError] = useState<string | null>(null);

    const handleInvoke = async () => {
        setError(null);
        setResult(null);

        try {
            const parsedPayload = JSON.parse(payload);
            const response = await invokeMutation.mutateAsync({
                agentId,
                body: {
                    skill: selectedSkill || undefined,
                    payload: parsedPayload,
                    timeout_seconds: 30
                },
                apiKey: apiKey || undefined
            });
            setResult(response);
        } catch (err: unknown) {
            const e = err as ApiError;
            console.error("Invocation failed:", e);
            setError(e.response?.data?.detail?.reason || e.response?.data?.error?.message || e.message || "Invocation failed");
        }
    };

    return (
        <div className="mb-12">
             <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-6 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-primary" />
                {t("playground.title")}
            </h3>
            
            <div className="glass rounded-3xl overflow-hidden border border-white/5">
                <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-white/5">
                    {/* Left: Input */}
                    <div className="p-6 space-y-6 bg-black/20">
                        <div className="space-y-4">
                            <div>
                                <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2 block">{t("playground.select_skill")}</label>
                                <select 
                                    value={selectedSkill}
                                    onChange={handleSkillChange}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary/50 transition-colors"
                                >
                                    <option value="">{t("playground.raw_invocation")}</option>
                                    {skills.map(s => (
                                        <option key={s.name} value={s.name}>{s.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider block">{t("playground.payload_label")}</label>
                                    <div className="flex items-center gap-3">
                                        <button 
                                            onClick={() => {
                                                try {
                                                    setPayload(JSON.stringify(JSON.parse(payload), null, 2));
                                                } catch {
                                                    // ignore invalid json
                                                }
                                            }}
                                            className="text-[10px] text-white/50 hover:text-white transition-colors flex items-center gap-1"
                                            title="Format JSON"
                                        >
                                            <Braces className="w-3 h-3" /> Format
                                        </button>
                                        <button 
                                            onClick={() => setPayload(generateTemplate(selectedSkill))}
                                            className="text-[10px] text-primary hover:text-primary/80 transition-colors flex items-center gap-1"
                                            title="Reset to template"
                                        >
                                            <Wand2 className="w-3 h-3" /> Auto-Fill
                                        </button>
                                    </div>
                                </div>
                                <div className="relative">
                                    <textarea
                                        value={payload}
                                        onChange={(e) => setPayload(e.target.value)}
                                        className="w-full h-48 bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-primary/50 transition-colors resize-none"
                                        placeholder="{}"
                                    />
                                </div>
                                <p className="text-[10px] text-muted-foreground mt-2">
                                    {t("playground.payload_hint") || "Tip: Modify the values in the JSON above to customize your request."}
                                </p>
                            </div>

                            <div>
                                <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2 block flex items-center gap-2">
                                    <Key className="w-3 h-3" /> {t("playground.api_key_label")}
                                </label>
                                <input
                                    type="password"
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary/50 transition-colors"
                                    placeholder="sk-..."
                                />
                            </div>
                        </div>

                        <button
                            onClick={handleInvoke}
                            disabled={invokeMutation.isPending}
                            className={cn(
                                "w-full py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all",
                                invokeMutation.isPending 
                                    ? "bg-white/5 text-muted-foreground cursor-not-allowed"
                                    : "bg-primary text-black hover:bg-primary/90 shadow-lg shadow-primary/20"
                            )}
                        >
                            {invokeMutation.isPending ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    {t("playground.running_btn")}
                                </>
                            ) : (
                                <>
                                    <Play className="w-4 h-4 fill-current" />
                                    {t("playground.run_btn")}
                                </>
                            )}
                        </button>
                    </div>

                    {/* Right: Output */}
                    <div className="p-6 bg-black/40 flex flex-col min-h-[400px]">
                        <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 block flex items-center gap-2">
                            <Code className="w-3 h-3" /> {t("playground.response_label")}
                        </label>
                        
                        <div className="flex-1 rounded-xl bg-black/60 border border-white/5 p-4 overflow-auto relative group">
                            {error ? (
                                <div className="text-destructive flex items-start gap-2">
                                    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                                    <div className="space-y-1">
                                        <p className="font-bold text-sm">{t("playground.failed_title")}</p>
                                        <p className="text-xs font-mono whitespace-pre-wrap break-all">{error}</p>
                                    </div>
                                </div>
                            ) : result ? (
                                <div className="text-emerald-400 space-y-2">
                                    <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider mb-2 text-emerald-500">
                                        <CheckCircle2 className="w-3 h-3" /> {t("playground.success_title")}
                                    </div>
                                    <pre className="text-xs font-mono whitespace-pre-wrap break-all">
                                        {JSON.stringify(result, null, 2)}
                                    </pre>
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-muted-foreground/30 space-y-4">
                                    <Terminal className="w-12 h-12" />
                                    <p className="text-sm">{t("playground.ready_msg")}</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
