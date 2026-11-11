export type SiteStatus =
  | 'PLANNING'
  | 'PRE_DEMOLITION_SURVEY'
  | 'ACTIVE_DEMOLITION'
  | 'MATERIAL_SORTING'
  | 'COMPLETED';

export interface DemolitionSite {
  id: string;
  name: string;
  site_code: string;
  description?: string;
  address: string;
  city: string;
  postal_code?: string;
  country: string;
  latitude?: number;
  longitude?: number;
  status: SiteStatus;
  estimated_demolition_date?: string;
  actual_demolition_date?: string;
  contractor_id: string;
  created_at: string;
  updated_at: string;
}
