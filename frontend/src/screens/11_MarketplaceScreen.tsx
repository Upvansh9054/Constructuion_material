import React, { useState } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select } from '../components/ui/select';
import { Dialog, DialogFooter } from '../components/ui/dialog';
import { MarketplaceListing } from '../types/marketplace';
import { MaterialItem } from '../types/material';
import { formatCurrency, formatTonnes } from '../lib/utils';
import {
  ShoppingBag,
  Search,
  MapPin,
  Truck,
  PlusCircle,
  CheckCircle2,
} from 'lucide-react';

interface MarketplaceScreenProps {
  listings: MarketplaceListing[];
  materials: MaterialItem[];
  onCreateListing: (newListing: MarketplaceListing) => void;
  onNavigateToScreen: (screen: string) => void;
}

export const MarketplaceScreen: React.FC<MarketplaceScreenProps> = ({
  listings,
  materials,
  onCreateListing,
  onNavigateToScreen,
}) => {
  const [search, setSearch] = useState('');
  const [cityFilter, setCityFilter] = useState('ALL');
  const [activeBidModal, setActiveBidModal] = useState<MarketplaceListing | null>(null);
  const [isPublishModalOpen, setIsPublishModalOpen] = useState(false);

  // Bid form state
  const [bidQuantityTonnes, setBidQuantityTonnes] = useState('10');
  const [bidPricePerTonne, setBidPricePerTonne] = useState('320');
  const [haulageType, setHaulageType] = useState('FLATBED_TRAILER');
  const [bidSuccessMessage, setBidSuccessMessage] = useState(false);

  // New Listing form state
  const [selectedMaterialId, setSelectedMaterialId] = useState(materials[0]?.id || '');
  const [listingTitle, setListingTitle] = useState('');
  const [listingPrice, setListingPrice] = useState('280');
  const [listingMinOrder, setListingMinOrder] = useState('5');
  const [listingAddress, setListingAddress] = useState('450 Demolition Way, Sector B');
  const [listingCity, setListingCity] = useState('Chicago, IL');
  const [listingLogistics, setListingLogistics] = useState('Crane loading on site. Flatbed pickup.');

  const filteredListings = listings.filter((l) => {
    const matchesSearch =
      l.title.toLowerCase().includes(search.toLowerCase()) ||
      l.pickup_city.toLowerCase().includes(search.toLowerCase());
    const matchesCity = cityFilter === 'ALL' || l.pickup_city.includes(cityFilter);
    return matchesSearch && matchesCity;
  });

  const handlePublishListing = (e: React.FormEvent) => {
    e.preventDefault();
    const item = materials.find((m) => m.id === selectedMaterialId);
    if (!item) return;

    const tonnes = item.estimated_weight_tonnes;
    const price = parseFloat(listingPrice) || 200;

    const newListing: MarketplaceListing = {
      id: `list-${Date.now().toString().slice(-4)}`,
      material_item_id: item.id,
      seller_id: 'usr-contractor-01',
      title: listingTitle || `${formatTonnes(tonnes)} ${item.subcategory || item.category}`,
      description: item.description,
      available_tonnes: tonnes,
      min_order_tonnes: parseFloat(listingMinOrder) || 1,
      price_per_tonne_usd: price,
      total_price_usd: Math.round(tonnes * price),
      pickup_address: listingAddress,
      pickup_city: listingCity,
      logistics_notes: listingLogistics,
      status: 'ACTIVE',
      listed_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    onCreateListing(newListing);
    setIsPublishModalOpen(false);
  };

  const handlePlaceBid = (e: React.FormEvent) => {
    e.preventDefault();
    setBidSuccessMessage(true);
    setTimeout(() => {
      setBidSuccessMessage(false);
      setActiveBidModal(null);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Secondary Material Marketplace
          </h2>
          <p className="text-xs text-slate-400">
            Connect demolition contractors with certified material buyers, mini-mills, and reclamation yards
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => onNavigateToScreen('buyers')}>
            Buyer Directory
          </Button>
          <Button variant="primary" size="sm" onClick={() => setIsPublishModalOpen(true)}>
            <PlusCircle className="w-4 h-4 mr-1.5" /> Publish Material Lot
          </Button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex-1 max-w-md">
          <Input
            placeholder="Search material lots, profiles, or cities..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={<Search className="w-4 h-4" />}
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={cityFilter}
            onChange={(e) => setCityFilter(e.target.value)}
            className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-slate-300 focus:outline-none"
          >
            <option value="ALL">All Pickup Locations</option>
            <option value="Chicago">Chicago, IL</option>
            <option value="Pittsburgh">Pittsburgh, PA</option>
            <option value="Buffalo">Buffalo, NY</option>
          </select>
        </div>
      </div>

      {/* Material Lots Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredListings.map((listing) => (
          <Card key={listing.id} className="flex flex-col justify-between hover:border-slate-700 transition-all">
            <div>
              <div className="flex items-start justify-between gap-2">
                <Badge variant={listing.status === 'ACTIVE' ? 'success' : 'outline'}>
                  {listing.status}
                </Badge>
                <div className="text-right">
                  <div className="text-base font-bold text-emerald-400 font-mono">
                    {formatCurrency(listing.price_per_tonne_usd)}
                    <span className="text-xs text-slate-400 font-normal"> / t</span>
                  </div>
                </div>
              </div>

              <h3 className="text-base font-bold text-white mt-3 leading-snug">{listing.title}</h3>
              <p className="text-xs text-slate-400 mt-1 line-clamp-2">{listing.description}</p>

              <div className="mt-4 space-y-2 text-xs">
                <div className="flex items-center justify-between p-2 rounded bg-slate-800/60">
                  <span className="text-slate-400">Available Mass:</span>
                  <span className="font-bold text-white font-mono">{formatTonnes(listing.available_tonnes)}</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-slate-800/60">
                  <span className="text-slate-400">Total Lot Value:</span>
                  <span className="font-bold text-emerald-400 font-mono">{formatCurrency(listing.total_price_usd)}</span>
                </div>

                <div className="flex items-center gap-1.5 text-slate-400 pt-1 text-[11px]">
                  <MapPin className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                  <span className="truncate">{listing.pickup_city} • {listing.pickup_address}</span>
                </div>

                {listing.logistics_notes && (
                  <div className="flex items-center gap-1.5 text-slate-400 text-[11px]">
                    <Truck className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                    <span className="truncate">{listing.logistics_notes}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-800 flex items-center gap-2">
              <Button
                variant="primary"
                size="sm"
                className="w-full text-xs"
                onClick={() => {
                  setActiveBidModal(listing);
                  setBidPricePerTonne(listing.price_per_tonne_usd.toString());
                  setBidQuantityTonnes(listing.available_tonnes.toString());
                }}
              >
                <ShoppingBag className="w-3.5 h-3.5 mr-1" />
                Place Purchase Bid / Quote
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {/* Place Bid Dialog */}
      {activeBidModal && (
        <Dialog
          isOpen={true}
          onClose={() => setActiveBidModal(null)}
          title={`Place Bid: ${activeBidModal.title}`}
          description={`Lot ID: ${activeBidModal.id} • Available: ${formatTonnes(activeBidModal.available_tonnes)}`}
        >
          <form onSubmit={handlePlaceBid} className="space-y-4 text-xs">
            {bidSuccessMessage && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Bid submitted to seller! Notification dispatched.</span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Requested Quantity (Tonnes)"
                type="number"
                value={bidQuantityTonnes}
                onChange={(e) => setBidQuantityTonnes(e.target.value)}
                required
              />
              <Input
                label="Bid Price ($/t)"
                type="number"
                value={bidPricePerTonne}
                onChange={(e) => setBidPricePerTonne(e.target.value)}
                required
              />
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between font-mono">
              <span className="text-slate-400">Total Purchase Offer:</span>
              <span className="text-base font-bold text-emerald-400">
                {formatCurrency((parseFloat(bidQuantityTonnes) || 0) * (parseFloat(bidPricePerTonne) || 0))}
              </span>
            </div>

            <Select
              label="Haulage Fleet Transport"
              value={haulageType}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setHaulageType(e.target.value)}
            >
              <option value="FLATBED_TRAILER">Standard 48ft Flatbed Trailer</option>
              <option value="CRANE_TRUCK">Crane Loading Boom Truck</option>
              <option value="DUMP_TRAILER">End-Dump Scrap Aggregate Trailer</option>
              <option value="BUYER_PICKUP">Buyer-Arranged Freight Forwarder</option>
            </Select>

            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setActiveBidModal(null)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm">
                Submit Formal Purchase Bid
              </Button>
            </DialogFooter>
          </form>
        </Dialog>
      )}

      {/* Publish New Lot Dialog */}
      <Dialog
        isOpen={isPublishModalOpen}
        onClose={() => setIsPublishModalOpen(false)}
        title="Publish Material Lot to Recovery Marketplace"
        description="Offer verified deconstruction components directly to regional recycling yards and salvage buyers"
      >
        <form onSubmit={handlePublishListing} className="space-y-4 text-xs">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Select Material from Inventory *
            </label>
            <select
              value={selectedMaterialId}
              onChange={(e) => {
                setSelectedMaterialId(e.target.value);
                const item = materials.find((m) => m.id === e.target.value);
                if (item) {
                  setListingTitle(`${formatTonnes(item.estimated_weight_tonnes)} ${item.subcategory || item.category}`);
                }
              }}
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:outline-none"
            >
              {materials.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.category}: {m.subcategory || m.id} ({formatTonnes(m.estimated_weight_tonnes)})
                </option>
              ))}
            </select>
          </div>

          <Input
            label="Listing Title *"
            placeholder="e.g. 98 Tonnes Structural Steel I-Beams (W14x90)"
            value={listingTitle}
            onChange={(e) => setListingTitle(e.target.value)}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Price Per Tonne ($ USD) *"
              type="number"
              value={listingPrice}
              onChange={(e) => setListingPrice(e.target.value)}
              required
            />
            <Input
              label="Minimum Purchase (Tonnes)"
              type="number"
              value={listingMinOrder}
              onChange={(e) => setListingMinOrder(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Pickup Location (Address) *"
              value={listingAddress}
              onChange={(e) => setListingAddress(e.target.value)}
              required
            />
            <Input
              label="Pickup City *"
              value={listingCity}
              onChange={(e) => setListingCity(e.target.value)}
              required
            />
          </div>

          <Input
            label="Logistics & Loading Notes"
            placeholder="e.g. Crane loading assistance provided on site."
            value={listingLogistics}
            onChange={(e) => setListingLogistics(e.target.value)}
          />

          <DialogFooter>
            <Button type="button" variant="outline" size="sm" onClick={() => setIsPublishModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm">
              Publish Lot to Marketplace
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
};
