export interface ChatRequest {
  message: string;
  session_id?: string | null;
}

export interface ChatResponse {
  reply: string;
  session_id?: string | null;
}
