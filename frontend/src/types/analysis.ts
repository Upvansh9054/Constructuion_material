export type JobStatus = 'QUEUED' | 'IN_PROGRESS' | 'SUCCESS' | 'FAILED';

export interface AnalysisJob {
  id: string;
  survey_id: string;
  celery_task_id?: string;
  status: JobStatus;
  progress_percentage: number;
  processed_images_count: number;
  total_images_count: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface DemolitionAuditReport {
  id: string;
  site_id: string;
  survey_id: string;
  report_title: string;
  executive_summary: string;
  regulatory_compliance_notes?: string;
  buyer_matching_insights?: string;
  total_recoverable_tonnes: number;
  total_estimated_value_usd: number;
  total_carbon_offset_kg_co2e: number;
  detailed_breakdown_json: any[];
  pdf_report_s3_key?: string;
  created_at: string;
}

export interface DetectionBoxDTO {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
  confidence: number;
  category: 'CONCRETE' | 'BRICKS' | 'STEEL' | 'TIMBER' | 'GLASS' | 'MIXED_DEBRIS';
  subcategory?: string;
  class_id: number;
  mask_polygon?: number[][];
  area_pixels?: number;
}

export interface SingleImageInferenceResponse {
  image_id?: string;
  file_name?: string;
  model_version: string;
  model_architecture: string;
  inference_latency_ms: number;
  image_width: number;
  image_height: number;
  is_fine_tuned: boolean;
  warning?: string;
  detections: DetectionBoxDTO[];
  annotated_download_url?: string;
}

export interface ModelEvaluationDTO {
  model_name: string;
  architecture: string;
  parameter_count_millions: number;
  mAP50_coco_baseline: number;
  latency_cpu_ms: number;
  latency_gpu_ms: number;
  memory_footprint_mb: number;
  segmentation_capable: boolean;
  demolition_suitability_grade: string;
  evaluation_notes: string;
}

export interface MaterialLabelCorrectionRequest {
  material_item_id: string;
  corrected_category: string;
  corrected_subcategory?: string;
  condition_grade?: string;
  notes?: string;
  save_to_training_pool?: boolean;
}

export interface MaterialLabelCorrectionResponse {
  material_item_id: string;
  previous_category: string;
  updated_category: string;
  is_verified: boolean;
  training_sample_saved: boolean;
  training_dataset_path?: string;
}

export interface DatasetStatsResponse {
  is_ready_for_training: boolean;
  train_count: number;
  val_count: number;
  class_distribution: Record<string, number>;
  classes: string[];
  errors: string[];
  warnings: string[];
}

export interface TrainingPipelineResponse {
  success: boolean;
  message: string;
  metrics?: {
    mAP50: number;
    mAP50_95: number;
    precision: number;
    recall: number;
    best_weights: string;
    duration_seconds: number;
  };
  dataset_readiness: Record<string, any>;
}


