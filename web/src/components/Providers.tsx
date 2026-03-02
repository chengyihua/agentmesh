"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { LanguageProvider } from "@/contexts/LanguageContext";
import { AuthProvider } from "@/contexts/AuthContext";

export function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                staleTime: 5000,
                refetchInterval: 10000, // Auto refetch for health monitoring
            },
        },
    }));

    return (
        <QueryClientProvider client={queryClient}>
            <LanguageProvider>
                <AuthProvider>
                    <div className="dark">
                        {children}
                    </div>
                </AuthProvider>
            </LanguageProvider>
        </QueryClientProvider>
    );
}
