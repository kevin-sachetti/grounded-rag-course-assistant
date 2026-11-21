from functools import lru_cache

from app.infra.config import settings


@lru_cache
def get_llm(temperature: float = 0.0):
    """Retorna o chat model configurado. Provedor trocável (ollama/openai/anthropic).

    A troca de provedor acontece só aqui — o resto do sistema não muda.
    A temperatura vem de cada chat; o cache guarda um modelo por temperatura.
    """
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
            # Modelos com "modo de raciocínio" (ex.: Qwen3) pensam em voz alta
            # antes de responder. Desligado por padrão: deixa a resposta bem
            # mais rápida, o que pesa quando o modelo roda na máquina local.
            reasoning=settings.llm_reasoning,
            num_ctx=settings.llm_context_tokens,
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
        )

    raise ValueError(f"Provedor de LLM não suportado: {settings.llm_provider}")
