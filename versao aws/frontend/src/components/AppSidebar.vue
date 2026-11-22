<script setup lang="ts">
import { onMounted } from "vue";

import icon from "../assets/grounded-icon.svg";

import { useChatsStore } from "../stores/chats";
import { useUiStore } from "../stores/ui";
import AppFooter from "./AppFooter.vue";
import AppIcon from "./AppIcon.vue";

const store = useChatsStore();
const ui = useUiStore();
onMounted(store.load);

function openChat(id: string) {
  store.open(id);
  ui.closeMenu();
}
</script>

<template>
  <aside class="sidebar" :class="{ open: ui.menuOpen }">
    <div class="brand">
      <img class="brand-icon" :src="icon" alt="" aria-hidden="true" />
      <span class="brand-name">Grounded RAG Assistant</span>
    </div>

    <nav class="actions">
      <button class="action primary" type="button" @click="ui.openModal('new-chat')">
        <AppIcon name="plus" /> Novo chat
      </button>
      <button class="action" type="button" @click="ui.openModal('materials')">
        <AppIcon name="library" /> Materiais
      </button>
      <button class="action" type="button" @click="ui.openModal('account')">
        <AppIcon name="user" /> Minha conta
      </button>
    </nav>

    <section class="chats">
      <h2 class="section-title">Chats</h2>
      <p v-if="store.loading" class="hint">Carregando…</p>
      <p v-else-if="store.error" class="hint error">{{ store.error }}</p>
      <p v-else-if="!store.chats.length" class="hint">Nenhum chat ainda. Crie um para começar.</p>
      <ul v-else class="chat-list">
        <li v-for="chat in store.chats" :key="chat.id">
          <button
            type="button"
            class="chat-item"
            :class="{ active: chat.id === store.activeId }"
            @click="openChat(chat.id)"
          >
            {{ chat.name }}
          </button>
        </li>
      </ul>
    </section>

    <!-- No celular o rodapé mora aqui dentro, para não ocupar a tela da conversa. -->
    <AppFooter class="drawer-footer" />
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  padding: var(--space-4);
  overflow-y: auto;
  background: var(--surface);
  border-right: 1px solid var(--border);
  min-height: 0;
}

.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) 0 0;
}

.brand-icon {
  width: var(--brand-icon-size);
}

.brand-name {
  font-size: var(--text-md);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.action {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-align: left;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: transparent;
  transition: background var(--transition), border-color var(--transition);
}

.action:hover {
  background: var(--surface-2);
}

.action.primary {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.action.primary:hover {
  background: var(--accent-soft);
}

.chats {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-height: 0;
  overflow-y: auto;
}

.section-title {
  margin: 0;
  padding: 0 var(--space-2);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-faint);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.hint {
  margin: 0;
  padding: 0 var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.hint.error {
  color: var(--danger);
}

.chat-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.chat-item {
  width: 100%;
  text-align: left;
  padding: var(--space-2);
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background var(--transition), color var(--transition);
}

.chat-item:hover {
  background: var(--surface-2);
  color: var(--text);
}

.chat-item.active {
  background: var(--surface-3);
  color: var(--text);
}

.drawer-footer {
  display: none;
}

/* Celular: o menu vira uma gaveta que entra pela esquerda */
@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 20;
    width: min(86vw, var(--sidebar-width));
    transform: translateX(-100%);
    transition: transform 200ms ease;
  }

  .sidebar.open {
    transform: none;
    box-shadow: 0 0 0 100vmax rgba(0, 0, 0, 0.55);
  }

  .brand-icon {
    width: 150px;
  }

  .drawer-footer {
    display: block;
    margin: auto calc(-1 * var(--space-4)) calc(-1 * var(--space-4));
  }
}
</style>
