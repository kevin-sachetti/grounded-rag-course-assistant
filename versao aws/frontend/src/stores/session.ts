import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { api, setUnauthorizedHandler } from "../api/client";
import type { Me } from "../api/types";
import { isSignedIn, logout } from "../auth";

// Em que tela a pessoa está:
//   signed-out  tela de entrar / criar conta
//   terms       pop-up dos termos de uso (primeira entrada)
//   retention   pop-up do aviso de 30 dias, logo depois de aceitar os termos
//   ready       o sistema
type Phase = "loading" | "signed-out" | "terms" | "retention" | "ready";

export const useSessionStore = defineStore("session", () => {
  const phase = ref<Phase>("loading");
  const me = ref<Me | null>(null);
  const error = ref<string | null>(null);

  const storageFree = computed(() =>
    me.value ? Math.max(0, me.value.storage_limit_bytes - me.value.storage_used_bytes) : 0,
  );
  const questionsLeft = computed(() =>
    me.value ? Math.max(0, me.value.questions_per_day - me.value.questions_today) : 0,
  );

  setUnauthorizedHandler(() => {
    phase.value = "signed-out";
  });

  async function init() {
    phase.value = "loading";
    if (!(await isSignedIn())) {
      phase.value = "signed-out";
      return;
    }
    await enter();
  }

  /** Depois do login: carrega o usuário e decide se mostra os termos. */
  async function enter() {
    try {
      me.value = await api.me();
      phase.value = me.value.terms_accepted ? "ready" : "terms";
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Não foi possível carregar a sua conta";
      if (phase.value === "loading") phase.value = "signed-out";
    }
  }

  async function acceptTerms() {
    await api.acceptTerms();
    if (me.value) me.value.terms_accepted = true;
    phase.value = "retention";
  }

  function ackRetention() {
    phase.value = "ready";
  }

  /** Atualiza espaço usado e perguntas do dia (depois de enviar ou perguntar). */
  async function refresh() {
    try {
      me.value = await api.me();
    } catch {
      // mantém os números anteriores
    }
  }

  async function signOut() {
    await logout();
    // Recarrega para limpar chats, materiais e conversas da memória.
    window.location.reload();
  }

  async function deleteAccount() {
    await api.deleteAccount();
    await logout().catch(() => {});
    window.location.reload();
  }

  return {
    phase, me, error, storageFree, questionsLeft,
    init, enter, acceptTerms, ackRetention, refresh, signOut, deleteAccount,
  };
});
