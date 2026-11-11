import React from 'react';
import { MaterialCategory } from '../../types/material';
import { cn } from '../../lib/utils';

interface CategoryFilterProps {
  selectedCategory: MaterialCategory | 'ALL';
  onSelectCategory: (category: MaterialCategory | 'ALL') => void;
}

const CATEGORIES: { id: MaterialCategory | 'ALL'; label: string }[] = [
  { id: 'ALL', label: 'All Categories' },
  { id: 'CONCRETE', label: '1. Concrete' },
  { id: 'BRICKS', label: '2. Bricks' },
  { id: 'STEEL', label: '3. Steel' },
  { id: 'TIMBER', label: '4. Timber' },
  { id: 'GLASS', label: '5. Glass' },
  { id: 'MIXED_DEBRIS', label: '6. Mixed Debris' },
];

export const CategoryFilter: React.FC<CategoryFilterProps> = ({
  selectedCategory,
  onSelectCategory,
}) => {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
      {CATEGORIES.map((cat) => {
        const isSelected = selectedCategory === cat.id;
        return (
          <button
            key={cat.id}
            onClick={() => onSelectCategory(cat.id)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all',
              isSelected
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-950/40'
                : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            )}
          >
            {cat.label}
          </button>
        );
      })}
    </div>
  );
};
