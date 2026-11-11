import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { DEV_DETECTION_FRAMES, DetectionFrame } from '../mock/fixtures';
import { formatTonnes } from '../lib/utils';
import {
  Cpu,
  Sliders,
  AlertTriangle,
  ArrowRight,
  Scan,
  RefreshCw,
  Eye,
  EyeOff,
} from 'lucide-react';

interface AiAnalysisScreenProps {
  onProceedToInventory: () => void;
  onNavigateToScreen: (screen: string) => void;
}

export const AiAnalysisScreen: React.FC<AiAnalysisScreenProps> = ({
  onProceedToInventory,
  onNavigateToScreen,
}) => {
  const [frames] = useState<DetectionFrame[]>(DEV_DETECTION_FRAMES);
  const [selectedFrameIndex, setSelectedFrameIndex] = useState(0);
  const [confThreshold, setConfThreshold] = useState<number>(0.75);
  const [selectedDetectionId, setSelectedDetectionId] = useState<string | null>('det-1');
  const [showBoxes, setShowBoxes] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');

  const currentFrame = frames[selectedFrameIndex] || frames[0];

  const visibleDetections = currentFrame.detections.filter((d) => {
    const passesConf = d.confidence >= confThreshold;
    const passesCat = categoryFilter === 'ALL' || d.category === categoryFilter;
    return passesConf && passesCat;
  });

  const activeDetection = currentFrame.detections.find((d) => d.id === selectedDetectionId);

  const categoryColors: Record<string, { border: string; bg: string; text: string; fill: string }> = {
    STEEL: { border: 'border-blue-500', bg: 'bg-blue-500/20', text: 'text-blue-300', fill: '#3b82f6' },
    BRICKS: { border: 'border-amber-500', bg: 'bg-amber-500/20', text: 'text-amber-300', fill: '#f59e0b' },
    CONCRETE: { border: 'border-zinc-400', bg: 'bg-zinc-400/20', text: 'text-zinc-200', fill: '#a1a1aa' },
    TIMBER: { border: 'border-emerald-500', bg: 'bg-emerald-500/20', text: 'text-emerald-300', fill: '#10b981' },
    GLASS: { border: 'border-cyan-400', bg: 'bg-cyan-400/20', text: 'text-cyan-300', fill: '#22d3ee' },
    MIXED_DEBRIS: { border: 'border-slate-500', bg: 'bg-slate-500/20', text: 'text-slate-300', fill: '#64748b' },
  };

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">
            <Cpu className="w-4 h-4" />
            AI Computer Vision Inference Engine
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Material Detection & Volumetric Localization
          </h2>
          <p className="text-xs text-slate-400">
            Real-time visual inference bounding boxes, condition grading, and spatial mass mapping
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button variant="outline" size="sm" onClick={() => onNavigateToScreen('upload')}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Re-Scan Image
          </Button>
          <Button variant="primary" size="sm" onClick={onProceedToInventory}>
            Transfer to Inventory <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Button>
        </div>
      </div>

      {/* Model Telemetry Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300">
        <div>
          <span className="text-slate-500 block text-[10px] uppercase font-semibold">Active Model</span>
          <span className="font-mono text-emerald-400 font-semibold">YOLOv8x-Demolition-v1.2</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase font-semibold">Inference Device</span>
          <span className="font-mono text-white">NVIDIA TensorRT / CUDA</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase font-semibold">Batch Latency</span>
          <span className="font-mono text-white">32.4 ms / tile</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase font-semibold">Tiling Strategy</span>
          <span className="font-mono text-white">SAHI Sliced (1280px tiles)</span>
        </div>
      </div>

      {/* Main Visualizer & Inspector Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Detection Viewport (2 Cols) */}
        <div className="lg:col-span-2 space-y-3">
          {/* Viewport Control Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Sliders className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-400">Confidence:</span>
                <span className="font-mono font-bold text-emerald-400">{Math.round(confThreshold * 100)}%</span>
                <input
                  type="range"
                  min="0.4"
                  max="0.95"
                  step="0.05"
                  value={confThreshold}
                  onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                  className="w-20 accent-emerald-500 ml-1 cursor-pointer"
                />
              </div>

              <button
                onClick={() => setShowBoxes(!showBoxes)}
                className="flex items-center gap-1 text-slate-400 hover:text-white"
              >
                {showBoxes ? <Eye className="w-3.5 h-3.5 text-emerald-400" /> : <EyeOff className="w-3.5 h-3.5" />}
                <span>{showBoxes ? 'Visible' : 'Hidden'}</span>
              </button>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="rounded bg-slate-950 border border-slate-800 px-2 py-0.5 text-[11px] text-slate-300"
              >
                <option value="ALL">All Categories</option>
                <option value="STEEL">Steel</option>
                <option value="CONCRETE">Concrete</option>
                <option value="BRICKS">Bricks</option>
                <option value="TIMBER">Timber</option>
                <option value="GLASS">Glass</option>
                <option value="MIXED_DEBRIS">Mixed Debris</option>
              </select>

              <div className="flex items-center gap-1">
                <span className="text-[11px] text-slate-500">Frame:</span>
                {frames.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedFrameIndex(idx)}
                    className={`px-2 py-0.5 rounded text-[11px] font-mono font-semibold ${
                      selectedFrameIndex === idx ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    #{idx + 1}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Canvas Viewport with Bounding Boxes */}
          <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl aspect-[16/10] max-h-[520px]">
            <img
              src={currentFrame.image_url}
              alt="Site Drone Orthomosaic"
              className="w-full h-full object-cover"
            />

            {/* Simulated Bounding Box Overlay */}
            {showBoxes &&
              visibleDetections.map((det) => {
                const color = categoryColors[det.category] || categoryColors.MIXED_DEBRIS;
                const isSelected = selectedDetectionId === det.id;

                const left = `${det.box.x_min * 100}%`;
                const top = `${det.box.y_min * 100}%`;
                const width = `${(det.box.x_max - det.box.x_min) * 100}%`;
                const height = `${(det.box.y_max - det.box.y_min) * 100}%`;

                return (
                  <div
                    key={det.id}
                    onClick={() => setSelectedDetectionId(det.id)}
                    style={{ left, top, width, height }}
                    className={`absolute cursor-pointer border-2 transition-all group ${
                      isSelected
                        ? `${color.border} bg-emerald-500/10 ring-2 ring-white/50 z-20`
                        : `${color.border} bg-black/10 hover:bg-black/20 z-10`
                    }`}
                  >
                    {/* Bounding Box Chip */}
                    <div
                      className={`absolute -top-6 left-0 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider whitespace-nowrap shadow-md flex items-center gap-1 ${
                        isSelected ? 'bg-white text-slate-950' : 'bg-slate-950/90 text-white border border-slate-700'
                      }`}
                    >
                      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color.fill }} />
                      <span>{det.category}</span>
                      <span className="text-emerald-400 font-mono">{Math.round(det.confidence * 100)}%</span>
                    </div>
                  </div>
                );
              })}

            {/* Bottom Overlay Info */}
            <div className="absolute bottom-3 left-3 px-3 py-1.5 rounded-lg bg-slate-950/80 backdrop-blur-md border border-slate-800 text-[11px] text-slate-400 flex items-center gap-2">
              <Scan className="w-3.5 h-3.5 text-emerald-400" />
              <span>Camera Source: {currentFrame.camera_source.replace(/_/g, ' ')}</span>
              <span>•</span>
              <span className="text-white font-semibold">{visibleDetections.length} material items localized</span>
            </div>
          </div>
        </div>

        {/* Selected Detection Inspector (1 Col) */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Detection Inspector</CardTitle>
                {activeDetection && <Badge category={activeDetection.category}>{activeDetection.category}</Badge>}
              </div>
              <CardDescription className="text-xs">
                Spatial metrics, physical volume, and safety grading
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {activeDetection ? (
                <>
                  <div>
                    <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                      Classification
                    </span>
                    <h3 className="text-base font-bold text-white mt-0.5">{activeDetection.subcategory}</h3>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold block">Confidence</span>
                      <span className="text-lg font-bold text-emerald-400 font-mono">
                        {Math.round(activeDetection.confidence * 100)}%
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold block">Estimated Mass</span>
                      <span className="text-lg font-bold text-white font-mono">
                        {formatTonnes(activeDetection.estimated_tonnes)}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1.5 text-xs">
                    <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                      <span className="text-slate-400">Condition Grade:</span>
                      <Badge condition={activeDetection.condition}>{activeDetection.condition.replace(/_/g, ' ')}</Badge>
                    </div>

                    <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                      <span className="text-slate-400">Bounding Coordinates:</span>
                      <span className="font-mono text-slate-300 text-[11px]">
                        [{activeDetection.box.x_min}, {activeDetection.box.y_min}, {activeDetection.box.x_max},{' '}
                        {activeDetection.box.y_max}]
                      </span>
                    </div>
                  </div>

                  {activeDetection.hazard_risk && (
                    <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold block">Contamination Risk</span>
                        <span className="text-[11px] text-rose-200">{activeDetection.hazard_risk}</span>
                      </div>
                    </div>
                  )}

                  <div className="pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full text-xs"
                      onClick={() => onNavigateToScreen('assessment')}
                    >
                      Calibrate Volume & Condition →
                    </Button>
                  </div>
                </>
              ) : (
                <div className="py-8 text-center text-xs text-slate-500">
                  Click any bounding box on the image canvas to inspect volumetric properties and grading.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
