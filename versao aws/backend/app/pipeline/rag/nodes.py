from app.adapters.llm import get_llm
from app.pipeline.rag.prompts import ANSWER_TEMPLATE, REFUSAL_MESSAGE
from app.pipeline.rag.state import RagState
from app.pipeline.retrieval import kept, rerank_stage, select, vector_stage


def format_chunks(candidates: list[dict]) -> str:
    return "\n\n---\n\n".join(c["text"] for c in kept(candidates))


async def retrieve(state: RagState) -> dict:
    """1º estágio da busca. Sem re-ranqueamento, a seleção já acontece aqui."""
    params = state["params"]
    candidates = await vector_stage(
        state["user_id"], state["material_ids"], state["question"], params
    )
    if not params.use_reranker:
        candidates = select(candidates, params)
    return {"candidates": candidates}


async def rerank(state: RagState) -> dict:
    """2º estágio da busca: re-ranqueamento e seleção pelo limiar."""
    candidates = await rerank_stage(state["question"], state["candidates"])
    return {"candidates": select(candidates, state["params"])}


async def refuse(state: RagState) -> dict:
    """Nenhum trecho atingiu o limiar: recusa sem chamar o LLM."""
    return {"answer": REFUSAL_MESSAGE, "extractive": "", "refused": True}


async def respond_raw(state: RagState) -> dict:
    """Devolve os trechos usados como estão, sem passar por LLM.

    Resposta extrativa: o texto é literalmente o do material.
    """
    text = format_chunks(state["candidates"])
    return {"answer": text, "extractive": text, "refused": False}


async def generate(state: RagState) -> dict:
    """Reformula os trechos usados em uma resposta clara.

    Única chamada de LLM do fluxo. A versão extrativa segue junto, para o
    painel mostrar as duas.
    """
    text = format_chunks(state["candidates"])
    prompt = ANSWER_TEMPLATE.format(context=text, question=state["question"])
    response = await get_llm(state["params"].temperature).ainvoke(prompt)
    return {"answer": response.content, "extractive": text, "refused": False}
