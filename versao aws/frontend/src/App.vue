<script setup lang="ts">
import { onMounted } from "vue";

import icon from "./assets/grounded-icon.svg";
import AccountModal from "./components/AccountModal.vue";
import AppFooter from "./components/AppFooter.vue";
import AuthScreen from "./components/AuthScreen.vue";
import AppSidebar from "./components/AppSidebar.vue";
import ChatArea from "./components/ChatArea.vue";
import ChatFormModal from "./components/ChatFormModal.vue";
import MaterialsModal from "./components/MaterialsModal.vue";
import RetentionModal from "./components/RetentionModal.vue";
import TermsModal from "./components/TermsModal.vue";
import { useSessionStore } from "./stores/session";
import { useUiStore } from "./stores/ui";

const ui = useUiStore();
const session = useSessionStore();
onMounted(session.init);
</script>

<template>
  <div v-if="session.phase === 'loading'" class="loading" aria-busy="true">
    <img :src="icon" alt="" aria-hidden="true" />
  </div>

  <AuthScreen v-else-if="session.phase === 'signed-out'" />

  <div v-else class="layout">
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
    <AccountModal v-if="ui.modal === 'account'" />

    <!-- Primeira entrada: termos de uso e, depois de aceitar, o aviso dos 30 dias -->
    <TermsModal v-if="session.phase === 'terms'" />
    <RetentionModal v-if="session.phase === 'retention'" />
  </div>
</template>

<style scoped>
.loading {
  display: grid;
  place-items: center;
  height: 100%;
}

.loading img {
  width: 96px;
  border-radius: 18px;
  opacity: 0.6;
}

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
