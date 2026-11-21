// Tipos espelhando os esquemas da API (backend/app/features/*/schemas.py).

export type MaterialStatus = "pending" | "processing" | "done" | "error";
export type MediaType = "audio" | "video" | "pdf" | "text" | "other";

export interface Material {
  id: string;
  filename: string;
  content_type: string | null;
  media_type: MediaType;
  status: MaterialStatus;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMaterial {
  id: string;
  filename: string;
  media_type: MediaType;
  status: MaterialStatus;
}

export interface ChatParams {
  temperature: number;
  similarity_threshold: number;
  retrieval_k: number;
  use_reranker: boolean;
  use_agent: boolean;
}

export interface Chat extends ChatParams {
  id: string;
  name: string;
  materials: ChatMaterial[];
  created_at: string;
  updated_at: string;
}

export interface ChatCreate extends Partial<ChatParams> {
  name: string;
  material_ids: string[];
}

export interface ChatUpdate extends Partial<ChatParams> {
  name?: string;
  material_ids?: string[];
}

// ---- Detalhes do processamento (backend/app/pipeline/answer.py) ----

export interface Candidate {
  material_id: string;
  material_name: string | null;
  chunk_index: number;
  text: string;
  vector_score: number; // 1º estágio, 0 a 1
  rerank_score: number | null; // 2º estágio, 0 a 1 (null se desligado)
  kept: boolean; // usado na resposta
}

export interface Search {
  query: string;
  candidates: Candidate[];
}

export interface AgentStep {
  tool: string;
  input: string;
}

export interface AnswerDetails {
  mode: "agent" | "fixed";
  params: Omit<ChatParams, "use_agent">;
  steps: AgentStep[];
  searches: Search[];
  versions: { extractive: string; final: string };
  history_messages: number;
  elapsed_seconds: number;
}

export interface Message {
  id: string;
  chat_id: string;
  role: "user" | "assistant";
  content: string;
  refused: boolean;
  details: AnswerDetails | null;
  created_at: string;
}

export interface Exchange {
  question: Message;
  answer: Message;
}
