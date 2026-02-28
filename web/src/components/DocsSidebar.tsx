'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Menu, X, ChevronDown, ChevronRight } from 'lucide-react';
import { NavCategory } from '@/lib/docs';

interface DocsSidebarProps {
  nav: NavCategory[];
}

export function DocsSidebar({ nav }: DocsSidebarProps) {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>(
    nav.reduce((acc, cat) => ({ ...acc, [cat.title]: true }), {})
  );

  const toggleCategory = (title: string) => {
    setExpandedCategories(prev => ({
      ...prev,
      [title]: !prev[title]
    }));
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden fixed top-20 right-4 z-50 p-2 bg-zinc-900 border border-white/10 rounded-lg text-white"
      >
        {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Sidebar Container */}
      <aside
        className={cn(
          "fixed md:sticky top-[3.5rem] h-[calc(100vh-3.5rem)] w-64 border-r border-white/10 overflow-y-auto transition-transform duration-300 z-40 bg-black md:bg-transparent",
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        <div className="py-6 pr-6 space-y-6">
          {nav.map((category) => (
            <div key={category.title} className="space-y-2">
              <button
                onClick={() => toggleCategory(category.title)}
                className="flex items-center justify-between w-full text-sm font-bold text-white/90 hover:text-white group"
              >
                <span>{category.title}</span>
                {expandedCategories[category.title] ? (
                  <ChevronDown className="w-4 h-4 text-white/50 group-hover:text-white transition-colors" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-white/50 group-hover:text-white transition-colors" />
                )}
              </button>
              
              {expandedCategories[category.title] && (
                <div className="space-y-1 ml-2 border-l border-white/10 pl-2">
                  {category.items.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setIsOpen(false)}
                        className={cn(
                          "block px-3 py-1.5 text-sm rounded-md transition-colors",
                          isActive
                            ? "text-blue-400 bg-blue-500/10 font-medium"
                            : "text-muted-foreground hover:text-white hover:bg-white/5"
                        )}
                      >
                        {item.title}
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      </aside>
    </>
  );
}
