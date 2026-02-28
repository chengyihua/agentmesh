import { getNavigation } from '@/lib/docs';
import { DocsSidebar } from '@/components/DocsSidebar';
import { Navigation } from '@/components/Navigation';

export default function GuideLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const nav = getNavigation();

  return (
    <div className="flex flex-col min-h-screen bg-black text-white">
      <Navigation />
      <div className="flex flex-1 relative container mx-auto px-4">
        <DocsSidebar nav={nav} />
        <main className="flex-1 w-full min-w-0 max-w-4xl mx-auto p-6 md:p-12 lg:p-16 overflow-x-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
