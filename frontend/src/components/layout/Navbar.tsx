import React from 'react';
import { ShieldCheck, Bell, User, Camera, HardHat, Building } from 'lucide-react';
import { NavScreenId } from './Sidebar';

interface NavbarProps {
  onNavigateToScreen: (screen: NavScreenId) => void;
  unreadCount?: number;
  user: { email: string; role: string; name: string };
  onSwitchRole?: (role: 'SURVEYOR' | 'CONTRACTOR' | 'BUYER') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onNavigateToScreen,
  unreadCount = 2,
  user,
  onSwitchRole,
}) => {
  const isBuyer = user.role === 'BUYER' || user.role === 'MATERIAL_BUYER';
  const isSurveyor = user.role === 'SURVEYOR';
  const isContractor = !isBuyer && !isSurveyor;

  const handleBrandClick = () => {
    if (isBuyer) {
      onNavigateToScreen('marketplace');
    } else if (isSurveyor) {
      onNavigateToScreen('upload');
    } else {
      onNavigateToScreen('dashboard');
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-40 gap-4">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleBrandClick}
          className="flex items-center gap-3 text-left focus:outline-none group"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-emerald-400 flex items-center justify-center shadow-lg shadow-emerald-900/40 text-slate-950 group-hover:scale-105 transition-transform">
            <ShieldCheck className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight leading-none group-hover:text-emerald-300 transition-colors">
              Demolition Intelligence
            </h1>
            <p className="text-[11px] text-slate-400 mt-0.5">Material Recovery & Circular Economy</p>
          </div>
        </button>
      </div>

      {/* Middle: 3-Stage Persona Switcher (Live Demo / Presentation Bar) */}
      <div className="hidden md:flex items-center gap-1.5 p-1 rounded-xl bg-slate-950/80 border border-slate-800">
        <span className="text-[10px] uppercase font-bold text-slate-500 px-2 tracking-wider">
          Workflow Persona:
        </span>
        <button
          type="button"
          onClick={() => onSwitchRole?.('SURVEYOR')}
          className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
            isSurveyor
              ? 'bg-emerald-600 text-white shadow-md shadow-emerald-950'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
          title="Step 1: Drone Upload & AI Material Localization"
        >
          <Camera className="w-3.5 h-3.5" />
          <span>1. Surveyor</span>
        </button>

        <button
          type="button"
          onClick={() => onSwitchRole?.('CONTRACTOR')}
          className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
            isContractor
              ? 'bg-emerald-600 text-white shadow-md shadow-emerald-950'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
          title="Step 2: Operations, Weighbridge Scaling & DMAR Reports"
        >
          <HardHat className="w-3.5 h-3.5" />
          <span>2. Contractor</span>
        </button>

        <button
          type="button"
          onClick={() => onSwitchRole?.('BUYER')}
          className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
            isBuyer
              ? 'bg-emerald-600 text-white shadow-md shadow-emerald-950'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
          title="Step 3: Secondary Material Procurement & Off-Taker Bidding"
        >
          <Building className="w-3.5 h-3.5" />
          <span>3. Buyer</span>
        </button>
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
