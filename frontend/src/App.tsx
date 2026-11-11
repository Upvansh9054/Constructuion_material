import React, { useState } from 'react';
import { PageLayout } from './components/layout/PageLayout';
import { NavTab } from './components/layout/Sidebar';
import { DashboardOverview } from './features/dashboard/DashboardOverview';
import { MaterialList } from './features/materials/MaterialList';
import { SurveyUpload } from './features/surveys/SurveyUpload';
import { MarketplaceView } from './features/marketplace/MarketplaceView';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { MaterialItem, ValuationSummary } from './types/material';
import { MarketplaceListing } from './types/marketplace';
import { Sparkles, Download, FileText, CheckCircle2 } from 'lucide-react';

// Baseline demonstration dataset showcasing the 6 material streams
const INITIAL_MATERIALS: MaterialItem[] = [
  {
    id: 'mat-001',
    survey_id: 'srv-001',
    category: 'STEEL',
    subcategory: 'Structural I-Beams (W14x90)',
    description: 'Clean structural steel columns and rafters extracted from warehouse mezzanine.',
    condition_grade: 'REUSABLE_EXCELLENT',
    estimated_volume_m3: 12.5,
    estimated_weight_tonnes: 98.1,
    unit_count: 24,
    confidence_score: 0.94,
    estimated_market_value_usd: 31392.0,
    embodied_carbon_offset_kg: 176580.0,
    is_verified_by_surveyor: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'mat-002',
    survey_id: 'srv-001',
    category: 'BRICKS',
    subcategory: 'Reclaimed Red Clay Facing Bricks',
    description: '1940s vintage solid clay masonry with lime mortar; easy cleaning potential.',
    condition_grade: 'REUSABLE_EXCELLENT',
    estimated_volume_m3: 35.0,
    estimated_weight_tonnes: 63.0,
    unit_count: 21000,
    confidence_score: 0.89,
    estimated_market_value_usd: 11088.0,
    embodied_carbon_offset_kg: 18144.0,
    is_verified_by_surveyor: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'mat-003',
    survey_id: 'srv-001',
    category: 'CONCRETE',
    subcategory: 'Precast Floor Slabs & Foundation Piers',
    description: 'High-strength structural concrete suitable for mobile aggregate crushing on-site.',
    condition_grade: 'RECYCLABLE',
    estimated_volume_m3: 320.0,
    estimated_weight_tonnes: 768.0,
    confidence_score: 0.91,
    estimated_market_value_usd: 11750.4,
    embodied_carbon_offset_kg: 79872.0,
    is_verified_by_surveyor: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'mat-004',
    survey_id: 'srv-001',
    category: 'TIMBER',
    subcategory: 'Heavy Douglas Fir Roof Trusses',
    description: 'Structural timber framing, dry and free of rot; nails require extraction.',
    condition_grade: 'REUSABLE_GOOD',
    estimated_volume_m3: 28.0,
    estimated_weight_tonnes: 18.2,
    unit_count: 16,
    confidence_score: 0.86,
    estimated_market_value_usd: 3976.7,
    embodied_carbon_offset_kg: 8190.0,
    is_verified_by_surveyor: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'mat-005',
    survey_id: 'srv-001',
    category: 'GLASS',
    subcategory: 'Commercial Double Glazing Panes',
    description: 'Large architectural facade sheets; suitable for specialized cullet remelting.',
    condition_grade: 'RECYCLABLE',
    estimated_volume_m3: 4.8,
    estimated_weight_tonnes: 12.0,
    confidence_score: 0.83,
    estimated_market_value_usd: 459.0,
    embodied_carbon_offset_kg: 3360.0,
    is_verified_by_surveyor: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'mat-006',
    survey_id: 'srv-001',
    category: 'MIXED_DEBRIS',
    subcategory: 'Dry Demolition Rubble & Masonry Spall',
    description: 'Inert mixed rubble; mechanical sorting and screening required prior to road base downcycling.',
    condition_grade: 'DOWN_CYCLE_ONLY',
    estimated_volume_m3: 110.0,
    estimated_weight_tonnes: 165.0,
    confidence_score: 0.78,
    estimated_market_value_usd: 528.0,
    embodied_carbon_offset_kg: 2887.5,
    is_verified_by_surveyor: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const INITIAL_LISTINGS: MarketplaceListing[] = [
  {
    id: 'list-001',
    material_item_id: 'mat-001',
    seller_id: 'usr-demo-contractor',
    title: '98 Tonnes Structural Steel I-Beams (W14x90)',
    description: 'Salvaged and unbolted structural beams in excellent condition. Stored under dry tarps.',
    available_tonnes: 98.1,
    min_order_tonnes: 10.0,
    price_per_tonne_usd: 320.0,
    total_price_usd: 31392.0,
    pickup_address: '450 Demolition Way, Sector B',
    pickup_city: 'Chicago, IL',
    logistics_notes: 'Crane loading assistance available on-site through next Friday.',
    status: 'ACTIVE',
    listed_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'list-002',
    material_item_id: 'mat-002',
    seller_id: 'usr-demo-contractor',
    title: '21,000 Cleaned Reclaimed Red Clay Facing Bricks',
    description: 'Historical vintage brick lot. Palletized and shrink-wrapped for freight transport.',
    available_tonnes: 63.0,
    min_order_tonnes: 5.0,
    price_per_tonne_usd: 176.0,
    total_price_usd: 11088.0,
    pickup_address: '450 Demolition Way, Sector B',
    pickup_city: 'Chicago, IL',
    logistics_notes: 'Forklift loading onto flatbed trailers.',
    status: 'ACTIVE',
    listed_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [materials, setMaterials] = useState<MaterialItem[]>(INITIAL_MATERIALS);
  const [listings] = useState<MarketplaceListing[]>(INITIAL_LISTINGS);

  const calculateSummary = (): ValuationSummary => {
    const catMap: Record<string, any> = {};
    for (const m of materials) {
      if (!catMap[m.category]) {
        catMap[m.category] = {
          category: m.category,
          total_volume_m3: 0,
          total_weight_tonnes: 0,
          estimated_value_usd: 0,
          carbon_offset_kg_co2e: 0,
          item_count: 0,
        };
      }
      catMap[m.category].total_volume_m3 += m.estimated_volume_m3;
      catMap[m.category].total_weight_tonnes += m.estimated_weight_tonnes;
      catMap[m.category].estimated_value_usd += m.estimated_market_value_usd;
      catMap[m.category].carbon_offset_kg_co2e += m.embodied_carbon_offset_kg;
      catMap[m.category].item_count += 1;
    }

    const categories = Object.values(catMap);
    return {
      total_estimated_value_usd: categories.reduce((sum, c) => sum + c.estimated_value_usd, 0),
      total_recoverable_tonnes: categories.reduce((sum, c) => sum + c.total_weight_tonnes, 0),
      total_carbon_offset_kg_co2e: categories.reduce((sum, c) => sum + c.carbon_offset_kg_co2e, 0),
      categories,
    };
  };

  const handleVerifyItem = (item: MaterialItem) => {
    setMaterials(prev =>
      prev.map(m => (m.id === item.id ? { ...m, is_verified_by_surveyor: true } : m))
    );
  };

  return (
    <PageLayout activeTab={activeTab} onSelectTab={setActiveTab}>
      {activeTab === 'dashboard' && (
        <DashboardOverview
          summary={calculateSummary()}
          onNavigateToSurveys={() => setActiveTab('surveys')}
          onTriggerAnalysis={() => setActiveTab('materials')}
        />
      )}

      {activeTab === 'materials' && (
        <MaterialList items={materials} onVerifyItem={handleVerifyItem} />
      )}

      {activeTab === 'surveys' && (
        <SurveyUpload onUploadSuccess={() => setActiveTab('materials')} />
      )}

      {activeTab === 'marketplace' && (
        <MarketplaceView listings={listings} />
      )}

      {activeTab === 'reports' && (
        <div className="space-y-6 max-w-4xl mx-auto">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Demolition Material Audit Report (DMAR)</CardTitle>
                  <CardDescription>
                    Automated circular compliance report generated via OpenAI & Computer Vision Inventory
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4" />
                  Download PDF
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6 text-sm text-slate-300">
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4" />
                  Executive Synthesis
                </div>
                <p className="text-slate-200 leading-relaxed">
                  Pre-demolition visual audit completed for <strong>Metro Logistics Center (Phase 2)</strong>.
                  Analysis of 48 inspection frames identified <strong>1,124.3 metric tonnes</strong> of recyclable
                  and reusable material streams. Structural steel salvage (98.1 t) and architectural brick
                  recovery (63.0 t) represent the highest financial yield at an estimated recovery valuation
                  of <strong>$59,194.10 USD</strong>.
                </p>
                <p className="text-slate-400 text-xs">
                  Diversion of these streams from regional landfills offsets an estimated{' '}
                  <strong className="text-emerald-300">289.0 t CO₂e</strong> in embodied emissions.
                </p>
              </div>

              <div className="space-y-2">
                <h4 className="font-semibold text-white">Regulatory Compliance & Landfill Diversion</h4>
                <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 text-xs text-slate-300 space-y-1.5">
                  <div className="flex items-center gap-2 text-emerald-400 font-medium">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Meets EPA 70% C&D Waste Diversion Threshold (Current: 88.4%)</span>
                  </div>
                  <p className="text-slate-400 pl-6">
                    Mandatory pre-demolition asbestos survey clear for structural mezzanine; all wood rafter
                    elements approved for architectural salvage yards.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'sites' && (
        <Card className="p-8 text-center">
          <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-white">Site Management Module</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
            Browse registered demolition sites, view contractor assignments, and manage project lifecycles.
          </p>
        </Card>
      )}
    </PageLayout>
  );
};
