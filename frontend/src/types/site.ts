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
  building_type?: string;
  building_length_m?: number;
  building_width_m?: number;
  building_height_m?: number;
  number_of_floors?: number;
  total_building_volume_m3?: number;
  footprint_sqm?: number;
  structural_type?: string;
  has_asbestos_risk?: boolean;
  has_lead_paint?: boolean;
  hazard_notes?: string;
  status: SiteStatus;
  estimated_demolition_date?: string;
  actual_demolition_date?: string;
  contractor_id: string;
  created_at: string;
  updated_at: string;
}

