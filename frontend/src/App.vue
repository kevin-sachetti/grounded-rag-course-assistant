<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <header class="topbar">
    <RouterLink to="/" class="brand">Chatbot Educacional</RouterLink>
  </header>
  <main class="container">
    <RouterView />
  </main>
</template>

<style>
* {
  box-sizing: border-box;
}
body {
  margin: 0;
  font-family: system-ui, sans-serif;
  color: #1a1a1a;
  background: #f6f7f9;
}
.topbar {
  background: #1f2937;
  padding: 12px 20px;
}
.brand {
  color: #fff;
  font-weight: 600;
  text-decoration: none;
}
.container {
  max-width: 760px;
  margin: 24px auto;
  padding: 0 16px;
}
input,
button {
  font: inherit;
  padding: 8px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}
button {
  background: #2563eb;
  color: #fff;
  border: none;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
