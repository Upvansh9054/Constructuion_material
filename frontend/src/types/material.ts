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
  dimension_length_m?: number;
  dimension_width_m?: number;
  dimension_height_m?: number;
  surface_area_m2?: number;
  min_volume_m3?: number;
  max_volume_m3?: number;
  min_weight_tonnes?: number;
  max_weight_tonnes?: number;
  uncertainty_percentage?: number;
  assumed_density_t_per_m3?: number;
  packing_factor?: number;
  calculation_method?: string;
  reference_measurement_notes?: string;
  damage_severity_pct?: number;
  damage_type?: string;
  requires_specialist_abatement?: boolean;
  hazard_inspection_warning?: string;
  recommended_recovery_route?: string;
  recoverability_percentage?: number;
  unit_count?: number;
  contamination_risk?: string;
  confidence_score?: number;
  bounding_box?: BoundingBox;
  estimated_market_value_usd: number;
  embodied_carbon_offset_kg: number;
  is_verified_by_surveyor: boolean;
  verified_weight_tonnes?: number;
  verified_volume_m3?: number;
  weighbridge_ticket_number?: string;
  weighbridge_scale_id?: string;
  weighbridge_timestamp?: string;
  verified_by_user_id?: string;
  verified_at?: string;
  surveyor_adjustment_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface QuantityEstimationRequest {
  category: MaterialCategory;
  detection_box?: BoundingBox;
  image_width?: number;
  image_height?: number;
  camera_height_m?: number;
  focal_length_mm?: number;
  sensor_width_mm?: number;
  reference_measurement_m?: number;
  reference_pixel_length?: number;
  manual_length_m?: number;
  manual_width_m?: number;
  manual_height_m?: number;
  custom_density_t_per_m3?: number;
  custom_packing_factor?: number;
}

export interface QuantityEstimationResponse {
  nominal_volume_m3: number;
  nominal_weight_tonnes: number;
  min_volume_m3: number;
  max_volume_m3: number;
  min_weight_tonnes: number;
  max_weight_tonnes: number;
  uncertainty_percentage: number;
  dimension_length_m: number;
  dimension_width_m: number;
  dimension_height_m: number;
  surface_area_m2: number;
  assumed_density_t_per_m3: number;
  packing_factor: number;
  estimation_method: string;
  assumptions_applied: Record<string, any>;
}

export interface MaterialConditionAssessmentRequest {
  category: MaterialCategory;
  building_year?: number;
  site_has_asbestos_risk?: boolean;
  site_has_lead_paint?: boolean;
  manual_hazard_flags?: string[];
  crop_image_bytes_base64?: string;
}

export interface MaterialConditionAssessmentResponse {
  grade: ConditionGrade;
  damage_severity_pct: number;
  damage_type?: string;
  contamination_risk?: string;
  requires_specialist_abatement: boolean;
  hazard_inspection_warning?: string;
  recommended_recovery_route: string;
  recoverability_percentage: number;
  inspection_notes: string;
  confidence: number;
  indicators: string[];
}

export interface WeighbridgeVerificationRequest {
  verified_weight_tonnes: number;
  verified_volume_m3?: number;
  weighbridge_ticket_number: string;
  weighbridge_scale_id?: string;
  weighbridge_timestamp?: string;
  surveyor_notes?: string;
}

export interface WeighbridgeVerificationResponse {
  material_item_id: string;
  estimated_weight_tonnes: number;
  verified_weight_tonnes: number;
  weight_delta_tonnes: number;
  weight_variance_percentage: number;
  weighbridge_ticket_number: string;
  is_verified: boolean;
  verified_by_user_id: string;
  verified_at: string;
}

export interface AssumptionsDefaultsResponse {
  densities: Record<string, Record<string, number>>;
  packing_factors: Record<string, Record<string, number>>;
  depth_priors: Record<string, Record<string, number>>;
  regulatory_guidance: Record<string, string>;
}

export interface StereoReconstructionRequest {
  image_a_id?: string;
  image_b_id?: string;
  image_a_base64?: string;
  image_b_base64?: string;
  focal_length_mm?: number;
  sensor_width_mm?: number;
  baseline_distance_m?: number;
  camera_height_m?: number;
}

export interface StereoReconstructionResponse {
  point_count: number;
  bounding_box_3d: Record<string, number>;
  convex_hull_volume_m3: number;
  reconstruction_confidence: number;
  matched_features_count: number;
  triangulation_error_px: number;
  methodology_used: string;
  point_cloud_summary: Record<string, any>;
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

