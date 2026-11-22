from functools import lru_cache

from app.infra.config import settings


@lru_cache
def get_llm(temperature: float = 0.0):
    """Retorna o modelo de linguagem configurado.

    Na AWS, o Amazon Nova Lite pelo Bedrock. O Ollama serve para testar no
    computador sem gastar. A temperatura vem de cada chat; o cache guarda um
    modelo por temperatura.
    """
    provider = settings.llm_provider.lower()

    if provider == "bedrock":
        from langchain_aws import ChatBedrockConverse

        return ChatBedrockConverse(
            model=settings.llm_model,
            region_name=settings.aws_region,
            temperature=temperature,
            max_tokens=settings.llm_max_tokens,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
            reasoning=False,
        )

    raise ValueError(f"Provedor de LLM não suportado: {settings.llm_provider}")
