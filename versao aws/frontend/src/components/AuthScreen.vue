<script setup lang="ts">
import { computed, ref } from "vue";

import icon from "../assets/grounded-icon.svg";
import { authMessage, confirmCode, forgotPassword, login, newPassword, register, resendCode } from "../auth";
import { useSessionStore } from "../stores/session";

type Mode = "login" | "register" | "confirm" | "forgot" | "reset";

const session = useSessionStore();
const mode = ref<Mode>("login");
const email = ref("");
const password = ref("");
const code = ref("");
const busy = ref(false);
const error = ref<string | null>(null);
const info = ref<string | null>(null);

const titles: Record<Mode, string> = {
  login: "Entrar",
  register: "Criar conta",
  confirm: "Confirmar e-mail",
  forgot: "Esqueci a senha",
  reset: "Nova senha",
};
const title = computed(() => titles[mode.value]);

function go(m: Mode) {
  mode.value = m;
  error.value = null;
  info.value = null;
  code.value = "";
}

async function run(fn: () => Promise<void>) {
  busy.value = true;
  error.value = null;
  try {
    await fn();
  } catch (e) {
    error.value = authMessage(e);
  } finally {
    busy.value = false;
  }
}

const submit = () =>
  run(async () => {
    const e = email.value.trim();
    if (mode.value === "login") {
      if ((await login(e, password.value)) === "confirm") {
        await resendCode(e);
        go("confirm");
        info.value = "Sua conta ainda não foi confirmada. Enviamos um novo código para o seu e-mail.";
        return;
      }
      await session.enter();
    } else if (mode.value === "register") {
      await register(e, password.value);
      go("confirm");
      info.value = "Enviamos um código para o seu e-mail. Digite-o abaixo para ativar a conta.";
    } else if (mode.value === "confirm") {
      await confirmCode(e, code.value.trim());
      await login(e, password.value);
      await session.enter();
    } else if (mode.value === "forgot") {
      await forgotPassword(e);
      go("reset");
      info.value = "Enviamos um código para o seu e-mail. Digite-o com a nova senha.";
    } else {
      await newPassword(e, code.value.trim(), password.value);
      go("login");
      info.value = "Senha alterada. Entre com a nova senha.";
    }
  });

const resend = () =>
  run(async () => {
    await resendCode(email.value.trim());
    info.value = "Enviamos um novo código.";
  });
</script>

<template>
  <main class="auth">
    <section class="card">
      <img class="logo" :src="icon" alt="" aria-hidden="true" />
      <h1 class="app-name">Grounded RAG Assistant</h1>
      <p class="tagline">Respostas só com base no material que você envia.</p>

      <h2 class="title">{{ title }}</h2>
      <p v-if="info" class="info">{{ info }}</p>

      <form class="form" @submit.prevent="submit">
        <label class="field">
          <span class="field-label">E-mail</span>
          <input v-model="email" class="input" type="email" autocomplete="email" required :disabled="busy" />
        </label>

        <label v-if="mode === 'confirm' || mode === 'reset'" class="field">
          <span class="field-label">Código recebido por e-mail</span>
          <input v-model="code" class="input" inputmode="numeric" autocomplete="one-time-code" required :disabled="busy" />
        </label>

        <label v-if="mode !== 'forgot'" class="field">
          <span class="field-label">{{ mode === "reset" ? "Nova senha" : "Senha" }}</span>
          <input
            v-model="password"
            class="input"
            type="password"
            :autocomplete="mode === 'login' || mode === 'confirm' ? 'current-password' : 'new-password'"
            required
            :disabled="busy"
          />
          <small v-if="mode === 'register' || mode === 'reset'" class="hint">
            Pelo menos 8 caracteres, com letra maiúscula, minúscula, número e símbolo.
          </small>
        </label>

        <p v-if="error" class="form-error" role="alert">{{ error }}</p>

        <button type="submit" class="btn primary" :disabled="busy">
          {{ busy ? "Aguarde…" : title }}
        </button>
      </form>

      <nav class="links">
        <template v-if="mode === 'login'">
          <button type="button" class="link" @click="go('register')">Criar conta</button>
          <button type="button" class="link" @click="go('forgot')">Esqueci a senha</button>
        </template>
        <template v-else-if="mode === 'confirm'">
          <button type="button" class="link" :disabled="busy" @click="resend">Reenviar código</button>
          <button type="button" class="link" @click="go('login')">Voltar para entrar</button>
        </template>
        <button v-else type="button" class="link" @click="go('login')">Voltar para entrar</button>
      </nav>
    </section>
  </main>
</template>

<style scoped>
.auth {
  display: grid;
  place-items: center;
  min-height: 100%;
  padding: var(--space-6) var(--space-4);
  background: var(--bg);
}

.card {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 400px;
  padding: var(--space-6);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
}

.logo {
  width: 120px;
  border-radius: 22px;
}

.app-name {
  margin: var(--space-3) 0 0;
  font-size: 1.15rem;
  font-weight: 600;
}

.tagline {
  margin: var(--space-1) 0 var(--space-6);
  font-size: var(--text-sm);
  color: var(--text-muted);
  text-align: center;
}

.title {
  align-self: flex-start;
  margin: 0 0 var(--space-3);
  font-size: 1rem;
  font-weight: 600;
}

.info {
  align-self: stretch;
  margin: 0 0 var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius);
  background: var(--accent-soft);
  font-size: var(--text-sm);
  color: var(--accent-strong);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  width: 100%;
}

.hint {
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.links {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  width: 100%;
  margin-top: var(--space-4);
}

.link {
  padding: 0;
  border: none;
  background: none;
  font-size: var(--text-sm);
  color: var(--accent-strong);
  text-decoration: underline;
  cursor: pointer;
}
</style>
