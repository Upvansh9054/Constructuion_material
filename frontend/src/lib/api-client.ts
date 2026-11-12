import { DemolitionSite } from '../types/site';
import {
  AssumptionsDefaultsResponse,
  MaterialConditionAssessmentRequest,
  MaterialConditionAssessmentResponse,
  MaterialItem,
  QuantityEstimationRequest,
  QuantityEstimationResponse,
  StereoReconstructionRequest,
  StereoReconstructionResponse,
  ValuationSummary,
  WeighbridgeVerificationRequest,
  WeighbridgeVerificationResponse,
} from '../types/material';
import { MediaStatusResponse, MediaUploadBatchResponse, SiteSurvey, SurveyImage } from '../types/survey';
import {
  AnalysisJob,
  DatasetStatsResponse,
  DemolitionAuditReport,
  MaterialLabelCorrectionRequest,
  MaterialLabelCorrectionResponse,
  ModelEvaluationDTO,
  SingleImageInferenceResponse,
  TrainingPipelineResponse,
} from '../types/analysis';
import { MarketplaceListing } from '../types/marketplace';

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    company_name?: string;
    is_active: boolean;
    is_superuser: boolean;
  };
}

export interface BuyerProfile {
  id: string;
  user_id: string;
  company_name: string;
  company_type: string;
  city: string;
  state: string;
  distance_km: number;
  accepted_categories: string[];
  certified_standards: string[];
  contact_person: string;
  contact_email: string;
  contact_phone: string;
  total_purchased_tonnes: number;
  active_bids_count: number;
  rating: number;
  created_at: string;
  updated_at: string;
}

export interface BidTransaction {
  id: string;
  listing_id: string;
  buyer_id: string;
  requested_tonnes: number;
  bid_price_per_tonne_usd: number;
  total_offer_usd: number;
  haulage_type: string;
  status: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLogItem {
  id: string;
  user_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  change_details?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('demolition_auth_token');
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('demolition_auth_token', token);
      } else {
        localStorage.removeItem('demolition_auth_token');
      }
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || `Request failed with status ${response.status}`);
    }

    if (response.status === 204) {
      return null as T;
    }

    return response.json();
  }

  // --- Auth (Module 1, 2) ---
  async login(username: string, password: string): Promise<AuthTokenResponse> {
    const body = new URLSearchParams();
    body.append('username', username);
    body.append('password', password);

    const data = await this.request<AuthTokenResponse>('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
    });

    this.setToken(data.access_token);
    return data;
  }

  async register(userData: {
    email: string;
    password: string;
    full_name: string;
    role: string;
    company_name?: string;
    phone_number?: string;
  }) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getMe() {
    return this.request('/auth/me');
  }

  logout() {
    this.setToken(null);
  }

  // --- Sites (Module 3, 4) ---
  async getSites(page = 1, pageSize = 20, search?: string, city?: string) {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (search) params.append('search', search);
    if (city) params.append('city', city);
    return this.request<{ items: DemolitionSite[]; total: number }>(`/sites/?${params.toString()}`);
  }

  async getSite(id: string) {
    return this.request<DemolitionSite>(`/sites/${id}`);
  }

  async createSite(site: Partial<DemolitionSite>) {
    return this.request<DemolitionSite>('/sites/', {
      method: 'POST',
      body: JSON.stringify(site),
    });
  }

  async updateSite(id: string, site: Partial<DemolitionSite>) {
    return this.request<DemolitionSite>(`/sites/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(site),
    });
  }

  async deleteSite(id: string) {
    return this.request<void>(`/sites/${id}`, {
      method: 'DELETE',
    });
  }

  // --- Surveys & Media (Module 5) ---
  async listSurveys(siteId?: string) {
    const endpoint = siteId ? `/surveys/?site_id=${siteId}` : '/surveys/';
    return this.request<SiteSurvey[]>(endpoint);
  }

  async getSurvey(id: string) {
    return this.request<SiteSurvey>(`/surveys/${id}`);
  }

  async createSurvey(survey: {
    site_id: string;
    survey_date: string;
    assessment_name?: string;
    assessment_type?: string;
    survey_notes?: string;
    weather_condition?: string;
  }) {
    return this.request<SiteSurvey>('/surveys/', {
      method: 'POST',
      body: JSON.stringify(survey),
    });
  }

  async uploadSurveyMediaDirect(surveyId: string, formData: FormData): Promise<SurveyImage> {
    return this.request<SurveyImage>(`/surveys/${surveyId}/upload-direct`, {
      method: 'POST',
      body: formData,
    });
  }

  async uploadMultipleMedia(surveyId: string, formData: FormData): Promise<MediaUploadBatchResponse> {
    return this.request<MediaUploadBatchResponse>(`/surveys/${surveyId}/upload-media`, {
      method: 'POST',
      body: formData,
    });
  }

  async getSurveyMedia(surveyId: string, mediaType?: string, includeFrames = true): Promise<SurveyImage[]> {
    const params = new URLSearchParams({ include_frames: String(includeFrames) });
    if (mediaType) params.append('media_type', mediaType);
    return this.request<SurveyImage[]>(`/surveys/${surveyId}/media?${params.toString()}`);
  }

  async getMediaProcessingStatus(surveyId: string): Promise<MediaStatusResponse> {
    return this.request<MediaStatusResponse>(`/surveys/${surveyId}/media-status`);
  }

  async deleteSurveyMedia(surveyId: string, imageId: string): Promise<void> {
    return this.request<void>(`/surveys/${surveyId}/media/${imageId}`, {
      method: 'DELETE',
    });
  }

  async extractVideoFrames(
    surveyId: string,
    videoId: string,
    intervalSeconds = 1.0,
    similarityThreshold = 0.97
  ): Promise<SurveyImage[]> {
    return this.request<SurveyImage[]>(`/surveys/${surveyId}/extract-video-frames`, {
      method: 'POST',
      body: JSON.stringify({
        video_id: videoId,
        interval_seconds: intervalSeconds,
        similarity_threshold: similarityThreshold,
      }),
    });
  }

  // --- Materials & Valuation (Module 7, 8, 9, 10) ---
  async getMaterialCategories() {
    return this.request<any[]>('/materials/categories');
  }

  async getMaterials(surveyId?: string, category?: string, isVerified?: boolean) {
    const params = new URLSearchParams();
    if (surveyId) params.append('survey_id', surveyId);
    if (category) params.append('category', category);
    if (isVerified !== undefined) params.append('is_verified', String(isVerified));
    return this.request<{ items: MaterialItem[]; total: number }>(`/materials/?${params.toString()}`);
  }

  async getValuationSummary(surveyId: string) {
    return this.request<ValuationSummary>(`/materials/summary/${surveyId}`);
  }

  async createMaterial(data: Partial<MaterialItem>) {
    return this.request<MaterialItem>('/materials/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateMaterial(id: string, data: Partial<MaterialItem>) {
    return this.request<MaterialItem>(`/materials/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async verifyMaterial(id: string) {
    return this.request<MaterialItem>(`/materials/${id}/verify`, {
      method: 'POST',
    });
  }

  async deleteMaterial(id: string) {
    return this.request<void>(`/materials/${id}`, {
      method: 'DELETE',
    });
  }

  async getAssumptionsDefaults(): Promise<AssumptionsDefaultsResponse> {
    return this.request<AssumptionsDefaultsResponse>('/materials/assumptions/defaults');
  }

  async estimateQuantities(data: QuantityEstimationRequest): Promise<QuantityEstimationResponse> {
    return this.request<QuantityEstimationResponse>('/materials/estimate-quantities', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async assessCondition(data: MaterialConditionAssessmentRequest): Promise<MaterialConditionAssessmentResponse> {
    return this.request<MaterialConditionAssessmentResponse>('/materials/assess-condition', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async verifyWeighbridge(
    materialId: string,
    data: WeighbridgeVerificationRequest
  ): Promise<WeighbridgeVerificationResponse> {
    return this.request<WeighbridgeVerificationResponse>(`/materials/${materialId}/verify-weighbridge`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async reconstruct3D(data: StereoReconstructionRequest): Promise<StereoReconstructionResponse> {
    return this.request<StereoReconstructionResponse>('/materials/reconstruct-3d', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // --- AI Analysis (Module 6) ---
  async triggerAnalysis(surveyId: string) {
    return this.request<AnalysisJob>('/analysis/trigger', {
      method: 'POST',
      body: JSON.stringify({ survey_id: surveyId }),
    });
  }

  async getAnalysisJob(jobId: string) {
    return this.request<AnalysisJob>(`/analysis/jobs/${jobId}`);
  }

  async inferImage(
    file: File,
    confidenceThreshold = 0.4,
    iouThreshold = 0.45
  ): Promise<SingleImageInferenceResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('confidence_threshold', String(confidenceThreshold));
    formData.append('iou_threshold', String(iouThreshold));
    return this.request<SingleImageInferenceResponse>('/analysis/infer-image', {
      method: 'POST',
      body: formData,
    });
  }

  async inferSurveyImage(
    imageId: string,
    confidenceThreshold = 0.4,
    iouThreshold = 0.45
  ): Promise<SingleImageInferenceResponse> {
    const formData = new FormData();
    formData.append('image_id', imageId);
    formData.append('confidence_threshold', String(confidenceThreshold));
    formData.append('iou_threshold', String(iouThreshold));
    return this.request<SingleImageInferenceResponse>('/analysis/infer-image', {
      method: 'POST',
      body: formData,
    });
  }

  async getModelEvaluations(): Promise<ModelEvaluationDTO[]> {
    return this.request<ModelEvaluationDTO[]>('/analysis/models/evaluation');
  }

  async correctMaterialAnnotation(
    correction: MaterialLabelCorrectionRequest
  ): Promise<MaterialLabelCorrectionResponse> {
    return this.request<MaterialLabelCorrectionResponse>('/analysis/annotations/correct', {
      method: 'POST',
      body: JSON.stringify(correction),
    });
  }

  async getDatasetStats(datasetDir?: string): Promise<DatasetStatsResponse> {
    const params = new URLSearchParams();
    if (datasetDir) params.append('dataset_dir', datasetDir);
    return this.request<DatasetStatsResponse>(`/analysis/dataset/stats?${params.toString()}`);
  }

  async generateSampleDataset(numTrain = 6, numVal = 2): Promise<DatasetStatsResponse> {
    const params = new URLSearchParams({
      num_train: String(numTrain),
      num_val: String(numVal),
    });
    return this.request<DatasetStatsResponse>(`/analysis/dataset/generate-sample?${params.toString()}`, {
      method: 'POST',
    });
  }

  async triggerModelTraining(cfg?: {
    base_model?: string;
    dataset_yaml_path?: string;
    epochs?: number;
    batch_size?: number;
    learning_rate?: number;
  }): Promise<TrainingPipelineResponse> {
    return this.request<TrainingPipelineResponse>('/analysis/train', {
      method: 'POST',
      body: JSON.stringify(cfg || {}),
    });
  }

  // --- Marketplace & Bids (Module 12, 13) ---
  async getListings(city?: string, statusFilter?: string) {
    const params = new URLSearchParams();
    if (city) params.append('city', city);
    if (statusFilter) params.append('status_filter', statusFilter);
    return this.request<{ items: MarketplaceListing[]; total: number }>(`/marketplace/?${params.toString()}`);
  }

  async getListing(id: string) {
    return this.request<MarketplaceListing>(`/marketplace/${id}`);
  }

  async createListing(listing: Partial<MarketplaceListing>) {
    return this.request<MarketplaceListing>('/marketplace/', {
      method: 'POST',
      body: JSON.stringify(listing),
    });
  }

  async placeBid(listingId: string, bid: { requested_tonnes: number; bid_price_per_tonne_usd: number; haulage_type?: string; notes?: string }) {
    return this.request<BidTransaction>(`/marketplace/${listingId}/bids`, {
      method: 'POST',
      body: JSON.stringify(bid),
    });
  }

  async getListingBids(listingId: string) {
    return this.request<BidTransaction[]>(`/marketplace/${listingId}/bids`);
  }

  async getMyBids() {
    return this.request<BidTransaction[]>('/marketplace/bids/my');
  }

  async updateBidStatus(bidId: string, status: string, notes?: string) {
    return this.request<BidTransaction>(`/marketplace/bids/${bidId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes }),
    });
  }

  // --- Buyers & Recyclers (Module 11) ---
  async getBuyers(search?: string, city?: string, companyType?: string) {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (city) params.append('city', city);
    if (companyType) params.append('company_type', companyType);
    return this.request<{ items: BuyerProfile[]; total: number }>(`/buyers/?${params.toString()}`);
  }

  async getBuyerProfile(id: string) {
    return this.request<BuyerProfile>(`/buyers/${id}`);
  }

  async createBuyerProfile(profile: Partial<BuyerProfile>) {
    return this.request<BuyerProfile>('/buyers/', {
      method: 'POST',
      body: JSON.stringify(profile),
    });
  }

  // --- Demolition Pre-Demolition Reports (Module 14) ---
  async generateDmarReport(siteId: string, surveyId: string, reportTitle?: string) {
    return this.request<DemolitionAuditReport>('/reports/', {
      method: 'POST',
      body: JSON.stringify({ site_id: siteId, survey_id: surveyId, report_title: reportTitle }),
    });
  }

  async listReports(siteId?: string, surveyId?: string) {
    const params = new URLSearchParams();
    if (siteId) params.append('site_id', siteId);
    if (surveyId) params.append('survey_id', surveyId);
    return this.request<DemolitionAuditReport[]>(`/reports/?${params.toString()}`);
  }

  async getReport(id: string) {
    return this.request<DemolitionAuditReport>(`/reports/${id}`);
  }

  // --- Immutable Audit Logs (Module 15) ---
  async getAuditLogs(page = 1, pageSize = 25, action?: string) {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (action) params.append('action', action);
    return this.request<{ items: AuditLogItem[]; total: number }>(`/audit-logs/?${params.toString()}`);
  }
}

export const apiClient = new ApiClient();
