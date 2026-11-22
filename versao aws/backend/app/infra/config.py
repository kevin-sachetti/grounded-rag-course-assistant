from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da versão AWS, lidas de variáveis de ambiente / arquivo .env.

    Na Lambda, os valores vêm das variáveis definidas no template do SAM.
    Para rodar no computador (desenvolvimento), `local_dev` usa um DynamoDB e
    um S3 locais e `auth_disabled` dispensa o login.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- AWS ----
    aws_region: str = "us-east-2"
    # Desenvolvimento no computador: cria tabelas e bucket nos emuladores.
    # Os endereços deles vêm das variáveis do próprio boto3
    # (AWS_ENDPOINT_URL_DYNAMODB e AWS_ENDPOINT_URL_S3).
    local_dev: bool = False
    # Endereço do S3 local visto pelo navegador (o envio vai direto do navegador
    # ao S3). Vazio na AWS, onde o endereço é o mesmo para todos.
    aws_public_endpoint_url: str = ""
    data_bucket: str = "grounded-rag-dados"
    table_users: str = "grounded-rag-usuarios"
    table_materials: str = "grounded-rag-materiais"
    table_chats: str = "grounded-rag-chats"
    table_messages: str = "grounded-rag-mensagens"
    table_usage: str = "grounded-rag-uso"
    # Nome da Lambda de ingestão. Vazio = processa na própria API (desenvolvimento).
    ingest_function: str = ""

    # ---- Login (Cognito) ----
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    # Só para desenvolvimento local: todo pedido vira deste usuário, sem login.
    auth_disabled: bool = False
    dev_user_id: str = "usuario-de-desenvolvimento"

    # ---- Limites (decididos com o autor em 21/11/2026) ----
    storage_limit_mb: int = 200  # espaço por usuário
    questions_per_day: int = 20  # perguntas por usuário por dia
    monthly_budget_usd: float = 10.0  # teto do mês, somando todos os usuários
    # Custo estimado de uma pergunta: Lambda (~5,5 s com 10 GB) + Bedrock.
    # Medido na prova de conceito; serve para o contador do teto.
    cost_per_question_usd: float = 0.001
    # Custo estimado de vetorizar um trecho na ingestão (~0,8 s com 10 GB).
    cost_per_chunk_usd: float = 0.00014
    inactivity_days: int = 30  # sem entrar por isso, chats e materiais são apagados
    # Fuso usado para "perguntas do dia" e para o mês do teto.
    timezone: str = "America/Sao_Paulo"
    # Validade do endereço de envio direto ao S3.
    upload_url_seconds: int = 900

    # Carrega o e5 e o bge na inicialização da Lambda (e não na 1ª pergunta).
    preload_models: bool = False

    # ---- Ingestão ----
    # Medidos em CARACTERES (~3,5 char = 1 token em português).
    # 1400 ≈ 400 tokens: cabe no limite de 512 do e5-large e fica na faixa
    # recomendada pela literatura; ~1 conceito explicado por chunk.
    chunk_size: int = 1400
    chunk_overlap: int = 200  # ~14% — cobre frases cortadas na fala contínua

    # ---- Embeddings ----
    embedding_model_name: str = "intfloat/multilingual-e5-large"
    # O e5 foi treinado com estes prefixos; sem eles a busca piora sem erro.
    embedding_query_prefix: str = "query: "
    embedding_document_prefix: str = "passage: "

    # ---- LLM ----
    # Na AWS, o Amazon Nova Lite no Bedrock. "ollama" serve para testar no
    # computador sem gastar com o Bedrock.
    llm_provider: str = "bedrock"  # bedrock | ollama
    llm_model: str = "amazon.nova-lite-v1:0"  # disponível direto em Ohio
    ollama_base_url: str = "http://ollama:11434"
    llm_max_tokens: int = 1024

    # Os valores abaixo são os INICIAIS de cada chat novo; depois cada chat
    # guarda os seus.
    retrieval_k: int = 3  # trechos que sobram no final (pico de F1 na literatura)
    use_reranker: bool = True
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    retrieval_candidates: int = 7  # candidatos do 1º estágio
    # Relevância mínima (0 a 1, na escala do re-ranqueador). Sem trecho acima
    # dela, o sistema recusa. Calibrada com os modelos originais (sem conversão).
    similarity_threshold: float = 0.6

    # Prefixo das rotas visto pelo navegador: na AWS o CloudFront repassa
    # /api/* para a Lambda, e o Mangum tira o prefixo antes do FastAPI.
    api_base_path: str = "/"

    # CORS — só para o desenvolvimento; na AWS o site e a API têm o mesmo endereço.
    cors_origins: list[str] = ["http://localhost:5173"]

    log_level: str = "INFO"


settings = Settings()
