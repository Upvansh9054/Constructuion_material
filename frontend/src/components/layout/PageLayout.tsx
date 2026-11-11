import React from 'react';
import { Navbar } from './Navbar';
import { Sidebar, NavTab } from './Sidebar';

interface PageLayoutProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  children: React.ReactNode;
}

export const PageLayout: React.FC<PageLayoutProps> = ({ activeTab, onSelectTab, children }) => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar activeTab={activeTab} onSelectTab={onSelectTab} />
        <main className="flex-1 overflow-y-auto p-6 lg:p-8 bg-slate-950/90">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
};

