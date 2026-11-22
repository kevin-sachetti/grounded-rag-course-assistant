import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { api } from "../api/client";
import type { Chat, ChatCreate, ChatUpdate } from "../api/types";

// Lista de chats do menu lateral e qual deles está aberto.
export const useChatsStore = defineStore("chats", () => {
  const chats = ref<Chat[]>([]);
  const activeId = ref<string | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const active = computed(() => chats.value.find((c) => c.id === activeId.value) ?? null);

  async function load() {
    loading.value = true;
    error.value = null;
    try {
      chats.value = await api.listChats();
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Não foi possível carregar os chats";
    } finally {
      loading.value = false;
    }
  }

  function open(id: string) {
    activeId.value = id;
  }

  async function create(data: ChatCreate) {
    const chat = await api.createChat(data);
    chats.value.unshift(chat);
    activeId.value = chat.id;
    return chat;
  }

  async function update(id: string, data: ChatUpdate) {
    const chat = await api.updateChat(id, data);
    chats.value = chats.value.map((c) => (c.id === id ? chat : c));
    return chat;
  }

  async function remove(id: string) {
    await api.deleteChat(id);
    chats.value = chats.value.filter((c) => c.id !== id);
    if (activeId.value === id) activeId.value = null;
  }

  // Depois de uma resposta o chat sobe para o topo da lista.
  function touch(id: string) {
    const i = chats.value.findIndex((c) => c.id === id);
    if (i > 0) chats.value.unshift(...chats.value.splice(i, 1));
  }

  return { chats, activeId, active, loading, error, load, open, create, update, remove, touch };
});
