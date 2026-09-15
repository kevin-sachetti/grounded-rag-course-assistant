# API

- **Base:** `http://localhost:8000`
- **Autenticação:** nenhuma
- **Documentação interativa (Swagger):** `http://localhost:8000/docs`
- **Formato:** JSON, exceto o envio de material, que é `multipart/form-data`

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Estado da API, do banco e do pgvector |
| `GET` | `/courses` | Lista cursos |
| `POST` | `/courses` | Cria curso |
| `GET` | `/courses/{course_id}` | Busca curso |
| `PATCH` | `/courses/{course_id}` | Atualiza curso |
| `DELETE` | `/courses/{course_id}` | Exclui curso |
| `POST` | `/courses/{course_id}/materials` | Envia material |
| `GET` | `/courses/{course_id}/materials` | Lista materiais do curso |
| `GET` | `/materials/{material_id}` | Busca material |
| `DELETE` | `/materials/{material_id}` | Exclui material |
| `POST` | `/courses/{course_id}/chat` | Faz uma pergunta |

---

## Saúde

### `GET /health`

Confirma que a API responde, que conecta no banco e que a extensão `vector` está ativa.

```json
{ "status": "ok", "database": "connected", "pgvector": true }
```

---

## Cursos

### `POST /courses` — criar

**Corpo:**

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `name` | string | sim | 1 a 200 caracteres |
| `description` | string | não | — |

```json
{ "name": "Biologia - Fotossíntese", "description": "Curso introdutório" }
```

**Resposta `201`:**

```json
{
  "id": "5f4bd615-71e8-49cd-b509-7cffa52d0bbc",
  "name": "Biologia - Fotossíntese",
  "description": "Curso introdutório",
  "created_at": "2026-08-20T01:55:03.422516Z",
  "updated_at": "2026-08-20T01:55:03.422516Z"
}
```

`422` se `name` estiver vazio ou passar de 200 caracteres.

### `GET /courses` — listar

Devolve um array de cursos, do mais recente para o mais antigo.

### `GET /courses/{course_id}` — buscar

Devolve o curso. `404` se não existir.

### `PATCH /courses/{course_id}` — atualizar

Atualização parcial: só os campos enviados são alterados.

```json
{ "name": "Biologia I" }
```

Devolve o curso atualizado. `404` se não existir.

### `DELETE /courses/{course_id}` — excluir

Exclui também todos os materiais do curso: os vetores no índice, os arquivos no disco e os registros no banco. `204` sem corpo. `404` se não existir.

---

## Materiais

### `POST /courses/{course_id}/materials` — enviar

`multipart/form-data` com o arquivo no campo **`file`**.

```bash
curl -X POST http://localhost:8000/courses/<course_id>/materials -F "file=@contents/fotossintese.txt"
```

O tipo é detectado pela extensão, ou pelo `content-type` se a extensão não for reconhecida:

| Tipo | Extensões | Como o texto é extraído |
|---|---|---|
| `audio` | mp3, wav, m4a, ogg, flac, aac | Transcrição com Whisper |
| `video` | mp4, mov, mkv, avi, webm | Transcrição com Whisper |
| `pdf` | pdf | Texto das páginas |
| `text` | txt, md | Leitura direta (UTF-8) |
| `other` | qualquer outra | Não suportado — o processamento termina em `error` |

**Resposta `201`** — o material é registrado na hora com `status: "pending"`, e o processamento acontece em segundo plano:

```json
{
  "id": "d4ffed32-4900-4d1c-9dc3-bc68d1778f00",
  "course_id": "5f4bd615-71e8-49cd-b509-7cffa52d0bbc",
  "filename": "fotossintese.txt",
  "content_type": "text/plain",
  "media_type": "text",
  "status": "pending",
  "created_at": "2026-08-20T01:55:03.635555Z",
  "updated_at": "2026-08-20T01:55:03.635555Z"
}
```

`404` se o curso não existir.

**Status do processamento:**

| Status | Significado |
|---|---|
| `pending` | Recebido, aguardando processamento |
| `processing` | Extraindo texto, dividindo em trechos e gerando vetores |
| `done` | Pronto para ser consultado no chat |
| `error` | Falhou — detalhes no log da API |

### `GET /courses/{course_id}/materials` — listar

Array de materiais do curso, do mais recente para o mais antigo.

### `GET /materials/{material_id}` — buscar

Devolve o material. É a rota usada para acompanhar o `status` depois do envio. `404` se não existir.

### `DELETE /materials/{material_id}` — excluir

Remove os vetores do material do índice, o arquivo do disco e o registro do banco. `204` sem corpo. `404` se não existir.

---

## Chat

### `POST /courses/{course_id}/chat` — perguntar

**Corpo:**

```json
{ "question": "Como funciona o ciclo de Calvin?" }
```

**Resposta `200`:**

```json
{
  "answer": "…",
  "sources": [
    { "material_id": "d4ffed32-…", "chunk_index": 8, "score": 0.9932 },
    { "material_id": "d4ffed32-…", "chunk_index": 9, "score": 0.976 }
  ]
}
```

| Campo | Significado |
|---|---|
| `answer` | A resposta |
| `sources[].material_id` | Material de onde o trecho veio |
| `sources[].chunk_index` | Posição do trecho dentro do material |
| `sources[].score` | Relevância do trecho para a pergunta, de 0 a 1 (maior = mais relevante) |

`404` se o curso não existir.

**O conteúdo da resposta depende do modo configurado:**

| Modo | `answer` | `sources` |
|---|---|---|
| Pipeline extrativo *(padrão)* | Os trechos recuperados, separados por `---`. Sem trechos: `"Não encontrei nada no material do curso."` | Os trechos retornados, **sem corte por relevância** |
| Pipeline reformulado | Texto gerado pelo LLM a partir dos trechos | Os trechos usados, sem corte por relevância |
| Agente | Resposta final do agente | Só os trechos buscados pelo agente com relevância ≥ `SIMILARITY_THRESHOLD`, sem repetição |

Com o re-ranqueamento ligado, `score` é a nota do cross-encoder; desligado, é a similaridade da busca vetorial, que tem outra escala — ver [experimentos](experimentos.md).

**Tempo de resposta:** cerca de 6,5 segundos no modo padrão, com 8 GB de RAM no Docker. A primeira pergunta depois de subir a API é mais lenta porque carrega os modelos na memória.

---

## Observação: acentos no terminal do Windows

No Git Bash, enviar JSON com acentos direto no `-d` pode corromper os caracteres e a API responde `There was an error parsing the body`. Nesse caso, salve o corpo num arquivo UTF-8 e envie com `--data-binary`:

```bash
curl -X POST http://localhost:8000/courses/<course_id>/chat -H "Content-Type: application/json" --data-binary @pergunta.json
```
