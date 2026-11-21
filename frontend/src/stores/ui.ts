import { defineStore } from "pinia";
import { ref } from "vue";

export type Modal = "materials" | "new-chat" | "edit-chat" | null;

// Estado da tela que não vem da API: gaveta do menu (celular) e janela aberta.
export const useUiStore = defineStore("ui", () => {
  const menuOpen = ref(false);
  const modal = ref<Modal>(null);

  function toggleMenu() {
    menuOpen.value = !menuOpen.value;
  }

  function closeMenu() {
    menuOpen.value = false;
  }

  function openModal(m: Exclude<Modal, null>) {
    modal.value = m;
    menuOpen.value = false;
  }

  function closeModal() {
    modal.value = null;
  }

  return { menuOpen, modal, toggleMenu, closeMenu, openModal, closeModal };
});
