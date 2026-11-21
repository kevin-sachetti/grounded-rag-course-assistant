<script setup lang="ts">
import icon from "./assets/grounded-icon.svg";
import AppFooter from "./components/AppFooter.vue";
import AppSidebar from "./components/AppSidebar.vue";
import ChatArea from "./components/ChatArea.vue";
import ChatFormModal from "./components/ChatFormModal.vue";
import MaterialsModal from "./components/MaterialsModal.vue";
import { useUiStore } from "./stores/ui";

const ui = useUiStore();
</script>

<template>
  <div class="layout">
    <!-- Barra do topo: só aparece no celular, para abrir a gaveta do menu -->
    <header class="mobile-bar">
      <button type="button" class="menu-button" aria-label="Abrir menu" @click="ui.toggleMenu()">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" /></svg>
      </button>
      <img class="mobile-icon" :src="icon" alt="" aria-hidden="true" />
      <span class="mobile-title">Grounded RAG Assistant</span>
    </header>

    <AppSidebar />
    <div v-if="ui.menuOpen" class="backdrop" @click="ui.closeMenu()" />
    <ChatArea />
    <AppFooter class="footer" />

    <MaterialsModal v-if="ui.modal === 'materials'" />
    <ChatFormModal v-if="ui.modal === 'new-chat'" mode="new" />
    <ChatFormModal v-if="ui.modal === 'edit-chat'" mode="edit" />
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  grid-template-rows: 1fr auto;
  height: 100%;
}

.footer {
  grid-column: 1 / -1;
}

.mobile-bar,
.backdrop {
  display: none;
}

@media (max-width: 767px) {
  .layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .footer {
    display: none;
  }

  .mobile-bar {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-2) var(--space-3);
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }

  .menu-button {
    display: grid;
    place-items: center;
    width: 40px;
    height: 40px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: transparent;
  }

  .menu-button svg {
    width: 20px;
    height: 20px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.8;
    stroke-linecap: round;
  }

  .mobile-icon {
    width: 32px;
  }

  .mobile-title {
    font-weight: 600;
  }

  .backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 19;
  }
}
</style>
