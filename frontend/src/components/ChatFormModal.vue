<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { useChatsStore } from "../stores/chats";
import { useMaterialsStore } from "../stores/materials";
import { useUiStore } from "../stores/ui";
import { statusLabel } from "../utils/format";
import BaseModal from "./BaseModal.vue";

const props = defineProps<{ mode: "new" | "edit" }>();

const chats = useChatsStore();
const materials = useMaterialsStore();
const ui = useUiStore();

const editing = computed(() => (props.mode === "edit" ? chats.active : null));

// Valores iniciais de um chat novo: os mesmos dos experimentos, agente ligado.
const form = reactive({
  name: editing.value?.name ?? "",
  material_ids: editing.value?.materials.map((m) => m.id) ?? ([] as string[]),
  temperature: editing.value?.temperature ?? 0.6,
  similarity_threshold: editing.value?.similarity_threshold ?? 0.6,
  retrieval_k: editing.value?.retrieval_k ?? 3,
  use_reranker: editing.value?.use_reranker ?? true,
  use_agent: editing.value?.use_agent ?? true,
});

const saving = ref(false);
const error = ref<string | null>(null);
const confirmDelete = ref(false);

onMounted(materials.load);

function toggleMaterial(id: string) {
  const i = form.material_ids.indexOf(id);
  if (i >= 0) form.material_ids.splice(i, 1);
  else form.material_ids.push(id);
}

async function save() {
  if (!form.name.trim()) {
    error.value = "Dê um nome ao chat.";
    return;
  }
  saving.value = true;
  error.value = null;
  try {
    const data = { ...form, name: form.name.trim() };
    if (editing.value) await chats.update(editing.value.id, data);
    else await chats.create(data);
    ui.closeModal();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Não foi possível salvar";
  } finally {
    saving.value = false;
  }
}

async function remove() {
  if (!editing.value) return;
  saving.value = true;
  try {
    await chats.remove(editing.value.id);
    ui.closeModal();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Não foi possível excluir";
  } finally {
    saving.value = false;
  }
}

const fmt = (n: number) => n.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
</script>

<template>
  <BaseModal :title="mode === 'new' ? 'Novo chat' : 'Editar chat'" wide @close="ui.closeModal()">
    <form class="form" @submit.prevent="save">
      <label class="field">
        <span class="field-label">Nome</span>
        <input v-model="form.name" class="input" maxlength="200" placeholder="Biologia — fotossíntese" autofocus />
      </label>

      <fieldset class="group">
        <legend class="field-label">Materiais que este chat usa</legend>
        <p v-if="!materials.materials.length" class="hint">
          A biblioteca está vazia.
          <button type="button" class="link" @click="ui.openModal('materials')">Enviar materiais</button>
        </p>
        <label v-for="m in materials.materials" :key="m.id" class="check">
          <input type="checkbox" :checked="form.material_ids.includes(m.id)" @change="toggleMaterial(m.id)" />
          <span class="check-name">{{ m.filename }}</span>
          <span v-if="m.status !== 'done'" class="badge" :class="m.status === 'error' ? 'bad' : 'busy'">
            {{ statusLabel(m.status) }}
          </span>
        </label>
      </fieldset>

      <fieldset class="group">
        <legend class="field-label">Como responder</legend>

        <label class="switch">
          <input v-model="form.use_agent" type="checkbox" />
          <span class="switch-track" aria-hidden="true" />
          <span>
            <strong>Agente</strong>
            <small>
              Ligado, o modelo decide como consultar o material: buscar mais de uma vez, listar os assuntos ou
              resumir. Desligado, faz uma busca e redige a resposta a partir dela.
            </small>
          </span>
        </label>

        <label class="switch">
          <input v-model="form.use_reranker" type="checkbox" />
          <span class="switch-track" aria-hidden="true" />
          <span>
            <strong>Re-ranqueamento</strong>
            <small>Uma segunda leitura confere se cada trecho responde mesmo à pergunta. É o que torna a recusa confiável.</small>
          </span>
        </label>
      </fieldset>

      <fieldset class="group sliders">
        <legend class="field-label">Parâmetros</legend>

        <label class="range">
          <span class="range-head"><span>Temperatura</span><output>{{ fmt(form.temperature) }}</output></span>
          <input v-model.number="form.temperature" type="range" min="0" max="1" step="0.05" />
          <small>Mais baixa: respostas mais previsíveis. Mais alta: mais variação na escrita.</small>
        </label>

        <label class="range">
          <span class="range-head"><span>Relevância mínima</span><output>{{ fmt(form.similarity_threshold) }}</output></span>
          <input v-model.number="form.similarity_threshold" type="range" min="0" max="1" step="0.05" />
          <small>
            Trechos com nota abaixo disso não são usados; se nenhum passar, o assistente avisa que o material não
            responde.
            <template v-if="!form.use_reranker">
              Sem o re-ranqueamento, a nota é a da busca vetorial, que quase sempre fica acima de 0,7.
            </template>
          </small>
        </label>

        <label class="range">
          <span class="range-head"><span>Trechos por resposta</span><output>{{ form.retrieval_k }}</output></span>
          <input v-model.number="form.retrieval_k" type="range" min="1" max="10" step="1" />
          <small>Quantos trechos do material, no máximo, sustentam cada resposta.</small>
        </label>
      </fieldset>

      <p v-if="error" class="form-error">{{ error }}</p>
      <button type="submit" hidden />
    </form>

    <template #actions>
      <template v-if="editing">
        <template v-if="confirmDelete">
          <span class="confirm-text">Excluir o chat e toda a conversa?</span>
          <button type="button" class="btn danger" :disabled="saving" @click="remove">Excluir</button>
          <button type="button" class="btn" @click="confirmDelete = false">Cancelar</button>
        </template>
        <button v-else type="button" class="btn danger delete" @click="confirmDelete = true">Excluir chat</button>
      </template>
      <template v-if="!confirmDelete">
        <button type="button" class="btn" @click="ui.closeModal()">Cancelar</button>
        <button type="button" class="btn primary" :disabled="saving" @click="save">
          {{ mode === "new" ? "Criar chat" : "Salvar" }}
        </button>
      </template>
    </template>
  </BaseModal>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.group {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin: 0;
  padding: 0;
  border: none;
}

.group legend {
  margin-bottom: var(--space-3);
  padding: 0;
}

.hint {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.link {
  padding: 0;
  border: none;
  background: none;
  color: var(--accent-strong);
  text-decoration: underline;
}

.check {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
}

.check:has(input:checked) {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.check input {
  accent-color: var(--accent);
}

.check-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.switch {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: start;
  gap: var(--space-3);
  cursor: pointer;
}

.switch input {
  position: absolute;
  opacity: 0;
}

.switch-track {
  position: relative;
  width: 40px;
  height: 22px;
  margin-top: 2px;
  border-radius: 999px;
  background: var(--surface-3);
  transition: background var(--transition);
}

.switch-track::after {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--text-muted);
  transition: transform var(--transition), background var(--transition);
}

.switch input:checked + .switch-track {
  background: var(--accent);
}

.switch input:checked + .switch-track::after {
  transform: translateX(18px);
  background: #1a140d;
}

.switch input:focus-visible + .switch-track {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.switch strong {
  display: block;
  font-weight: 600;
}

small {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-muted);
  line-height: 1.45;
}

.sliders {
  gap: var(--space-4);
}

.range {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.range-head {
  display: flex;
  justify-content: space-between;
}

.range output {
  font-variant-numeric: tabular-nums;
  color: var(--accent-strong);
}

.range input {
  accent-color: var(--accent);
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
