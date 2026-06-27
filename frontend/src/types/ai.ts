export interface AiSetting {
  id: number;
  company_id: number;
  provider_name: string;
  api_key_masked: string | null;
  api_host: string | null;
  model_name: string;
  system_prompt: string | null;
  temperature: number | null;
  max_tokens: number | null;
  timeout_seconds: number | null;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface AiChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface AiChatResponse {
  role: string;
  content: string;
  tokens_used: number | null;
}

export interface AiReport {
  report_title: string;
  report_content: string;
  generated_at: string;
  model_used: string;
}

export interface AiTestConnectionResponse {
  status: 'ok' | 'error';
  message: string;
  latency_ms: number | null;
}
