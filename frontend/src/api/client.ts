import type { ChatResponse, Course, Material } from "../types";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(`Erro ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listCourses: () => fetch(`${BASE}/courses`).then(asJson<Course[]>),

  getCourse: (id: string) => fetch(`${BASE}/courses/${id}`).then(asJson<Course>),

  createCourse: (name: string, description: string) =>
    fetch(`${BASE}/courses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description: description || null }),
    }).then(asJson<Course>),

  listMaterials: (courseId: string) =>
    fetch(`${BASE}/courses/${courseId}/materials`).then(asJson<Material[]>),

  uploadMaterial: (courseId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/courses/${courseId}/materials`, {
      method: "POST",
      body: form,
    }).then(asJson<Material>);
  },

  chat: (courseId: string, question: string) =>
    fetch(`${BASE}/courses/${courseId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }).then(asJson<ChatResponse>),
};
