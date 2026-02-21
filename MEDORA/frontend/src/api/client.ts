import type {
  ChatRequest,
  ChatRequestWithImage,
  ChatResponse,
  ChatSessionDetail,
  ChatSessionListItem,
  HealthResponse,
  SignUpRequest,
  LoginRequest,
  TokenResponse,
  UserResponse,
  UserUpdateRequest,
} from "./types";

const getBaseUrl = (): string => {
  const env = import.meta.env.VITE_API_BASE_URL;
  if (env && typeof env === "string") return env.replace(/\/$/, "");
  // Use empty base so requests go to same origin; Vite dev server proxies /api -> backend (see vite.config.js)
  return "";
};

const API_TIMEOUT_MS = 60_000;

const apiUrl = (path: string): string => {
  const base = getBaseUrl();
  const p = path.startsWith("/") ? path.slice(1) : path;
  if (base) return `${base}/${p}`;
  return `/api/${p}`;
};

/** Turn FastAPI error detail (string | array | object) into a single readable message. */
function formatApiError(detail: unknown): string {
  let out = "";
  if (typeof detail === "string") {
    out = detail.trim();
  } else if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (first && typeof first === "object" && "msg" in first && typeof first.msg === "string") {
      out = first.msg;
    } else {
      out = detail.map((d) => (d && typeof d === "object" && "msg" in d ? (d as { msg: string }).msg : String(d))).join(". ");
    }
  } else if (detail && typeof detail === "object" && "msg" in detail && typeof (detail as { msg: unknown }).msg === "string") {
    out = (detail as { msg: string }).msg;
  } else {
    out = typeof detail === "object" ? JSON.stringify(detail) : String(detail);
  }
  return out.trim() || "Something went wrong. Please try again.";
}

export function getStoredToken(): string | null {
  return localStorage.getItem("medora_token");
}

function authHeaders(): HeadersInit {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  timeout?: number;
  skipAuth?: boolean;
};

async function request<T>(path: string, options: RequestOptions): Promise<T> {
  const { body, timeout = API_TIMEOUT_MS, skipAuth, ...rest } = options;
  const url = apiUrl(path);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(url, {
      ...rest,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(skipAuth ? {} : authHeaders()),
        ...(rest.headers as HeadersInit),
      },
      body: body !== undefined && body !== null ? JSON.stringify(body) : undefined,
    });
    const rawText = await res.text();
    if (!res.ok) {
      let parsed: unknown = {};
      try {
        parsed = rawText ? JSON.parse(rawText) : {};
      } catch {
        // non-JSON error body
      }
      const bodyObj = parsed && typeof parsed === "object" ? parsed as Record<string, unknown> : {};
      const detail = ("detail" in bodyObj ? bodyObj.detail : bodyObj) || res.statusText;
      let message = formatApiError(detail);
      if (!message || message.length < 3 || /^[\s\[\]{}]+$/.test(message)) {
        message = res.status === 400 ? "Invalid request. Check your email and password." : "Something went wrong. Please try again.";
      }
      if (res.status === 404) {
        throw new Error("Cannot reach server. Is the backend running? (Try: cd MEDORA/backend && uvicorn app.main:app --reload --port 8000)");
      }
      throw new Error(message);
    }
    try {
      return (rawText ? JSON.parse(rawText) : {}) as T;
    } catch {
      throw new Error("Invalid response from server. Please try again.");
    }
  } catch (err) {
    if (err instanceof Error) {
      if (err.name === "AbortError") throw new Error("Request timed out. Please try again.");
      // "Failed to fetch" = backend unreachable (not running, wrong URL, or CORS)
      if (err.message === "Failed to fetch" || err.message === "Load failed") {
        const base = getBaseUrl();
        throw new Error(
          base
            ? `Cannot reach the server at ${base}. Is the MEDORA backend running? (From MEDORA/backend run: uvicorn app.main:app --reload --port 8000)`
            : "Cannot reach the server. Start the MEDORA backend (e.g. cd MEDORA/backend && uvicorn app.main:app --reload --port 8000)."
        );
      }
      throw err;
    }
    throw new Error("Network error. Please check your connection.");
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health", { method: "GET" });
}

export async function postWellbeingChat(
  req: ChatRequest
): Promise<ChatResponse> {
  return request<ChatResponse>("/wellbeing/chat", { method: "POST", body: req });
}

/** Stream Wellbeing reply as NDJSON. onEvent receives { type: 'meta'|'text'|'done', ... }. */
export async function postWellbeingChatStream(
  req: ChatRequest,
  onEvent: (event: { type: string; content?: string; metadata?: Record<string, unknown> }) => void
): Promise<void> {
  const url = apiUrl("/wellbeing/chat/stream");
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const raw = await res.text();
    let message = "Something went wrong.";
    try {
      const parsed = raw ? JSON.parse(raw) : {};
      const detail = (parsed as Record<string, unknown>).detail;
      message = formatApiError(detail) || message;
    } catch {
      // ignore
    }
    throw new Error(message);
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error("Stream not supported");
  const dec = new TextDecoder();
  let buffer = "";
  try {
    for (; ;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += dec.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        try {
          const event = JSON.parse(trimmed) as { type: string; content?: string; metadata?: Record<string, unknown> };
          onEvent(event);
        } catch {
          // skip malformed line
        }
      }
    }
    if (buffer.trim()) {
      try {
        const event = JSON.parse(buffer.trim()) as { type: string; content?: string; metadata?: Record<string, unknown> };
        onEvent(event);
      } catch {
        // skip
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export async function postOrchestratorChat(
  req: ChatRequestWithImage
): Promise<ChatResponse> {
  return request<ChatResponse>("/chat", { method: "POST", body: req });
}

export async function postVirtualDoctorChat(
  req: ChatRequestWithImage
): Promise<ChatResponse> {
  return request<ChatResponse>("/virtual-doctor/chat", {
    method: "POST",
    body: req,
  });
}

export async function postDietaryChat(
  req: ChatRequest
): Promise<ChatResponse> {
  return request<ChatResponse>("/dietary/chat", { method: "POST", body: req });
}

export async function postDiagnosticChat(
  req: ChatRequestWithImage
): Promise<ChatResponse> {
  return request<ChatResponse>("/diagnostic/chat", {
    method: "POST",
    body: req,
  });
}

// Auth
export async function signUp(req: SignUpRequest): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/signup", {
    method: "POST",
    body: req,
    skipAuth: true,
  });
}

export async function login(req: LoginRequest): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: req,
    skipAuth: true,
  });
}

export async function getMe(): Promise<UserResponse> {
  return request<UserResponse>("/users/me", { method: "GET" });
}

export async function updateProfile(data: UserUpdateRequest): Promise<UserResponse> {
  return request<UserResponse>("/users/me", { method: "PATCH", body: data });
}

export async function getMyChats(): Promise<ChatSessionListItem[]> {
  return request<ChatSessionListItem[]>("/users/me/chats", { method: "GET" });
}

export async function getMyChat(clientSessionId: string): Promise<ChatSessionDetail> {
  return request<ChatSessionDetail>(`/users/me/chats/${encodeURIComponent(clientSessionId)}`, { method: "GET" });
}

// Voice intent classification
export interface VoiceIntentResult {
  action: "navigate" | "send_query" | "toggle_theme" | "greeting" | "logout" | "new_chat";
  target?: string;       // route path for navigate
  query?: string;        // user query for send_query
  speech?: string | null; // text to speak aloud
  response?: string;     // agent response for send_query
  agent_name?: string;   // which agent handled it
  navigate_to?: string;  // route to navigate for send_query
  metadata?: Record<string, unknown>;
}

export async function postVoiceIntent(
  transcript: string,
  sessionId: string = "default",
  context: Array<{ role: string; content: string }> = [],
): Promise<VoiceIntentResult> {
  return request<VoiceIntentResult>("/voice/intent", {
    method: "POST",
    body: { transcript, session_id: sessionId, context },
  });
}

