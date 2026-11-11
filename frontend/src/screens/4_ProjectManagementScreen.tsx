import React, { useState } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { DemolitionSite } from '../types/site';
import {
  Search,
  PlusCircle,
  MapPin,
  Calendar,
  Camera,
  Layers,
} from 'lucide-react';

interface ProjectManagementScreenProps {
  projects: DemolitionSite[];
  onNavigateToScreen: (screen: string, contextId?: string) => void;
}

export const ProjectManagementScreen: React.FC<ProjectManagementScreenProps> = ({
  projects,
  onNavigateToScreen,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  const filteredProjects = projects.filter((prj) => {
    const matchesSearch =
      prj.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prj.site_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prj.city.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || prj.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const statusTabs = [
    { id: 'ALL', label: 'All Sites' },
    { id: 'ACTIVE_DEMOLITION', label: 'Active Demolition' },
    { id: 'PRE_DEMOLITION_SURVEY', label: 'Pre-Survey' },
    { id: 'MATERIAL_SORTING', label: 'Sorting' },
    { id: 'PLANNING', label: 'Planning' },
    { id: 'COMPLETED', label: 'Completed' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Demolition Project Management</h2>
          <p className="text-xs text-slate-400">
            Lifecycle monitoring, site surveyor schedules, and materials recovery progress across registered sites
          </p>
        </div>
        <Button variant="primary" size="sm" onClick={() => onNavigateToScreen('create-project')}>
          <PlusCircle className="w-4 h-4 mr-1.5" /> Register New Demolition Site
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex-1 max-w-md">
          <Input
            placeholder="Search by project name, code (e.g. MLC), or city..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            icon={<Search className="w-4 h-4" />}
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
            {statusTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`px-3 py-1 rounded-md text-xs font-semibold whitespace-nowrap transition-all ${
                  statusFilter === tab.id
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="hidden sm:flex items-center bg-slate-950 rounded-lg p-1 border border-slate-800 text-xs">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-2.5 py-1 rounded font-semibold ${
                viewMode === 'grid' ? 'bg-slate-800 text-white' : 'text-slate-400'
              }`}
            >
              Cards
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-2.5 py-1 rounded font-semibold ${
                viewMode === 'table' ? 'bg-slate-800 text-white' : 'text-slate-400'
              }`}
            >
              Table
            </button>
          </div>
        </div>
      </div>

      {/* Projects Grid View */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredProjects.map((prj) => (
            <Card key={prj.id} className="flex flex-col justify-between hover:border-slate-700 transition-all">
              <div>
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[11px] font-mono font-bold text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                    {prj.site_code}
                  </span>
                  <Badge
                    variant={
                      prj.status === 'ACTIVE_DEMOLITION'
                        ? 'warning'
                        : prj.status === 'COMPLETED'
                        ? 'success'
                        : 'outline'
                    }
                  >
                    {prj.status.replace(/_/g, ' ')}
                  </Badge>
                </div>

                <h3 className="text-base font-bold text-white mt-3 leading-snug">{prj.name}</h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">{prj.description}</p>

                <div className="mt-4 space-y-2 text-xs text-slate-300">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <MapPin className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    <span className="truncate">{prj.address}, {prj.city}</span>
                  </div>

                  <div className="flex items-center justify-between p-2 rounded bg-slate-800/60 text-xs">
                    <div className="flex items-center gap-1.5 text-slate-400">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>Target Demolition:</span>
                    </div>
                    <span className="font-mono text-white font-medium">
                      {prj.estimated_demolition_date || 'In Progress'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1 text-xs"
                  onClick={() => onNavigateToScreen('upload', prj.id)}
                >
                  <Camera className="w-3.5 h-3.5 mr-1" />
                  Survey Photos
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  className="flex-1 text-xs"
                  onClick={() => onNavigateToScreen('inventory', prj.id)}
                >
                  <Layers className="w-3.5 h-3.5 mr-1" />
                  Materials
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        /* Table View */
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                    <th className="py-3 px-4">Project Name & Site Code</th>
                    <th className="py-3 px-4">Location</th>
                    <th className="py-3 px-4">Demolition Status</th>
                    <th className="py-3 px-4">Scheduled Date</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredProjects.map((prj) => (
                    <tr key={prj.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-bold text-white">{prj.name}</div>
                        <div className="text-[11px] font-mono text-slate-500">{prj.site_code}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {prj.city}, {prj.country}
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          variant={
                            prj.status === 'ACTIVE_DEMOLITION'
                              ? 'warning'
                              : prj.status === 'COMPLETED'
                              ? 'success'
                              : 'outline'
                          }
                        >
                          {prj.status.replace(/_/g, ' ')}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400">
                        {prj.estimated_demolition_date || 'TBD'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-7 text-[11px]"
                            onClick={() => onNavigateToScreen('upload', prj.id)}
                          >
                            Upload
                          </Button>
                          <Button
                            variant="primary"
                            size="sm"
                            className="h-7 text-[11px]"
                            onClick={() => onNavigateToScreen('inventory', prj.id)}
                          >
                            Inventory
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
