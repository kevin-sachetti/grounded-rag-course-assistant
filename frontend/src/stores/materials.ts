import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { api } from "../api/client";
import type { Material } from "../api/types";

const POLL_MS = 2500;

// Biblioteca de materiais. Enquanto algum está sendo processado, a lista se
// atualiza sozinha até todos ficarem prontos (ou com erro).
export const useMaterialsStore = defineStore("materials", () => {
  const materials = ref<Material[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const uploading = ref(0);
  let timer: ReturnType<typeof setTimeout> | null = null;

  const busy = computed(() =>
    materials.value.some((m) => m.status === "pending" || m.status === "processing"),
  );

  async function load() {
    loading.value = true;
    error.value = null;
    try {
      materials.value = await api.listMaterials();
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Não foi possível carregar os materiais";
    } finally {
      loading.value = false;
    }
    schedule();
  }

  function schedule() {
    if (timer) clearTimeout(timer);
    timer = busy.value ? setTimeout(load, POLL_MS) : null;
  }

  async function upload(files: File[]) {
    error.value = null;
    for (const file of files) {
      uploading.value++;
      try {
        materials.value.unshift(await api.uploadMaterial(file));
      } catch (e) {
        error.value = `${file.name}: ${e instanceof Error ? e.message : "falha no envio"}`;
      } finally {
        uploading.value--;
      }
    }
    schedule();
  }

  async function remove(id: string) {
    await api.deleteMaterial(id);
    materials.value = materials.value.filter((m) => m.id !== id);
  }

  return { materials, loading, error, uploading, busy, load, upload, remove };
});
