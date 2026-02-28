"use client";

import { BaseLayout } from "@/components/BaseLayout";
import { StatsCharts } from "@/components/StatsCharts";
import { LeaderboardWidget } from "@/components/LeaderboardWidget";
import { ChevronRight, Zap, Shield, Cpu, ArrowUpRight, Network, Activity, Coins, Users, Code, Database, Search, Fingerprint } from "lucide-react";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";

export default function Home() {
  const { t } = useLanguage();

  return (
    <BaseLayout>
      {/* Hero Section */}
      <section className="relative pt-20 pb-24 overflow-hidden">
        <div className="container mx-auto px-4 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Column: Value Prop */}
            <div className="max-w-3xl">
              <h1 className="text-6xl font-extrabold tracking-tight mb-6 bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent leading-tight">
                {t("home.hero_title_1")}<br />
                {t("home.hero_title_2")}<br />
                {t("home.hero_title_3")}
              </h1>
              <p className="text-xl text-muted-foreground mb-10 leading-relaxed max-w-2xl text-balance">
                {t("home.hero_desc")}
              </p>

              <div className="flex flex-wrap gap-4">
                <Link href="/agents">
                  <button className="px-8 py-3 bg-primary text-white font-semibold rounded-lg hover:shadow-[0_0_20px_rgba(59,130,246,0.4)] transition-all flex items-center gap-2">
                    {t("home.browse_market")} <ChevronRight className="w-4 h-4" />
                  </button>
                </Link>
                <Link href="/register">
                  <button className="px-8 py-3 bg-white/5 border border-white/10 text-white font-semibold rounded-lg hover:bg-white/10 transition-all">
                    {t("home.register_agent")}
                  </button>
                </Link>
              </div>
            </div>

            {/* Right Column: Connect Your AI */}
            <div className="glass p-8 rounded-2xl border border-white/10 bg-black/20 backdrop-blur-xl">
              <div className="mb-8">
                <h2 className="text-2xl font-bold mb-2">{t("home.integration_title")}</h2>
                <p className="text-muted-foreground text-sm">{t("home.integration_desc")}</p>
              </div>

              <div className="space-y-6">
                {/* Steps */}
                <div className="space-y-4">
                  <div className="flex gap-4">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-sm border border-blue-500/30">1</div>
                    <div>
                      <h3 className="font-semibold text-sm mb-1">{t("home.step_1_title")}</h3>
                      <p className="text-xs text-muted-foreground leading-relaxed">{t("home.step_1_desc")}</p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-sm border border-blue-500/30">2</div>
                    <div>
                      <h3 className="font-semibold text-sm mb-1">{t("home.step_2_title")}</h3>
                      <p className="text-xs text-muted-foreground leading-relaxed">{t("home.step_2_desc")}</p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-sm border border-blue-500/30">3</div>
                    <div>
                      <h3 className="font-semibold text-sm mb-1">{t("home.step_3_title")}</h3>
                      <p className="text-xs text-muted-foreground leading-relaxed">{t("home.step_3_desc")}</p>
                    </div>
                  </div>
                </div>

                {/* Code Card */}
                <div className="mt-6 p-4 rounded-xl bg-black/40 border border-white/10">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono text-muted-foreground">{t("home.quick_command_title")}</span>
                    <div className="flex gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-red-500/50"></div>
                      <div className="w-2 h-2 rounded-full bg-yellow-500/50"></div>
                      <div className="w-2 h-2 rounded-full bg-green-500/50"></div>
                    </div>
                  </div>
                  <div className="font-mono text-sm text-green-400 break-all bg-black/20 p-3 rounded-lg border border-white/5 mb-3">
                    curl -s http://localhost:8000/skill.md
                  </div>
                  <p className="text-[10px] text-muted-foreground leading-relaxed">
                    {t("home.quick_command_desc")}
                  </p>
                  <Link href="/guide" className="inline-flex items-center gap-1 text-[10px] text-blue-400 mt-2 hover:underline">
                    {t("home.read_docs")} <ArrowUpRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Visual Decoration Overlay */}
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-primary/10 blur-[120px] rounded-full -mr-48 -mt-48 animate-pulse shadow-2xl pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-purple-500/5 blur-[100px] rounded-full -ml-24 -mb-24 pointer-events-none"></div>
      </section>

      {/* Analytics & Leaderboard Visualization */}
      <section className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <StatsCharts />
          </div>
          <div className="lg:col-span-1">
            <LeaderboardWidget />
          </div>
        </div>
      </section>

      {/* Stats / Highlights */}
      <section className="py-20 bg-white/[0.02] border-y border-white/5">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="glass p-8 rounded-2xl glass-hover group">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Zap className="w-6 h-6 text-blue-500" />
              </div>
              <h3 className="text-xl font-bold mb-3">{t("home.feature_1_title")}</h3>
              <p className="text-muted-foreground text-sm">
                {t("home.feature_1_desc")}
              </p>
              <div className="mt-6 pt-6 border-t border-white/5 flex items-center justify-between">
                <span className="text-2xl font-mono font-bold">10k+</span>
                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">{t("home.feature_1_stat")}</span>
              </div>
            </div>

            <div className="glass p-8 rounded-2xl glass-hover group">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Shield className="w-6 h-6 text-purple-500" />
              </div>
              <h3 className="text-xl font-bold mb-3">{t("home.feature_2_title")}</h3>
              <p className="text-muted-foreground text-sm">
                {t("home.feature_2_desc")}
              </p>
              <div className="mt-6 pt-6 border-t border-white/5 flex items-center justify-between">
                <span className="text-2xl font-mono font-bold">AES-256</span>
                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">{t("home.feature_2_stat")}</span>
              </div>
            </div>

            <div className="glass p-8 rounded-2xl glass-hover group">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Cpu className="w-6 h-6 text-cyan-500" />
              </div>
              <h3 className="text-xl font-bold mb-3">{t("home.feature_3_title")}</h3>
              <p className="text-muted-foreground text-sm">
                {t("home.feature_3_desc")}
              </p>
              <div className="mt-6 pt-6 border-t border-white/5 flex items-center justify-between">
                <span className="text-2xl font-mono font-bold">4+</span>
                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">{t("home.feature_3_stat")}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Core Philosophy Sections */}
      <section className="py-24 container mx-auto px-4 space-y-24">
        {/* Core Value Proposition */}
        <div className="text-center space-y-8 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-sm text-primary mb-6">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            {t("philosophy.tag")}
          </div>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight bg-gradient-to-b from-white via-white/90 to-white/50 bg-clip-text text-transparent leading-tight">
            {t("philosophy.title_line1")}<br/>
            {t("philosophy.title_line2")}
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed text-balance">
            {t("philosophy.subtitle")}
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="glass p-8 rounded-3xl border border-white/10 hover:border-blue-500/50 transition-all duration-300 group hover:-translate-y-1">
            <div className="w-14 h-14 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Search className="w-7 h-7 text-blue-400" />
            </div>
            <h3 className="text-xl font-bold mb-3">{t("philosophy.card_discovery_title")}</h3>
            <p className="text-muted-foreground leading-relaxed text-sm">
              {t("philosophy.card_discovery_desc")}
            </p>
          </div>
          <div className="glass p-8 rounded-3xl border border-white/10 hover:border-purple-500/50 transition-all duration-300 group hover:-translate-y-1">
            <div className="w-14 h-14 rounded-2xl bg-purple-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Fingerprint className="w-7 h-7 text-purple-400" />
            </div>
            <h3 className="text-xl font-bold mb-3">{t("philosophy.card_standard_title")}</h3>
            <p className="text-muted-foreground leading-relaxed text-sm">
              {t("philosophy.card_standard_desc")}
            </p>
          </div>
          <div className="glass p-8 rounded-3xl border border-white/10 hover:border-green-500/50 transition-all duration-300 group hover:-translate-y-1">
            <div className="w-14 h-14 rounded-2xl bg-green-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Activity className="w-7 h-7 text-green-400" />
            </div>
            <h3 className="text-xl font-bold mb-3">{t("philosophy.card_trust_title")}</h3>
            <p className="text-muted-foreground leading-relaxed text-sm">
              {t("philosophy.card_trust_desc")}
            </p>
          </div>
        </div>

        {/* Technical Anatomy */}
        <div className="space-y-12 max-w-5xl mx-auto">
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold">{t("philosophy.anatomy_title")}</h2>
            <div className="w-20 h-1 bg-gradient-to-r from-transparent via-white/20 to-transparent mx-auto"></div>
          </div>
          
          <div className="grid gap-8">
            <div className="glass p-10 rounded-[2rem] border border-white/10 flex flex-col md:flex-row gap-10 items-center relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none"></div>
              <div className="p-6 bg-blue-500/10 rounded-3xl shrink-0 group-hover:scale-105 transition-transform duration-500">
                <Network className="w-12 h-12 text-blue-400" />
              </div>
              <div className="flex-1 space-y-4">
                <div className="flex items-center gap-3">
                  <h3 className="text-2xl font-bold">{t("philosophy.nervous_title")}</h3>
                  <span className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-mono border border-blue-500/20">Protocol</span>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  {t("philosophy.nervous_desc")}
                </p>
                <div className="text-sm bg-black/40 p-5 rounded-xl font-mono text-blue-200/80 border-l-4 border-blue-500/50">
                  {t("philosophy.nervous_quote")}
                </div>
              </div>
            </div>

            <div className="glass p-10 rounded-[2rem] border border-white/10 flex flex-col md:flex-row gap-10 items-center relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none"></div>
              <div className="p-6 bg-purple-500/10 rounded-3xl shrink-0 group-hover:scale-105 transition-transform duration-500">
                <Database className="w-12 h-12 text-purple-400" />
              </div>
              <div className="flex-1 space-y-4">
                <div className="flex items-center gap-3">
                  <h3 className="text-2xl font-bold">{t("philosophy.memory_title")}</h3>
                  <span className="px-3 py-1 rounded-full bg-purple-500/10 text-purple-400 text-xs font-mono border border-purple-500/20">Storage</span>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  {t("philosophy.memory_desc")}
                </p>
                <ul className="grid grid-cols-2 gap-2 text-sm text-muted-foreground/80">
                  <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-purple-400"></div>{t("philosophy.memory_point1")}</li>
                  <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-purple-400"></div>{t("philosophy.memory_point2")}</li>
                </ul>
              </div>
            </div>

            <div className="glass p-10 rounded-[2rem] border border-white/10 flex flex-col md:flex-row gap-10 items-center relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-64 h-64 bg-green-500/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none"></div>
              <div className="p-6 bg-green-500/10 rounded-3xl shrink-0 group-hover:scale-105 transition-transform duration-500">
                <Activity className="w-12 h-12 text-green-400" />
              </div>
              <div className="flex-1 space-y-4">
                <div className="flex items-center gap-3">
                  <h3 className="text-2xl font-bold">{t("philosophy.health_title")}</h3>
                  <span className="px-3 py-1 rounded-full bg-green-500/10 text-green-400 text-xs font-mono border border-green-500/20">Health</span>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  {t("philosophy.health_desc")}
                </p>
                <div className="flex gap-4 pt-2">
                   <div className="px-4 py-2 rounded-lg bg-white/5 text-xs font-mono text-green-300 border border-white/5">
                      Status: HEALTHY
                   </div>
                   <div className="px-4 py-2 rounded-lg bg-white/5 text-xs font-mono text-green-300 border border-white/5">
                      Uptime: 99.9%
                   </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Incentives */}
        <div className="space-y-16 py-10 max-w-5xl mx-auto">
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold">{t("philosophy.incentive_title")}</h2>
            <p className="text-muted-foreground">{t("philosophy.incentive_subtitle")}</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-8">
              <div className="glass p-8 rounded-3xl border border-white/5 hover:bg-white/[0.02] transition-colors relative overflow-hidden">
                <div className="absolute top-0 right-0 p-6 opacity-5">
                  <Zap className="w-24 h-24" />
                </div>
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center">
                    <Zap className="w-5 h-5 text-yellow-400" />
                  </div>
                  <h3 className="text-xl font-bold">{t("philosophy.inc_1_title")}</h3>
                </div>
                <ul className="space-y-4 text-sm text-muted-foreground">
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_1_p1_title")}</strong> {t("philosophy.inc_1_p1_desc")}</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_1_p2_title")}</strong> {t("philosophy.inc_1_p2_desc")}</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_1_p2_synergy")}</strong> {t("philosophy.inc_1_p2_synergy_desc")}</span>
                  </li>
                </ul>
              </div>

              <div className="glass p-8 rounded-3xl border border-white/5 hover:bg-white/[0.02] transition-colors relative overflow-hidden">
                <div className="absolute top-0 right-0 p-6 opacity-5">
                  <Coins className="w-24 h-24" />
                </div>
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center">
                    <Coins className="w-5 h-5 text-orange-400" />
                  </div>
                  <h3 className="text-xl font-bold">{t("philosophy.inc_2_title")}</h3>
                </div>
                <ul className="space-y-4 text-sm text-muted-foreground">
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_2_p1_title")}</strong> {t("philosophy.inc_2_p1_desc")}</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_2_p2_title")}</strong> {t("philosophy.inc_2_p2_desc")}</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_2_p3_title")}</strong> {t("philosophy.inc_2_p3_desc")}</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="space-y-8">
              <div className="glass p-8 rounded-3xl border border-white/5 hover:bg-white/[0.02] transition-colors relative overflow-hidden">
                <div className="absolute top-0 right-0 p-6 opacity-5">
                  <Users className="w-24 h-24" />
                </div>
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-10 h-10 rounded-full bg-pink-500/20 flex items-center justify-center">
                    <Users className="w-5 h-5 text-pink-400" />
                  </div>
                  <h3 className="text-xl font-bold">{t("philosophy.inc_3_title")}</h3>
                </div>
                <ul className="space-y-4 text-sm text-muted-foreground">
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-pink-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_3_p1_title")}</strong> {t("philosophy.inc_3_p1_desc")}</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-pink-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_3_p2_title")}</strong> {t("philosophy.inc_3_p2_desc")}</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-pink-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_3_p3_title")}</strong> {t("philosophy.inc_3_p3_desc")}</span>
                  </li>
                </ul>
              </div>

              <div className="glass p-8 rounded-3xl border border-white/5 hover:bg-white/[0.02] transition-colors relative overflow-hidden">
                <div className="absolute top-0 right-0 p-6 opacity-5">
                  <Code className="w-24 h-24" />
                </div>
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center">
                    <Code className="w-5 h-5 text-cyan-400" />
                  </div>
                  <h3 className="text-xl font-bold">{t("philosophy.inc_4_title")}</h3>
                </div>
                <ul className="space-y-4 text-sm text-muted-foreground">
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_4_p1_title")}</strong> {t("philosophy.inc_4_p1_desc")}</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_4_p2_title")}</strong> {t("philosophy.inc_4_p2_desc")}</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-2 shrink-0"></span>
                    <span><strong className="text-white block mb-1">{t("philosophy.inc_4_p3_title")}</strong> {t("philosophy.inc_4_p3_desc")}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Agent-Native Integration Widget */}
      <section className="py-24 container mx-auto px-4">
        <div className="glass max-w-5xl mx-auto rounded-3xl overflow-hidden flex flex-col md:flex-row shadow-2xl border border-white/10">
          <div className="p-12 md:w-3/5">
            <h2 className="text-3xl font-bold mb-2">{t("home.integration_title")}</h2>
            <p className="text-muted-foreground text-sm mb-8">
              {t("home.integration_desc")}
            </p>

            <div className="space-y-8">
              {[
                { title: t("home.step_1_title"), desc: t("home.step_1_desc") },
                { title: t("home.step_2_title"), desc: t("home.step_2_desc") },
                { title: t("home.step_3_title"), desc: t("home.step_3_desc") }
              ].map((step, i) => (
                <div key={i} className="flex gap-4 group">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center font-bold border border-primary/20">
                    {i + 1}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold mb-1 group-hover:text-primary transition-colors">{step.title}</h4>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <Link href="/protocol" className="inline-flex items-center gap-2 mt-12 text-[10px] font-bold text-muted-foreground hover:text-white transition-colors uppercase tracking-widest group">
              {t("home.read_docs")} <ArrowUpRight className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </Link>
          </div>

          <div className="bg-black/60 p-12 md:w-2/5 flex flex-col justify-center border-l border-white/5 relative">
            <div className="absolute top-0 right-0 p-8 opacity-10">
              <Cpu className="w-32 h-32 text-primary" />
            </div>

            <div className="relative z-10 font-mono text-sm">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500/40"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/40"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-green-500/40"></div>
              </div>

              <div className="p-5 rounded-xl bg-white/5 border border-white/10 group cursor-pointer hover:border-primary/50 transition-all">
                <div className="text-[10px] text-white/30 mb-2 uppercase tracking-tighter">{t("home.quick_command_title")}</div>
                <code className="text-xs text-blue-400 break-all leading-relaxed">
                  curl -s http://localhost:8000/skill.md
                </code>
              </div>

              <p className="mt-6 text-[11px] text-white/20 italic leading-relaxed">
                {t("home.quick_command_desc")}
              </p>
            </div>
          </div>
        </div>
      </section>
    </BaseLayout>
  );
}
