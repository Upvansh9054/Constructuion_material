import React from 'react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  ShieldCheck,
  Sparkles,
  ArrowRight,
  Layers,
  DollarSign,
  Leaf,
  Scan,
  TrendingUp,
  Cpu,
  Building2,
  Boxes,
} from 'lucide-react';

interface LandingPageProps {
  onEnterApp: () => void;
  onGoToAuth: (mode?: 'login' | 'register') => void;
  onNavigateToScreen: (screen: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onEnterApp,
  onGoToAuth,
  onNavigateToScreen,
}) => {
  const categories = [
    {
      id: 'CONCRETE',
      name: '1. Concrete',
      spec: 'Structural precast slabs, foundation footings & crushed road aggregate base',
      density: '2.40 t/m³',
      carbonOffset: '130 kg CO₂e / t',
      color: 'border-zinc-700 bg-zinc-900/50',
    },
    {
      id: 'BRICKS',
      name: '2. Bricks',
      spec: 'Reclaimed architectural facing bricks, clay masonry & refractory blocks',
      density: '1.80 t/m³',
      carbonOffset: '240 kg CO₂e / t',
      color: 'border-amber-800/60 bg-amber-950/20',
    },
    {
      id: 'STEEL',
      name: '3. Steel',
      spec: 'Heavy I-beams (W-profiles), truss frames, corrugated cladding & rebar',
      density: '7.85 t/m³',
      carbonOffset: '1,800 kg CO₂e / t',
      color: 'border-blue-800/60 bg-blue-950/20',
    },
    {
      id: 'TIMBER',
      name: '4. Timber',
      spec: 'Hardwood roof framing, heavy Douglas fir beams & dimensional lumber',
      density: '0.65 t/m³',
      carbonOffset: '450 kg CO₂e / t',
      color: 'border-emerald-800/60 bg-emerald-950/20',
    },
    {
      id: 'GLASS',
      name: '5. Glass',
      spec: 'Commercial storefront facade sheets, double glazing & remelting cullet',
      density: '2.50 t/m³',
      carbonOffset: '350 kg CO₂e / t',
      color: 'border-cyan-800/60 bg-cyan-950/20',
    },
    {
      id: 'MIXED_DEBRIS',
      name: '6. Mixed Debris',
      spec: 'Inert masonry spall & plaster rubble screened for aggregate downcycling',
      density: '1.50 t/m³',
      carbonOffset: '50 kg CO₂e / t',
      color: 'border-slate-700 bg-slate-900/50',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-emerald-400 flex items-center justify-center shadow-lg shadow-emerald-900/40">
              <ShieldCheck className="w-5 h-5 text-slate-950" />
            </div>
            <div>
              <span className="font-bold text-base text-white tracking-tight">Demolition Intelligence</span>
              <span className="text-slate-500 text-xs block leading-none">Material Recovery AI</span>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-6 text-xs font-semibold text-slate-400">
            <button onClick={() => onNavigateToScreen('analysis')} className="hover:text-emerald-400 transition-colors">
              AI Vision Pipeline
            </button>
            <button onClick={() => onNavigateToScreen('inventory')} className="hover:text-emerald-400 transition-colors">
              Material Categories
            </button>
            <button onClick={() => onNavigateToScreen('marketplace')} className="hover:text-emerald-400 transition-colors">
              Recovery Market
            </button>
            <button onClick={() => onNavigateToScreen('reports')} className="hover:text-emerald-400 transition-colors">
              DMAR Compliance
            </button>
          </nav>

          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => onGoToAuth('login')}>
              Sign In
            </Button>
            <Button variant="primary" size="sm" onClick={onEnterApp}>
              Enter App <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 lg:py-28 px-6">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(16,185,129,0.15),rgba(255,255,255,0))]" />
        <div className="max-w-5xl mx-auto text-center relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-semibold tracking-wide">
            <Sparkles className="w-3.5 h-3.5" />
            Next-Gen Circular Construction & Demolition Intelligence
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-[1.1]">
            Turn Demolition Waste Into <br />
            <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
              Verified Circular Revenue
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Automate site material audits from drone orthophotos and site scans. Our computer vision pipeline detects
            concrete, bricks, steel, timber, and glass, calculates volumetric tonnage, evaluates secondary salvage
            value, and connects contractors with certified recyclers.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Button size="lg" variant="primary" onClick={onEnterApp} className="px-8 shadow-xl shadow-emerald-950/80">
              <Scan className="w-4 h-4 mr-2" /> Launch Demo Workspace
            </Button>
            <Button size="lg" variant="outline" onClick={() => onGoToAuth('register')} className="px-6">
              Create Contractor Account
            </Button>
          </div>
        </div>

        {/* Live KPI Ticker */}
        <div className="max-w-6xl mx-auto mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="space-y-1 text-center md:text-left">
            <div className="text-2xl lg:text-3xl font-extrabold text-white">1,124.3 t</div>
            <div className="text-xs text-slate-400 flex items-center justify-center md:justify-start gap-1">
              <Layers className="w-3 h-3 text-emerald-400" /> Recoverable Mass Identified
            </div>
          </div>
          <div className="space-y-1 text-center md:text-left">
            <div className="text-2xl lg:text-3xl font-extrabold text-emerald-400">$59,194 USD</div>
            <div className="text-xs text-slate-400 flex items-center justify-center md:justify-start gap-1">
              <DollarSign className="w-3 h-3 text-emerald-400" /> Active Site Recovery Value
            </div>
          </div>
          <div className="space-y-1 text-center md:text-left">
            <div className="text-2xl lg:text-3xl font-extrabold text-white">289.0 t CO₂e</div>
            <div className="text-xs text-slate-400 flex items-center justify-center md:justify-start gap-1">
              <Leaf className="w-3 h-3 text-emerald-400" /> Embodied Carbon Diverted
            </div>
          </div>
          <div className="space-y-1 text-center md:text-left">
            <div className="text-2xl lg:text-3xl font-extrabold text-teal-400">88.4%</div>
            <div className="text-xs text-slate-400 flex items-center justify-center md:justify-start gap-1">
              <TrendingUp className="w-3 h-3 text-emerald-400" /> EPA Landfill Diversion Rate
            </div>
          </div>
        </div>
      </section>

      {/* The 6 Material Streams Section */}
      <section className="py-16 px-6 max-w-7xl mx-auto w-full">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <Badge variant="outline" className="mb-2 text-emerald-400 border-emerald-500/30">
              Core Material Stream Coverage
            </Badge>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Classified According to CIRIA & EPA Guidelines
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Trained deep learning YOLO models classify, segment, and assess volumetric bulk density for the 6
              primary commercial demolition waste streams.
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={() => onNavigateToScreen('inventory')}>
            Explore Material Inventory <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.map((cat) => (
            <div
              key={cat.id}
              className={`p-5 rounded-xl border ${cat.color} backdrop-blur-sm space-y-3 transition-all hover:scale-[1.01]`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-white">{cat.name}</span>
                <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                  {cat.density}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{cat.spec}</p>
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <span className="text-slate-500">ICE Carbon Credit:</span>
                <span className="text-emerald-400 font-semibold">{cat.carbonOffset}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 4-Step Technical Workflow */}
      <section className="py-16 px-6 border-t border-slate-800/60 bg-slate-900/30">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold text-white">Automated Demolition Intelligence Workflow</h2>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              From drone flight to secondary buyer sale in four automated steps.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <Scan className="w-5 h-5" />
              </div>
              <div className="text-xs font-bold text-slate-500 uppercase">Step 01</div>
              <h3 className="font-bold text-white text-sm">Site Imagery Ingestion</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Direct presigned upload of high-res orthomosaics, handheld phone photos, and structural plans to S3 storage.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <Cpu className="w-5 h-5" />
              </div>
              <div className="text-xs font-bold text-slate-500 uppercase">Step 02</div>
              <h3 className="font-bold text-white text-sm">AI Material Segmentation</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Decoupled PyTorch & YOLOv8 model runs inference to identify materials, bounding boxes, and surface condition wear.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <Boxes className="w-5 h-5" />
              </div>
              <div className="text-xs font-bold text-slate-500 uppercase">Step 03</div>
              <h3 className="font-bold text-white text-sm">Volumetric & Carbon Audit</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Density formulas convert pixel bounding boxes to metric tonnes, evaluating market valuation and embodied CO₂e.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
                <Building2 className="w-5 h-5" />
              </div>
              <div className="text-xs font-bold text-slate-500 uppercase">Step 04</div>
              <h3 className="font-bold text-white text-sm">Marketplace & DMAR Report</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Generate official EPA-compliant compliance PDFs and list salvageable lots to certified regional buyers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-10 px-6 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span className="font-semibold text-slate-400">Demolition Intelligence & Material Recovery</span>
            <span>• v0.1.0 Enterprise</span>
          </div>
          <div>Circular Economy Architecture adhering to EPA C&D and CIRIA Guidelines</div>
        </div>
      </footer>
    </div>
  );
};
