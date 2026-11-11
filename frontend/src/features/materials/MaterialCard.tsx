import React from 'react';
import { Card } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { MaterialItem } from '../../types/material';
import { formatCurrency, formatTonnes, formatCO2 } from '../../lib/utils';
import { CheckCircle2, AlertTriangle, Scale, DollarSign, Leaf } from 'lucide-react';

interface MaterialCardProps {
  item: MaterialItem;
  onVerify?: (item: MaterialItem) => void;
}

export const MaterialCard: React.FC<MaterialCardProps> = ({ item, onVerify }) => {
  return (
    <Card className="hover:border-slate-700 transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-2">
          <Badge category={item.category}>{item.category.replace('_', ' ')}</Badge>
          <Badge condition={item.condition_grade}>
            {item.condition_grade.replace(/_/g, ' ')}
          </Badge>
        </div>

        <div className="mt-3">
          <h4 className="text-base font-semibold text-white">
            {item.subcategory || item.category}
          </h4>
          {item.description && (
            <p className="text-xs text-slate-400 mt-1 line-clamp-2">{item.description}</p>
          )}
        </div>

        {item.contamination_risk && (
          <div className="mt-2.5 flex items-center gap-1.5 p-2 rounded-md bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate">{item.contamination_risk}</span>
          </div>
        )}

        <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
          <div className="p-2 rounded bg-slate-800/60 border border-slate-800">
            <div className="flex items-center gap-1 text-slate-400 text-[10px] uppercase font-semibold">
              <Scale className="w-3 h-3 text-slate-400" />
              Weight
            </div>
            <div className="font-bold text-slate-100 mt-0.5">
              {formatTonnes(item.estimated_weight_tonnes)}
            </div>
          </div>

          <div className="p-2 rounded bg-slate-800/60 border border-slate-800">
            <div className="flex items-center gap-1 text-slate-400 text-[10px] uppercase font-semibold">
              <DollarSign className="w-3 h-3 text-emerald-400" />
              Est. Value
            </div>
            <div className="font-bold text-emerald-400 mt-0.5">
              {formatCurrency(item.estimated_market_value_usd)}
            </div>
          </div>
        </div>

        <div className="mt-2 flex items-center justify-between text-xs px-2 py-1.5 rounded bg-emerald-950/20 border border-emerald-900/30 text-emerald-300">
          <div className="flex items-center gap-1">
            <Leaf className="w-3.5 h-3.5 text-emerald-400" />
            <span>Offset:</span>
          </div>
          <span className="font-semibold">{formatCO2(item.embodied_carbon_offset_kg)}</span>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
        <div className="flex items-center gap-1 text-slate-400">
          {item.confidence_score && (
            <span>Conf: {Math.round(item.confidence_score * 100)}%</span>
          )}
        </div>

        {item.is_verified_by_surveyor ? (
          <div className="flex items-center gap-1 text-emerald-400 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Verified</span>
          </div>
        ) : (
          <button
            onClick={() => onVerify?.(item)}
            className="text-xs text-slate-400 hover:text-white underline underline-offset-2"
          >
            Review & Verify
          </button>
        )}
      </div>
    </Card>
  );
};

