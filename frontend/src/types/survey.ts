export type SurveyStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'ANALYSIS_COMPLETED'
  | 'FAILED';

export interface SurveyImage {
  id: string;
  survey_id: string;
  file_name: string;
  original_s3_key: string;
  annotated_s3_key?: string;
  thumbnail_s3_key?: string;
  download_url?: string;
  file_size_bytes: number;
  mime_type: string;
  width?: number;
  height?: number;
  gps_latitude?: number;
  gps_longitude?: number;
  created_at: string;
}

export interface SiteSurvey {
  id: string;
  site_id: string;
  surveyor_id?: string;
  survey_date: string;
  weather_condition?: string;
  survey_notes?: string;
  status: SurveyStatus;
  total_images_count: number;
  created_at: string;
  updated_at: string;
  images?: SurveyImage[];
}

