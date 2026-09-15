# Chatbot Educacional Customizável com Inteligência Artificial

Trabalho de Conclusão de Curso — Análise e Desenvolvimento de Sistemas.
*Título em revisão, acompanhando a evolução do projeto para uma arquitetura agêntica.*

## O que é

Um assistente conversacional que o educador alimenta com o material do próprio curso — vídeo, áudio, PDF ou texto. O sistema transcreve e indexa esse conteúdo e responde às dúvidas dos alunos **usando exclusivamente o material cadastrado**. Quando a resposta não está no material, ele informa isso em vez de inventar.

Tecnicamente, é um sistema de **RAG (Retrieval-Augmented Generation)** com:

- **ingestão multimídia** — transcrição automática de áudio e vídeo;
- **recuperação em dois estágios** — busca vetorial densa seguida de re-ranqueamento por cross-encoder;
- **dois modos de resposta** — um pipeline fixo e um agente que escolhe ferramentas, ambos restritos ao material do curso;
- **execução local** — os modelos de embeddings, re-ranqueamento e transcrição rodam na própria máquina.

## Estado atual

| Parte | Situação |
|---|---|
| API, banco e pgvector | ✅ testado |
| Cursos (CRUD) | ✅ testado |
| Upload e ingestão de arquivo de texto | ✅ testado |
| Busca vetorial + re-ranqueamento | ✅ testado e medido — ver [experimentos](docs/experimentos.md) |
| Exclusão de material (arquivo + vetores) | ✅ testado |
| Ingestão de áudio, vídeo e PDF | ⚠️ implementado, não testado |
| Resposta reformulada por LLM | ⚠️ implementado, não testado |
| Agente com ferramentas | ⚠️ implementado, não testado |
| Frontend | ⏳ a definir |

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.14 |
| API | FastAPI |
| Orquestração | LangChain + LangGraph |
| Banco | PostgreSQL 17 + pgvector |
| Embeddings | `intfloat/multilingual-e5-large` (local) |
| Re-ranqueamento | `BAAI/bge-reranker-v2-m3` (local) |
| Transcrição | Whisper (local) |
| LLM | OpenAI (opcional, desligado por padrão) |
| Infraestrutura | Docker Compose |
| Frontend | Vue + TypeScript (a definir) |

Os motivos de cada escolha estão em [docs/decisoes.md](docs/decisoes.md).

## Pré-requisitos

- **Docker Desktop.**
- **8 GB de RAM liberados para o Docker** (*Settings → Resources → Memory*). Com 2 GB os modelos não cabem na memória e a API trava — ver [experimentos](docs/experimentos.md).
- **Internet na primeira execução**: são baixados cerca de 4,5 GB de modelos, que depois ficam em cache.
- **Chave da OpenAI** apenas para os modos que usam LLM, desligados por padrão.

## Como rodar

1. Criar o arquivo de variáveis de ambiente:

   ```bash
   cp backend/.env.example backend/.env
   ```

2. Subir o banco e a API:

   ```bash
   docker compose up -d --build
   ```

3. Conferir se está tudo de pé:

   ```bash
   curl http://localhost:8000/health
   ```

   Resposta esperada: `{"status":"ok","database":"connected","pgvector":true}`

A documentação interativa da API (Swagger) fica em http://localhost:8000/docs.

> A primeira ingestão baixa o modelo de embeddings e a primeira pergunta baixa o re-ranker, então as duas demoram bem mais que o normal. Os modelos ficam guardados no volume `modelcache`.

## Uso rápido

```bash
# 1. criar um curso (guarde o "id" da resposta)
curl -X POST http://localhost:8000/courses -H "Content-Type: application/json" -d '{"name": "Biologia"}'

# 2. enviar um material para o curso
curl -X POST http://localhost:8000/courses/<course_id>/materials -F "file=@contents/fotossintese.txt"

# 3. acompanhar o processamento até "status": "done"
curl http://localhost:8000/materials/<material_id>

# 4. perguntar
curl -X POST http://localhost:8000/courses/<course_id>/chat -H "Content-Type: application/json" -d '{"question": "Como funciona o ciclo de Calvin?"}'
```

Detalhes de cada endpoint em [docs/api.md](docs/api.md).

## Configuração

As configurações ficam em `backend/app/infra/config.py` e podem ser sobrescritas no `backend/.env`, com o nome em maiúsculas. **Depois de alterar o `.env`, recrie o container** com `docker compose up -d` — só recarregar o código não aplica variáveis novas.

| Variável | Padrão | O que controla |
|---|---|---|
| `USE_AGENT` | `false` | Modo agente (`true`) ou pipeline fixo (`false`) |
| `USE_LLM_REFORMULATION` | `false` | No pipeline, reformula a resposta com LLM |
| `USE_RERANKER` | `true` | Liga o segundo estágio da recuperação |
| `RETRIEVAL_CANDIDATES` | `7` | Trechos trazidos pela busca vetorial |
| `RETRIEVAL_K` | `3` | Trechos que sobram depois do re-ranqueamento |
| `SIMILARITY_THRESHOLD` | `0.6` | Relevância mínima (hoje aplicada só no agente) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1400` / `200` | Tamanho dos trechos, em caracteres |
| `EMBEDDING_MODEL_NAME` | `intfloat/multilingual-e5-large` | Modelo de embeddings |
| `RERANKER_MODEL_NAME` | `BAAI/bge-reranker-v2-m3` | Modelo de re-ranqueamento |
| `WHISPER_MODEL_SIZE` | `base` | Tamanho do modelo de transcrição |
| `LLM_PROVIDER` / `LLM_MODEL` | `openai` / `gpt-5.4-nano` | Provedor e modelo de LLM |
| `AGENT_MAX_STEPS` | `12` | Limite de passos do agente |
| `OPENAI_API_KEY` | — | Chave da OpenAI |

> Trocar `EMBEDDING_MODEL_NAME` exige reprocessar todos os materiais: vetores de modelos diferentes não são comparáveis.

## Modos de resposta

| Modo | Configuração | Usa LLM | Resposta |
|---|---|---|---|
| Pipeline extrativo *(padrão)* | `USE_AGENT=false`, `USE_LLM_REFORMULATION=false` | Não | Os trechos do material, sem alteração |
| Pipeline reformulado | `USE_AGENT=false`, `USE_LLM_REFORMULATION=true` | 1 chamada | Texto redigido a partir dos trechos |
| Agente | `USE_AGENT=true` | Várias chamadas | O modelo escolhe quais ferramentas usar |

## Estrutura

```
TCC/
├── backend/
│   ├── app/
│   │   ├── main.py        entrada da API
│   │   ├── features/      cursos, materiais e chat (rotas e regras de negócio)
│   │   ├── pipeline/      ingestão, recuperação, pipeline RAG e agente
│   │   ├── adapters/      integrações trocáveis: storage, embeddings, vectorstore, reranker, llm
│   │   └── infra/         configuração, banco e logging
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/              a definir
├── contents/              materiais usados nos testes
├── docker/postgres/       script que habilita o pgvector
├── docs/                  documentação
└── docker-compose.yml
```

## Documentação

- [Arquitetura](docs/arquitetura.md) — camadas, fluxos, modelo de dados e limitações
- [Decisões técnicas](docs/decisoes.md) — o que foi escolhido, alternativas e motivos
- [Experimentos](docs/experimentos.md) — o que foi medido e o que os resultados mostram
- [API](docs/api.md) — endpoints, entradas e saídas

## Limitações conhecidas

- As tabelas são criadas na subida da API, sem migrações — mudar o schema exige recriar tabelas.
- O upload não valida tamanho nem tipo de arquivo.
- Não há autenticação.
- O processamento dos materiais não sobrevive a um reinício da API: um material pode ficar parado em `processing`.

Detalhes em [docs/arquitetura.md](docs/arquitetura.md#limitações-conhecidas).
