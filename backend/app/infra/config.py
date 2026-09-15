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

    # Modo de resposta.
    # true  = agente: o LLM escolhe as ferramentas e quantas rodadas fazer
    # false = pipeline fixo: recuperar → reordenar → responder
    # Manter os dois permite comparar as duas arquiteturas.
    use_agent: bool = False
    agent_max_steps: int = 12  # teto de passos, evita loop infinito

    # Reformulação da resposta pelo LLM (só vale no modo pipeline —
    # no modo agente o LLM é sempre usado, ele é o próprio agente).
    # DESLIGADA por padrão: a resposta devolve os trechos recuperados como estão.
    # Ligar (true) quando quisermos comparar com a versão reformulada.
    use_llm_reformulation: bool = False

    llm_provider: str = "openai"  # openai | anthropic
    llm_model: str = "gpt-5.4-nano"  # usado pelo agente e pela reformulação
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
    # usado. Hoje aplicado só na ferramenta de busca do agente — o pipeline não
    # corta por nota. As notas vêm na resposta do chat, para calibração.
    similarity_threshold: float = 0.6

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # CORS — origens liberadas para o frontend
    cors_origins: list[str] = ["http://localhost:5173"]

    # App
    log_level: str = "INFO"


settings = Settings()
