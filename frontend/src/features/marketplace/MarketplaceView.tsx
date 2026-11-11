import React from 'react';
import { Card } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { MarketplaceListing } from '../../types/marketplace';
import { formatCurrency, formatTonnes } from '../../lib/utils';
import { ShoppingBag, MapPin, Truck } from 'lucide-react';

interface MarketplaceViewProps {
  listings: MarketplaceListing[];
}

export const MarketplaceView: React.FC<MarketplaceViewProps> = ({ listings }) => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Secondary Material Marketplace</h2>
          <p className="text-xs text-slate-400">
            Directly connect demolition contractors with material buyers, precast manufacturers, and recycling yards
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {listings.map((listing) => (
          <Card key={listing.id} className="flex flex-col justify-between hover:border-slate-700 transition-all">
            <div>
              <div className="flex items-center justify-between">
                <Badge variant={listing.status === 'ACTIVE' ? 'success' : 'outline'}>
                  {listing.status}
                </Badge>
                <span className="text-xs font-bold text-emerald-400">
                  {formatCurrency(listing.price_per_tonne_usd)} / t
                </span>
              </div>

              <h4 className="text-base font-semibold text-white mt-3">{listing.title}</h4>
              <p className="text-xs text-slate-400 mt-1 line-clamp-2">{listing.description}</p>

              <div className="mt-4 space-y-2 text-xs">
                <div className="flex items-center justify-between p-2 rounded bg-slate-800/60">
                  <span className="text-slate-400">Available Mass:</span>
                  <span className="font-semibold text-white">{formatTonnes(listing.available_tonnes)}</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-slate-800/60">
                  <span className="text-slate-400">Total Lot Price:</span>
                  <span className="font-bold text-emerald-400">{formatCurrency(listing.total_price_usd)}</span>
                </div>

                <div className="flex items-center gap-1.5 text-slate-400 pt-1">
                  <MapPin className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                  <span className="truncate">{listing.pickup_city} • {listing.pickup_address}</span>
                </div>

                {listing.logistics_notes && (
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Truck className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                    <span className="truncate">{listing.logistics_notes}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-800 flex items-center gap-2">
              <Button size="sm" className="w-full">
                <ShoppingBag className="w-3.5 h-3.5" />
                Contact Seller / Bid
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
