<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { useSessionStore } from "../stores/session";
import { useUiStore } from "../stores/ui";
import BaseModal from "./BaseModal.vue";

const session = useSessionStore();
const ui = useUiStore();
const confirming = ref(false);
const busy = ref(false);
const error = ref<string | null>(null);

onMounted(session.refresh);

const mb = (bytes: number) =>
  (bytes / (1024 * 1024)).toLocaleString("pt-BR", { maximumFractionDigits: bytes < 10 * 1024 * 1024 ? 1 : 0 });
const used = computed(() => session.me?.storage_used_bytes ?? 0);
const limit = computed(() => session.me?.storage_limit_bytes ?? 1);
const pct = computed(() => `${Math.min(100, (used.value / limit.value) * 100)}%`);

async function remove() {
  busy.value = true;
  error.value = null;
  try {
    await session.deleteAccount();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Não foi possível excluir a conta";
    busy.value = false;
  }
}
</script>

<template>
  <BaseModal title="Minha conta" @close="ui.closeModal()">
    <div v-if="session.me" class="usage">
      <div class="row">
        <span>Espaço usado</span>
        <span class="value">{{ mb(used) }} de {{ mb(limit) }} MB</span>
      </div>
      <div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="parseFloat(pct)">
        <span :style="{ width: pct }" />
      </div>

      <div class="row">
        <span>Perguntas hoje</span>
        <span class="value">{{ session.me.questions_today }} de {{ session.me.questions_per_day }}</span>
      </div>
      <p class="note">O limite de perguntas renova à meia-noite.</p>

      <p v-if="session.me.month_blocked" class="blocked">
        O limite de uso da demonstração deste mês foi atingido. Você ainda pode ver seus chats e materiais, mas
        novas perguntas e envios voltam no próximo mês. Para usar sem limites, instale a
        <a href="https://github.com/kevin-sachetti/grounded-rag-course-assistant" target="_blank" rel="noopener">versão local</a>.
      </p>

      <p class="note">
        Se você ficar {{ session.me.inactivity_days }} dias sem entrar, seus chats e materiais são apagados
        automaticamente.
      </p>
    </div>

    <p v-if="error" class="form-error">{{ error }}</p>

    <template #actions>
      <template v-if="confirming">
        <span class="confirm-text">Excluir a conta, os chats e os materiais? Não tem volta.</span>
        <button type="button" class="btn danger" :disabled="busy" @click="remove">Excluir de vez</button>
        <button type="button" class="btn" :disabled="busy" @click="confirming = false">Cancelar</button>
      </template>
      <template v-else>
        <button type="button" class="btn danger delete" @click="confirming = true">Excluir conta</button>
        <button type="button" class="btn" @click="session.signOut()">Sair</button>
      </template>
    </template>
  </BaseModal>
</template>

<style scoped>
.usage {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.row {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-sm);
}

.value {
  font-variant-numeric: tabular-nums;
  color: var(--accent-strong);
}

.bar {
  height: 6px;
  margin-bottom: var(--space-3);
  overflow: hidden;
  border-radius: 999px;
  background: var(--surface-3);
}

.bar span {
  display: block;
  height: 100%;
  background: var(--accent);
}

.note {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.blocked {
  margin: var(--space-2) 0;
  padding: var(--space-3);
  border: 1px dashed var(--accent);
  border-radius: var(--radius);
  font-size: var(--text-sm);
  color: var(--accent-strong);
}

.delete {
  margin-right: auto;
}

.confirm-text {
  margin-right: auto;
  align-self: center;
  font-size: var(--text-sm);
  color: var(--text-muted);
}
</style>
