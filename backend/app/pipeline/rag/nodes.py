from langchain_core.documents import Document

from app.adapters.llm import get_llm
from app.pipeline.retrieval import rerank_top, vector_search
from app.pipeline.rag.prompts import ANSWER_TEMPLATE
from app.pipeline.rag.state import RagState


def _format_docs(documents: list[Document]) -> str:
    return "\n\n---\n\n".join(d.page_content for d in documents)


def _build_sources(state: RagState) -> list[dict]:
    scores = state.get("scores", [])
    return [
        {
            "material_id": d.metadata.get("material_id"),
            "chunk_index": d.metadata.get("chunk_index"),
            "score": scores[i] if i < len(scores) else None,
        }
        for i, d in enumerate(state["documents"])
    ]


async def retrieve(state: RagState) -> dict:
    """1º estágio da recuperação. Lógica em app/pipeline/retrieval.py."""
    results = await vector_search(state["course_id"], state["question"])
    return {
        "documents": [doc for doc, _ in results],
        "scores": [score for _, score in results],
    }


async def rerank(state: RagState) -> dict:
    """2º estágio da recuperação. Lógica em app/pipeline/retrieval.py."""
    results = await rerank_top(state["question"], state["documents"])
    return {
        "documents": [doc for doc, _ in results],
        "scores": [score for _, score in results],
    }


async def respond_raw(state: RagState) -> dict:
    """Devolve os trechos recuperados como estão, sem passar por LLM.

    Modo padrão: resposta extrativa (o texto é literalmente o do material).
    Custo zero e fidelidade total — serve para avaliar a recuperação sozinha.
    """
    documents = state["documents"]
    if not documents:
        return {"answer": "Não encontrei nada no material do curso.", "sources": []}

    return {"answer": _format_docs(documents), "sources": _build_sources(state)}


async def generate(state: RagState) -> dict:
    """Reformula os trechos recuperados em uma resposta clara para o aluno.

    Única chamada de LLM do fluxo. Só roda com use_llm_reformulation = true.
    """
    prompt = ANSWER_TEMPLATE.format(
        context=_format_docs(state["documents"]), question=state["question"]
    )
    response = await get_llm().ainvoke(prompt)
    return {"answer": response.content, "sources": _build_sources(state)}
