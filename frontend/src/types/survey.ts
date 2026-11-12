export type SurveyStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'ANALYSIS_COMPLETED'
  | 'FAILED';

export interface SurveyImage {
  id: string;
  survey_id: string;
  file_name: string;
  media_type?: 'IMAGE' | 'VIDEO' | 'ORTHOMOSAIC' | 'SCAN_360';
  original_s3_key: string;
  annotated_s3_key?: string;
  thumbnail_s3_key?: string;
  cv_preprocessed_s3_key?: string;
  download_url?: string;
  thumbnail_url?: string;
  file_size_bytes: number;
  mime_type: string;
  width?: number;
  height?: number;
  is_extracted_frame?: boolean;
  parent_video_id?: string;
  frame_index?: number;
  timestamp_seconds?: number;
  duration_seconds?: number;
  fps?: number;
  codec?: string;
  processing_status?: string;
  error_message?: string;
  camera_altitude_m?: number;
  focal_length_mm?: number;
  sensor_width_mm?: number;
  gsd_cm_per_px?: number;
  gps_latitude?: number;
  gps_longitude?: number;
  created_at: string;
}

export interface SiteSurvey {
  id: string;
  site_id: string;
  surveyor_id?: string;
  assessment_name?: string;
  assessment_type?: string;
  survey_date: string;
  weather_condition?: string;
  survey_notes?: string;
  status: SurveyStatus;
  processing_status?: string;
  total_images_count: number;
  processed_images_count?: number;
  extracted_frames_count?: number;
  created_at: string;
  updated_at: string;
  images?: SurveyImage[];
}

export interface MediaUploadBatchResponse {
  survey_id: string;
  job_id?: string;
  uploaded_count: number;
  failed_count: number;
  images: SurveyImage[];
  errors: string[];
}

export interface MediaStatusResponse {
  survey_id: string;
  processing_status: string;
  total_images_count: number;
  processed_images_count: number;
  extracted_frames_count: number;
  active_job_id?: string;
  progress_percentage: number;
  error_message?: string;
}

