export type MaterialCategory =
  | 'CONCRETE'
  | 'BRICKS'
  | 'STEEL'
  | 'TIMBER'
  | 'GLASS'
  | 'MIXED_DEBRIS';

export type ConditionGrade =
  | 'REUSABLE_EXCELLENT'
  | 'REUSABLE_GOOD'
  | 'RECYCLABLE'
  | 'DOWN_CYCLE_ONLY'
  | 'HAZARDOUS_CONTAMINATED';

export interface BoundingBox {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
}

export interface MaterialItem {
  id: string;
  survey_id: string;
  source_image_id?: string;
  category: MaterialCategory;
  subcategory?: string;
  description?: string;
  condition_grade: ConditionGrade;
  estimated_volume_m3: number;
  estimated_weight_tonnes: number;
  unit_count?: number;
  contamination_risk?: string;
  confidence_score?: number;
  bounding_box?: BoundingBox;
  estimated_market_value_usd: number;
  embodied_carbon_offset_kg: number;
  is_verified_by_surveyor: boolean;
  surveyor_adjustment_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface MaterialCategorySummary {
  category: MaterialCategory;
  total_volume_m3: number;
  total_weight_tonnes: number;
  estimated_value_usd: number;
  carbon_offset_kg_co2e: number;
  item_count: number;
}

export interface ValuationSummary {
  total_estimated_value_usd: number;
  total_recoverable_tonnes: number;
  total_carbon_offset_kg_co2e: number;
  categories: MaterialCategorySummary[];
}
