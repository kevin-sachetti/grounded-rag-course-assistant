<script setup lang="ts">
import { onMounted, ref } from "vue";

import type { MediaType } from "../api/types";
import { useChatsStore } from "../stores/chats";
import { SUPPORTED_EXT, useMaterialsStore } from "../stores/materials";
import { useSessionStore } from "../stores/session";
import { useUiStore } from "../stores/ui";
import { statusLabel } from "../utils/format";
import AppIcon from "./AppIcon.vue";
import BaseModal from "./BaseModal.vue";

const ACCEPT = SUPPORTED_EXT.map((e) => `.${e}`).join(",");

const store = useMaterialsStore();
const chats = useChatsStore();
const ui = useUiStore();
const session = useSessionStore();
const freeMb = () => Math.floor(session.storageFree / (1024 * 1024));
const input = ref<HTMLInputElement | null>(null);
const dragging = ref(false);
const confirming = ref<string | null>(null);

onMounted(store.load);

function icon(t: MediaType): "pdf" | "text" {
  return t === "pdf" ? "pdf" : "text";
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
      <p class="drop-hint">
        Texto, Markdown, PDF, Word, PowerPoint e Excel · {{ freeMb() }} MB livres no seu espaço
      </p>
      <p class="drop-hint">
        Áudio e vídeo só na
        <a href="https://github.com/kevin-sachetti/grounded-rag-course-assistant" target="_blank" rel="noopener" @click.stop>versão local</a>.
      </p>
      <input ref="input" type="file" multiple :accept="ACCEPT" hidden @change="pick" />
    </div>

    <p v-if="store.uploading" class="note">Enviando {{ store.uploading }} arquivo(s)…</p>
    <p v-if="store.error" class="form-error">{{ store.error }}</p>
    <div v-if="store.rejected.length" class="rejected" role="alert">
      <p class="form-error">Não enviado:</p>
      <ul>
        <li v-for="r in store.rejected" :key="r" class="form-error">{{ r }}</li>
      </ul>
    </div>

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
            <span v-if="m.status === 'uploading'">enviando</span>
            <span v-if="m.status === 'pending'">aguardando a vez</span>
            <span v-if="m.status === 'processing' && m.stage">{{ m.stage }} · {{ m.progress ?? 0 }}%</span>
          </span>
          <div
            v-if="m.status === 'uploading' || m.status === 'pending' || m.status === 'processing'"
            class="progress"
            :class="{ waiting: m.progress == null }"
            role="progressbar"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-valuenow="m.progress ?? undefined"
          >
            <span :style="{ width: m.progress != null ? `${m.progress}%` : undefined }" />
          </div>
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
      Excluir um material apaga o arquivo e os trechos dele, libera o espaço, e ele sai de todos os chats que o
      usavam.
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

.progress {
  position: relative;
  height: 4px;
  margin-top: var(--space-1);
  overflow: hidden;
  border-radius: 999px;
  background: var(--surface-3);
}

.progress span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
  transition: width 0.6s ease;
}

/* Sem percentual (na fila): um trecho da barra vai e volta. */
.progress.waiting span {
  width: 30%;
  animation: waiting 1.4s ease-in-out infinite alternate;
}

@keyframes waiting {
  from { transform: translateX(-10%); }
  to { transform: translateX(240%); }
}

@media (prefers-reduced-motion: reduce) {
  .progress.waiting span { animation: none; width: 100%; opacity: 0.35; }
}

.rejected ul {
  margin: var(--space-1) 0 0;
  padding-left: var(--space-4);
}

.rejected .form-error {
  margin: 0;
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
