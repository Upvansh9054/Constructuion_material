import React, { useState } from 'react';
import { MaterialItem, MaterialCategory } from '../../types/material';
import { MaterialCard } from './MaterialCard';
import { CategoryFilter } from './CategoryFilter';
import { Layers } from 'lucide-react';

interface MaterialListProps {
  items: MaterialItem[];
  onVerifyItem?: (item: MaterialItem) => void;
}

export const MaterialList: React.FC<MaterialListProps> = ({ items, onVerifyItem }) => {
  const [selectedCategory, setSelectedCategory] = useState<MaterialCategory | 'ALL'>('ALL');

  const filteredItems = items.filter((it) => {
    if (selectedCategory === 'ALL') return true;
    return it.category === selectedCategory;
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-bold text-white">Recoverable Material Streams</h3>
          <p className="text-xs text-slate-400">
            Detected via computer vision and volumetric scanning across survey images
          </p>
        </div>
      </div>

      <CategoryFilter
        selectedCategory={selectedCategory}
        onSelectCategory={setSelectedCategory}
      />

      {filteredItems.length === 0 ? (
        <div className="p-12 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30">
          <Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-slate-300">No material items match this category</h4>
          <p className="text-xs text-slate-500 mt-1">
            Upload site survey imagery to trigger the YOLO detection & estimation pipeline.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map((item) => (
            <MaterialCard key={item.id} item={item} onVerify={onVerifyItem} />
          ))}
        </div>
      )}
    </div>
  );
};

