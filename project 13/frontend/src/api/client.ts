import axios from "axios";

export interface TranscriptSegment {
  speaker: "Rep" | "Customer";
  timestamp_start: number;
  timestamp_end: number;
  text: string;
}

export interface TranscriptOutput {
  call_id: string;
  audio_file_name: string;
  duration_seconds: number;
  segments: TranscriptSegment[];
  full_text: string;
}

export interface CRMRecord {
  contact_name: string;
  contact_email: string;
  company: string;
  deal_stage: string;
  pain_points: string[];
  next_steps: string;
  call_date: string;
}

export interface BuyingSignal {
  quote: string;
  signal_type: string;
  confidence: number;
}

export interface OpportunityFlag {
  opportunity_type: "upsell" | "cross-sell";
  product_suggestion: string;
  evidence: string;
  confidence: number;
}

export interface OpportunityReport {
  buying_signals: BuyingSignal[];
  opportunity_flags: OpportunityFlag[];
}

export interface EmailDraft {
  subject: string;
  body: string;
}

export interface RubricScore {
  dimension: string;
  score: number;
  comment: string;
}

export interface CoachingReport {
  rubric_scores: RubricScore[];
  talk_ratio_rep: number;
  talk_ratio_customer: number;
  strengths: string[];
  areas_to_improve: string[];
  recommended_actions: string[];
}

export interface PipelineResult {
  call_id: string;
  transcript: TranscriptOutput | null;
  crm_record: CRMRecord | null;
  opportunity_report: OpportunityReport | null;
  email_draft: EmailDraft | null;
  coaching_report: CoachingReport | null;
  status: string;
  error_message: string | null;
}

export interface SessionSummary {
  call_id: string;
  contact_name: string | null;
  company: string | null;
  deal_stage: string | null;
  call_date: string | null;
  status: string;
}

export interface StatusResponse {
  call_id: string;
  status: string;
  completed_nodes: string[];
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "/api";

const client = axios.create({
  baseURL: apiBaseUrl,
  timeout: 120000,
});

// Auth interceptor: attach Bearer token to every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Redirect to login on 401
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      localStorage.removeItem("auth_token");
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export async function getSessions(): Promise<SessionSummary[]> {
  const { data } = await client.get<SessionSummary[]>("/sessions");
  return data;
}

export async function getPipelineStatus(callId: string): Promise<StatusResponse> {
  const { data } = await client.get<StatusResponse>(`/pipeline/${callId}/status`);
  return data;
}

export async function getPipelineResult(callId: string): Promise<PipelineResult> {
  const { data } = await client.get<PipelineResult>(`/pipeline/${callId}/result`);
  return data;
}

export async function updateCRMRecord(callId: string, crm: CRMRecord): Promise<{ call_id: string; status: string }> {
  const { data } = await client.patch<{ call_id: string; status: string }>(`/pipeline/${callId}/crm`, crm);
  return data;
}

export async function updateEmailDraft(callId: string, email: EmailDraft): Promise<{ call_id: string; status: string }> {
  const { data } = await client.patch<{ call_id: string; status: string }>(`/pipeline/${callId}/email`, email);
  return data;
}

export async function uploadAudio(file: File): Promise<{ call_id: string; status: string }> {
  const formData = new FormData();
  formData.append("audio_file", file);
  const { data } = await client.post<{ call_id: string; status: string }>("/pipeline/run", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
