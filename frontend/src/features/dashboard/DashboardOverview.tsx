import React from 'react';
import { StatCard } from '../../components/common/StatCard';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { ValuationSummary } from '../../types/material';
import { formatCurrency, formatTonnes, formatCO2 } from '../../lib/utils';
import { DollarSign, Scale, Leaf, AlertCircle, PlusCircle, Sparkles, ArrowRight } from 'lucide-react';

interface DashboardOverviewProps {
  summary: ValuationSummary;
  onNavigateToSurveys: () => void;
  onTriggerAnalysis: () => void;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({
  summary,
  onNavigateToSurveys,
  onTriggerAnalysis,
}) => {
  return (
    <div className="space-y-6">
      {/* Top Banner / Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-900/40">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4" />
            Demolition Material Intelligence Engine
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Active Site: Metro Logistics Center Demolition (Phase 2)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Industrial commercial building dismantling • 42,000 m² structural area
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button variant="outline" size="sm" onClick={onNavigateToSurveys}>
            <PlusCircle className="w-4 h-4" />
            Upload Survey Photos
          </Button>
          <Button variant="primary" size="sm" onClick={onTriggerAnalysis}>
            <Sparkles className="w-4 h-4" />
            Run AI Analysis
          </Button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Potential Recovery Value"
          value={formatCurrency(summary.total_estimated_value_usd)}
          subtitle="Secondary material market index"
          icon={<DollarSign className="w-4 h-4 text-emerald-400" />}
          trend="+18.4%"
          trendPositive={true}
        />
        <StatCard
          title="Recoverable Material"
          value={formatTonnes(summary.total_recoverable_tonnes)}
          subtitle="6 streams identified"
          icon={<Scale className="w-4 h-4 text-blue-400" />}
        />
        <StatCard
          title="Embodied Carbon Offset"
          value={formatCO2(summary.total_carbon_offset_kg_co2e)}
          subtitle="Landfill diversion credit"
          icon={<Leaf className="w-4 h-4 text-emerald-400" />}
          trend="Saved"
          trendPositive={true}
        />
        <StatCard
          title="Audit Readiness"
          value="94%"
          subtitle="Pre-demolition compliance (DMAR)"
          icon={<AlertCircle className="w-4 h-4 text-amber-400" />}
        />
      </div>

      {/* Material Breakdown & Progress */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Identified Material Streams Breakdown</CardTitle>
            <CardDescription>
              Volumetric mass and market recovery value distribution across the 6 initial categories
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {summary.categories.map((cat) => {
                const percent = summary.total_recoverable_tonnes > 0
                  ? Math.round((cat.total_weight_tonnes / summary.total_recoverable_tonnes) * 100)
                  : 0;

                return (
                  <div key={cat.category} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200">
                          {cat.category.replace('_', ' ')}
                        </span>
                        <span className="text-slate-500">({cat.item_count} items)</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-slate-400">{formatTonnes(cat.total_weight_tonnes)}</span>
                        <span className="font-bold text-emerald-400">
                          {formatCurrency(cat.estimated_value_usd)}
                        </span>
                      </div>
                    </div>
                    {/* Progress bar */}
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Circular Economy & Quick AI Insights */}
        <Card className="flex flex-col justify-between">
          <div>
            <CardHeader>
              <CardTitle>Circular Economy Offsets</CardTitle>
              <CardDescription>
                CO₂e reduction achieved by recycling & reusing structural components
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-slate-300">
              <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 space-y-1">
                <div className="font-semibold text-white">Structural Steel Reusability</div>
                <p className="text-slate-400">
                  Direct salvage of heavy I-beams displaces virgin electric arc blast furnace production by ~1,800 kg CO₂e / tonne.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 space-y-1">
                <div className="font-semibold text-white">Concrete Aggregate Crushing</div>
                <p className="text-slate-400">
                  On-site mobile crushing eliminates haulage emissions and satisfies road sub-base aggregate demand.
                </p>
              </div>
            </CardContent>
          </div>

          <div className="p-4 pt-0">
            <Button variant="outline" size="sm" className="w-full justify-between" onClick={onNavigateToSurveys}>
              <span>Inspect Raw Survey Images</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};
