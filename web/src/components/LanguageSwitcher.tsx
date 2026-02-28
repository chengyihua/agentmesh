"use client";

import { useLanguage } from "@/contexts/LanguageContext";
import { Globe } from "lucide-react";

export function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();

  return (
    <button
      onClick={() => setLanguage(language === "en" ? "zh" : "en")}
      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-white bg-white/5 border border-white/10 rounded-md transition-colors"
    >
      <Globe className="w-3 h-3" />
      {language === "en" ? "中" : "EN"}
    </button>
  );
}
