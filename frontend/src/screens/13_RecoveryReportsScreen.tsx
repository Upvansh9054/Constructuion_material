import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { DEV_AUDIT_REPORT } from '../mock/fixtures';
import { formatCurrency, formatTonnes, formatCO2 } from '../lib/utils';
import {
  FileText,
  Download,
  Printer,
  Sparkles,
  ShieldCheck,
  Building2,
  Leaf,
  DollarSign,
  Scale,
} from 'lucide-react';

interface RecoveryReportsScreenProps {
  onNavigateToScreen?: (screen: string) => void;
}

export const RecoveryReportsScreen: React.FC<RecoveryReportsScreenProps> = () => {
  const [report] = useState(DEV_AUDIT_REPORT);
  const [activeTab, setActiveTab] = useState<'EXECUTIVE' | 'COMPLIANCE' | 'BUYERS'>('EXECUTIVE');

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">
            <FileText className="w-4 h-4" />
            Demolition Material Audit Report (DMAR)
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">{report.report_title}</h2>
          <p className="text-xs text-slate-400">
            Certified pre-demolition compliance manifest synthesized from computer vision inventory and valuation models
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handlePrint}>
            <Printer className="w-4 h-4 mr-1.5" /> Print Manifest
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => alert('Downloading official DMAR compliance document (PDF)...')}
          >
            <Download className="w-4 h-4 mr-1.5" /> Download PDF Report
          </Button>
        </div>
      </div>

      {/* Audit Certificate Badge */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-950/60 to-slate-900 border border-emerald-900/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 flex-shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <span className="font-bold text-white text-sm block">EPA 70% C&D Waste Diversion Certified</span>
            <span className="text-slate-400 text-[11px]">
              Actual project diversion rate: <strong className="text-emerald-400">88.4%</strong> • Exceeds threshold requirements
            </span>
          </div>
        </div>

        <span className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
          Ref: DMAR-2026-CH-094
        </span>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4">
          <span className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider flex items-center gap-1">
            <Scale className="w-3.5 h-3.5 text-slate-400" /> Total Recoverable Mass
          </span>
          <div className="text-2xl font-bold text-white mt-1 font-mono">
            {formatTonnes(report.total_recoverable_tonnes)}
          </div>
          <span className="text-[11px] text-slate-400 mt-0.5 block">6 distinct deconstruction streams</span>
        </Card>

        <Card className="p-4">
          <span className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider flex items-center gap-1">
            <DollarSign className="w-3.5 h-3.5 text-emerald-400" /> Total Recovery Valuation
          </span>
          <div className="text-2xl font-bold text-emerald-400 mt-1 font-mono">
            {formatCurrency(report.total_estimated_value_usd)}
          </div>
          <span className="text-[11px] text-slate-400 mt-0.5 block">Secondary material market pricing</span>
        </Card>

        <Card className="p-4">
          <span className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider flex items-center gap-1">
            <Leaf className="w-3.5 h-3.5 text-emerald-400" /> Embodied Carbon Offsets
          </span>
          <div className="text-2xl font-bold text-teal-300 mt-1 font-mono">
            {formatCO2(report.total_carbon_offset_kg_co2e)}
          </div>
          <span className="text-[11px] text-slate-400 mt-0.5 block">Displacing virgin extraction emissions</span>
        </Card>
      </div>

      {/* Document View Tabs */}
      <Card>
        <CardHeader className="pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            {[
              { id: 'EXECUTIVE', label: 'Executive Synthesis' },
              { id: 'COMPLIANCE', label: 'Regulatory & Landfill Compliance' },
              { id: 'BUYERS', label: 'Off-Taker Matching Insights' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === tab.id
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent className="pt-5 space-y-4 text-xs text-slate-300">
          {activeTab === 'EXECUTIVE' && (
            <div className="space-y-4">
              <div className="flex items-center gap-1.5 text-emerald-400 font-semibold text-xs">
                <Sparkles className="w-4 h-4" /> Synthesized Demolition Engineering Analysis
              </div>
              <p className="leading-relaxed whitespace-pre-line text-slate-200">
                {report.executive_summary}
              </p>
            </div>
          )}

          {activeTab === 'COMPLIANCE' && (
            <div className="space-y-4">
              <div className="flex items-center gap-1.5 text-teal-400 font-semibold text-xs">
                <ShieldCheck className="w-4 h-4" /> Environmental Protection & Diversion Standards
              </div>
              <p className="leading-relaxed whitespace-pre-line text-slate-200">
                {report.regulatory_compliance_notes}
              </p>
            </div>
          )}

          {activeTab === 'BUYERS' && (
            <div className="space-y-4">
              <div className="flex items-center gap-1.5 text-blue-400 font-semibold text-xs">
                <Building2 className="w-4 h-4" /> Secondary Market Procurement Matching
              </div>
              <p className="leading-relaxed whitespace-pre-line text-slate-200">
                {report.buyer_matching_insights}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stream Summary Matrix */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Material Streams Audit Manifest</CardTitle>
          <CardDescription className="text-xs">
            Certified inventory breakdown per resource stream included in this report
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                  <th className="py-3 px-4">Material Category</th>
                  <th className="py-3 px-4">Recovered Mass</th>
                  <th className="py-3 px-4">Volume (m³)</th>
                  <th className="py-3 px-4">Estimated Market Value</th>
                  <th className="py-3 px-4">Embodied Carbon Offset</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {report.detailed_breakdown_json.map((cat: any) => (
                  <tr key={cat.category} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-white">{cat.category}</td>
                    <td className="py-3 px-4 font-mono font-semibold text-white">
                      {formatTonnes(cat.total_weight_tonnes)}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400">{cat.total_volume_m3} m³</td>
                    <td className="py-3 px-4 font-mono font-bold text-emerald-400">
                      {formatCurrency(cat.estimated_value_usd)}
                    </td>
                    <td className="py-3 px-4 font-mono text-emerald-300">
                      {formatCO2(cat.carbon_offset_kg_co2e)}
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
