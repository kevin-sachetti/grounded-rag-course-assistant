<script setup lang="ts">
import { onBeforeUnmount, onMounted } from "vue";

import AppIcon from "./AppIcon.vue";

defineProps<{ title: string; wide?: boolean }>();
const emit = defineEmits<{ close: [] }>();

function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") emit("close");
}
onMounted(() => window.addEventListener("keydown", onKey));
onBeforeUnmount(() => window.removeEventListener("keydown", onKey));
</script>

<template>
  <Teleport to="body">
    <div class="overlay" @click.self="emit('close')">
      <section class="modal" :class="{ wide }" role="dialog" aria-modal="true" :aria-label="title">
        <header class="modal-head">
          <h2>{{ title }}</h2>
          <button type="button" class="icon-button" aria-label="Fechar" @click="emit('close')">
            <AppIcon name="close" />
          </button>
        </header>
        <div class="modal-body">
          <slot />
        </div>
        <footer v-if="$slots.actions" class="modal-actions">
          <slot name="actions" />
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: rgba(6, 5, 4, 0.7);
  animation: fade 140ms ease;
}

.modal {
  display: flex;
  flex-direction: column;
  width: min(520px, 100%);
  max-height: min(86vh, 760px);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
  animation: rise 160ms ease;
}

.modal.wide {
  width: min(680px, 100%);
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--border);
}

.modal-head h2 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
}

.modal-body {
  padding: var(--space-6);
  overflow-y: auto;
}

.modal-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--border);
}

@keyframes fade {
  from {
    opacity: 0;
  }
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
}

@media (max-width: 767px) {
  .modal-head,
  .modal-body,
  .modal-actions {
    padding-left: var(--space-4);
    padding-right: var(--space-4);
  }
}
</style>
