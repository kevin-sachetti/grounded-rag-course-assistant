// Tipos espelhando os esquemas da API (backend/app/features/*/schemas.py).

export type MaterialStatus = "uploading" | "pending" | "processing" | "done" | "error";
// Na versão AWS só documentos; áudio e vídeo ficam na versão local.
export type MediaType = "pdf" | "text" | "document";

export interface Material {
  id: string;
  filename: string;
  media_type: MediaType;
  size_bytes: number;
  status: MaterialStatus;
  chunk_count: number;
  /** Só durante o processamento: etapa atual e percentual (0 a 100). */
  stage?: string | null;
  progress?: number | null;
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
  params: ChatParams;
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

// ---- Usuário (backend/app/features/users/router.py) ----

export interface Me {
  terms_accepted: boolean;
  storage_used_bytes: number;
  storage_limit_bytes: number;
  questions_today: number;
  questions_per_day: number;
  inactivity_days: number;
  month_blocked: boolean;
}

/** Resposta da 1ª etapa do envio: o material e o formulário para o S3. */
export interface UploadTicket {
  material: Material;
  url: string;
  fields: Record<string, string>;
}
