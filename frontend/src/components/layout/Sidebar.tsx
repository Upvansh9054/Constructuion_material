import React from 'react';
import { LayoutDashboard, MapPin, Camera, Layers, ShoppingBag, FileText, Settings } from 'lucide-react';
import { cn } from '../../lib/utils';

export type NavTab = 'dashboard' | 'sites' | 'surveys' | 'materials' | 'marketplace' | 'reports';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'sites', label: 'Demolition Sites', icon: MapPin },
    { id: 'surveys', label: 'Surveys & Evidence', icon: Camera },
    { id: 'materials', label: 'Material Inventory', icon: Layers },
    { id: 'marketplace', label: 'Recovery Market', icon: ShoppingBag },
    { id: 'reports', label: 'Audit Reports (DMAR)', icon: FileText },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/40 flex flex-col justify-between p-4">
      <div className="space-y-1">
        <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
          Platform Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id as NavTab)}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-left',
                isActive
                  ? 'bg-emerald-600/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              )}
            >
              <Icon className={cn('w-4 h-4', isActive ? 'text-emerald-400' : 'text-slate-400')} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      <div className="pt-4 border-t border-slate-800">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-colors">
          <Settings className="w-4 h-4 text-slate-400" />
          <span>System Settings</span>
        </button>
      </div>
    </aside>
  );
};
