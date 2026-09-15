# Experimentos

Registro do que foi medido durante o desenvolvimento, com os números obtidos e o que eles mostram.

## Ambiente

| Item | Valor |
|---|---|
| Sistema | Windows 11 Pro, Docker Desktop (backend WSL2) |
| CPU disponível para o Docker | 12 núcleos |
| RAM disponível para o Docker | 2 GB nos experimentos 1 a 3; 8 GB no experimento 4 |
| Execução dos modelos | CPU, sem GPU |
| Modelo de embeddings | `intfloat/multilingual-e5-large` |
| Modelo de re-ranqueamento | `BAAI/bge-reranker-v2-m3` |
| Chunking | 1.400 caracteres, sobreposição de 200 |
| Trechos finais (k) | 3 |

## Material de teste

- **Fonte:** artigo "Fotossíntese" da Wikipédia em português (licença CC BY-SA), salvo em `contents/fotossintese.txt`.
- **Tamanho:** 16.730 caracteres.
- **Resultado da ingestão:** 17 trechos.

## Perguntas

| Id | Pergunta | Está no material? |
|---|---|---|
| P1 | "O que é o ciclo de Calvin?" | Sim — há um parágrafo dedicado |
| P2 | "Como faço um bolo de chocolate?" | Não — assunto sem relação |

---

## Experimento 1 — Um limiar de similaridade separa perguntas do tema e fora dele?

**Hipótese:** comparando a nota de similaridade da busca vetorial com um limiar fixo (0,6), seria possível recusar perguntas que não estão no material.

**Método:** busca vetorial apenas, sem re-ranqueamento, k = 3.

**Resultado:**

| Pergunta | Notas dos 3 trechos |
|---|---|
| P1 — no material | 0,8392 · 0,8372 · 0,7898 |
| P2 — fora do material | 0,7831 · 0,7825 · 0,7778 |
| **Diferença entre as melhores notas** | **0,056** |

**Conclusão: hipótese refutada.** A pergunta sem relação nenhuma com o material tirou 0,78, bem acima do limiar de 0,6, e ficou a só 0,056 da pergunta pertinente. Um limiar fixo não separa os dois casos.

**Por que acontece:** o modelo e5 vetoriza a pergunta e o trecho **separadamente** e compara os vetores. As notas ficam concentradas numa faixa estreita e alta, então o valor absoluto diz pouco sobre relevância.

A busca em si **acertou**: o primeiro trecho de P1 era o parágrafo sobre o ciclo de Calvin. O problema está na nota, não na ordenação.

---

## Experimento 2 — O re-ranqueamento resolve a separação?

**Hipótese:** um cross-encoder, que lê pergunta e trecho **juntos**, produz notas capazes de separar perguntas pertinentes das impertinentes.

**Método:** busca vetorial com 20 candidatos, re-ranqueamento com `bge-reranker-v2-m3`, mantendo os 3 melhores.

**Resultado:**

| Pergunta | Só busca vetorial | Com re-ranqueamento |
|---|---|---|
| P1 — no material | 0,8392 · 0,8372 · 0,7898 | **0,9932** · 0,9760 · 0,4282 |
| P2 — fora do material | 0,7831 · 0,7825 · 0,7778 | **0,0003** · 0,0003 · 0,0000 |
| **Diferença entre as melhores notas** | **0,056** | **0,993** |

**Conclusão: hipótese confirmada.** A separação passou de 0,056 para 0,993, cerca de 18 vezes maior. Qualquer limiar entre 0,05 e 0,40 separa os dois casos com folga.

**Resultado adicional:** em P1, o terceiro trecho recebeu 0,43, contra 0,99 e 0,98 dos dois primeiros. A busca vetorial dava 0,79 a ele, indistinguível dos outros. O cross-encoder identificou que esse trecho era só parcialmente relevante, o que permite descartar trechos fracos até dentro de uma pergunta pertinente.

---

## Experimento 3 — Quantos candidatos o re-ranqueamento precisa?

**Hipótese:** reduzir os candidatos de 20 para 7 diminui o tempo de resposta sem perder qualidade, já que o material inteiro tem só 17 trechos.

**Resultado:**

| Candidatos | Notas P1 | Notas P2 | Tempo por pergunta |
|---|---|---|---|
| 20 | 0,9932 · 0,9760 · 0,4282 | 0,0003 · 0,0003 · 0,0000 | 15,2 s e 15,9 s |
| 7 | 0,9932 · 0,9760 · 0,4282 | 0,0003 · 0,0000 · 0,0000 | 9,2 s a 13,1 s (média 10,7 s) |

**Conclusão:** qualidade idêntica, com os mesmos três trechos e as mesmas notas em P1. O tempo caiu, mas menos que a proporção de candidatos sugeria.

> ⚠️ **Os tempos deste experimento não são confiáveis.** Foram medidos com 2 GB de RAM no Docker, e o experimento 4 mostrou que parte do tempo era espera por falta de memória. A comparação de qualidade continua válida.

**Decisão tomada:** 7 candidatos.

---

## Experimento 4 — Memória disponível para o Docker

**Contexto:** ao carregar o re-ranqueador junto com o modelo de embeddings, a API parou de responder. Uma requisição ficou 240 s sem resposta e o container não aceitava nem ser encerrado.

**Diagnóstico:**

| Medida | Valor |
|---|---|
| RAM da máquina | 15,9 GB |
| RAM liberada para o Docker | 1,92 GB |
| Uso de CPU do container travado | 0,04 % |
| Memória estimada dos dois modelos | cerca de 2,2 GB cada, fora o ambiente Python |

A CPU quase parada mostra que o processo não estava calculando, e sim **esperando o disco**: sem memória suficiente, os dados dos modelos eram trocados com o disco o tempo todo.

**Intervenção:** memória do Docker aumentada para 8 GB (8,23 GB reportados).

**Resultado, com 7 candidatos e modelos já carregados:**

| Rodada | P1 | P2 |
|---|---|---|
| 1 | 6,46 s | 6,53 s |
| 2 | 6,78 s | 6,43 s |
| 3 | 6,44 s | 6,38 s |

| | 2 GB | 8 GB |
|---|---|---|
| Tempo médio | 10,7 s | **6,5 s** |
| Variação | 9,2 s a 13,1 s | **6,38 s a 6,78 s** |
| Notas | — | Idênticas às anteriores |

A primeira pergunta depois de subir a API levou 18,3 s, porque inclui carregar os modelos na memória.

**Conclusão:** cerca de um terço do tempo medido antes era falta de memória. Com 8 GB o tempo caiu e ficou estável: variação de 0,4 s, contra 3,9 s antes.

**Consequência:** com o tempo em 6,5 s, a troca do re-ranqueador por um modelo menor (`jina-reranker-v2`, 278M) foi descartada. O ganho estimado de cerca de 2 s não compensa a exigência de executar código do repositório do modelo (`trust_remote_code`) nem o risco de perda de qualidade.

---

## Testes de validação

Verificações de comportamento feitas após correções no backend.

| Teste | Resultado esperado | Resultado obtido |
|---|---|---|
| Ingestão de texto | 17 trechos, status `done`, texto salvo | 17 trechos, `done`, 16.730 caracteres salvos |
| Exclusão de material remove vetores | Índice vai de 17 para 0 vetores | 17 → 0 |
| Pergunta após excluir o material | Nenhum trecho encontrado | `"Não encontrei nada no material do curso."`, 0 fontes |
| Exclusão remove o arquivo | Arquivo apagado do disco | Apagado |
| Resultados após refatoração da recuperação | Mesmas notas de antes | 0,9932 · 0,976 · 0,4282 e 0,0003 · 0 · 0 |

---

## Limitações destes resultados

- **Amostra pequena:** um único material e duas perguntas. Os números mostram a tendência, mas não bastam para calibrar o limiar com segurança.
- **Julgamento de relevância manual:** "está no material" foi avaliado por leitura, sem conjunto rotulado.
- **Um único tipo de conteúdo:** texto enciclopédico. Transcrições de aula, com fala corrida e erros de reconhecimento, podem se comportar diferente.
- **Ambiente único:** tempos medidos numa só máquina, em CPU, dentro do Docker Desktop.
- **Modos com LLM não avaliados:** reformulação e agente ainda não foram executados.

## Experimentos planejados

- Calibrar `SIMILARITY_THRESHOLD` com um conjunto maior de perguntas, incluindo perguntas difíceis: do mesmo assunto geral, mas ausentes do material (por exemplo, mitose num curso de fotossíntese).
- Comparar pipeline e agente com as mesmas perguntas.
- Comparar resposta extrativa e resposta reformulada.
- Avaliar o tamanho do modelo Whisper em áudio real de aula.
- Avaliar com os critérios da proposta: precisão semântica, coerência textual e usabilidade.
