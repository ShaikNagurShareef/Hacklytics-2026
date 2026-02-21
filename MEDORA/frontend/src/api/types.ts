export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  agent_name?: string;
  pdf_data?: string;
}

export interface ChatRequest {
  session_id: string;
  query: string;
  context: Array<{ role: string; content: string }>;
}

export interface ChatRequestWithImage extends ChatRequest {
  image_base64?: string | null;
  image_mime_type?: string;
}

export interface ChatResponse {
  agent_name: string;
  content: string;
  metadata: Record<string, unknown>;
}

export interface HealthResponse {
  status: string;
}

// Auth
export interface SignUpRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  email: string;
  full_name: string | null;
  created_at: string;
}

export interface UserUpdateRequest {
  full_name?: string | null;
}

// Chat history (saved sessions for authenticated users)
export interface ChatSessionListItem {
  id: number;
  client_session_id: string;
  title: string | null;
  agent_type: string | null;
  updated_at: string;
}

export interface ChatMessageOut {
  role: string;
  content: string;
  agent_name: string | null;
  created_at: string;
}

export interface ChatSessionDetail {
  id: number;
  client_session_id: string;
  title: string | null;
  agent_type: string | null;
  created_at: string;
  updated_at: string;
  messages: ChatMessageOut[];
}
