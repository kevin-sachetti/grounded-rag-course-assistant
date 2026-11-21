<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

// Enquanto a resposta não chega, uma raiz cresce: o assistente está buscando no material.
const elapsed = ref(0);
let timer: ReturnType<typeof setInterval>;
onMounted(() => (timer = setInterval(() => elapsed.value++, 1000)));
onBeforeUnmount(() => clearInterval(timer));
</script>

<template>
  <div class="loader" role="status">
    <svg viewBox="0 0 64 40" aria-hidden="true">
      <path class="ground" d="M2 8H62" />
      <path class="root r1" d="M32 8C31 16 24 20 16 30" />
      <path class="root r2" d="M32 8V36" />
      <path class="root r3" d="M32 8C33 16 40 20 48 30" />
      <path class="root r4" d="M24 21C20 22 15 21 10 24" />
      <path class="root r5" d="M40 21C44 22 49 21 54 24" />
    </svg>
    <span>Buscando no material… {{ elapsed }} s</span>
  </div>
</template>

<style scoped>
.loader {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--text-muted);
  font-size: var(--text-sm);
}

svg {
  width: 56px;
  height: 35px;
  fill: none;
  stroke-linecap: round;
}

.ground {
  stroke: var(--border-strong);
  stroke-width: 1.5;
}

.root {
  stroke: var(--accent);
  stroke-width: 2;
  stroke-dasharray: 40;
  stroke-dashoffset: 40;
  animation: grow 2.4s ease-in-out infinite;
}

.r2 {
  animation-delay: 0.15s;
}

.r3 {
  animation-delay: 0.3s;
}

.r4,
.r5 {
  stroke-width: 1.4;
  stroke: var(--leaf);
  animation-delay: 0.6s;
}

@keyframes grow {
  0% {
    stroke-dashoffset: 40;
    opacity: 1;
  }
  60% {
    stroke-dashoffset: 0;
    opacity: 1;
  }
  100% {
    stroke-dashoffset: 0;
    opacity: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .root {
    animation: none;
    stroke-dashoffset: 0;
  }
}
</style>
