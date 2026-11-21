<script setup lang="ts">
import { onMounted, ref } from "vue";

import type { MediaType } from "../api/types";
import { useChatsStore } from "../stores/chats";
import { useMaterialsStore } from "../stores/materials";
import { useUiStore } from "../stores/ui";
import { statusLabel } from "../utils/format";
import AppIcon from "./AppIcon.vue";
import BaseModal from "./BaseModal.vue";

const ACCEPT = ".txt,.md,.pdf,.mp3,.wav,.m4a,.ogg,.flac,.aac,.mp4,.mov,.mkv,.avi,.webm";

const store = useMaterialsStore();
const chats = useChatsStore();
const ui = useUiStore();
const input = ref<HTMLInputElement | null>(null);
const dragging = ref(false);
const confirming = ref<string | null>(null);

onMounted(store.load);

function icon(t: MediaType): "audio" | "video" | "pdf" | "text" {
  return t === "audio" || t === "video" || t === "pdf" ? t : "text";
}

function badge(status: string) {
  if (status === "done") return "ok";
  if (status === "error") return "bad";
  return "busy";
}

function pick(e: Event) {
  const files = (e.target as HTMLInputElement).files;
  if (files?.length) store.upload([...files]);
  if (input.value) input.value.value = "";
}

function drop(e: DragEvent) {
  dragging.value = false;
  const files = e.dataTransfer?.files;
  if (files?.length) store.upload([...files]);
}

async function remove(id: string) {
  confirming.value = null;
  await store.remove(id);
  // Os chats que usavam o material perdem a ligação: recarrega a lista.
  await chats.load();
}
</script>

<template>
  <BaseModal title="Materiais" wide @close="ui.closeModal()">
    <div
      class="drop"
      :class="{ dragging }"
      role="button"
      tabindex="0"
      @click="input?.click()"
      @keydown.enter="input?.click()"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="drop"
    >
      <AppIcon name="upload" :size="26" />
      <p class="drop-title">Arraste arquivos ou clique para enviar</p>
      <p class="drop-hint">Texto, Markdown, PDF, áudio (mp3, wav, m4a…) e vídeo (mp4, mov…)</p>
      <input ref="input" type="file" multiple :accept="ACCEPT" hidden @change="pick" />
    </div>

    <p v-if="store.uploading" class="note">Enviando {{ store.uploading }} arquivo(s)…</p>
    <p v-if="store.error" class="form-error">{{ store.error }}</p>

    <p v-if="!store.materials.length && !store.loading" class="empty">
      A biblioteca está vazia. Os materiais enviados aqui podem ser usados em qualquer chat.
    </p>

    <ul class="list">
      <li v-for="m in store.materials" :key="m.id" class="item">
        <span class="type"><AppIcon :name="icon(m.media_type)" :size="20" /></span>
        <div class="info">
          <span class="name" :title="m.filename">{{ m.filename }}</span>
          <span class="meta">
            <span class="badge" :class="badge(m.status)">{{ statusLabel(m.status) }}</span>
            <span v-if="m.status === 'done'">{{ m.chunk_count }} {{ m.chunk_count === 1 ? "trecho" : "trechos" }}</span>
            <span v-if="m.status === 'error'">não foi possível ler este arquivo</span>
          </span>
        </div>

        <div v-if="confirming === m.id" class="confirm">
          <span>Excluir de vez?</span>
          <button type="button" class="btn danger" @click="remove(m.id)">Excluir</button>
          <button type="button" class="btn" @click="confirming = null">Cancelar</button>
        </div>
        <button v-else type="button" class="icon-button" aria-label="Excluir material" @click="confirming = m.id">
          <AppIcon name="trash" />
        </button>
      </li>
    </ul>

    <p class="note">
      Excluir um material apaga o arquivo e os trechos dele, e ele sai de todos os chats que o usavam.
    </p>
  </BaseModal>
</template>

<style scoped>
.drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-6);
  border: 1.5px dashed var(--border-strong);
  border-radius: var(--radius-lg);
  color: var(--text-muted);
  text-align: center;
  cursor: pointer;
  transition: border-color var(--transition), background var(--transition);
}

.drop:hover,
.drop.dragging {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.drop-title {
  margin: var(--space-2) 0 0;
  color: var(--text);
}

.drop-hint {
  margin: 0;
  font-size: var(--text-sm);
}

.empty,
.note {
  margin: var(--space-4) 0 0;
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.list {
  list-style: none;
  margin: var(--space-4) 0 0;
  padding: 0;
}

.item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--border);
}

.type {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  flex: none;
  border-radius: var(--radius);
  background: var(--surface-2);
  color: var(--accent-strong);
}

.info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.name {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-faint);
}

.confirm {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.confirm .btn {
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-sm);
}
</style>
