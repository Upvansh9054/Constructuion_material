import React from 'react';
import {
  LayoutDashboard,
  Building2,
  PlusCircle,
  Camera,
  Cpu,
  Layers,
  Sliders,
  DollarSign,
  ShoppingBag,
  Users,
  FileText,
  Bell,
  Settings,
  Globe,
  LogOut,
} from 'lucide-react';
import { cn } from '../../lib/utils';

export type NavScreenId =
  | 'landing'
  | 'auth'
  | 'dashboard'
  | 'projects'
  | 'create-project'
  | 'upload'
  | 'analysis'
  | 'inventory'
  | 'assessment'
  | 'recovery'
  | 'marketplace'
  | 'buyers'
  | 'reports'
  | 'notifications'
  | 'settings';

interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  badgeCritical?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

interface SidebarProps {
  activeScreen: NavScreenId;
  onSelectScreen: (screen: NavScreenId) => void;
  unreadCount?: number;
  onLogout?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeScreen,
  onSelectScreen,
  unreadCount = 2,
  onLogout,
}) => {
  const navSections: NavSection[] = [
    {
      title: 'Operations Overview',
      items: [
        { id: 'dashboard', label: 'Main Dashboard', icon: LayoutDashboard },
        { id: 'projects', label: 'Demolition Sites', icon: Building2, badge: '5' },
        { id: 'create-project', label: 'Register New Site', icon: PlusCircle },
        { id: 'upload', label: 'Site Media Upload', icon: Camera },
      ],
    },
    {
      title: 'AI Intelligence & Scans',
      items: [
        { id: 'analysis', label: 'AI Material Vision', icon: Cpu },
        { id: 'inventory', label: 'Material Inventory', icon: Layers, badge: '9' },
        { id: 'assessment', label: 'Quantity & Condition', icon: Sliders },
        { id: 'recovery', label: 'Value & Carbon Math', icon: DollarSign },
      ],
    },
    {
      title: 'Circular Commerce',
      items: [
        { id: 'marketplace', label: 'Recovery Market', icon: ShoppingBag, badge: '4' },
        { id: 'buyers', label: 'Certified Off-Takers', icon: Users },
        { id: 'reports', label: 'DMAR Compliance Reports', icon: FileText },
      ],
    },
    {
      title: 'System & Platform',
      items: [
        { id: 'notifications', label: 'Alerts & Notices', icon: Bell, badge: unreadCount > 0 ? `${unreadCount}` : undefined, badgeCritical: true },
        { id: 'settings', label: 'Profile & Settings', icon: Settings },
        { id: 'landing', label: 'Public Portal', icon: Globe },
      ],
    },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/40 flex flex-col justify-between overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800 flex-shrink-0">
      <div className="p-4 space-y-6">
        {navSections.map((section, sIdx) => (
          <div key={sIdx} className="space-y-1">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 px-3 mb-1.5">
              {section.title}
            </div>

            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeScreen === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectScreen(item.id as NavScreenId)}
                  className={cn(
                    'w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-all text-left group',
                    isActive
                      ? 'bg-emerald-600/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  )}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <Icon
                      className={cn(
                        'w-4 h-4 flex-shrink-0 transition-colors',
                        isActive ? 'text-emerald-400' : 'text-slate-500 group-hover:text-slate-300'
                      )}
                    />
                    <span className="truncate">{item.label}</span>
                  </div>

                  {item.badge && (
                    <span
                      className={cn(
                        'px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold',
                        item.badgeCritical
                          ? 'bg-rose-500/20 text-rose-400 animate-pulse'
                          : isActive
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : 'bg-slate-800 text-slate-400'
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {onLogout && (
        <div className="p-4 border-t border-slate-800">
          <button
            onClick={onLogout}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors text-left"
          >
            <LogOut className="w-4 h-4 text-slate-500" />
            <span>Sign Out Workspace</span>
          </button>
        </div>
      )}
    </aside>
  );
};
