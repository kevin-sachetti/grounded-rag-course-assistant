<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../api/client";
import type { Course, Material } from "../types";

const props = defineProps<{ id: string }>();

const course = ref<Course | null>(null);
const materials = ref<Material[]>([]);
const uploading = ref(false);

async function load() {
  course.value = await api.getCourse(props.id);
  materials.value = await api.listMaterials(props.id);
}

async function onFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  uploading.value = true;
  try {
    await api.uploadMaterial(props.id, file);
    await load();
  } finally {
    uploading.value = false;
    input.value = "";
  }
}

onMounted(load);
</script>

<template>
  <div v-if="course">
    <h1>{{ course.name }}</h1>
    <p v-if="course.description" class="desc">{{ course.description }}</p>
    <RouterLink :to="`/courses/${course.id}/chat`" class="chat-link">
      Ir para o chat →
    </RouterLink>

    <div class="materials">
      <div class="materials-head">
        <h2>Materiais</h2>
        <button @click="load" :disabled="uploading">Atualizar status</button>
      </div>

      <label class="upload">
        <input type="file" @change="onFile" :disabled="uploading" />
      </label>

      <ul class="list">
        <li v-for="m in materials" :key="m.id">
          <span>{{ m.filename }}</span>
          <span class="badge" :data-status="m.status">{{ m.status }}</span>
          <span class="type">{{ m.media_type }}</span>
        </li>
        <li v-if="materials.length === 0" class="empty">
          Nenhum material enviado ainda.
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.desc {
  color: #4b5563;
}
.chat-link {
  display: inline-block;
  margin: 8px 0 20px;
  font-weight: 600;
}
.materials-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.upload {
  display: block;
  margin: 8px 0 16px;
}
.list {
  list-style: none;
  padding: 0;
}
.list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  margin-bottom: 8px;
}
.badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #e5e7eb;
}
.badge[data-status="done"] {
  background: #dcfce7;
  color: #166534;
}
.badge[data-status="error"] {
  background: #fee2e2;
  color: #991b1b;
}
.badge[data-status="processing"] {
  background: #fef9c3;
  color: #854d0e;
}
.type {
  color: #6b7280;
  font-size: 12px;
  margin-left: auto;
}
.empty {
  color: #6b7280;
}
</style>
