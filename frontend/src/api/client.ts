// Cliente da API. Uma função por rota (ver docs da API em /docs no backend).

import type { Chat, ChatCreate, ChatUpdate, Exchange, Material, Message } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) {
    let message = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // corpo sem JSON: fica a mensagem genérica
    }
    throw new ApiError(res.status, message);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

function json(method: string, body: unknown): RequestInit {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export const api = {
  // Biblioteca de materiais
  listMaterials: () => request<Material[]>("/materials"),
  getMaterial: (id: string) => request<Material>(`/materials/${id}`),
  uploadMaterial: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Material>("/materials", { method: "POST", body: form });
  },
  deleteMaterial: (id: string) => request<void>(`/materials/${id}`, { method: "DELETE" }),

  // Chats
  listChats: () => request<Chat[]>("/chats"),
  getChat: (id: string) => request<Chat>(`/chats/${id}`),
  createChat: (data: ChatCreate) => request<Chat>("/chats", json("POST", data)),
  updateChat: (id: string, data: ChatUpdate) => request<Chat>(`/chats/${id}`, json("PATCH", data)),
  deleteChat: (id: string) => request<void>(`/chats/${id}`, { method: "DELETE" }),

  // Mensagens
  listMessages: (chatId: string) => request<Message[]>(`/chats/${chatId}/messages`),
  sendMessage: (chatId: string, content: string) =>
    request<Exchange>(`/chats/${chatId}/messages`, json("POST", { content })),
};
