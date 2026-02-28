import { redirect } from 'next/navigation';
import { getNavigation } from '@/lib/docs';

export default function GuidePage() {
  const nav = getNavigation();
  
  // Find the first available link
  for (const category of nav) {
    if (category.items.length > 0) {
      redirect(category.items[0].href);
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center text-white">
      <h1 className="text-3xl font-bold mb-4">Documentation Center</h1>
      <p className="text-gray-400 mb-8">Welcome to the AgentMesh documentation.</p>
      <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-yellow-200">
        No documentation files found. Please check the <code>web/docs</code> directory.
      </div>
    </div>
  );
}
