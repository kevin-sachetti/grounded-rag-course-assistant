"""Ponto de entrada da resposta: escolhe entre agente e fluxo fixo e monta os detalhes.

Os detalhes são o que o painel "entender a resposta" mostra:

    mode             "agent" ou "fixed"
    params           parâmetros do chat usados nesta resposta
    steps            ferramentas chamadas pelo agente, em ordem (vazio no fluxo fixo)
    searches         cada busca feita, com todos os candidatos e as notas de cada etapa
    versions         extractive = os trechos usados, como estão no material
                     final      = a resposta exibida
    history_messages quantas mensagens anteriores o agente recebeu (0 no fluxo fixo)
    elapsed_seconds  tempo total da resposta
"""

import time
from uuid import UUID

from langchain_core.messages import AIMessage, HumanMessage

from app.infra.config import settings
from app.pipeline.agent.graph import build_agent
from app.pipeline.params import AnswerParams
from app.pipeline.rag.graph import graph as rag_graph
from app.pipeline.retrieval import kept


def _extractive(searches: list[dict]) -> str:
    """Junta os trechos usados em todas as buscas, sem repetir."""
    seen: set[tuple] = set()
    parts = []
    for s in searches:
        for c in kept(s["candidates"]):
            key = (c["material_id"], c["chunk_index"])
            if key not in seen:
                seen.add(key)
                parts.append(c["text"])
    return "\n\n---\n\n".join(parts)


async def _fixed(material_ids: list[UUID], question: str, params: AnswerParams) -> dict:
    result = await rag_graph.ainvoke(
        {"material_ids": material_ids, "question": question, "params": params}
    )
    searches = [{"query": question, "candidates": result.get("candidates", [])}]
    return {
        "answer": result["answer"],
        "refused": result.get("refused", False),
        "steps": [],
        "searches": searches,
        "extractive": result.get("extractive", ""),
    }


async def _agent(
    material_ids: list[UUID], question: str, params: AnswerParams, history: list[tuple[str, str]]
) -> dict:
    graph, trace = build_agent(material_ids, params)
    previous = [
        HumanMessage(content=text) if role == "user" else AIMessage(content=text)
        for role, text in history
    ]
    result = await graph.ainvoke(
        {"messages": [*previous, HumanMessage(content=question)]},
        config={"recursion_limit": settings.agent_max_steps},
    )
    steps, searches = trace["steps"], trace["searches"]
    # Recusa: o agente só buscou e nenhuma busca trouxe trecho aceito.
    only_searched = bool(steps) and all(s["tool"] == "buscar_no_material" for s in steps)
    nothing_kept = not any(kept(s["candidates"]) for s in searches)
    return {
        "answer": result["messages"][-1].content,
        "refused": only_searched and nothing_kept,
        "steps": steps,
        "searches": searches,
        "extractive": _extractive(searches),
    }


async def answer_question(
    material_ids: list[UUID],
    question: str,
    params: AnswerParams,
    use_agent: bool,
    history: list[tuple[str, str]] | None = None,
) -> dict:
    """Responde a pergunta e devolve {"answer", "refused", "details"}.

    `history` = mensagens anteriores do chat, em ordem, como (role, texto).
    Só o agente as usa: no fluxo fixo a busca é feita com a pergunta como veio.
    """
    start = time.perf_counter()
    history = history or []
    if use_agent:
        r = await _agent(material_ids, question, params, history)
    else:
        r = await _fixed(material_ids, question, params)

    details = {
        "mode": "agent" if use_agent else "fixed",
        "params": params.as_dict(),
        "steps": r["steps"],
        "searches": r["searches"],
        "versions": {"extractive": r["extractive"], "final": r["answer"]},
        "history_messages": len(history) if use_agent else 0,
        "elapsed_seconds": round(time.perf_counter() - start, 2),
    }
    return {"answer": r["answer"], "refused": r["refused"], "details": details}
