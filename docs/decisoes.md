# Decisões técnicas

Cada decisão com o contexto, as alternativas avaliadas e o motivo da escolha. Decisões marcadas como **provisórias** devem ser revistas com base em testes.

## Sumário

| # | Decisão | Escolha | Situação |
|---|---|---|---|
| D1 | Linguagem | Python 3.14 | Definida |
| D2 | Framework da API | FastAPI | Definida |
| D3 | Banco de dados | PostgreSQL + pgvector | Definida |
| D4 | Orquestração | LangChain + LangGraph | Definida |
| D5 | Organização do código | Camadas features / pipeline / adapters / infra | Definida |
| D6 | Modelo de embeddings | multilingual-e5-large | Definida |
| D7 | Tamanho dos trechos | 1.400 caracteres, sobreposição de 200 | Provisória |
| D8 | Quantidade de trechos | k = 3, com 7 candidatos | Provisória |
| D9 | Re-ranqueamento | bge-reranker-v2-m3 | Definida |
| D10 | Uso de LLM | Mínimo; OpenAI, tier mais barato | Provisória |
| D11 | Limiar de relevância | 0,6 sobre a nota do re-ranqueador | Provisória |
| D12 | Arquitetura agêntica | Agente com ferramentas restritas ao material | Implementada, não testada |
| D13 | Transcrição | Whisper `base` | Provisória |
| D14 | Infraestrutura | Execução local com Docker | Definida |
| D15 | Frontend | Vue + TypeScript | Só o framework definido |

---

## D1 — Linguagem: Python 3.14

**Contexto.** A proposta original usava Python 3.10. Com o projeto refeito do zero, a versão foi reavaliada.

**Alternativas:** 3.10 (versão da proposta), 3.11, 3.12 e 3.14.

**Escolha: 3.14.**

**Motivo.** O risco de usar a versão mais nova é faltar pacote pré-compilado (*wheel*) para as bibliotecas de aprendizado de máquina. Esse risco foi verificado diretamente no PyPI antes da escolha:

- todos os pacotes com código nativo têm wheel para 3.14: `torch` 2.13, `numba` 0.67, `scipy`, `scikit-learn`, `pydantic-core`, `psycopg-binary`, entre outros;
- `tokenizers` e `safetensors` usam wheels de ABI estável, compatíveis com 3.14;
- o índice CPU do PyTorch tem wheel 3.14 para x86_64, que é o usado no Docker.

A instalação confirmou: nenhuma dependência precisou ser compilada.

**Observação.** O recurso mais conhecido da 3.14, o Python sem GIL, não é aproveitado: exige uma compilação especial que as bibliotecas de aprendizado de máquina ainda não suportam bem.

## D2 — Framework da API: FastAPI

**Escolha: FastAPI.**

**Motivo.** Assíncrono, o que é necessário para atender requisições enquanto modelos processam em segundo plano. Valida entrada e saída por tipos com Pydantic e gera a documentação interativa da API automaticamente.

## D3 — Banco de dados: PostgreSQL + pgvector

**Contexto.** O sistema precisa guardar dados relacionais (cursos e materiais) e fazer busca por similaridade de vetores.

**Alternativas avaliadas:**

| Opção | Por que não |
|---|---|
| FAISS (proposta original) | É só um índice: não gerencia metadados nem persistência sozinho |
| Chroma, Qdrant | Bons bancos vetoriais, mas exigiriam um segundo banco para os dados relacionais |
| MongoDB | A busca vetorial só existe na versão em nuvem (Atlas); a versão local não tem |
| DynamoDB | Sem busca vetorial nativa e só em nuvem |
| Amazon Bedrock Knowledge Bases | Só em nuvem, e esconderia justamente o pipeline de RAG, que é objeto do trabalho |

**Escolha: PostgreSQL com a extensão pgvector.**

**Motivo.**

- Um banco só guarda os dados relacionais e os vetores.
- Os dados são naturalmente relacionais: curso → materiais → trechos.
- Roda localmente em Docker.
- Tem caminho direto para a nuvem: o mesmo pgvector existe no Amazon Aurora e no RDS, sem mudança de código.

## D4 — Orquestração: LangChain + LangGraph

**Escolha: LangChain para os componentes e LangGraph para os fluxos.**

**Motivo.**

- **LangChain** padroniza os componentes: divisão de texto, embeddings, banco vetorial e LLM. Trocar um modelo ou um banco muda uma linha, não o sistema.
- **LangGraph** modela o processamento como um grafo de estados, com arestas condicionais e ciclos. O pipeline usa as arestas condicionais; o agente depende do ciclo agente → ferramentas → agente, que um encadeamento linear não expressa.

## D5 — Organização do código

**Alternativas:**

| Opção | Característica |
|---|---|
| Por camada técnica (`models/`, `routes/`, `services/`) | Simples, mas cada funcionalidade fica espalhada em várias pastas |
| Por funcionalidade (`courses/`, `materials/`, `chat/`) | Coesa, mas mistura regra de negócio com processamento de IA e integrações |

**Escolha: modelo híbrido em quatro camadas.**

- `features/` — funcionalidades, organizadas por assunto;
- `pipeline/` — processamento de IA, separado do CRUD;
- `adapters/` — integrações trocáveis;
- `infra/` — fundação técnica.

**Motivo.** O projeto tem três naturezas distintas: regra de negócio, processamento de IA e integrações externas. Cada uma ganhou um lugar próprio. Os nomes foram escolhidos para serem autoexplicativos: `features` em vez de `domains` e `infra` em vez de `core`.

## D6 — Modelo de embeddings: multilingual-e5-large

**Contexto.** O modelo roda localmente em CPU, então tamanho importa tanto quanto qualidade em português.

**Alternativas**, com resultados do benchmark MTEB-BR (português brasileiro, 93 modelos, 22 tarefas):

| Modelo | Parâmetros | Posição | Nota | Observação |
|---|---|---|---|---|
| Qwen3-Embedding-8B | 7,6 B | 2º | 0,670 | Exige GPU |
| Qwen3-Embedding-4B | 4 B | 6º | 0,662 | Exige GPU |
| embeddinggemma-300m | 308 M | 13º | 0,649 | Exige aceitar licença e usar token do HuggingFace |
| **multilingual-e5-large** | **560 M** | **19º** | **0,641** | **Aberto** |
| bge-m3 | 568 M | 29º | 0,643 | Primeira escolha, substituída |
| Qwen3-Embedding-0.6B | 596 M | 38º | ~0,620 | — |

**Escolha: `intfloat/multilingual-e5-large`.**

**Motivo.** O `embeddinggemma-300m` tinha nota um pouco melhor e metade do tamanho, mas o acesso exige aceitar a licença e configurar um token. O e5-large fica 0,008 abaixo, é aberto e é bem estabelecido na literatura. Os modelos de 4 B e 8 B foram descartados por exigirem GPU.

**Consequências:**

1. **Prefixos obrigatórios.** O e5 foi treinado com `query: ` nas perguntas e `passage: ` nos documentos. Sem eles a recuperação piora sem gerar nenhum erro. O adapter de embeddings adiciona os prefixos automaticamente, e eles são configuráveis para outros modelos.
2. **Limite de 512 tokens por texto.** O que passa disso é cortado em silêncio, o que limita o tamanho dos trechos (D7).
3. **Trocar de modelo exige reprocessar todos os materiais**, porque vetores de modelos diferentes não são comparáveis.

## D7 — Tamanho dos trechos: 1.400 caracteres, sobreposição de 200 *(provisória)*

**Contexto.** O texto de um material é dividido em trechos. Trechos pequenos são precisos, mas cortam explicações no meio. Trechos grandes preservam contexto, mas o vetor passa a representar vários assuntos misturados e a busca perde precisão.

**O que a literatura indica:**

- Faixa inicial recomendada: 400 a 512 tokens por trecho.
- A precisão cai quando os trechos passam de cerca de 1.000 tokens.
- Sobreposição tem evidência contraditória: um estudo de 2026 não encontrou benefício; outro encontrou o melhor resultado com 25%, e piora com 50%.

**Cuidado com a unidade.** O divisor do LangChain conta **caracteres**, mas a literatura fala em **tokens**. Em português, cerca de 3,5 caracteres formam um token.

**Escolha: 1.400 caracteres (≈ 400 tokens) com sobreposição de 200 (≈ 14%).**

**Motivo.**

- Fica dentro da faixa recomendada e abaixo do limite de 512 tokens do e5 (D6), que equivale a cerca de 1.800 caracteres.
- Numa aula falada, um conceito costuma ocupar de 600 a 1.500 caracteres, então cada trecho tende a conter uma explicação completa.
- A sobreposição de 14% fica na faixa conservadora e ajuda na fala contínua, onde frases são cortadas no meio com frequência.

**A rever:** com transcrições reais de aula.

## D8 — Quantidade de trechos: k = 3, com 7 candidatos *(provisória)*

**Contexto.** Poucos trechos focam a resposta, mas podem deixar parte dela de fora. Muitos trechos trazem ruído, e os estudos mostram que o modelo não converte a evidência extra em resposta melhor.

**Escolha: 3 trechos finais, a partir de 7 candidatos da busca vetorial.**

**Motivo.**

- A literatura aponta pico de desempenho (F1) em k = 3.
- No modo extrativo os trechos vão direto para o aluno ler: 3 trechos de 1.400 caracteres são legíveis, 4 ou mais viram um bloco de texto grande demais.
- Os candidatos foram reduzidos de 20 para 7 sem nenhuma perda de qualidade — ver [experimento 3](experimentos.md#experimento-3--quantos-candidatos-o-re-ranqueamento-precisa).

## D9 — Re-ranqueamento: bge-reranker-v2-m3

**Contexto.** O [experimento 1](experimentos.md#experimento-1--um-limiar-de-similaridade-separa-perguntas-do-tema-e-fora-dele) mostrou que as notas da busca vetorial não separam uma pergunta pertinente de uma sem relação (diferença de 0,056).

**Alternativas:**

| Modelo | Parâmetros | Observação |
|---|---|---|
| **bge-reranker-v2-m3** | 568 M | Referência multilíngue mais adotada |
| jina-reranker-v2-base-multilingual | 278 M | Mais rápido; exige executar código do repositório do modelo |
| Qwen3-Reranker-0.6B | 600 M | Mais recente |
| mmarco-mMiniLMv2-L12 | 118 M | O mais leve, qualidade menor |

**Escolha: `BAAI/bge-reranker-v2-m3`, em busca de dois estágios.**

**Motivo.** Um cross-encoder lê pergunta e trecho juntos, e por isso produz notas que discriminam relevância. A separação passou de 0,056 para 0,993 — ver [experimento 2](experimentos.md#experimento-2--o-re-ranqueamento-resolve-a-separação).

**Custo aceito.** O cross-encoder não pode ser pré-calculado: roda uma vez por candidato a cada pergunta. O tempo ficou em cerca de 6,5 s por pergunta com 8 GB de RAM.

**Por que não o jina.** Com o tempo em 6,5 s, o ganho estimado de cerca de 2 s não compensava a execução de código de terceiros nem o risco de perder qualidade.

## D10 — Uso de LLM *(provisória)*

**Contexto.** A chamada ao LLM é a única parte com custo por uso. A proposta prevê o LLM para reformular perguntas e melhorar a clareza das respostas — não para ser a fonte do conhecimento.

**Evolução da decisão:**

1. **Primeira versão:** duas chamadas por pergunta, uma para avaliar se os trechos serviam e outra para redigir a resposta.
2. **Avaliação removida:** a decisão de relevância passou para as notas de similaridade, sem LLM, deixando uma chamada por pergunta.
3. **Reformulação desligada por padrão:** para avaliar a recuperação isoladamente, sem custo — se os trechos vierem errados, nenhum LLM corrige.

**Provedor e modelo: OpenAI, no tier mais barato** (`gpt-5.4-nano`).

**Modelos descartados:**

| Modelo | Motivo |
|---|---|
| `gpt-3.5-turbo` | API desligada pela OpenAI em 23/10/2026 |
| `gpt-4o-mini` | Saiu da página oficial de preços, substituído por gerações novas |

**Pendente:** o nome `gpt-5.4-nano` e seus preços vieram de fontes de terceiros e precisam ser confirmados na conta da OpenAI antes do uso.

**Ordem de grandeza de custo**, com preços de terceiros (US$ 0,20 por milhão de tokens de entrada e US$ 1,25 de saída) e cerca de 2.100 tokens de entrada e 310 de saída por pergunta:

| Modo | Chamadas por pergunta | Custo estimado a cada mil perguntas |
|---|---|---|
| Pipeline reformulado | 1 | cerca de US$ 0,80 |
| Agente | 2 a 4, com mais contexto | alguns dólares |

## D11 — Limiar de relevância: 0,6 *(provisória)*

**Escolha: 0,6.**

**Situação.** Sobre as notas da busca vetorial esse limiar não funciona (experimento 1). Sobre as notas do re-ranqueador ele separa bem os casos testados: mantém 0,99 e 0,98, descarta 0,43 e recusa a pergunta sem relação (0,0003).

**Onde é aplicado hoje:** só na ferramenta de busca do agente. O pipeline ainda não corta trechos pela nota.

**A rever:** com um conjunto maior de perguntas, incluindo perguntas do mesmo assunto geral que não estão no material.

## D12 — Arquitetura agêntica

**Contexto.** O projeto evoluiu de um RAG com caminho fixo para uma arquitetura agêntica.

**Diferença:**

| | RAG tradicional | RAG agêntico |
|---|---|---|
| Quem define o caminho | O código | O modelo, a cada pergunta |
| Fluxo | Linear | Cíclico |
| Buscas | Uma, fixa | Quantas forem necessárias |
| Ações | Só buscar | Escolhe entre ferramentas |

**Níveis considerados:**

| Nível | O que acrescenta |
|---|---|
| 1 | Avalia o resultado da busca e reformula a pergunta em caso de falha |
| 2 | Planeja: divide perguntas com mais de um assunto em buscas separadas |
| 3 | Escolhe entre ferramentas conforme a intenção da pergunta |

**Escolha: nível 3.**

**Risco identificado.** Mais autonomia pode enfraquecer a principal promessa do trabalho, a de responder só com o material autorizado.

**Solução — autonomia de estratégia, não de fonte.** Todas as ferramentas leem apenas o material do curso, e o curso é fixado na montagem das ferramentas, não informado pelo modelo. O agente decide como procurar, mas não tem acesso a nenhuma fonte externa. Ver [arquitetura](arquitetura.md#fluxo-3--agente).

**Custos aceitos:**

- toda pergunta passa a usar o LLM;
- o comportamento deixa de ser determinístico;
- são várias chamadas por pergunta.

**O pipeline fixo foi mantido** (`USE_AGENT=false`), o que permite comparar as duas arquiteturas com as mesmas perguntas.

**Relação com a proposta.** Um dos objetivos específicos já previa usar o modelo de linguagem para reformular perguntas, que é a base do RAG agêntico.

## D13 — Transcrição: Whisper `base` *(provisória)*

**Escolha atual: `base`** (74 M parâmetros).

**Situação.** Ainda não foi testado com áudio real. Português é menos bem atendido que inglês por esses modelos, e o `base` tende a errar termos técnicos. O `small` (244 M) costuma ser o mínimo recomendável para material educacional em português.

**A rever:** com gravações reais de aula, medindo qualidade e tempo.

## D14 — Infraestrutura

**Escolha: execução local com Docker Compose**, conforme a proposta. Uma hospedagem em nuvem, apenas para demonstração, fica para depois.

Decisões de ambiente, cada uma motivada por um problema concreto:

| Decisão | Problema que resolve |
|---|---|
| PyTorch instalado do índice CPU | O pacote padrão traz bibliotecas de GPU que somam alguns GB e não servem sem GPU |
| `ffmpeg` na imagem | O Whisper não lê áudio nem vídeo sem ele |
| Volume nomeado para o PostgreSQL | Montar uma pasta do Windows quebra as permissões que o PostgreSQL exige (`0700`) |
| Volume `modelcache` | Sem ele, cada reconstrução da imagem baixaria os modelos de novo |
| `HF_HUB_DISABLE_XET=1` | O download do re-ranqueador falhou no meio pelo backend Xet do HuggingFace (*CAS Client Error*); o download HTTP clássico é estável |
| 8 GB de RAM para o Docker | Com 2 GB a API travava ao carregar os dois modelos — ver [experimento 4](experimentos.md#experimento-4--memória-disponível-para-o-docker) |
| Teto `pgvector<0.4` | Exigência do `langchain-postgres` 0.0.17 |

## D15 — Frontend: Vue + TypeScript

**Alternativas:**

| | React | Vue |
|---|---|---|
| Ecossistema e material de apoio | Maior | Menor |
| Curva de aprendizado | Mais íngreme | Mais suave |
| Organização | Mais decisões a tomar | Roteamento e estado oficiais |

**Escolha: Vue com TypeScript.**

**Situação.** **Só o framework está definido.** Telas, funcionalidades e aparência ainda não foram decididos. O código em `frontend/` é um rascunho, não uma versão aprovada.

---

## Referências

- STEKEL, T. R. C. *MTEB-BR: A Text Embedding Benchmark for Brazilian Portuguese*. arXiv:2607.04581, 2026. https://arxiv.org/abs/2607.04581v2
- *Beyond Multilingual Averages: MTEB-PT, a Benchmark for Portuguese Sentence Encoders*. arXiv:2607.04071, 2026. https://arxiv.org/html/2607.04071
- WANG, L. et al. *Multilingual E5 Text Embeddings: A Technical Report*. arXiv:2402.05672, 2024. https://arxiv.org/abs/2402.05672
- Cartão do modelo multilingual-e5-large. https://huggingface.co/intfloat/multilingual-e5-large
- Cartão do modelo bge-reranker-v2-m3. https://huggingface.co/BAAI/bge-reranker-v2-m3
- *A Systems-Level Analysis of Sensitivity, Robustness, and Stability in Retrieval-Augmented Generation*. arXiv:2606.28337, 2026. https://arxiv.org/pdf/2606.28337
- *Chunk Size as an Experimental Variable in RAG Systems*. Towards Data Science. https://towardsdatascience.com/chunk-size-as-an-experimental-variable-in-rag-systems/
- *RAG Chunking Strategies: A 2026 Retrieval Playbook*. https://www.digitalapplied.com/blog/rag-chunking-strategies-2026-retrieval-quality-playbook
- *Best Reranker Models for RAG: Open-Source vs API Comparison (2026)*. https://docs.bswen.com/blog/2026-02-25-best-reranker-models/
- ASAI, A. et al. *Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection*. arXiv:2310.11511, 2023. https://arxiv.org/abs/2310.11511
- YAN, S.-Q. et al. *Corrective Retrieval Augmented Generation*. arXiv:2401.15884, 2024. https://arxiv.org/abs/2401.15884
- OpenAI — página de descontinuação de modelos. https://developers.openai.com/api/docs/deprecations
- RADFORD, A. et al. *Robust Speech Recognition via Large-Scale Weak Supervision*. OpenAI, 2022.
- REIMERS, N.; GUREVYCH, I. *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. EMNLP, 2019.
