from functools import lru_cache

from app.infra.config import settings


@lru_cache
def get_llm():
    """Retorna o chat model configurado. Provedor trocável (openai/anthropic).

    A troca de provedor acontece só aqui — o resto do sistema não muda.
    Só é chamado quando settings.use_llm_reformulation está ligado.
    """
    provider = settings.llm_provider.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            temperature=0,
        )

    raise ValueError(f"Provedor de LLM não suportado: {settings.llm_provider}")
