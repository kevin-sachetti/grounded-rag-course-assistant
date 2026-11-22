"""Busca em dois estágios do fluxo fixo.

Cada trecho encontrado vira um "candidato" (dict simples, pronto para ir ao
banco como JSON) com as notas de cada etapa:

    material_id, chunk_index, text
    vector_score  nota do 1º estágio (busca vetorial, 0 a 1)
    rerank_score  nota do 2º estágio (re-ranqueador, 0 a 1) ou None se desligado
    kept          se o trecho foi usado na resposta

Guardar todos os candidatos, e não só os escolhidos, é o que permite ao
painel "entender a resposta" mostrar também o que foi descartado e por quê.
"""

import asyncio

from app.adapters.reranker import score as rerank_scores
from app.adapters.vectorstore import search
from app.infra.config import settings
from app.pipeline.params import AnswerParams


def relevance(candidate: dict) -> float:
    """Nota usada para decidir: a do re-ranqueador quando existe, senão a vetorial."""
    if candidate.get("rerank_score") is not None:
        return candidate["rerank_score"]
    return candidate["vector_score"]


async def vector_stage(
    user_id: str, material_ids: list[str], question: str, params: AnswerParams
) -> list[dict]:
    """1º estágio: busca vetorial, restrita aos materiais do chat do usuário.

    Com re-ranking ligado traz mais candidatos, para o cross-encoder ter o
    que reordenar; sem ele já traz o número final.
    """
    k = (
        max(settings.retrieval_candidates, params.retrieval_k)
        if params.use_reranker
        else params.retrieval_k
    )
    results = await search(user_id, material_ids, question, k=k)
    return [{**r, "rerank_score": None, "kept": False} for r in results]


async def rerank_stage(question: str, candidates: list[dict]) -> list[dict]:
    """2º estágio: o cross-encoder dá nota a cada candidato e reordena.

    Roda em thread separada: é trabalho pesado de CPU e travaria o servidor
    inteiro se rodasse direto no laço de eventos.
    """
    if not candidates:
        return []
    scores = await asyncio.to_thread(
        rerank_scores, question, [c["text"] for c in candidates]
    )
    scored = [{**c, "rerank_score": s} for c, s in zip(candidates, scores)]
    return sorted(scored, key=lambda c: c["rerank_score"], reverse=True)


def select(candidates: list[dict], params: AnswerParams) -> list[dict]:
    """Marca como usados os `retrieval_k` melhores que atingem o limiar.

    Os candidatos já chegam em ordem (da busca vetorial ou do re-ranqueador).
    Se nenhum atinge o limiar, nenhum é usado — é isso que leva à recusa.
    """
    selected = []
    for position, c in enumerate(candidates):
        kept = position < params.retrieval_k and relevance(c) >= params.similarity_threshold
        selected.append({**c, "kept": kept})
    return selected


def kept(candidates: list[dict]) -> list[dict]:
    return [c for c in candidates if c["kept"]]
