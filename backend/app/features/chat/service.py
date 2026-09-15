from uuid import UUID

from langchain_core.messages import HumanMessage

from app.infra.config import settings
from app.pipeline.agent.graph import build_agent
from app.pipeline.rag.graph import graph as rag_graph


def _dedupe(sources: list[dict]) -> list[dict]:
    """Remove trechos repetidos: o agente pode buscar várias vezes."""
    vistos: set[tuple] = set()
    unicos = []
    for s in sources:
        chave = (s.get("material_id"), s.get("chunk_index"))
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(s)
    return unicos


async def answer_question(course_id: UUID, question: str) -> dict:
    """Responde a pergunta do aluno.

    Dois modos, escolhidos por settings.use_agent:
    - agente: o LLM decide quais ferramentas usar, em quantas rodadas
    - pipeline: fluxo fixo recuperar → reordenar → responder
    """
    if not settings.use_agent:
        return await rag_graph.ainvoke(
            {"course_id": course_id, "question": question}
        )

    graph, sources = build_agent(course_id)
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=question)]},
        config={"recursion_limit": settings.agent_max_steps},
    )
    return {
        "answer": result["messages"][-1].content,
        "sources": _dedupe(sources),
    }
