import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "../api/client";
import type { Message } from "../api/types";
import { useChatsStore } from "./chats";

// Conversas, por chat. Enquanto a resposta não chega, a pergunta aparece na
// tela como "pendente"; quando a API responde, entram as duas mensagens salvas.
export const useMessagesStore = defineStore("messages", () => {
  const byChat = ref<Record<string, Message[]>>({});
  const loading = ref(false);
  const pending = ref<Record<string, string>>({}); // chatId -> pergunta em andamento
  const error = ref<Record<string, string>>({});

  async function load(chatId: string) {
    if (byChat.value[chatId]) return;
    loading.value = true;
    try {
      byChat.value[chatId] = await api.listMessages(chatId);
    } catch (e) {
      error.value[chatId] = e instanceof Error ? e.message : "Não foi possível carregar a conversa";
    } finally {
      loading.value = false;
    }
  }

  async function send(chatId: string, content: string): Promise<boolean> {
    pending.value[chatId] = content;
    delete error.value[chatId];
    try {
      const { question, answer } = await api.sendMessage(chatId, content);
      (byChat.value[chatId] ??= []).push(question, answer);
      useChatsStore().touch(chatId);
      return true;
    } catch (e) {
      error.value[chatId] = e instanceof Error ? e.message : "Não foi possível gerar a resposta";
      return false;
    } finally {
      delete pending.value[chatId];
    }
  }

  return { byChat, loading, pending, error, load, send };
});
