<script setup lang="ts">
import { ref } from "vue";

import { TERMS } from "../legal/terms";
import { useSessionStore } from "../stores/session";
import BaseModal from "./BaseModal.vue";

const session = useSessionStore();
const busy = ref(false);
const error = ref<string | null>(null);

async function accept() {
  busy.value = true;
  error.value = null;
  try {
    await session.acceptTerms();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Não foi possível registrar o aceite";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <BaseModal title="Termos de uso" wide locked>
    <div class="terms">
      <p v-for="(p, i) in TERMS" :key="i">{{ p }}</p>
    </div>
    <p v-if="error" class="form-error">{{ error }}</p>
    <template #actions>
      <button type="button" class="btn" :disabled="busy" @click="session.signOut()">Recusar e sair</button>
      <button type="button" class="btn primary" :disabled="busy" @click="accept">Li e aceito</button>
    </template>
  </BaseModal>
</template>

<style scoped>
.terms {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  font-size: var(--text-sm);
  line-height: 1.55;
  color: var(--text-muted);
}

.terms p {
  margin: 0;
}
</style>
