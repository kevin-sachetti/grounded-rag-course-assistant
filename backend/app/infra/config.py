from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação, lidas de variáveis de ambiente / arquivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Banco de dados
    database_url: str = "postgresql+psycopg://tcc:tcc@localhost:5432/tcc"

    # Armazenamento de arquivos (storage adapter local)
    upload_dir: str = "/data/uploads"
    # Tamanho máximo de um arquivo enviado. Igual ao limite do nginx da interface.
    max_upload_mb: int = 1024

    # Ingestão
    whisper_model_size: str = "base"  # tamanho do modelo Whisper (tiny/base/small/medium)
    # Modelo de embeddings (local, aberto). 19º no MTEB-BR, 560M params,
    # 1024 dimensões, máximo de 512 tokens por texto.
    embedding_model_name: str = "intfloat/multilingual-e5-large"
    # O E5 foi treinado com estes prefixos; sem eles a recuperação piora.
    # Outros modelos usam prefixo diferente ou nenhum — daí serem configuráveis.
    embedding_query_prefix: str = "query: "
    embedding_document_prefix: str = "passage: "
    # Medidos em CARACTERES (~3,5 char = 1 token em português).
    # 1400 ≈ 400 tokens: cabe no limite de 512 do e5-large e fica na faixa
    # recomendada pela literatura; ~1 conceito explicado por chunk.
    chunk_size: int = 1400
    chunk_overlap: int = 200  # ~14% — cobre frases cortadas na fala contínua

    # Agente ligado ou desligado é escolha de cada chat (tabela chats).
    agent_max_steps: int = 12  # teto de passos do agente, evita loop infinito

    # Reformulação da resposta pelo LLM no fluxo fixo (agente desligado).
    # Ligada: com o LLM local não há custo por uso. Desligar (false) devolve
    # os trechos como estão — útil para testar sem o Ollama de pé.
    use_llm_reformulation: bool = True

    # LLM local via Ollama (sem custo por uso). openai/anthropic seguem como opção.
    llm_provider: str = "ollama"  # ollama | openai | anthropic
    # Escolhido em teste com Qwen3 8B, Qwen3.5 4B e Granite 4.1 3B (16/11/2026):
    # único que buscou antes de recusar, fez uma busca por assunto e usou a
    # ferramenta de resumo, com 7 a 18 s por resposta no agente.
    llm_model: str = "qwen3.5:4b"  # usado pelo agente e pela reformulação
    ollama_base_url: str = "http://ollama:11434"
    llm_reasoning: bool = False  # modo de raciocínio dos modelos que o têm
    # Janela de contexto do Ollama, em tokens. O padrão dele (4096) não comporta
    # o texto da ferramenta de resumo (~3.400 tokens) somado ao histórico.
    llm_context_tokens: int = 8192

    # Quantas mensagens anteriores do chat o agente recebe para entender
    # perguntas de continuação ("e o que mais?"). 6 = as últimas 3 trocas.
    chat_history_messages: int = 6

    # Os valores abaixo são os INICIAIS de cada chat novo; depois cada chat
    # guarda os seus (tabela chats).
    retrieval_k: int = 3  # trechos que sobram no final (pico de F1 na literatura)

    # Re-ranking (busca em dois estágios).
    # O e5 varre tudo e traz `retrieval_candidates`; o cross-encoder reordena
    # e sobram `retrieval_k`. Motivo: as notas do e5 ficam espremidas em uma
    # faixa estreita e não separam pergunta pertinente de impertinente.
    use_reranker: bool = True
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    # Alguns modelos (ex: jina-reranker-v2) carregam código Python do próprio
    # repositório no HuggingFace. Ligar só para modelos de origem confiável.
    reranker_trust_remote_code: bool = False
    retrieval_candidates: int = 7  # candidatos do 1º estágio

    # Relevância mínima (0 a 1, na escala do re-ranqueador) para um trecho ser
    # usado. Vale no fluxo fixo e no agente: sem trecho acima dela, recusa.
    # Com o re-ranqueamento desligado, é comparada à nota da busca vetorial.
    similarity_threshold: float = 0.6

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # CORS — origens liberadas para o frontend
    cors_origins: list[str] = ["http://localhost:5173"]

    # App
    log_level: str = "INFO"


settings = Settings()
