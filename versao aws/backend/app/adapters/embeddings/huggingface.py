from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from app.infra.config import settings


class PrefixedEmbeddings(Embeddings):
    """Adiciona prefixos ao texto antes de vetorizar.

    Modelos da família E5 são treinados com "query: " nas perguntas e
    "passage: " nos documentos. Omitir os prefixos não gera erro — apenas
    piora a recuperação de forma silenciosa.

    Os prefixos vêm das configurações: outro modelo pode exigir outros
    (ou nenhum, bastando deixá-los vazios).
    """

    def __init__(
        self, inner: Embeddings, query_prefix: str, document_prefix: str
    ) -> None:
        self._inner = inner
        self._query_prefix = query_prefix
        self._document_prefix = document_prefix

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._inner.embed_documents(
            [f"{self._document_prefix}{t}" for t in texts]
        )

    def embed_query(self, text: str) -> list[float]:
        return self._inner.embed_query(f"{self._query_prefix}{text}")

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._inner.aembed_documents(
            [f"{self._document_prefix}{t}" for t in texts]
        )

    async def aembed_query(self, text: str) -> list[float]:
        return await self._inner.aembed_query(f"{self._query_prefix}{text}")


@lru_cache
def get_embeddings() -> Embeddings:
    """Modelo de embeddings (local). Carregado uma vez e mantido em cache.

    Usado na ingestão (vetorizar os chunks) e no chat (vetorizar a pergunta).
    """
    model = HuggingFaceEmbeddings(model_name=settings.embedding_model_name)
    return PrefixedEmbeddings(
        model,
        query_prefix=settings.embedding_query_prefix,
        document_prefix=settings.embedding_document_prefix,
    )
