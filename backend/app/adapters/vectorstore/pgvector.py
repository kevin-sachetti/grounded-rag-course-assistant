from functools import lru_cache
from uuid import UUID, uuid5

from langchain_postgres import PGVector

from app.adapters.embeddings import get_embeddings
from app.infra.config import settings

COLLECTION = "material_chunks"


@lru_cache
def get_vectorstore() -> PGVector:
    """Vector store no Postgres/pgvector (via LangChain). Guarda chunks + vetores."""
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION,
        connection=settings.database_url,
        use_jsonb=True,
        async_mode=True,
    )


def chunk_ids(material_id: UUID, chunk_count: int) -> list[str]:
    """Ids determinísticos dos chunks de um material.

    Derivados do material_id, então dá para recalculá-los depois sem
    guardar lista nenhuma — é o que permite apagar os vetores de um
    material quando ele é excluído ou reprocessado.
    """
    return [str(uuid5(material_id, str(i))) for i in range(chunk_count)]


async def add_chunks(material_id: UUID, chunks: list[str]) -> None:
    """Indexa os chunks de um material, guardando material_id e posição nos metadados."""
    metadatas = [
        {"material_id": str(material_id), "chunk_index": i} for i in range(len(chunks))
    ]
    await get_vectorstore().aadd_texts(
        texts=chunks,
        metadatas=metadatas,
        ids=chunk_ids(material_id, len(chunks)),
    )


async def delete_chunks(material_id: UUID, chunk_count: int) -> None:
    """Remove do índice os vetores de um material.

    Sem isso, apagar um material deixaria os trechos dele no índice e o
    assistente continuaria respondendo com conteúdo que o usuário removeu.
    """
    if chunk_count <= 0:
        return
    await get_vectorstore().adelete(ids=chunk_ids(material_id, chunk_count))


async def search(material_ids: list[UUID], query: str, k: int = 4):
    """Busca os k chunks mais similares à pergunta, só entre os materiais dados.

    O filtro por material_id garante que um chat só enxerga os materiais
    escolhidos para ele.

    Devolve pares (documento, nota). A nota é *relevância normalizada* entre
    0 e 1, onde MAIOR = mais parecido — e não a distância bruta (onde menor
    seria melhor).
    """
    if not material_ids:
        return []
    return await get_vectorstore().asimilarity_search_with_relevance_scores(
        query,
        k=k,
        filter={"material_id": {"$in": [str(m) for m in material_ids]}},
    )
