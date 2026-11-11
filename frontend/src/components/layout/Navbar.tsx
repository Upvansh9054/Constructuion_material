import React from 'react';
import { ShieldCheck, Activity, Bell, User } from 'lucide-react';
import { NavScreenId } from './Sidebar';

interface NavbarProps {
  onNavigateToScreen: (screen: NavScreenId) => void;
  unreadCount?: number;
  user: { email: string; role: string; name: string };
}

export const Navbar: React.FC<NavbarProps> = ({
  onNavigateToScreen,
  unreadCount = 2,
  user,
}) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => onNavigateToScreen('dashboard')}
          className="flex items-center gap-3 text-left focus:outline-none"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-emerald-400 flex items-center justify-center shadow-lg shadow-emerald-900/40 text-slate-950">
            <ShieldCheck className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight leading-none">
              Demolition Intelligence
            </h1>
            <p className="text-[11px] text-slate-400 mt-0.5">Material Recovery & Circular Economy</p>
          </div>
        </button>
      </div>

      {/* Middle Search & Status */}
      <div className="hidden lg:flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
          <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span className="font-mono text-[11px]">YOLOv8x Inference Engine: Operational</span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Notifications Icon with Badge */}
        <button
          onClick={() => onNavigateToScreen('notifications')}
          className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          title="Regulatory & Hazard Alerts"
        >
          <Bell className="w-4 h-4" />
          {unreadCount > 0 && (
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500 animate-ping" />
          )}
          {unreadCount > 0 && (
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500" />
          )}
        </button>

        {/* User Profile Pill */}
        <button
          onClick={() => onNavigateToScreen('settings')}
          className="flex items-center gap-2.5 pl-3 py-1 pr-2 rounded-xl border border-slate-800 hover:border-slate-700 bg-slate-800/40 hover:bg-slate-800 transition-all text-left"
        >
          <div className="w-7 h-7 rounded-lg bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <User className="w-3.5 h-3.5" />
          </div>
          <div className="hidden sm:block">
            <div className="text-xs font-semibold text-slate-200 leading-none">{user.name}</div>
            <div className="text-[10px] text-emerald-400 mt-0.5 font-mono">{user.role}</div>
          </div>
        </button>
      </div>
    </header>
  );
};
