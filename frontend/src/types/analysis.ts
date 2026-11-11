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

