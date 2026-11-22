<script setup lang="ts">
import { useSessionStore } from "../stores/session";
import BaseModal from "./BaseModal.vue";

const session = useSessionStore();
</script>

<template>
  <BaseModal title="Antes de começar" locked>
    <p class="text">
      Se você ficar <strong>{{ session.me?.inactivity_days ?? 30 }} dias sem entrar</strong>, seus chats e
      materiais são apagados automaticamente. A sua conta continua existindo, e você pode voltar a usá-la quando
      quiser.
    </p>
    <template #actions>
      <button type="button" class="btn primary" @click="session.ackRetention()">Entendi</button>
    </template>
  </BaseModal>
</template>

<style scoped>
.text {
  margin: 0;
  line-height: 1.55;
}
</style>
