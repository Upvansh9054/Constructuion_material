import React, { useState } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Dialog, DialogFooter } from '../components/ui/dialog';
import { MaterialItem, MaterialCategory, ConditionGrade } from '../types/material';
import { formatCurrency, formatTonnes, formatCO2 } from '../lib/utils';
import {
  Search,
  CheckCircle2,
  AlertTriangle,
  Download,
  ShoppingBag,
  Sliders,
} from 'lucide-react';

interface MaterialInventoryScreenProps {
  materials: MaterialItem[];
  onUpdateMaterial: (updated: MaterialItem) => void;
  onNavigateToScreen: (screen: string, contextId?: string) => void;
}

export const MaterialInventoryScreen: React.FC<MaterialInventoryScreenProps> = ({
  materials,
  onUpdateMaterial,
  onNavigateToScreen,
}) => {
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<MaterialCategory | 'ALL'>('ALL');
  const [conditionFilter, setConditionFilter] = useState<ConditionGrade | 'ALL'>('ALL');
  const [verifiedFilter, setVerifiedFilter] = useState<'ALL' | 'VERIFIED' | 'PENDING'>('ALL');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [activeItemModal, setActiveItemModal] = useState<MaterialItem | null>(null);

  const filteredMaterials = materials.filter((m) => {
    const matchesSearch =
      m.subcategory?.toLowerCase().includes(search.toLowerCase()) ||
      m.category.toLowerCase().includes(search.toLowerCase()) ||
      m.id.toLowerCase().includes(search.toLowerCase());
    const matchesCat = categoryFilter === 'ALL' || m.category === categoryFilter;
    const matchesCond = conditionFilter === 'ALL' || m.condition_grade === conditionFilter;
    const matchesVer =
      verifiedFilter === 'ALL' ||
      (verifiedFilter === 'VERIFIED' ? m.is_verified_by_surveyor : !m.is_verified_by_surveyor);

    return matchesSearch && matchesCat && matchesCond && matchesVer;
  });

  const categories: { id: MaterialCategory | 'ALL'; label: string }[] = [
    { id: 'ALL', label: 'All Streams' },
    { id: 'CONCRETE', label: '1. Concrete' },
    { id: 'BRICKS', label: '2. Bricks' },
    { id: 'STEEL', label: '3. Steel' },
    { id: 'TIMBER', label: '4. Timber' },
    { id: 'GLASS', label: '5. Glass' },
    { id: 'MIXED_DEBRIS', label: '6. Mixed Debris' },
  ];

  const toggleSelectAll = () => {
    if (selectedIds.length === filteredMaterials.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredMaterials.map((m) => m.id));
    }
  };

  const toggleSelectOne = (id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]));
  };

  const handleBulkVerify = () => {
    selectedIds.forEach((id) => {
      const item = materials.find((m) => m.id === id);
      if (item) {
        onUpdateMaterial({ ...item, is_verified_by_surveyor: true });
      }
    });
    setSelectedIds([]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">Material Inventory</h2>
          <p className="text-xs text-slate-400">
            Detected and cataloged construction components classified across the 6 circular resource streams
          </p>
        </div>

        <div className="flex items-center gap-2">
          {selectedIds.length > 0 && (
            <Button variant="primary" size="sm" onClick={handleBulkVerify}>
              <CheckCircle2 className="w-4 h-4 mr-1" />
              Verify Selected ({selectedIds.length})
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => alert('Exporting circular material inventory manifest to CSV...')}
          >
            <Download className="w-4 h-4 mr-1" /> Export CSV
          </Button>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setCategoryFilter(cat.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
              categoryFilter === cat.id
                ? 'bg-emerald-600 text-white shadow-md'
                : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Search and Secondary Filters Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex-1 max-w-sm">
          <Input
            placeholder="Search subcategory, ID, or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={<Search className="w-4 h-4" />}
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={conditionFilter}
            onChange={(e) => setConditionFilter(e.target.value as any)}
            className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-slate-300 focus:outline-none"
          >
            <option value="ALL">All Condition Grades</option>
            <option value="REUSABLE_EXCELLENT">Reusable (Excellent)</option>
            <option value="REUSABLE_GOOD">Reusable (Good)</option>
            <option value="RECYCLABLE">Recyclable</option>
            <option value="DOWN_CYCLE_ONLY">Downcycle Only</option>
            <option value="HAZARDOUS_CONTAMINATED">Hazardous / Contaminated</option>
          </select>

          <select
            value={verifiedFilter}
            onChange={(e) => setVerifiedFilter(e.target.value as any)}
            className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-slate-300 focus:outline-none"
          >
            <option value="ALL">Verification: All</option>
            <option value="VERIFIED">Verified by Surveyor</option>
            <option value="PENDING">Pending Review</option>
          </select>
        </div>
      </div>

      {/* Main Inventory Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                  <th className="py-3 px-4 w-8">
                    <input
                      type="checkbox"
                      checked={selectedIds.length === filteredMaterials.length && filteredMaterials.length > 0}
                      onChange={toggleSelectAll}
                      className="rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-emerald-500"
                    />
                  </th>
                  <th className="py-3 px-4">Stream & Subcategory</th>
                  <th className="py-3 px-4">Condition Grade</th>
                  <th className="py-3 px-4">Volume (m³)</th>
                  <th className="py-3 px-4">Estimated Mass</th>
                  <th className="py-3 px-4">Market Value</th>
                  <th className="py-3 px-4">Carbon Offset</th>
                  <th className="py-3 px-4">Verification</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredMaterials.map((item) => {
                  const isSelected = selectedIds.includes(item.id);
                  return (
                    <tr
                      key={item.id}
                      className={`hover:bg-slate-800/40 transition-colors ${
                        isSelected ? 'bg-emerald-500/5' : ''
                      }`}
                    >
                      <td className="py-3 px-4">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectOne(item.id)}
                          className="rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-emerald-500"
                        />
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-bold text-white flex items-center gap-2">
                          <span>{item.subcategory || item.category}</span>
                          {item.contamination_risk && (
                            <span title={item.contamination_risk}>
                              <AlertTriangle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <Badge category={item.category} className="text-[10px] py-0 px-1.5">
                            {item.category.replace('_', ' ')}
                          </Badge>
                          <span className="text-[10px] font-mono text-slate-500">{item.id}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge condition={item.condition_grade} className="text-[10px] py-0.5">
                          {item.condition_grade.replace(/_/g, ' ')}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {item.estimated_volume_m3.toFixed(1)} m³
                      </td>
                      <td className="py-3 px-4 font-mono font-semibold text-white">
                        {formatTonnes(item.estimated_weight_tonnes)}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-emerald-400">
                        {formatCurrency(item.estimated_market_value_usd)}
                      </td>
                      <td className="py-3 px-4 font-mono text-emerald-300 text-[11px]">
                        {formatCO2(item.embodied_carbon_offset_kg)}
                      </td>
                      <td className="py-3 px-4">
                        {item.is_verified_by_surveyor ? (
                          <span className="flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                          </span>
                        ) : (
                          <span className="text-amber-400 text-[11px] font-medium">Pending Review</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 px-2 text-[11px]"
                            onClick={() => setActiveItemModal(item)}
                          >
                            Inspect
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-7 px-2 text-[11px]"
                            onClick={() => onNavigateToScreen('assessment', item.id)}
                          >
                            <Sliders className="w-3 h-3 mr-1" /> Calibrate
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Item Inspection Dialog */}
      {activeItemModal && (
        <Dialog
          isOpen={true}
          onClose={() => setActiveItemModal(null)}
          title={`Material Item: ${activeItemModal.subcategory || activeItemModal.category}`}
          description={`Survey Log ID: ${activeItemModal.id} • Registered to Survey session`}
        >
          <div className="space-y-4 text-xs">
            <div className="flex items-center gap-2">
              <Badge category={activeItemModal.category}>{activeItemModal.category}</Badge>
              <Badge condition={activeItemModal.condition_grade}>
                {activeItemModal.condition_grade.replace(/_/g, ' ')}
              </Badge>
            </div>

            <p className="text-slate-300 leading-relaxed">{activeItemModal.description}</p>

            <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">Estimated Weight</span>
                <span className="text-base font-bold text-white font-mono">
                  {formatTonnes(activeItemModal.estimated_weight_tonnes)}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">Estimated Volume</span>
                <span className="text-base font-bold text-white font-mono">
                  {activeItemModal.estimated_volume_m3} m³
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">Recovery Value</span>
                <span className="text-base font-bold text-emerald-400 font-mono">
                  {formatCurrency(activeItemModal.estimated_market_value_usd)}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">Carbon Offset</span>
                <span className="text-base font-bold text-emerald-300 font-mono">
                  {formatCO2(activeItemModal.embodied_carbon_offset_kg)}
                </span>
              </div>
            </div>

            {activeItemModal.contamination_risk && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-1">
                <span className="font-bold flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-rose-400" /> Contamination Advisory
                </span>
                <p className="text-slate-300 text-[11px]">{activeItemModal.contamination_risk}</p>
              </div>
            )}

            <DialogFooter>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  onUpdateMaterial({ ...activeItemModal, is_verified_by_surveyor: true });
                  setActiveItemModal(null);
                }}
              >
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Mark Verified
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  setActiveItemModal(null);
                  onNavigateToScreen('marketplace');
                }}
              >
                <ShoppingBag className="w-3.5 h-3.5 mr-1" /> List on Marketplace
              </Button>
            </DialogFooter>
          </div>
        </Dialog>
      )}
    </div>
  );
};
