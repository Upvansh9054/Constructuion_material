import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { StatCard } from '../components/common/StatCard';
import { ValuationSummary } from '../types/material';
import { formatCurrency, formatTonnes, formatCO2 } from '../lib/utils';
import {
  DollarSign,
  TrendingUp,
  Leaf,
  Download,
  CheckCircle2,
  ShieldAlert,
} from 'lucide-react';

interface RecoveryValueScreenProps {
  summary: ValuationSummary;
  onNavigateToScreen: (screen: string) => void;
}

export const RecoveryValueScreen: React.FC<RecoveryValueScreenProps> = ({
  summary,
}) => {
  // Financial metrics
  const totalMass = summary.total_recoverable_tonnes; // 1,124.3 t
  const salvageValue = summary.total_estimated_value_usd; // $59,194 USD
  const landfillTippingFeePerTonne = 85.0; // Regional standard C&D tipping fee ($/t)
  const landfillFeesAvoided = Math.round(totalMass * landfillTippingFeePerTonne); // $95,565 USD
  const totalFinancialBenefit = salvageValue + landfillFeesAvoided; // $154,759 USD

  const streamAnalytics = [
    {
      category: 'STEEL',
      mass: 98.1,
      salvageValue: 31392.0,
      tippingAvoided: 8338.5,
      carbonSaved: 176580.0,
      virginCost: 98100.0,
      primaryRoute: 'Direct Reuse & Mini-Mill EAF',
    },
    {
      category: 'CONCRETE',
      mass: 768.0,
      salvageValue: 11750.4,
      tippingAvoided: 65280.0,
      carbonSaved: 79872.0,
      virginCost: 76800.0,
      primaryRoute: 'On-site Road Sub-base Crushing',
    },
    {
      category: 'BRICKS',
      mass: 63.0,
      salvageValue: 11088.0,
      tippingAvoided: 5355.0,
      carbonSaved: 18144.0,
      virginCost: 28350.0,
      primaryRoute: 'Architectural Salvage Cleaning',
    },
    {
      category: 'TIMBER',
      mass: 18.2,
      salvageValue: 3976.7,
      tippingAvoided: 1547.0,
      carbonSaved: 8190.0,
      virginCost: 14560.0,
      primaryRoute: 'Structural Framing Reclamation',
    },
    {
      category: 'GLASS',
      mass: 12.0,
      salvageValue: 459.0,
      tippingAvoided: 1020.0,
      carbonSaved: 3360.0,
      virginCost: 7200.0,
      primaryRoute: 'Facade Cullet Remelting',
    },
    {
      category: 'MIXED_DEBRIS',
      mass: 165.0,
      salvageValue: 528.0,
      tippingAvoided: 14025.0,
      carbonSaved: 2887.5,
      virginCost: 0.0,
      primaryRoute: 'Mechanical Sorting & Aggregate Screen',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Recovery Value & Circular Carbon Analysis
          </h2>
          <p className="text-xs text-slate-400">
            Comparative financial yield: Secondary market salvage value, landfill tipping fee avoidance, and carbon offsets
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => alert('Exporting full economic valuation report (PDF)...')}
        >
          <Download className="w-4 h-4 mr-1.5" /> Export Valuation Audit
        </Button>
      </div>

      {/* Hero Financial Ticker */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Secondary Salvage Value"
          value={formatCurrency(salvageValue)}
          subtitle="Direct sales on marketplace"
          icon={<DollarSign className="w-4 h-4 text-emerald-400" />}
          trend="+18.4%"
          trendPositive={true}
        />

        <StatCard
          title="Tipping Fees Avoided"
          value={formatCurrency(landfillFeesAvoided)}
          subtitle="$85/t baseline landfill fee"
          icon={<TrendingUp className="w-4 h-4 text-blue-400" />}
          trend="Saved"
          trendPositive={true}
        />

        <StatCard
          title="Total Net Economic Advantage"
          value={formatCurrency(totalFinancialBenefit)}
          subtitle="Salvage revenue + avoided costs"
          icon={<DollarSign className="w-4 h-4 text-emerald-400" />}
          trend="Net Gain"
          trendPositive={true}
        />

        <StatCard
          title="Embodied Carbon Offset"
          value={formatCO2(summary.total_carbon_offset_kg_co2e)}
          subtitle="ICE displacement benchmark"
          icon={<Leaf className="w-4 h-4 text-emerald-400" />}
        />
      </div>

      {/* Comparative ROI: Deconstruction vs Conventional Wrecking */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-emerald-500/30 bg-emerald-950/10">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm text-emerald-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" /> AI-Directed Selective Deconstruction (Our Approach)
              </CardTitle>
              <span className="text-xs font-bold text-emerald-300 font-mono">+44% Net Margin</span>
            </div>
            <CardDescription className="text-xs">
              Materials scanned, cataloged at source, unbolted, and pre-sold to certified buyers
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="text-slate-400">Secondary Material Resale Revenue:</span>
              <span className="font-bold text-emerald-400">{formatCurrency(salvageValue)}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="text-slate-400">Landfill Tipping Disposal Cost Avoidance:</span>
              <span className="font-bold text-emerald-400">+{formatCurrency(landfillFeesAvoided)}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="text-slate-400">Carbon Credits & ESG Subsidies:</span>
              <span className="font-bold text-teal-300">{formatCO2(summary.total_carbon_offset_kg_co2e)}</span>
            </div>
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between font-bold text-white">
              <span>Total Financial Yield:</span>
              <span className="text-base text-emerald-400 font-mono">{formatCurrency(totalFinancialBenefit)}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-rose-900/30 bg-rose-950/5">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm text-rose-400 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4" /> Conventional Indiscriminate Wrecking Ball
              </CardTitle>
              <span className="text-xs font-bold text-rose-400 font-mono">- $95,565 Loss</span>
            </div>
            <CardDescription className="text-xs">
              Immediate mechanical crushing with zero salvage and total landfill disposal
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-400">
              <span>Secondary Material Salvage:</span>
              <span className="font-bold text-slate-500">$0.00 (Crushed into debris)</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-400">
              <span>Mandatory Landfill Tipping Fees:</span>
              <span className="font-bold text-rose-400">- {formatCurrency(landfillFeesAvoided)}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-400">
              <span>Virgin Sourcing Replacement Footprint:</span>
              <span className="font-bold text-rose-400">+ 289 t CO₂e emitted</span>
            </div>
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between font-bold text-white">
              <span>Net Financial Result:</span>
              <span className="text-base text-rose-400 font-mono">-$95,565 (Heavy Disposal Penalty)</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Stream-by-Stream Valuation Matrix */}
      <Card>
        <CardHeader>
          <CardTitle>Stream-by-Stream Economic & Carbon Matrix</CardTitle>
          <CardDescription>
            Detailed ledger of recovery value and virgin replacement cost displacement per material stream
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                  <th className="py-3 px-4">Material Category</th>
                  <th className="py-3 px-4">Recovered Mass</th>
                  <th className="py-3 px-4">Secondary Salvage</th>
                  <th className="py-3 px-4">Tipping Avoided</th>
                  <th className="py-3 px-4">Carbon Offset</th>
                  <th className="py-3 px-4">Primary Disposition Route</th>
                  <th className="py-3 px-4 text-right">Net Value Added</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {streamAnalytics.map((s) => (
                  <tr key={s.category} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-white">{s.category}</td>
                    <td className="py-3 px-4 font-mono text-slate-300">{formatTonnes(s.mass)}</td>
                    <td className="py-3 px-4 font-mono font-semibold text-emerald-400">
                      {formatCurrency(s.salvageValue)}
                    </td>
                    <td className="py-3 px-4 font-mono text-blue-300">
                      {formatCurrency(s.tippingAvoided)}
                    </td>
                    <td className="py-3 px-4 font-mono text-emerald-300">
                      {formatCO2(s.carbonSaved)}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">{s.primaryRoute}</td>
                    <td className="py-3 px-4 font-mono font-bold text-white text-right">
                      {formatCurrency(s.salvageValue + s.tippingAvoided)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
