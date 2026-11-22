<script setup lang="ts">
import { computed } from "vue";

import leaves from "../assets/fallen-leaves.svg";
import leavesColor from "../assets/fallen-leaves-color.svg";
import { author } from "../author";

const phoneHref = computed(() => `tel:${author.phone.replace(/[^\d+]/g, "")}`);
</script>

<template>
  <footer class="app-footer">
    <div class="author">
      <span class="name">{{ author.name }}</span>

      <nav class="links" aria-label="Contato">
        <a v-if="author.linkedin" :href="`https://www.linkedin.com/in/${author.linkedin}/`" target="_blank" rel="noopener">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <rect x="3" y="3" width="18" height="18" rx="4" />
            <path d="M8 10.5V16M8 7.6v.1M11.5 16v-3.2a2.3 2.3 0 0 1 4.5 0V16M11.5 10.5V16" />
          </svg>
          LinkedIn
        </a>
        <a v-if="author.github" :href="`https://github.com/${author.github}`" target="_blank" rel="noopener">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="6" cy="5.5" r="2" />
            <circle cx="6" cy="18.5" r="2" />
            <circle cx="18" cy="8" r="2" />
            <path d="M6 7.5v9M18 10c0 4-6 3-11.2 7" />
          </svg>
          GitHub
        </a>
        <a v-if="author.email" :href="`mailto:${author.email}`">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <rect x="3" y="5.5" width="18" height="13" rx="2.5" />
            <path d="m4 7.5 8 5.5 8-5.5" />
          </svg>
          {{ author.email }}
        </a>
        <a v-if="author.phone" :href="phoneHref">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6.6 3.5h2.6l1.4 4-2 1.4a11 11 0 0 0 6.5 6.5l1.4-2 4 1.4v2.6a2 2 0 0 1-2.1 2A16 16 0 0 1 4.6 5.6a2 2 0 0 1 2-2.1Z" />
          </svg>
          {{ author.phone }}
        </a>
      </nav>
    </div>

    <!-- Folhas caídas da árvore de fundo, no mesmo tom apagado. -->
    <img class="leaves" :src="leaves" alt="" aria-hidden="true" />
    <!-- 2 folhas secas e 3 verdes, mais visíveis, por cima das apagadas -->
    <img class="leaves color" :src="leavesColor" alt="" aria-hidden="true" />
  </footer>
</template>

<style scoped>
.app-footer {
  position: relative;
  overflow: hidden; /* as folhas ficam dentro do rodapé */
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--border);
  background: var(--surface);
}

.author {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3) var(--space-6);
  padding-right: 200px; /* espaço para o montinho de folhas */
}

.name {
  font-weight: 600;
  letter-spacing: 0.01em;
}

/* Contatos lado a lado */
.links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.links a {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--text-muted);
  font-size: var(--text-sm);
  text-decoration: none;
  transition: color var(--transition), border-color var(--transition), background var(--transition);
}

.links a:hover {
  color: var(--text);
  border-color: var(--accent);
  background: var(--accent-soft);
}

.links svg {
  width: 16px;
  height: 16px;
  flex: none;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.leaves {
  position: absolute;
  right: 0;
  bottom: 0;
  height: 100%;
  max-width: 60%;
  object-fit: contain;
  object-position: right bottom;
  opacity: var(--tree-bg-opacity);
  pointer-events: none;
  user-select: none;
}

.leaves.color {
  opacity: var(--fallen-leaves-color-opacity);
}

@media (max-width: 640px) {
  .app-footer {
    padding: var(--space-4);
  }

  .author {
    flex-direction: column;
    align-items: flex-start;
    padding-right: 0;
  }

  .links {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
