export type ListingStatus = 'DRAFT' | 'ACTIVE' | 'RESERVED' | 'SOLD' | 'CANCELLED';

export interface MarketplaceListing {
  id: string;
  material_item_id: string;
  seller_id: string;
  title: string;
  description?: string;
  available_tonnes: number;
  min_order_tonnes: number;
  price_per_tonne_usd: number;
  total_price_usd: number;
  pickup_address: string;
  pickup_city: string;
  logistics_notes?: string;
  status: ListingStatus;
  listed_at?: string;
  sold_at?: string;
  created_at: string;
  updated_at: string;
}

