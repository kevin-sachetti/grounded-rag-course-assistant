// Cliente da API. Uma função por rota (ver docs da API em /docs no backend).

import { accessToken } from "../auth";
import type {
  Chat,
  ChatCreate,
  ChatUpdate,
  Exchange,
  Material,
  Me,
  Message,
  UploadTicket,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

// Avisado quando a sessão expira (401), para a tela voltar ao login.
let onUnauthorized: () => void = () => {};
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await accessToken().catch(() => null);
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    let message = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // corpo sem JSON: fica a mensagem genérica
    }
    if (res.status === 401) onUnauthorized();
    throw new ApiError(res.status, message);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

function json(method: string, body: unknown): RequestInit {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

/** Envia o arquivo direto ao S3, com o formulário que a API gerou. */
async function sendToStorage(ticket: UploadTicket, file: File): Promise<void> {
  const form = new FormData();
  for (const [k, v] of Object.entries(ticket.fields)) form.append(k, v);
  form.append("file", file); // precisa ser o último campo
  const res = await fetch(ticket.url, { method: "POST", body: form });
  if (!res.ok) throw new ApiError(res.status, "Não foi possível enviar o arquivo. Tente de novo.");
}

export const api = {
  // Usuário
  me: () => request<Me>("/me"),
  acceptTerms: () => request<void>("/me/terms", { method: "POST" }),
  deleteAccount: () => request<void>("/me", { method: "DELETE" }),

  // Biblioteca de materiais: pede o endereço, envia ao S3 e confirma.
  listMaterials: () => request<Material[]>("/materials"),
  getMaterial: (id: string) => request<Material>(`/materials/${id}`),
  uploadMaterial: async (file: File) => {
    const ticket = await request<UploadTicket>(
      "/materials/upload",
      json("POST", { filename: file.name, size: file.size }),
    );
    await sendToStorage(ticket, file);
    return request<Material>(`/materials/${ticket.material.id}/confirm`, { method: "POST" });
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
