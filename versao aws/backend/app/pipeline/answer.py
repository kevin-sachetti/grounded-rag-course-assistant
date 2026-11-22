"""Ponto de entrada da resposta: roda o fluxo fixo e monta os detalhes.

Na versão AWS não há agente: toda pergunta faz uma busca em dois estágios e,
se algum trecho passa da relevância mínima, uma chamada ao Nova Lite.

Os detalhes são o que o painel "entender a resposta" mostra:

    mode             sempre "fixed"
    params           parâmetros do chat usados nesta resposta
    steps            vazio (só o agente da versão local usa ferramentas)
    searches         a busca feita, com todos os candidatos e as notas de cada etapa
    versions         extractive = os trechos usados, como estão no material
                     final      = a resposta exibida
    history_messages 0 (o fluxo fixo não usa o histórico)
    elapsed_seconds  tempo total da resposta
"""
import time

from app.pipeline.params import AnswerParams
from app.pipeline.rag.graph import graph as rag_graph


async def answer_question(
    user_id: str, material_ids: list[str], question: str, params: AnswerParams
) -> dict:
    """Responde a pergunta e devolve {"answer", "refused", "details"}."""
    start = time.perf_counter()
    result = await rag_graph.ainvoke(
        {"user_id": user_id, "material_ids": material_ids, "question": question, "params": params}
    )
    details = {
        "mode": "fixed",
        "params": params.as_dict(),
        "steps": [],
        "searches": [{"query": question, "candidates": result.get("candidates", [])}],
        "versions": {"extractive": result.get("extractive", ""), "final": result["answer"]},
        "history_messages": 0,
        "elapsed_seconds": round(time.perf_counter() - start, 2),
    }
    return {"answer": result["answer"], "refused": result.get("refused", False), "details": details}
