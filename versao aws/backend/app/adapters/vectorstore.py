"""Busca vetorial sem banco vetorial: os vetores de cada material ficam no S3.

Na versão local, o pgvector faz essa conta. Aqui, a Lambda carrega os trechos
e os vetores dos materiais do chat e compara com a pergunta pela similaridade
do cosseno, contra todos os trechos, sem índice aproximado, como a versão local
também faz. Um chat tem poucos materiais, e um material, no máximo alguns
milhares de trechos: a conta leva milissegundos.

O que foi carregado fica em memória enquanto a Lambda está viva (cache), para
a próxima pergunta não ler o S3 de novo.
"""
import asyncio
from collections import OrderedDict

import numpy as np

from app.adapters import storage
from app.adapters.embeddings import get_embeddings

_CACHE_SIZE = 64  # materiais guardados em memória
_cache: OrderedDict[tuple[str, str], tuple[list[str], np.ndarray]] = OrderedDict()


def normalize(vectors: np.ndarray) -> np.ndarray:
    """Vetores de tamanho 1: assim o produto escalar já é o cosseno."""
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / np.where(norms == 0, 1, norms)


def embed_chunks(chunks: list[str]) -> np.ndarray:
    """Vetores dos trechos (o adapter acrescenta o prefixo "passage: ")."""
    return normalize(np.asarray(get_embeddings().embed_documents(chunks), dtype=np.float32))


def _load(user_id: str, material_id: str) -> tuple[list[str], np.ndarray]:
    key = (user_id, material_id)
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]
    chunks, vectors = storage.load_index(user_id, material_id)
    _cache[key] = (chunks, normalize(vectors))
    if len(_cache) > _CACHE_SIZE:
        _cache.popitem(last=False)
    return _cache[key]


def forget(user_id: str, material_id: str) -> None:
    """Tira o material do cache (quando ele é excluído)."""
    _cache.pop((user_id, material_id), None)


def _search(user_id: str, material_ids: list[str], query: str, k: int) -> list[dict]:
    if not material_ids:
        return []
    q = normalize(np.asarray(get_embeddings().embed_query(query), dtype=np.float32))
    found = []
    for material_id in material_ids:
        chunks, vectors = _load(user_id, material_id)
        if not chunks:
            continue
        sims = vectors @ q
        for i in np.argsort(-sims)[:k]:
            found.append((float(sims[i]), material_id, int(i), chunks[i]))
    found.sort(key=lambda f: f[0], reverse=True)
    return [
        {"material_id": m, "chunk_index": i, "text": t, "vector_score": s}
        for s, m, i, t in found[:k]
    ]


async def search(user_id: str, material_ids: list[str], query: str, k: int) -> list[dict]:
    """Os k trechos mais parecidos com a pergunta, só entre os materiais dados.

    Roda em thread separada: vetorizar a pergunta é trabalho de CPU.
    """
    return await asyncio.to_thread(_search, user_id, material_ids, query, k)
