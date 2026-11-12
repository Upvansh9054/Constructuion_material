import React, { useState } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { DEV_NOTIFICATIONS, NotificationItem } from '../mock/fixtures';
import {
  AlertTriangle,
  DollarSign,
  Cpu,
  Clock,
  Check,
  ArrowRight,
} from 'lucide-react';

interface NotificationsScreenProps {
  notifications?: NotificationItem[];
  onMarkAllAsRead?: () => void;
  onMarkOneAsRead?: (id: string) => void;
  onNavigateToScreen: (screen: string, contextId?: string) => void;
}

export const NotificationsScreen: React.FC<NotificationsScreenProps> = ({
  notifications: initialNotifications,
  onMarkAllAsRead: externalMarkAllAsRead,
  onMarkOneAsRead: externalMarkOneAsRead,
  onNavigateToScreen,
}) => {
  const [localNotifications, setLocalNotifications] = useState<NotificationItem[]>(
    initialNotifications || DEV_NOTIFICATIONS
  );
  const [filterPriority, setFilterPriority] = useState<string>('ALL');

  const notifications = initialNotifications || localNotifications;

  const filtered = notifications.filter((n) => {
    if (filterPriority === 'ALL') return true;
    if (filterPriority === 'UNREAD') return !n.is_read;
    return n.priority === filterPriority;
  });

  const markAllAsRead = () => {
    if (externalMarkAllAsRead) {
      externalMarkAllAsRead();
    } else {
      setLocalNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    }
  };

  const markOneAsRead = (id: string) => {
    if (externalMarkOneAsRead) {
      externalMarkOneAsRead(id);
    } else {
      setLocalNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    }
  };

  const getIcon = (type: NotificationItem['type']) => {
    switch (type) {
      case 'HAZARD_ALERT':
        return <AlertTriangle className="w-5 h-5 text-rose-400" />;
      case 'BID_RECEIVED':
        return <DollarSign className="w-5 h-5 text-emerald-400" />;
      case 'AI_COMPLETE':
        return <Cpu className="w-5 h-5 text-blue-400" />;
      case 'COMPLIANCE_REMINDER':
        return <Clock className="w-5 h-5 text-amber-400" />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Activity & Regulatory Alerts
          </h2>
          <p className="text-xs text-slate-400">
            Real-time notifications: Pre-demolition hazardous detections, secondary buyer bids, and AI inference completions
          </p>
        </div>

        <Button variant="outline" size="sm" onClick={markAllAsRead}>
          <Check className="w-4 h-4 mr-1.5" /> Mark All as Read
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        {[
          { id: 'ALL', label: 'All Alerts' },
          { id: 'UNREAD', label: 'Unread Only' },
          { id: 'CRITICAL', label: 'Critical Hazards' },
          { id: 'HIGH', label: 'Purchase Bids' },
          { id: 'NORMAL', label: 'System & Reports' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilterPriority(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
              filterPriority === tab.id
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {filtered.map((item) => (
          <Card
            key={item.id}
            className={`p-4 transition-all hover:border-slate-700 ${
              !item.is_read ? 'bg-slate-900/90 border-slate-700/80' : 'bg-slate-950/60 opacity-85'
            }`}
          >
            <div className="flex items-start gap-4">
              <div
                className={`p-2.5 rounded-xl border flex-shrink-0 ${
                  item.priority === 'CRITICAL'
                    ? 'bg-rose-500/10 border-rose-500/30'
                    : item.priority === 'HIGH'
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-slate-800/80 border-slate-700/60'
                }`}
              >
                {getIcon(item.type)}
              </div>

              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-white">{item.title}</span>
                    {!item.is_read && (
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    )}
                  </div>
                  <span className="text-[11px] font-mono text-slate-500">
                    {new Date(item.timestamp).toLocaleDateString()} • {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">{item.message}</p>

                <div className="pt-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                        item.priority === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-300'
                          : item.priority === 'HIGH'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {item.priority}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {!item.is_read && (
                      <button
                        onClick={() => markOneAsRead(item.id)}
                        className="text-[11px] text-slate-400 hover:text-white underline underline-offset-2"
                      >
                        Dismiss
                      </button>
                    )}
                    {item.link_screen && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs px-2.5"
                        onClick={() => onNavigateToScreen(item.link_screen!, item.project_id)}
                      >
                        Inspect Action <ArrowRight className="w-3 h-3 ml-1" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
