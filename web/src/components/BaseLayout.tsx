import { Navigation } from "./Navigation";

export function BaseLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="flex flex-col min-h-screen">
            <Navigation />
            <main className="flex-1 flex flex-col">
                {children}
            </main>
            <footer className="border-t border-white/5 py-12 bg-background">
                <div className="container mx-auto px-4 text-center">
                    <p className="text-sm text-muted-foreground">
                        &copy; {new Date().getFullYear()} AgentMesh Team. Open-source under Apache-2.0.
                    </p>
                </div>
            </footer>
        </div>
    );
}
