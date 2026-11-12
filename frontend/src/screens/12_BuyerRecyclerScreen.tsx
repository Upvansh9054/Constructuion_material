import React, { useState } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { DEV_BUYERS_RECYCLERS, BuyerRecycler } from '../mock/fixtures';
import { formatTonnes } from '../lib/utils';
import {
  Search,
  MapPin,
  Phone,
  Mail,
  ShieldCheck,
  Star,
  Send,
  CheckCircle2,
} from 'lucide-react';

interface BuyerRecyclerScreenProps {
  onNavigateToScreen: (screen: string) => void;
  onSendRfq?: (buyer: BuyerRecycler) => void;
}

export const BuyerRecyclerScreen: React.FC<BuyerRecyclerScreenProps> = ({ onNavigateToScreen, onSendRfq }) => {
  const [buyers] = useState<BuyerRecycler[]>(DEV_BUYERS_RECYCLERS);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [invitedId, setInvitedId] = useState<string | null>(null);

  const filteredBuyers = buyers.filter((b) => {
    const matchesSearch =
      b.name.toLowerCase().includes(search.toLowerCase()) ||
      b.city.toLowerCase().includes(search.toLowerCase()) ||
      b.contact_person.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === 'ALL' || b.company_type === typeFilter;
    return matchesSearch && matchesType;
  });

  const handleInviteToBid = (id: string) => {
    const targetBuyer = buyers.find((b) => b.id === id);
    setInvitedId(id);
    if (targetBuyer && onSendRfq) {
      onSendRfq(targetBuyer);
    }
    setTimeout(() => setInvitedId(null), 3500);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Buyer & Recycler Management
          </h2>
          <p className="text-xs text-slate-400">
            Directory of certified industrial off-takers, secondary steel mini-mills, aggregate crushing yards, and salvage depots
          </p>
        </div>

        <Button variant="outline" size="sm" onClick={() => onNavigateToScreen('marketplace')}>
          View Marketplace Lots
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900 border border-slate-800">
        <div className="flex-1 max-w-md">
          <Input
            placeholder="Search certified buyers, contacts, or cities..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={<Search className="w-4 h-4" />}
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-slate-300 focus:outline-none"
          >
            <option value="ALL">All Off-Taker Types</option>
            <option value="STEEL_MILL">Secondary Steel Mills (EAF)</option>
            <option value="AGGREGATE_CRUSHER">Aggregate Crushing Facilities</option>
            <option value="ARCHITECTURAL_SALVAGE">Architectural Salvage Yards</option>
            <option value="TIMBER_RECLAIMER">Timber Reclamation Mills</option>
            <option value="GLASS_RECYCLER">Cullet Remelters</option>
          </select>
        </div>
      </div>

      {/* Directory Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredBuyers.map((buyer) => (
          <Card key={buyer.id} className="flex flex-col justify-between hover:border-slate-700 transition-all">
            <div>
              <div className="flex items-start justify-between gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  {buyer.company_type.replace(/_/g, ' ')}
                </span>
                <div className="flex items-center gap-1 text-amber-400 text-xs font-bold">
                  <Star className="w-3.5 h-3.5 fill-current" />
                  <span>{buyer.rating.toFixed(1)}</span>
                </div>
              </div>

              <h3 className="text-base font-bold text-white mt-3 leading-snug">{buyer.name}</h3>

              <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-400">
                <MapPin className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                <span>
                  {buyer.city}, {buyer.state} ({buyer.distance_km} km haulage distance)
                </span>
              </div>

              {/* Accepted Material Stream Chips */}
              <div className="mt-3.5 flex flex-wrap gap-1.5">
                {buyer.accepted_categories.map((cat) => (
                  <Badge key={cat} category={cat as any} className="text-[10px] py-0 px-1.5">
                    {cat}
                  </Badge>
                ))}
              </div>

              {/* Certified Standards */}
              <div className="mt-3.5 space-y-1">
                <span className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider block">
                  Accreditations
                </span>
                <div className="flex flex-wrap gap-1 text-[11px] text-slate-400">
                  {buyer.certified_standards.map((cert) => (
                    <span
                      key={cert}
                      className="inline-flex items-center gap-1 bg-slate-800/80 px-2 py-0.5 rounded text-[10px] text-slate-300 border border-slate-700/60"
                    >
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      {cert}
                    </span>
                  ))}
                </div>
              </div>

              {/* Metrics */}
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-slate-800/60 border border-slate-800">
                  <span className="text-slate-500 text-[10px] block uppercase font-semibold">Tonnage Purchased</span>
                  <span className="font-bold text-white font-mono">{formatTonnes(buyer.total_purchased_tonnes)}</span>
                </div>
                <div className="p-2 rounded bg-slate-800/60 border border-slate-800">
                  <span className="text-slate-500 text-[10px] block uppercase font-semibold">Active Bids</span>
                  <span className="font-bold text-emerald-400 font-mono">{buyer.active_bids_count} active</span>
                </div>
              </div>

              {/* Contact Person */}
              <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400 space-y-1">
                <div className="font-semibold text-slate-200">{buyer.contact_person}</div>
                <div className="flex items-center gap-2 text-[11px]">
                  <Mail className="w-3 h-3 text-slate-500" />
                  <span className="truncate">{buyer.email}</span>
                </div>
                <div className="flex items-center gap-2 text-[11px]">
                  <Phone className="w-3 h-3 text-slate-500" />
                  <span>{buyer.phone}</span>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-800">
              {invitedId === buyer.id ? (
                <div className="p-2 text-center rounded bg-emerald-500/20 text-emerald-300 text-xs font-semibold flex items-center justify-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" /> RfQ Invitation Dispatched!
                </div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs"
                  onClick={() => handleInviteToBid(buyer.id)}
                >
                  <Send className="w-3.5 h-3.5 mr-1" /> Request Direct Bid / Quote
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
