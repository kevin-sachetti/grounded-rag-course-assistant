<script setup lang="ts">
import { computed, ref } from "vue";

import type { Message } from "../api/types";
import { miniMarkdown } from "../utils/format";
import AnswerDetails from "./AnswerDetails.vue";
import AppIcon from "./AppIcon.vue";

const props = defineProps<{ message: Message }>();
const showDetails = ref(false);

// Materiais de onde vieram os trechos usados, para a linha "Baseado em".
const sources = computed(() => {
  const d = props.message.details;
  if (!d) return [];
  const count = new Map<string, Set<number>>();
  for (const s of d.searches)
    for (const c of s.candidates)
      if (c.kept) {
        const name = c.material_name ?? "material";
        if (!count.has(name)) count.set(name, new Set());
        count.get(name)!.add(c.chunk_index);
      }
  return [...count.entries()].map(([name, set]) => ({ name, n: set.size }));
});
</script>

<template>
  <article v-if="message.role === 'user'" class="msg user">
    <p>{{ message.content }}</p>
  </article>

  <article v-else class="msg assistant" :class="{ refused: message.refused }">
    <div v-if="message.refused" class="refusal-head">
      <AppIcon name="roots" />
      <span>O material deste chat não responde a essa pergunta</span>
    </div>

    <div class="prose" v-html="miniMarkdown(message.content)" />

    <footer v-if="message.details" class="msg-foot">
      <span v-if="sources.length" class="sources">
        Baseado em
        <span v-for="s in sources" :key="s.name" class="badge ok">{{ s.name }} · {{ s.n }} trecho{{ s.n > 1 ? "s" : "" }}</span>
      </span>
      <button type="button" class="understand" :aria-expanded="showDetails" @click="showDetails = !showDetails">
        <AppIcon name="roots" :size="16" />
        {{ showDetails ? "Esconder" : "Entender a resposta" }}
        <AppIcon name="chevron" :size="14" class="chev" :class="{ up: showDetails }" />
      </button>
    </footer>

    <AnswerDetails v-if="showDetails && message.details" :details="message.details" :refused="message.refused" />
  </article>
</template>

<style scoped>
.msg {
  max-width: 100%;
}

.user {
  align-self: flex-end;
  max-width: min(80%, 560px);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg);
  background: var(--surface-3);
}

.user p {
  margin: 0;
  white-space: pre-wrap;
}

.assistant {
  padding: var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: rgba(22, 21, 19, 0.85);
}

/* Recusa: borda tracejada e tom âmbar, para não parecer uma resposta comum */
.assistant.refused {
  border: 1px dashed var(--refusal);
  background: var(--refusal-soft);
}

.refusal-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
  color: var(--refusal);
  font-size: var(--text-sm);
  font-weight: 600;
}

.msg-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border);
}

.sources {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
  color: var(--text-faint);
}

.understand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  margin-left: auto;
  padding: var(--space-1) var(--space-3);
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  background: transparent;
  color: var(--accent-strong);
  font-size: var(--text-sm);
  transition: background var(--transition), border-color var(--transition);
}

.understand:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.chev {
  transition: transform var(--transition);
}

.chev.up {
  transform: rotate(180deg);
}
</style>
