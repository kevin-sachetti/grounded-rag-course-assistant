# API

- **Base:** `http://localhost:8000` (pela interface, as mesmas rotas ficam em `http://localhost:8080/api`)
- **Autenticação:** nenhuma
- **Documentação interativa (Swagger):** `http://localhost:8000/docs`
- **Formato:** JSON, exceto o envio de material, que é `multipart/form-data`

## Rotas

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Estado da API, do banco e do pgvector |
| `POST` | `/materials` | Envia um material para a biblioteca |
| `GET` | `/materials` | Lista a biblioteca |
| `GET` | `/materials/{material_id}` | Busca um material |
| `DELETE` | `/materials/{material_id}` | Exclui um material |
| `GET` | `/chats` | Lista os chats |
| `POST` | `/chats` | Cria um chat |
| `GET` | `/chats/{chat_id}` | Busca um chat |
| `PATCH` | `/chats/{chat_id}` | Altera um chat |
| `DELETE` | `/chats/{chat_id}` | Exclui um chat |
| `GET` | `/chats/{chat_id}/messages` | Lista a conversa de um chat |
| `POST` | `/chats/{chat_id}/messages` | Faz uma pergunta |

---

## Saúde

### `GET /health`

Confirma que a API responde, que conecta no banco e que a extensão `vector` está ativa.

```json
{ "status": "ok", "database": "connected", "pgvector": true }
```

---

## Materiais

Os materiais ficam numa biblioteca única. Cada chat escolhe quais deles usa.

### `POST /materials` — enviar

`multipart/form-data` com o arquivo no campo **`file`**.

```bash
curl -X POST http://localhost:8000/materials -F "file=@contents/fotossintese.txt"
```

O tipo é detectado pela extensão do arquivo:

| Tipo | Extensões | Como o texto é extraído |
|---|---|---|
| `audio` | mp3, wav, m4a, ogg, flac, aac | Transcrição com o Whisper |
| `video` | mp4, mov, mkv, avi, webm | Transcrição com o Whisper |
| `pdf` | pdf | Texto das páginas, com o pypdf |
| `text` | txt, md | Leitura direta (UTF-8) |

**Resposta `201`.** O material é registrado na hora com `status: "pending"`, e o processamento acontece em segundo plano:

```json
{
  "id": "d4ffed32-4900-4d1c-9dc3-bc68d1778f00",
  "filename": "fotossintese.txt",
  "content_type": "text/plain",
  "media_type": "text",
  "status": "pending",
  "chunk_count": 0,
  "stage": null,
  "progress": null,
  "created_at": "2026-11-20T01:55:03.635555Z",
  "updated_at": "2026-11-20T01:55:03.635555Z"
}
```

| Status | Significado |
|---|---|
| `pending` | Recebido, aguardando processamento |
| `processing` | Extraindo o texto, dividindo em trechos e gerando os vetores |
| `done` | Pronto para ser usado nos chats; `chunk_count` diz quantos trechos gerou |
| `error` | Falhou (por exemplo, um PDF escaneado, sem texto); os detalhes ficam no log da API |

Enquanto o material está em `processing`, `stage` diz a etapa atual (por exemplo, `"transcrevendo o áudio"` ou `"gerando os vetores"`) e `progress` o percentual do processamento inteiro, de 0 a 100. Nos demais status, os dois vêm `null`. O progresso fica na memória da API: se ela reiniciar no meio, o material continua em `processing` sem percentual.

**Envio recusado** — nada é gravado:

| Código | Quando |
|---|---|
| `409` | Já existe um material com o mesmo nome, sem diferenciar maiúsculas de minúsculas |
| `413` | O arquivo passa de `MAX_UPLOAD_MB` (1.024 MB) |
| `415` | Formato não suportado |
| `422` | Arquivo vazio ou sem nome |

O nome guardado é só o nome do arquivo, sem pastas: `../../aula.txt` vira `aula.txt`.

### `GET /materials` — listar

Lista os materiais da biblioteca, do mais recente para o mais antigo.

### `GET /materials/{material_id}` — buscar

Devolve o material. Serve para acompanhar o `status` depois do envio. `404` se não existir.

### `DELETE /materials/{material_id}` — excluir

Remove os vetores do material, o arquivo do disco, a ligação com os chats que o usavam e o registro do banco. `204` sem corpo. `404` se não existir.

---

## Chats

Um chat tem nome, materiais e parâmetros próprios. Só responde com os materiais dele.

### `POST /chats` — criar

| Campo | Tipo | Obrigatório | Regra | Padrão |
|---|---|---|---|---|
| `name` | string | sim | 1 a 200 caracteres | — |
| `material_ids` | lista de UUID | não | Materiais da biblioteca | `[]` |
| `temperature` | número | não | 0 a 2 | 0,6 |
| `similarity_threshold` | número | não | 0 a 1 | 0,6 |
| `retrieval_k` | inteiro | não | 1 a 10 | 3 |
| `use_reranker` | booleano | não | — | `true` |
| `use_agent` | booleano | não | — | `true` |

```json
{ "name": "Fotossíntese", "material_ids": ["d4ffed32-4900-4d1c-9dc3-bc68d1778f00"] }
```

**Resposta `201`:**

```json
{
  "id": "5f4bd615-71e8-49cd-b509-7cffa52d0bbc",
  "name": "Fotossíntese",
  "temperature": 0.6,
  "similarity_threshold": 0.6,
  "retrieval_k": 3,
  "use_reranker": true,
  "use_agent": true,
  "materials": [
    { "id": "d4ffed32-…", "filename": "fotossintese.txt", "media_type": "text", "status": "done" }
  ],
  "created_at": "2026-11-20T02:10:11.120000Z",
  "updated_at": "2026-11-20T02:10:11.120000Z"
}
```

`422` se algum material não existir.

### `GET /chats` — listar

Lista os chats, do usado ou alterado mais recentemente para o mais antigo.

### `GET /chats/{chat_id}` — buscar

Devolve o chat. `404` se não existir.

### `PATCH /chats/{chat_id}` — alterar

Aceita os mesmos campos da criação, todos opcionais. Só o que vier é alterado; `material_ids`, se vier, substitui a lista inteira. `404` se o chat não existir e `422` se algum material não existir.

### `DELETE /chats/{chat_id}` — excluir

Exclui o chat e a conversa dele. Os materiais continuam na biblioteca. `204` sem corpo. `404` se não existir.

---

## Mensagens

### `GET /chats/{chat_id}/messages` — conversa

Lista as mensagens do chat, em ordem. `404` se o chat não existir.

### `POST /chats/{chat_id}/messages` — perguntar

**Corpo:**

```json
{ "content": "Como funciona o ciclo de Calvin?" }
```

`content` tem de 1 a 4.000 caracteres. A resposta usa os materiais e os parâmetros do chat e, no modo agente, as últimas 6 mensagens da conversa.

**Resposta `200`** — a pergunta e a resposta, já gravadas:

```json
{
  "question": { "id": "…", "chat_id": "…", "role": "user", "content": "Como funciona o ciclo de Calvin?", "refused": false, "details": null, "created_at": "…" },
  "answer": {
    "id": "…",
    "chat_id": "…",
    "role": "assistant",
    "content": "O ciclo de Calvin é …",
    "refused": false,
    "details": {
      "mode": "agent",
      "params": { "temperature": 0.6, "similarity_threshold": 0.6, "retrieval_k": 3, "use_reranker": true },
      "steps": [ { "tool": "buscar_no_material", "input": "ciclo de Calvin" } ],
      "searches": [
        {
          "query": "ciclo de Calvin",
          "candidates": [
            {
              "material_id": "d4ffed32-…",
              "material_name": "fotossintese.txt",
              "chunk_index": 8,
              "text": "…",
              "vector_score": 0.87,
              "rerank_score": 0.9932,
              "kept": true
            }
          ]
        }
      ],
      "versions": { "final": "O ciclo de Calvin é …", "extractive": "…" },
      "history_messages": 0,
      "elapsed_seconds": 9.4
    },
    "created_at": "…"
  }
}
```

| Campo | Significado |
|---|---|
| `answer.content` | A resposta |
| `answer.refused` | `true` quando nenhum trecho atingiu a relevância mínima e o sistema recusou responder |
| `details.mode` | `agent` ou `fixed` |
| `details.steps` | Ferramentas que o agente chamou, em ordem (vazio no modo fixo) |
| `details.searches[].candidates` | Todos os trechos encontrados em cada busca, com a nota vetorial, a nota do re-ranqueamento (`null` se desligado) e se foram usados |
| `details.versions` | A resposta final e a extrativa, formada só pelos trechos usados |

**Erros:** `404` se o chat não existir. `502` se não for possível gerar a resposta (por exemplo, com o Ollama fora do ar); nesse caso nada é gravado.

**Tempo de resposta**, com os modelos já carregados: 7 a 18 s com placa de vídeo NVIDIA e 35 a 40 s só com processador. A primeira pergunta depois de subir o sistema é mais lenta, porque carrega os modelos na memória.

---

## Observação: acentos no terminal do Windows

No Git Bash, enviar JSON com acentos direto no `-d` pode corromper os caracteres, e a API responde `There was an error parsing the body`. Nesse caso, salve o corpo num arquivo UTF-8 e envie com `--data-binary`:

```bash
curl -X POST http://localhost:8000/chats/<chat_id>/messages -H "Content-Type: application/json" --data-binary @pergunta.json
```
