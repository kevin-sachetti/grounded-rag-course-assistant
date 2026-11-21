<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";

import treeBg from "../assets/grounded-tree-bg.svg";
import { useChatsStore } from "../stores/chats";
import { useMessagesStore } from "../stores/messages";
import { useUiStore } from "../stores/ui";
import AppIcon from "./AppIcon.vue";
import MessageItem from "./MessageItem.vue";
import RootLoader from "./RootLoader.vue";

const chats = useChatsStore();
const messages = useMessagesStore();
const ui = useUiStore();

const draft = ref("");
const scroller = ref<HTMLElement | null>(null);
const box = ref<HTMLTextAreaElement | null>(null);

const chat = computed(() => chats.active);
const list = computed(() => (chat.value ? messages.byChat[chat.value.id] ?? [] : []));
const pending = computed(() => (chat.value ? messages.pending[chat.value.id] : undefined));
const error = computed(() => (chat.value ? messages.error[chat.value.id] : undefined));
const notReady = computed(() => chat.value?.materials.filter((m) => m.status !== "done").length ?? 0);

watch(
  () => chat.value?.id,
  async (id) => {
    if (!id) return;
    await messages.load(id);
    scrollDown();
  },
  { immediate: true },
);

watch(() => [list.value.length, pending.value], scrollDown);

async function scrollDown() {
  await nextTick();
  scroller.value?.scrollTo({ top: scroller.value.scrollHeight, behavior: "smooth" });
}

async function send() {
  const text = draft.value.trim();
  if (!text || !chat.value || pending.value) return;
  draft.value = "";
  resize();
  const ok = await messages.send(chat.value.id, text);
  if (!ok) draft.value = text; // devolve a pergunta para tentar de novo
}

function onKey(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

function resize() {
  const el = box.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
}
</script>

<template>
  <main class="chat-area">
    <!-- Árvore monocromática grande, bem apagada, atrás da conversa. -->
    <img class="tree-bg" :src="treeBg" alt="" aria-hidden="true" />

    <!-- Nenhum chat aberto -->
    <div v-if="!chat" class="welcome">
      <h1>Grounded RAG Assistant</h1>
      <p>Respostas só com base no seu material — e você vê de onde cada uma veio.</p>
      <div class="welcome-actions">
        <button type="button" class="btn primary" @click="ui.openModal('new-chat')">
          <AppIcon name="plus" /> Novo chat
        </button>
        <button type="button" class="btn" @click="ui.openModal('materials')">
          <AppIcon name="library" /> Materiais
        </button>
      </div>
    </div>

    <template v-else>
      <header class="chat-head">
        <div class="chat-title">
          <h1>{{ chat.name }}</h1>
          <span class="chat-meta">
            {{ chat.materials.length }} material{{ chat.materials.length === 1 ? "" : "is" }}
            · {{ chat.use_agent ? "agente" : "fluxo fixo" }}
          </span>
        </div>
        <button type="button" class="btn" @click="ui.openModal('edit-chat')">
          <AppIcon name="settings" /> Editar chat
        </button>
      </header>

      <div ref="scroller" class="scroller">
        <div class="thread">
          <div v-if="!chat.materials.length" class="notice">
            Este chat ainda não tem materiais, então não há de onde tirar respostas.
            <button type="button" class="link" @click="ui.openModal('edit-chat')">Escolher materiais</button>
          </div>
          <div v-else-if="notReady" class="notice">
            {{ notReady }} material(is) deste chat ainda está(ão) sendo processado(s); o conteúdo deles entra nas
            respostas quando ficar pronto.
          </div>

          <p v-if="!list.length && !pending && chat.materials.length" class="start">
            Pergunte qualquer coisa sobre o material. Se ele não tiver a resposta, o assistente avisa.
          </p>

          <MessageItem v-for="m in list" :key="m.id" :message="m" />

          <template v-if="pending">
            <article class="pending-question">{{ pending }}</article>
            <RootLoader />
          </template>

          <p v-if="error" class="form-error">{{ error }}</p>
        </div>
      </div>

      <form class="composer" @submit.prevent="send">
        <textarea
          ref="box"
          v-model="draft"
          class="input"
          rows="1"
          placeholder="Pergunte algo sobre o material…"
          :disabled="!!pending"
          @input="resize"
          @keydown="onKey"
        />
        <button type="submit" class="send" :disabled="!draft.trim() || !!pending" aria-label="Enviar">
          <AppIcon name="send" />
        </button>
      </form>
    </template>
  </main>
</template>

<style scoped>
.chat-area {
  position: relative;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: var(--bg);
}

.tree-bg {
  position: absolute;
  left: 50%;
  top: 50%;
  height: 92%;
  max-width: 92%;
  transform: translate(-50%, -50%);
  opacity: var(--tree-bg-opacity);
  pointer-events: none;
  user-select: none;
}

.welcome {
  position: relative;
  margin: auto;
  max-width: var(--chat-max-width);
  padding: var(--space-8);
  text-align: center;
}

.welcome h1 {
  margin: 0 0 var(--space-2);
  font-size: 1.6rem;
  font-weight: 600;
}

.welcome p {
  margin: 0;
  color: var(--text-muted);
}

.welcome-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-3);
  margin-top: var(--space-6);
}

.chat-head {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-6);
  border-bottom: 1px solid var(--border);
  background: rgba(14, 13, 12, 0.75);
}

.chat-title {
  min-width: 0;
}

.chat-title h1 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chat-meta {
  font-size: var(--text-sm);
  color: var(--text-faint);
}

.scroller {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.thread {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: var(--chat-max-width);
  margin: 0 auto;
  padding: var(--space-6);
}

.notice {
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  background: var(--surface);
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.link {
  padding: 0;
  border: none;
  background: none;
  color: var(--accent-strong);
  text-decoration: underline;
}

.start {
  margin: var(--space-8) 0 0;
  text-align: center;
  color: var(--text-muted);
}

.pending-question {
  align-self: flex-end;
  max-width: min(80%, 560px);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg);
  background: var(--surface-3);
  white-space: pre-wrap;
  opacity: 0.8;
}

.composer {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: var(--space-2);
  width: 100%;
  max-width: var(--chat-max-width);
  margin: 0 auto;
  padding: var(--space-3) var(--space-6) var(--space-6);
}

.composer textarea {
  flex: 1;
  min-height: 46px;
  max-height: 200px;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  background: var(--surface);
  resize: none;
  line-height: 1.45;
}

.send {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  flex: none;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--accent);
  color: #1a140d;
  transition: background var(--transition), opacity var(--transition);
}

.send:hover:not(:disabled) {
  background: var(--accent-strong);
}

.send:disabled {
  opacity: 0.35;
  cursor: default;
}

@media (max-width: 767px) {
  .chat-head {
    padding: var(--space-2) var(--space-4);
  }

  .chat-head .btn {
    padding: var(--space-2);
  }

  .thread {
    padding: var(--space-4);
  }

  .composer {
    padding: var(--space-2) var(--space-3) var(--space-3);
  }
}
</style>
