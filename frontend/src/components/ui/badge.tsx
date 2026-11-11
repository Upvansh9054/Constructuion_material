import React from 'react';
import { cn } from '../../lib/utils';
import { ConditionGrade, MaterialCategory } from '../../types/material';

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'destructive' | 'outline' | 'category' | 'condition';
  category?: MaterialCategory;
  condition?: ConditionGrade;
}

const categoryStyles: Record<MaterialCategory, string> = {
  CONCRETE: 'bg-zinc-700/50 text-zinc-200 border-zinc-600',
  BRICKS: 'bg-amber-900/40 text-amber-300 border-amber-700/50',
  STEEL: 'bg-blue-900/40 text-blue-300 border-blue-700/50',
  TIMBER: 'bg-emerald-950/60 text-emerald-300 border-emerald-800/50',
  GLASS: 'bg-cyan-900/40 text-cyan-300 border-cyan-700/50',
  MIXED_DEBRIS: 'bg-neutral-800 text-neutral-300 border-neutral-700',
};

const conditionStyles: Record<ConditionGrade, string> = {
  REUSABLE_EXCELLENT: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  REUSABLE_GOOD: 'bg-lime-500/20 text-lime-400 border-lime-500/30',
  RECYCLABLE: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  DOWN_CYCLE_ONLY: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  HAZARDOUS_CONTAMINATED: 'bg-rose-500/20 text-rose-400 border-rose-500/30 animate-pulse',
};

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  category,
  condition,
  children,
  ...props
}) => {
  let style = 'bg-slate-800 text-slate-300 border-slate-700';

  if (category) {
    style = categoryStyles[category] || style;
  } else if (condition) {
    style = conditionStyles[condition] || style;
  } else {
    switch (variant) {
      case 'success':
        style = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
        break;
      case 'warning':
        style = 'bg-amber-500/20 text-amber-400 border-amber-500/30';
        break;
      case 'destructive':
        style = 'bg-rose-500/20 text-rose-400 border-rose-500/30';
        break;
      case 'outline':
        style = 'border-slate-700 text-slate-300 bg-transparent';
        break;
    }
  }

  return (
    <div
      className={cn(
        'inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold tracking-wide transition-colors',
        style,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
