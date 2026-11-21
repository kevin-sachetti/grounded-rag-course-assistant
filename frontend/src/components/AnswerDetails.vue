<script setup lang="ts">
import { computed, ref } from "vue";

import type { AnswerDetails, Candidate } from "../api/types";
import { miniMarkdown, score, seconds, toolLabel } from "../utils/format";

// Painel "entender a resposta": de onde ela veio, passo a passo.
const props = defineProps<{ details: AnswerDetails; refused: boolean }>();

const version = ref<"final" | "extractive">("final");
const open = ref<Set<string>>(new Set());

const key = (s: number, c: Candidate) => `${s}-${c.material_id}-${c.chunk_index}`;

function toggle(k: string) {
  const next = new Set(open.value);
  if (next.has(k)) next.delete(k);
  else next.add(k);
  open.value = next;
}

const usedCount = computed(
  () => new Set(props.details.searches.flatMap((s) => s.candidates.filter((c) => c.kept).map((c) => `${c.material_id}-${c.chunk_index}`))).size,
);

const p = computed(() => props.details.params);
const two = (n: number) => n.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const pct = (n: number | null) => `${Math.round((n ?? 0) * 100)}%`;
</script>

<template>
  <div class="details">
    <!-- Resumo do processamento -->
    <div class="summary">
      <span class="badge">{{ details.mode === "agent" ? "Agente" : "Fluxo fixo" }}</span>
      <span class="badge">{{ seconds(details.elapsed_seconds) }}</span>
      <span class="badge">temperatura {{ two(p.temperature) }}</span>
      <span class="badge">relevância mínima {{ two(p.similarity_threshold) }}</span>
      <span class="badge">até {{ p.retrieval_k }} trechos</span>
      <span class="badge">re-ranqueamento {{ p.use_reranker ? "ligado" : "desligado" }}</span>
      <span v-if="details.history_messages" class="badge">{{ details.history_messages }} mensagens anteriores</span>
    </div>

    <!-- Passos do agente -->
    <section v-if="details.steps.length" class="block">
      <h4>O que o agente fez</h4>
      <ol class="steps">
        <li v-for="(s, i) in details.steps" :key="i">
          <span>{{ toolLabel(s.tool) }}</span>
          <q v-if="s.input">{{ s.input }}</q>
        </li>
      </ol>
    </section>

    <!-- Buscas e trechos -->
    <section v-for="(search, si) in details.searches" :key="si" class="block">
      <h4>
        Busca<template v-if="details.searches.length > 1"> {{ si + 1 }}</template>:
        <q>{{ search.query }}</q>
      </h4>
      <p v-if="!search.candidates.length" class="muted">Nenhum trecho encontrado nos materiais do chat.</p>

      <ul class="candidates">
        <li
          v-for="c in search.candidates"
          :key="key(si, c)"
          class="candidate"
          :class="{ kept: c.kept }"
        >
          <button type="button" class="cand-head" :aria-expanded="open.has(key(si, c))" @click="toggle(key(si, c))">
            <span class="origin">
              <span class="material">{{ c.material_name ?? "material" }}</span>
              <span class="muted">trecho {{ c.chunk_index + 1 }}</span>
            </span>
            <span class="scores">
              <span class="score" title="Nota da busca vetorial (1º estágio)">
                <small>vetorial</small>{{ score(c.vector_score) }}
              </span>
              <span v-if="c.rerank_score !== null" class="score main" title="Nota do re-ranqueamento (2º estágio)">
                <small>re-ranq.</small>{{ score(c.rerank_score) }}
                <span class="bar"><span :style="{ width: pct(c.rerank_score) }" /></span>
              </span>
              <span class="badge" :class="c.kept ? 'ok' : ''">{{ c.kept ? "usado" : "descartado" }}</span>
            </span>
          </button>
          <p v-if="open.has(key(si, c))" class="chunk-text">{{ c.text }}</p>
        </li>
      </ul>
    </section>

    <!-- Versões da resposta -->
    <section v-if="!refused" class="block">
      <h4>Versões da resposta</h4>
      <div class="tabs" role="tablist">
        <button type="button" role="tab" :aria-selected="version === 'final'" @click="version = 'final'">
          Resposta final
        </button>
        <button type="button" role="tab" :aria-selected="version === 'extractive'" @click="version = 'extractive'">
          Trechos usados ({{ usedCount }})
        </button>
      </div>
      <div v-if="version === 'final'" class="version prose" v-html="miniMarkdown(details.versions.final)" />
      <p v-else class="version chunk-text">{{ details.versions.extractive || "Nenhum trecho foi usado." }}</p>
    </section>
  </div>
</template>

<style scoped>
.details {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-top: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: rgba(14, 13, 12, 0.6);
}

.summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
}

.block h4 {
  margin: 0 0 var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-muted);
}

q {
  color: var(--text);
  font-weight: 400;
}

.muted {
  color: var(--text-faint);
  font-size: var(--text-sm);
}

.steps {
  margin: 0;
  padding-left: var(--space-6);
  font-size: var(--text-sm);
}

.steps li + li {
  margin-top: var(--space-1);
}

.steps q {
  margin-left: var(--space-2);
}

/* Cada trecho é uma "raiz": os usados ficam com o traço verde aceso */
.candidates {
  list-style: none;
  margin: 0;
  padding: 0 0 0 var(--space-3);
  border-left: 2px solid var(--border);
}

.candidate {
  position: relative;
  margin-bottom: var(--space-1);
}

.candidate::before {
  content: "";
  position: absolute;
  left: calc(-1 * var(--space-3) - 2px);
  top: 18px;
  width: var(--space-3);
  border-top: 2px solid var(--border);
}

.candidate.kept::before {
  border-color: var(--leaf);
}

.cand-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  text-align: left;
  opacity: 0.75;
}

.candidate.kept .cand-head {
  border-color: rgba(143, 174, 134, 0.45);
  opacity: 1;
}

.cand-head:hover {
  opacity: 1;
}

.origin {
  display: flex;
  gap: var(--space-2);
  align-items: baseline;
  min-width: 0;
}

.material {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.scores {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-variant-numeric: tabular-nums;
  font-size: var(--text-sm);
}

.score small {
  margin-right: var(--space-1);
  color: var(--text-faint);
}

.score.main {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--text);
}

.bar {
  display: inline-block;
  width: 48px;
  height: 4px;
  margin-left: var(--space-1);
  border-radius: 2px;
  background: var(--surface-3);
  overflow: hidden;
}

.bar span {
  display: block;
  height: 100%;
  background: var(--leaf);
}

.chunk-text {
  margin: var(--space-2) 0 0;
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  background: var(--surface);
  font-size: var(--text-sm);
  color: var(--text-muted);
  white-space: pre-wrap;
  line-height: 1.6;
}

.tabs {
  display: inline-flex;
  gap: 2px;
  padding: 2px;
  border-radius: var(--radius);
  background: var(--surface-2);
}

.tabs button {
  padding: var(--space-1) var(--space-3);
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.tabs button[aria-selected="true"] {
  background: var(--surface-3);
  color: var(--text);
}

.version {
  margin-top: var(--space-3);
}
</style>
