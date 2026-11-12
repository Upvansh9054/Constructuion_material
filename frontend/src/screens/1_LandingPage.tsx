import React from 'react';
import { Button } from '../components/ui/button';
import { ShieldCheck, Sparkles, ArrowRight } from 'lucide-react';

interface LandingPageProps {
  onEnterApp: () => void;
  onGoToAuth: (mode?: 'login' | 'register') => void;
  onNavigateToScreen: (screen: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onEnterApp,
  onGoToAuth,
}) => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white justify-between">
      {/* Top Header */}
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

          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => onGoToAuth('login')}>
              Sign In
            </Button>
            <Button variant="primary" size="sm" onClick={onEnterApp}>
              Enter Workspace <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </div>
        </div>
      </header>

      {/* Clean Minimal Hero Section */}
      <section className="relative overflow-hidden py-24 lg:py-36 px-6 flex-1 flex items-center justify-center">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(16,185,129,0.15),rgba(255,255,255,0))]" />
        <div className="max-w-4xl mx-auto text-center relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-semibold tracking-wide">
            <Sparkles className="w-3.5 h-3.5" />
            Next-Gen Circular Construction & Demolition Intelligence
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-[1.15]">
            Turn Demolition Waste Into <br />
            <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
              Verified Circular Revenue
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
            AI-driven computer vision and certified material recovery for licensed surveyors, demolition contractors, and secondary market off-takers.
          </p>

          <div className="pt-4">
            <Button size="lg" variant="primary" onClick={onEnterApp} className="px-8 shadow-xl shadow-emerald-950/80 text-sm font-semibold">
              Enter Demolition Workspace <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {/* Clean Minimal Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/80 py-6 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span className="font-semibold text-slate-400">Demolition Intelligence</span>
            <span>• Circular Material Recovery Architecture</span>
          </div>
          <div>EPA C&D and CIRIA Guidelines Compliant</div>
        </div>
      </footer>
    </div>
  );
};
