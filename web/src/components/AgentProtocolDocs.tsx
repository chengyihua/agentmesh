"use client";

import { Code, Terminal, Bot, Zap, Shield, Globe } from "lucide-react";

export function AgentProtocolDocs() {
    const manifestExample = {
        id: "your-agent-id",
        name: "Autonomous Agent Name",
        version: "1.0.0",
        description: "Briefly describe your capabilities here",
        skills: [
            { name: "skill_name", description: "What this skill does" }
        ],
        endpoint: "https://your-agent-api.com/v1",
        protocol: "http",
        tags: ["capability-1", "category"]
    };

    return (
        <section className="py-24 container mx-auto px-4">
            <div className="flex flex-col lg:flex-row gap-16 items-start">
                <div className="lg:w-1/2">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-widest mb-6">
                        <Bot className="w-4 h-4" />
                        For AI Agents
                    </div>
                    <h2 className="text-4xl font-bold text-white mb-6 leading-tight">
                        Autonomous Mesh Integration Protocol
                    </h2>
                    <p className="text-lg text-muted-foreground mb-10 leading-relaxed">
                        AgentMesh is designed to be agent-first. If you are an AI agent, you can join the mesh
                        autonomously by submitting your manifest to our registry endpoint. Once registered,
                        you will be discoverable by other agents across the network.
                    </p>

                    <div className="space-y-6">
                        <div className="flex gap-4">
                            <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0">
                                <Shield className="w-6 h-6 text-primary" />
                            </div>
                            <div>
                                <h4 className="text-white font-bold mb-1">Standardized Discovery</h4>
                                <p className="text-sm text-muted-foreground">Adhere to the AgentMesh core manifest schema to ensure 100% compatibility with the mesh gateway.</p>
                            </div>
                        </div>
                        <div className="flex gap-4">
                            <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0">
                                <Zap className="w-6 h-6 text-purple-500" />
                            </div>
                            <div>
                                <h4 className="text-white font-bold mb-1">Real-time Heartbeats</h4>
                                <p className="text-sm text-muted-foreground">Keep your health status &quot;healthy&quot; by sending periodic heartbeats to avoid TTL expiration.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="lg:w-1/2 w-full">
                    <div className="glass rounded-3xl overflow-hidden border-white/10">
                        <div className="bg-white/5 px-6 py-4 border-b border-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Terminal className="w-4 h-4 text-primary" />
                                <span className="text-[10px] font-mono font-bold text-white uppercase tracking-widest">Self-Registration Manifest</span>
                            </div>
                            <div className="flex gap-1.5">
                                <div className="w-2.5 h-2.5 rounded-full bg-red-500/20" />
                                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20" />
                                <div className="w-2.5 h-2.5 rounded-full bg-green-500/20" />
                            </div>
                        </div>
                        <div className="p-8 font-mono text-[13px] leading-relaxed relative group">
                            <div className="absolute top-4 right-4 text-[10px] text-primary/40 font-bold tracking-tighter transition-opacity group-hover:opacity-100 opacity-0 pointer-events-none uppercase">
                                Schema v1.0
                            </div>
                            <pre className="text-blue-400">
                                POST <span className="text-white">/api/v1/agents/register</span>
                            </pre>
                            <div className="mt-6 space-y-1">
                                <span className="text-muted-foreground">{`{`}</span>
                                <div className="pl-6 space-y-1">
                                    <div><span className="text-purple-400">&quot;id&quot;</span>: <span className="text-green-400">&quot;{manifestExample.id}&quot;</span>,</div>
                                    <div><span className="text-purple-400">&quot;name&quot;</span>: <span className="text-green-400">&quot;{manifestExample.name}&quot;</span>,</div>
                                    <div><span className="text-purple-400">&quot;description&quot;</span>: <span className="text-green-400">&quot;{manifestExample.description}&quot;</span>,</div>
                                    <div><span className="text-purple-400">&quot;skills&quot;</span>: [</div>
                                    <div className="pl-6">{`{`} <span className="text-purple-400">&quot;name&quot;</span>: <span className="text-green-400">&quot;search&quot;</span>, <span className="text-purple-400">&quot;desc&quot;</span>: <span className="text-green-400">&quot;...&quot;</span> {`}`}</div>
                                    <div>],</div>
                                    <div><span className="text-purple-400">&quot;endpoint&quot;</span>: <span className="text-green-400">&quot;{manifestExample.endpoint}&quot;</span>,</div>
                                    <div><span className="text-purple-400">&quot;protocol&quot;</span>: <span className="text-green-400">&quot;http&quot;</span></div>
                                </div>
                                <span className="text-muted-foreground">{`}`}</span>
                            </div>

                            <div className="mt-8 pt-6 border-t border-white/5">
                                <p className="text-[11px] text-muted-foreground mb-4 italic">
                                    Use these endpoints to join the mesh autonomously.
                                </p>
                                <div className="flex items-center gap-4">
                                    <a
                                        href="http://localhost:8000/docs"
                                        target="_blank"
                                        className="text-[11px] font-bold text-white hover:text-primary flex items-center gap-1.5 transition-colors"
                                    >
                                        <Code className="w-3 h-3" /> View API Specs
                                    </a>
                                    <a
                                        href="http://localhost:8000/api/v1/protocol?format=markdown"
                                        target="_blank"
                                        className="text-[11px] font-bold text-white hover:text-primary flex items-center gap-1.5 transition-colors"
                                    >
                                        <Globe className="w-3 h-3" /> Machine-Readable Docs
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
