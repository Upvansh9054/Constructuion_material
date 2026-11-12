import React, { useState } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Dialog, DialogFooter } from '../components/ui/dialog';
import { MaterialItem, MaterialCategory, ConditionGrade } from '../types/material';
import { formatCurrency, formatTonnes, formatCO2 } from '../lib/utils';
import { apiClient } from '../lib/api-client';
import {
  Search,
  CheckCircle2,
  AlertTriangle,
  Download,
  ShoppingBag,
  Sliders,
  Scale,
  ShieldAlert,
  Box,
  FileText,
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

  // Weighbridge ticket verification modal state
  const [weighbridgeModalItem, setWeighbridgeModalItem] = useState<MaterialItem | null>(null);
  const [wbWeightTonnes, setWbWeightTonnes] = useState<number>(0);
  const [wbTicketNumber, setWbTicketNumber] = useState<string>('');
  const [wbScaleId, setWbScaleId] = useState<string>('SCALE-METRO-01');
  const [wbNotes, setWbNotes] = useState<string>('');
  const [wbSubmitting, setWbSubmitting] = useState<boolean>(false);

  const filteredMaterials = materials.filter((m) => {
    const matchesSearch =
      m.subcategory?.toLowerCase().includes(search.toLowerCase()) ||
      m.category.toLowerCase().includes(search.toLowerCase()) ||
      m.id.toLowerCase().includes(search.toLowerCase()) ||
      (m.weighbridge_ticket_number && m.weighbridge_ticket_number.toLowerCase().includes(search.toLowerCase()));
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

  const openWeighbridgeModal = (item: MaterialItem) => {
    setWeighbridgeModalItem(item);
    setWbWeightTonnes(item.verified_weight_tonnes || item.estimated_weight_tonnes);
    setWbTicketNumber(item.weighbridge_ticket_number || `WB-${new Date().getFullYear()}-${Math.floor(10000 + Math.random() * 90000)}`);
    setWbScaleId(item.weighbridge_scale_id || 'SCALE-METRO-01');
    setWbNotes('');
  };

  const handleSaveWeighbridgeTicket = async () => {
    if (!weighbridgeModalItem || wbWeightTonnes <= 0 || !wbTicketNumber.trim()) return;

    setWbSubmitting(true);
    try {
      // Try live API if connected
      const res = await apiClient.verifyWeighbridge(weighbridgeModalItem.id, {
        verified_weight_tonnes: wbWeightTonnes,
        weighbridge_ticket_number: wbTicketNumber.trim(),
        weighbridge_scale_id: wbScaleId.trim() || undefined,
        surveyor_notes: wbNotes.trim() || undefined,
      });

      const updated: MaterialItem = {
        ...weighbridgeModalItem,
        is_verified_by_surveyor: true,
        verified_weight_tonnes: res.verified_weight_tonnes,
        weighbridge_ticket_number: res.weighbridge_ticket_number,
        weighbridge_scale_id: wbScaleId,
        verified_at: res.verified_at,
        reference_measurement_notes: wbNotes ? `Weighbridge verified: ${wbNotes}` : weighbridgeModalItem.reference_measurement_notes,
      };
      onUpdateMaterial(updated);
    } catch {
      // Local fallback
      const updated: MaterialItem = {
        ...weighbridgeModalItem,
        is_verified_by_surveyor: true,
        verified_weight_tonnes: wbWeightTonnes,
        weighbridge_ticket_number: wbTicketNumber.trim(),
        weighbridge_scale_id: wbScaleId.trim(),
        verified_at: new Date().toISOString(),
        reference_measurement_notes: wbNotes ? `Weighbridge verified: ${wbNotes}` : weighbridgeModalItem.reference_measurement_notes,
      };
      onUpdateMaterial(updated);
    } finally {
      setWbSubmitting(false);
      setWeighbridgeModalItem(null);
    }
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

        <div className="flex flex-wrap items-center gap-2">
          {selectedIds.length > 0 && (
            <Button variant="primary" size="sm" onClick={handleBulkVerify}>
              <CheckCircle2 className="w-4 h-4 mr-1" />
              Verify Selected ({selectedIds.length})
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigateToScreen('marketplace')}
            className="border-emerald-800/40 text-emerald-400 hover:bg-emerald-950/40"
          >
            <ShoppingBag className="w-4 h-4 mr-1" /> Marketplace
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigateToScreen('reports')}
          >
            <FileText className="w-4 h-4 mr-1" /> DMAR Permit
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => alert('Exporting circular material inventory manifest to CSV...')}
          >
            <Download className="w-4 h-4 mr-1" /> Export CSV
          </Button>
        </div>
      </div>

      {/* Handover & Workflow Banner */}
      <div className="p-3.5 rounded-xl bg-slate-900/90 border border-emerald-900/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 flex-shrink-0">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div>
            <span className="font-semibold text-white">Step 2: Pre-Demolition Audit Verified by Licensed Surveyor</span>
            <p className="text-slate-400 text-[11px]">
              Tonnage and condition grades calibrated via drone photogrammetry. Contractor logs weighbridge tickets at the scale, sells materials on the marketplace, and generates EPA DMAR reports.
            </p>
          </div>
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
            placeholder="Search subcategory, ID, ticket #..."
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
            <option value="VERIFIED">Verified / Certified</option>
            <option value="PENDING">Pending Scale Ticket</option>
          </select>
        </div>
      </div>

      {/* Main Inventory Table with Separated Estimated vs Verified Quantities */}
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
                  <th className="py-3 px-4">Condition & Route</th>
                  <th className="py-3 px-4">Volume (m³)</th>
                  <th className="py-3 px-4">Estimated Mass (t)</th>
                  <th className="py-3 px-4">Verified Weighbridge (t)</th>
                  <th className="py-3 px-4">Market Value</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredMaterials.map((item) => {
                  const isSelected = selectedIds.includes(item.id);
                  const hasWeighbridge = item.verified_weight_tonnes !== undefined && item.verified_weight_tonnes !== null;
                  const deltaTonnes = hasWeighbridge ? item.verified_weight_tonnes! - item.estimated_weight_tonnes : 0;
                  const variancePct = hasWeighbridge && item.estimated_weight_tonnes > 0
                    ? ((deltaTonnes / item.estimated_weight_tonnes) * 100).toFixed(1)
                    : null;

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
                          {item.requires_specialist_abatement && (
                            <span title="EPA/OSHA Hazardous Abatement Warning" className="flex items-center text-rose-400">
                              <ShieldAlert className="w-3.5 h-3.5" />
                            </span>
                          )}
                          {!item.requires_specialist_abatement && item.contamination_risk && (
                            <span title={item.contamination_risk}>
                              <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
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
                        {item.recommended_recovery_route && (
                          <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                            {item.recommended_recovery_route.replace(/_/g, ' ')}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {item.estimated_volume_m3.toFixed(1)} m³
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-mono font-semibold text-white">
                          {formatTonnes(item.estimated_weight_tonnes)}
                        </div>
                        <div className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
                          <span>±{item.uncertainty_percentage || 20}%</span>
                          <span className="text-slate-600">•</span>
                          <span className="text-slate-500 truncate max-w-[90px]" title={item.calculation_method}>
                            {item.calculation_method?.replace(/_/g, ' ') || 'visual prior'}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        {hasWeighbridge ? (
                          <div>
                            <div className="font-mono font-bold text-emerald-400 flex items-center gap-1.5">
                              <Scale className="w-3.5 h-3.5 text-emerald-400" />
                              {formatTonnes(item.verified_weight_tonnes!)}
                            </div>
                            <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1 mt-0.5">
                              <span className="text-slate-300 font-semibold">{item.weighbridge_ticket_number}</span>
                              <span className={deltaTonnes >= 0 ? 'text-amber-400' : 'text-emerald-400'}>
                                ({deltaTonnes >= 0 ? '+' : ''}{deltaTonnes.toFixed(1)}t, {variancePct}%)
                              </span>
                            </div>
                          </div>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
                            Pre-Demolition Est.
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-emerald-400">
                        {formatCurrency(item.estimated_market_value_usd)}
                      </td>
                      <td className="py-3 px-4">
                        {item.is_verified_by_surveyor ? (
                          <span className="flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Certified
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
                            className="h-7 px-2 text-[11px] border-emerald-900/40 text-emerald-300 hover:bg-emerald-950/30"
                            onClick={() => openWeighbridgeModal(item)}
                          >
                            <Scale className="w-3 h-3 mr-1 text-emerald-400" /> Ticket
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

      {/* Weighbridge Verification Modal */}
      {weighbridgeModalItem && (
        <Dialog
          isOpen={true}
          onClose={() => setWeighbridgeModalItem(null)}
          title={`Weighbridge Scale Verification: ${weighbridgeModalItem.subcategory || weighbridgeModalItem.category}`}
          description={`Log official certified scale ticket measurement for ${weighbridgeModalItem.id}`}
        >
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-slate-400">
                <span>Visual Survey Pre-Estimate:</span>
                <span className="font-mono font-bold text-white">
                  {formatTonnes(weighbridgeModalItem.estimated_weight_tonnes)}
                </span>
              </div>
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Uncertainty Envelope:</span>
                <span className="font-mono text-slate-300">
                  {weighbridgeModalItem.min_weight_tonnes || (weighbridgeModalItem.estimated_weight_tonnes * 0.8).toFixed(1)}t –{' '}
                  {weighbridgeModalItem.max_weight_tonnes || (weighbridgeModalItem.estimated_weight_tonnes * 1.2).toFixed(1)}t
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Certified Weighbridge Mass (Tonnes) *
                </label>
                <Input
                  type="number"
                  step="0.05"
                  value={wbWeightTonnes}
                  onChange={(e) => setWbWeightTonnes(parseFloat(e.target.value) || 0)}
                  placeholder="e.g. 96.4"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Official Ticket / Manifest Number *
                </label>
                <Input
                  type="text"
                  value={wbTicketNumber}
                  onChange={(e) => setWbTicketNumber(e.target.value)}
                  placeholder="e.g. WB-2026-88412"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-slate-300 font-semibold mb-1">
                  Scale Calibration ID / Facility Location
                </label>
                <Input
                  type="text"
                  value={wbScaleId}
                  onChange={(e) => setWbScaleId(e.target.value)}
                  placeholder="e.g. SCALE-METRO-01 (Certified Class III)"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-slate-300 font-semibold mb-1">
                  Weighbridge Operator / Surveyor Field Notes
                </label>
                <textarea
                  rows={2}
                  value={wbNotes}
                  onChange={(e) => setWbNotes(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                  placeholder="Certified gross minus tare recorded at plant weighbridge."
                />
              </div>
            </div>

            {wbWeightTonnes > 0 && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 space-y-1">
                <div className="flex items-center justify-between font-semibold">
                  <span>Variance from Pre-Demolition Visual Estimate:</span>
                  <span className="font-mono">
                    {(wbWeightTonnes - weighbridgeModalItem.estimated_weight_tonnes >= 0 ? '+' : '')}
                    {(wbWeightTonnes - weighbridgeModalItem.estimated_weight_tonnes).toFixed(2)} t (
                    {(
                      ((wbWeightTonnes - weighbridgeModalItem.estimated_weight_tonnes) /
                        (weighbridgeModalItem.estimated_weight_tonnes || 1)) *
                      100
                    ).toFixed(1)}
                    %)
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Visual photogrammetry estimate remains archived for model training and accuracy calibration.
                </p>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" size="sm" onClick={() => setWeighbridgeModalItem(null)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveWeighbridgeTicket}
                disabled={wbSubmitting || wbWeightTonnes <= 0 || !wbTicketNumber.trim()}
              >
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                {wbSubmitting ? 'Recording Ticket...' : 'Save Weighbridge Ticket'}
              </Button>
            </DialogFooter>
          </div>
        </Dialog>
      )}

      {/* Item Comprehensive Inspection Dialog */}
      {activeItemModal && (
        <Dialog
          isOpen={true}
          onClose={() => setActiveItemModal(null)}
          title={`Material Item: ${activeItemModal.subcategory || activeItemModal.category}`}
          description={`Survey Log ID: ${activeItemModal.id} • Registered to Survey session`}
        >
          <div className="space-y-4 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <Badge category={activeItemModal.category}>{activeItemModal.category}</Badge>
              <Badge condition={activeItemModal.condition_grade}>
                {activeItemModal.condition_grade.replace(/_/g, ' ')}
              </Badge>
              {activeItemModal.recommended_recovery_route && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">
                  Route: {activeItemModal.recommended_recovery_route.replace(/_/g, ' ')} ({activeItemModal.recoverability_percentage || 85}%)
                </span>
              )}
            </div>

            <p className="text-slate-300 leading-relaxed">{activeItemModal.description}</p>

            {/* Hazardous Alert Card */}
            {activeItemModal.requires_specialist_abatement && (
              <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/40 text-rose-200 space-y-1.5">
                <div className="font-bold flex items-center gap-2 text-rose-300">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  MANDATORY SPECIALIST ABATEMENT REQUIRED
                </div>
                <p className="text-[11px] text-rose-300/90 leading-relaxed">
                  {activeItemModal.hazard_inspection_warning || 'Regulated hazardous material identified. Prohibited from crushing or commercial recycling under EPA NESHAP / OSHA regulations.'}
                </p>
              </div>
            )}

            {/* Physical Dimensions & Volumetric Geometry */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5 text-xs">
                <Box className="w-3.5 h-3.5 text-emerald-400" />
                3D Physical Geometry & Estimation Methodology
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center pt-1 font-mono">
                <div className="p-2 rounded bg-slate-900 border border-slate-800/80">
                  <span className="text-[10px] text-slate-500 block uppercase">Length</span>
                  <span className="text-sm font-bold text-white">{activeItemModal.dimension_length_m ? `${activeItemModal.dimension_length_m}m` : 'N/A'}</span>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800/80">
                  <span className="text-[10px] text-slate-500 block uppercase">Width</span>
                  <span className="text-sm font-bold text-white">{activeItemModal.dimension_width_m ? `${activeItemModal.dimension_width_m}m` : 'N/A'}</span>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800/80">
                  <span className="text-[10px] text-slate-500 block uppercase">Height / Depth</span>
                  <span className="text-sm font-bold text-white">{activeItemModal.dimension_height_m ? `${activeItemModal.dimension_height_m}m` : 'N/A'}</span>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800/80">
                  <span className="text-[10px] text-slate-500 block uppercase">Surface Area</span>
                  <span className="text-sm font-bold text-emerald-400">{activeItemModal.surface_area_m2 ? `${activeItemModal.surface_area_m2}m²` : 'N/A'}</span>
                </div>
              </div>
              <div className="text-[11px] text-slate-400 pt-1 flex items-center justify-between">
                <span>Method: <strong>{activeItemModal.calculation_method?.replace(/_/g, ' ') || 'Calibrated GSD Photogrammetry'}</strong></span>
                <span>Uncertainty: <strong>±{activeItemModal.uncertainty_percentage || 20}%</strong></span>
              </div>
            </div>

            {/* Mass Comparison: Visual Estimate vs Certified Weighbridge */}
            <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">Visual Pre-Estimate</span>
                <span className="text-base font-bold text-white font-mono">
                  {formatTonnes(activeItemModal.estimated_weight_tonnes)}
                </span>
                <span className="text-[10px] text-slate-500 block">
                  [{activeItemModal.min_weight_tonnes || (activeItemModal.estimated_weight_tonnes * 0.8).toFixed(1)}t – {activeItemModal.max_weight_tonnes || (activeItemModal.estimated_weight_tonnes * 1.2).toFixed(1)}t]
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">Certified Weighbridge</span>
                {activeItemModal.verified_weight_tonnes !== undefined ? (
                  <div>
                    <span className="text-base font-bold text-emerald-400 font-mono">
                      {formatTonnes(activeItemModal.verified_weight_tonnes)}
                    </span>
                    <span className="text-[10px] text-slate-400 block font-mono">
                      Ticket: {activeItemModal.weighbridge_ticket_number || 'Certified'}
                    </span>
                  </div>
                ) : (
                  <span className="text-amber-400 text-xs font-semibold block mt-1">Pending scale receipt</span>
                )}
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

            {activeItemModal.reference_measurement_notes && (
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 space-y-1">
                <span className="font-semibold text-slate-400 flex items-center gap-1.5 text-[11px]">
                  <FileText className="w-3.5 h-3.5 text-slate-400" /> Surveyor Field Notes & Calibration Log
                </span>
                <p className="text-slate-300 text-[11px] whitespace-pre-wrap">{activeItemModal.reference_measurement_notes}</p>
              </div>
            )}

            <DialogFooter>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  openWeighbridgeModal(activeItemModal);
                  setActiveItemModal(null);
                }}
              >
                <Scale className="w-3.5 h-3.5 mr-1" /> Log Weighbridge Ticket
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
