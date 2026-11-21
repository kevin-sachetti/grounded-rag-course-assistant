import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { api } from "../api/client";
import type { Material } from "../api/types";

const POLL_MS = 2000;

// Mesmas regras da API (backend/app/features/materials): conferidas aqui
// antes do envio para o usuário não esperar o upload de um arquivo recusado.
export const SUPPORTED_EXT = [
  "txt", "md", "pdf",
  "mp3", "wav", "m4a", "ogg", "flac", "aac",
  "mp4", "mov", "mkv", "avi", "webm",
];
export const MAX_UPLOAD_MB = 1024;

const extension = (name: string) => (name.includes(".") ? name.split(".").pop()!.toLowerCase() : "");

// Biblioteca de materiais. Enquanto algum está sendo processado, a lista se
// atualiza sozinha até todos ficarem prontos (ou com erro).
export const useMaterialsStore = defineStore("materials", () => {
  const materials = ref<Material[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  // Um aviso por arquivo recusado no último envio.
  const rejected = ref<string[]>([]);
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

  /** Motivo para recusar o arquivo antes do envio, ou null se ele pode ir. */
  function check(file: File, names: Set<string>): string | null {
    if (!SUPPORTED_EXT.includes(extension(file.name))) return "formato não suportado";
    if (file.size === 0) return "o arquivo está vazio";
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `passa do limite de ${MAX_UPLOAD_MB} MB`;
    if (names.has(file.name.toLowerCase())) return "já existe um material com esse nome";
    return null;
  }

  async function upload(files: File[]) {
    error.value = null;
    rejected.value = [];
    // Nomes da biblioteca e do próprio lote: dois arquivos iguais no mesmo envio também contam.
    const names = new Set(materials.value.map((m) => m.filename.toLowerCase()));
    for (const file of files) {
      const reason = check(file, names);
      if (reason) {
        rejected.value.push(`${file.name}: ${reason}.`);
        continue;
      }
      names.add(file.name.toLowerCase());
      uploading.value++;
      try {
        materials.value.unshift(await api.uploadMaterial(file));
      } catch (e) {
        rejected.value.push(`${file.name}: ${e instanceof Error ? e.message : "falha no envio"}`);
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

  return { materials, loading, error, rejected, uploading, busy, load, upload, remove };
});
