<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api/client";
import type { Course } from "../types";

const router = useRouter();
const courses = ref<Course[]>([]);
const name = ref("");
const description = ref("");
const loading = ref(false);

async function load() {
  courses.value = await api.listCourses();
}

async function create() {
  if (!name.value.trim()) return;
  loading.value = true;
  try {
    const course = await api.createCourse(name.value, description.value);
    name.value = "";
    description.value = "";
    router.push(`/courses/${course.id}`);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <h1>Cursos</h1>

  <form class="row" @submit.prevent="create">
    <input v-model="name" placeholder="Nome do curso" />
    <input v-model="description" placeholder="Descrição (opcional)" />
    <button :disabled="loading">Criar</button>
  </form>

  <ul class="list">
    <li v-for="c in courses" :key="c.id">
      <RouterLink :to="`/courses/${c.id}`">{{ c.name }}</RouterLink>
    </li>
    <li v-if="courses.length === 0" class="empty">Nenhum curso ainda.</li>
  </ul>
</template>

<style scoped>
.row {
  display: flex;
  gap: 8px;
  margin: 16px 0;
}
.row input {
  flex: 1;
}
.list {
  list-style: none;
  padding: 0;
}
.list li {
  padding: 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  margin-bottom: 8px;
}
.empty {
  color: #6b7280;
}
</style>
