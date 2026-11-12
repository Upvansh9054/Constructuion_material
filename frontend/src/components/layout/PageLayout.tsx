import React from 'react';
import { Navbar } from './Navbar';
import { Sidebar, NavScreenId } from './Sidebar';

interface PageLayoutProps {
  activeScreen: NavScreenId;
  onSelectScreen: (screen: NavScreenId) => void;
  unreadCount?: number;
  user: { email: string; role: string; name: string };
  onLogout?: () => void;
  onSwitchRole?: (role: 'SURVEYOR' | 'CONTRACTOR' | 'BUYER') => void;
  children: React.ReactNode;
}

export const PageLayout: React.FC<PageLayoutProps> = ({
  activeScreen,
  onSelectScreen,
  unreadCount = 2,
  user,
  onLogout,
  onSwitchRole,
  children,
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500 selection:text-white">
      <Navbar
        onNavigateToScreen={onSelectScreen}
        unreadCount={unreadCount}
        user={user}
        onSwitchRole={onSwitchRole}
      />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          activeScreen={activeScreen}
          onSelectScreen={onSelectScreen}
          unreadCount={unreadCount}
          userRole={user.role}
          onLogout={onLogout}
        />
        <main className="flex-1 overflow-y-auto p-6 lg:p-8 bg-slate-950/90 scrollbar-thin scrollbar-thumb-slate-800">
          <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
