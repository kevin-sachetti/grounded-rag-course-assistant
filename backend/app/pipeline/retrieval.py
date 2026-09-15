import asyncio
from uuid import UUID

from langchain_core.documents import Document

from app.adapters.reranker import rerank as rerank_documents
from app.adapters.vectorstore import search
from app.infra.config import settings

Scored = list[tuple[Document, float]]


async def vector_search(course_id: UUID, question: str) -> Scored:
    """1º estágio: busca vetorial no pgvector, restrita ao curso.

    Com re-ranking ligado traz mais candidatos, para o cross-encoder ter o
    que reordenar; sem ele já traz o número final.
    """
    k = (
        settings.retrieval_candidates
        if settings.use_reranker
        else settings.retrieval_k
    )
    return await search(course_id, question, k=k)


async def rerank_top(question: str, documents: list[Document]) -> Scored:
    """2º estágio: cross-encoder reordena e mantém os melhores.

    Roda em thread separada: é trabalho pesado de CPU e travaria o servidor
    inteiro se rodasse direto no laço de eventos.
    """
    if not documents:
        return []
    docs, scores = await asyncio.to_thread(
        rerank_documents, question, documents, settings.retrieval_k
    )
    return list(zip(docs, scores))


async def search_and_rerank(course_id: UUID, question: str) -> Scored:
    """Os dois estágios em sequência. Usado pela ferramenta de busca do agente."""
    results = await vector_search(course_id, question)
    if not settings.use_reranker:
        return results
    return await rerank_top(question, [doc for doc, _ in results])
