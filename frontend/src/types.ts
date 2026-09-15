export interface Course {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Material {
  id: string;
  course_id: string;
  filename: string;
  content_type: string | null;
  media_type: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Source {
  material_id: string | null;
  chunk_index: number | null;
  score: number | null;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}
