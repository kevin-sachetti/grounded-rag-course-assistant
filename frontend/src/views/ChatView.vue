<script setup lang="ts">
import { ref } from "vue";
import { api } from "../api/client";
import type { Source } from "../types";

const props = defineProps<{ id: string }>();

interface Message {
  role: "user" | "bot";
  text: string;
  sources?: Source[];
}

const messages = ref<Message[]>([]);
const question = ref("");
const loading = ref(false);

async function send() {
  const q = question.value.trim();
  if (!q) return;

  messages.value.push({ role: "user", text: q });
  question.value = "";
  loading.value = true;

  try {
    const res = await api.chat(props.id, q);
    messages.value.push({ role: "bot", text: res.answer, sources: res.sources });
  } catch {
    messages.value.push({ role: "bot", text: "Erro ao responder." });
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <h1>Chat do curso</h1>

  <div class="chat">
    <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
      <p>{{ m.text }}</p>
      <small v-if="m.sources && m.sources.length" class="sources">
        Baseado em {{ m.sources.length }} trecho(s) do material
      </small>
    </div>
    <p v-if="messages.length === 0" class="empty">
      Faça uma pergunta sobre o conteúdo do curso.
    </p>
  </div>

  <form class="row" @submit.prevent="send">
    <input
      v-model="question"
      placeholder="Faça uma pergunta..."
      :disabled="loading"
    />
    <button :disabled="loading">Enviar</button>
  </form>
</template>

<style scoped>
.chat {
  min-height: 300px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
.msg {
  max-width: 80%;
  padding: 10px 12px;
  border-radius: 10px;
  margin-bottom: 10px;
}
.msg p {
  margin: 0;
  white-space: pre-wrap;
}
.msg.user {
  margin-left: auto;
  background: #2563eb;
  color: #fff;
}
.msg.bot {
  background: #f1f5f9;
}
.sources {
  display: block;
  margin-top: 6px;
  opacity: 0.7;
  font-size: 11px;
}
.row {
  display: flex;
  gap: 8px;
}
.row input {
  flex: 1;
}
.empty {
  color: #6b7280;
}
</style>
