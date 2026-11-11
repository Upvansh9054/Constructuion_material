import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Select } from '../components/ui/select';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { MaterialItem, ConditionGrade } from '../types/material';
import { formatCurrency, formatTonnes, formatCO2 } from '../lib/utils';
import {
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Scale,
  DollarSign,
  Leaf,
} from 'lucide-react';

interface QuantityConditionScreenProps {
  materials: MaterialItem[];
  selectedMaterialId?: string;
  onSaveAssessment: (updatedItem: MaterialItem) => void;
  onCancel: () => void;
}

export const QuantityConditionScreen: React.FC<QuantityConditionScreenProps> = ({
  materials,
  selectedMaterialId = 'mat-001',
  onSaveAssessment,
  onCancel,
}) => {
  const [activeId, setActiveId] = useState(selectedMaterialId);
  const currentItem = materials.find((m) => m.id === activeId) || materials[0];

  // Calibration state initialized from selected item
  const [volumeM3, setVolumeM3] = useState<number>(currentItem.estimated_volume_m3);
  const [conditionGrade, setConditionGrade] = useState<ConditionGrade>(currentItem.condition_grade);
  const [densityTonnesPerM3, setDensityTonnesPerM3] = useState<number>(
    currentItem.category === 'STEEL'
      ? 7.85
      : currentItem.category === 'CONCRETE'
      ? 2.4
      : currentItem.category === 'BRICKS'
      ? 1.8
      : currentItem.category === 'TIMBER'
      ? 0.65
      : 1.5
  );
  const [packingFactor, setPackingFactor] = useState<number>(0.85);
  const [surveyorNotes, setSurveyorNotes] = useState<string>(
    currentItem.surveyor_adjustment_notes || 'Inspected on-site; flange straightness verified.'
  );
  const [hasAsbestosRisk, setHasAsbestosRisk] = useState<boolean>(
    Boolean(currentItem.contamination_risk?.includes('Asbestos'))
  );
  const [hasLeadPaint, setHasLeadPaint] = useState<boolean>(false);
  const [hasHeavyMortar, setHasHeavyMortar] = useState<boolean>(false);
  const [isSaved, setIsSaved] = useState(false);

  // Synchronize when active item dropdown switches
  const handleSelectMaterial = (id: string) => {
    setActiveId(id);
    const it = materials.find((m) => m.id === id);
    if (it) {
      setVolumeM3(it.estimated_volume_m3);
      setConditionGrade(it.condition_grade);
      setSurveyorNotes(it.surveyor_adjustment_notes || '');
      setIsSaved(false);
    }
  };

  // Real-time recalculation math
  const calculatedWeightTonnes = Math.round(volumeM3 * densityTonnesPerM3 * packingFactor * 10) / 10;

  const basePrices: Record<string, number> = {
    STEEL: 320.0,
    CONCRETE: 18.0,
    BRICKS: 110.0,
    TIMBER: 190.0,
    GLASS: 45.0,
    MIXED_DEBRIS: 8.0,
  };

  const conditionMultipliers: Record<ConditionGrade, number> = {
    REUSABLE_EXCELLENT: 1.6,
    REUSABLE_GOOD: 1.15,
    RECYCLABLE: 0.85,
    DOWN_CYCLE_ONLY: 0.4,
    HAZARDOUS_CONTAMINATED: 0.0,
  };

  const carbonFactors: Record<string, number> = {
    STEEL: 1800.0,
    CONCRETE: 130.0,
    BRICKS: 240.0,
    TIMBER: 450.0,
    GLASS: 350.0,
    MIXED_DEBRIS: 50.0,
  };

  const recalculatedValuation = Math.round(
    calculatedWeightTonnes * (basePrices[currentItem.category] || 20) * (conditionMultipliers[conditionGrade] || 1.0)
  );

  const recalculatedCarbon = Math.round(
    calculatedWeightTonnes * (carbonFactors[currentItem.category] || 100) * (conditionGrade === 'HAZARDOUS_CONTAMINATED' ? 0 : 1.0)
  );

  const handleSave = () => {
    const updated: MaterialItem = {
      ...currentItem,
      estimated_volume_m3: volumeM3,
      estimated_weight_tonnes: calculatedWeightTonnes,
      condition_grade: conditionGrade,
      estimated_market_value_usd: recalculatedValuation,
      embodied_carbon_offset_kg: recalculatedCarbon,
      is_verified_by_surveyor: true,
      surveyor_adjustment_notes: surveyorNotes,
      contamination_risk: hasAsbestosRisk
        ? 'High Asbestos (ACM) Probability - Specialist Abatement Required'
        : hasLeadPaint
        ? 'Lead-based Surface Coating Flagged'
        : hasHeavyMortar
        ? 'Heavy Mortar Adhesion'
        : undefined,
    };

    onSaveAssessment(updated);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Material Inventory', onClick: onCancel },
          { label: 'Quantity & Condition Calibration Workbench' },
        ]}
      />

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Quantity & Condition Assessment
          </h2>
          <p className="text-xs text-slate-400">
            Surveyor calibration workbench for validating volumetric depth, bulk density, and contamination risks
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Select
            value={activeId}
            onChange={(e) => handleSelectMaterial(e.target.value)}
            className="w-56 text-xs bg-slate-900 border-slate-700"
          >
            {materials.map((m) => (
              <option key={m.id} value={m.id}>
                {m.category}: {m.subcategory || m.id}
              </option>
            ))}
          </Select>

          <Button variant="outline" size="sm" onClick={onCancel}>
            Back
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Interactive Calibration Controls (2 Cols) */}
        <div className="lg:col-span-2 space-y-5">
          {/* Volumetric Mass Calibration */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-emerald-400" />
                  Volumetric & Density Adjustments
                </CardTitle>
                <Badge category={currentItem.category}>{currentItem.category}</Badge>
              </div>
              <CardDescription className="text-xs">
                Fine-tune photogrammetric volume and material packing factor
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Volume: {volumeM3} m³
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="500"
                    step="1"
                    value={volumeM3}
                    onChange={(e) => setVolumeM3(parseFloat(e.target.value))}
                    className="w-full accent-emerald-500"
                  />
                  <span className="text-[10px] text-slate-500 block mt-1">Calibrated from 2D bound projection</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Bulk Density: {densityTonnesPerM3} t/m³
                  </label>
                  <input
                    type="range"
                    min="0.4"
                    max="8.0"
                    step="0.05"
                    value={densityTonnesPerM3}
                    onChange={(e) => setDensityTonnesPerM3(parseFloat(e.target.value))}
                    className="w-full accent-emerald-500"
                  />
                  <span className="text-[10px] text-slate-500 block mt-1">CIRIA Reference Standard</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Packing Factor: {Math.round(packingFactor * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0.4"
                    max="1.0"
                    step="0.05"
                    value={packingFactor}
                    onChange={(e) => setPackingFactor(parseFloat(e.target.value))}
                    className="w-full accent-emerald-500"
                  />
                  <span className="text-[10px] text-slate-500 block mt-1">Void ratio & hollow sections</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Condition & Contamination Grading */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Physical Condition & Safety Screening
              </CardTitle>
              <CardDescription className="text-xs">
                Assess reusability grade and identify hazardous abatement requirements
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Assessed Condition Grade
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {[
                    { id: 'REUSABLE_EXCELLENT', label: 'Reusable (Excellent)' },
                    { id: 'REUSABLE_GOOD', label: 'Reusable (Good)' },
                    { id: 'RECYCLABLE', label: 'Recyclable' },
                    { id: 'DOWN_CYCLE_ONLY', label: 'Downcycle Only' },
                    { id: 'HAZARDOUS_CONTAMINATED', label: 'Contaminated' },
                  ].map((grade) => (
                    <button
                      key={grade.id}
                      type="button"
                      onClick={() => setConditionGrade(grade.id as ConditionGrade)}
                      className={`p-2.5 rounded-lg text-xs font-medium border text-left transition-all ${
                        conditionGrade === grade.id
                          ? 'border-emerald-500 bg-emerald-500/15 text-emerald-300 font-bold'
                          : 'border-slate-800 bg-slate-900 text-slate-400 hover:text-white'
                      }`}
                    >
                      {grade.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Contamination Checklist */}
              <div className="pt-3 border-t border-slate-800 space-y-2">
                <span className="text-xs font-semibold text-slate-300 block">Safety & Contamination Checks</span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <label className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-900 border border-slate-800 cursor-pointer text-slate-300">
                    <input
                      type="checkbox"
                      checked={hasAsbestosRisk}
                      onChange={(e) => setHasAsbestosRisk(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-800 text-rose-500 focus:ring-rose-500"
                    />
                    <span>Asbestos (ACM) Risk</span>
                  </label>

                  <label className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-900 border border-slate-800 cursor-pointer text-slate-300">
                    <input
                      type="checkbox"
                      checked={hasLeadPaint}
                      onChange={(e) => setHasLeadPaint(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-800 text-amber-500 focus:ring-amber-500"
                    />
                    <span>Lead Paint Coating</span>
                  </label>

                  <label className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-900 border border-slate-800 cursor-pointer text-slate-300">
                    <input
                      type="checkbox"
                      checked={hasHeavyMortar}
                      onChange={(e) => setHasHeavyMortar(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-800 text-blue-500 focus:ring-blue-500"
                    />
                    <span>Mortar / Adhesion Spall</span>
                  </label>
                </div>
              </div>

              {/* Surveyor Inspection Notes */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Surveyor Field Verification Notes
                </label>
                <textarea
                  rows={2}
                  value={surveyorNotes}
                  onChange={(e) => setSurveyorNotes(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                  placeholder="Record structural measurements, physical accessibility, and crane loading requirements..."
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: Dynamic Calculation Summary & Sign-off (1 Col) */}
        <div className="space-y-4">
          <Card className="border-emerald-900/40 bg-gradient-to-b from-slate-900 to-slate-950">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Real-Time Valuation Summary</CardTitle>
              <CardDescription className="text-xs">
                Dynamically computed from calibrated mass and grade
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="space-y-3 p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    <Scale className="w-4 h-4 text-slate-500" />
                    Calibrated Mass:
                  </span>
                  <span className="text-base font-bold text-white font-mono">
                    {formatTonnes(calculatedWeightTonnes)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    <DollarSign className="w-4 h-4 text-emerald-400" />
                    Estimated Market Value:
                  </span>
                  <span className="text-base font-bold text-emerald-400 font-mono">
                    {formatCurrency(recalculatedValuation)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    <Leaf className="w-4 h-4 text-emerald-400" />
                    Embodied CO₂e Offset:
                  </span>
                  <span className="text-base font-bold text-emerald-300 font-mono">
                    {formatCO2(recalculatedCarbon)}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                <div className="font-semibold text-slate-300">Valuation Multiplier Rule</div>
                <p>
                  Grade: <strong>{conditionGrade.replace(/_/g, ' ')}</strong> (multiplier:{' '}
                  {conditionMultipliers[conditionGrade]}x). Direct reuse commands a 60% salvage premium over scrap remelting.
                </p>
              </div>

              {isSaved && (
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Assessment certified & inventory updated!</span>
                </div>
              )}

              <Button variant="primary" className="w-full" onClick={handleSave}>
                <CheckCircle2 className="w-4 h-4 mr-1.5" />
                Certify Calibration & Save
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
