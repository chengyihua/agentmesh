"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, Globe, Loader2 } from "lucide-react";
import { useAgents } from "@/hooks/useRegistry";
import { useRouter } from "next/navigation";

export function CommandSearch() {
    const [isOpen, setIsOpen] = useState(false);
    const [search, setSearch] = useState("");
    const { data: agents, isLoading } = useAgents();
    const router = useRouter();

    const toggle = useCallback(() => setIsOpen((prev) => !prev), []);

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                toggle();
            }
            if (e.key === "Escape") {
                setIsOpen(false);
            }
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    }, [toggle]);

    const filteredAgents = search.trim() === ""
        ? []
        : agents?.filter((a) =>
            a.name.toLowerCase().includes(search.toLowerCase()) ||
            a.id.toLowerCase().includes(search.toLowerCase()) ||
            a.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()))
        ).slice(0, 5) || [];

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] px-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-background/60 backdrop-blur-sm animate-in fade-in duration-200"
                onClick={() => setIsOpen(false)}
            />

            {/* Modal */}
            <div className="relative w-full max-w-2xl glass rounded-2xl shadow-2xl border-white/10 flex flex-col overflow-hidden animate-in zoom-in-95 duration-200 origin-top">
                <div className="flex items-center px-6 py-4 border-b border-white/5 bg-white/[0.02]">
                    <Search className="w-5 h-5 text-muted-foreground mr-3" />
                    <input
                        type="text"
                        placeholder="Search agents, skills, or tags..."
                        autoFocus
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder:text-muted-foreground text-base"
                    />
                    <div className="flex items-center gap-1.5 px-1.5 py-0.5 rounded border border-white/10 text-[10px] text-muted-foreground font-mono">
                        <kbd>ESC</kbd>
                    </div>
                </div>

                <div className="max-h-[400px] overflow-y-auto p-2">
                    {search === "" ? (
                        <div className="p-8 text-center text-muted-foreground">
                            <p className="text-sm">Type to search for agents in the mesh...</p>
                        </div>
                    ) : isLoading ? (
                        <div className="p-8 flex items-center justify-center gap-2 text-muted-foreground">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <p className="text-sm text-white/50">Searching registry...</p>
                        </div>
                    ) : filteredAgents.length === 0 ? (
                        <div className="p-8 text-center text-muted-foreground">
                            <p className="text-sm">No results found for &quot;{search}&quot;</p>
                        </div>
                    ) : (
                        <div className="space-y-1">
                            <p className="px-4 py-2 text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Matching Agents</p>
                            {filteredAgents.map((agent) => (
                                <button
                                    key={agent.id}
                                    onClick={() => {
                                        router.push(`/agents/${agent.id}`);
                                        setIsOpen(false);
                                        setSearch("");
                                    }}
                                    className="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors group text-left"
                                >
                                    <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                                        <Globe className="w-5 h-5 text-primary" />
                                    </div>
                                    <div className="flex-1 overflow-hidden">
                                        <div className="flex items-center justify-between">
                                            <h4 className="font-bold text-white group-hover:text-primary transition-colors truncate">{agent.name}</h4>
                                            <span className="text-[10px] font-mono text-muted-foreground">v{agent.version}</span>
                                        </div>
                                        <p className="text-xs text-muted-foreground truncate">{agent.description}</p>
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                <div className="p-3 border-t border-white/5 bg-white/[0.01] flex items-center justify-between text-[10px] text-muted-foreground font-medium">
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1"><span className="p-0.5 rounded border border-white/10">⏎</span> Select</span>
                        <span className="flex items-center gap-1"><span className="p-0.5 rounded border border-white/10">↑↓</span> Navigate</span>
                    </div>
                    <p>Powered by AgentMesh Registry</p>
                </div>
            </div>
        </div>
    );
}
